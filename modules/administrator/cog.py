from typing import Optional

from botbase import BotBase
from utils.configuration import MASTER_GUILD_ID, EPHEMERAL_AUDIT_ACTION, EPHEMERAL_ERROR_ACTION
from utils.guild_data import GuildData, ReactionRoleMessageEntity

import disnake
from disnake.ext import commands

import logging
import emoji
import re

DISCORD_EMOJI_PATTERN =  re.compile(r'<a?:.+?:\d{18,20}>')

def parse_emoji(text: str) -> Optional[str]:
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
        
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, event: disnake.RawReactionActionEvent):
        if event.guild_id is None: return
        parsed_emoji = parse_emoji(event.emoji.__str__())
        if parsed_emoji is None: return
        guild_entity = await self.guild_data.get_guild(event.guild_id)
        if event.message_id not in guild_entity.reaction_role_messages: return
        reaction_role_message = await self.guild_data.get_guild_reaction_role_message(event.message_id, event.guild_id)
        try: 
            role_id = reaction_role_message.map[parsed_emoji]
            await self.bot.http.add_role(event.guild_id, event.user_id, role_id)
        except KeyError: return
        except: self.logger.warning(f"(ID máy chủ {event.guild_id}): Không thể cấp vai trò {role_id} cho {event.user_id}")
    
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, event: disnake.RawReactionActionEvent):
        if event.guild_id is None: return
        parsed_emoji = parse_emoji(event.emoji.__str__())
        if parsed_emoji is None: return
        guild_entity = await self.guild_data.get_guild(event.guild_id)
        if event.message_id not in guild_entity.reaction_role_messages: return
        reaction_role_message = await self.guild_data.get_guild_reaction_role_message(event.message_id, event.guild_id)
        try: 
            role_id = reaction_role_message.map[parsed_emoji]
            await self.bot.http.remove_role(event.guild_id, event.user_id, role_id)
        except KeyError: return
        except: self.logger.warning(f"(ID máy chủ {event.guild_id}): Không thể xoá vai trò {role_id} cho {event.user_id}")
        
        
        
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
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    @commands.bot_has_guild_permissions(administrator=True)
    @commands.cooldown(3, 10, commands.BucketType.guild)
    async def add_reaction_role_message(self, inter: disnake.ApplicationCommandInteraction):
        if inter.author.bot: return
        message_id = inter.options["add"].get("message_id", "")
        if not isinstance(message_id, str):
            return await inter.response.send_message("❌ Tham số nhập vào không hợp lệ", ephemeral=EPHEMERAL_ERROR_ACTION)
        if not message_id.strip().isdecimal():
            return await inter.response.send_message("❌ Tham số nhập vào không hợp lệ", ephemeral=EPHEMERAL_ERROR_ACTION)
        message_id = int(message_id.strip())
        emoji = inter.options["add"].get("emoji", "")
        parsed_emoji = parse_emoji(emoji)
        if parsed_emoji is None:
            return await inter.response.send_message("❌ Tham số nhập vào không hợp lệ", ephemeral=EPHEMERAL_ERROR_ACTION)
        role = inter.options["add"].get("role", None)
        if not isinstance(role, disnake.Role):
            return await inter.response.send_message("❌ Tham số nhập vào không hợp lệ", ephemeral=EPHEMERAL_ERROR_ACTION)
        await inter.response.defer(ephemeral=EPHEMERAL_AUDIT_ACTION)
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
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(3, 10, commands.BucketType.guild)
    async def delete_reaction_role_message(self, inter: disnake.ApplicationCommandInteraction):
        if inter.author.bot: return
        message_id = inter.options["delete"].get("message_id", "")
        if not isinstance(message_id, str):
            return await inter.response.send_message("❌ Tham số nhập vào không hợp lệ", ephemeral=EPHEMERAL_ERROR_ACTION)
        if not message_id.strip().isdecimal():
            return await inter.response.send_message("❌ Tham số nhập vào không hợp lệ", ephemeral=EPHEMERAL_ERROR_ACTION)
        message_id = int(message_id.strip())
        await inter.response.defer(ephemeral=EPHEMERAL_AUDIT_ACTION)
        await self.guild_data.delete_reaction_role_message(message_id, inter.guild_id)
        await inter.edit_original_response(f"✅ Đã xoá tự động cấp vai trò cho tin nhắn có ID: {message_id}")
        
    
    @commands.slash_command(
        name="system",
        guild_ids=[MASTER_GUILD_ID]
    )
    async def system(self, inter: disnake.ApplicationCommandInteraction) -> None: pass
    
    @system.sub_command(
        name="shutdown",
        description="Dừng bot"
    )
    @commands.is_owner()
    async def shutdown(self, inter: disnake.ApplicationCommandInteraction):
        self.logger.warning(f"Lệnh tắt được thực thi bởi @{inter.author.name} (UID: {inter.author.id})")
        await inter.response.send_message("⚠️ Đang tắt bot", ephemeral=EPHEMERAL_AUDIT_ACTION)
        await self.bot.close()
