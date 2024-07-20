import json
import logging
from bisect import bisect_right
from random import randint

import disnake
from disnake.ext import commands

from botbase import BotBase
from .data import MemberXPData
from utils.configuration import MASTER_GUILD_ID, EPHEMERAL_AUDIT_ACTION, EPHEMERAL_ERROR_ACTION

MessageableChannel = disnake.TextChannel, disnake.Thread, disnake.VoiceChannel, disnake.StageChannel, disnake.PartialMessageable


LEVEL_LIMIT = 1000
LEVEL_XP_LIMIT = [100]
for i in range(2, LEVEL_LIMIT + 1): LEVEL_XP_LIMIT.append(100 * i + LEVEL_XP_LIMIT[-1])


def get_current_level(xp: int) -> int:
    return bisect_right(LEVEL_XP_LIMIT, xp)


class LevelingCog(commands.Cog):
    def __init__(self, bot: BotBase):
        self.bot: BotBase = bot
        self.logger = logging.getLogger(__name__)
        self.data = MemberXPData(self.bot.database)

        self.chat_xp_min: int = 15
        self.chat_xp_max: int = 40
        self.chat_xp_cooldown: int = 45
        self.chat_effective_channel: set[int] = set()
        self.booster_extra_xp_percent: int = 10
        self.level_up_notification: bool = True
        self.level_role: dict[int, int] = {}

        self.__load_config__()


    def __get_new_role__(self, previous_level: int, new_level: int) -> list[int]:
        result = []
        if not previous_level < new_level: return result
        for key in self.level_role:
            if previous_level < key <= new_level: result.append(self.level_role[key])
        return result


    def __load_config__(self):
        with open("modules/leveling/config.json") as f:
            configuration: dict = json.load(f)
            self.chat_xp_min = configuration.get("chat_xp_min", 15)
            self.chat_xp_max = configuration.get("chat_xp_max", 40)
            self.chat_xp_cooldown = configuration.get("chat_xp_cooldown", 45)
            self.booster_extra_xp_percent = configuration.get("booster_extra_xp_percent", 10)
            self.level_up_notification = configuration.get("level_up_notification", True)
            self.chat_effective_channel = set()
            for channel_id in configuration.get("chat_effective_channel", []): self.chat_effective_channel.add(channel_id)
            self.level_role = {}
            for level_role_data in configuration.get("level_role", []):
                self.level_role[level_role_data["level"]] = level_role_data["role_id"]

            self.logger.info("Đã tải lại tệp cấu hình JSON")


    async def __process__(self, channel: MessageableChannel, member: disnake.Member, amount: int):
        await self.data.increase_member_xp(member.id, amount)
        new_xp = await self.data.get_member_xp(member.id)
        new_level = get_current_level(new_xp)
        previous_level = get_current_level(new_xp - amount)
        if self.level_up_notification and previous_level < new_level:
            new_role = self.__get_new_role__(previous_level, new_level)
            response = f"✨ <@{member.id}> đã lên level {new_level} "
            if new_role.__len__() > 0:
                response += "và nhận được vai trò "
                for role_id in new_role:
                    try:
                        await self.bot.http.add_role(channel.guild.id, member.id, role_id)
                        response += f"<@&{role_id}> "
                    except Exception as e:
                        self.logger.error(f"Đã có lỗi xảy ra khi thêm vai trò {role_id} cho thành viên ID: {member.id}", repr(e))
            await channel.send(response, allowed_mentions=disnake.AllowedMentions(everyone=False, users=True, roles=False))



    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.guild is None: return
        if message.author.bot: return
        if message.webhook_id is not None: return
        if message.is_system(): return

        if message.guild.id != MASTER_GUILD_ID: return
        if message.channel.id not in self.chat_effective_channel: return
        if not self.data.check_cooldown(message.author.id, self.chat_xp_cooldown): return
        is_booster = (message.author.premium_since is not None)
        amount = int(randint(self.chat_xp_min, self.chat_xp_max) * (100 + (self.booster_extra_xp_percent if is_booster else 0)) / 100)
        await self.__process__(message.channel, message.author, amount)



    @commands.slash_command(
        name="level",
        description="Xem cấp và điểm XP của bạn hoặc thành viên khác",
        dm_permission=False,
        guild_ids=[MASTER_GUILD_ID],
        options=[
            disnake.Option(
                name="member",
                description="Thành viên",
                type=disnake.OptionType.user,
                required=False
            )
        ]
    )
    async def view_level(self, inter: disnake.ApplicationCommandInteraction):
        if inter.guild_id is None: return
        if inter.guild_id != MASTER_GUILD_ID: return
        member = inter.options.get("member", inter.author)
        if not isinstance(member, disnake.Member):
            return await inter.response.send_message("❌ Tham số nhập vào không hợp lệ", ephemeral=EPHEMERAL_ERROR_ACTION)
        if member.bot:
            return await inter.response.send_message("❌ Không được chỉ định thành viên là bot", ephemeral=EPHEMERAL_ERROR_ACTION)
        xp = await self.data.get_member_xp(member.id)
        current_level = get_current_level(xp)
        is_booster = (member.premium_since is not None)
        embed = disnake.Embed(
            title=member.display_name,
            color=0xFFFFFF,
            url=f"https://discord.com/users/{member.id}"
        )
        embed.description = f"""
```ansi
Level: {current_level}
XP: {xp} / {'UNLIMITED' if current_level == LEVEL_XP_LIMIT.__len__() else LEVEL_XP_LIMIT[current_level]}
{f"Booster: +{self.booster_extra_xp_percent}% lượng XP nhận được" if is_booster else ""}
```
        """
        embed.set_thumbnail(member.display_avatar)
        await inter.response.send_message(embed=embed)


    @commands.slash_command(
        name="xp",
        dm_permission=False,
        default_member_permissions=disnake.Permissions(administrator=True),
        guild_ids=[MASTER_GUILD_ID]
    )
    async def xp(self, inter: disnake.ApplicationCommandInteraction) -> None:
        pass


    @xp.sub_command(
        name="add",
        description="Cộng thêm điểm XP cho một thành viên",
        options=[
            disnake.Option(
                name="member",
                description="Thành viên",
                type=disnake.OptionType.user,
                required=True
            ),
            disnake.Option(
                name="amount",
                description="Lượng điểm XP cần thêm",
                type=disnake.OptionType.integer,
                required=True
            )
        ]
    )
    @commands.has_guild_permissions(administrator=True)
    async def xp_add(self, inter: disnake.ApplicationCommandInteraction) -> None:
        if inter.guild_id is None: return
        if inter.guild_id != MASTER_GUILD_ID: return
        member = inter.options["add"].get("member", None)
        if not isinstance(member, disnake.Member):
            return await inter.response.send_message("❌ Tham số nhập vào không hợp lệ", ephemeral=EPHEMERAL_ERROR_ACTION)
        if member.bot:
            return await inter.response.send_message("❌ Không được chỉ định thành viên là bot", ephemeral=EPHEMERAL_ERROR_ACTION)
        amount = inter.options["add"].get("amount", None)
        if not isinstance(amount, int):
            return await inter.response.send_message("❌ Tham số nhập vào không hợp lệ", ephemeral=EPHEMERAL_ERROR_ACTION)
        if amount < 1:
            return await inter.response.send_message("❌ Giá trị không được phép nhỏ hơn 1", ephemeral=EPHEMERAL_ERROR_ACTION)
        await inter.response.defer(ephemeral=EPHEMERAL_AUDIT_ACTION)
        await self.__process__(inter.channel, inter.author, amount)
        await inter.edit_original_response(f"✅ Đã thêm `{amount} xp` cho thành viên {member.mention}")


    @xp.sub_command(
        name="remove",
        description="Trừ bớt điểm XP của một thành viên",
        options=[
            disnake.Option(
                name="member",
                description="Thành viên",
                type=disnake.OptionType.user,
                required=True
            ),
            disnake.Option(
                name="amount",
                description="Lượng điểm XP cần bớt",
                type=disnake.OptionType.integer,
                required=True
            )
        ]
    )
    @commands.has_guild_permissions(administrator=True)
    async def xp_remove(self, inter: disnake.ApplicationCommandInteraction) -> None:
        if inter.guild_id is None: return
        if inter.guild_id != MASTER_GUILD_ID: return
        member = inter.options["remove"].get("member", None)
        if not isinstance(member, disnake.Member):
            return await inter.response.send_message("❌ Tham số nhập vào không hợp lệ", ephemeral=EPHEMERAL_ERROR_ACTION)
        if member.bot:
            return await inter.response.send_message("❌ Không được chỉ định thành viên là bot", ephemeral=EPHEMERAL_ERROR_ACTION)
        amount = inter.options["remove"].get("amount", None)
        if not isinstance(amount, int):
            return await inter.response.send_message("❌ Tham số nhập vào không hợp lệ", ephemeral=EPHEMERAL_ERROR_ACTION)
        if amount < 1:
            return await inter.response.send_message("❌ Giá trị không được phép nhỏ hơn 1", ephemeral=EPHEMERAL_ERROR_ACTION)
        await inter.response.defer(ephemeral=EPHEMERAL_AUDIT_ACTION)
        await self.data.reduce_member_xp(member.id, amount)
        await inter.edit_original_response(f"✅ Đã trừ `{amount} xp` của thành viên {member.mention}")


    @xp.sub_command(
        name="reload",
        description="Tải lại tệp JSON cấu hình của bot"
    )
    @commands.is_owner()
    async def reload_config(self, inter: disnake.ApplicationCommandInteraction) -> None:
        self.__load_config__()
        self.logger.warning(f"Lệnh tải lại tệp cấu hình JSON được thực thi bởi @{inter.author.name} (UID: {inter.author.id})")
        await inter.response.send_message("✅ Tải lại thành công", ephemeral=EPHEMERAL_AUDIT_ACTION)
