from botbase import BotBase
from utils.configuration import MASTER_GUILD_ID
from utils.guild_data import GuildData, ReactionRoleMessageEntity

import disnake
from disnake.ext import commands

import logging
import emoji
import re

DISCORD_EMOJI_PATTERN =  re.compile(r'<a?:.+?:\d{18,20}>')

def parse_emoji(text: str) -> str | None:
    # if text is emoji return unique ID, None otherwise
    text = text.strip()
    if DISCORD_EMOJI_PATTERN.fullmatch(text) is not None: return text.split(":")[-1][: -1]
    elif emoji.is_emoji(text):
        return emoji.demojize(text)[1 : -1]
    else: return None
        

class AdminCommands(commands.Cog):
    def __init__(self, bot: BotBase):
        self.bot: BotBase = bot
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.guild_data: GuildData = bot.guild_data
        
    @commands.Cog.listener
    async def on_raw_reaction_add(event: disnake.RawReactionActionEvent):
        pass
        
        
    @commands.slash_command(
        name="reactionrole",
        default_member_permissions=disnake.Permissions(administrator=True)
    )
    async def reaction_role(self, inter: disnake.ApplicationCommandInteraction): pass
    
    @reaction_role.sub_command(
        name="add",
        description="Tự động cấp vai trò khi người dùng thêm biểu cảm vào tin nhắn",
        options=[
            disnake.Option(
                name="message_id",
                description="ID tin nhắn",
                type=disnake.OptionType.string,
                required=True
            ),
            disnake.Option(
                name="emoji",
                description="Emoji",
                type=disnake.OptionType.string,
                required=True
            ),
            disnake.Option(
                name="role",
                description="Vai trò sẽ được tự động cấp",
                type=disnake.OptionType.role,
                required=True
            )
        ]
    )
    async def add_reaction_role_message(self, inter: disnake.ApplicationCommandInteraction):
        if inter.guild_id is None: return
        if inter.author.bot: return
        if not inter.author.guild_permissions.administrator:
            return await inter.response.send_message("❌ Bạn cần có quyền `Quản trị máy chủ` để sử dụng lệnh này", ephemeral=True)
        if not inter.guild.me.guild_permissions.administrator:
            return await inter.response.send_message("❌ Bot cần có quyền `Quản trị máy chủ` để thực hiện các chức năng cho lệnh này", ephemeral=True)
        message_id = inter.options["add"].get("message_id", "")
        if not isinstance(message_id, str):
            return await inter.response.send_message("❌ Tham số nhập vào không hợp lệ", ephemeral=True)
        if not message_id.strip().isdecimal():
            return await inter.response.send_message("❌ Tham số nhập vào không hợp lệ", ephemeral=True)
        message_id = int(message_id.strip())
        emoji = inter.options["add"].get("emoji", "")
        parsed_emoji = parse_emoji(emoji)
        if parsed_emoji is None:
            return await inter.response.send_message("❌ Tham số nhập vào không hợp lệ", ephemeral=True)
        role = inter.options["add"].get("role", None)
        if not isinstance(role, disnake.Role):
            return await inter.response.send_message("❌ Tham số nhập vào không hợp lệ", ephemeral=True)
        await inter.response.defer(ephemeral=True)
        entity: ReactionRoleMessageEntity = await self.guild_data.get_guild_reaction_role_message(message_id, inter.guild_id)
        entity.map[parsed_emoji] = role.id
        await self.guild_data.update_reaction_role_message(entity)
        hook_reacted = False
        try:
            message: disnake.Message = self.bot.get_message(message_id)
            if message is not None:
                await message.add_reaction(emoji)
                hook_reacted = True
        except: pass
        await inter.edit_original_response(
            f"✅ Đã thêm tự động cấp vai trò ở tin nhắn với ID: {message_id}\n"
            f"        {emoji} --> {role.mention}\n"
            f"{f'-# Tuy nhiên đã có lỗi xảy ra khi bot cố gắng thêm trước biểu cảm {emoji} vào tin nhắn. Bạn hãy thêm nó thủ công nhé' if not hook_reacted else ''}"
        )
        
    
    @reaction_role.sub_command(
        name="delete",
        description="Xoá tự động cấp vai trò khi người dùng thêm biểu cảm vào tin nhắn",
        options=[
            disnake.Option(
                name="message_id",
                description="ID tin nhắn",
                type=disnake.OptionType.string,
                required=True
            )
        ]
    )
    async def delete_reaction_role_message(self, inter: disnake.ApplicationCommandInteraction):
        if inter.guild_id is None: return
        if inter.author.bot: return
        if not inter.author.guild_permissions.administrator:
            return await inter.response.send_message("❌ Bạn cần có quyền `Quản trị máy chủ` để sử dụng lệnh này", ephemeral=True)
        message_id = inter.options["delete"].get("message_id", "")
        if not isinstance(message_id, str):
            return await inter.response.send_message("❌ Tham số nhập vào không hợp lệ", ephemeral=True)
        if not message_id.strip().isdecimal():
            return await inter.response.send_message("❌ Tham số nhập vào không hợp lệ", ephemeral=True)
        message_id = int(message_id.strip())
        await inter.response.defer(ephemeral=True)
        await self.guild_data.delete_reaction_role_message(message_id, inter.guild_id)
        await inter.edit_original_response(f"✅ Đã xoá tự động cấp vai trò cho tin nhắn có ID: {message_id}")
        
    
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
