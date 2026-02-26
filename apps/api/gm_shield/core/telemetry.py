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
from gm_shield.core.logging import get_logger

logger = get_logger(__name__)


def setup_telemetry(app: FastAPI) -> None:
    """Configure OpenTelemetry metrics and mount the Prometheus scrape endpoint.

    Instrumentation is skipped entirely when ``settings.ENABLE_METRICS`` is
    ``False`` (the default for local development).

    When enabled:
    - A ``MeterProvider`` backed by a ``PrometheusMetricReader`` is registered
      as the global OTel metrics provider.
    - FastAPI request duration and other HTTP metrics are auto-instrumented.
    - A ``/metrics`` endpoint is mounted for Prometheus to scrape.

    Args:
        app: The FastAPI application instance to instrument.
    """
    if not settings.ENABLE_METRICS:
        return

    resource = Resource(attributes={SERVICE_NAME: "gm-smart-shield-api"})

    # Prometheus reader registers itself with the default prometheus_client registry,
    # making all collected metrics available via the /metrics ASGI sub-application.
    reader = PrometheusMetricReader()

    # Auto-instrumentation adds request duration histograms for every FastAPI route.
    provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(provider)

    # Mount the Prometheus scrape endpoint alongside the regular API routes.
    FastAPIInstrumentor.instrument_app(app)
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    logger.info("telemetry_enabled", endpoint="/metrics")
