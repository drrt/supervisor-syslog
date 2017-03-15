import pytest
import os
import copy
import argparse

import supervisor_syslog

os.chdir(os.path.dirname(__file__))


config_args = argparse.Namespace(
    bsd=False,
    ca=None,
    cert=None,
    config=None,
    data=None,
    facility=None,
    hostname=None,
    key=None,
    port=None,
    server=None,
    tls=None,
    verify=False,
    yaml=None,
)

config_yaml = {
    'testsection': {
        'cert': '-----BEGIN CERTIFICATE-----\n',
        'key': '-----BEGIN RSA PRIVATE KEY-----\n',
        'facility': 'user',
        'ca': '-----BEGIN CERTIFICATE-----\n',
        'data': '[test data]',
        'port': 12345,
        'server': 'localhost',
        'bsd': True
    }
}

def test_config_check_server():
    a = config_args
    with pytest.raises(ValueError) as err:
        supervisor_syslog.config_check(a)
    assert err.match('required')

def test_config_check_cert():
    a = copy.copy(config_args)
    a.server = 'bar'
    a.cert = 'foo'
    with pytest.raises(ValueError) as err:
        supervisor_syslog.config_check(a)
    assert err.match('inclusive')

def test_config_check_facility():
    a = copy.copy(config_args)
    a.server = 'biz'
    a.facility = 'baz'
    with pytest.raises(ValueError) as err:
        supervisor_syslog.config_check(a)
    assert err.match('invalid')

def test_config_file_overall():
    a = copy.copy(config_args)
    a.yaml = 'testsection'
    supervisor_syslog.config_file(a, config_yaml)

def test_config_file_subsection():
    a = copy.copy(config_args)
    a.yaml = 'testfail'
    with pytest.raises(ValueError) as err:
        supervisor_syslog.config_file(a, config_yaml)
    assert err.match('no such yaml')

def test_config_file_override():
    a = copy.copy(config_args)
    a.yaml = 'testsection'
    b = supervisor_syslog.config_file(a, config_yaml)
    assert b.bsd == True

def test_config_file_tls_file_1():
    a = copy.copy(config_args)
    a.yaml = 'testsection'
    b = supervisor_syslog.config_file(a, config_yaml)
    assert 'tmp' in b.cert

def test_config_file_tls_file_2():
    a = copy.copy(config_args)
    a.yaml = 'testsection'
    a.cert = '/tmp/foofile'
    b = supervisor_syslog.config_file(a, config_yaml)
    assert 'foofile' in b.cert

def test_config_file_tls_file_3():
    a = copy.copy(config_args)
    a.yaml = 'testsection'
    b = supervisor_syslog.config_file(a, config_yaml)
    assert os.path.isfile(b.cert)

