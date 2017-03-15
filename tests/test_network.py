import pytest
import os
import time 
import thread
import ssl 
import socket

import supervisor_syslog

os.chdir(os.path.dirname(__file__))

def _socket_handler(s):
    while True:
        try:
            c, a = s.accept()
            c.close()
        except:
            # ignore all "server' failures
            pass

@pytest.fixture(scope='session')
def tls_server(request):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s = ssl.wrap_socket(s, server_side=True, cert_reqs=ssl.CERT_NONE,
                        ca_certs='tls/one_ca.cert',
                        keyfile='tls/one_server.key',
                        certfile='tls/one_server.cert')
    except Exception as err:
        print(rept(err))
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('localhost', 0))
    s.listen(1)
    thread.start_new_thread(_socket_handler, (s,))
    yield s.getsockname()

@pytest.fixture(scope='session')
def plain_server(request):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('localhost', 0))
    s.listen(1)    
    thread.start_new_thread(_socket_handler, (s,))
    yield s.getsockname()

def _s_connect(addr, c):
    __tracebackhide__ = True
    ca = 'tls/' + c[0] if c[0] else None
    cert = 'tls/' + c[1] if c[1] else None 
    key = 'tls/' + c[2] if c[2] else None
    tls = c[3] if c[3] else False
    supervisor_syslog.syslog_socket(address=addr, tls=tls,
        ca_certs=ca, certfile=cert, keyfile=key)

def test_match_certs_verify(tls_server):
    c = [ 'one_ca.cert', 'one_client.cert', 'one_client.key', True ]
    _s_connect(tls_server, c)
    
def test_mismatch_verify(tls_server):
    c = [ 'two_ca.cert', 'two_client.cert', 'two_client.key', True ]
    with pytest.raises(ssl.SSLError) as err:
        _s_connect(tls_server, c)

def test_match_nocerts_verify(tls_server):
    c = [ 'one_ca.cert', None, None, True ]
    _s_connect(tls_server, c)

def test_mismatch_nocerts_verify(tls_server):
    c = [ 'two_ca.cert', None, None, True ]
    with pytest.raises(ssl.SSLError) as err:
        _s_connect(tls_server, c)

def test_noca_certs(tls_server):
    c = [ None, 'one_client.cert', 'one_client.key', True ]
    _s_connect(tls_server, c)

def test_noca_nocerts(tls_server):
    c = [ None, None, None, True ]
    _s_connect(tls_server, c)

def test_badca_nocerts(tls_server):
    c = [ 'bad_ca.cert', None, None, True ]
    with pytest.raises(ssl.SSLError) as err:
        _s_connect(tls_server, c)

def test_noca_badcert(tls_server):
    c = [ None,  'bad_client.cert', None, True ]
    with pytest.raises(ssl.SSLError) as err:
        _s_connect(tls_server, c)

def test_noca_badkey(tls_server):
    c = [ None, None,  'bad_client.key', True ]
    with pytest.raises(ssl.SSLError) as err:
        _s_connect(tls_server, c)

def test_tls_plain(plain_server):
    c = [ None, None, None, True ]
    with pytest.raises(socket.error) as err:
        _s_connect(plain_server, c)

def test_plain_plain(plain_server):
    c = [ None, None, None, False ]
    _s_connect(plain_server, c)

