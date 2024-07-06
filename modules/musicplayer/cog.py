from botbase import BotBase

import disnake
from disnake.ext import commands

class MusicPlayer(commands.Cog):
    def __init__(self, bot: BotBase):
        self.bot: BotBase = bot