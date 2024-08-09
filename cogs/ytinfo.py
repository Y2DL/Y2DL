from discord import app_commands, Embed, ui, Interaction, Permissions, AllowedMentions, SelectOption
from discord.ext import commands
from discord.ext.commands import Context
from helpers import YoutubeHelper, ReturnYoutubeDislikeHelper, TwitchHelper, LocalizationHelper, YtVideoType, EmbedHelper, locale
from config import load_config
from dateutil import parser
from utils import StringUtils, IntUtils, EmbedUtils
from database import Y2dlDatabase
from bson.json_util import dumps
import json
import asyncio
import isodate

class YouTubeInfo(commands.Cog, name="YouTube Info", description="Commands for showing YouTube channel/video/playlist information"):
    def __init__(self, bot):
        self.dbot = bot
        self._last_member = None
        self.embedHlpr = EmbedHelper()
        self.platform, self.database, self.bot, self.logging, self.services, self.color = load_config()

    @commands.hybrid_group(
        name="ytinfo",
        description="Shows information about a YouTube channel, video, or a playlist."
    )
    async def ytinfo(self, ctx: Context):
        pass

    @ytinfo.command(
        name="channel",
        description="Shows information about a YouTube channel.",
        usage="{pr}ytinfo channel <channel_id_or_handle>"
    )
    async def channel(self, ctx: Context, channel_id_or_handle: str):
        await ctx.defer()
        channel_id = None
        channel_handle = None
        if "@" in channel_id_or_handle:
            channel_handle = channel_id_or_handle
        else:
            channel_id = channel_id_or_handle
        embed, vids, title = self.embedHlpr.get_yt_channel("en-US", channel_id, channel_handle)
        q = "'"
        if (vids is not None and "items" in vids and len(vids["items"]) >= 1):
            view = VideoSelectView(f'{title}{q}s Latest 25 videos', vids["items"][:25], ctx.author.id)
            await ctx.reply(embed=embed, view=view, allowed_mentions=AllowedMentions.none())
        else:
            await ctx.reply(embed=embed, allowed_mentions=AllowedMentions.none())

    @ytinfo.command(
        name="video",
        description="Shows information about a YouTube video.",
        usage="{pr}ytinfo video <video_id>"
    )
    async def video(self, ctx: Context, video_id: str):
        await ctx.defer()
        embed = self.embedHlpr.get_yt_video("en-US", video_id)
        await ctx.reply(embed=embed, allowed_mentions=AllowedMentions.none())

    @ytinfo.command(
        name="playlist",
        description="Shows information about a YouTube playlist.",
        usage="{pr}ytinfo playlist <playlist_id>"
    )
    async def playlist(self, ctx: Context, playlist_id: str):
        await ctx.defer()
        ytHelper = YoutubeHelper(self.platform.youtube.api_key)
        items = ytHelper.get_playlistitems(playlist_id)
        plInfo = ytHelper.get_playlist_info(playlist_id)
        userLocale = "en-US"
        if ("items" not in items or len(items["items"]) < 1):
            await ctx.send(
                embed = EmbedUtils.error(
                    title=locale.get("ERR_FETCH_CHANNEL", userLocale),
                    description=locale.get("ERR_FETCH_CHANNEL_DESC", userLocale),
                )
            )
            return
        embed = EmbedUtils.primary(
            title=plInfo["items"][0]["snippet"]["title"],
            url="https://youtube.com/playlist?list=" + plInfo["items"][0]["id"],
            description=StringUtils.limit(plInfo["items"][0]["snippet"]["description"], 100),
        ).set_author(
            name=plInfo["items"][0]["snippet"]["channelTitle"],
            url="https://youtube.com/channel/" + plInfo["items"][0]["snippet"]["channelId"]
        ).set_thumbnail(
            url = plInfo["items"][0]["snippet"]["thumbnails"]["standard"]["url"]
        ).add_field(
            name=locale.get("VIDEOS", userLocale),
            value=plInfo["items"][0]["contentDetails"]["itemCount"],
            inline = True
        ).add_field(
            name=locale.get("PUBLICITY", userLocale),
            value=plInfo["items"][0]["status"]["privacyStatus"].capitalize(),
            inline = True
        )
        view = VideoSelectView(f'{plInfo["items"][0]["snippet"]["title"]} by {plInfo["items"][0]["snippet"]["channelTitle"]}', items["items"][:25], ctx.author.id)
        await ctx.reply(embed=embed, view=view, allowed_mentions=AllowedMentions.none())

class VideoSelect(ui.Select):
    def __init__(self, placeholder, videos, author):
        options = []
        t = "'"
        for video in videos:
            video_author = f"{video['snippet']['videoOwnerChannelTitle'] if 'videoOwnerChannelTitle' in video['snippet'] else f'Can{t}t get video author'}"
            options.append(SelectOption(label=f"{StringUtils.limit(video['snippet']['title'], 100)}", description=f"by {video_author}", value=video['snippet']['resourceId']['videoId']))
        super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=options)
        self.author = author
        self.embedHlpr = EmbedHelper()
        self.platform, self.database, self.bot, self.logging, self.services, self.color = load_config()

    async def callback(self, interaction: Interaction):
        if interaction.user.id != self.author:
            await interaction.response.send_message(
                embed=EmbedUtils.error(
                    title=locale.get("ERR_NOT_THE_COMMAND_EXECUTOR", interaction.locale),
                    description=locale.get("ERR_NOT_THE_COMMAND_EXECUTOR_DESC", interaction.locale)
                ),
                ephemeral=True
            )
            print(f"{interaction.user.id}, {self.author}")
            return
        ytHelper = YoutubeHelper(self.platform.youtube.api_key)
        await interaction.response.defer()
        embed = self.embedHlpr.get_yt_video(interaction.locale, self.values[0])
        await interaction.message.edit(embed=embed)

class VideoSelectView(ui.View):
    def __init__(self, placeholder, videos, author):
        super().__init__(timeout=600)
        self.add_item(VideoSelect(placeholder, videos, author))