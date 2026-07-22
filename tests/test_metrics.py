"""Prometheus latency metric contract tests."""

from collections.abc import Callable
from uuid import UUID

from fastapi.testclient import TestClient

from app.main import create_app
from app.metrics import METRICS_REGISTRY
from app.services.tasks import TaskService, get_task_service
from tests.fakes import InMemoryTaskRepository


def _count(method: str, route: str, status_code: str) -> float:
    for metric in METRICS_REGISTRY.collect():
        if metric.name != "api_http_request_duration_seconds":
            continue
        for sample in metric.samples:
            if sample.name.endswith("_count") and sample.labels == {
                "method": method,
                "route": route,
                "status_code": status_code,
            }:
                return sample.value
    return 0


def _change_after(
    action: Callable[[], object], method: str, route: str, status_code: str
) -> float:
    before = _count(method, route, status_code)
    action()
    return _count(method, route, status_code) - before


def test_business_routes_use_normalized_labels() -> None:
    application = create_app()
    service = TaskService(InMemoryTaskRepository())
    application.dependency_overrides[get_task_service] = lambda: service

    with TestClient(application) as client:
        created = client.post("/tasks", json={"name": "Measure API"})
        task_id = created.json()["id"]
        assert (
            _change_after(
                lambda: client.get(f"/tasks/{task_id}"),
                "GET",
                "/tasks/{task_id}",
                "200",
            )
            == 1
        )

        metrics = client.get("/metrics").text

    assert 'route="/tasks/{task_id}"' in metrics
    assert str(UUID(task_id)) not in metrics


def test_non_business_routes_are_not_measured() -> None:
    application = create_app()
    with TestClient(application) as client:
        before = sum(
            sample.value
            for metric in METRICS_REGISTRY.collect()
            if metric.name == "api_http_request_duration_seconds"
            for sample in metric.samples
            if sample.name.endswith("_count")
        )
        client.get("/metrics")
        client.get("/docs")
        client.get("/openapi.json")
        client.get("/missing")
        after = sum(
            sample.value
            for metric in METRICS_REGISTRY.collect()
            if metric.name == "api_http_request_duration_seconds"
            for sample in metric.samples
            if sample.name.endswith("_count")
        )

    assert after == before


def test_error_response_is_measured() -> None:
    application = create_app()

    def failing_service() -> None:
        raise RuntimeError("test failure")

    application.dependency_overrides[get_task_service] = failing_service

    with TestClient(application, raise_server_exceptions=False) as client:
        assert (
            _change_after(
                lambda: client.get("/tasks/00000000-0000-0000-0000-000000000001"),
                "GET",
                "/tasks/{task_id}",
                "500",
            )
            == 1
        )


def test_validation_error_status_is_measured() -> None:
    application = create_app()
    with TestClient(application) as client:
        assert (
            _change_after(
                lambda: client.get("/tasks/not-a-uuid"),
                "GET",
                "/tasks/{task_id}",
                "422",
            )
            == 1
        )
