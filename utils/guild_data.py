from utils.database import Database

class GuildEntity:
    __slots__ = "id", "wordchain_channel_id"
    
    def __init__(self, id: int):
        self.id = id

class GuildData:
    def __init__(self, database: Database):
        self.database = database
        self.storage: dict[int, GuildEntity] = {}
        
    async def get(self, guild_id: int):
        pass