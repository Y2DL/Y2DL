from disnake import Localized, ApplicationCommandInteraction, Embed, ui
from helpers import YoutubeHelper, ReturnYoutubeDislikeHelper, TwitchHelper, LocalizationHelper, YtVideoType
from config import load_config
from dateutil import parser
from utils import StringUtils, IntUtils, EmbedUtils
import json
import isodate

platform, database, bot, logging, services, colors = load_config()

async def init_slash_commands(client):
    ytHelper = YoutubeHelper(platform.youtube.api_key)
    twHelper = TwitchHelper(platform.twitch.client_id, platform.twitch.client_secret)
    locale = LocalizationHelper()
    await twHelper.initialize()

    @client.slash_command(
        name="about",
        description=Localized(key="CMD_ABOUT_DESC")
    )
    async def about(inter: ApplicationCommandInteraction):
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
            f'by {locale.get("LANG_TRANSLATOR", inter.locale)}'
        )
        await inter.response.send_message(embed=embed)

    @client.slash_command(
        name="ytinfo",
        description=Localized(key="CMD_YTINFO_DESC")
    )
    async def ytinfo(inter: ApplicationCommandInteraction):
        pass

    @client.slash_command(
        name="twinfo",
        description=Localized(key="CMD_TWINFO_DESC")
    )
    async def twinfo(inter: ApplicationCommandInteraction):
        pass

    @twinfo.sub_command(
        name="broadcaster",
        description=Localized(key="CMD_TWINFO_CHANNEL_DESC")
    )
    async def broadcaster(inter: ApplicationCommandInteraction, login_name_or_id: str):
        await inter.response.defer()
        try:
            chnl = await twHelper.get_channel(login_name_or_id, inter.locale)
            embed = EmbedUtils.primary(
                title = chnl.display_name,
                url = "https://twitch.tv/" + chnl.login,
                description = StringUtils.limit(chnl.description, 100)
            ).set_thumbnail(
                url = chnl.profile_image_url
            ).add_field(
                locale.get("FOLLOWERS", inter.locale),
                IntUtils.humanize_number(chnl.followers),
                inline = True
            ).add_field(
                locale.get("BROADCASTER_TYPE", inter.locale),
                chnl.type_name,
                inline = True
            ).add_field(
                locale.get("CREATED_AT", inter.locale),
                f"<t:{int(chnl.created_at.timestamp())}>",
                inline = True
            )
            if (chnl.stream is not None):
                embed.add_field(
                    locale.get("STREAMING_GAME", inter.locale).format(chnl.stream.game_name),
                    chnl.stream.title,
                    inline = False
                ).add_field(
                    locale.get("VIEWS", inter.locale),
                    IntUtils.humanize_number(chnl.stream.viewer_count),
                    inline = True
                ).add_field(
                    locale.get("STARTED_AT", inter.locale),
                    f"<t:{int(chnl.stream.started_at.timestamp())}>",
                    inline = True
                )
            elif (chnl.last_stream is not None):
                dur = isodate.parse_duration("PT" + chnl.last_stream.duration.upper())
                embed.add_field(
                    locale.get("PREVIOUSLY_STREAMED", inter.locale),
                    f"[**{chnl.last_stream.title}**](https://twitch.tv/videos/{chnl.last_stream.id})\n{chnl.description}",
                    inline = False
                ).add_field(
                    locale.get("VIEWS", inter.locale),
                    IntUtils.humanize_number(chnl.last_stream.view_count),
                    inline = True
                ).add_field(
                    locale.get("DURATION", inter.locale),
                    dur,
                    inline = True
                ).add_field(
                    locale.get("STARTED_AT", inter.locale),
                    f"<t:{int(chnl.last_stream.created_at.timestamp())}>",
                    inline = True
                )
            await inter.followup.send(embed=embed)
        except:
            await inter.followup.send(
                embed=EmbedUtils.error(
                    title=locale.get("ERR_FETCH_STREAMER", inter.locale),
                    description=locale.get("ERR_FETCH_STREAMER_DESC", inter.locale)
                )
            )

    @ytinfo.sub_command(
        name="channel",
        description=Localized(key="CMD_YTINFO_CHANNEL_DESC")
    )
    async def channel(inter: ApplicationCommandInteraction, channel_id: str = None, channel_handle: str = None):
        await inter.response.defer()
        if (channel_id is None and channel_handle is None) or (channel_id != None and channel_handle != None):
            await inter.followup.send(
                embed=EmbedUtils.error(
                    title=locale.get("ERR_CMD_CHNL_TOO_MANY", inter.locale),
                    description=locale.get("ERR_CMD_CHNL_TOO_MANY_DESC", inter.locale)
                )
            )
            return
        chnls = ytHelper.get_channels(channel_id, channel_handle)

        if ("items" not in chnls or len(chnls["items"]) < 1):
            await inter.followup.send(
                embed=EmbedUtils.error(
                    title=locale.get("ERR_FETCH_CHANNEL", inter.locale),
                    description=locale.get("ERR_FETCH_CHANNEL_DESC", inter.locale),
                )
            )
            return
        vids = ytHelper.get_playlistitems(chnls["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"])
        pub_at = int(parser.parse(chnls["items"][0]["snippet"]["publishedAt"]).timestamp())
        embed = EmbedUtils.primary(
            title = chnls["items"][0]["snippet"]["title"] + f' ({chnls["items"][0]["snippet"]["customUrl"]})',
            url = "https://youtube.com/" + chnls["items"][0]["snippet"]["customUrl"],
            description = StringUtils.limit(chnls["items"][0]["snippet"]["description"], 100),
        ).set_thumbnail(
            url = chnls["items"][0]["snippet"]["thumbnails"]["high"]["url"]
        ).add_field(
            locale.get("SUBSCRIBERS", inter.locale),
            IntUtils.humanize_number(chnls["items"][0]["statistics"]["subscriberCount"]),
            inline = True
        ).add_field(
            locale.get("VIEWS", inter.locale),
            IntUtils.humanize_number(chnls["items"][0]["statistics"]["viewCount"]),
            inline = True
        ).add_field(
            locale.get("VIDEOS", inter.locale),
            IntUtils.humanize_number(chnls["items"][0]["statistics"]["videoCount"]),
            inline = True
        ).add_field(
            locale.get("CREATED_AT", inter.locale),
            f"<t:{pub_at}>",
            inline = True
        )
        if ("items" in vids and len(vids["items"]) > 1):
            vid = ytHelper.get_videos(vids["items"][0]["snippet"]["resourceId"]["videoId"])
            ryd_res = ReturnYoutubeDislikeHelper.get_dislikes(vids["items"][0]["snippet"]["resourceId"]["videoId"])
            pub_at_vid = int(parser.parse(vids["items"][0]["snippet"]["publishedAt"]).timestamp())
            dur = isodate.parse_duration(vid["items"][0]["contentDetails"]["duration"])
            embed.add_field(
                locale.get("LATEST_CONTENT", inter.locale).format(vid["items"][0]["snippet"]["videoType"].toLocale(inter.locale)),
                f'[**{vids["items"][0]["snippet"]["title"]}**](https://youtu.be/{vids["items"][0]["snippet"]["resourceId"]["videoId"]})\n' +
                StringUtils.limit(vids["items"][0]["snippet"]["description"], 100),
                inline = False
            ).add_field(
                locale.get("VIEWS", inter.locale),
                IntUtils.humanize_number(vid["items"][0]["statistics"]["viewCount"]),
                inline = True
            ).add_field(
                locale.get("LIKES", inter.locale),
                IntUtils.humanize_number(vid["items"][0]["statistics"]["likeCount"]),
                inline = True
            ).add_field(
                locale.get("DISLIKES", inter.locale),
                IntUtils.humanize_number(ryd_res["dislikes"]),
                inline = True
            ).add_field(
                locale.get("COMMENTS", inter.locale),
                IntUtils.humanize_number(vid["items"][0]["statistics"]["commentCount"]),
                inline = True
            ).add_field(
                locale.get("PUBLISHED_AT", inter.locale),
                f"<t:{pub_at_vid}>",
                inline = True
            ).add_field(
                locale.get("DURATION", inter.locale),
                dur,
                inline = True
            ).set_footer(
                text = locale.get("DISLIKES_NOTE", inter.locale)
            )

        await inter.followup.send(embed=embed)

    @ytinfo.sub_command(
        name="video",
        description=Localized(key="CMD_YTINFO_VIDEO_DESC")
    )
    async def video(inter: ApplicationCommandInteraction, video_id: str):
        await inter.response.defer()
        vids = ytHelper.get_videos(video_id)
        if ("items" not in vids or len(vids["items"]) < 1):
            await inter.followup.send(
                embed=EmbedUtils.error(
                    title=locale.get("ERR_FETCH_VIDEO", inter.locale),
                    description=locale.get("ERR_FETCH_VIDEO_DESC", inter.locale)
                )
            )
            return
        pub_at = int(parser.parse(vids["items"][0]["snippet"]["publishedAt"]).timestamp())
        ryd_res = ReturnYoutubeDislikeHelper.get_dislikes(vids["items"][0]["id"])
        dur = isodate.parse_duration(vids["items"][0]["contentDetails"]["duration"])
        embed = EmbedUtils.primary(
            title = vids["items"][0]["snippet"]["title"],
            url = "https://youtu.be/" + vids["items"][0]["id"],
            description = StringUtils.limit(vids["items"][0]["snippet"]["description"], 100),
        ).set_author(
            name = vids["items"][0]["snippet"]["channelTitle"],
            url = "https://youtube.com/channel/" + vids["items"][0]["snippet"]["channelId"]
        ).set_thumbnail(
            url = vids["items"][0]["snippet"]["thumbnails"]["medium"]["url"]
        ).add_field(
            locale.get("VIEWS", inter.locale),
            IntUtils.humanize_number(vids["items"][0]["statistics"]["viewCount"]),
            inline = True
        ).add_field(
            locale.get("LIKES", inter.locale),
            IntUtils.humanize_number(vids["items"][0]["statistics"]["likeCount"]),
            inline = True
        ).add_field(
            locale.get("DISLIKES", inter.locale),
            IntUtils.humanize_number(ryd_res["dislikes"]),
            inline = True
        ).add_field(
            locale.get("COMMENTS", inter.locale),
            IntUtils.humanize_number(vids["items"][0]["statistics"]["commentCount"]),
            inline = True
        ).add_field(
            locale.get("PUBLISHED_AT", inter.locale),
            f"<t:{pub_at}>",
            inline = True
        ).add_field(
            locale.get("DURATION", inter.locale),
            dur,
            inline = True
        ).add_field(
            locale.get("PUBLICITY", inter.locale),
            vids["items"][0]["status"]["privacyStatus"].capitalize(),
            inline = True
        ).add_field(
            locale.get("VIDEO_TYPE", inter.locale),
            vids["items"][0]["snippet"]["videoType"].toLocale(inter.locale),
            inline = True
        ).add_field(
            locale.get("LICENSE", inter.locale),
            vids["items"][0]["status"]["license"].capitalize(),
            inline = True
        ).set_footer(
            text = locale.get("DISLIKES_NOTE", inter.locale)
        )
        if "tags" in vids["items"][0]["snippet"]:
            embed.add_field(
                "Tags" + f' ({len(vids["items"][0]["snippet"]["tags"])})' if len(vids["items"][0]["snippet"]["tags"]) <= 15 else "",
                ", ".join(vids["items"][0]["snippet"]["tags"]) if len(vids["items"][0]["snippet"]["tags"]) <= 15 else IntUtils.humanize_number(len(vids["items"][0]["snippet"]["tags"]))
            )
        await inter.followup.send(embed=embed)
