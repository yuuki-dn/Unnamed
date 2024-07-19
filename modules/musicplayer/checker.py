import disnake
from .player import VoiceSessionHandler

def is_voice_connectable(func):
	"Checker decorator"
	async def wrapper(inter: disnake.ApplicationCommandInteraction, *args, **kwargs):
		if not inter.author.voice:
			await inter.response.send_message("Bạn hãy vào một kênh thoại để sử dụng lệnh này nhé")
			return

		if not inter.guild.me.voice:
			perms = inter.author.voice.channel.permissions_for(inter.guild.me)
			if not perms.connect:
				await inter.edit_original_response("Tôi không có quyền để kết nối vào kênh thoại của bạn")
				return

		await func(inter, *args, **kwargs)

	return wrapper


def is_player_member(func):
	"Checker decorator"
	async def wrapper(inter: disnake.ApplicationCommandInteraction, *args, **kwargs):
		player: VoiceSessionHandler = inter.author.guild.voice_client

		if not player:
			await inter.edit_original_response("Hiện tại tôi đang không phát nhạc trên máy chủ")
			return

		if not inter.author.voice:
			await inter.response.send_message("Bạn hãy kênh thoại của tôi để sử dụng lệnh này nhé")
			return

		if inter.author.id not in inter.guild.me.voice.channel.voice_states:
			await inter.edit_original_response("Bạn cần ở trong kênh thoại của tôi để sử dụng lệnh này")
			return

		await func(inter, player=player, *args, **kwargs)

	return wrapper
