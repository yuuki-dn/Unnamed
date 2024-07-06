import disnake
from disnake.ext import commands

from os import environ, _Environ
from dotenv import load_dotenv
import logging

from utils.configuration import PREFIX, INTENTS, COMMAND_SYNC_FLAGS

class BotBase(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)
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

    # Event
    async def on_ready(self):
        self.logger.info(f"Khởi tạo thành công! Đã đăng nhập với tên {self.user.name} (UID: {self.user.id})")
    

    def activate(self) -> None:
        # Đăng nhập
        token = self.env.get("TOKEN")
        if token is None:
            raise EnvironmentError("Bot token chưa được cài đặt trong biến môi trường")
        self.run(token)
        
    
    def deactive(self) -> None:
        exit()
