from utils.database import Database
from utils.cache import LRUCache, get_current_time

import logging

class MemberXPData:
	def __init__(self, database: Database):
		self.logger = logging.getLogger(__name__)
		self.database = database
		self.cooldown_cache = LRUCache(1000, 300)


	def check_cooldown(self, member_id: int, cooldown: int) -> bool:
		last_activity = 0
		try: last_activity = self.cooldown_cache.get(member_id)
		except KeyError: pass
		current_time = get_current_time()
		passed = (last_activity + cooldown) < current_time
		if passed:
			self.cooldown_cache.put(member_id, current_time)
			self.logger.debug(f"Reset XP cooldown for member {member_id}")
		return passed


	async def get_member_xp(self, member_id: int) -> int:
		"Return 0 by default"
		sql = "SELECT xp FROM member_xp WHERE user_id = %s LIMIT 1;"
		result = await self.database.execute_query(sql, (member_id))
		if result.__len__() == 0:
			self.logger.debug(f"Found no XP data of member {member_id}. Fallback to 0")
			return 0
		else:
			self.logger.debug(f"Member {member_id} has {result[0][0]} xp")
			return result[0][0]


	async def increase_member_xp(self, member_id: int, amount: int) -> None:
		sql = """
            INSERT INTO member_xp (user_id, xp) 
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
            xp = xp + VALUES(xp);
        """
		await self.database.execute_update(sql, (member_id, amount))
		self.logger.debug(f"Added {amount} xp to member {member_id}")


	async def reduce_member_xp(self, member_id: int, amount: int) -> None:
		previous = await self.get_member_xp(member_id)
		new_xp = previous - amount
		if new_xp < 0: new_xp = 0
		sql = """
            INSERT INTO member_xp (user_id, xp) 
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
            xp = VALUES(xp);
        """
		await self.database.execute_update(sql, (member_id, new_xp))