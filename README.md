# supervisor-syslog

### What is it?
A supervisord event listener for remote syslogging. It will listen to all of your \[program\] output and ship the results to a syslog server of your choice, bypassing all local syslog infrastructure.

### Why would you use this over `stdout_logfile=syslog`

Using supervisord's build-in syslog functionality:
* Disables local file logging (and tail functionality)
* Only send to the localhost's syslog agent, which would need to be reconfigured for aggregation 

### How is this different than [supervisor-logging](https://github.com/infoxchange/supervisor-logging)?

supervisor-syslog supports:
* TLS connections
* Certificate verification
* Client certificates
* BSD and RFC5424 formatted syslog
* Adding structured data to RFC5424 messages

supervisor-syslog does _not_:
* Support UDP
* Honor localhost timezone settings

### Configuration

supervisor-syslog can be configured with command line flags or a YAML file. Options common to both:

| option | description | default |
| :---- | :---- | :---- |
| --server | The IP address or hostname of the remote syslog server | |
| --port | The port of the remote syslog service | 6514 |
| --hostname | Override the local hostname in send messages | the local hostname |
| --bsd | Send BSD-style syslog messages | send RFC5424 messages |
| --facility | Syslog facility to use | user |
| --data | Structured data to include in RFC5424 messages | |
| --tls | Require TLS when connecting to the remote server | do not require TLS |
| --ca | Path to a file that contains certificates | |
| --verify | Verify the remote syslog server with the certificates from above | |
| --cert | Path to a client certifate | |
| --key | Path to a client key file | |

When using a configuration file, the following options are available:

| option | description |
| :---- | :---- |
| --config | Path to a configuration file |
| --yaml | Optional name of a YAML node that the config lives under |

You can mix command-line options with --config and --yaml.
The options present in the configuration file will override conflicting
command-line options without warning.

NOTE: You can embed certificates and keys in the configuration file, see below for an example.

### supervisord config

Create a new eventlistener:
```
[eventlistener:logging]
command = supervisor-syslog --server remotehost.example.com --tls
events = PROCESS_LOG
```
Add to all of your `program` sections:
```
[program:myprogram]
stdout_events_enabled = true
stderr_events_enabled = true
```

### Example command line and YAML for sending logs to Loggly

`supervisor-syslog --config loggly.yaml --yaml logging`

```
logging:
    server: logs-01.loggly.com
    tls: true
    verify: true
    data: '<token>@41058 tag="supervisor"'

    ca: |
        -----BEGIN CERTIFICATE-----
        <paste loggly's certificate chain here>
        -----END CERTIFICATE-----
```

### Requirements

* python >= 2.7.6 and < 3.0
* PyYAML >= 3.0

### Message format caveats

* Messages to stdout will always be priority `info`, messages to stderr will always be priority `error`
* Process name will always be the supervisord program name that sent the message
* RFC5424 messages will include the process PID as well as a serial number from supervisord
* BSD messages will not include any configured structured data
* Timestamps are always in UTC (and offset of +00:00) regardless of the host system's configuration

