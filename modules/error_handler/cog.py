import traceback
from typing import Union

import disnake
from disnake.ext import commands

from botbase import BotBase as ClientUser
from .errors import ClientException, parse_error, paginator, send_message


class ErrorHandler(commands.Cog):
    def __init__(self, bot: ClientUser):
        self.bot = bot

    @commands.Cog.listener('on_user_command_error')
    @commands.Cog.listener('on_message_command_error')
    @commands.Cog.listener('on_slash_command_error')
    async def on_interaction_command_error(self, inter: disnake.AppCmdInter, error: Exception):


        await self.handle_error_cmd(ctx=inter, error=error)

    async def handle_error_cmd(self, ctx: disnake.ApplicationCommandInteraction, error: Exception):

        if isinstance(error, ClientException):
            return


        title_txt = "Đã xảy ra sự cố"

        error_msg, full_error_msg = parse_error(ctx, error)

        if isinstance(error, disnake.NotFound) and str(error).endswith("Unknown Interaction"):
            return

        kwargs = {"text": ""}
        color = disnake.Color.red()

        if not error_msg:

            kwargs["embeds"] = disnake.Embed(
                color=color,
                title=title_txt,
                description=f"```py\n{repr(error)[:2030].replace(self.bot.http.token, 'mytoken')}```"
            )
        else:

            kwargs["embeds"] = []

            for p in paginator(error_msg):
                kwargs["embeds"].append(disnake.Embed(color=color, description=p))

        try:
            await send_message(ctx, **kwargs)
            print(full_error_msg)

        except ValueError:
            error_msg, full_error_msg = parse_error(ctx, error)

            if isinstance(error, disnake.NotFound) and str(error).endswith("Unknown Interaction"):
                return

            kwargs = {"text": ""}
            color = disnake.Color.red()

            if not error_msg:

                kwargs["embed"] = disnake.Embed(
                    color=color,
                    title=title_txt,
                    description=f"```py\n{repr(error)[:2030].replace(self.bot.http.token, 'mytoken')}```"
                )
            else:

                kwargs["embed"] = []

                for p in paginator(error_msg):
                    kwargs["embed"].append(disnake.Embed(color=color, description=p))

            await send_message(ctx, **kwargs)
            print(full_error_msg)

        except:
            print(("-" * 50) + f"\n{error_msg}\n" + ("-" * 50))
            traceback.print_exc()
            print(full_error_msg)

    @commands.Cog.listener("on_command_error")
    async def prefix_command_handle(self, ctx: Union[disnake.AppCommandInter, commands.Context], error: Exception):

        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.NotOwner):
            print(f"{ctx.author} [{ctx.author.id}] không sở hữu bot để sử dụng: {ctx.command.name}")
            return

        if isinstance(error, commands.MissingPermissions) and (await ctx.bot.is_owner(ctx.author)):
            try:
                await ctx.reinvoke()
            except Exception as e:
                await self.on_legacy_command_error(ctx, e)
            return


        title_txt = "Đã xảy ra sự cố"

        error_msg = parse_error(ctx, error)
        kwargs = {"content": ""}

        if not error_msg:

            if ctx.channel.permissions_for(ctx.guild.me).embed_links:
                kwargs["embed"] = disnake.Embed(
                    color=disnake.Colour.red(),
                    title=title_txt,
                    description=f"```py\n{repr(error)[:2030].replace(self.bot.http.token, 'mytoken')}```"
                )

            else:
                kwargs[
                    "content"] += f"\n{title_txt}\n ```py\n{repr(error)[:2030].replace(self.bot.http.token, 'mytoken')}```"

        else:

            if ctx.channel.permissions_for(ctx.guild.me).embed_links:
                kwargs["embed"] = disnake.Embed(color=disnake.Colour.red(), description=error_msg)
            else:
                kwargs["content"] += f"\n{error_msg}"

        try:
            kwargs["delete_after"] = error.delete_original
        except AttributeError:
            pass

        try:
            if error.self_delete and ctx.channel.permissions_for(ctx.guild.me).manage_messages:
                await ctx.message.delete()
        except:
            pass

        if hasattr(ctx, "inter"):
            if ctx.inter.response.is_done():
                func = ctx.inter.edit_original_message
            else:
                func = ctx.inter.response.edit_message
                kwargs.pop("delete_after", None)
        else:
            try:
                func = ctx.store_message.edit
            except:
                func = ctx.send

        await func(**kwargs)