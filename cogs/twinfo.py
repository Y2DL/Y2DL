from discord import app_commands, Embed, ui, MessageInteraction, Permissions, AllowedMentions
from discord.ext.commands import Context
from discord.ext import commands
from helpers import YoutubeHelper, ReturnYoutubeDislikeHelper, TwitchHelper, LocalizationHelper, YtVideoType, EmbedHelper, locale
from config import load_config
from dateutil import parser
from utils import StringUtils, IntUtils, EmbedUtils
from database import Y2dlDatabase
from bson.json_util import dumps
import json
import asyncio
import isodate

class TwitchInfo(commands.Cog, name="Twitch Info", description="Commands for showing Twitch broadcaster/video information"):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.embedHlpr = EmbedHelper()

    @commands.hybrid_group(
        name="twinfo",
        description="Shows information about a Twitch broadcaster, and videos."
    )
    async def twinfo(self, ctx: Context):
        pass

    @twinfo.command(
        name="broadcaster",
        description=app_commands.locale_str("Shows information about a Twitch broadcaster"),
        usage="{pr}twinfo broadcaster <login_name>"
    )
    async def broadcaster(self, ctx: Context, login_name: str):
        await ctx.defer()
        embed = await self.embedHlpr.get_tw_streamer("en-US", login_name)
        await ctx.reply(embed=embed, allowed_mentions=AllowedMentions.none())