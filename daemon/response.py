"""
daemon.response
~~~~~~~~~~~~~~~~~

Response builder — rewritten, same fields and behavior.
"""

import datetime
import os
import mimetypes
from .dictionary import CaseInsensitiveDict


BASE_DIR = ""


class Response:
    __attrs__ = [
        "_content", "_header",
        "status_code", "method", "headers", "url",
        "history", "encoding", "reason", "cookies",
        "elapsed", "request", "body", "reason",
    ]

    def __init__(self, request=None):
        self._content = False
        self._content_consumed = False
        self._next = None

        self.status_code = None
        self.headers = {}
        self.url = None
        self.encoding = None
        self.history = []
        self.reason = None
        self.cookies = CaseInsensitiveDict()
        self.elapsed = datetime.timedelta(0)
        self.request = None
        self.content = None  # optional dynamic payload

    # ---------------- cookie helpers ----------------

    def set_cookie(self, name, value, path="/", max_age=None):
        cookie = "{}={}; Path={}".format(name, value, path)
        if max_age:
            cookie += "; Max-Age={}".format(max_age)
        self.cookies[name] = cookie

    # ---------------- mime helpers ----------------

    def get_mime_type(self, path):
        try:
            mt, _ = mimetypes.guess_type(path)
        except Exception:
            return "application/octet-stream"
        return mt or "application/octet-stream"

    def prepare_content_type(self, mime_type="text/html"):
        base_dir = ""
        main, sub = mime_type.split("/", 1)
        print("[Response] processing MIME main_type={} sub_type={}".format(main, sub))

        if main == "text":
            self.headers["Content-Type"] = "text/{}".format(sub)
            base_dir = BASE_DIR + ("www/" if sub == "html" else "static/")
        elif main == "image":
            self.headers["Content-Type"] = "image/{}".format(sub)
            base_dir = BASE_DIR + "static/"
        elif main == "application":
            self.headers["Content-Type"] = "application/{}".format(sub)
            base_dir = BASE_DIR + ("apps/" if sub != "octet-stream" else "static/")
        else:
            raise ValueError("Invalid MIME type: {}/{}".format(main, sub))

        return base_dir

    def build_content(self, path, base_dir):
        # avoid duplicating static/ when request already carries it
        if path.startswith("/static/"):
            filepath = path.lstrip("/")
        else:
            filepath = os.path.join(base_dir, path.lstrip("/"))

        print("[Response] serving the object at location {}".format(filepath))

        try:
            with open(filepath, "rb") as f:
                buf = f.read()
            return len(buf), buf
        except FileNotFoundError:
            return 0, b"File not found"
        except Exception as e:
            return 0, ("Error reading file: {}".format(e)).encode()

    # ---------------- header builders ----------------

    def build_response_header(self, request):
        reqhdr = request.headers

        # dynamic headers
        headers = {
            "Accept": reqhdr.get("Accept", "application/json"),
            "Accept-Language": reqhdr.get("Accept-Language", "en-US,en;q=0.9"),
            "Authorization": reqhdr.get("Authorization", "Basic <credentials>"),
            "Cache-Control": "no-cache",
            "Content-Type": self.headers.get("Content-Type", "text/html"),
            "Content-Length": str(len(self._content)),
            "Date": datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"),
            "Max-Forward": "10",
            "Pragma": "no-cache",
            "Proxy-Authorization": "Basic dXNlcjpwYXNz",
            "Warning": "199 Miscellaneous warning",
            "User-Agent": reqhdr.get("User-Agent", "Chrome/123.0.0.0"),
        }

        # status line + headers
        lines = ["HTTP/1.1 200 OK"]
        lines += ["{}: {}".format(k, v) for k, v in headers.items()]

        # cookies
        for _, cookie in self.cookies.items():
            lines.append("Set-Cookie: {}".format(cookie))

        lines.append("")  # blank line
        return ("\r\n".join(lines) + "\r\n").encode()

    def build_notfound(self):
        return (
            "HTTP/1.1 404 Not Found\r\n"
            "Accept-Ranges: bytes\r\n"
            "Content-Type: text/html\r\n"
            "Content-Length: 13\r\n"
            "Cache-Control: max-age=86000\r\n"
            "Connection: close\r\n"
            "\r\n"
            "404 Not Found"
        ).encode()

    # ---------------- top-level response builder ----------------

    def build_response(self, request):
        # Dynamic payload from route hook?
        if getattr(self, "content", None):
            print("[Response] Building dynamic response for {} {}".format(request.method, request.path))
            self.headers["Content-Type"] = "application/json"
            self._content = self.content.encode() if isinstance(self.content, str) else self.content
            self._header = self.build_response_header(request)
            return self._header + self._content

        path = request.path
        mime = self.get_mime_type(path)
        print("[Response] {} path {} mime_type {}".format(request.method, request.path, mime))

        if path.endswith(".html") or mime == "text/html":
            base = self.prepare_content_type("text/html")
        elif mime == "text/css":
            base = self.prepare_content_type("text/css")
        elif path.endswith(".js") or mime in ("application/javascript", "text/javascript"):
            base = self.prepare_content_type("application/javascript")
        elif mime.startswith("image/"):
            base = self.prepare_content_type(mime)
        else:
            return self.build_notfound()

        size, self._content = self.build_content(path, base)
        if size == 0 and self._content == b"File not found":
            return self.build_notfound()

        self._header = self.build_response_header(request)
        return self._header + self._content
