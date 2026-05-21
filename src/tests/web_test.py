"""
Unit tests for opalib.web framework.

Tests core functionality including routing, request/response handling, and middleware.
"""

import unittest
from io import BytesIO
from src.web import (
    Application,
    Request,
    Response,
    Router,
    Middleware,
    JSONMiddleware,
    CORSMiddleware,
)


class TestRequest(unittest.TestCase):
    """Test Request class."""

    def test_request_creation(self):
        """Test basic request creation."""
        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/users/123",
            "QUERY_STRING": "page=1&limit=10",
            "HTTP_USER_AGENT": "TestClient",
            "wsgi.input": BytesIO(b""),
            "CONTENT_LENGTH": "0",
        }

        request = Request(environ)

        self.assertEqual(request.method, "GET")
        self.assertEqual(request.path, "/users/123")
        self.assertEqual(request.query_string, "page=1&limit=10")
        self.assertEqual(request.headers.get("User-Agent"), "TestClient")

    def test_request_json_body(self):
        """Test JSON body parsing."""
        json_data = b'{"name": "John", "age": 30}'
        environ = {
            "REQUEST_METHOD": "POST",
            "PATH_INFO": "/users",
            "QUERY_STRING": "",
            "wsgi.input": BytesIO(json_data),
            "CONTENT_LENGTH": str(len(json_data)),
        }

        request = Request(environ)
        self.assertEqual(request.json["name"], "John")
        self.assertEqual(request.json["age"], 30)

    def test_request_query_params(self):
        """Test query parameter parsing."""
        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/search",
            "QUERY_STRING": "q=python&limit=20",
            "wsgi.input": BytesIO(b""),
            "CONTENT_LENGTH": "0",
        }

        request = Request(environ)
        self.assertEqual(request.get_query_param("q"), "python")
        self.assertEqual(request.get_query_param("limit"), "20")
        self.assertEqual(request.get_query_param("missing", "default"), "default")

    def test_request_data_property(self):
        """Test request body data parsing for JSON and form data."""
        json_data = b'{"name": "John", "age": 30}'
        json_environ = {
            "REQUEST_METHOD": "POST",
            "PATH_INFO": "/users",
            "QUERY_STRING": "",
            "CONTENT_TYPE": "application/json",
            "wsgi.input": BytesIO(json_data),
            "CONTENT_LENGTH": str(len(json_data)),
        }

        request = Request(json_environ)
        self.assertEqual(request.data["name"], "John")
        self.assertEqual(request.data["age"], 30)

        form_data = b"name=Jane&age=25"
        form_environ = {
            "REQUEST_METHOD": "POST",
            "PATH_INFO": "/users",
            "QUERY_STRING": "",
            "CONTENT_TYPE": "application/x-www-form-urlencoded",
            "wsgi.input": BytesIO(form_data),
            "CONTENT_LENGTH": str(len(form_data)),
        }

        request = Request(form_environ)
        self.assertEqual(request.data["name"], "Jane")
        self.assertEqual(request.data["age"], "25")

    def test_request_cookies(self):
        """Test cookie parsing."""
        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/",
            "QUERY_STRING": "",
            "HTTP_COOKIE": "session_id=abc123; user=john",
            "wsgi.input": BytesIO(b""),
            "CONTENT_LENGTH": "0",
        }

        request = Request(environ)
        self.assertEqual(request.cookies.get("session_id"), "abc123")
        self.assertEqual(request.cookies.get("user"), "john")


class TestResponse(unittest.TestCase):
    """Test Response class."""

    def test_response_creation(self):
        """Test basic response creation."""
        response = Response("Hello", status=200, content_type="text/plain")

        self.assertEqual(response.status, 200)
        self.assertEqual(response.content, "Hello")
        self.assertEqual(response.content_type, "text/plain")

    def test_response_json(self):
        """Test JSON response."""
        data = {"message": "success"}
        response = Response(data, content_type="application/json")

        self.assertEqual(response.content, '{"message": "success"}')

    def test_response_cookie(self):
        """Test cookie setting."""
        response = Response("test")
        response.set_cookie("session", "abc123", path="/", http_only=True)

        headers = response.get_headers()
        cookie_headers = [h for h in headers if h[0] == "Set-Cookie"]

        self.assertEqual(len(cookie_headers), 1)
        self.assertIn("session=abc123", cookie_headers[0][1])
        self.assertIn("HttpOnly", cookie_headers[0][1])

    def test_response_status_string(self):
        """Test status string generation."""
        response = Response("test", status=404)
        self.assertEqual(response.get_status_string(), "404 Not Found")

        response = Response("test", status=201)
        self.assertEqual(response.get_status_string(), "201 Created")


class TestRouter(unittest.TestCase):
    """Test Router class."""

    def setUp(self):
        """Set up test fixtures."""
        self.router = Router()

    def test_simple_route(self):
        """Test simple route matching."""

        def handler(request):
            return "ok"

        self.router.add_route("/", ["GET"], handler)
        matched_handler, params = self.router.match_route("GET", "/")

        self.assertIsNotNone(matched_handler)
        self.assertEqual(params, {})

    def test_parametrized_route(self):
        """Test route with parameters."""

        def handler(request):
            return "ok"

        self.router.add_route("/users/<user_id>", ["GET"], handler)
        matched_handler, params = self.router.match_route("GET", "/users/123")

        self.assertIsNotNone(matched_handler)
        self.assertEqual(params["user_id"], "123")

    def test_multiple_parameters(self):
        """Test route with multiple parameters."""

        def handler(request):
            return "ok"

        self.router.add_route("/posts/<post_id>/comments/<comment_id>", ["GET"], handler)
        matched_handler, params = self.router.match_route(
            "GET", "/posts/456/comments/789"
        )

        self.assertIsNotNone(matched_handler)
        self.assertEqual(params["post_id"], "456")
        self.assertEqual(params["comment_id"], "789")

    def test_method_matching(self):
        """Test HTTP method matching."""

        def get_handler(request):
            return "get"

        def post_handler(request):
            return "post"

        self.router.add_route("/items", ["GET"], get_handler)
        self.router.add_route("/items", ["POST"], post_handler)

        get_matched, _ = self.router.match_route("GET", "/items")
        post_matched, _ = self.router.match_route("POST", "/items")

        self.assertEqual(get_matched(None), "get")
        self.assertEqual(post_matched(None), "post")

    def test_wildcard_route_matching(self):
        """Test catch-all route matching using wildcard path segments."""

        def static_handler(request):
            return "ok"

        self.router.add_route("/static/<path...>", ["GET"], static_handler)
        matched_handler, params = self.router.match_route("GET", "/static/css/app.css")

        self.assertIsNotNone(matched_handler)
        self.assertEqual(params["path"], "css/app.css")

    def test_no_route_match(self):
        """Test when no route matches."""
        handler, params = self.router.match_route("GET", "/nonexistent")

        self.assertIsNone(handler)
        self.assertEqual(params, {})


class TestMiddleware(unittest.TestCase):
    """Test Middleware functionality."""

    def test_json_middleware(self):
        """Test JSON middleware auto-conversion."""
        middleware = JSONMiddleware()
        response = Response({"message": "test"}, content_type="text/plain")

        processed = middleware.process_response(response)

        self.assertEqual(processed.content_type, "application/json")

    def test_cors_middleware(self):
        """Test CORS middleware."""
        middleware = CORSMiddleware(allowed_origins=["http://example.com"])
        response = Response("test")

        processed = middleware.process_response(response)

        self.assertIn("Access-Control-Allow-Origin", processed.headers)
        self.assertIn("Access-Control-Allow-Methods", processed.headers)


class TestApplication(unittest.TestCase):
    """Test Application class."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = Application("TestApp")

    def test_app_creation(self):
        """Test application creation."""
        self.assertEqual(self.app.name, "TestApp")
        self.assertIsNotNone(self.app.router)
        self.assertGreater(len(self.app.middlewares), 0)

    def test_route_decorator(self):
        """Test route decorator."""

        @self.app.get("/test")
        def test_handler(request):
            return {"status": "ok"}

        handler, _ = self.app.router.match_route("GET", "/test")
        self.assertIsNotNone(handler)

    def test_post_decorator(self):
        """Test POST decorator."""

        @self.app.post("/submit")
        def submit_handler(request):
            return {"status": "submitted"}

        handler, _ = self.app.router.match_route("POST", "/submit")
        self.assertIsNotNone(handler)

    def test_wsgi_app_not_found(self):
        """Test WSGI app 404 response."""
        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/nonexistent",
            "QUERY_STRING": "",
            "wsgi.input": BytesIO(b""),
            "CONTENT_LENGTH": "0",
        }

        responses = []

        def start_response(status, headers):
            responses.append({"status": status, "headers": headers})

        body = self.app.wsgi_app(environ, start_response)
        status = responses[0]["status"]

        self.assertIn("404", status)

    def test_wsgi_app_with_route(self):
        """Test WSGI app with matching route."""

        @self.app.get("/hello")
        def hello(request):
            return {"message": "Hello"}

        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/hello",
            "QUERY_STRING": "",
            "wsgi.input": BytesIO(b""),
            "CONTENT_LENGTH": "0",
        }

        responses = []

        def start_response(status, headers):
            responses.append({"status": status, "headers": headers})

        body = self.app.wsgi_app(environ, start_response)
        status = responses[0]["status"]

        self.assertIn("200", status)

    def test_wsgi_app_redirect(self):
        """Test redirect response generation."""

        @self.app.get("/redirect")
        def redirect(request):
            response = Response("", status=302)
            response.redirect("/hello")
            return response

        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/redirect",
            "QUERY_STRING": "",
            "wsgi.input": BytesIO(b""),
            "CONTENT_LENGTH": "0",
        }

        responses = []

        def start_response(status, headers):
            responses.append({"status": status, "headers": headers})

        _ = self.app.wsgi_app(environ, start_response)
        status = responses[0]["status"]
        headers = dict(responses[0]["headers"])

        self.assertIn("302", status)
        self.assertEqual(headers.get("Location"), "/hello")

    def test_wsgi_app_json_body(self):
        """Test WSGI app with JSON POST."""

        @self.app.post("/users")
        def create_user(request):
            data = request.json
            return {"id": 1, "name": data.get("name")}

        json_data = b'{"name":"John"}'
        environ = {
            "REQUEST_METHOD": "POST",
            "PATH_INFO": "/users",
            "QUERY_STRING": "",
            "CONTENT_TYPE": "application/json",
            "wsgi.input": BytesIO(json_data),
            "CONTENT_LENGTH": str(len(json_data)),
        }

        responses = []

        def start_response(status, headers):
            responses.append({"status": status, "headers": headers})

        body = self.app.wsgi_app(environ, start_response)
        status = responses[0]["status"]

        self.assertIn("200", status)


if __name__ == "__main__":
    unittest.main()
