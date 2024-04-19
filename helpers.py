from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
import sys
import datetime
import requests

class LoggingHelper:
    def init_logging():
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        fileHandler = logging.FileHandler(filename=str.format('logs/y2dl_log_{}.log', datetime.datetime.now()), encoding='utf-8', mode='w')
        fileHandler.setLevel(logging.DEBUG)
        conHandler = logging.StreamHandler()
        conHandler.setLevel(logging.INFO)
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S")
        fileHandler.setFormatter(formatter)
        conHandler.setFormatter(formatter)
        logger.addHandler(fileHandler)
        logger.addHandler(conHandler)

class YoutubeHelper:
    def __init__(self, api_key):
        self.yt_api = build('youtube', 'v3', developerKey=api_key)

    def get_channels(self, channel_ids):
        req = self.yt_api.channels().list(
            part = 'snippet,statistics,contentDetails',
            id = channel_ids,
            maxResults = 50
        )
        res = req.execute()
        return res

    def get_videos(self, video_ids):
        req = self.yt_api.videos().list(
            part = 'snippet,statistics,contentDetails,liveStreamingDetails',
            id = video_ids,
            maxResults = 50
        )
        res = req.execute()
        return res

class ReturnYoutubeDislikeHelper:
    def get_dislikes(video_id):
        res = requests.get(f"https://returnyoutubedislikeapi.com/votes?videoId={video_id}")
        return res.json()