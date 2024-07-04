import disnake
from disnake.ext import commands

class LevelingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot