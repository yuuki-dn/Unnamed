from dotenv import load_dotenv
from os import environ
import aiomysql
import asyncio
from aiomysql import Connection, Cursor

load_dotenv()

host = environ["MYSQL_HOST"]
port = int(environ["MYSQL_PORT"])
username = environ["MYSQL_USERNAME"]
password = environ["MYSQL_PASSWORD"]
schema = environ["MYSQL_SCHEMA"]

async def setup_database() -> None:
    print("Đang kết nối tới cơ sở dữ liệu MySQL")
    connection: Connection = await aiomysql.connect(
        host=host,
        port=port,
        user=username,
        password=password,
        db=schema
    )
    try:
        with open("init.sql") as f:
            cursor: Cursor = await connection.cursor()
            await cursor.execute(f.read())
            print("Khởi tạo cơ sở dữ liệu thành công")
    except Exception as e:
        print("Khởi tạo cơ sở dữ liệu thất bại\n" + repr(e))
        
asyncio.run(setup_database())