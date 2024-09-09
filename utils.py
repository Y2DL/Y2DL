import requests
from typing import Union, Optional, Any
from discord import Embed, Colour
from discord.types.embed import EmbedType
import datetime
from config import load_config
import re

platform, database, bot, logging, services, color = load_config()

class StringUtils:
    def limit(input_str, max_length):
        if input_str is None:
            raise ValueError("input_str cannot be None")
        if max_length <= 0:
            raise ValueError("max_length must be greater than zero")
        if len(input_str) <= max_length:
            return input_str        
        return input_str[:max_length - 3].rstrip('\n ') + "..."

    def smallify(input_str: str, link_handles: bool = True):
        if link_handles:
            out = re.sub(r'@(\S+)', '[@\\1](https://youtube.com/@\\1)', input_str, flags=re.MULTILINE)
        else:
            out = input_str
        out = re.sub(r'\n(.)', '\n-# \\1', out, flags=re.MULTILINE)

        return '-# ' + out

class IntUtils:
    def humanize_number(number):
        num_suffixes = ["", "K", "M", "B", "T"]
        magnitude = 0
        if not isinstance(number, float):
            number = float(number)
        while abs(number) >= 1000 and magnitude < len(num_suffixes) - 1:
            magnitude += 1
            number /= 1000.0
        formatted_number = "{:.2f}{}".format(number, num_suffixes[magnitude]) if num_suffixes[magnitude] else "{:.0f}".format(number)
        return formatted_number

class EmbedUtils:
    def primary(*, title: Optional[Any]=None, description: Optional[Any]=None, url: Optional[Any]=None):
        return Embed(title = title, description = description, url = url, color = int(color.primary, 0))
    
    def secondary(*, title: Optional[Any]=None, description: Optional[Any]=None, url: Optional[Any]=None):
        return Embed(title = title, description = description, url = url, color = int(color.secondary, 0))

    def success(*, title: Optional[Any]=None, description: Optional[Any]=None, url: Optional[Any]=None):
        return Embed(title = title, description = description, url = url, color = int(color.success, 0))

    def error(*, title: Optional[Any]=None, description: Optional[Any]=None, url: Optional[Any]=None):
        return Embed(title = title, description = description, url = url, color = int(color.error, 0))

    def invis(*, title: Optional[Any]=None, description: Optional[Any]=None, url: Optional[Any]=None):
        return Embed(title = title, description = description, url = url, color = int(color.invis, 0))