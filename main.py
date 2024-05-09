from disnake.ext import commands as cmds
from disnake import Embed, MessageInteraction, Reaction, ModalInteraction
from database import Y2dlDatabase
from config_ui import Y2dlGuildConfig
from utils import EmbedUtils
from helpers import YoutubeHelper, LoggingHelper, ReturnYoutubeDislikeHelper, LocalizationHelper
import commands
import ssl
import config
import asyncio
import logging as log
import datetime

platform, database, bot, logging, services, color = config.load_config()
locale = LocalizationHelper()

class Y2dlMain(cmds.AutoShardedInteractionBot):
    async def on_ready(self):
        db = Y2dlDatabase(database.connection_string)
        for guild in self.guilds:
            if db.get_guild_config(guild.id) == None:
                db.init_guild_config(guild.id)
        log.info(f'Ready as bot "{self.user}"!')        

    async def on_button_click(self, interaction: MessageInteraction):
        if not interaction.message.interaction.author.id == interaction.author.id:
            await interaction.response.send_message(
                embed=EmbedUtils.error(
                    title=locale.get("ERR_NOT_THE_COMMAND_EXECUTOR", interaction.locale),
                    description=locale.get("ERR_NOT_THE_COMMAND_EXECUTOR_DESC", interaction.locale)
                ),
                ephemeral=True
            )
            return
        if interaction.data.custom_id.startswith('gcfg_'):
            await Y2dlGuildConfig.btn_selmenu_recieved(interaction)
        
    async def on_dropdown(self, interaction: MessageInteraction):
        if not interaction.message.interaction.author.id == interaction.author.id:
            await interaction.response.send_message(
                embed=EmbedUtils.error(
                    title=locale.get("ERR_NOT_THE_COMMAND_EXECUTOR", interaction.locale),
                    description=locale.get("ERR_NOT_THE_COMMAND_EXECUTOR_DESC", interaction.locale)
                ),
                ephemeral=True
            )
            return
        if interaction.data.custom_id.startswith('ytpl_'):
            await commands.playlist_vid_selmenu(interaction)
        elif interaction.data.custom_id.startswith('gcfg_'):
            await Y2dlGuildConfig.btn_selmenu_recieved(interaction)

    async def on_modal_submit(self, interaction: MessageInteraction):
        if not interaction.message.interaction.author.id == interaction.author.id:
            await interaction.response.send_message(
                embed=EmbedUtils.error(
                    title=locale.get("ERR_NOT_THE_COMMAND_EXECUTOR", interaction.locale),
                    description=locale.get("ERR_NOT_THE_COMMAND_EXECUTOR_DESC", interaction.locale)
                ),
                ephemeral=True
            )
            return
        if interaction.data.custom_id.startswith("gcfg_"):
            await Y2dlGuildConfig.modal_recieved(interaction)

    async def on_reaction_add(self, reaction: Reaction, user):
        if reaction.emoji == bot.delete_response_emoji:
            if self.user.id == reaction.message.author.id and reaction.message.interaction.author.id == user.id:
                await reaction.message.delete()
            else:
                await reaction.remove(user)

Embed.set_default_colour(int(color.primary, 0))
LoggingHelper.init_logging()
client = Y2dlMain(shard_count=1)
loop = asyncio.get_event_loop()
loop.run_until_complete(commands.init_slash_commands(client))
client.i18n.load('i18n/')
client.run(bot.bot_token)

