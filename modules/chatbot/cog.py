from botbase import BotBase

import disnake
from disnake.ext import commands

class ChatBot(commands.Cog):
    def __init__(self, bot: BotBase):
        self.bot: BotBase = bot