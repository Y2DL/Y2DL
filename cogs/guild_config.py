from disnake import Localized, ApplicationCommandInteraction, Embed, ui, MessageInteraction, Permissions, ModalInteraction, ButtonStyle
from disnake.ext import commands
from disnake.ui import Button, Modal, TextInput
from helpers import YoutubeHelper, ReturnYoutubeDislikeHelper, TwitchHelper, LocalizationHelper, YtVideoType, EmbedHelper, locale
from config import load_config
from dateutil import parser
from utils import StringUtils, IntUtils, EmbedUtils
from database import Y2dlDatabase
from bson.json_util import dumps
from flask import session
from cachetools import TTLCache
from waitress import serve
from aiohttp import web
import aiohttp
import threading
import json
import asyncio
import isodate
import random
import string

tw_auth_sessions = TTLCache(64, 3600)
tw_auth_msgs = TTLCache(64, 3600)

class Y2dlGuildConfig(commands.Cog):

    def __init__(self, bot, port):
        self.dbot = bot
        self.port = port
        self._last_member = None
        self.platform, self.database, self.bot, self.logging, self.services, self.color = load_config()

    @commands.slash_command(
        name="guildcfg",
        description=Localized(key="CMD_GUILDCFG_DESC"),
        dm_permission=False
    )
    async def guildcfg(self, inter: ApplicationCommandInteraction):
        db = Y2dlDatabase(self.database.connection_string)
        cfg = db.get_guild_config(inter.guild_id)[0]
        embed = EmbedUtils.secondary(
            title = locale.get("CONFIG", inter.locale).format(inter.guild.name),
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

    @commands.Cog.listener()
    async def on_button_click(self, inter: MessageInteraction):
        if not inter.message.interaction.author.id == inter.author.id:
            await inter.response.send_message(
                embed=EmbedUtils.error(
                    title=locale.get("ERR_NOT_THE_COMMAND_EXECUTOR", interaction.locale),
                    description=locale.get("ERR_NOT_THE_COMMAND_EXECUTOR_DESC", interaction.locale)
                ),
                ephemeral=True
            )
            return
        if inter.data.custom_id.endswith("add_yt"):
            modal = Modal(title=locale.get("GCFG_ADD_YT", inter.locale), custom_id="gcfg_add_yt", components=[TextInput(label=locale.get("GCFG_ADD_YT_MODAL", inter.locale), custom_id="gcfg_add_yt_id")])
            await inter.response.send_modal(modal)
        elif inter.data.custom_id.endswith("add_tw"):
            await inter.response.defer()
            embed=EmbedUtils.secondary(
                title=locale.get("GCFG_REQUIRES_AUTH", inter.locale),
                description=locale.get("GCFG_REQUIRES_AUTH_DESC", inter.locale)
            )

            session_id = ''.join(random.choices(string.ascii_letters + string.digits, k=32))

            await inter.edit_original_message(
                embed=embed,
                components = [
                    Button(style=ButtonStyle.link,label=locale.get("GCFG_AUTH", inter.locale),
                        url=f"https://id.twitch.tv/oauth2/authorize?response_type=code&client_id={self.platform.twitch.client_id}&redirect_uri={self.platform.twitch.redirect_uri}&scope=user:read:broadcast+channel:read:hype_train+channel:read:polls+channel:read:predictions+channel:read:goals+channel:read:subscriptions+moderator:read:followers+channel:read:ads+channel:read:redemptions+bits:read&state={session_id}"
                    ),
                ]
            )

            tw_auth_sessions[session_id] = {
                'guild_id': inter.guild_id,
                'channel_id': inter.channel_id,
                'message_id': inter.message.id,
                'locale': inter.locale
            }

            tw_auth_msgs[session_id] = inter.edit_original_message

            print(session_id)
            print(json.dumps(tw_auth_sessions[session_id]))

    @commands.Cog.listener()
    async def on_modal_submit(self, inter: ModalInteraction):
        if not inter.message.interaction.author.id == inter.author.id:
            await inter.response.send_message(
                embed=EmbedUtils.error(
                    title=locale.get("ERR_NOT_THE_COMMAND_EXECUTOR", interaction.locale),
                    description=locale.get("ERR_NOT_THE_COMMAND_EXECUTOR_DESC", interaction.locale)
                ),
                ephemeral=True
            )
            return
        if inter.data.custom_id.endswith("add_yt"):
            await inter.response.send_message(
                "test"
            )

    app = web.Application(debug=True)

    async def callback(request):
        if "code" not in request.rel_url.query:
            return web.Response(body='{"code": "400", "err": "`code` and/or `state` not found"}', status=400, content_type='application/json')

        code = request.rel_url.query['code']
        state = request.rel_url.query['state']
        
        if tw_auth_sessions.get(state):
            session = tw_auth_sessions.get(state)
            msg = tw_auth_msgs.get(state)

            await msg(
                embed=EmbedUtils.success(
                    title=locale.get("GCFG_TWAUTHED", session["locale"]),
                    description=locale.get("GCFG_AUTHED_DESC", session["locale"])
                ),
                components=[
                    Button(style=ButtonStyle.primary,label=locale.get("GCFG_AUTHED_BTN", session["locale"]), custom_id="gcfg_tw_cfgr")
                ]
            )

            del tw_auth_msgs[state]
            del tw_auth_sessions[state]

            with open('auth_complete.html', 'r', encoding="utf-8") as outp:
                out = outp.read().replace('[gcfg_auth_complete]', locale.get("GCFG_TWAUTH_COMPLETE", session["locale"])).replace('[gcfg_auth_complete_desc]', locale.get("GCFG_TWAUTH_COMPLETE_DESC", session["locale"]))
                return web.Response(body=out, status=200, content_type='text/html')
        else:
            return web.Response(body='{"code": "400", "err": "invalid token"}', status=400, content_type='application/json')

    app.add_routes([web.get('/callback', callback)])

    async def start_server(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", self.port)
        await site.start()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.start_server()