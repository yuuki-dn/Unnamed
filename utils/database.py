import logging
import signal
import asyncio
from os import _Environ

import aiomysql
from aiomysql import Connection, Cursor

class Database():
    connection: Connection = None
    
    
    def __init__(self, environ: _Environ, loop: asyncio.AbstractEventLoop):
        self.logger = logging.getLogger(__name__)
        
        host = environ["MYSQL_HOST"]
        port = int(environ["MYSQL_PORT"])
        username = environ["MYSQL_USERNAME"]
        password = environ["MYSQL_PASSWORD"]
        schema = environ["MYSQL_SCHEMA"]
        
        for value in (host, username, password, schema):
            if value is None: raise EnvironmentError("Thông tin kết nối cơ sở dữ liệu chưa được cấu hình trong biến môi trường")
        
        asyncio.run_coroutine_threadsafe(self.connect(host, port, username, password, schema), loop=loop)
            
    
    async def connect(self, host: str, port: int, username: str, password: str, schema: str) -> None:
        self.logger.info("Đang kết nối tới cơ sở dữ liệu MySQL")
        self.connection = await aiomysql.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            db=schema
        )
        try:
            with open("utils/init.sql") as f:
                init_cursor: Cursor = await self.connection.cursor()
                await init_cursor.execute(f.read())
                self.logger.info("Khởi tạo cơ sở dữ liệu thành công")
        except Exception as e:
            self.logger.error("Khởi tạo cơ sở dữ liệu thất bại\n" + repr(e))
        
    
    
    async def get_cursor(self) -> Cursor:
        return await self.connection.cursor()
    
    async def commit(self) -> None:
        await self.connection.commit()
    
    async def close(self) -> None:
        self.connection.close()