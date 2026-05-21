# opalib.web - Custom Web Framework Documentation

A fully custom web framework built from scratch (no Flask, Django, or FastAPI) for building web applications in Python.

## Features

✅ **Request/Response Handling** - Full HTTP request parsing and response building  
✅ **Routing System** - URL patterns with parameters  
✅ **HTTP Methods** - GET, POST, PUT, DELETE, PATCH support  
✅ **Middleware System** - Request/response processing pipeline  
✅ **CORS Support** - Cross-Origin Resource Sharing built-in  
✅ **JSON Handling** - Automatic JSON conversion  
✅ **Query Parameters** - Easy query string parsing  
✅ **Form Data** - Form submission handling  
✅ **Cookies** - Cookie setting and parsing  
✅ **Static Files** - Serve static files  
✅ **Custom Middleware** - Create your own middleware  
✅ **Development Server** - Built-in WSGI server  

## Quick Start

### Installation

```bash
pip install opalib
```

### Basic Application

```python
from src.web import create_app

app = create_app("MyApp")

@app.get("/")
def home(request):
    return {"message": "Hello, World!"}

if __name__ == "__main__":
    app.run()
```

Visit `http://localhost:8000/` to see the response.

## Core Components

### 1. Request Object

The `Request` object contains all HTTP request information.

```python
@app.post("/users")
def create_user(request):
    # Headers
    user_agent = request.headers.get("User-Agent")
    
    # Query parameters
    page = request.get_query_param("page", "1")
    
    # JSON body
    data = request.json  # {"name": "John", "email": "john@example.com"}
    
    # Form data
    username = request.get_form_value("username")
    
    # Cookies
    session_id = request.cookies.get("session_id")
    
    # Route parameters
    user_id = request.route_params.get("user_id")
    
    return {"status": "created"}
```

**Request Properties:**
- `request.method` - HTTP method (GET, POST, etc.)
- `request.path` - Request path
- `request.headers` - Dictionary of headers
- `request.cookies` - Dictionary of cookies
- `request.body` - Raw request body
- `request.json` - Parsed JSON body
- `request.query_params` - Query parameters dictionary
- `request.form_data` - Form data dictionary
- `request.route_params` - URL parameters from route

### 2. Response Object

The `Response` object represents the HTTP response.

```python
from src.web import Response

@app.get("/custom-response")
def custom(request):
    response = Response(
        content={"status": "success"},
        status=200,
        content_type="application/json"
    )
    response.set_cookie("session", "abc123", http_only=True)
    response.headers["X-Custom"] = "value"
    return response
```

**Response Methods:**
- `set_cookie(name, value, max_age, path, secure, http_only)` - Set a cookie
- `response.headers[key] = value` - Add custom headers

### 3. Routing

#### Simple Routes

```python
@app.get("/")
def home(request):
    return "Home page"

@app.post("/submit")
def submit(request):
    return {"status": "submitted"}
```

#### URL Parameters

```python
@app.get("/users/<user_id>")
def get_user(request):
    user_id = request.route_params["user_id"]
    return {"user_id": user_id}

@app.get("/posts/<post_id>/comments/<comment_id>")
def get_comment(request):
    post_id = request.route_params["post_id"]
    comment_id = request.route_params["comment_id"]
    return {"post_id": post_id, "comment_id": comment_id}
```

#### HTTP Methods

```python
@app.get("/items")
def list_items(request):
    return {"items": []}

@app.post("/items")
def create_item(request):
    return {"status": "created"}, 201

@app.put("/items/<item_id>")
def update_item(request):
    return {"status": "updated"}

@app.delete("/items/<item_id>")
def delete_item(request):
    return {"status": "deleted"}

@app.patch("/items/<item_id>")
def patch_item(request):
    return {"status": "patched"}
```

### 4. Query Parameters

```python
@app.get("/search")
def search(request):
    query = request.get_query_param("q", "")
    limit = request.get_query_param("limit", "10")
    offset = request.get_query_param("offset", "0")
    
    return {
        "query": query,
        "limit": limit,
        "offset": offset
    }
```

URL: `/search?q=python&limit=20&offset=10`

### 5. Form Data

```python
@app.post("/login")
def login(request):
    username = request.get_form_value("username")
    password = request.get_form_value("password")
    
    if username == "admin" and password == "secret":
        return {"status": "logged in"}
    return {"error": "invalid credentials"}, 401
```

### 6. JSON Requests

```python
@app.post("/users")
def create_user(request):
    data = request.json  # Automatically parsed from JSON body
    
    name = data.get("name")
    email = data.get("email")
    
    return {"id": 123, "name": name, "email": email}, 201
```

Request body:
```json
{
    "name": "John Doe",
    "email": "john@example.com"
}
```

### 7. Response Types

```python
# JSON response (automatically converted)
@app.get("/json")
def json_response(request):
    return {"message": "Hello"}

# String response
@app.get("/text")
def text_response(request):
    return "Hello, World!"

# HTML response
@app.get("/html")
def html_response(request):
    return Response(
        "<h1>Hello</h1>",
        content_type="text/html"
    )

# Custom status code
@app.get("/created")
def created_response(request):
    return Response(
        {"id": 123},
        status=201,
        content_type="application/json"
    )
```

### 8. Cookies

```python
@app.get("/set-cookie")
def set_cookie(request):
    response = Response({"status": "ok"}, content_type="application/json")
    response.set_cookie(
        name="session_id",
        value="abc123xyz",
        path="/",
        http_only=True,
        max_age=3600
    )
    return response

@app.get("/read-cookie")
def read_cookie(request):
    session_id = request.cookies.get("session_id")
    return {"session_id": session_id}
```

### 9. Middleware

#### Using Built-in Middleware

```python
from src.web import create_app, JSONMiddleware, CORSMiddleware

app = create_app("MyApp")

# Already included by default:
# - JSONMiddleware (auto-converts dict to JSON)
# - CORSMiddleware (adds CORS headers)
```

#### Creating Custom Middleware

```python
from src.web import Middleware, Request, Response

class LoggingMiddleware(Middleware):
    def process_request(self, request: Request):
        print(f"{request.method} {request.path}")
        return None  # Continue to handler
    
    def process_response(self, response: Response):
        print(f"Response status: {response.status}")
        return response

app.use(LoggingMiddleware())
```

#### Request/Response Processing

```python
class AuthMiddleware(Middleware):
    def process_request(self, request):
        # Short-circuit if unauthorized
        if request.headers.get("Authorization") != "Bearer token123":
            return Response(
                {"error": "unauthorized"},
                status=401,
                content_type="application/json"
            )
        return None  # Continue to handler
    
    def process_response(self, response):
        response.headers["X-Processed"] = "true"
        return response

app.use(AuthMiddleware())
```

### 10. Static Files

```python
# Serve files from a folder
app.static("/static", "./static")

# Now access: http://localhost:8000/static/style.css
```

### 11. Custom Headers

```python
@app.get("/api/data")
def api_data(request):
    response = Response(
        {"data": "value"},
        content_type="application/json"
    )
    response.headers["X-API-Version"] = "1.0"
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Custom-Header"] = "custom-value"
    return response
```

## Error Handling

```python
@app.get("/divide/<a>/<b>")
def divide(request):
    try:
        a = int(request.route_params["a"])
        b = int(request.route_params["b"])
        result = a / b
        return {"result": result}
    except ZeroDivisionError:
        return Response(
            {"error": "Cannot divide by zero"},
            status=400,
            content_type="application/json"
        )
    except ValueError:
        return Response(
            {"error": "Invalid numbers"},
            status=400,
            content_type="application/json"
        )
```

## Running the Server

```python
if __name__ == "__main__":
    # Start development server on localhost:8000
    app.run(host="127.0.0.1", port=8000, debug=True)
    
    # Or customize:
    # app.run(host="0.0.0.0", port=5000, debug=False)
```

## Complete Example

See `example_web_app.py` for a comprehensive example with all features.

```bash
python example_web_app.py
```

Then test endpoints:

```bash
# GET request
curl http://localhost:8000/

# GET with parameters
curl "http://localhost:8000/hello?name=John"

# GET with URL params
curl http://localhost:8000/users/123

# POST with JSON
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"name":"John","email":"john@example.com"}'

# PUT request
curl -X PUT http://localhost:8000/users/123 \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane"}'

# DELETE request
curl -X DELETE http://localhost:8000/users/123
```

## Architecture

### WSGI Compatibility

The framework is fully compatible with WSGI servers:

```python
# With gunicorn
# gunicorn 'example_web_app:app.wsgi_app'

# With other WSGI servers
wsgi_app = app.wsgi_app
```

### Request Flow

1. WSGI server receives HTTP request
2. Request object is created from WSGI environ
3. Middleware `process_request()` methods run
4. Router matches URL to handler
5. Handler function executes
6. Middleware `process_response()` methods run
7. Response is converted to WSGI format
8. Client receives response

## Comparison with Flask

| Feature | opalib.web | Flask |
|---------|-----------|-------|
| Built from scratch | ✅ Yes | ❌ No (uses Werkzeug) |
| Routing | ✅ Custom | ✅ Werkzeug |
| Middleware | ✅ Custom | ✅ Built-in |
| CORS | ✅ Built-in | ❌ Extension needed |
| Size | ✅ Lightweight | ❌ Larger |
| Learning | ✅ Full transparency | ❌ Black box dependencies |

## Limitations

- No ORM integration (use SQLAlchemy separately)
- No template engine (render HTML manually or use Jinja2)
- No session management (implement using cookies)
- No authentication (implement using middleware)
- Development server only (use production WSGI server like Gunicorn)

## Future Enhancements

- [ ] SSL/TLS support
- [ ] Request timeout handling
- [ ] Rate limiting middleware
- [ ] Built-in authentication
- [ ] WebSocket support
- [ ] Hot reload in debug mode
- [ ] Request logging middleware
- [ ] File upload handling
