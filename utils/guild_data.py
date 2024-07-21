from typing import Optional
from utils.database import Database
from utils.cache import LRUCache

import logging


class ReactionRoleMessageEntity:
    __slots__ = "message_id", "guild_id", "map"

    def __init__(self, message_id: int, guild_id: int):
        self.message_id = message_id
        self.guild_id = guild_id
        self.map: dict[str, int] = {}

    def copy(self):
        copy = ReactionRoleMessageEntity(
            self.message_id,
            self.guild_id
        )
        copy.map = self.map.copy()
        return copy


class GuildEntity:
    __slots__ = "guild_id", "wordchain_channel_id", "reaction_role_messages"

    def __init__(self, guild_id: int, wordchain_channel_id=0):
        self.guild_id = guild_id
        self.wordchain_channel_id = wordchain_channel_id
        self.reaction_role_messages: set[int] = set()

    def copy(self):
        copy = GuildEntity(
            self.guild_id,
            self.wordchain_channel_id,
        )
        copy.reaction_role_messages = self.reaction_role_messages.copy()
        return copy


class GuildData:
    def __init__(self, database: Database):
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.database: Database = database
        self.guild_cache: LRUCache = LRUCache(100, 600)
        self.reaction_role_message_cache: LRUCache = LRUCache(1000, 600)

    async def __fetch_reaction_role_message__(self, message_id: int, guild_id: int) -> Optional[ReactionRoleMessageEntity]:
        try:
            result: list = await self.database.execute_query(
                "SELECT emoji, role_id FROM reaction_role_messages WHERE message_id = %s AND guild_id = %s",
                (message_id, guild_id))
            if result.__len__() == 0:
                return None
            entity = ReactionRoleMessageEntity(message_id, guild_id)
            for data in result:
                entity.map[data[0]] = data[1]
            return entity
        except Exception as err:
            self.logger.error(f"Truy vấn dữ liệu cho tin nhắn với ID: {message_id} thất bại\n" + repr(err))
            return None

    async def __fetch_guild__(self, guild_id: int) -> Optional[GuildEntity]:
        try:
            result = await self.database.execute_query("SELECT wordchain_channel_id FROM guilds WHERE guild_id = %s;", guild_id)
            if result.__len__() == 0:
                return None
            entity = GuildEntity(guild_id, result[0][0])
            result = await self.database.execute_query("SELECT message_id FROM reaction_role_messages WHERE guild_id = %s;", guild_id)
            for data in result:
                entity.reaction_role_messages.add(data[0])
            return entity
        except Exception as err:
            self.logger.error(f"Truy vấn dữ liệu cho máy chủ với ID: {guild_id} thất bại\n" + repr(err))
            return None

    async def get_guild(self, guild_id: int, create_if_not_exist: bool = True) -> Optional[GuildEntity]:
        try:
            entity = self.guild_cache.get(guild_id)
        except KeyError:
            entity = await self.__fetch_guild__(guild_id)
            self.guild_cache.put(guild_id, entity)
        if create_if_not_exist and (entity is None):
            return GuildEntity(guild_id, 0)
        return entity.copy() if entity is not None else entity

    async def get_guild_reaction_role_message(self, message_id: int, guild_id: int) -> ReactionRoleMessageEntity:
        try:
            entity = self.reaction_role_message_cache.get(message_id)
        except KeyError:
            entity = await self.__fetch_reaction_role_message__(message_id, guild_id)
            self.guild_cache.put(message_id, entity)
        if entity is None:
            return ReactionRoleMessageEntity(message_id, guild_id)
        return entity.copy() if entity is not None else entity

    async def update_guild(self, entity: GuildEntity) -> None:
        try:
            previous = await self.get_guild(entity.guild_id, False)
            if previous is None:
                await self.database.execute_update(
                    "INSERT INTO guilds (guild_id, wordchain_channel_id) VALUES (%s, %s)",
                    (entity.guild_id, entity.wordchain_channel_id))
            else:
                await self.database.execute_update("UPDATE guilds SET wordchain_channel_id = %s WHERE guild_id = %s",
                                                   (entity.wordchain_channel_id, entity.guild_id))
            self.guild_cache.delete(entity.guild_id)
        except Exception as err:
            self.logger.error(f"Cập nhật dữ liệu cho máy chủ với ID: {entity.guild_id} thất bại\n" + repr(err))

    async def update_reaction_role_message(self, entity: ReactionRoleMessageEntity) -> None:
        try:
            guild_entity = await self.get_guild(entity.guild_id, False)
            if guild_entity is None:
                await self.update_guild(await self.get_guild(entity.guild_id))
            previous: ReactionRoleMessageEntity = await self.get_guild_reaction_role_message(entity.message_id, entity.guild_id)
            previous_key = set()
            for key in previous.map:
                previous_key.add(key)
            new_key = set()
            for key in entity.map:
                new_key.add(key)

            for key in new_key.difference(previous_key):
                # insert new
                await self.database.execute_update(
                    "INSERT INTO reaction_role_messages (message_id, guild_id, emoji, role_id) VALUES (%s, %s, %s, %s)",
                    (entity.message_id, entity.guild_id, key, entity.map[key]))

            for key in new_key.intersection(previous_key):
                # update exists
                await self.database.execute_update(
                    "UPDATE reaction_role_messages SET role_id = %s WHERE message_id = %s AND guild_id = %s AND emoji = %s",
                    (entity.map[key], entity.message_id, entity.guild_id, key))

            for key in previous_key.difference(new_key):
                # delete
                await self.database.execute_update(
                    "DELETE FROM reaction_role_messages WHERE message_id = %s AND guild_id = %s AND emoji = %s ",
                    (entity.message_id, entity.guild_id, key))

            self.guild_cache.delete(entity.guild_id)
            self.reaction_role_message_cache.delete(entity.message_id)
        except Exception as err:
            self.logger.error(f"Cập nhật dữ liệu cho tin nhắn với ID: {entity.message_id} thất bại\n" + repr(err))

    async def delete_guild(self, guild_id: int) -> None:
        try:
            await self.database.execute_update("DELETE FROM guilds WHERE guild_id = %s", guild_id)
            self.guild_cache.delete(guild_id)
        except Exception as err:
            self.logger.error(f"Cập nhật dữ liệu cho máy chủ với ID: {guild_id} thất bại\n" + repr(err))

    async def delete_reaction_role_message(self, message_id: int, guild_id: int) -> None:
        try:
            await self.database.execute_update(
                "DELETE FROM reaction_role_messages WHERE message_id = %s AND guild_id = %s", (message_id, guild_id,))
            self.guild_cache.delete(guild_id)
            self.reaction_role_message_cache.delete(message_id)
        except Exception as err:
            self.logger.error(f"Cập nhật dữ liệu cho tin nhắn với ID: {message_id} thất bại\n" + repr(err))
