from botbase import BotBase

from .player import VoiceSessionHandler, QueueInterface
from .checker import is_player_member, is_voice_connectable

import disnake
import logging
import json

from mafic import Track, Playlist, PlayerNotConnected, TrackEndEvent, NodePool, Node
from mafic.events import EndReason
from disnake.ext import commands
from utils.conv import time_format


def limit_text_size(text: str, size: int) -> str:
	if text.__len__() < size:
		return text
	else:
		return text[:size - 3] + "..."



class Music(commands.Cog):
	def __init__(self, bot: BotBase):
		self.bot: BotBase = bot
		self.logger: logging.Logger = logging.getLogger(__name__)

		self.pool = NodePool(self.bot)
		self.bot.loop.create_task(self.load_node())

	async def load_node(self):
		self.aval_node: list[Node] = []
		self.failed_node: list[Node] = []
		with open("modules/musicplayer/node.json", 'r') as config:
			data: list = json.loads(config.read())

		try:
			with open('lavalinksessionkey.ini', 'r') as fw:
				session_id = fw.read()
		except FileNotFoundError:
			session_id = None

		for node in data:
			try:
				await self.pool.create_node(host=node['host'],
												port=node['port'],
												password=node['password'],
												label=node['label'],
												resuming_session_id=session_id)
				self.aval_node.append(node)
			except Exception as e:
				self.logger.error(f"Đã xảy ra sự cố khi kết nối đến lavalink {node['host']}: {e}")
				self.failed_node.append(node)
			else:
				break

	@commands.Cog.listener()
	async def on_node_ready(self, node: Node):
		with open('lavalinksessionkey.ini', 'w') as fw:
			fw.write(node.session_id)


	@commands.cooldown(1, 5, commands.BucketType.guild)
	@commands.slash_command(
		name="play",
		description="Phát một bản nhạc trên kênh thoại",
		options=[
			disnake.Option(
				name="search",
				description="Tên hoặc link bài hát",
				required=True,
				type=disnake.OptionType.string
			)
		]
	)
	@commands.guild_only()
	@is_voice_connectable
	async def play(self, inter: disnake.ApplicationCommandInteraction, search: str):
		await inter.response.defer()

		player: VoiceSessionHandler = inter.author.guild.voice_client
		begined = True

		if player is None:
			player: VoiceSessionHandler = await inter.author.voice.channel.connect(cls=VoiceSessionHandler)
			player.notification_channel = inter.channel
			begined = False

		result = await player.fetch_tracks(search)

		if not result:
			await inter.edit_original_response("Không tìm thấy bài hát nào")
			return

		if isinstance(result, Playlist):
			total_time = 0
			for track in result.tracks:
				player.queue.add(track)
				if not track.stream: total_time += track.length

			thumbnail_track = result.tracks[0]
			embed = disnake.Embed(
				title=limit_text_size(thumbnail_track.title, 32),
				url=thumbnail_track.uri,
				color=0xFFFFFF
			)

			embed.description = f"`{result.tracks.__len__()} bài hát | {time_format(total_time)}`"
			embed.set_thumbnail(result.tracks[0].artwork_url)

			await inter.edit_original_response(embed=embed)

		elif isinstance(result, list):
			track: Track = result[0]
			player.queue.add(track)
			embed = disnake.Embed(
				title=limit_text_size(track.title, 32),
				url=track.uri,
				color=0xFFFFFF
			)

			embed.description = f"`{track.author} | {time_format(track.length)}`"
			embed.set_thumbnail(track.artwork_url)

			await inter.edit_original_response(embed=embed)


		if not begined:
			await player._continue()

	@commands.slash_command(name="stop", description="Dừng phát nhạc")
	@commands.guild_only()
	@is_player_member
	async def stop(self, inter: disnake.ApplicationCommandInteraction, player: VoiceSessionHandler):
		await inter.response.defer()

		try:
			await player.disconnect()
			await inter.edit_original_response("Đã dừng phát nhạc")
		except PlayerNotConnected:
			await inter.edit_original_response("Bot đang không phát nhạc.")


	@commands.slash_command(name="pause", description="Tạm dừng bài hát")
	@commands.guild_only()
	@is_player_member
	async def pause(self, inter: disnake.ApplicationCommandInteraction, player: VoiceSessionHandler):
		await inter.response.defer()
		if player.paused:
			await player.resume()
			await inter.edit_original_response("Đã tiếp tục phát")
		else:
			await player.pause()
			await inter.edit_original_response(f"Đã tạm dừng bài hát")

	@commands.cooldown(1, 10, commands.BucketType.guild)
	@commands.slash_command(name="next", description="Phát bài hát tiếp theo")
	@commands.guild_only()
	@is_player_member
	async def next(self, inter: disnake.ApplicationCommandInteraction, player: VoiceSessionHandler):
		await inter.response.defer()
		await player.next()
		await inter.edit_original_response("Đã chuyển sang bài hát tiếp theo")

	@commands.cooldown(1, 10, commands.BucketType.guild)
	@commands.slash_command(name="prev", description="Phát lại bài hát trước đó")
	@is_player_member
	async def prev(self, inter: disnake.ApplicationCommandInteraction, player: VoiceSessionHandler):
		await inter.response.defer()
		result = await player.previous()
		if result:
			await inter.edit_original_response("Đã quay lại bài hát trước đó")
		else:
			await inter.edit_original_response("Không có bài hát nào đã phát trước đó")

	@commands.cooldown(1, 20, commands.BucketType.guild)
	@commands.slash_command(name="queue_display", description="Hiển thị danh sách chờ")
	@is_player_member
	async def queuedisplay(self, inter: disnake.ApplicationCommandInteraction, player: VoiceSessionHandler):
		await inter.response.defer()
		if not player.queue.upcoming:
			return await inter.edit_original_response("Không có bài hát trong hàng đợi")

		view = QueueInterface(player=player)
		embed = view.embed

		kwargs = {
			"embed": embed,
			"view": view
		}
		try:
			func = inter.followup.send
			kwargs["ephemeral"] = True
		except AttributeError:
			func = inter.send
			kwargs["ephemeral"] = True

		view.message = await func(**kwargs)

		await view.wait()

	# @is_player_member
	# @commands.slash_command(name="change_node", description="Đổi máy chủ phát nhạc")
	# async def change_node(
	# 		self,
	# 		inter: disnake.AppCmdInter,
	# 		player: VoiceSessionHandler,
	# 		node: str = commands.Param(name="server", description="Máy chủ âm nhạc")
	# ):
	# 	await inter.response.defer()
	# 	if node not in self.aval_node:
	# 		await inter.edit_original_response(f"Máy chủ âm nhạc **{node}** không tìm thấy.")
	# 		return
	#
	# 	if node == player.node:
	# 		await inter.edit_original_response(f"Người chơi đã ở trên máy chủ âm nhạc **{node}**.")
	# 		return
	#
	# 	await player.transfer_to(node)
	# 	await inter.edit_original_response(f"Di chuyển trình phát sang máy chủ âm nhạc **{node}**")
	#
	# @change_node.autocomplete("node")
	# async def node_suggestions(self, inter: disnake.Interaction, query: str):
	#
	# 	node: list[Node] = self.aval_node
	#
	# 	if not query:
	# 		return [n.label for n in node]
	#
	# 	return [n.label for n in node and query.lower() in n.label.lower()] -> chưa test, hãy sửa

	@commands.Cog.listener()
	async def on_track_end(self, event: TrackEndEvent[VoiceSessionHandler]):
		player = event.player
		reason = event.reason
		if reason == EndReason.FINISHED:
			await player._continue()
		elif reason == EndReason.LOAD_FAILED:
			await player.notification_channel.send(f"Đã có lỗi xảy ra khi tải bài hát {player.queue.current_track.title}")
			self.logger.warning(f"Tải bài hát được yêu cầu ở máy chủ {player.guild.id} thất bại")
			await player.next()




