import pytest

import os
import subprocess
import sys
import time
import uuid

import requests

from app import create_app
from models import db


BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000").rstrip("/")


@pytest.fixture(scope="session")
def live_server():
    """Use an existing API server or start one for the integration tests."""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=1)
        if response.status_code == 200:
            yield BASE_URL
            return
    except requests.RequestException:
        pass

    server = subprocess.Popen([sys.executable, "app.py"])
    try:
        for _ in range(30):
            try:
                response = requests.get(f"{BASE_URL}/api/health", timeout=1)
                if response.status_code == 200:
                    break
            except requests.RequestException:
                time.sleep(0.2)
        else:
            pytest.fail(f"API server did not become ready at {BASE_URL}")

        yield BASE_URL
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)


@pytest.fixture()
def live_auth_token(live_server):
    """Register and log in a unique user through the running API."""
    credentials = {
        "username": f"integration-{uuid.uuid4().hex}",
        "password": "password123",
    }
    register_response = requests.post(
        f"{live_server}/api/auth/register", json=credentials, timeout=5
    )
    assert register_response.status_code == 201

    login_response = requests.post(
        f"{live_server}/api/auth/login", json=credentials, timeout=5
    )
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


@pytest.fixture()
def app():
    """Create an isolated application and database for each test."""
    test_app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "JWT_SECRET_KEY": "test-jwt-secret",
        }
    )
    yield test_app
    with test_app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_headers(client):
    credentials = {"username": "testuser", "password": "password123"}
    client.post("/api/auth/register", json=credentials)
    response = client.post("/api/auth/login", json=credentials)
    token = response.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}




