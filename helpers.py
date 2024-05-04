from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from twitchAPI.twitch import Twitch, VideoType
from twitchAPI.helper import first
from enum import Enum
import logging
import sys
import datetime
import requests
import os
import json

class LocalizationHelper:
    def __init__(self):
        dir = os.fsencode('i18n/')
        self.locales = {}
        for file in os.listdir(dir):
            fn = os.fsdecode(file)
            if fn.endswith('.json'):
                filename = os.path.splitext(fn)[0]  # Get filename without extension
                with open(os.path.join('i18n', fn), 'r') as f:
                    self.locales[filename] = json.load(f)
    
    def get(self, key, country_code):
        code = country_code.value
        if code in self.locales and key in self.locales[code]:
            return self.locales[code][key]
        else:
            return self.locales["en-US"][key]

locale = LocalizationHelper()

class YtVideoType(str, Enum):
    Video = 'Video'
    StreamScheduled = 'Scheduled Stream'
    StreamOngoing = 'Ongoing Stream'
    StreamFinished = 'Finished Stream'
    VideoPremiereScheduled = 'Scheduled Premiere'
    VideoPremiereOngoing = 'Ongoing Premiere'

class LoggingHelperFormatter(logging.Formatter):
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
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        fileHandler = logging.FileHandler(filename=str.format('logs/y2dl_log_[].log', datetime.datetime.now().date()), encoding='utf-8', mode='w')
        fileHandler.setLevel(logging.DEBUG)
        conHandler = logging.StreamHandler()
        conHandler.setLevel(logging.INFO)
        formatter = LoggingHelperFormatter(fmt="[%(asctime)s %(lvlnme)s] %(message)s", datefmt="%H:%M:%S")
        fileHandler.setFormatter(formatter)
        conHandler.setFormatter(formatter)
        logger.addHandler(fileHandler)
        logger.addHandler(conHandler)

class TwitchHelper:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.twitch_api = None

    async def initialize(self):
        self.twitch_api = await Twitch(self.client_id, self.client_secret)

    async def get_channel(self, login_names, code):
        tw = await first(self.twitch_api.get_users(logins=login_names))
        tw.stream = await first(self.twitch_api.get_streams(user_login=login_names))
        tw.last_stream = await first(self.twitch_api.get_videos(user_id=tw.id, video_type=VideoType.ARCHIVE))
        
        flw = await self.twitch_api.get_channel_followers(tw.id)
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
    def get_dislikes(video_id):
        res = requests.get(f"https://returnyoutubedislikeapi.com/votes?videoId={video_id}")
        return res.json()