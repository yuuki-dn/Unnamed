from __future__ import annotations

import logging
import asyncio

import aiomysql
from aiomysql import Cursor


class Database:
    connection = None

    def __init__(self, environ, loop: asyncio.AbstractEventLoop):
        self.logger = logging.getLogger(__name__)
        self.loop = loop

        self.action_lock = asyncio.Lock()

        host = environ["MYSQL_HOST"]
        port = int(environ["MYSQL_PORT"])
        username = environ["MYSQL_USERNAME"]
        password = environ["MYSQL_PASSWORD"]
        schema = environ["MYSQL_SCHEMA"]


        for value in (host, port, username, password, schema):
            if value is None:
                raise EnvironmentError("Thông tin kết nối cơ sở dữ liệu chưa được cấu hình trong biến môi trường")

        future = asyncio.ensure_future(self.connect(host, port, username, password, schema), loop=loop)
        future.add_done_callback(self.connect_callback)

    async def connect(self, host, port, username, password, schema) -> None:
        self.logger.info("Đang kết nối tới cơ sở dữ liệu MySQL")

        async def wrapper():
            self.connection = await aiomysql.connect(host=host, port=port, user=username, password=password, db=schema, autocommit=True)

        await asyncio.wait_for(wrapper(), 10)

    def connect_callback(self, future):
        try:
            future.result()
            self.logger.info("Kết nối tới cơ sở dữ liệu thành công")
        except Exception as e:
            self.logger.error("Kết nối tới cơ sở dữ liệu thất bại", repr(e))

    async def execute_update(self, query: str, *args, **kwargs) -> None:
        async with self.action_lock:
            async with await self.cursor() as cursor:
                await cursor.execute(query, *args, **kwargs)

    async def execute_query(self, query: str, *args, **kwargs) -> list | None:
        async with self.action_lock:
            async with await self.cursor() as cursor:
                await cursor.execute(query, *args, **kwargs)
                result = await cursor.fetchall()
                return result

    async def cursor(self) -> Cursor:
        return await self.connection.cursor()

    async def close(self) -> None:
        self.connection.close()
