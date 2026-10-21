import pytest

import app as app_module
from app import app, tasks


@pytest.fixture
def client():
    """Provide a configured Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_tasks():
    """Reset in-memory tasks and IDs before each test."""
    tasks.clear()
    tasks.extend([
        {"id": 1, "title": "Project-1 Report"},
        {"id": 2, "title": "Project-2 MMFs"}
    ])
    app_module.next_id = 3


def test_index(client):
    """Return the task tracker page."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Task Tracker" in response.data


def test_get_tasks(client):
    """Return all stored tasks."""
    response = client.get('/api/tasks')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2


def test_add_task_success(client):
    """Create a task and return its title and default priority."""
    response = client.post('/api/tasks', json={"title": "Test new task"})
    assert response.status_code == 201
    assert response.get_json()['title'] == "Test new task"
    assert response.get_json()['priority'] == "Medium"
    get_response = client.get('/api/tasks')
    assert len(get_response.get_json()) == 3
    assert get_response.get_json()[-1]['priority'] == "Medium"


def test_add_task_supported_priorities(client):
    """Store and return each supported priority value."""
    for priority in ("Low", "Medium", "High"):
        response = client.post(
            '/api/tasks',
            json={"title": f"{priority} task", "priority": priority}
        )
        assert response.status_code == 201
        assert response.get_json()['priority'] == priority

    stored_tasks = client.get('/api/tasks').get_json()
    assert [task['priority'] for task in stored_tasks[-3:]] == [
        "Low", "Medium", "High"
    ]


def test_add_task_rejects_invalid_priority(client):
    """Reject unsupported priority values without storing a task."""
    response = client.post(
        '/api/tasks',
        json={"title": "Invalid task", "priority": "Urgent"}
    )
    assert response.status_code == 400
    assert "error" in response.get_json()
    assert len(client.get('/api/tasks').get_json()) == 2


def test_add_task_missing_title(client):
    """Reject requests that do not include a title."""
    response = client.post('/api/tasks', json={"wrong_key": "value"})
    assert response.status_code == 400
    assert "error" in response.get_json()
    response2 = client.post('/api/tasks', json={})
    assert response2.status_code == 400


def test_delete_task(client):
    """Delete an existing task."""
    response = client.delete('/api/tasks/1')
    assert response.status_code == 200
    get_response = client.get('/api/tasks')
    data = get_response.get_json()
    assert len(data) == 1
    assert data[0]['id'] == 2
