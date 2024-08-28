import json


class Request:
    def __init__(self, environ):
        self.environ = environ
        self.method = environ.get('REQUEST_METHOD', 'GET')
        self.path = environ.get('PATH_INFO', '/')
        self.query_string = environ.get('QUERY_STRING', '')
        self.headers = self._parse_headers(environ)
        self.body = self._get_body(environ)
        self._parse_query_params()
        self.state: dict = {}

    @staticmethod
    def _parse_headers(environ):
        """Parse and return headers from the WSGI environment."""
        headers = {}
        for key, value in environ.items():
            if key.startswith('HTTP_'):
                header_key = key[5:].replace('_', '-').title()
                headers[header_key] = value
        return headers

    @staticmethod
    def _get_body(environ):
        """Read and return the request body."""
        content_length = int(environ.get('CONTENT_LENGTH') or 0)
        if content_length > 0:
            return environ['wsgi.input'].read(content_length).decode('utf-8')
        return ''

    def _parse_query_params(self):
        """Parse query parameters into a dictionary."""
        import urllib.parse
        self.query_params = urllib.parse.parse_qs(self.query_string)

    def get_header(self, name):
        """Get a header value by name."""
        return self.headers.get(name.title(), None)

    def query(self, name, default=None):
        """Get a query parameter value by name."""
        return self.query_params.get(name, [default])[0]

    def get_json(self):
        """Parse and return the request body as JSON, if applicable."""
        if 'application/json' in self.get_header('Content-Type') or '':
            try:
                return json.loads(self.body)
            except json.JSONDecodeError:
                return None
        return None

    def __repr__(self):
        return f"<Request method={self.method} path={self.path}>"
