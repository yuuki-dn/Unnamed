from botbase import BotBase

import disnake
from disnake.ext import commands

class AdminCommands(commands.Cog):
    def __init__(self, bot: BotBase):
        self.bot: BotBase = bot
        
    
    @commands.slash_command(
        name="reactionrole",
        default_member_permissions=disnake.Permissions(administrator=True)
    )
    async def reaction_role(self, inter: disnake.ApplicationCommandInteraction): pass
    
    
    @commands.slash_command(name="admin")
    async def admin(self, inter: disnake.ApplicationCommandInteraction) -> None: pass
    
    
    @admin.sub_command(
        name="reload",
        description="Tải lại tệp JSON cấu hình của bot"
    )
    async def reload_config(self, inter: disnake.ApplicationCommandInteraction):
        pass
    
    
    @admin.sub_command(
        name="shutdown",
        description="Dừng bot"
    )
    async def shutdown(self, inter: disnake.ApplicationCommandInteraction):
        pass