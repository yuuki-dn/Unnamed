import disnake
from .player import VoiceSessionHandler

def is_voice_connectable(func):
	async def wrapper(self, inter: disnake.ApplicationCommandInteraction, **kwargs):
		if inter.guild_id is None:
			return
		if not inter.author.voice:
			await inter.send("Bạn hãy vào một kênh thoại để sử dụng lệnh này nhé")
			return

		if not inter.guild.me.voice:
			perms = inter.author.voice.channel.permissions_for(inter.guild.me)
			if not perms.connect:
				await inter.send("Tôi không có quyền để kết nối vào kênh thoại của bạn")
				return

		await func(self, inter, **kwargs)

	return wrapper


def is_player_member(func):
	async def wrapper(self, inter: disnake.ApplicationCommandInteraction, **kwargs):
		if inter.guild_id is None:
			return

		player: VoiceSessionHandler = inter.author.guild.voice_client

		if not player:
			await inter.send("Hiện tại tôi đang không phát nhạc trên máy chủ")
			return

		if not inter.author.voice:
			await inter.send("Bạn hãy vào kênh thoại của tôi để sử dụng lệnh này nhé")
			return

		if inter.author.id not in inter.guild.me.voice.channel.voice_states:
			await inter.send("Bạn cần ở trong kênh thoại của tôi để sử dụng lệnh này")
			return

		await func(self, inter, player=player, **kwargs)

	return wrapper
