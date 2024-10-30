import ssl
import logging

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from prometheus_client import REGISTRY
from faststream.rabbit import (
    ExchangeType,
    RabbitBroker,
    RabbitExchange,
    RabbitQueue,
)
from faststream.rabbit.prometheus import RabbitPrometheusMiddleware
from faststream.rabbit.opentelemetry import RabbitTelemetryMiddleware
from faststream.security import BaseSecurity
from faststream.rabbit.fastapi import RabbitRouter

from pipo_hub.config import settings

tracer_provider = TracerProvider(
    resource=Resource.create(attributes={"service.name": "faststream"})
)
trace.set_tracer_provider(tracer_provider)

router = RabbitRouter(
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
        RabbitPrometheusMiddleware(registry=REGISTRY),
        RabbitTelemetryMiddleware(tracer_provider=tracer_provider),
    ),
)

broker = router.broker


@router.get("/livez")
async def liveness() -> bool:
    return True


@router.get("/readyz")
async def readiness() -> bool:
    return await router.broker.ping(timeout=settings.probes.readiness.timeout)


plq = RabbitQueue(
    name=settings.player.queue.service.parking_lot.queue,
    durable=settings.player.queue.service.parking_lot.durable,
)

dlx = RabbitExchange(
    name=settings.player.queue.service.dead_letter.exchange.name,
    type=ExchangeType.TOPIC,
    durable=settings.player.queue.service.dead_letter.exchange.durable,
)

dlq = RabbitQueue(
    name=settings.player.queue.service.dead_letter.queue.name,
    durable=settings.player.queue.service.dead_letter.queue.durable,
    routing_key=settings.player.queue.service.dead_letter.queue.routing_key,
    arguments=settings.player.queue.service.dead_letter.queue.args,
)


async def declare_dlx(b: RabbitBroker):
    await b.declare_queue(plq)
    await b.declare_exchange(dlx)
    await b.declare_queue(dlq)


dispatcher_queue = RabbitQueue(
    settings.player.queue.service.dispatcher.queue,
    durable=True,
    arguments=settings.player.queue.service.dispatcher.args,
)

server_publisher = broker.publisher(
    dispatcher_queue,
    description="Produces to dispatch queue",
)

hub_exch = RabbitExchange(
    settings.player.queue.service.hub.exchange,
    type=ExchangeType.TOPIC,
    durable=True,
)

hub_queue = RabbitQueue(
    settings.player.queue.service.hub.queue,
    routing_key=settings.player.queue.service.hub.routing_key,
    durable=settings.player.queue.service.hub.durable,
    exclusive=settings.player.queue.service.hub.exclusive,
    arguments=settings.player.queue.service.hub.args,
)
