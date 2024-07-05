import disnake
from disnake.ext import commands
import logging

logger: logging.Logger = logging.getLogger(__name__)

class IllegalWordException(Exception):
    def __init__(self, *args, **kwargs):
        return super().__init__("Từ nhập vào không hợp lệ", *args, **kwargs)


class ChainNotMatchException(Exception):
    def __init__(self, *args, **kwargs):
        return super().__init__("Từ nhập vào không khớp với chuỗi từ hiện tại", *args, **kwargs)


class DuplicateWordError(Exception):
    def __init__(self, *args, word: str, previous_data = None, **kwargs):
        self.previous_data = previous_data
        return super().__init__(f"Từ {word} đã được gán trước đó.", *args, **kwargs)
        

def check_word(word: str) -> str:
    if word.__len__() < 3: raise IllegalWordException()
    word = word.strip().lower()
    if not word.isalpha(): raise IllegalWordException()
    return word


class TrieNode:
    __slots__ = "children", "data"
    
    def __init__(self):
        self.children: list[TrieNode | None] = [None] * 26
        self.data: object | None = None
        

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def _char_to_index(self, char: str) -> int:
        return ord(char) - ord('a')
    
    def insert(self, word: str, data: object) -> None:
        node = self.root
        for char in word:
            index = self._char_to_index(char)
            if node.children[index] is None:
                node.children[index] = TrieNode()
            node = node.children[index]
        if node.data is not None: raise DuplicateWordError(word=word, previous_data=node.data)
        node.data = data
    
    def search(self, word: str) -> object | None:
        node = self.root
        for char in word:
            index = self._char_to_index(char)
            if node.children[index] is None:
                return None
            node = node.children[index]
        return node.data
    

class GuildChain(Trie):
    def __init__(self):
        self.last_end_character = None
        return super().__init__()
        
    def add_word(self, word: str, member_id: int):
        if (self.last_end_character is not None) and (word[0] != self.last_end_character): raise ChainNotMatchException()
        self.insert(word, member_id)
        self.last_end_character = word[-1]
        

class WordChainStorage:
    def __init__(self):
        self.dictionary: Trie = Trie()
        self.guild_pool: dict[GuildChain] = {}
        with open("wordchain/wordlist.txt") as f:
            count = 0
            for line in f.readlines():
                try:
                    word = check_word(line)
                    self.dictionary.insert(word, 0)
                    count += 1
                except Exception as e:
                    logger.error(repr(e))
            logger.info(f"Đã nạp {count} từ vựng tiếng Anh vào bộ nhớ")
            
                
    def add_word(self, word: str, member_id: int, guild_id: int) -> None:
        word = check_word(word)
        if self.dictionary.search(word) is None: raise IllegalWordException()
        guild: GuildChain = self.guild_pool.get(guild_id)
        if guild is None:
            self.guild_pool[guild_id] = GuildChain()
            guild = self.guild_pool.get(guild_id)
        guild.add_word(word, member_id)
        
    def clear(self, guild_id: int):
        try: self.guild_pool.pop(guild_id)
        except: pass
    

class WordChain(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.storage = WordChainStorage()
        

# For testing
if __name__ == "__main__":
    storage = WordChainStorage()
    while True:
        try:
            word = input("> ")
            storage.add_word(word, 123, 123)
        except Exception as e:
            print(repr(e))