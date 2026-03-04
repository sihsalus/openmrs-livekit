"""
OpenTelemetry tracing setup for the Nebu agent.

Call setup_tracing() once at startup. After that, use:
    from opentelemetry import trace
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("my-span") as span:
        span.set_attribute("key", "value")
"""

import logging
import os

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.semconv.resource import ResourceAttributes

logger = logging.getLogger("nebu.tracing")

_initialized = False


def setup_tracing() -> None:
    global _initialized
    if _initialized:
        return

    enabled = os.getenv("OTEL_ENABLED", "true").lower() != "false"
    if not enabled:
        logger.info("OpenTelemetry tracing disabled (OTEL_ENABLED=false)")
        return

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://nebu-tempo:4317")
    service_name = os.getenv("OTEL_SERVICE_NAME", "nebu-agent")
    environment = os.getenv("ENVIRONMENT", "development")

    resource = Resource.create({
        ResourceAttributes.SERVICE_NAME: service_name,
        ResourceAttributes.DEPLOYMENT_ENVIRONMENT: environment,
    })

    exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    _initialized = True
    logger.info("OpenTelemetry tracing initialized", extra={"endpoint": endpoint, "service": service_name})


def get_tracer(name: str = "nebu.agent"):
    return trace.get_tracer(name)
