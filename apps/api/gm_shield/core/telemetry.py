"""
OpenTelemetry + Prometheus telemetry setup.

When ``ENABLE_METRICS=true`` is set, this module:
1. Creates an OpenTelemetry ``MeterProvider`` backed by a Prometheus metric reader.
2. Auto-instruments all FastAPI routes (records request duration, count, etc.).
3. Mounts a ``/metrics`` endpoint compatible with a standard Prometheus scrape job.

This module is a no-op when metrics are disabled (the default for local development).
"""

from fastapi import FastAPI
from opentelemetry import metrics
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_client import make_asgi_app

from gm_shield.core.config import settings


def setup_telemetry(app: FastAPI) -> None:
    """
    Conditionally configure OpenTelemetry metrics and mount the ``/metrics`` endpoint.

    Does nothing when ``settings.ENABLE_METRICS`` is ``False`` (the default),
    so this function is safe to call unconditionally from ``main.py``.

    When enabled:
    - A ``PrometheusMetricReader`` is registered with the global ``MeterProvider``.
    - ``FastAPIInstrumentor`` adds auto-instrumentation middleware (``http.server.duration``, etc.).
    - The standard Prometheus ASGI app is mounted at ``/metrics``.

    Args:
        app: The FastAPI application instance to instrument and extend.
    """
    if not settings.ENABLE_METRICS:
        return

    resource = Resource(attributes={SERVICE_NAME: "gm-smart-shield-api"})

    # Prometheus reader registers itself with the default prometheus_client registry,
    # making all collected metrics available via the /metrics ASGI sub-application.
    reader = PrometheusMetricReader()
    provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(provider)

    # Auto-instrumentation adds request duration histograms for every FastAPI route.
    FastAPIInstrumentor.instrument_app(app)

    # Mount the Prometheus scrape endpoint alongside the regular API routes.
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    print("Telemetry enabled: Prometheus metrics exposed at /metrics")
