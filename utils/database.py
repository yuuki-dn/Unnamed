import logging
import asyncio
from os import _Environ

from mysql.connector.aio import MySQLConnection

class Database():
    connection: MySQLConnection = None
    
    
    def __init__(self, environ: _Environ, loop: asyncio.AbstractEventLoop):
        self.logger = logging.getLogger(__name__)
        self.loop = loop
        
        host = environ["MYSQL_HOST"]
        port = int(environ["MYSQL_PORT"])
        username = environ["MYSQL_USERNAME"]
        password = environ["MYSQL_PASSWORD"]
        schema = environ["MYSQL_SCHEMA"]
        
        for value in (host, username, password, schema):
            if value is None: raise EnvironmentError("Thông tin kết nối cơ sở dữ liệu chưa được cấu hình trong biến môi trường")
            
        self.connection = MySQLConnection(host=host, port=port, user=username, password=password, database=schema)
        
        future = asyncio.ensure_future(self.connect(), loop=loop)
        future.add_done_callback(self.connect_callback)
        
            
    
    async def connect(self) -> None:
        self.logger.info("Đang kết nối tới cơ sở dữ liệu MySQL")
        
        async def wrapper(connection: MySQLConnection):
            await connection.connect()
            while not connection.is_connected(): await asyncio.sleep(1)
            
        await asyncio.wait_for(wrapper(self.connection), 10)
        
        
    def connect_callback(self, future):
        try:
            result = future.result()
            self.logger.info("Kết nối tới cơ sở dữ liệu thành công")
        except Exception as e:
            self.logger.error("Kết nối tới cơ sở dữ liệu thất bại", repr(e))
            
        
    
    async def execute_update(self, query: str, *args, **kwargs) -> None:
        async with await self.connection.cursor() as cursor:
            await cursor.execute(query, *args, **kwargs)
            await self.commit()
   
            
    async def execute_query(self, query: str, *args, **kwargs) -> list | None:
        result = None
        async with await self.connection.cursor() as cursor:
            await cursor.execute(query, *args, **kwargs)
            result = await cursor.fetchall()
        return result
    
    
    async def commit(self) -> None:
        await self.connection.commit()
        
        
    async def close(self) -> None:
        self.connection.close()