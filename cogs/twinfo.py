from disnake import Localized, ApplicationCommandInteraction, Embed, ui, MessageInteraction, Permissions
from disnake.ext import commands
from helpers import YoutubeHelper, ReturnYoutubeDislikeHelper, TwitchHelper, LocalizationHelper, YtVideoType, EmbedHelper, locale
from config import load_config
from dateutil import parser
from utils import StringUtils, IntUtils, EmbedUtils
from database import Y2dlDatabase
from bson.json_util import dumps
import json
import asyncio
import isodate

class Y2dlTwInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.embedHlpr = EmbedHelper()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.embedHlpr.initialize_twitch())

    @commands.slash_command(
        name="twinfo",
        description=Localized(key="CMD_TWINFO_DESC")
    )
    async def twinfo(self, inter: ApplicationCommandInteraction):
        pass

    @twinfo.sub_command(
        name="broadcaster",
        description=Localized(key="CMD_TWINFO_CHANNEL_DESC")
    )
    async def broadcaster(self, inter: ApplicationCommandInteraction, login_name: str):
        await inter.response.defer()
        embed = await self.embedHlpr.get_tw_streamer(inter.locale, login_name)
        await inter.followup.send(embed=embed)