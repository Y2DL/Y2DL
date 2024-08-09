from discord.ext import commands as cmds
from discord import Embed, MessageInteraction, Intents, Reaction, AllowedMentions
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

class Y2dlMain(cmds.AutoShardedBot):
    async def setup_hook(self):
        db = Y2dlDatabase(database.connection_string)
        for guild in self.guilds:
            if db.get_guild_config(guild.id) == None:
                db.init_guild_config(guild.id)
        await client.add_cog(ytinfo.YouTubeInfo(client))
        await client.add_cog(twinfo.TwitchInfo(client))
        await client.add_cog(other.Y2dlOther(client))
        await client.add_cog(guild_config.GuildConfig(client, platform.twitch.oauth2_port))   

    async def on_reaction_add(self, reaction: Reaction, user):
        if reaction.emoji == bot.delete_response_emoji:
            if self.user.id == reaction.message.author.id:
                await reaction.message.delete()
            else:
                await reaction.remove(user)

    async def on_command_error(self, ctx: cmds.Context, error):
        if isinstance(error, cmds.NotOwner):
            embed = EmbedUtils.error(
                title="You are not the instance owner!",
                description="If you are the instance owner, check `config/config.toml` if your user ID is correct."
            )
            await ctx.reply(embed=embed, allowed_mentions=AllowedMentions.none())
        elif isinstance(error, cmds.BadArgument):
            embed = EmbedUtils.error(
                title="Bad argument",
                description=f"Usage: `{ctx.command.usage.format(pr=bot.prefix)}`"
            )
            await ctx.reply(embed=embed, allowed_mentions=AllowedMentions.none())
        elif isinstance(error, cmds.MissingRequiredArgument):
            embed = EmbedUtils.error(
                title="Missing required argument",
                description=f"Usage: `{ctx.command.usage.format(pr=bot.prefix)}`"
            )
            await ctx.reply(embed=embed, allowed_mentions=AllowedMentions.none())
        elif isinstance(error, cmds.NoPrivateMessage):
            embed = EmbedUtils.error(
                title=f"`{ctx.command.name}` doesn't work in (G)DMs!",
                description="Try it on a guild/server."
            )
            await ctx.reply(embed=embed, allowed_mentions=AllowedMentions.none())
        elif isinstance(error, cmds.MissingPermissions):
            embed = EmbedUtils.error(
                title=f"You don't have enough permissions to run `{ctx.command.name}`!"
            )
            await ctx.reply(embed=embed, allowed_mentions=AllowedMentions.none())
        elif isinstance(error, cmds.CommandError):
            embed = EmbedUtils.error(
                title="An error occured.",
                description=f"Please contact the Y2DL instance owner for help.\n\n```{error}```"
            )
            await ctx.reply(embed=embed, allowed_mentions=AllowedMentions.none())

intents = Intents.default()
intents.message_content = True
client = Y2dlMain(command_prefix=bot.prefix, intents=intents, shard_count=1, test_guilds=[1212198952649363487, 1196627583509475438], help_command=None)

def start_bot():
    LoggingHelper.init_logging()
    client.run(bot.bot_token)

if __name__ == '__main__':
    start_bot()

