from botbase import BotBase
from utils.configuration import MASTER_GUILD_ID

import disnake
from disnake.ext import commands

import logging

class AdminCommands(commands.Cog):
    def __init__(self, bot: BotBase):
        self.bot: BotBase = bot
        self.logger: logging.Logger = logging.getLogger(__name__)
        
    # @commands.slash_command(
    #     name="reactionrole",
    #     default_member_permissions=disnake.Permissions(administrator=True)
    # )
    # async def reaction_role(self, inter: disnake.ApplicationCommandInteraction): pass
    
    @commands.slash_command(
        name="system",
        guild_ids=[MASTER_GUILD_ID]
    )
    async def system(self, inter: disnake.ApplicationCommandInteraction) -> None: pass
    
    @system.sub_command(
        name="reload",
        description="Tải lại tệp JSON cấu hình của bot"
    )
    async def reload_config(self, inter: disnake.ApplicationCommandInteraction):
        allowed = False
        if inter.author.id == inter.bot.owner_id: allowed = True
        elif inter.author.id in inter.bot.owner_ids: allowed = True
        if not allowed: return await inter.response.send_message("❌ Chỉ chủ sở hữu bot mới có quyền sử dụng lệnh này", ephemeral=True)
        self.logger.warning(f"Lệnh tải lại tệp cấu hình JSON được thực thi bởi @{inter.author.name} (UID: {inter.author.id})")
        await inter.response.send_message("✅ Tải lại thành công", ephemeral=True)
    
    @system.sub_command(
        name="shutdown",
        description="Dừng bot"
    )
    async def shutdown(self, inter: disnake.ApplicationCommandInteraction):
        allowed = False
        if inter.author.id == inter.bot.owner_id: allowed = True
        elif inter.author.id in inter.bot.owner_ids: allowed = True
        if not allowed: return await inter.response.send_message("❌ Chỉ chủ sở hữu bot mới có quyền sử dụng lệnh này", ephemeral=True)
        self.logger.warning(f"Lệnh tắt được thực thi bởi @{inter.author.name} (UID: {inter.author.id})")
        await inter.response.send_message("⚠️ Đang tắt bot", ephemeral=True)
        await self.bot.close()