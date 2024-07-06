from botbase import BotBase

import disnake
from disnake.ext import commands
import logging

from modules.wordchain.dictionary import Dictionary, IllegalWordException, reform_word
from utils.cache import LRUCache
from utils.guild_data import GuildData

logger: logging.Logger = logging.getLogger(__name__)

class ChainNotMatchException(Exception):
    def __init__(self, *args, **kwargs):
        return super().__init__("Từ nhập vào không khớp với chuỗi từ hiện tại", *args, **kwargs)


class DuplicateWordError(Exception):
    def __init__(self, *args, word: str, previous_data = None, **kwargs):
        self.previous_data = previous_data
        return super().__init__(f"Từ {word} đã được sử dụng trước đó.", *args, **kwargs)
        
    
class GuildChain(LRUCache):
    __slots__ = "chain", "previous_last_character"
    
    def __init__(self):
        self.previous_last_character = ""
        super().__init__(5000)
        
    def add_word(self, word: str, user_id: int):
        word = reform_word(word)
        if not word.startswith(self.previous_last_character):
            raise ChainNotMatchException()
        data = self.get(word)
        if data is not None: raise DuplicateWordError(word=word, previous_data=data)
        self.put(word, user_id)
        

class WordChain(commands.Cog):
    def __init__(self, bot: BotBase):
        self.bot: BotBase = bot
        self.dictionary: Dictionary = Dictionary()
        self.storage: dict[int, GuildChain] = {}
        self.guild_data: GuildData = None
        
    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.guild is None: return
        if message.author.bot: return
        if message.is_system(): return
        if message.webhook_id is not None: return
        
        
    @commands.slash_command(
        name="wordchain",
        default_member_permissions=disnake.Permissions(administrator=True)
    )
    @commands.has_guild_permissions(administrator=True)
    async def wordchain(self, inter: disnake.ApplicationCommandInteraction): pass
    
    
    @wordchain.sub_command(
        name="start",
        description="Kích hoạt trò chơi nối từ trên máy chủ ở kênh hiện tại"
    )
    @commands.has_guild_permissions(administrator=True)
    async def start(self, inter: disnake.ApplicationCommandInteraction):
        pass
    
    
    @wordchain.sub_command(
        name="reset",
        description="Đặt lại dữ liệu trò chơi nối từ trên máy chủ"
    )
    @commands.has_guild_permissions(administrator=True)
    async def reset(self, inter: disnake.ApplicationCommandInteraction):
        pass
    
    
    @wordchain.sub_command(
        name="stop",
        description="Dừng trò chơi nối từ trên máy chủ"
    )
    @commands.has_guild_permissions(administrator=True)
    async def stop(self, inter: disnake.ApplicationCommandInteraction):
        pass