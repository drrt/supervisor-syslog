#!/usr/bin/python

import sys
import os
import argparse
import socket
import ssl
import yaml
import tempfile
import datetime

priority_names = {
    "emerg":    0,
    "alert":    1,
    "critical": 2,
    "error":    3,
    "warning":  4,
    "notice":   5,
    "info":     6,
    "debug":    7,
    }

facility_names = {
    "kern":     0,
    "user":     1,
    "mail":     2,
    "daemon":   3,
    "auth":     4,
    "syslog":   5,
    "lpr":      6,
    "news":     7,
    "uucp":     8,
    "cron":     9,
    "authpriv": 10,
    "ftp":      11,
    "local0":   16,
    "local1":   17,
    "local2":   18,
    "local3":   19,
    "local4":   20,
    "local5":   21,
    "local6":   22,
    "local7":   23,
    }


def syslog_socket(address=None, ca_certs=None, keyfile=None, certfile=None, tls=False):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if tls:
        cert_reqs = ssl.CERT_REQUIRED if ca_certs else ssl.CERT_NONE
        s = ssl.wrap_socket(s, ca_certs=ca_certs, keyfile=keyfile,
                            certfile=certfile, cert_reqs=cert_reqs)
    s.connect(address)
    return s


def event_fail(fd):
    fd.write('RESULT 4\nFAIL')
    fd.flush()


def event_ok(fd):
    fd.write('RESULT 2\nOK')
    fd.flush()


def event_ready(fd):
    fd.write('READY\n')
    fd.flush()


def write_stderr(s):
    sys.stderr.write(s)
    sys.stderr.flush()


def parse_commandline(parser):
    parser.add_argument('--config', help='configuration file')
    parser.add_argument('--server', help='name or address of remote syslog server')
    parser.add_argument('--port', help='remote syslog server port', type=int)
    parser.add_argument('--bsd', help='send BSD style logs', action='store_true')
    parser.add_argument('--hostname', help='hostname to inject in syslog messages')
    parser.add_argument('--tls', help='use TLS')
    parser.add_argument('--ca', help='ca file for verifying remote server')
    parser.add_argument('--cert', help='certificate to present to the remote server')
    parser.add_argument('--key', help='keyfile for the certificate')
    parser.add_argument('--facility', help='syslog facility')
    parser.add_argument('--data', help='structured data')
    parser.add_argument('--verify', help='verify server common name', action='store_true')
    parser.add_argument('--yaml', help='yaml subsection')

    return parser.parse_args()


def config_file(args, config):
    # shift yaml up one config level if --yaml option is present
    if args.yaml:
        try:
            config = config[args.yaml]
        except:
            raise ValueError('no such yaml key "{}"'.format(args.yaml))
        
    # override the yaml config with any command line arguments present
    for n in vars(args):
        if not getattr(args, n):
            setattr(args, n, config.get(n))

    # if the certificates are embedded in the yaml, write them 
    # to temporary files and replace them with pathnames
    for n in ('ca', 'cert', 'key'):
        # are we a pem or a pathname
        if getattr(args, n) and '-----' in getattr(args, n):
            (fd, path) = tempfile.mkstemp()
            os.write(fd, getattr(args, n))
            setattr(args, n, path)
            os.close(fd)

    return args 


def config_check(args):
    if not args.server:
        raise ValueError('argument --server is required')

    if args.cert or args.ca:
        args.tls = True

    if args.tls:
        # parser does not support mutually inclusive arguments
        if ((args.cert and not args.key) or (not args.cert and args.key)):
            raise ValueError('cert and key are mutually inclusive')

    # we are managing defaults here due to the yaml/cmdline merge
    args.facility = 'user' if not args.facility else args.facility
    args.port = 6514 if not args.port else args.port

    try:
        facility_names[args.facility]
    except KeyError:
        raise ValueError('facility "{}" is invalid'.format(args.facility))

    return args


def read_event(fd):
    payload = {}

    # first line is the generic supervisor event header
    # ver: server: serial: pool: poolserial: eventname: len:
    d = fd.readline()
    payload.update(dict([ x.split(':') for x in d.split() ]))

    # read the rest of the event. the PROCESS_LOG header is always terminated
    # with a newline, the remainder is the msg
    # processname: groupname: pid: channel:
    # msg
    # ...
    ( d, msg ) = fd.read(int(payload.get('len'))).split('\n', 1)
    payload.update(dict([ x.split(':') for x in d.split() ]))

    # encode our message if necessary
    if type(msg) is unicode:
        msg = msg.encode('utf-8')

    payload.update({'msg': msg})

    return (payload)


def create_priority(eventname, facility):
    # set the message priority based on the incoming supervisor event type
    if eventname == 'PROCESS_LOG_STDOUT':
        priority = (facility_names[facility] << 3) | priority_names['info']
    else:
        priority = (facility_names[facility] << 3) | priority_names['error']

    return priority


def msg_bsd(priority, hostname, payload):
    # craft a rfc3164 (BSD) style syslog message
    fmt = '<{}>{} {} {}: {}'
    time_date = datetime.datetime.now().strftime('%b %e %H:%M:%S')
    msg = fmt.format(priority, time_date, hostname,
                     payload.get('processname'), payload.get('msg'))
    return msg


def msg_rfc5424(priority, hostname, data, payload):
    # craft a rfc5424 complaint syslog message
    fmt = '<{}>1 {} {} {} {} {} {} {}'
    data = data if data else '-'
    time_date = str(datetime.datetime.utcnow()).replace(' ', 'T', 1) + '-00:00'
    msg = fmt.format(priority, time_date, hostname, payload.get('processname'),
                     payload.get('pid'), payload.get('serial'), data, payload.get('msg'))
    return msg


def handler():
    parser = argparse.ArgumentParser()
    args = parse_commandline(parser)

    # parse the config file if requested
    if args.config:
        try:
            config = yaml.load(file(args.config, 'r'))
            args = config_file(args, config)
        except ValueError as err:
            parser.error(err)
        except IOError as err:
            parser.error(str(err))

    try:
        args = config_check(args)
    except ValueError as err:
        parser.error(err)
    except Exception as err:
        sys.exit(repr(err))

    try:
        ssl_socket = syslog_socket(address=(args.server, args.port), tls=args.tls,
                                  ca_certs=args.ca, keyfile=args.key, certfile=args.cert)
    except Exception as err:
        sys.exit(repr(err))

    # pick a hostname to include in the syslog messages
    hostname = args.hostname if args.hostname else socket.gethostname()

    while True:
        event_ready(sys.stdout)

        try:
            payload = read_event(sys.stdin)
        except Exception as err:
            event_fail(sys.stdout)
            write_stderr(repr(err))
            continue

        priority = create_priority(payload.get('eventname'), args.facility)

        if args.bsd:
            msg = msg_bsd(priority, hostname, payload)
        else:
            msg = msg_rfc5424(priority, hostname, args.data, payload)

        try:
            ssl_socket.send(msg)
        except Exception as err:
            event_fail(sys.stdout)
            write_stderr(repr(err) + '\n')
        else:
            event_ok(sys.stdout)


