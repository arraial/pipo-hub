#!usr/bin/env python3
import asyncio
import signal
import contextlib
from fastapi import FastAPI
from prometheus_client import make_asgi_app
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from pipo_hub.broker import load_broker
from pipo_hub.config import settings
from pipo_hub.bot import PipoBot
from pipo_hub.cogs.music_bot import MusicBot
from pipo_hub.signal_manager import SignalManager
from pipo_hub.player.music_queue.handlers import router as probe_router


@contextlib.asynccontextmanager
async def _run_bot(app: FastAPI):
    asyncio.current_task().set_name(settings.main_task_name)
    SignalManager.add_handlers(
        asyncio.get_event_loop(),
        settings.main_task_name,
        (signal.SIGUSR1, signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT),
    )

    broker = load_broker(settings.app)
    await broker.connect()
    await broker.start()

    bot = PipoBot(
        command_prefix=settings.commands.prefix, description=settings.bot_description
    )

    async with bot:
        await bot.add_cog(MusicBot(bot, settings.channel, settings.voice_channel))
        await bot.start(settings.token)
        yield
        await bot.close()


def get_app() -> FastAPI:
    application = FastAPI(lifespan=_run_bot)
    application.mount("/metrics", make_asgi_app())
    application.include_router(probe_router)
    FastAPIInstrumentor.instrument_app(application)
    return application
