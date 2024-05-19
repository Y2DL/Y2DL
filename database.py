from pymongo import MongoClient
import logging
import time

class Y2dlDatabase:
    def __init__(self, connection_string):
        
        self.client = MongoClient(connection_string)
        self.db = self.client["y2dl"]

    def get_tw_tkn(self, login_name):
        tkns = self.db["twitch_auths"]
        query = { "_id": login_name }
        tkn = tkns.find(query, limit=1)
        return None if tkns.count_documents(query, limit=1) < 1 else tkn if tkn else None

    def del_tw_tkn(self, login_name):
        tkns = self.db["twitch_auths"]
        query = { "_id": login_name }
        tkn = tkns.count_documents(query, limit=1)
        if tkn >= 1:
            tkns.delete_one(query)

    def set_tw_tkn(self, login_name, refresh_token, access_token):
        tkns = self.db["twitch_auths"]
        query = { "_id": login_name }
        def_cfg = {
            "_id": login_name,
            "refresh_token": refresh_token,
            "access_token": access_token
        }
        tkn = tkns.count_documents(query, limit=1)
        if tkn < 1:
            tkns.insert_one(def_cfg)
        else:
            tkns.update_one(query, def_cfg)

    def get_guild_config(self, guild_id):
        cfgs = self.db["guild_config"]
        query = { "_id": f"{guild_id}" }
        cfg = cfgs.find(query, limit=1)
        return None if cfgs.count_documents(query, limit=1) < 1 else cfg if cfg else None

    def init_guild_config(self, guild_id):
        cfgs = self.db["guild_config"]
        def_cfg = {
            "_id": f"{guild_id}",
            "youtube": {
                "enabled": False,
                "channels": []
            },
            "twitch": {
                "enabled": False,
                "channels": []
            }
        }
        query = { "_id": f"{guild_id}" }
        cfg = cfgs.count_documents(query, limit=1)
        if cfg < 1:
            cfgs.insert_one(def_cfg)
            logging.info(f'Configured guild {guild_id}')

    def del_guild_config(self, guild_id):
        cfgs = self.db["guild_config"]
        query = { "_id": f"{guild_id}" }
        cfg = cfgs.count_documents(query, limit=1)
        if cfg >= 1:
            cfgs.delete_one(query)

    def set_guild_config(self, guild_id, guild_config):
        cfgs = self.db["guild_config"]
        query = { "_id": f"{guild_id}" }
        cfg = cfgs.count_documents(query, limit=1)
        if cfg >= 1:
            cfgs.update_one(query, {"$set": guild_config})

    def latency(self):
        start_time = time.time()
        server_info = self.client.server_info()
        latency_seconds = time.time() - start_time
        latency_ms = latency_seconds * 1000.0
        return latency_ms