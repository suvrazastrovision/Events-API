import requests
import uuid


def test_health_endpoint_returns_healthy(live_server):
    response = requests.get(f"{live_server}/api/health", timeout=5)
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_live_user_registration_succeeds(live_server):
    credentials = {
        "username": f"register-{uuid.uuid4().hex}",
        "password": "password123",
    }
    response = requests.post(
        f"{live_server}/api/auth/register", json=credentials, timeout=5
    )

    assert response.status_code == 201
    assert response.json()["user"]["username"] == credentials["username"]


def test_live_user_login_returns_token(live_server):
    credentials = {
        "username": f"login-{uuid.uuid4().hex}",
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
    assert login_response.json()["access_token"]


def test_create_public_event_requires_auth_and_succeeds_with_token(
    live_server, live_auth_token
):
    event = {
        "title": "Live Integration Workshop",
        "description": "Created through the running Events API",
        "date": "2026-10-15T18:30:00",
        "location": "Berlin",
        "capacity": 25,
        "is_public": True,
        "requires_admin": False,
    }
    unauthorized_response = requests.post(
        f"{live_server}/api/events", json=event, timeout=5
    )
    assert unauthorized_response.status_code == 401

    authorized_response = requests.post(
        f"{live_server}/api/events",
        json=event,
        headers={"Authorization": f"Bearer {live_auth_token}"},
        timeout=5,
    )
    assert authorized_response.status_code == 201
    created_event = authorized_response.json()
    assert created_event["title"] == event["title"]
    assert created_event["description"] == event["description"]
    assert created_event["date"] == event["date"]
    assert created_event["location"] == event["location"]
    assert created_event["capacity"] == event["capacity"]
    assert created_event["is_public"] is True


def test_rsvp_to_public_event_succeeds_without_auth(live_server, live_auth_token):
    event_response = requests.post(
        f"{live_server}/api/events",
        json={
            "title": "Public RSVP Event",
            "date": "2026-11-01T19:00:00",
            "is_public": True,
        },
        headers={"Authorization": f"Bearer {live_auth_token}"},
        timeout=5,
    )
    assert event_response.status_code == 201
    event_id = event_response.json()["id"]

    rsvp_response = requests.post(
        f"{live_server}/api/rsvps/event/{event_id}",
        json={"attending": True},
        timeout=5,
    )

    assert rsvp_response.status_code in (200, 201)
    assert rsvp_response.json()["event_id"] == event_id


def test_register_and_login(client):
    credentials = {"username": "alice", "password": "password123"}
    register_response = client.post("/api/auth/register", json=credentials)
    login_response = client.post("/api/auth/login", json=credentials)
    assert register_response.status_code == 201
    assert register_response.get_json()["user"]["is_admin"] is True
    assert login_response.status_code == 200
    assert "access_token" in login_response.get_json()


def test_duplicate_username_is_rejected(client):
    credentials = {"username": "alice", "password": "password123"}
    client.post("/api/auth/register", json=credentials)
    response = client.post("/api/auth/register", json=credentials)
    assert response.status_code == 400
    assert response.get_json()["error"] == "Username already exists"


def test_create_event_requires_authentication(client):
    response = client.post(
        "/api/events",
        json={"title": "Workshop", "date": "2026-09-01T18:00:00"},
    )
    assert response.status_code == 401


def test_authenticated_user_can_create_and_list_event(client, auth_headers):
    create_response = client.post(
        "/api/events",
        headers=auth_headers,
        json={"title": "Python Workshop", "date": "2026-09-01T18:00:00", "capacity": 20},
    )
    list_response = client.get("/api/events")
    assert create_response.status_code == 201
    assert create_response.get_json()["title"] == "Python Workshop"
    assert list_response.status_code == 200
    assert len(list_response.get_json()) == 1


def test_user_can_rsvp_to_event(client, auth_headers):
    event = client.post(
        "/api/events",
        headers=auth_headers,
        json={"title": "Meetup", "date": "2026-09-02T18:00:00"},
    ).get_json()
    response = client.post(
        f"/api/rsvps/event/{event['id']}",
        headers=auth_headers,
        json={"attending": True},
    )
    assert response.status_code == 201
    assert response.get_json()["attending"] is True

def test_live_duplicate_username_registration_returns_400(live_server):
    credentials = {
        "username": f"duplicate-{uuid.uuid4().hex}",
        "password": "password123",
    }
    first_response = requests.post(
        f"{live_server}/api/auth/register", json=credentials, timeout=5
    )
    second_response = requests.post(
        f"{live_server}/api/auth/register", json=credentials, timeout=5
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 400
    assert second_response.json()["error"] == "Username already exists"


def test_live_create_event_without_auth_returns_401(live_server):
    response = requests.post(
        f"{live_server}/api/events",
        json={"title": "Unauthorized Event", "date": "2026-12-01T18:00:00"},
        timeout=5,
    )

    assert response.status_code == 401


def test_live_rsvp_to_private_event_without_auth_returns_401(
    live_server, live_auth_token
):
    event_response = requests.post(
        f"{live_server}/api/events",
        json={
            "title": "Private Event",
            "date": "2026-12-02T18:00:00",
            "is_public": False,
        },
        headers={"Authorization": f"Bearer {live_auth_token}"},
        timeout=5,
    )
    assert event_response.status_code == 201
    event_id = event_response.json()["id"]

    response = requests.post(
        f"{live_server}/api/rsvps/event/{event_id}",
        json={"attending": True},
        timeout=5,
    )

    assert response.status_code == 401
    assert response.json()["error"] == "Authentication required for this event"


