from typing import Optional, Union

import disnake
from disnake.abc import Connectable

from botbase import BotBase
from mafic import Player, Track
from random import randint

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


	async def next(self):
		track = self.queue.next()
		if track is None:
			if self.notification_channel is not None:
				await self.notification_channel.send("Danh sách chờ đã hết! Bot sẽ tự động rời khỏi kênh thoại của bạn")
			return
		await self.play(track)
		if self.notification_channel is not None:
			await self.notification_channel.send(f"Đang phát: {track.title}")


