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

class Y2dlOther(commands.Cog):
    def __init__(self, bot):
        self.dbot = bot
        self._last_member = None
        self.platform, self.database, self.bot, self.logging, self.services, self.color = load_config()

    @commands.slash_command(
        name="about",
        description=Localized(key="CMD_ABOUT_DESC")
    )
    async def about(self, inter: ApplicationCommandInteraction):
        ver = "v2.0.0"
        embed = EmbedUtils.secondary(
            title = inter.bot.user.name,
        ).set_thumbnail(
            url = inter.bot.user.avatar.url
        ).add_field(
            locale.get("Y2DL_VER", inter.locale).format(ver),
            "by jbcarreon123",
            inline=True
        ).add_field(
            f'Language: {locale.get("LANG_NAME", inter.locale)}',
            f'by {locale.get("LANG_TRANSLATOR", inter.locale)}',
            inline=True
        )
        await inter.response.send_message(embed=embed)

    @commands.slash_command(
        name="ping",
        description=Localized(key="CMD_PING_DESC")
    )
    async def ping(self, inter: ApplicationCommandInteraction):
        db = Y2dlDatabase(self.database.connection_string)
        embed = EmbedUtils.secondary(
            title = "Pong!"
        ).add_field(
            locale.get("API_LATENCY", inter.locale),
            f"{round(self.dbot.latency * 1000.0, 2)}ms",
            inline = True
        ).add_field(
            locale.get("DB_LATENCY", inter.locale),
            f"{round(db.latency(), 2)}ms",
            inline = True
        )
        await inter.response.send_message(embed=embed)