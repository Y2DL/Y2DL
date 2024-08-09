from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from twitchAPI.twitch import Twitch, VideoType
from twitchAPI.helper import first
from enum import Enum
from cachetools.func import ttl_cache
from cachetools import TTLCache
from asyncache import cached
from dateutil import parser
from utils import StringUtils, IntUtils, EmbedUtils
import json
import isodate
import logging as log
import config
import sys
import datetime
import requests
import os
import re

platform, database, bot, logging, services, color = config.load_config()

class LocalizationHelper:
    def __init__(self):
        dir = os.fsencode('i18n/')
        self.locales = {}
        for file in os.listdir(dir):
            fn = os.fsdecode(file)
            if fn.endswith('.json'):
                filename = os.path.splitext(fn)[0]
                with open(os.path.join('i18n', fn), 'r', encoding="utf-8" ) as f:
                    self.locales[filename] = json.load(f)
    
    def get(self, key, country_code):
        code = country_code.value if hasattr(country_code, "value") else country_code
        if code in self.locales and key in self.locales[code]:
            return self.locales[code][key]
        else:
            return self.locales["en-US"][key]

locale = LocalizationHelper()

class YtVideoType(str, Enum):
    Video = 'YTVIDTYPE_VIDEO'
    StreamSchesduled = 'YTVIDTYPE_STR_SCHEDULED'
    StreamOngoing = 'YTVIDTYPE_STR_ONGOING'
    StreamFinished = 'YTVIDTYPE_STR_FINISHED'
    VideoPremiereScheduled = 'YTVIDTYPE_PRE_SCHEDULED'
    VideoPremiereOngoing = 'YTVIDTYPE_PRE_ONGOING'
    def toLocale(self, country_code):
        return locale.get(self.value, country_code)

class LoggingHelperFormatter(log.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%'):
        mapping = {
            'DEBUG': 'DBG',
            'INFO': 'INF',
            'WARNING': 'WRN',
            'ERROR': 'ERR',
            'CRITICAL': 'CRT'
        }
        super().__init__(fmt, datefmt, style)
        self.mapping = mapping

    def format(self, record):
        record.lvlnme = self.mapping.get(record.levelname, record.levelname)
        return super().format(record)

class LoggingHelper:
    def init_logging():
        logger = log.getLogger()
        logger.setLevel(log.DEBUG)
        fileHandler = log.FileHandler(filename=str.format('logs/y2dl_log_[].log', datetime.datetime.now().date()), encoding='utf-8', mode='w')
        fileHandler.setLevel(log.DEBUG)
        conHandler = log.StreamHandler()
        conHandler.setLevel(log.INFO)
        formatter = LoggingHelperFormatter(fmt="[%(asctime)s %(lvlnme)s] %(message)s", datefmt="%H:%M:%S")
        fileHandler.setFormatter(formatter)
        conHandler.setFormatter(formatter)
        logger.addHandler(fileHandler)
        logger.addHandler(conHandler)

class TwitchHelper:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

    @cached(TTLCache(maxsize=64, ttl=600))
    async def get_channel(self, login_names, code):
        twitch_api = await Twitch(self.client_id, self.client_secret)
        tw = await first(twitch_api.get_users(logins=login_names))
        tw.stream = await first(twitch_api.get_streams(user_login=login_names))
        tw.last_stream = await first(twitch_api.get_videos(user_id=tw.id, video_type=VideoType.ARCHIVE))
        
        flw = await twitch_api.get_channel_followers(tw.id)
        tw.followers = flw.total
        if tw.broadcaster_type == "affiliate":
            tw.type_name = locale.get("TWTYPE_AFFILIATE", code)
        elif tw.broadcaster_type == "partner":
            tw.type_name = locale.get("TWTYPE_PARTNER", code)
        else:
            tw.type_name = locale.get("TWTYPE_DEFAULT", code)
        return tw

class YoutubeHelper:
    def __init__(self, api_key):
        self.yt_api = build('youtube', 'v3', developerKey=api_key)

    @ttl_cache(maxsize=64, ttl=600)
    def get_playlist_info(self, playlist_id):
        req = self.yt_api.playlists().list(
            part = 'snippet,contentDetails,status',
            id = playlist_id,
            maxResults = 50
        )
        try:
            res = req.execute()
            return res
        except:
            return {"items": []}

    @ttl_cache(maxsize=64, ttl=600)
    def get_playlistitems(self, playlist_id):
        req = self.yt_api.playlistItems().list(
            part = 'snippet,contentDetails',
            playlistId = playlist_id,
            maxResults = 50
        )
        try:
            res = req.execute()
            return res
        except:
            return {"items": []}

    @ttl_cache(maxsize=64, ttl=600)
    def get_channels(self, channel_ids = None, channel_handle = None):
        req = self.yt_api.channels().list(
            part = 'snippet,statistics,contentDetails',
            id = channel_ids,
            forHandle = channel_handle,
            maxResults = 50
        )
        try:
            res = req.execute()
            return res
        except:
            return {"items": []}

    @ttl_cache(maxsize=64, ttl=600)
    def get_videos(self, video_ids):
        req = self.yt_api.videos().list(
            part = 'snippet,statistics,contentDetails,liveStreamingDetails,status',
            id = video_ids,
            maxResults = 50
        )
        try:
            res = req.execute()
            for item in res["items"]:
                vidType = YtVideoType.Video
                if "liveStreamingDetails" in item:
                    if item["snippet"]["liveBroadcastContent"] == "none":
                        if "actualEndTime" in item["liveStreamingDetails"]:
                            vidType = YtVideoType.StreamFinished
                    elif item["status"]["uploadStatus"] == "processed":
                        if "actualStartTime" in item["liveStreamingDetails"]:
                            vidType = YtVideoType.VideoPremiereOngoing
                        else:
                            vidType = YtVideoType.VideoPremiereScheduled
                    elif item["status"]["uploadStatus"] == "uploaded":
                        if "concurrentViewers" in item["liveStreamingDetails"]:
                            vidType = YtVideoType.StreamOngoing
                        else:
                            vidType = YtVideoType.StreamScheduled
                res["items"][res["items"].index(item)]["snippet"]["videoType"] = vidType
            return res
        except:
            return {"items": []}

class ReturnYoutubeDislikeHelper:
    @ttl_cache(maxsize=64, ttl=600)
    def get_dislikes(video_id):
        res = requests.get(f"https://returnyoutubedislikeapi.com/votes?videoId={video_id}")
        return res.json()

class DeArrowHelper:
    @ttl_cache(maxsize=64, ttl=600)
    def get_branding(video_id):
        res = requests.get(f"https://sponsor.ajay.app/api/branding?videoID={video_id}")
        return res.json()

class EmbedHelper:
    def __init__(self):
        self.ytHelper = YoutubeHelper(platform.youtube.api_key)
        self.twHelper = TwitchHelper(platform.twitch.client_id, platform.twitch.client_secret)
        locale = LocalizationHelper()

    async def initialize_twitch(self):
        await self.twHelper.initialize()

    async def get_tw_streamer(self, userLocale, login_name):
        try:
            chnl = await self.twHelper.get_channel(login_name, locale)
            embed = EmbedUtils.primary(
                title = chnl.display_name,
                url = "https://twitch.tv/" + chnl.login,
                description = StringUtils.limit(chnl.description, 100)
            ).set_thumbnail(
                url = chnl.profile_image_url
            ).add_field(
                name=locale.get("FOLLOWERS", userLocale),
                value=IntUtils.humanize_number(chnl.followers),
                inline = True
            ).add_field(
                name=locale.get("BROADCASTER_TYPE", userLocale),
                value=chnl.type_name,
                inline = True
            ).add_field(
                name=locale.get("CREATED_AT", userLocale),
                value=f"<t:{int(chnl.created_at.timestamp())}>",
                inline = True
            )
            if (chnl.stream is not None):
                embed.add_field(
                    name=locale.get("STREAMING_GAME", locale).format(chnl.stream.game_name),
                    value=chnl.stream.title,
                    inline = False
                ).add_field(
                    name=locale.get("VIEWS", userLocale),
                    value=IntUtils.humanize_number(chnl.stream.viewer_count),
                    inline = True
                ).add_field(
                    name=locale.get("STARTED_AT", userLocale),
                    value=f"<t:{int(chnl.stream.started_at.timestamp())}>",
                    inline = True
                )
            elif (chnl.last_stream is not None):
                dur = isodate.parse_duration("PT" + chnl.last_stream.duration.upper())
                embed.add_field(
                    name=locale.get("PREVIOUSLY_STREAMED", userLocale),
                    value=f"[**{chnl.last_stream.title}**](https://twitch.tv/videos/{chnl.last_stream.id})\n{chnl.description}",
                    inline = False
                ).add_field(
                    name=locale.get("VIEWS", userLocale),
                    value=IntUtils.humanize_number(chnl.last_stream.view_count),
                    inline = True
                ).add_field(
                    name=locale.get("DURATION", userLocale),
                    value=dur,
                    inline = True
                ).add_field(
                    name=locale.get("STARTED_AT", userLocale),
                    value=f"<t:{int(chnl.last_stream.created_at.timestamp())}>",
                    inline = True
                )
            return embed
        except:
            return EmbedUtils.error(
                title=locale.get("ERR_FETCH_STREAMER", userLocale),
                description=locale.get("ERR_FETCH_STREAMER_DESC", locale)
            )

    def get_yt_channel(self, userLocale, channel_id = None, channel_handle = None):
        if (channel_id is None and channel_handle is None) or (channel_id != None and channel_handle != None):
            vids = None
            title = None
            return EmbedUtils.error(
                title=locale.get("ERR_CMD_CHNL_TOO_MANY", userLocale),
                description=locale.get("ERR_CMD_CHNL_TOO_MANY_DESC", locale)
            ), vids, title
        chnls = self.ytHelper.get_channels(channel_id, channel_handle)
        if ("items" not in chnls or len(chnls["items"]) < 1):
            vids = None
            title = None
            return EmbedUtils.error(
                title=locale.get("ERR_FETCH_CHANNEL", userLocale),
                description=locale.get("ERR_FETCH_CHANNEL_DESC", userLocale),
            ), vids, title
        vids = self.ytHelper.get_playlistitems(chnls["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"])
        pub_at = int(parser.parse(chnls["items"][0]["snippet"]["publishedAt"]).timestamp())
        embed = EmbedUtils.primary(
            title = chnls["items"][0]["snippet"]["title"] + f' ({chnls["items"][0]["snippet"]["customUrl"]})',
            url = "https://youtube.com/" + chnls["items"][0]["snippet"]["customUrl"],
            description = StringUtils.limit(chnls["items"][0]["snippet"]["description"], 100),
        ).set_thumbnail(
            url = chnls["items"][0]["snippet"]["thumbnails"]["high"]["url"]
        ).add_field(
            name=locale.get("SUBSCRIBERS", userLocale),
            value=IntUtils.humanize_number(chnls["items"][0]["statistics"]["subscriberCount"]),
            inline = True
        ).add_field(
            name=locale.get("VIEWS", userLocale),
            value=IntUtils.humanize_number(chnls["items"][0]["statistics"]["viewCount"]),
            inline = True
        ).add_field(
            name=locale.get("VIDEOS", userLocale),
            value=IntUtils.humanize_number(chnls["items"][0]["statistics"]["videoCount"]),
            inline = True
        ).add_field(
            name=locale.get("CREATED_AT", userLocale),
            value=f"<t:{pub_at}>",
            inline = True
        )
        if ("items" in vids and len(vids["items"]) > 1):
            vid = self.ytHelper.get_videos(vids["items"][0]["snippet"]["resourceId"]["videoId"])
            ryd_res = ReturnYoutubeDislikeHelper.get_dislikes(vids["items"][0]["snippet"]["resourceId"]["videoId"])
            pub_at_vid = int(parser.parse(vids["items"][0]["snippet"]["publishedAt"]).timestamp())
            dur = isodate.parse_duration(vid["items"][0]["contentDetails"]["duration"])
            embed.add_field(
                name=locale.get("LATEST_CONTENT", locale).format(vid["items"][0]["snippet"]["videoType"].toLocale(locale)),
                value= f'[**{vids["items"][0]["snippet"]["title"]}**](https://youtu.be/{vids["items"][0]["snippet"]["resourceId"]["videoId"]})\n' +
                StringUtils.limit('-# ' + re.sub(r'\n(.)', '\n-# \\1', re.sub(r'@(\S+)', '[@\\1](https://youtube.com/@\\1)', vids["items"][0]["snippet"]["description"], flags=re.MULTILINE), flags=re.MULTILINE), 100),
                inline = False
            ).add_field(
                name=locale.get("VIEWS", userLocale),
                value=IntUtils.humanize_number(vid["items"][0]["statistics"]["viewCount"]),
                inline = True
            ).add_field(
                name=locale.get("LIKES", userLocale),
                value=IntUtils.humanize_number(vid["items"][0]["statistics"]["likeCount"]),
                inline = True
            ).add_field(
                name=locale.get("DISLIKES", userLocale),
                value=IntUtils.humanize_number(ryd_res["dislikes"]),
                inline = True
            ).add_field(
                name=locale.get("COMMENTS", userLocale),
                value=IntUtils.humanize_number(vid["items"][0]["statistics"]["commentCount"]),
                inline = True
            ).add_field(
                name=locale.get("PUBLISHED_AT", userLocale),
                value=f"<t:{pub_at_vid}>",
                inline = True
            ).add_field(
                name=locale.get("DURATION", userLocale),
                value=dur,
                inline = True
            ).set_footer(
                text = locale.get("DISLIKES_NOTE", userLocale)
            )
        title = chnls["items"][0]["snippet"]["title"]
        return embed, vids, title

    def get_yt_video(self, userLocale, video_id):
        vids = self.ytHelper.get_videos(video_id)
        if ("items" not in vids or len(vids["items"]) < 1):
            return EmbedUtils.error(
                title=locale.get("ERR_FETCH_VIDEO", userLocale),
                description=locale.get("ERR_FETCH_VIDEO_DESC", locale)
            )
        pub_at = int(parser.parse(vids["items"][0]["snippet"]["publishedAt"]).timestamp())
        ryd_res = ReturnYoutubeDislikeHelper.get_dislikes(vids["items"][0]["id"])
        dur = isodate.parse_duration(vids["items"][0]["contentDetails"]["duration"])
        embed = EmbedUtils.primary(
            title = vids["items"][0]["snippet"]["title"],
            url = "https://youtu.be/" + vids["items"][0]["id"],
            description = StringUtils.limit(re.sub(r'@(\S+)', '[@\\1](https://youtube.com/@\\1)', vids["items"][0]["snippet"]["description"], flags=re.MULTILINE), 100),
        ).set_author(
            name = vids["items"][0]["snippet"]["channelTitle"],
            url = "https://youtube.com/channel/" + vids["items"][0]["snippet"]["channelId"]
        ).set_thumbnail(
            url = vids["items"][0]["snippet"]["thumbnails"]["medium"]["url"]
        )

        dea = DeArrowHelper.get_branding(vids["items"][0]["id"])
        if len(dea["titles"]) >= 1 and dea["titles"][0]["original"] == False:
            embed.add_field(
                name=locale.get("DEARROW_TITLE", userLocale),
                value=dea["titles"][0]["title"],
                inline=False
            )
        
        embed.add_field(
            name=locale.get("VIEWS", userLocale),
            value=IntUtils.humanize_number(vids["items"][0]["statistics"]["viewCount"]),
            inline = True
        ).add_field(
            name=locale.get("LIKES", userLocale),
            value=IntUtils.humanize_number(vids["items"][0]["statistics"]["likeCount"]),
            inline = True
        ).add_field(
            name=locale.get("DISLIKES", userLocale),
            value=IntUtils.humanize_number(ryd_res["dislikes"]),
            inline = True
        ).add_field(
            name=locale.get("COMMENTS", userLocale),
            value=IntUtils.humanize_number(vids["items"][0]["statistics"]["commentCount"]),
            inline = True
        ).add_field(
            name=locale.get("PUBLISHED_AT", userLocale),
            value=f"<t:{pub_at}>",
            inline = True
        ).add_field(
            name=locale.get("DURATION", userLocale),
            value=dur,
            inline = True
        ).add_field(
            name=locale.get("PUBLICITY", userLocale),
            value=vids["items"][0]["status"]["privacyStatus"].capitalize(),
            inline = True
        ).add_field(
            name=locale.get("VIDEO_TYPE", userLocale),
            value=vids["items"][0]["snippet"]["videoType"].toLocale(userLocale),
            inline = True
        ).add_field(
            name=locale.get("LICENSE", userLocale),
            value=vids["items"][0]["status"]["license"].capitalize(),
            inline = True
        ).set_footer(
            text = locale.get("DISLIKES_NOTE", userLocale)
        )
        if "tags" in vids["items"][0]["snippet"]:
            embed.add_field(
                name=locale.get("TAGS", userLocale) + f' ({len(vids["items"][0]["snippet"]["tags"])})' if len(vids["items"][0]["snippet"]["tags"]) <= 15 else locale.get("TAGS", userLocale),
                value=", ".join(vids["items"][0]["snippet"]["tags"]) if len(vids["items"][0]["snippet"]["tags"]) <= 15 else IntUtils.humanize_number(len(vids["items"][0]["snippet"]["tags"]))
            )
        return embed