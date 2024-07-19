from botbase import BotBase

from .player import VoiceSessionHandler
from .checker import is_voice_member, is_voice_connectable

import asyncio
import disnake
import logging
import json

from mafic import Track, Playlist, PlayerNotConnected, TrackEndEvent, NodePool, Node
from disnake.ext import commands


class Music(commands.Cog):
	def __init__(self, bot: BotBase):
		self.bot: BotBase = bot
		self.logger: logging.Logger = logging.getLogger(__name__)

		self.bot.pool = NodePool(self.bot)
		self.bot.loop.create_task(self.load_node())

	async def load_node(self):
		with open("modules/musicplayer/node.json", 'r') as config:
			data: list = json.loads(config.read())

		try:
			with open('lavalinksessionkey.ini', 'r') as fw:
				session_id = fw.read()
		except FileNotFoundError:
			session_id = None

		for node in data:
			for f in range(5):
				try:
					await self.bot.pool.create_node(host=node['host'],
													port=node['port'],
													password=node['password'],
													label=node['label'],
													resuming_session_id=session_id)
				except Exception as e:
					self.logger.error(f"Đã xảy ra sự cố khi kết nối đến lavalink {e}")

	@commands.Cog.listener()
	async def on_node_ready(self, node: Node):
		with open('lavalinksessionkey.ini', 'w') as fw:
			fw.write(node.session_id)


	async def play_next(self, ctx):
		player: VoiceSessionHandler = ctx.author.guild.voice_client
		next: Track = player.queue.next()
		if next is None:
			await ctx.send("Không có bài hát trong hàng đợi")
			return

		await player.play(next)
		await ctx.send(f"Đang phát: {next.title}")



	@commands.slash_command(
		name="play",
		description="Phát một bản nhạc trên kênh thoại",
		options=[
			disnake.Option(
				name="search",
				description="",
				required=True,
				type=disnake.OptionType.string
			)
		]
	)
	@is_voice_connectable
	async def play(self, inter: disnake.ApplicationCommandInteraction, search: str):
		await inter.response.defer()

		vc: VoiceSessionHandler = inter.author.guild.voice_client
		begined = True

		if vc is None:
			vc: VoiceSessionHandler = await inter.author.voice.channel.connect(cls=VoiceSessionHandler)
			vc.notification_channel = inter.channel
			begined = False

		result = await vc.fetch_tracks(search)

		if isinstance(result, Playlist):
			...
		elif isinstance(result, list):
			...
		else:
			await inter.edit_original_response("Không tìm thấy bài hát nào")
			return

		if not begined:
			await vc.next()


	@commands.slash_command(name="stop", description="Dừng phát nhạc")
	@is_voice_member
	async def stopplayer(self, inter: disnake.ApplicationCommandInteraction):
		await inter.response.defer()

		vc: VoiceSessionHandler = inter.author.guild.voice_client

		try:
			await vc.stop()
			await asyncio.sleep(1)
			await vc.disconnect()
			await inter.edit_original_response("Disconnected")
		except PlayerNotConnected:
			await inter.edit_original_response("Bot đang không phát nhạc.")


	@commands.slash_command(
		name="set_volume",
		description="Cài đặt âm lượng cho bot",
		options=[
			disnake.Option(
				name="amount",
				description="Âm lượng",
				max_value=100,
				min_value=1,
				required=True,
				type=disnake.OptionType.integer
			)
		]
	)
	@is_voice_member
	async def set_volume(self, inter: disnake.ApplicationCommandInteraction, amount: int = 100):
		await inter.response.defer()
		player: VoiceSessionHandler = inter.author.guild.voice_client

		await player.set_volume(amount)

		await inter.edit_original_response(f"Đã chỉnh âm lượng thành {amount}")

	@commands.slash_command(name="pause", description="Tạm dừng bài hát")
	@is_voice_member
	async def pause(self, inter: disnake.ApplicationCommandInteraction):
		await inter.response.defer()
		player: VoiceSessionHandler = inter.author.guild.voice_client
		if player.paused:
			await player.resume()
			await inter.edit_original_response("Đã tiếp tục phát")
		else:
			await player.pause()
			await inter.edit_original_response(f"Đã tạm dừng bài hát")


	@commands.slash_command(name="skip", description="Bỏ qua bài hát")
	@is_voice_member
	async def skip(self, inter: disnake.ApplicationCommandInteraction):
		await inter.response.defer()
		player: VoiceSessionHandler = inter.author.guild.voice_client
		if not player.queue:
			await inter.edit_original_response("Không có bài hát nào khác trong hàng đợi")
		await self.play_next(ctx=inter)

		await inter.edit_original_response(f"Đã tiếp tục phát")

	@commands.slash_command(name="current_playlist", description="Hiển thị danh sách phát đang trong hàng đợi (nếu có)")
	@is_voice_member
	async def display_playlist(self, inter: disnake.ApplicationCommandInteraction):
		await inter.response.defer()


	@commands.Cog.listener()
	async def on_track_end(self, event: TrackEndEvent[VoiceSessionHandler]):

		if not event.player.queue:
			return await event.player.disconnect()
		try:
			playTrack = await event.player.play(event.player.queue[event.player.guild.id].pop(0)) # Load bài hát tiếp theo và xóa nó khỏi queue
		except IndexError:
			print("Đã xảy ra sự cố Index")
			await event.player.disconnect()
			return
		try:
			if playTrack is None:
				await event.player.disconnect()
			channel = event.player.guild.get_channel(event.player.channel.id)
			await channel.send(f"Đang phát {playTrack}")
		except Exception as e:
			print(e)

