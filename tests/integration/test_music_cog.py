import discord.ext.commands as commands
import pytest
import discord.ext.test as dpytest
from pipo_hub.bot import PipoBot
import pytest_asyncio
import pytest

from pipo_hub.config import settings
from pipo_hub.cogs.music_bot import MusicBot


@pytest.mark.integration
class TestMusicCog:
    @pytest_asyncio.fixture
    async def bot(self):
        intents = PipoBot.get_intents()
        intents.members = True
        dummy = commands.Bot(
            intents=intents,
            command_prefix=settings.commands.prefix,
        )
        voice_channel = "voice"
        music_channel = "music"
        command_channel = "command"
        await dummy._async_setup_hook()
        await dummy.add_cog(
            MusicBot(
                dummy,
                channel_id=music_channel,
                voice_channel_id=voice_channel,
            )
        )
        dpytest.configure(
            client=dummy,
            text_channels=[command_channel, music_channel],
            voice_channels=[voice_channel],
        )
        yield dummy
        await dpytest.empty_queue()

    # FIXME
    @pytest.mark.skip(reason="requires fix")
    @pytest.mark.discord
    @pytest.mark.asyncio
    async def test_move_message(self, bot):
        guild = bot.guilds[0]
        command = settings.commands.prefix + "status"
        command_text_channel = guild.text_channels[0]
        bot_text_channel = guild.text_channels[1]
        bot_member = guild.members[0]
        sent_msg = await command_text_channel.send(content=command)
        assert dpytest.verify().message().content(command)
