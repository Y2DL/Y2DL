from pymongo import MongoClient
import logging

class Y2dlDatabase:
    def __init__(self, connection_string):
        client = MongoClient(connection_string)
        self.db = client["y2dl"]

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