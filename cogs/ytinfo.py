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

class Y2dlYtInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.embedHlpr = EmbedHelper()

    @commands.Cog.listener()
    async def on_dropdown(self, interaction: MessageInteraction):
        if not interaction.message.interaction.author.id == interaction.author.id:
            await interaction.response.send_message(
                embed=EmbedUtils.error(
                    title=locale.get("ERR_NOT_THE_COMMAND_EXECUTOR", interaction.locale),
                    description=locale.get("ERR_NOT_THE_COMMAND_EXECUTOR_DESC", interaction.locale)
                ),
                ephemeral=True
            )
            return
        if interaction.data.custom_id.startswith('ytpl_'):
            ytHelper = YoutubeHelper(platform.youtube.api_key)
            await interaction.response.defer()
            embed = self.embedHlpr.get_yt_video(interaction.locale, interaction.data.values[0])
            await interaction.edit_original_message(embed=embed)

    @commands.slash_command(
        name="ytinfo",
        description=Localized(key="CMD_YTINFO_DESC")
    )
    async def ytinfo(self, inter: ApplicationCommandInteraction):
        pass

    @ytinfo.sub_command(
        name="channel",
        description=Localized(key="CMD_YTINFO_CHANNEL_DESC")
    )
    async def channel(self, inter: ApplicationCommandInteraction, channel_id: str = None, channel_handle: str = None):
        await inter.response.defer()
        embed, vids, title = self.embedHlpr.get_yt_channel(inter.locale, channel_id, channel_handle)
        q = "'"
        if (vids is not None and "items" in vids and len(vids["items"]) >= 1):
            selectMenu = ui.StringSelect(custom_id="ytpl_selmenu", placeholder=f'{title}{q}s Latest 25 videos')
            items = vids["items"][:25]
            for vid in items:
                selectMenu.add_option(label=f"{StringUtils.limit(vid['snippet']['title'], 100)}", value=vid['snippet']['resourceId']['videoId'])
            await inter.followup.send(embed=embed, components=[selectMenu])
        else:
            await inter.followup.send(embed=embed)

    @ytinfo.sub_command(
        name="video",
        description=Localized(key="CMD_YTINFO_VIDEO_DESC")
    )
    async def video(self, inter: ApplicationCommandInteraction, video_id: str):
        await inter.response.defer()
        embed = self.embedHlpr.get_yt_video(inter.locale, video_id)
        await inter.followup.send(embed=embed)

    @ytinfo.sub_command(
        name="playlist",
        description=Localized(key="CMD_YTINFO_PLAYLIST_DESC")
    )
    async def playlist(self, inter: ApplicationCommandInteraction, playlist_id: str):
        await inter.response.defer()
        ytHelper = YoutubeHelper(platform.youtube.api_key)
        items = ytHelper.get_playlistitems(playlist_id)
        plInfo = ytHelper.get_playlist_info(playlist_id)
        userLocale = inter.locale
        if ("items" not in items or len(items["items"]) < 1):
            await inter.followup.send(
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
            locale.get("VIDEOS", userLocale),
            plInfo["items"][0]["contentDetails"]["itemCount"],
            inline = True
        ).add_field(
            locale.get("PUBLICITY", userLocale),
            plInfo["items"][0]["status"]["privacyStatus"].capitalize(),
            inline = True
        )
        single_tick = "'"
        selectMenu = ui.StringSelect(custom_id="ytpl_selmenu", placeholder=f'{plInfo["items"][0]["snippet"]["title"]} by {plInfo["items"][0]["snippet"]["channelTitle"]}')
        vids = items["items"][:25]
        for vid in vids:
            vidAuthor = f"{vid['snippet']['videoOwnerChannelTitle'] if 'videoOwnerChannelTitle' in vid['snippet'] else f'Can{single_tick}t get video author'}"
            selectMenu.add_option(label=f"{StringUtils.limit(vid['snippet']['title'], 96 - len(vidAuthor))} by {vidAuthor}", value=vid['snippet']['resourceId']['videoId'])
        await inter.followup.send(embed=embed, components=[selectMenu])