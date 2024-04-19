from pymongo import MongoClient

class Y2dlDatabase:
    def __init__(self, connection_string):
        client = MongoClient(connection_string)
        self.db = client["y2dl"]

    def get_guild_config(self, guild_id):
        cfgs = self.db["guild_config"]
        query = { "guild_id": f"{guild_id}" }
        cfg = cfgs.find(query)
        return cfg if cfg else None

    def init_guild_config(self, guild_id):
        cfgs = self.db["guild_config"]
        def_cfg = {
            "guild_id": f"{guild_id}",
            "youtube": {
                "dynamic_channel_message_info": {
                    "enabled": False,
                    "channels": []
                },
                "dynamic_channel_vcname_info": {
                    "enabled": False,
                    "channels": []
                },
                "channel_releases": {
                    "enabled": False,
                    "channels": []
                },
                "milestone_notifications": {
                    "enabled": False,
                    "channels": []
                }
            },
            "twitch": {
                "dynamic_channel_message_info": {
                    "enabled": False,
                    "channels": []
                },
                "dynamic_channel_vcname_info": {
                    "enabled": False,
                    "channels": []
                },
                "event_notifications": {
                    "enabled": False,
                    "channels": []
                },
                "milestone_notifications": {
                    "enabled": False,
                    "channels": []
                }
            }
        }
        query = { "guild_id": f"{guild_id}" }
        cfg = cfgs.find(query)
        if not cfg:
            cfgs.insert_one(def_cfg)

    def del_guild_config(self, guild_id):
        cfgs = self.db["guild_config"]
        query = { "guild_id": f"{guild_id}" }
        cfg = cfgs.find(query)
        if cfg:
            cfgs.delete_one(query)

    def set_guild_config(self, guild_id, guild_config):
        cfgs = self.db["guild_config"]
        query = { "guild_id": f"{guild_id}" }
        cfg = cfgs.find(query)
        if cfg:
            cfgs.update_one(query, {"$set": guild_config})