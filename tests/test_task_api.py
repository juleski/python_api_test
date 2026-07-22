"""Task route contract tests using an in-memory repository adapter."""

from fastapi.testclient import TestClient

from app.main import app
from app.services.tasks import TaskService, get_task_service
from tests.fakes import InMemoryTaskRepository


def test_task_endpoint_workflow() -> None:
    service = TaskService(InMemoryTaskRepository())
    app.dependency_overrides[get_task_service] = lambda: service
    try:
        with TestClient(app) as client:
            created_response = client.post(
                "/tasks",
                json={"name": "  Build API  ", "description": ""},
            )
            assert created_response.status_code == 201
            created = created_response.json()
            assert created["name"] == "Build API"
            assert created["description"] is None
            assert created["status"] == "To Do"

            task_id = created["id"]
            update_response = client.put(
                f"/tasks/{task_id}",
                json={"status": "In Progress", "description": "Persist tasks"},
            )
            assert update_response.status_code == 200
            assert update_response.json()["status"] == "In Progress"

            get_response = client.get(f"/tasks/{task_id}")
            assert get_response.status_code == 200
            assert get_response.json()["description"] == "Persist tasks"

            list_response = client.get(
                "/tasks", params={"status": "In Progress", "name": "build"}
            )
            assert list_response.status_code == 200
            assert [item["id"] for item in list_response.json()["items"]] == [task_id]
    finally:
        app.dependency_overrides.clear()


def test_task_validation_not_found_and_invalid_cursor() -> None:
    service = TaskService(InMemoryTaskRepository())
    app.dependency_overrides[get_task_service] = lambda: service
    try:
        with TestClient(app) as client:
            assert client.post("/tasks", json={"name": " "}).status_code == 422
            assert (
                client.put(
                    "/tasks/00000000-0000-0000-0000-000000000001", json={}
                ).status_code
                == 422
            )
            missing = client.get("/tasks/00000000-0000-0000-0000-000000000001")
            assert missing.status_code == 404
            assert missing.json() == {"detail": "Task not found"}
            assert client.get("/tasks", params={"cursor": "invalid"}).status_code == 422
    finally:
        app.dependency_overrides.clear()
