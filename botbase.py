import disnake
from disnake.ext import commands

from os import environ, _Environ
from dotenv import load_dotenv
import logging

from configuration import PREFIX, INTENTS, COMMAND_SYNC_FLAGS

from administrator.cog import AdminCommands
from chatbot.cog import ChatBot
from leveling.cog import LevelingCog
from musicplayer.cog import MusicPlayer
from wordchain.cog import WordChain


class BotBase(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger("BotBase")
        load_dotenv()
        self.env: _Environ = environ
        self.boot_time = disnake.utils.utcnow()
        
        # Khởi tạo
        super().__init__(
            command_prefix=PREFIX,
            intents=INTENTS,
            command_sync_flags=COMMAND_SYNC_FLAGS,
            *args, **kwargs
        )
        
        # Thêm các module xử lí
        self.add_cog(AdminCommands(self))
        self.add_cog(ChatBot(self))
        self.add_cog(LevelingCog(self))
        self.add_cog(MusicPlayer(self))
        self.add_cog(WordChain(self))
        
        # Đăng nhập
        token = self.env.get("TOKEN")
        if token is None:
            raise EnvironmentError("Bot token chưa được cài đặt trong biến môi trường")
        self.run(token)
        

    # Event
    async def on_ready(self):
        self.logger.info(f"Khởi tạo thành công! Đã đăng nhập với tên {self.user.name} (UID: {self.user.id})")
    

    # async def close(self) -> None:
    #     await super(commands.AutoShardedBot, self).close()
    #     exit()
