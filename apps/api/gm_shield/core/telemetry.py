from fastapi import FastAPI
from opentelemetry import metrics
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_client import make_asgi_app

from gm_shield.core.config import settings


def setup_telemetry(app: FastAPI):
    """
    Configures OpenTelemetry metrics and instrumentation.
    Exposes /metrics endpoint for Prometheus scraping.
    """
    if not settings.ENABLE_METRICS:
        return

    resource = Resource(attributes={SERVICE_NAME: "gm-smart-shield-api"})

    # Create Prometheus reader
    # This registers with the default prometheus_client registry
    reader = PrometheusMetricReader()

    # Create Meter Provider
    provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(provider)

    # Instrument FastAPI
    # This adds auto-instrumentation (request duration, etc.)
    FastAPIInstrumentor.instrument_app(app)

    # Mount Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    print("Telemetry enabled: Metrics exposed at /metrics")
