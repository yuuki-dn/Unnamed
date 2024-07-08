from marisa_trie import Trie
import logging

logger: logging.Logger = logging.getLogger(__name__)

class IllegalWordException(Exception):
    def __init__(self, *args, **kwargs):
        return super().__init__("Từ nhập vào không hợp lệ", *args, **kwargs)
        

def reform_word(word: str) -> str:
    if word.__len__() < 3: raise IllegalWordException()
    word = word.strip().lower()
    if not word.isalpha(): raise IllegalWordException()
    return word


class Dictionary:
    __slots__ = "storage"
    
    def __init__(self):
        with open("modules/wordchain/wordlist.txt") as f:
            index = []
            for line in f.readlines():
                if line.strip().__len__() == 0: continue
                try: index.append(reform_word(line))
                except Exception as e: logger.error(repr(e))
            self.storage = Trie(index)
            logger.info(f"Đã nạp {index.__len__()} từ vựng tiếng Anh vào bộ nhớ")
            
    def check(self, word: str):
        return reform_word(word) in self.storage
            
            
# For testing
if __name__ == "__main__":
    dictionary = Dictionary()
    while True:
        try:
            word = input("> ")
            print(dictionary.check(word))
        except Exception as e:
            print(repr(e))