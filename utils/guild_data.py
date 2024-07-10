from utils.database import Database
from utils.cache import LRUCache

import logging

class ReactionRoleMessageEntity:
    __slots__ = "message_id", "guild_id", "map"
    
    def __init__(self, message_id: int, guild_id: int):
        self.message_id = message_id
        self.guild_id = guild_id
        self.map: dict[int, int] = {}


class GuildEntity:
    __slots__ = "guild_id", "wordchain_channel_id", "reaction_role_messages"
    
    def __init__(self, guild_id: int, wordchain_channel_id = 0):
        self.guild_id = guild_id
        self.wordchain_channel_id = wordchain_channel_id
        self.reaction_role_messages: set[int] = set()
        

class GuildData:
    def __init__(self, database: Database):
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.database: Database = database
        self.guild_cache: LRUCache = LRUCache(100, 600)
        self.reaction_role_message_cache: LRUCache = LRUCache(1000, 600)
        
    async def __fetch_reaction_role_message__(self, message_id: int, guild_id: int) -> ReactionRoleMessageEntity | None:
        try:
            cursor = await self.database.get_cursor()
            await cursor.execute("SELECT `role_id`, `emoji_id` FROM `reaction_role_messages` WHERE `message_id` = %s", (message_id))
            result: list = await cursor.fetchall()
            if result.__len__() == 0: return None
            entity = ReactionRoleMessageEntity(message_id, guild_id)
            for data in result: entity.map[data[1]] = data[0]
            await cursor.close()
        except Exception as err:
            self.logger.error(f"Truy vấn dữ liệu cho tin nhắn với ID: {message_id} thất bại\n" + repr(err))
            return None
        
    async def __fetch_guild__(self, guild_id: int) -> GuildEntity | None:
        try:
            cursor = await self.database.get_cursor()
            await cursor.execute("SELECT `wordchain_channel_id` FROM `guilds` WHERE `guild_id` = %s", (guild_id))
            result = await cursor.fetchone()
            if result is None: return None
            entity = GuildEntity(guild_id, self.database, result[0])
            await cursor.execute("SELECT `message_id` FROM `reaction_role_messages` WHERE `guild_id` = %s", (guild_id))
            result = await cursor.fetchall()
            for data in result: entity.reaction_role_messages.add(data[0])
            await cursor.close()
            return entity
        except Exception as err:
            self.logger.error(f"Truy vấn dữ liệu cho máy chủ với ID: {guild_id} thất bại\n" + repr(err))
            return None
        
    async def get_guild(self, guild_id: int, create_if_not_exist: bool = True) -> GuildEntity | None:
        entity = None
        try: entity = self.guild_cache[guild_id]
        except KeyError:
            entity = await self.__fetch_guild__(guild_id)
            self.guild_cache.put(guild_id, entity)
        if create_if_not_exist and (entity is None): entity = GuildEntity(guild_id, 0)
        return entity
    
    async def get_guild_reaction_role_message(self, message_id: int, guild_id: int) -> ReactionRoleMessageEntity:
        entity = None
        try: entity = self.reaction_role_message_cache[message_id]
        except KeyError:
            entity = await self.__fetch_reaction_role_message__(message_id)
            self.guild_cache.put(message_id, entity)
        if entity is None: entity = ReactionRoleMessageEntity(message_id, guild_id)
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
            self.guild_cache.delete(entity.guild_id)
        except Exception as err:
            self.logger.error(f"Cập nhật dữ liệu cho máy chủ với ID: {entity.guild_id} thất bại\n" + repr(err))
 
    async def update_reaction_role_message(self, entity: ReactionRoleMessageEntity) -> None:
        try:
            previous: ReactionRoleMessageEntity = await self.get_guild_reaction_role_message(entity.message_id)
            cursor = await self.database.get_cursor()
            
            previous_key = set()
            for key in previous.map: previous_key.add(key)
            new_key = set()
            for key in entity.map: new_key.add(key)
            
            for key in new_key.difference(previous_key):
                # insert new
                await cursor.execute("INSERT INTO `reaction_role_messages` (`message_id`, `emoji_id`, `role_id`) VALUE (%s, %s)", (entity.message_id, key, entity.map[key]))
            
            for key in new_key.intersection(previous_key):
                # update exists
                await cursor.execute("UPDATE `reaction_role_messages` SET `role_id` = %s WHERE `message_id` = %s AND `emoji_id` = %s", (entity.map[key], entity.message_id, key))
                
            for key in previous_key.intersection(new_key):
                # delete
                await cursor.execute("DELETE FROM `reaction_role_messages` WHERE `message_id` = %s AND `emoji_id` = %s", (entity.message_id, key))
                
            await self.database.commit()
            await cursor.close()
            self.guild_cache.delete(entity.guild_id)
            self.reaction_role_message_cache.delete(entity.message_id)
        except Exception as err:
            self.logger.error(f"Cập nhật dữ liệu cho tin nhắn với ID: {entity.message_id} thất bại\n" + repr(err))

        
    async def delete_guild(self, guild_id: int) -> None:
        try:
            cursor = await self.database.get_cursor()
            await cursor.execute("DELETE FROM `guilds` WHERE `guild_id` = %s", (guild_id))
            await self.database.commit()
            await cursor.close()
            self.guild_cache.delete(guild_id)
        except Exception as err:
            self.logger.error(f"Cập nhật dữ liệu cho máy chủ với ID: {guild_id} thất bại\n" + repr(err))
            
    async def delete_reaction_role_message(self, message_id: int) -> None:
        try:
            cursor = await self.database.get_cursor()
            await cursor.execute("DELETE FROM `reaction_role_messages` WHERE `message_id` = %s", (message_id))
            await self.database.commit()
            await cursor.close()
            try: 
                entity: ReactionRoleMessageEntity = self.reaction_role_message_cache[message_id]
                self.guild_cache.delete(entity.guild_id)
            except KeyError: pass
            finally: self.reaction_role_message_cache.delete(message_id)
        except Exception as err:
            self.logger.error(f"Cập nhật dữ liệu cho tin nhắn với ID: {message_id} thất bại\n" + repr(err))
        
            