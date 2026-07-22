"""Prometheus instrumentation for business API latency."""

from time import perf_counter

from fastapi import APIRouter, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

MEASURED_ROUTES = frozenset({"/", "/health", "/tasks", "/tasks/{task_id}"})
METRICS_REGISTRY = CollectorRegistry()

API_REQUEST_DURATION = Histogram(
    "api_http_request_duration_seconds",
    "Time spent serving business API requests.",
    ("method", "route", "status_code"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
    registry=METRICS_REGISTRY,
)


class ApiLatencyMiddleware(BaseHTTPMiddleware):
    """Measure matched business routes using their low-cardinality templates."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        started_at = perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            route = request.scope.get("route")
            route_path = getattr(route, "path", None)
            if route_path in MEASURED_ROUTES:
                API_REQUEST_DURATION.labels(
                    method=request.method,
                    route=route_path,
                    status_code=str(status_code),
                ).observe(perf_counter() - started_at)


router = APIRouter(include_in_schema=False)


@router.get("/metrics")
async def metrics() -> Response:
    """Expose metrics in the Prometheus text exposition format."""
    return Response(
        content=generate_latest(METRICS_REGISTRY),
        headers={"Content-Type": CONTENT_TYPE_LATEST},
    )
