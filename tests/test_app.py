import importlib

from fastapi.testclient import TestClient
from src import app as app_module


def get_client():
    global app_module
    app_module = importlib.reload(app_module)
    return TestClient(app_module.app)


def test_root_redirects_to_static_index():
    client = get_client()

    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_data():
    client = get_client()

    response = client.get("/activities")
    assert response.status_code == 200

    activities = response.json()
    assert isinstance(activities, dict)
    assert "Chess Club" in activities
    assert "participants" in activities["Chess Club"]


def test_signup_participant_success():
    client = get_client()
    activity = "Chess Club"
    email = "newstudent@mergington.edu"

    response = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity}"

    activities = client.get("/activities").json()
    assert email in activities[activity]["participants"]


def test_signup_duplicate_participant_returns_400():
    client = get_client()
    activity = "Chess Club"
    email = "duplicate@mergington.edu"

    first_response = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert first_response.status_code == 200

    second_response = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Student already signed up"


def test_unregister_participant_success():
    client = get_client()
    activity = "Chess Club"
    email = "remove@mergington.edu"

    signup_response = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert signup_response.status_code == 200

    delete_response = client.delete(
        f"/activities/{activity}/participants", params={"email": email}
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == f"Unregistered {email} from {activity}"

    activities = client.get("/activities").json()
    assert email not in activities[activity]["participants"]


def test_unregister_missing_participant_returns_404():
    client = get_client()
    activity = "Chess Club"
    email = "missing@mergington.edu"

    response = client.delete(f"/activities/{activity}/participants", params={"email": email})
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
