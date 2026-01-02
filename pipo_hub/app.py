#!usr/bin/env python3
import asyncio
import signal
from contextlib import asynccontextmanager

from fastapi import FastAPI
from faststream.asgi import AsgiResponse, get, make_ping_asgi
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_client import REGISTRY, make_asgi_app

from pipo_hub.bot import PipoBot
from pipo_hub.broker import load_broker
from pipo_hub.cogs.music_bot import MusicBot
from pipo_hub.config import settings
from pipo_hub.signal_manager import SignalManager

__broker = load_broker(settings.app)


def get_broker():
    return __broker


async def delay(coro, seconds):
    await asyncio.sleep(seconds)
    await coro


@asynccontextmanager
async def _run_bot(app: FastAPI):
    """TODO

    TODO
    Discord bot.start operation is blocking, therefore a delay is
    applied for Uvicorn to launch app correctly.
    app : FastAPI
        ASGI application to run.
    """
    asyncio.current_task().set_name(settings.main_task_name)
    SignalManager.add_handlers(
        asyncio.get_event_loop(),
        settings.main_task_name,
        (signal.SIGUSR1, signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT),
    )

    broker = get_broker()
    await broker.connect()
    await broker.start()

    bot = PipoBot(
        command_prefix=settings.commands.prefix, description=settings.bot_description
    )
    await bot.add_cog(MusicBot(bot, settings.channel, settings.voice_channel))
    asyncio.create_task(delay(bot.start(settings.token), settings.pipo.startup_delay))
    yield
    await bot.close()


@get
async def liveness_ping(scope):
    return AsgiResponse(b"", status_code=settings.probes.liveness.status_code)


def create_app(broker=None) -> FastAPI:
    broker = broker or get_broker()
    application = FastAPI(
        lifespan=_run_bot,
    )
    application.mount(settings.probes.liveness.endpoint, liveness_ping)
    application.mount(
        settings.probes.readiness.endpoint,
        make_ping_asgi(broker, timeout=settings.probes.readiness.timeout),
    )
    application.mount(settings.telemetry.metrics.endpoint, make_asgi_app(REGISTRY))
    FastAPIInstrumentor.instrument_app(application)
    return application
