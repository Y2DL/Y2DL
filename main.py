from disnake.ext import commands
from disnake import Embed
from database import Y2dlDatabase
from helpers import YoutubeHelper, LoggingHelper, ReturnYoutubeDislikeHelper
from commands import init_slash_commands
import ssl
import config
import asyncio
import logging as log
import datetime

platform, database, bot, logging, services, color = config.load_config()

class Y2dlMain(commands.AutoShardedInteractionBot):
    async def on_ready(self):
        log.info(f'Ready as bot "{self.user}"!')

Embed.set_default_colour(int(color.primary, 0))
LoggingHelper.init_logging()
client = Y2dlMain(shard_count=1)
loop = asyncio.get_event_loop()
loop.run_until_complete(init_slash_commands(client))
client.i18n.load('i18n/')
client.run(bot.bot_token)

