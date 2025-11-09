"""
daemon.httpadapter
~~~~~~~~~~~~~~~~~

Rewritten HttpAdapter. Preserves public surface & utility helpers that
your app already calls (including login/protected helpers).
"""

from .request import Request
from .response import Response
from .dictionary import CaseInsensitiveDict  # noqa: F401


class HttpAdapter:
    """
    Request–response orchestrator for one client connection.
    """

    __attrs__ = [
        "ip", "port", "conn", "connaddr",
        "routes", "request", "response",
    ]

    def __init__(self, ip, port, conn, connaddr, routes):
        self.ip = ip
        self.port = port
        self.conn = conn
        self.connaddr = connaddr
        self.routes = routes
        self.request = Request()
        self.response = Response()

    def handle_client(self, conn, addr, routes):
        """
        1) recv raw, 2) parse → Request, 3) hook/login/protected/static, 4) send.
        """
        self.conn = conn
        self.connaddr = addr

        req = self.request
        resp = self.response

        try:
            raw = conn.recv(1024).decode()
            if not raw:
                # client closed early; nothing to do
                conn.close()
                return

            req.prepare(raw, routes)

            # --- priority 1: RESTful hook (apps/sampleApp routes) ---
            if req.hook:
                print("[HttpAdapter] hook in route-path METHOD {} PATH {}".format(
                    getattr(req.hook, "_route_path", "?"),
                    getattr(req.hook, "_route_methods", "?"),
                ))
                result = self._call_hook(req)

                # Allow hook to return Response or plain/dict
                if isinstance(result, Response):
                    packet = result.build_response(req)
                else:
                    if isinstance(result, dict):
                        body = str(result)
                        head = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
                    else:
                        body = str(result)
                        head = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n"
                    packet = (head + "Content-Length: {}\r\n\r\n{}".format(len(body), body)).encode()

                conn.sendall(packet)
                conn.close()
                return

            # --- priority 2: explicit login path (Task 1A) ---
            if req.method == "POST" and req.path == "/login":
                conn.sendall(self.handle_login(req, resp))
                conn.close()
                return

            # --- priority 3: protected resources (Task 1B) ---
            if req.path in ("/", "/index.html"):
                conn.sendall(self.handle_protected_route(req, resp))
                conn.close()
                return

            # --- default: serve static via Response factory ---
            conn.sendall(resp.build_response(req))

        except Exception as e:
            conn.sendall(self.build_error_response(500, "Internal Server Error: {}".format(e)))
        finally:
            conn.close()

    # -------------------- helpers --------------------

    def _call_hook(self, req):
        """Call route function with a flexible signature."""
        hook = req.hook
        names = getattr(hook, "__code__", None)
        names = names.co_varnames if names else ()

        if "body" in names:
            return hook(body=req.body)
        if "req" in names:
            return hook(req)
        return hook()

    @property
    def extract_cookies(self):
        """Compatibility property—cookies come from the Request object."""
        return self.request.cookies

    def build_response(self, req, resp):
        """Provide a Response wrapper with context (rarely used directly)."""
        r = Response()
        r.encoding = "utf-8"
        r.raw = resp
        r.reason = getattr(resp, "reason", "OK")
        r.url = req.url.decode() if isinstance(req.url, bytes) else req.url
        r.cookies = self.extract_cookies
        r.request = req
        r.connection = self
        return r

    def add_headers(self, request):
        """No-op; left for future extension."""
        pass

    def build_proxy_headers(self, proxy):
        """Return minimal proxy auth header (same effect)."""
        u, p = ("user1", "password")
        return {"Proxy-Authorization": "{}:{}".format(u, p)}

    # -------------------- Task 1A / 1B helpers kept by name --------------------

    def handle_login(self, req, resp):
        """Authenticate /login (admin/password) and set cookie."""
        form = req.parse_form_data()
        user = form.get("username", "")
        pw = form.get("password", "")
        print("[HttpAdapter] Login attempt: username={}, password={}".format(user, pw))

        if user == "admin" and pw == "password":
            resp.set_cookie("auth", "true")
            resp.status_code = 200
            req.path = "/index.html"
            return resp.build_response(req)

        return self.build_error_response(401, "Unauthorized")

    def handle_protected_route(self, req, resp):
        """Guard index or root by cookie."""
        if req.cookies.get("auth") == "true":
            if req.path == "/":
                req.path = "/index.html"
            return resp.build_response(req)
        return self.build_error_response(401, "Unauthorized - Please login first")

    def build_error_response(self, status_code, message):
        """Minimal HTML error envelope."""
        if status_code == 401:
            body = (
                "<html><body><h1>401 Unauthorized</h1>"
                "<p>{}</p><a href=\"/login.html\">Login Here</a></body></html>"
            ).format(message)
        else:
            body = "<html><body><h1>{} {}</h1><p>{}</p></body></html>".format(status_code, message, message)

        head = (
            "HTTP/1.1 {} {}\r\n"
            "Content-Type: text/html\r\n"
            "Content-Length: {}\r\n"
            "Connection: close\r\n\r\n"
        ).format(status_code, message, len(body))
        return (head + body).encode()
