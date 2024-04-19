from disnake.ext import commands
from database import Y2dlDatabase
from helpers import YoutubeHelper, LoggingHelper, ReturnYoutubeDislikeHelper
from commands import init_slash_commands
import config
import logging
import datetime

platform, database, bot, logging, services = config.load_config()

class Y2dlMain(commands.InteractionBot):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')

LoggingHelper.init_logging()
client = Y2dlMain()
init_slash_commands(client)
client.i18n.load('locale/')
client.run(bot.bot_token)