from disnake.abc import Connectable
# from botbase import BotBase
from mafic import Player, Track
from random import randint

from collections import deque

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

	def next(self) -> Track | None:
		if self.loop == LoopMode.SONG:
			return self.current_track

		if self.upcoming.__len__() == 0:
			if self.loop == LoopMode.PLAYLIST:
				for track in self.played:
					self.upcoming.append(track)
				self.played.clear()
			else:
				self.current_track = None
				return None

		if self.current_track is not None:
			self.played.append(self.current_track)
			self.current_track = None

		if self.shuffle:
			index = randint(0, self.upcoming.__len__() - 1)
			self.current_track = self.upcoming[index]
			del self.upcoming[index]

		else:
			self.current_track = self.upcoming.popleft()

		return self.current_track

	def previous(self) -> Track | None:
		if self.played.__len__() == 0:
			return None

		self.upcoming.appendleft(self.current_track)
		self.current_track = self.played.pop()
		return self.current_track

	def add(self, track: Track):
		self.upcoming.append(track)


# class MusicClient(Player[BotBase]):
#     def __init__(self, client: BotBase, channel: Connectable) -> None:
#         super().__init__(client, channel)
#         self.queue: dict[int, list[Track]] = {}


if __name__ == "__main__":
	queue = Queue()
	while True:
		cmd = input().strip().split()
		if cmd[0] == "add":
			queue.add(cmd[1])
		if cmd[0] == "next":
			print(queue.next())
		if cmd[0] == "prev":
			print(queue.previous())