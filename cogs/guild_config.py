from discord import app_commands, Embed, ui, MessageInteraction, Permissions, ButtonStyle, AllowedMentions
from discord.ext import commands
from discord.ext.commands import Context
from discord.ui import Button, Modal, TextInput
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

class GuildConfig(commands.Cog, name="Guild Config", description="Commands for configuring Y2DL"):

    def __init__(self, bot, port):
        self.dbot = bot
        self.port = port
        self._last_member = None
        self.platform, self.database, self.bot, self.logging, self.services, self.color = load_config()

    @commands.hybrid_command(
        name="guildcfg",
        description="Configures Y2DL on your guild",
        default_permissions=Permissions(manage_guild=True),
        usage="{pr}guildcfg"
    )
    @commands.guild_only()
    async def guildcfg(self, ctx: Context):
        db = Y2dlDatabase(self.database.connection_string)
        cfg = db.get_guild_config(ctx.guild.id)[0]
        embed = EmbedUtils.secondary(
            title = locale.get("CONFIG", "en-US").format(ctx.guild.name),
        ).add_field(
            name=locale.get("CHANNELS", "en-US").format(len(cfg["youtube"]["channels"])),
            value=locale.get("GCFG_NO_CHANNELS", "en-US") if len(cfg["youtube"]["channels"]) < 1 else "test",
            inline=False
        ).add_field(
            name=locale.get("BROADCASTERS", "en-US").format(len(cfg["twitch"]["channels"])),
            value=locale.get("GCFG_NO_BROADCASTERS", "en-US") if len(cfg["twitch"]["channels"]) < 1 else "test",
            inline=False
        )
        await ctx.reply(
            embed=embed,
            allowed_mentions=AllowedMentions.none()
        )

    @commands.Cog.listener()
    async def on_button_click(self, ctx: MessageInteraction):
        if not ctx.message.interaction.author.id == ctx.author.id:
            await ctx.reply(
                embed=EmbedUtils.error(
                    title=locale.get("ERR_NOT_THE_COMMAND_EXECUTOR", interaction.locale),
                    description=locale.get("ERR_NOT_THE_COMMAND_EXECUTOR_DESC", interaction.locale)
                ),
                ephemeral=True
            )
            return
        if ctx.data.custom_id.endswith("add_yt"):
            modal = Modal(title=locale.get("GCFG_ADD_YT", "en-US"), custom_id="gcfg_add_yt", components=[TextInput(label=locale.get("GCFG_ADD_YT_MODAL", "en-US"), custom_id="gcfg_add_yt_id")])
            await ctx.response.reply_modal(modal)
        elif ctx.data.custom_id.endswith("add_tw"):
            await ctx.response.defer()
            embed=EmbedUtils.secondary(
                title=locale.get("GCFG_REQUIRES_AUTH", "en-US"),
                description=locale.get("GCFG_REQUIRES_AUTH_DESC", "en-US")
            )

            session_id = ''.join(random.choices(string.ascii_letters + string.digits, k=32))

            await ctx.edit_original_message(
                embed=embed,
                components = [
                    Button(style=ButtonStyle.link,label=locale.get("GCFG_AUTH", "en-US"),
                        url=f"https://id.twitch.tv/oauth2/authorize?response_type=code&client_id={self.platform.twitch.client_id}&redirect_uri={self.platform.twitch.redirect_uri}&scope=user:read:broadcast+channel:read:hype_train+channel:read:polls+channel:read:predictions+channel:read:goals+channel:read:subscriptions+moderator:read:followers+channel:read:ads+channel:read:redemptions+bits:read&state={session_id}"
                    ),
                ]
            )

            tw_auth_sessions[session_id] = {
                'guild_id': ctx.guild_id,
                'channel_id': ctx.channel_id,
                'message_id': ctx.message.id,
                'locale': "en-US"
            }

            tw_auth_msgs[session_id] = ctx.edit_original_message

            print(session_id)
            print(json.dumps(tw_auth_sessions[session_id]))

    # TODO: Modal Submit

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