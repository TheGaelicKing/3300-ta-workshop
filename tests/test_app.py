import pytest

from app import app, tasks


@pytest.fixture
def client():
    """Provide a Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_tasks():
    """Reset in-memory tasks before each test."""
    tasks.clear()
    tasks.extend([
        {
            "id": 1,
            "title": "Project-1 Report",
            "priority": "Medium"
        },
        {
            "id": 2,
            "title": "Project-2 MMFs",
            "priority": "Medium"
        }
    ])


def test_index(client):
    """Return the task tracker page."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Task Tracker" in response.data


def test_get_tasks(client):
    """Return existing tasks with their priorities."""
    response = client.get('/api/tasks')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert all(task['priority'] == 'Medium' for task in data)


@pytest.mark.parametrize('priority', ['Low', 'Medium', 'High'])
def test_add_task_priorities(client, priority):
    """Store and return each supported task priority."""
    response = client.post(
        '/api/tasks',
        json={"title": "Priority task", "priority": priority}
    )

    assert response.status_code == 201
    created_task = response.get_json()
    assert created_task['priority'] == priority

    get_response = client.get('/api/tasks')
    stored_task = get_response.get_json()[-1]
    assert stored_task['priority'] == priority


def test_add_task_defaults_to_medium_priority(client):
    """Default an omitted priority to Medium."""
    response = client.post('/api/tasks', json={"title": "Default task"})

    assert response.status_code == 201
    assert response.get_json()['priority'] == 'Medium'


def test_add_task_success(client):
    """Create a task and preserve the existing add behavior."""
    response = client.post('/api/tasks', json={"title": "Test new task"})
    assert response.status_code == 201
    assert response.get_json()['title'] == "Test new task"
    get_response = client.get('/api/tasks')
    assert len(get_response.get_json()) == 3


def test_add_task_missing_title(client):
    """Reject requests that do not contain a title."""
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
