import disnake
from disnake.ext import commands

PREFIX = "$"  # Kí hiệu để gọi các lệnh văn bản
MASTER_GUILD_ID = 1208756727323955250  # ID Server chính

INTENTS = disnake.Intents(
    guilds=True,
    guild_messages=True,    
    guild_reactions=True,
    message_content=True,
    moderation=True,
    voice_states=True,
)

COMMAND_SYNC_FLAGS = commands.CommandSyncFlags(
    allow_command_deletion=True,
    sync_commands=True,
    sync_commands_debug=True,
    sync_global_commands=True,
    sync_guild_commands=True
)
