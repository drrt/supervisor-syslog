import pytest
import os
import re

import supervisor_syslog

os.chdir(os.path.dirname(__file__))

payload_good = {'ver': '3.0',
                'groupname': 'bar',
                'poolserial': '10',
                'pid': '123',
                'len': '60',
                'server': 'supervisor',
                'eventname': 'PROCESS_LOG_STDOUT',
                'processname': 'foo',
                'msg': 'adfasdfasdf adsdfasdf\n',
                'serial': '21',
                'pool': 'listener'}

def test_event_good():
    fd = open('inputs/event_good.txt')
    result = supervisor_syslog.read_event(fd)
    assert result == payload_good

def test_event_bad_1():
    fd = open('inputs/event_bad_1.txt')
    with pytest.raises(TypeError) as err:
        result = supervisor_syslog.read_event(fd)

def test_create_priority_1():
    r = supervisor_syslog.create_priority('PROCESS_LOG_STDOUT', 'user')
    assert r == 14

def test_create_priority_2():
    r = supervisor_syslog.create_priority('PROCESS_LOG_STDERR', 'local0')
    assert r == 131

def test_msg_bsd():
    g = '<14>[A-Z][a-z][a-z][ ]+[0-9]+ [0-9][0-9]:[0-9][0-9]:[0-9][0-9] testhost foo: adfasdfasdf adsdfasdf'
    r = supervisor_syslog.msg_bsd(14, 'testhost', payload_good)
    assert re.match(g, r)

def test_msg_rfc5424():
    g = '<14>1 [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]\+[0-9][0-9]:[0-9][0-9] testhost foo 123 21 \[foo=bar\] adfasdfasdf adsdfasdf'
    d = 'foo=bar'
    r = supervisor_syslog.msg_rfc5424(14, 'testhost', d, payload_good)
    assert re.match(g, r)
