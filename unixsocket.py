# coding=utf-8
__author__ = 'Kane'
import socket
from requests.adapters import HTTPAdapter, DEFAULT_POOLBLOCK
from requests.packages.urllib3 import PoolManager, HTTPSConnectionPool
from requests.packages.urllib3.connection import HTTPConnection


class UnixSocketResponse(object):
    def __init__(self):
        super(UnixSocketResponse, self).__init__()
        self.reason = "No reason"


class UnixSocketConnection(HTTPConnection):
    def __init__(self, *args, **kw):
        kw.update({'port': 80})
        super(UnixSocketConnection, self).__init__(*args, **kw)

        url = self.host
        i = url.index('unix.socket')
        url = url[:i + len('unix.socket')]
        self.host = url.lstrip('unix:')

    def connect(self):
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(self.host)
            self.sock = sock
        except:
            self.sock = 123

    def request(self, method, url, body=None, headers={}):
        headers['Host'] = 'unix.socket'
        HTTPConnection.request(self, method, url, body, headers)

    def send(self, data):
        # print 'send:[%s]' % data
        HTTPConnection.send(self, data)


class UnixConnectionPool(HTTPSConnectionPool):
    ConnectionCls = UnixSocketConnection


class UnixSocketPoolManager(PoolManager):
    def _new_pool(self, scheme, host, port):
        return super(UnixSocketPoolManager, self)._new_pool(scheme, host, port)


class UnixAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=DEFAULT_POOLBLOCK, **pool_kwargs):
        self._pool_connections = connections
        self._pool_maxsize = maxsize
        self._pool_block = block

        self.poolmanager = UnixSocketPoolManager(num_pools=connections, maxsize=maxsize,
                                                 block=block, strict=True, **pool_kwargs)

    def get_connection(self, url, proxies=None):
        # print url
        return UnixConnectionPool(url)

    def request_url(self, request, proxies):
        url = request.url
        i = url.index('unix.socket')
        return url[i + len('unix.socket'):]

    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        return super(UnixAdapter, self).send(request, stream, timeout, verify, cert, proxies)
