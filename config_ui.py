from disnake import Localized, ApplicationCommandInteraction, Embed, MessageInteraction, ButtonStyle, ModalInteraction
from disnake.ui import Button, Modal, TextInput
from helpers import YoutubeHelper, ReturnYoutubeDislikeHelper, TwitchHelper, LocalizationHelper
from config import load_config
from dateutil import parser
from database import Y2dlDatabase
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
    async def btn_selmenu_recieved(inter: MessageInteraction):
        if inter.data.custom_id.endswith("add_yt"):
            modal = Modal(title=locale.get("GCFG_ADD_YT", inter.locale), custom_id="gcfg_add_yt_channel", components=[TextInput(label=locale.get("GCFG_ADD_YT_MODAL", inter.locale), custom_id="gcfg_add_yt_id")])
            await inter.response.send_modal(modal)
        elif inter.data.custom_id.endswith("add_tw"):
            modal = Modal(title=locale.get("GCFG_ADD_TW", inter.locale), custom_id="gcfg_add_yt_channel", components=[TextInput(label=locale.get("GCFG_ADD_TW_MODAL", inter.locale), custom_id="gcfg_add_yt_id")])
            await inter.response.send_modal(modal)

    @staticmethod
    async def modal_recieved(inter: ModalInteraction):
        await inter.response.send_message(
            "test"
        )

    async def main_page(self, inter: ApplicationCommandInteraction):
        db = Y2dlDatabase(database.connection_string)
        cfg = db.get_guild_config(inter.guild_id)[0]
        embed = EmbedUtils.secondary(
            title = f"Config for {inter.guild.name}",
        ).add_field(
            locale.get("CHANNELS", inter.locale).format(len(cfg["youtube"]["channels"])),
            locale.get("GCFG_NO_CHANNELS", inter.locale) if len(cfg["youtube"]["channels"]) < 1 else "test",
            inline=False
        ).add_field(
            locale.get("BROADCASTERS", inter.locale).format(len(cfg["twitch"]["channels"])),
            locale.get("GCFG_NO_BROADCASTERS", inter.locale) if len(cfg["twitch"]["channels"]) < 1 else "test",
            inline=False
        )
        await inter.response.send_message(
            embed=embed,
            components = [
                Button(style=ButtonStyle.danger,label=locale.get("GCFG_ADD_YT", inter.locale), custom_id="gcfg_add_yt"),
                Button(style=ButtonStyle.primary,label=locale.get("GCFG_ADD_TW", inter.locale), custom_id="gcfg_add_tw")
            ]
        )

    