"""
opalib.web - A fully custom web framework for building web applications.

This module provides a minimal but complete web framework similar to Flask,
built from scratch without external web framework dependencies.
"""

import json
import re
import mimetypes
from typing import Callable, Dict, List, Any, Optional, Tuple, Union
from urllib.parse import parse_qs, urlparse, unquote
from datetime import datetime
from pathlib import Path
from wsgiref.simple_server import make_server
import traceback


class Request:
    """Represents an HTTP request."""

    def __init__(self, environ: Dict[str, Any]):
        """
        Initialize a Request object from WSGI environ dictionary.
        
        Args:
            environ: WSGI environment dictionary
        """
        self.environ = environ
        self.method = environ.get("REQUEST_METHOD", "GET").upper()
        self.path = environ.get("PATH_INFO", "/")
        self.query_string = environ.get("QUERY_STRING", "")
        self.headers = self._parse_headers()
        self.cookies = self._parse_cookies()
        self._body = None
        self._json = None
        self._form = None
        self.route_params: Dict[str, Any] = {}
        self.path_params = self.route_params

    def _parse_headers(self) -> Dict[str, str]:
        """Parse HTTP headers from WSGI environ."""
        headers = {}
        for key, value in self.environ.items():
            if key.startswith("HTTP_"):
                header_name = key[5:].replace("_", "-").title()
                headers[header_name] = value

        if self.environ.get("CONTENT_TYPE"):
            headers["Content-Type"] = self.environ["CONTENT_TYPE"]
        if self.environ.get("CONTENT_LENGTH"):
            headers["Content-Length"] = self.environ["CONTENT_LENGTH"]
        return headers

    def _parse_cookies(self) -> Dict[str, str]:
        """Parse cookies from request headers."""
        cookies = {}
        cookie_header = self.headers.get("Cookie", "")
        if cookie_header:
            for cookie in cookie_header.split(";"):
                if "=" in cookie:
                    name, value = cookie.split("=", 1)
                    cookies[name.strip()] = value.strip()
        return cookies

    @property
    def body(self) -> str:
        """Get raw request body."""
        if self._body is None:
            try:
                content_length = int(self.environ.get("CONTENT_LENGTH", 0))
            except ValueError:
                content_length = 0

            if content_length > 0:
                self._body = self.environ["wsgi.input"].read(content_length).decode("utf-8")
            else:
                self._body = ""
        return self._body

    @property
    def json(self) -> Optional[Dict[str, Any]]:
        """Get parsed JSON body."""
        if self._json is None and self.body:
            try:
                self._json = json.loads(self.body)
            except json.JSONDecodeError:
                self._json = None
        return self._json

    @property
    def query_params(self) -> Dict[str, List[str]]:
        """Get query parameters."""
        return parse_qs(self.query_string)

    @property
    def form_data(self) -> Dict[str, List[str]]:
        """Get form data from POST body."""
        if self._form is None:
            content_type = self.content_type or ""
            if "application/x-www-form-urlencoded" in content_type:
                self._form = parse_qs(self.body)
            else:
                self._form = {}
        return self._form

    @property
    def data(self) -> Union[Dict[str, Any], str]:
        """Return parsed request data for common content types."""
        if self.json is not None:
            return self.json
        if self.form_data:
            return {k: v[0] if len(v) == 1 else v for k, v in self.form_data.items()}
        return self.body

    @property
    def args(self) -> Dict[str, List[str]]:
        """Get query parameters alias for convenience."""
        return self.query_params

    @property
    def content_type(self) -> str:
        """Return the request content type."""
        return self.headers.get("Content-Type", "")

    @property
    def raw_body(self) -> bytes:
        """Get the raw request body as bytes."""
        if self._body is None:
            try:
                content_length = int(self.environ.get("CONTENT_LENGTH", 0))
            except ValueError:
                content_length = 0

            if content_length > 0:
                self._body = self.environ["wsgi.input"].read(content_length)
            else:
                self._body = b""
        return self._body

    @property
    def body(self) -> str:
        """Get raw request body."""
        if self._body is None:
            _ = self.raw_body
        if isinstance(self._body, bytes):
            try:
                return self._body.decode("utf-8")
            except UnicodeDecodeError:
                return ""
        return self._body

    def get_query_param(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a single query parameter."""
        params = self.query_params.get(key, [])
        return params[0] if params else default

    def get_form_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a single form field value."""
        form_data = self.form_data.get(key, [])
        return form_data[0] if form_data else default


class Response:
    """Represents an HTTP response."""

    def __init__(
        self,
        content: Union[str, Dict, bytes] = "",
        status: int = 200,
        headers: Optional[Dict[str, str]] = None,
        content_type: str = "text/plain",
    ):
        """
        Initialize a Response object.

        Args:
            content: Response body content
            status: HTTP status code
            headers: Additional HTTP headers
            content_type: Content-Type header value
        """
        self.status = status
        self.headers = headers or {}
        self.content_type = content_type
        self._content = content
        self.cookies: Dict[str, Dict[str, str]] = {}

    @property
    def content(self) -> Union[str, bytes]:
        """Get response content."""
        if isinstance(self._content, dict):
            return json.dumps(self._content)
        return self._content

    @content.setter
    def content(self, value: Union[str, Dict, bytes]):
        """Set response content."""
        self._content = value

    def set_cookie(
        self,
        name: str,
        value: str,
        max_age: Optional[int] = None,
        path: str = "/",
        secure: bool = False,
        http_only: bool = False,
    ):
        """
        Set a response cookie.

        Args:
            name: Cookie name
            value: Cookie value
            max_age: Cookie lifetime in seconds
            path: Cookie path
            secure: HTTPS only flag
            http_only: JavaScript inaccessible flag
        """
        self.cookies[name] = {
            "value": value,
            "path": path,
            "max_age": max_age,
            "secure": secure,
            "http_only": http_only,
        }

    def get_headers(self) -> List[Tuple[str, str]]:
        """Get all headers as list of tuples for WSGI."""
        headers = [("Content-Type", self.content_type)]
        headers.extend(self.headers.items())

        for name, cookie_data in self.cookies.items():
            cookie_str = f"{name}={cookie_data['value']}"
            if cookie_data.get("path"):
                cookie_str += f"; Path={cookie_data['path']}"
            if cookie_data.get("max_age"):
                cookie_str += f"; Max-Age={cookie_data['max_age']}"
            if cookie_data.get("secure"):
                cookie_str += "; Secure"
            if cookie_data.get("http_only"):
                cookie_str += "; HttpOnly"
            headers.append(("Set-Cookie", cookie_str))

        return headers

    def redirect(self, location: str, status: int = 302) -> None:
        """Set this response to redirect to another location."""
        self.status = status
        self.headers["Location"] = location
        self.content = ""

    def get_status_string(self) -> str:
        """Get HTTP status string."""
        status_messages = {
            200: "OK",
            201: "Created",
            204: "No Content",
            301: "Moved Permanently",
            302: "Found",
            304: "Not Modified",
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            405: "Method Not Allowed",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable",
        }
        message = status_messages.get(self.status, "Unknown")
        return f"{self.status} {message}"


class Router:
    """Handles URL routing and dispatching."""

    def __init__(self):
        """Initialize the router."""
        self.routes: Dict[str, List[Tuple[str, Callable]]] = {}
        self.before_request: List[Callable] = []
        self.after_request: List[Callable] = []

    def add_route(
        self,
        path: str,
        methods: List[str],
        handler: Callable,
    ):
        """
        Add a route to the router.

        Args:
            path: URL path (can include parameters like /users/<id>)
            methods: List of HTTP methods
            handler: Handler function
        """
        for method in methods:
            method = method.upper()
            if method not in self.routes:
                self.routes[method] = []
            self.routes[method].append((path, handler))

    def match_route(
        self, method: str, path: str
    ) -> Tuple[Optional[Callable], Dict[str, Any]]:
        """
        Match a request to a route.

        Args:
            method: HTTP method
            path: URL path

        Returns:
            Tuple of (handler, route_params)
        """
        method = method.upper()
        routes_for_method = self.routes.get(method, [])

        for route_pattern, handler in routes_for_method:
            params, match = self._match_pattern(route_pattern, path)
            if match:
                return handler, params

        return None, {}

    @staticmethod
    def _match_pattern(pattern: str, path: str) -> Tuple[Dict[str, str], bool]:
        """
        Match a URL pattern against a path.

        Args:
            pattern: Route pattern (e.g., /users/<id>/posts/<post_id>)
            path: Request path

        Returns:
            Tuple of (params_dict, is_match)
        """
        params = {}

        pattern_parts = [part for part in pattern.split("/") if part != ""]
        path_parts = [part for part in path.split("/") if part != ""]

        if pattern_parts and pattern_parts[-1].startswith("<") and pattern_parts[-1].endswith("...>"):
            base_parts = pattern_parts[:-1]
            if len(path_parts) < len(base_parts):
                return {}, False
            for pattern_part, path_part in zip(base_parts, path_parts[: len(base_parts)]):
                if pattern_part.startswith("<") and pattern_part.endswith(">"):
                    params[pattern_part[1:-1]] = unquote(path_part)
                elif pattern_part != path_part:
                    return {}, False
            wildcard_name = pattern_parts[-1][1:-4]
            params[wildcard_name] = unquote("/".join(path_parts[len(base_parts) :]))
            return params, True

        if len(pattern_parts) != len(path_parts):
            return {}, False

        for pattern_part, path_part in zip(pattern_parts, path_parts):
            if pattern_part.startswith("<") and pattern_part.endswith(">"):
                param_name = pattern_part[1:-1]
                params[param_name] = unquote(path_part)
            elif pattern_part != path_part:
                return {}, False

        return params, True


class Middleware:
    """Base class for middleware."""

    def process_request(self, request: Request) -> Optional[Response]:
        """
        Process request before handler.

        Args:
            request: Request object

        Returns:
            Response object to short-circuit, or None to continue
        """
        return None

    def process_response(self, response: Response) -> Response:
        """
        Process response after handler.

        Args:
            response: Response object

        Returns:
            Modified response object
        """
        return response


class JSONMiddleware(Middleware):
    """Middleware for automatic JSON response conversion."""

    def process_response(self, response: Response) -> Response:
        """Convert dict responses to JSON automatically."""
        if isinstance(response._content, dict):
            response.content_type = "application/json"
        return response


class CORSMiddleware(Middleware):
    """Middleware for CORS support."""

    def __init__(self, allowed_origins: List[str] = None):
        """
        Initialize CORS middleware.

        Args:
            allowed_origins: List of allowed origins (* for all)
        """
        self.allowed_origins = allowed_origins or ["*"]

    def process_response(self, response: Response) -> Response:
        """Add CORS headers."""
        origins = ", ".join(self.allowed_origins)
        response.headers["Access-Control-Allow-Origin"] = origins
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response


class Application:
    """Main web application class."""

    def __init__(self, name: str = "WebApp"):
        """
        Initialize the application.

        Args:
            name: Application name
        """
        self.name = name
        self.router = Router()
        self.middlewares: List[Middleware] = []
        self._add_default_middlewares()

    def _add_default_middlewares(self):
        """Add default middleware."""
        self.use(JSONMiddleware())
        self.use(CORSMiddleware())

    def use(self, middleware: Middleware):
        """
        Register middleware.

        Args:
            middleware: Middleware instance
        """
        self.middlewares.append(middleware)

    def route(
        self,
        path: str,
        methods: List[str] = None,
    ):
        """
        Decorator for registering routes.

        Args:
            path: URL path
            methods: HTTP methods (default: ['GET'])

        Returns:
            Decorator function
        """
        if methods is None:
            methods = ["GET"]

        def decorator(handler):
            self.router.add_route(path, methods, handler)
            return handler

        return decorator

    def get(self, path: str):
        """Decorator for GET routes."""
        return self.route(path, ["GET"])

    def post(self, path: str):
        """Decorator for POST routes."""
        return self.route(path, ["POST"])

    def put(self, path: str):
        """Decorator for PUT routes."""
        return self.route(path, ["PUT"])

    def delete(self, path: str):
        """Decorator for DELETE routes."""
        return self.route(path, ["DELETE"])

    def patch(self, path: str):
        """Decorator for PATCH routes."""
        return self.route(path, ["PATCH"])

    def options(self, path: str):
        """Decorator for OPTIONS routes."""
        return self.route(path, ["OPTIONS"])

    def any(self, path: str):
        """Decorator for routes that should handle any HTTP method."""
        return self.route(path, ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])

    def static(self, url_prefix: str, folder_path: str):
        """
        Serve static files.

        Args:
            url_prefix: URL prefix (e.g., /static)
            folder_path: Local folder path
        """

        def serve_static(request: Request) -> Response:
            sub_path = request.route_params.get("path", "")
            file_path = Path(folder_path) / sub_path.lstrip("/")
            file_path = file_path.resolve()

            if not str(file_path).startswith(str(Path(folder_path).resolve())):
                return Response("Forbidden", status=403)

            if file_path.is_file():
                with open(file_path, "rb") as f:
                    content_type, _ = mimetypes.guess_type(str(file_path))
                    return Response(
                        f.read(),
                        content_type=content_type or "application/octet-stream",
                    )

            return Response("Not Found", status=404)

        self.router.add_route(f"{url_prefix}/<path...>", ["GET"], serve_static)

    def wsgi_app(self, environ: Dict[str, Any], start_response: Callable):
        """
        WSGI application interface.

        Args:
            environ: WSGI environment
            start_response: WSGI start_response callable

        Returns:
            Response body
        """
        request = Request(environ)

        try:
            # Process request middleware
            for middleware in self.middlewares:
                response = middleware.process_request(request)
                if response:
                    break
            else:
                # Route the request
                handler, route_params = self.router.match_route(request.method, request.path)

                if handler:
                    request.route_params = route_params
                    request.path_params = route_params
                    result = handler(request)

                    if isinstance(result, Response):
                        response = result
                    elif isinstance(result, dict):
                        response = Response(result, content_type="application/json")
                    elif isinstance(result, str):
                        response = Response(result)
                    else:
                        response = Response(str(result))
                else:
                    response = Response(
                        json.dumps({"error": "Not Found"}),
                        status=404,
                        content_type="application/json",
                    )

            # Process response middleware
            for middleware in self.middlewares:
                response = middleware.process_response(response)

        except Exception as e:
            error_response = Response(
                json.dumps({"error": str(e), "traceback": traceback.format_exc()}),
                status=500,
                content_type="application/json",
            )
            response = error_response

        # Prepare WSGI response
        status_string = response.get_status_string()
        headers = response.get_headers()

        start_response(status_string, headers)

        if isinstance(response.content, bytes):
            return [response.content]
        return [response.content.encode("utf-8")]

    def run(self, host: str = "127.0.0.1", port: int = 8000, debug: bool = True):
        """
        Start the development server.

        Args:
            host: Host address
            port: Port number
            debug: Debug mode flag
        """
        print(f"Starting {self.name} on {host}:{port}")
        if debug:
            print("Debug mode: ON")
        print("Press CTRL+C to quit")

        server = make_server(host, port, self.wsgi_app)

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            server.server_close()


# Utility function for quick app creation
def create_app(name: str = "WebApp") -> Application:
    """
    Create a new web application instance.

    Args:
        name: Application name

    Returns:
        Application instance
    """
    return Application(name)