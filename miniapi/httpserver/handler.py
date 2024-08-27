import sys
from platform import python_implementation
from wsgiref.handlers import SimpleHandler
from wsgiref.simple_server import WSGIRequestHandler as _WSGIRequestHandler

__version__ = "0.2"

server_version = "WSGIServer/" + __version__
sys_version = python_implementation() + "/" + sys.version.split()[0]
software_version = server_version + ' ' + sys_version


class ServerHandler(SimpleHandler):
    server_software = software_version

    def close(self):
        SimpleHandler.close(self)


class WSGIRequestHandler(_WSGIRequestHandler):

    def handle(self):
        """Handle a single HTTP request"""

        self.raw_requestline = self.rfile.readline(65537)  # noqa
        if len(self.raw_requestline) > 65536:
            self.requestline = ''  # noqa
            self.request_version = ''
            self.command = ''
            self.send_error(414)
            return

        if not self.parse_request():
            return

        handler = ServerHandler(
            self.rfile, self.wfile, self.get_stderr(), self.get_environ()
        )
        handler.request_handler = self
        handler.run(self.server.get_app())  # noqa
