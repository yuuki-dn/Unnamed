import disnake
from disnake.ext import commands

from os import environ
from dotenv import load_dotenv
import logging
import asyncio

from utils.configuration import PREFIX, INTENTS, COMMAND_SYNC_FLAGS
from utils.database import Database
from utils.guild_data import GuildData



class BotBase(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        self.pool = None
        self.logger = logging.getLogger(__name__)
        load_dotenv()
        self.loop = asyncio.get_event_loop()
        self.env = environ
        self.boot_time = disnake.utils.utcnow()
        self.database = Database(self.env, self.loop)
        self.guild_data = GuildData(self.database)
        
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

    
    async def on_close(self):
        await self.database.connection.close()

    def run(self) -> None:
        # Đăng nhập
        token = self.env.get("TOKEN")
        if token is None: raise EnvironmentError("Bot token chưa được cài đặt trong biến môi trường")
        
        async def runner() -> None:
            try: await self.start(token)
            finally:
                self.logger.info("Đang thực hiện các tác vụ trước khi dừng bot")
                if not self.is_closed(): await self.close()
                await self.database.close()
                await self.loop.shutdown_asyncgens()
        
        def stop_loop_on_completion(f) -> None: 
            self.loop.stop()

        future = asyncio.ensure_future(runner(), loop=self.loop)
        future.add_done_callback(stop_loop_on_completion)
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            self.logger.warning("Đã nhận tín hiệu dừng bot")
        finally:
            future.remove_done_callback(stop_loop_on_completion)
            self.logger.info("Đang dọn dẹp môi trường")
            disnake.client._cleanup_loop(self.loop)

        if not future.cancelled():
            try: return future.result()
            except KeyboardInterrupt: return None
