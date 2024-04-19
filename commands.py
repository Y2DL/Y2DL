from disnake import Localized, ApplicationCommandInteraction, Embed
from helpers import YoutubeHelper, ReturnYoutubeDislikeHelper
from config import load_config
from dateutil import parser
from utils import StringUtils, IntUtils
import isodate

platform, database, bot, logging, services = load_config()

def init_slash_commands(client):
    ytHelper = YoutubeHelper(platform.youtube.api_key)

    @client.slash_command(
        name=Localized("ytinfo", key="CMD_YTINFO_NAME"),
        description=Localized("Shows information about a YouTube channel, video, or a playlist.", key="CMD_YTINFO_DESC")
    )
    async def ytinfo(inter: ApplicationCommandInteraction):
        pass

    @ytinfo.sub_command(
        name=Localized("channel", key="CMD_YTINFO_CHANNEL_NAME"),
        description=Localized("Shows information about a YouTube Channel", key="CMD_YTINFO_CHANNEL_DESC")
    )
    async def video(inter: ApplicationCommandInteraction, channel_id: str):
        await inter.response.defer()
        chnl = ytHelper.get_channels(channel_id)
        print(chnl)
        if (len(chnl["items"]) < 1):
            await inter.followup.send("Cannot find the channel! Make sure you put the ID right.")
        pub_at = int(parser.parse(chnl["items"][0]["snippet"]["publishedAt"]).timestamp())
        await inter.followup.send(f"<t:{pub_at}>")

    @ytinfo.sub_command(
        name=Localized("video", key="CMD_YTINFO_VIDEO_NAME"),
        description=Localized("Shows information about a YouTube video.", key="CMD_YTINFO_VIDEO_DESC")
    )
    async def video(inter: ApplicationCommandInteraction, video_id: str):
        await inter.response.defer()
        vids = ytHelper.get_videos(video_id)
        if (len(vids["items"]) < 1):
            await inter.followup.send("Cannot find the video! Make sure you put the ID right.")
        pub_at = int(parser.parse(vids["items"][0]["snippet"]["publishedAt"]).timestamp())
        ryd_res = ReturnYoutubeDislikeHelper.get_dislikes(vids["items"][0]["id"])
        dur = isodate.parse_duration(vids["items"][0]["contentDetails"]["duration"])
        embed = Embed(
            title = vids["items"][0]["snippet"]["title"],
            url = "https://youtu.be/" + vids["items"][0]["id"],
            description = StringUtils.limit(vids["items"][0]["snippet"]["description"], 100),
        ).set_author(
            name = vids["items"][0]["snippet"]["channelTitle"],
            url = "https://youtube.com/channel/" + vids["items"][0]["snippet"]["channelId"]
        ).set_thumbnail(
            url = vids["items"][0]["snippet"]["thumbnails"]["medium"]["url"]
        ).add_field(
            "Views",
            IntUtils.humanize_number(vids["items"][0]["statistics"]["viewCount"]),
            inline = True
        ).add_field(
            "Likes",
            IntUtils.humanize_number(vids["items"][0]["statistics"]["likeCount"]),
            inline = True
        ).add_field(
            "Dislikes",
            IntUtils.humanize_number(ryd_res["dislikes"]),
            inline = True
        ).add_field(
            "Comments",
            IntUtils.humanize_number(vids["items"][0]["statistics"]["commentCount"]),
            inline = True
        ).add_field(
            "Published at",
            f"<t:{pub_at}>",
            inline = True
        ).add_field(
            "Duration",
            dur,
            inline = True
        )
        if "tags" in vids["items"][0]["snippet"]:
            embed.add_field(
                "Tags",
                ", ".join(vids["items"][0]["snippet"]["tags"]) if len(vids["items"][0]["snippet"]["tags"]) <= 10 else IntUtils.humanize_number(len(vids["items"][0]["snippet"]["tags"]))
            )
        await inter.followup.send(embed=embed)
