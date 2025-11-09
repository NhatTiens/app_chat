"""
daemon.request
~~~~~~~~~~~~~~~~~

HTTP Request parser — rewritten, same attributes & methods.
"""

from .dictionary import CaseInsensitiveDict  # noqa: F401


class Request:
    __attrs__ = [
        "method", "url", "headers", "body", "reason",
        "cookies", "body", "routes", "hook",
    ]

    def __init__(self):
        self.method = None
        self.url = None
        self.headers = None
        self.path = None
        self.cookies = None
        self.body = None
        self.routes = {}
        self.hook = None
        self.version = None

    # ---------- parsing utilities ----------

    def extract_request_line(self, request):
        try:
            first = request.splitlines()[0]
            method, path, version = first.split()
            if path == "/":
                path = "/index.html"
            return method, path, version
        except Exception:
            return None, None, None

    def prepare_headers(self, request):
        headers = {}
        for line in request.split("\r\n")[1:]:
            if ": " in line:
                k, v = line.split(": ", 1)
                headers[k.lower()] = v
        return headers

    def prepare(self, request, routes=None):
        # request line
        self.method, self.path, self.version = self.extract_request_line(request)
        print("[Request] {} path {} version {}".format(self.method, self.path, self.version))

        # route hook (strip query for matching)
        self.routes = routes or {}
        if self.routes:
            route_path = self.path.split("?", 1)[0]
            self.hook = self.routes.get((self.method, route_path))

        # headers + cookies
        self.headers = self.prepare_headers(request)
        self.cookies = self.parse_cookies()

        # body
        self.body = self.extract_body(request) if self.method == "POST" else ""
        return

    def prepare_body(self, data, files, json=None):
        if data:
            self.body = data
        self.prepare_content_length(self.body)
        return

    def prepare_content_length(self, body):
        if self.headers is None:
            self.headers = {}
        self.headers["Content-Length"] = str(len(body) if body else 0)
        return

    def prepare_auth(self, auth, url=""):
        return

    def prepare_cookies(self, cookies):
        if self.headers is None:
            self.headers = {}
        self.headers["Cookie"] = cookies

    # ---------- helpers ----------

    def parse_cookies(self):
        cookies = {}
        raw = (self.headers or {}).get("cookie", "")
        for pair in raw.split(";"):
            if "=" in pair:
                k, v = pair.strip().split("=", 1)
                cookies[k] = v
        return cookies

    def extract_body(self, request):
        parts = request.split("\r\n\r\n", 1)
        return parts[1] if len(parts) > 1 else ""

    def parse_form_data(self):
        form = {}
        for pair in (self.body or "").split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                form[k] = v.replace("+", " ")
        return form
