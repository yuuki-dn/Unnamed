from utils.database import Database
from utils.cache import LRUCache, get_current_time

import logging

class MemberXPEntity:
    __slots__ = "user_id", "xp", "last_update_timestamp"
    
    def __init__(self, user_id: int, xp: int):
        self.user_id: int = user_id
        self.xp: int = xp
        self.last_update_timestamp: int = 0
        

class MemberXPData:
    def __init__(self, database: Database):
        self.logger = logging.getLogger(__name__)
        self.database = database
        self.cache: LRUCache = LRUCache(1000, 600)
        
    async def get_member_data(self, user_id: int) -> MemberXPEntity | None:
        try: 
            return self.cache.get(user_id)
        except KeyError:
            entity = None
            try:
                result = await self.database.execute_query("SELECT `xp` FROM `member_xp` WHERE `user_id` = %s", (user_id))
                entity = MemberXPEntity(user_id, 0)
                if result.__len__() == 0: 
                    await self.database.execute_update("INSERT INTO `member_xp` (`user_id`, `xp`) VALUE (%s, %s)", (user_id, 0))
                else:
                    entity.xp = result[0][0]
                self.cache.put(user_id, entity)
            except Exception as e:
                self.logger.error(f"Đã xảy ra lỗi khi lấy dữ liệu điểm XP cho thành viên ID: {user_id}", repr(e))
            finally: return entity
                
                
    async def add_xp(self, user_id: int, amount: int):
        entity = await self.get_member_data(user_id)
        if entity is None: return
        entity.xp += amount
        if entity.xp < 0: entity.xp = 0
        entity.last_update_timestamp = get_current_time()
        try:
            await self.database.execute_update("UPDATE `member_xp` SET `xp` = %s WHERE `user_id` = %s", (entity.xp, entity.user_id))
        except Exception as e:
            self.logger.error(f"Đã xảy ra lỗi khi cập nhật dữ liệu điểm XP cho thành viên ID: {user_id}", repr(e))
            
    
    async def remove_xp(self, user_id: int, amount: int):
        entity = await self.get_member_data(user_id)
        if entity is None: return
        entity.xp -= amount
        if entity.xp < 0: entity.xp = 0
        entity.last_update_timestamp = get_current_time()
        try:
            await self.database.execute_update("UPDATE `member_xp` SET `xp` = %s WHERE `user_id` = %s", (entity.xp, entity.user_id))
        except Exception as e:
            self.logger.error(f"Đã xảy ra lỗi khi cập nhật dữ liệu điểm XP cho thành viên ID: {user_id}", repr(e))
        