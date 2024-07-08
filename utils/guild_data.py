from utils.database import Database
from utils.cache import LRUCache

import logging

class GuildEntity:
    __slots__ = "guild_id", "wordchain_channel_id"
    
    def __init__(self, guild_id: int, wordchain_channel_id = 0):
        self.guild_id = guild_id
        self.wordchain_channel_id = wordchain_channel_id
        

class GuildData:
    def __init__(self, database: Database):
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.database: Database = database
        self.cache: LRUCache = LRUCache(100, 600)
        
    async def __fetch_guild__(self, guild_id: int) -> GuildEntity | None:
        try:
            cursor = await self.database.get_cursor()
            await cursor.execute("SELECT `wordchain_channel_id` FROM `guilds` WHERE `guild_id` = %s", (guild_id))
            result = await cursor.fetchone()
            if result is None: return None
            entity = GuildEntity(guild_id, result[0])
            await cursor.close()
            return entity
        except Exception as err:
            self.logger.error(f"Truy vấn dữ liệu cho máy chủ với ID: {guild_id} thất bại\n" + repr(err))
            return None
        
    async def get_guild(self, guild_id: int, create_if_not_exist: bool = True) -> GuildEntity | None:
        entity = None
        try: entity = self.cache.get(guild_id)
        except KeyError:
            entity = await self.__fetch_guild__(guild_id)
            self.cache.put(guild_id, entity)
        if create_if_not_exist and (entity is None): entity = GuildEntity(guild_id)
        return entity
    
    async def update_guild(self, entity: GuildEntity) -> None:
        try:
            previous = await self.get_guild(entity.guild_id, False)
            cursor = await self.database.get_cursor()
            if previous is None:
                await cursor.execute("INSERT INTO `guilds` (`guild_id`, `wordchain_channel_id`) VALUE (%s, %s)", (entity.guild_id, entity.wordchain_channel_id))
            else:
                await cursor.execute("UPDATE `guilds` SET `wordchain_channel_id` = %s WHERE `guild_id` = %s", (entity.wordchain_channel_id, entity.guild_id))
            await self.database.commit()
            await cursor.close()
            self.cache.delete(entity.guild_id)
        except Exception as err:
            self.logger.error(f"Cập nhật dữ liệu cho máy chủ với ID: {entity.guild_id} thất bại\n" + repr(err))
        
    async def delete_guild(self, guild_id: int) -> None:
        try:
            cursor = await self.database.get_cursor()
            await cursor.execute("DELETE FROM `guilds` WHERE `guild_id` = %s", (guild_id))
            await self.database.commit()
            await cursor.close()
            self.cache.delete(guild_id)
        except Exception as err:
            self.logger.error(f"Cập nhật dữ liệu cho máy chủ với ID: {guild_id} thất bại\n" + repr(err))