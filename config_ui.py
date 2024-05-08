from disnake import Localized, ApplicationCommandInteraction, Embed, MessageInteraction
from disnake.ui import Button
from helpers import YoutubeHelper, ReturnYoutubeDislikeHelper, TwitchHelper, LocalizationHelper
from config import load_config
from dateutil import parser
from cachetools import TTLCache
from utils import StringUtils, IntUtils, EmbedUtils
import json
import isodate

platform, database, bot, logging, services, colors = load_config()
locale = LocalizationHelper()

class Y2dlGuildConfig:
    def __init__(self, guild_id, executer):
        self.guild_id = guild_id
        self.executer = executer

    @staticmethod
    async def button_recieved(inter: MessageInteraction):
        if not inter.message.interaction.author.id == inter.author.id:
            await inter.response.send_message(
                embed=EmbedUtils.error(
                    title=locale.get("ERR_NOT_THE_COMMAND_EXECUTOR", inter.locale),
                    description=locale.get("ERR_NOT_THE_COMMAND_EXECUTOR_DESC", inter.locale)
                )
            )
            return
        await inter.response.send_message(
            "test"
        )

    async def test(self, inter: ApplicationCommandInteraction):
        await inter.response.send_message(
            "test 2",
            components = [Button(label="Test button 1", custom_id="gcfg_test1"), Button(label="Test button 2", custom_id="gcfg_test2"), Button(label="Test button 3", custom_id="gcfg_test3")]
        )

    