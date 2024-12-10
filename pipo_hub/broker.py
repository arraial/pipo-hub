import ssl
import logging
from faststream.rabbit import RabbitBroker
from faststream.security import BaseSecurity
from faststream.rabbit.opentelemetry import RabbitTelemetryMiddleware
from faststream.rabbit.prometheus import RabbitPrometheusMiddleware
from pipo_hub.player.music_queue.handlers import router
from pipo_hub.telemetry import setup_telemetry
from pipo_hub.config import settings
from prometheus_client import REGISTRY


def load_broker(service_name: str) -> RabbitBroker:
    telemetry = setup_telemetry(service_name, settings.telemetry.local)
    core_router = RabbitBroker(
        app_id=settings.app,
        url=settings.queue_broker_url,
        host=settings.player.queue.broker.host,
        virtualhost=settings.player.queue.broker.vhost,
        port=settings.player.queue.broker.port,
        timeout=settings.player.queue.broker.timeout,
        max_consumers=settings.player.queue.broker.max_consumers,
        graceful_timeout=settings.player.queue.broker.graceful_timeout,
        logger=logging.getLogger(__name__),
        security=BaseSecurity(ssl_context=ssl.create_default_context()),
        middlewares=(
            RabbitPrometheusMiddleware(
                registry=REGISTRY,
                app_name=settings.telemetry.metrics.service,
                metrics_prefix="faststream",
            ),
            RabbitTelemetryMiddleware(tracer_provider=telemetry.traces or None),
        ),
    )
    core_router.include_router(router)
    return core_router
