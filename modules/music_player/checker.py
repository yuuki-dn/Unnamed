import disnake
from .player import VoiceSessionHandler

def is_voice_connectable(func):
	async def wrapper(self, inter: disnake.ApplicationCommandInteraction, **kwargs):
		if inter.guild_id is None:
			return
		if not inter.author.voice:
			await inter.send(embed=disnake.Embed(
				title="⚠️ Bạn hãy vào một kênh thoại để sử dụng lệnh này nhé",
				color=0xFFFF00
			))
			return

		if not inter.guild.me.voice:
			perms = inter.author.voice.channel.permissions_for(inter.guild.me)
			if not perms.connect:
				await inter.send(embed=disnake.Embed(
					title="⚠️ Bot không có quyền để kết nối vào kênh thoại của bạn",
					color=0xFFFF00
				))
				return

		await func(self, inter, **kwargs)

	return wrapper


def is_player_member(func):
	async def wrapper(self, inter: disnake.ApplicationCommandInteraction, **kwargs):
		if inter.guild_id is None:
			return

		player: VoiceSessionHandler = inter.author.guild.voice_client

		if not player:
			await inter.send(embed=disnake.Embed(
				title="⚠️ Hiện tại bot không phát nhạc trên máy chủ",
				color=0xFFFF00
			))
			return

		if not (inter.author.voice and inter.author.id in inter.guild.me.voice.channel.voice_states):
			await inter.send(embed=disnake.Embed(
				title="⚠️ Bạn hãy vào kênh bot đang phát nhạc để sử dụng lệnh này nhé",
				color=0xFFFF00
			))
			return

		await func(self, inter, player=player, **kwargs)

	return wrapper
