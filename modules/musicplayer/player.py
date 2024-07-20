from typing import Optional, Union

import disnake
from disnake.abc import Connectable

from botbase import BotBase
from mafic import Player, Track
from random import randint
from typing import Optional
from utils.conv import fix_characters, time_format
from collections import deque

MessageableChannel = Union[disnake.TextChannel, disnake.Thread, disnake.VoiceChannel, disnake.StageChannel, disnake.PartialMessageable]


class LoopMode(enumerate):
	OFF = 0
	SONG = 1
	PLAYLIST = 2


class Queue:
	def __init__(self):
		self.current_track: Track = None

		self.played: deque[Track] = deque()
		self.upcoming: deque[Track] = deque()

		self.loop = LoopMode.OFF
		self.shuffle: bool = False

	def get_upcoming(self):
		return [track for track in self.upcoming]

	def _continue(self) -> Optional[Track]:
		if self.loop == LoopMode.SONG:
			return self.current_track
		else:
			return self.next()

	def previous(self) -> Optional[Track]:
		if self.played.__len__() == 0:
			return None

		if self.current_track is not None:
			self.upcoming.appendleft(self.current_track)
		self.current_track = self.played.pop()
		return self.current_track


	def next(self):
		if self.upcoming.__len__() == 0 and self.loop == LoopMode.PLAYLIST:
			for track in self.played:
				self.upcoming.append(track)
			self.played.clear()

		if self.current_track is not None:
			self.played.append(self.current_track)
			self.current_track = None

		if self.upcoming.__len__() != 0:
			if self.shuffle:
				index = randint(0, self.upcoming.__len__() - 1)
				self.current_track = self.upcoming[index]
				del self.upcoming[index]
			else:
				self.current_track = self.upcoming.popleft()

		return self.current_track

	def add(self, track: Track):
		self.upcoming.append(track)

	def clear(self):
		self.upcoming.clear()
		self.played.clear()




class VoiceSessionHandler(Player[BotBase]):
	def __init__(self, bot: BotBase, channel: Connectable) -> None:
		super().__init__(bot, channel)
		self.bot = bot
		self.channel = channel
		self.queue: Queue = Queue()
		self.notification_channel: MessageableChannel = None
		self.message_hook_id: int = None


	async def next(self):
		track = self.queue._continue()
		if track is None:
			if self.notification_channel is not None:
				await self.notification_channel.send("Danh sách chờ đã hết. Bot sẽ rời khỏi kênh của bạn")
			await self.disconnect(force=True)
			return
		await self.play(track, replace=True)
		if self.notification_channel is not None:
			try:
				await self.notification_channel.send(
					f"Đang phát: {track.title}, thời lượng: {time_format(track.length)}\n-# ↪ Bài hát tiếp theo: {self.queue.upcoming[0].title}, [URL](<{self.queue.upcoming[0].uri}>)")
			except KeyError:
				await self.notification_channel.send(
					f"Đang phát: {track.title}, thời lượng: {time_format(track.length)}\n-# Đã hết bài hát trong hàng đợi")

	async def previous(self) -> bool:
		track = self.queue.previous()
		if track is None:
			return False
		await self.play(track, replace=True)
		if self.notification_channel is not None:
			await self.notification_channel.send(
					f"Đang phát: {track.title}, thời lượng: {time_format(track.length)}\n-# ↪ Bài hát tiếp theo: {self.queue.upcoming[0].title}, [URL](<{self.queue.upcoming[0].uri}>)")
		return True

	async def _continue(self):
		track = self.queue._continue()
		if track is None:
			if self.notification_channel is not None:
				await self.notification_channel.send("Danh sách chờ đã hết. Bot sẽ rời khỏi kênh của bạn")
			await self.disconnect(force=True)
			return
		await self.play(track, replace=True)
		if self.notification_channel is not None:
			try:
				await self.notification_channel.send(f"Đang phát: {track.title}, thời lượng: {time_format(track.length)}\n-# ↪ Bài hát tiếp theo: {self.queue.upcoming[0].title},[URL](<{self.queue.upcoming[0].uri}>)")
			except KeyError:
				await self.notification_channel.send(
					f"Đang phát: {track.title}, thời lượng: {time_format(track.length)}\n-# Đã hết bài hát trong hàng đợi")

class QueueInterface(disnake.ui.View):

	def __init__(self, player: VoiceSessionHandler, timeout = 60):
		self.player = player
		self.pages = []
		self.selected = []
		self.current = 0
		self.max_pages = len(self.pages) - 1
		self.message: Optional[disnake.Message] = None
		super().__init__(timeout=timeout)
		self.embed = disnake.Embed()
		self.update_pages()
		self.update_embed()

	def update_pages(self):

		counter = 1

		self.pages = list(disnake.utils.as_chunks(self.player.queue.upcoming, max_size=12))
		self.selected.clear()

		self.clear_items()

		for n, page in enumerate(self.pages):

			txt = "\n"
			opts = []

			for t in page:
				duration = time_format(t.length) if not t.stream else '🔴 Livestream'

				txt += f"`┌ {counter})` [`{fix_characters(t.title, limit=50)}`]({t.uri})\n" \
					   f"`└ ⏲️ {duration}`\n"

				opts.append(
					disnake.SelectOption(
						label=f"{counter}. {t.author}"[:25], description=f"[{duration}] | {t.title}"[:50],
						value=f"queue_select_{t.id}",
					)
				)

				counter += 1

			self.pages[n] = txt
			self.selected.append(opts)

		first = disnake.ui.Button(emoji='⏮️', style=disnake.ButtonStyle.grey)
		first.callback = self.first
		self.add_item(first)

		back = disnake.ui.Button(emoji='⬅️', style=disnake.ButtonStyle.grey)
		back.callback = self.back
		self.add_item(back)

		next = disnake.ui.Button(emoji='➡️', style=disnake.ButtonStyle.grey)
		next.callback = self.next
		self.add_item(next)

		last = disnake.ui.Button(emoji='⏭️', style=disnake.ButtonStyle.grey)
		last.callback = self.last
		self.add_item(last)

		stop_interaction = disnake.ui.Button(emoji='⏹️', style=disnake.ButtonStyle.grey)
		stop_interaction.callback = self.stop_interaction
		self.add_item(stop_interaction)

		update_q = disnake.ui.Button(emoji='🔄', label="Làm mới", style=disnake.ButtonStyle.grey)
		update_q.callback = self.update_q
		self.add_item(update_q)

		self.current = 0
		self.max_page = len(self.pages) - 1

	async def on_timeout(self) -> None:

		if not self.message:
			return

		embed = self.message.embeds[0]
		embed.set_footer(text="Đã hết thời gian tương tác!")

		for c in self.children:
			c.disabled = True

		await self.message.edit(embed=embed, view=self)

	def update_embed(self):
		self.embed.title = f"**Các bài hát trong hàng [{self.current + 1} / {self.max_page + 1}]**"
		self.embed.description = self.pages[self.current]
		self.children[0].options = self.selected[self.current]

		for n, c in enumerate(self.children):
			if isinstance(c, disnake.ui.StringSelect):
				self.children[n].options = self.selected[self.current]

	async def first(self, interaction: disnake.MessageInteraction):

		self.current = 0
		self.update_embed()
		await interaction.response.edit_message(embed=self.embed, view=self)

	async def back(self, interaction: disnake.MessageInteraction):

		if self.current == 0:
			self.current = self.max_page
		else:
			self.current -= 1
		self.update_embed()
		await interaction.response.edit_message(embed=self.embed, view=self)

	async def next(self, interaction: disnake.MessageInteraction):

		if self.current == self.max_page:
			self.current = 0
		else:
			self.current += 1
		self.update_embed()
		await interaction.response.edit_message(embed=self.embed, view=self)

	async def last(self, interaction: disnake.MessageInteraction):

		self.current = self.max_page
		self.update_embed()
		await interaction.response.edit_message(embed=self.embed, view=self)

	async def stop_interaction(self, interaction: disnake.MessageInteraction):

		await interaction.response.edit_message(content="Đóng", embed=None, view=None)
		self.stop()

	async def update_q(self, interaction: disnake.MessageInteraction):

		self.current = 0
		self.max_page = len(self.pages) - 1
		self.update_pages()
		self.update_embed()
		await interaction.response.edit_message(embed=self.embed, view=self)
