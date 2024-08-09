from discord import app_commands, Embed, ui, MessageInteraction, Permissions, AllowedMentions, SelectOption, Interaction
from discord.ext import commands
from discord.ext.commands import Context
from helpers import YoutubeHelper, ReturnYoutubeDislikeHelper, TwitchHelper, LocalizationHelper, YtVideoType, EmbedHelper, locale
from config import load_config
from dateutil import parser
from utils import StringUtils, IntUtils, EmbedUtils
from database import Y2dlDatabase
from bson.json_util import dumps
import json
import asyncio
import isodate

class Y2dlOther(commands.Cog, name="Other Commands", description="Meta/other commands for the bot"):
    def __init__(self, bot):
        self.dbot = bot
        self._last_member = None
        self.platform, self.database, self.bot, self.logging, self.services, self.color = load_config()

    @commands.hybrid_command(
        name="about",
        description="About the bot or Y2DL",
        usage="{pr}about"
    )
    async def about(self, ctx: Context):
        ver = "v2.0.0"
        embed = EmbedUtils.secondary(
            title = ctx.bot.user.name,
        ).set_thumbnail(
            url = ctx.bot.user.avatar.url
        ).add_field(
            name=locale.get("Y2DL_VER", "en-US").format(ver),
            value="by jbcarreon123",
            inline=True
        ).add_field(
            name=f'Language: {locale.get("LANG_NAME", "en-US")}',
            value=f'by {locale.get("LANG_TRANSLATOR", "en-US")}',
            inline=True
        )
        await ctx.reply(embed=embed, allowed_mentions=AllowedMentions.none())

    @commands.hybrid_command(
        name="ping",
        description=app_commands.locale_str("CMD_PING_DESC"),
        usage="{pr}ping"
    )
    async def ping(self, ctx: Context):
        db = Y2dlDatabase(self.database.connection_string)
        embed = EmbedUtils.secondary(
            title = "Pong!"
        ).add_field(
            name=locale.get("API_LATENCY", "en-US"),
            value=f"{round(self.dbot.latency * 1000.0, 2)}ms",
            inline = True
        ).add_field(
            name=locale.get("DB_LATENCY", "en-US"),
            value=f"{round(db.latency(), 2)}ms",
            inline = True
        )
        await ctx.reply(embed=embed, allowed_mentions=AllowedMentions.none())

    @commands.hybrid_command(
        name="help",
        description="Get some help.",
        usage="{pr}help"
    )
    async def help(self, ctx: Context):
        view = HelpSelectView(self.dbot, ctx.author.id, self.dbot.cogs)
        
        await ctx.reply("Y2DL Help", view=view, allowed_mentions=AllowedMentions.none())

class HelpSelect(ui.Select):
    def __init__(self, bot, author, cogs):
        opts = []
        for c in cogs:
            cog = bot.get_cog(c)
            opts.append(SelectOption(
                label=cog.qualified_name, value=c, description=cog.description
            ))
        super().__init__(placeholder="Choose a cog on the list", min_values=1, max_values=1, options=opts)
        self.author = author
        self.dbot = bot
        self.embedHlpr = EmbedHelper()
        self.platform, self.database, self.bot, self.logging, self.services, self.color = load_config()

    async def callback(self, interaction: Interaction):
        if interaction.user.id != self.author:
            await interaction.response.send_message(
                embed=EmbedUtils.error(
                    title=locale.get("ERR_NOT_THE_COMMAND_EXECUTOR", interaction.locale),
                    description=locale.get("ERR_NOT_THE_COMMAND_EXECUTOR_DESC", interaction.locale)
                ),
                ephemeral=True
            )
            return
        await interaction.response.defer()
        cog: commands.Cog = self.dbot.get_cog(self.values[0])
        cmds = cog.walk_commands()
        embed = EmbedUtils.primary(
            title=cog.qualified_name,
            description=cog.description
        )
        for cmd in cmds:
            if cmd.usage is None: continue
            embed.add_field(
                name=f"{self.bot.prefix}{f'{cmd.parent.name} ' if cmd.parent else ''}{cmd.name}",
                value=f"{cmd.description}\n`{cmd.usage.format(pr=self.bot.prefix)}`"
            )
        await interaction.message.edit(embed=embed)

        

class HelpSelectView(ui.View):
    def __init__(self, bot, author, cogs):
        super().__init__(timeout=600)
        self.add_item(HelpSelect(bot, author, cogs))