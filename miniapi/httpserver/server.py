from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIServer


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    pass
