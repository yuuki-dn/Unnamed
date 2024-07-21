from botbase import BotBase
from utils.setup_logging import setup_logging
import gc

from modules.administrator.cog import AdminCommands
from modules.chatbot.cog import ChatBot
from modules.leveling.cog import LevelingCog
from modules.music_player.cog import Music
from modules.wordchain.cog import WordChain
from modules.error_handler.cog import ErrorHandler

# Setup logging
setup_logging()

# Garbage collect
gc.collect()
gc.enable()

# Initalize instance
bot = BotBase()

# Add processing component
bot.add_cog(AdminCommands(bot))
bot.add_cog(ChatBot(bot))
bot.add_cog(LevelingCog(bot))
bot.add_cog(Music(bot))
bot.add_cog(WordChain(bot))
bot.add_cog(ErrorHandler(bot))

# Start
bot.run()