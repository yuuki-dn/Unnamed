import logging
import time
from os import _Environ

import mysql.connector
from mysql.connector.abstracts import MySQLConnectionAbstract, MySQLCursorAbstract

INIT_SCRIPT = """
CREATE TABLE IF NOT EXIST

"""

class Database():
    connection: MySQLConnectionAbstract = None
    
    
    def __init__(self, environ: _Environ):
        self.logger = logging.getLogger(__name__)
        
        host = environ.get("MYSQL_HOST")
        username = environ.get("MYSQL_USERNAME")
        password = environ.get("MYSQL_PASSWORD")
        schema = environ.get("MYSQL_SCHEMA")
        
        for value in (host, username, password, schema):
            if value is None: raise EnvironmentError("Thông tin kết nối cơ sở dữ liệu chưa được cấu hình trong biến môi trường")
        
        self.connect(host, username, password, schema)
    
    
    def connect(self, host: str, username: str, password: str, schema: str) -> None:
        self.logger.info("Đang kết nối tới cơ sở dữ liệu MySQL")
        self.connection = mysql.connector.connect(
            host=host,
            username=username,
            password=password,
            database=schema
        )
        while not self.connection.is_connected():
            time.sleep(1)
        self.logger.info("Kết nối tới cơ sở dữ liệu thành công")
        
    def get_cursor(self) -> MySQLCursorAbstract:
        return self.connection.cursor()
    