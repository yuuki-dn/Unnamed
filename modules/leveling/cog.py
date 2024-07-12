from botbase import BotBase


import disnake
from disnake.ext import commands

class LevelingCog(commands.Cog):
    def __init__(self, bot: BotBase):
        self.bot: BotBase = bot

    
    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        pass