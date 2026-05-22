import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

TEST_DB_PATH = Path("data/test_todos.db")

if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["SQL_ECHO"] = "false"

from main import app  # noqa: E402


def test_health_check():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "time" in data


def test_create_todo():
    with TestClient(app) as client:
        response = client.post(
            "/todos",
            json={
                "title": "Test create todo",
                "due_time": "today",
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test create todo"
    assert data["completed"] is False
    assert data["due_time"] == "today"
    assert "id" in data


def test_todo_crud_flow():
    with TestClient(app) as client:
        create_response = client.post(
            "/todos",
            json={
                "title": "Test CRUD todo",
                "due_time": "tomorrow",
            },
        )

        assert create_response.status_code == 201
        created = create_response.json()
        todo_id = created["id"]

        get_response = client.get(f"/todos/{todo_id}")
        assert get_response.status_code == 200
        assert get_response.json()["title"] == "Test CRUD todo"

        patch_response = client.patch(
            f"/todos/{todo_id}",
            json={
                "title": "Updated CRUD todo",
                "completed": True,
                "due_time": "tonight",
            },
        )

        assert patch_response.status_code == 200
        updated = patch_response.json()
        assert updated["title"] == "Updated CRUD todo"
        assert updated["completed"] is True
        assert updated["due_time"] == "tonight"

        delete_response = client.delete(f"/todos/{todo_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == "Todo deleted"

        missing_response = client.get(f"/todos/{todo_id}")
        assert missing_response.status_code == 404


def test_create_todo_with_empty_title_should_fail():
    with TestClient(app) as client:
        response = client.post(
            "/todos",
            json={
                "title": "",
            },
        )

    assert response.status_code == 422