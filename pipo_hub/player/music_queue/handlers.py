from opentelemetry import trace
from faststream.rabbit import (
    ExchangeType,
    RabbitExchange,
    RabbitQueue,
)
from faststream.rabbit.fastapi import RabbitRouter
from pipo_hub.config import settings

tracer = trace.get_tracer(__name__)
router = RabbitRouter()


@router.get("/livez")
async def liveness() -> bool:
    return True


@router.get("/readyz")
async def readiness() -> bool:
    return await router.broker.ping(timeout=settings.probes.readiness.timeout)


server_publisher = router.publisher(
    settings.player.queue.service.dispatcher.queue,
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
