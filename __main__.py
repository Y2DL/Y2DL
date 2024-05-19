from disnake.ext import commands as cmds
from disnake import Embed, MessageInteraction, Reaction, ModalInteraction
from database import Y2dlDatabase
from utils import EmbedUtils
from helpers import YoutubeHelper, LoggingHelper, ReturnYoutubeDislikeHelper, LocalizationHelper
from cogs import ytinfo, twinfo, other, guild_config
import threading
import ssl
import config
import asyncio
import logging as log
import auth
import datetime

platform, database, bot, logging, services, color = config.load_config()
locale = LocalizationHelper()

class Y2dlMain(cmds.AutoShardedInteractionBot):
    async def on_ready(self):
        db = Y2dlDatabase(database.connection_string)
        for guild in self.guilds:
            if db.get_guild_config(guild.id) == None:
                db.init_guild_config(guild.id)
        log.info(f'Ready as bot "{self.user}"!')        

    async def on_reaction_add(self, reaction: Reaction, user):
        if reaction.emoji == bot.delete_response_emoji:
            if self.user.id == reaction.message.author.id and reaction.message.interaction.author.id == user.id:
                await reaction.message.delete()
            else:
                await reaction.remove(user)

client = Y2dlMain(shard_count=1, test_guilds=[1212198952649363487, 1196627583509475438])

def start_bot():
    Embed.set_default_colour(int(color.primary, 0))
    LoggingHelper.init_logging()
    client.add_cog(ytinfo.Y2dlYtInfo(client))
    client.add_cog(twinfo.Y2dlTwInfo(client))
    client.add_cog(other.Y2dlOther(client))
    client.add_cog(guild_config.Y2dlGuildConfig(client, platform.twitch.oauth2_port))
    client.i18n.load('i18n/')
    client.run(bot.bot_token)

if __name__ == '__main__':
    start_bot()

