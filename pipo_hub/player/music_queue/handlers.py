from faststream.rabbit import (
    ExchangeType,
    RabbitExchange,
    RabbitQueue,
)
from faststream.rabbit import RabbitRouter
from pipo_hub.config import settings

router = RabbitRouter()

dispatcher_exch = RabbitExchange(
    settings.player.queue.service.dispatcher.exchange,
    type=ExchangeType.DIRECT,
    durable=True,
    routing_key=settings.player.queue.service.dispatcher.routing_key,
)

server_publisher = router.publisher(
    exchange=dispatcher_exch,
    description="Produces to dispatcher exchange",
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
