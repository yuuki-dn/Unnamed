import asyncio
import traceback

from mafic.__libraries import Connectable

from botbase import BotBase
from mafic import Player, Track, Playlist, PlayerNotConnected, TrackEndEvent
from utils.conv import time_format
import disnake
from disnake.ext import commands
from collections import deque




class MusicClient(Player[BotBase]):
    def __init__(self, client: BotBase, channel: Connectable) -> None:
        super().__init__(client, channel)
        self.queue: dict[int, list[Track]] = {}


class MusicPlayer(commands.Cog):
    def __init__(self, bot: BotBase):
        self.bot: BotBase = bot
        self.is_playing = False
        self.is_pausing = False
        self.volume = 100
        self.vc = None

    async def play_next(self, ctx):
        player: MusicClient = ctx.author.guild.voice_client
        if ctx.guild.id not in player.queue or not player.queue[ctx.guild.id]:
            await ctx.send("Không có bài hát trong hàng đợi")
            return

        track = player.queue[ctx.guild.id].pop(0)
        await player.play(track)
        await ctx.send(f"Đang phát: {track.title}")
        


    @commands.slash_command(name="play", description="Phát một bản nhạc trên kênh thoại", options=[disnake.Option(name="search",
                                                                                                                  description="Tìm kiếm bài hát qua tên hoặc url",
                                                                                                                  required=True,
                                                                                                                  type=disnake.OptionType.string)])
    async def play(self, inter: disnake.ApplicationCommandInteraction, search: str):
        await inter.response.defer()

        if not inter.author.voice:
                await inter.edit_original_response("Nya Nya nyan, pliz join a voice channel")
                return

        if not inter.guild.me.voice:

                perms = inter.author.voice.channel.permissions_for(inter.guild.me)

                if not perms.connect:
                    await inter.edit_original_response("Nya! 💢, I dont have perm to connect to your channel")
                    return

        channel = inter.author.voice.channel

        try:
            vc: MusicClient = await channel.connect(cls=MusicClient)
        except Exception as e:
            if "Already connected to a voice channel" in str(e):
                vc = inter.author.guild.voice_client
            else:
                traceback.print_exc()
                await inter.edit_original_response(f"Nya! 💢")
                return

        await inter.edit_original_response(f"Đang tải {'các' if '&list=' or '&index=' in search else ''} bài hát từ url: {search}")

        tracks = await vc.fetch_tracks(search)
        
        
        
        if inter.guild.id not in vc.queue:
            vc.queue[inter.guild.id] = []
            
        if isinstance(tracks, Playlist):
            if len(tracks.tracks) > 1:
                fetchTracks = tracks.tracks
                vc.queue[inter.guild.id].extend(fetchTracks[1:])
        else:
            vc.queue[inter.guild.id].append(tracks)


        if vc.current:
            await inter.edit_original_response(f"Đã thêm bài hát {search} vào hàng đợi")
            return
        
        if not tracks:
            return await inter.edit_original_response("Không tìm thấy bài hát :<")
        
        loadedtrack = tracks[0]
        
        await vc.play(loadedtrack)
        
        await inter.edit_original_response(f"Đang phát: {loadedtrack.title}, thời lượng: {time_format(loadedtrack.length)}")

    @commands.slash_command(name="stop", description="Dừng các bài hát đang phát")
    async def stopplayer(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()

        vc: MusicClient = inter.author.guild.voice_client
        if not vc:
            await inter.edit_original_response("Nya! 💢, I'm not connected to any voice channel.")
            return
            
            
        if inter.author.id not in inter.guild.me.voice.channel.voice_states:
                await inter.edit_original_response("Nya! 💢, you are not on my channel.")
                return
        try:
            await vc.stop()
            await asyncio.sleep(1)
            await vc.disconnect()
            await inter.edit_original_response("Disconnected")
        except PlayerNotConnected:
            await inter.edit_original_response("Bot đang không phát nhạc.")
            
    @commands.slash_command(name="set_volume", description="Cài đặt âm lượng cho bot", options=[disnake.Option(name="amount", description="Âm lượng", max_value=100, min_value=1, required=True, type=disnake.OptionType.integer)])
    async def set_volume(self, inter: disnake.ApplicationCommandInteraction, amount: int = 100):
        await inter.response.defer()
        player: MusicClient = inter.author.guild.voice_client
        if not player:
            await inter.edit_original_response("Nya! 💢, I'm not connected to any voice channel.")
            return

        if inter.author.id not in inter.guild.me.voice.channel.voice_states:
                await inter.edit_original_response("Nya! 💢, you are not on my channel.")
                return
        
        await player.set_volume(amount)
        
        await inter.edit_original_response(f"Đã chỉnh âm lượng thành {amount}")
        
    @commands.slash_command(name="pause", description="Tạm dừng bài hát")
    async def pause(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        player: MusicClient = inter.author.guild.voice_client
        if not player:
            await inter.edit_original_response("Nya! 💢, I'm not connected to any voice channel.")
            return

        if inter.author.id not in inter.guild.me.voice.channel.voice_states:
                await inter.edit_original_response("Nya! 💢, you are not on my channel.")
                return
        if player.paused:
            await inter.edit_original_response("Bài hát đã bị tạm dừng rồi")
            return
        await player.pause()
        
        await inter.edit_original_response(f"Đã tạm dừng bài hát")
        
    @commands.slash_command(name="resume", description="Tiếp tục bài hát")
    async def resume(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        player: MusicClient = inter.author.guild.voice_client
        if not player:
            await inter.edit_original_response("Nya! 💢, I'm not connected to any voice channel.")
            return

        if inter.author.id not in inter.guild.me.voice.channel.voice_states:
                await inter.edit_original_response("Nya! 💢, you are not on my channel.")
                return
        if not player.paused:
            await inter.edit_original_response("Bài hát ko bị tạm dừng")
            return
        await player.resume()
        
        await inter.edit_original_response(f"Đã tiếp tục phát")

    @commands.slash_command(name="skip", description="Bỏ qua bài hát")
    async def skip(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        player: MusicClient = inter.author.guild.voice_client
        if not player:
            await inter.edit_original_response("Nya! 💢, I'm not connected to any voice channel.")
            return

        if inter.author.id not in inter.guild.me.voice.channel.voice_states:
            await inter.edit_original_response("Nya! 💢, you are not on my channel.")
            return
        if not player.queue:
            await inter.edit_original_response("Không có bài hát nào khác trong hàng đợi")
        await self.play_next(ctx=inter)

        await inter.edit_original_response(f"Đã tiếp tục phát")

    @commands.slash_command(name="current_playlist", description="Hiển thị danh sách phát đang trong hàng đợi (nếu có)")
    async def display_playlist(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        player: MusicClient = inter.author.guild.voice_client
        if not player:
            await inter.edit_original_response("Nya! 💢, I'm not connected to any voice channel.")
            return

        if inter.author.id not in inter.guild.me.voice.channel.voice_states:
            await inter.edit_original_response("Nya! 💢, you are not on my channel.")
            return

        if not player.queue[inter.guild.id]:
            await inter.edit_original_response("Không có bài hát đang trong hàng đợi")
            return

        for item in player.queue[inter.guild.id]:
            ...

    @commands.Cog.listener()
    async def on_track_end(self, event: TrackEndEvent[MusicClient]):

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

