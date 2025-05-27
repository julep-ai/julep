from __future__ import annotations

"""Telemetry utilities for agents-api."""

import logging
import os
import platform
import time
import uuid
from pathlib import Path

import yaml
from fastapi import FastAPI, Request
from opentelemetry import metrics, trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    OTLPMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, OTLPSpanExporter
from opentelemetry.trace import StatusCode

logger = logging.getLogger(__name__)

# Instance of telemetry after initialization
telemetry: Telemetry | None = None

CONFIG_PATH = Path.home() / ".config" / "julep" / "config.yml"
DEFAULT_LEVEL = 1


def _load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f) or {}
    return {}


def _save_config(config: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.safe_dump(config, f)


class Telemetry:
    """Manager for OpenTelemetry setup."""

    def __init__(self, app: FastAPI) -> None:
        self.app = app
        self.level, self.instance_id = self._determine_level()
        self.meter = None

    def _determine_level(self) -> tuple[int, str]:
        level_env = os.getenv("JULEP_TELEMETRY")
        config = _load_config()
        if level_env is not None:
            level = int(level_env)
        else:
            level = int(config.get("telemetry", DEFAULT_LEVEL))
        instance_id = config.get("instance_id")
        if not instance_id:
            instance_id = str(uuid.uuid4())
            config["instance_id"] = instance_id
            if "telemetry" not in config:
                config["telemetry"] = level
            _save_config(config)
        return level, instance_id

    def setup(self) -> None:
        level_name = {
            0: "Off",
            1: "Ping-only",
            2: "Crashes-only",
            3: "Metrics+Crashes",
        }.get(self.level, "Unknown")
        logger.info(
            "Telemetry level %s (%s) active. Adjust via JULEP_TELEMETRY or %s",
            self.level,
            level_name,
            CONFIG_PATH,
        )
        if self.level == 0:
            return

        resource = Resource.create({
            "service.name": "julep-agents-api",
            "service.version": self.app.version,
            "service.instance.id": self.instance_id,
            "os.platform": platform.system(),
        })
        tracer_provider = TracerProvider(resource=resource)
        span_exporter = OTLPSpanExporter(insecure=True)
        tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
        trace.set_tracer_provider(tracer_provider)

        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(insecure=True), export_interval_millis=5000
        )
        self.meter = MeterProvider(resource=resource, metric_readers=[metric_reader])
        metrics.set_meter_provider(self.meter)

        if self.level >= 3:
            FastAPIInstrumentor.instrument_app(self.app, tracer_provider=tracer_provider)
            self._setup_metrics()

        self._send_startup_ping()
        if self.level >= 2:
            self._add_crash_middleware()

    def _send_startup_ping(self) -> None:
        tracer = trace.get_tracer("julep.telemetry")
        with tracer.start_as_current_span("startup_ping") as span:
            span.set_attribute("service.version", self.app.version)
            span.set_attribute("service.instance_id", self.instance_id)
            span.set_attribute("telemetry.level", self.level)

    def _add_crash_middleware(self) -> None:
        @self.app.middleware("http")
        async def catch_exceptions(request: Request, call_next):
            try:
                return await call_next(request)
            except Exception as e:
                tracer = trace.get_tracer("julep.telemetry")
                with tracer.start_as_current_span("unhandled_exception") as span:
                    span.record_exception(e)
                    span.set_status(StatusCode.ERROR)
                raise

    def _setup_metrics(self) -> None:
        meter = metrics.get_meter("julep.agents_api")
        self.queries_counter = meter.create_counter("julep.queries.count")
        self.workflows_counter = meter.create_counter("julep.workflows.count")
        latency_hist = meter.create_histogram("julep.request_latency.seconds")

        @self.app.middleware("http")
        async def latency_middleware(request: Request, call_next):
            start = trace.get_current_span().context.trace_id
            del start  # AIDEV-NOTE: trace id not needed; using for type check
            start_time = time.monotonic()
            response = await call_next(request)
            duration = time.monotonic() - start_time
            latency_hist.record(duration, {"route": request.url.path})
            return response


def init_telemetry(app: FastAPI) -> Telemetry:
    """Initialize telemetry for the given app."""

    global telemetry
    telemetry = Telemetry(app)
    telemetry.setup()
    return telemetry
