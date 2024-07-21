import disnake
from disnake.ext import commands
from utils.converter import *
import traceback
from typing import Optional, Union


class ClientException(commands.CheckFailure):
    pass


class GenericError(commands.CheckFailure):

    def __init__(self, text: str, *, self_delete: int = None, delete_original: Optional[int] = None,
                 components: list = None):
        self.text = text
        self.self_delete = self_delete
        self.delete_original = delete_original


def parse_error(
        ctx: Union[disnake.ApplicationCommandInteraction, commands.Context, disnake.MessageInteraction],
        error: Exception
):
    error_txt = ""

    if isinstance(error, commands.NotOwner):
        error_txt = "**Chỉ nhà phát triển của tôi mới có thể sử dụng lệnh này**"

    if isinstance(error, commands.BotMissingPermissions):
        error_txt = "Tôi không có các quyền sau để thực thi lệnh này: ```\n{}```" \
            .format(", ".join(perms_translations.get(perm, perm) for perm in error.missing_permissions))

    if isinstance(error, commands.MissingPermissions):
        error_txt = "Bạn không có các quyền sau để thực hiện lệnh này: ```\n{}```" \
            .format(", ".join(perms_translations.get(perm, perm) for perm in error.missing_permissions))

    if isinstance(error, commands.NoPrivateMessage):
        error_txt = "Lệnh này không thể chạy trên tin nhắn riêng tư."

    if isinstance(error, commands.CommandOnCooldown):
        remaing = int(error.retry_after)
        if remaing < 1:
            remaing = 1
        error_txt = "**Bạn phải đợi {} mới có thể sử dụng lệnh này.**".format(
            time_format(int(remaing) * 1000, use_names=True))

    if isinstance(error, GenericError):
        error_txt = error.text

    if not error_txt:
        full_error_txt = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        print(full_error_txt)
    else:
        full_error_txt = ""

    return error_txt, full_error_txt


async def send_message(
    inter: Union[disnake.Interaction, disnake.ApplicationCommandInteraction],
    text=None,
    **kwargs,
):
    bot = inter.bot

    try:
        if not kwargs["components"]:
            kwargs.pop('components')
    except KeyError:
        pass

    if hasattr(inter, 'self_mod'):
        if inter.response.is_done():
            await inter.edit_original_message(content=text, **kwargs)
        else:
            await inter.response.edit_message(content=text, **kwargs)

    elif inter.response.is_done() and isinstance(inter, disnake.AppCmdInter):
        await inter.edit_original_message(content=text, **kwargs)

    else:

        try:

            channel = inter.channel

            is_forum = False

            try:
                if isinstance(channel.parent, disnake.ForumChannel):
                    is_forum = True
            except AttributeError:
                pass

            if is_forum:
                thread_kw = {}
                if channel.locked and channel.guild.me.guild_permissions.manage_threads:
                    thread_kw.update({"locked": False, "archived": False})
                elif channel.archived and channel.owner_id == bot.user.id:
                    thread_kw["archived"] = False
                if thread_kw:
                    await channel.edit(**thread_kw)

        except AttributeError:
            pass

        try:
            await inter.send(text, ephemeral=True, **kwargs)
        except disnake.InteractionTimedOut:

            try:
                if isinstance(inter.channel, disnake.Thread):
                    send_message_perm = inter.channel.parent.permissions_for(inter.guild.me).send_messages_in_threads
                else:
                    send_message_perm = inter.channel.permissions_for(inter.guild.me).send_messages

                if not send_message_perm:
                    return
            except AttributeError:
                return
            await inter.channel.send(text, **kwargs)


def paginator(txt: str):
    pages = commands.Paginator(prefix=None, suffix=None)
    pages.max_size = 1910
    for line in txt.splitlines():
        if len(line) >= pages.max_size - 3:
            l = [(line[i:i + pages.max_size - 3]) for i in range(0, len(line), pages.max_size - 3)]
            for l2 in l:
                pages.add_line(l2)
        else:
            pages.add_line(line)
    pages.close_page()
    return pages.pages