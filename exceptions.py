class InvalidGuildException(Exception):
    "Raised when guild is not found in the database. Also wraps Discord API Invalid Guild errors."
    pass

class InvalidNotifException(Exception):
    "Raised when notification config is not found in the database."
    pass