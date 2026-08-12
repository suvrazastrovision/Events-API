# Evently API Explained in Simple Words

## 1. What is this project?

Evently is a small **backend web application** for managing events.

It allows people to:

- create an account;
- log in;
- see events;
- create an event after logging in;
- say whether they will attend an event (RSVP);
- see who is attending an event.

This project is an **API**, not a normal website with pages and buttons. An API waits for requests and normally answers with data in **JSON** format.

For example, opening:

```text
GET http://localhost:5000/api/health
```

returns:

```json
{
  "status": "healthy"
}
```

That answer tells another program—or a person testing the API—that the server is alive.

## 2. What do the important words mean?

### Backend

The backend runs behind the scenes. It receives requests, checks rules, reads or changes the database, and sends responses.

### Flask

Flask is a Python web framework. It provides the tools needed to start a web server and connect URLs to Python functions.

### API endpoint

An endpoint is a URL plus an HTTP method that performs one job.

Examples:

- `GET /api/events` means “give me the events.”
- `POST /api/events` means “create a new event.”
- `POST /api/auth/login` means “check my login details.”

### JSON

JSON is a common text format for exchanging structured data. It looks similar to a Python dictionary:

```json
{
  "title": "Python Meetup",
  "capacity": 50
}
```

### Database

The database permanently stores users, events, and RSVPs. This project uses **SQLite**, which keeps the data in a local file.

### JWT token

A JWT token is a temporary digital proof that a user has logged in. After a successful login, the API returns a token. The client sends that token when it calls an endpoint that requires authentication.

### Blueprint

A Flask blueprint is a way to split a large application into smaller route files. Instead of putting every endpoint in `app.py`, this project groups them into authentication, event, and RSVP files.

## 3. How the files work together

```text
app.py
  |
  +-- config.py          Application settings
  +-- models.py          Database and table definitions
  +-- routes/auth.py     Registration and login endpoints
  +-- routes/events.py   Event endpoints
  +-- routes/rsvps.py    RSVP endpoints
  +-- openapi.yaml       Description of the API for Swagger UI
  +-- instance/events.db SQLite database file
```

`app.py` is the central starting point. It creates the Flask application and connects all the other pieces.

## 4. What happens when the application starts?

When you run:

```powershell
python app.py
```

the following sequence happens:

1. Python loads the imports at the top of `app.py`.
2. Python reaches the final `if __name__ == '__main__':` block.
3. `create_app()` builds and configures the Flask application.
4. The database, CORS support, and JWT support are connected.
5. Swagger UI and all route blueprints are registered.
6. Missing database tables are created.
7. Flask starts listening for requests on port `5000`.

The application then stays running and waits for requests.

## 5. Detailed explanation of `app.py`

### Imports

```python
from flask import Flask, jsonify, send_from_directory
```

- `Flask` creates the main application object.
- `jsonify` turns Python dictionaries and lists into JSON responses.
- `send_from_directory` sends an existing file to the client. Here it is used for `openapi.yaml`.

```python
from flask_cors import CORS
```

This enables Cross-Origin Resource Sharing. In simple terms, it allows a frontend running on another address or port to call this API from a browser.

```python
from flask_jwt_extended import JWTManager
```

This adds support for JWT login tokens.

```python
from flask_swagger_ui import get_swaggerui_blueprint
```

This provides the interactive API documentation shown at `/apidocs`.

```python
from config import Config
from models import db
```

- `Config` contains application settings.
- `db` is the shared SQLAlchemy database object.

```python
from routes.auth import auth_bp
from routes.events import events_bp
from routes.rsvps import rsvps_bp
```

These import the three groups of endpoints so that `app.py` can attach them to the application.

```python
import yaml
import os
```

- `os` is used to work with file paths and environment variables.
- `yaml` is currently imported but is not actually used in `app.py`.

### The application factory

```python
def create_app():
```

This function builds and returns the application. This pattern is called an **application factory**.

Keeping creation inside a function makes the app easier to test and reuse. Tests can call `create_app()` without starting a real server.

### Creating the Flask application

```python
app = Flask(__name__)
```

This creates the main Flask application object.

`__name__` tells Flask where this Python module lives, which helps Flask find project resources.

### Loading settings

```python
app.config.from_object(Config)
```

This copies settings from the `Config` class in `config.py` into the Flask application.

Those settings include:

- the SQLite database location;
- the Flask secret key;
- the JWT secret key;
- the one-hour JWT expiration time.

### Connecting extensions

```python
db.init_app(app)
CORS(app)
jwt = JWTManager(app)
```

These lines connect extra features to this particular Flask application:

- SQLAlchemy provides database access.
- CORS permits browser calls from other origins.
- JWTManager handles authentication tokens.

The variable `jwt` keeps the created JWT manager, although this file does not use it again directly.

### Configuring Swagger UI

```python
SWAGGER_URL = '/apidocs'
API_URL = '/api/openapi.yaml'
```

- `SWAGGER_URL` is where people can view the interactive documentation.
- `API_URL` is where Swagger reads the formal description of the endpoints.

```python
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "Evently API"}
)
```

This builds a ready-made Swagger documentation section named “Evently API.”

```python
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
```

This attaches Swagger UI to the application at:

```text
http://localhost:5000/apidocs
```

### Serving the OpenAPI file

```python
@app.route('/api/openapi.yaml')
def serve_openapi():
    return send_from_directory(..., 'openapi.yaml')
```

`@app.route(...)` tells Flask which URL should call the function below it.

When someone requests `/api/openapi.yaml`, Flask sends the project's `openapi.yaml` file. Swagger UI reads that file to learn what endpoints exist, what input they accept, and what output they return.

### Registering the application routes

```python
app.register_blueprint(auth_bp)
app.register_blueprint(events_bp)
app.register_blueprint(rsvps_bp)
```

These lines attach the endpoint groups imported from the `routes` directory.

After registration, Flask knows about URLs such as:

- `/api/auth/register`;
- `/api/auth/login`;
- `/api/events`;
- `/api/rsvps/event/1`.

Without these three lines, the route files would exist but Flask would not use them.

### Creating database tables

```python
with app.app_context():
    db.create_all()
```

Some database work needs access to the current Flask application. `app.app_context()` temporarily provides that connection.

`db.create_all()` creates any missing tables described in `models.py`:

- `user`;
- `event`;
- `rsvp`.

It does not normally delete existing tables or existing data.

For a small demonstration project this is convenient. Larger production systems usually use database migration tools instead.

### The root endpoint

```python
@app.route('/', methods=['GET'])
def root():
```

This connects a normal `GET /` request to the `root()` function.

The function returns JSON containing:

- the API name;
- its version;
- a description;
- documentation links;
- a short endpoint directory.

The `200` after the dictionary is the HTTP status code. `200 OK` means the request succeeded.

### The health endpoint

```python
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200
```

This is a simple check used to confirm that Flask can receive and answer requests. It does not deeply test the database or every feature; it only proves that the application is responding.

### Returning the finished application

```python
return app
```

After all configuration is finished, `create_app()` gives the completed application object back to its caller.

### Starting the development server

```python
if __name__ == '__main__':
```

This condition is true when you run `python app.py` directly. It is false when another Python module merely imports `app.py`.

That distinction prevents the server from starting accidentally during an import or a test.

```python
app = create_app()
```

This builds the application.

```python
debug = os.environ.get('FLASK_DEBUG', '').lower() in {'1', 'true', 'yes'}
```

This reads the optional `FLASK_DEBUG` environment variable. Debug mode is enabled only if its value is `1`, `true`, or `yes`, ignoring letter case.

Debug mode is useful during development because it provides more error information. It should not be enabled in production because it can expose sensitive details.

```python
port = int(os.environ.get('PORT', '5000'))
```

This reads the optional `PORT` environment variable and converts it to a number. If `PORT` is missing, it uses `5000`.

Examples:

- `python app.py` uses port `5000`.
- Setting `PORT=8000` before starting would use port `8000`.

```python
app.run(debug=debug, host='0.0.0.0', port=port)
```

This starts Flask's development web server.

- `debug=debug` uses the debug choice described above.
- `host='0.0.0.0'` listens on all network interfaces, not only localhost.
- `port=port` normally listens on port `5000`.

`0.0.0.0` is a listening instruction, not normally the address typed into a browser. On the same computer, use:

```text
http://localhost:5000
```

## 6. What the other Python files do

### `config.py`

This file stores settings:

- `SECRET_KEY` supports Flask security features.
- `SQLALCHEMY_DATABASE_URI` selects the database.
- `SQLALCHEMY_TRACK_MODIFICATIONS = False` disables unnecessary tracking overhead.
- `JWT_SECRET_KEY` signs and verifies login tokens.
- `JWT_ACCESS_TOKEN_EXPIRES` makes tokens expire after one hour.

Environment variables can replace the default secrets and database URL. The built-in secret values are convenient for local learning but must be changed for a real production deployment.

### `models.py`

This file describes the database tables as Python classes.

#### `User`

Stores a username, securely hashed password, admin flag, and creation time.

The real password is not stored directly. `set_password()` creates a password hash, and `check_password()` checks a login attempt against it.

#### `Event`

Stores an event's title, description, date, location, capacity, access rules, creator, and creation time.

#### `RSVP`

Connects a user to an event and records whether the user is attending.

The `to_dict()` methods convert database objects into ordinary dictionaries that Flask can return as JSON.

### `routes/auth.py`

This file handles accounts:

- `POST /api/auth/register` creates a user.
- `POST /api/auth/login` checks the username and password and returns a JWT token.

For demonstration purposes, the first registered user automatically becomes an administrator.

### `routes/events.py`

This file handles events:

- `GET /api/events` returns all events.
- `GET /api/events/<event_id>` returns one event.
- `POST /api/events` creates an event and requires a valid JWT token.

### `routes/rsvps.py`

This file handles attendance:

- `POST /api/rsvps/event/<event_id>` creates or updates an RSVP.
- `GET /api/rsvps/event/<event_id>` returns RSVPs and attendance totals.

The RSVP rules depend on the event:

- anyone can RSVP to a public event;
- a logged-in user is required for a private event;
- an administrator is required for an admin-only event;
- nobody new can attend after a limited-capacity event becomes full.

## 7. Example: how a request travels through the app

Imagine that a client sends:

```text
GET http://localhost:5000/api/events
```

The flow is:

```text
Client
  -> Flask server on port 5000
  -> events blueprint
  -> get_events() function
  -> Event database query
  -> Event objects converted to dictionaries
  -> JSON response returned to the client
```

For a protected request such as creating an event, Flask-JWT-Extended first checks the JWT token. If it is valid, the route creates the database record. If it is missing or invalid, the request is rejected.

## 8. Understanding HTTP methods and status codes

This project mainly uses two HTTP methods:

- `GET` reads information and should not create new data.
- `POST` submits information and can create or update data.

Common response status codes in this app are:

- `200 OK`: the request succeeded.
- `201 Created`: a new user, event, or RSVP was created.
- `400 Bad Request`: required or valid input was missing.
- `401 Unauthorized`: login is required or credentials are wrong.
- `403 Forbidden`: the user is logged in but lacks admin permission.
- `404 Not Found`: the requested event or other resource does not exist.

## 9. Why port 5000 matters

A computer can run many network programs at once. A **port** helps the computer send each request to the correct program.

This application normally uses port `5000`, so its local address is:

```text
http://localhost:5000
```

Only one service should own the same exact address and port combination. Earlier, another Python application was listening specifically on `127.0.0.1:5000`. That service could receive localhost requests before Evently did, which caused Evently's `/api/health` URL to return the other application's `404 Not Found` response.

After the conflicting service was stopped, requests to port `5000` reached Evently and `/api/health` returned `200` with `{"status":"healthy"}`.

## 10. A complete beginner testing sequence

1. Start the application:

   ```powershell
   .\.venv\Scripts\python.exe app.py
   ```

2. Open the basic API information:

   ```text
   http://localhost:5000/
   ```

3. Open the interactive documentation:

   ```text
   http://localhost:5000/apidocs
   ```

4. Register a user using `POST /api/auth/register`.

5. Log in using `POST /api/auth/login` and copy the returned token.

6. In Swagger UI, click **Authorize** and enter:

   ```text
   Bearer YOUR_TOKEN_HERE
   ```

7. Create an event using `POST /api/events`.

8. View the events using `GET /api/events`.

9. RSVP using `POST /api/rsvps/event/<event_id>`.

## 11. Important limitations

This is a development and learning application. Before using something like this in production, it would need additional work, including:

- strong secrets supplied through environment variables;
- restricted CORS rules instead of allowing every origin;
- stronger and more consistent input validation;
- database migrations;
- rate limiting;
- production error handling and logging;
- a production WSGI server instead of Flask's development server;
- more complete authorization and privacy rules;
- automated tests.

## 12. The shortest possible summary

`app.py` is the project's **assembler and starter**. It creates the Flask application, loads settings, connects the database and authentication tools, attaches all endpoint groups, creates missing database tables, adds documentation and health routes, and starts the development server—normally on port `5000`.
