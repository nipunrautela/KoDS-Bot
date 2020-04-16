import discord
from discord.ext import commands
from discord.utils import get
import time
import youtube_dl
import os
import shutil



class Voice(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.queue = {}

    # async def after_song_complete(self, ctx):
    #     print('im here XD!')
    #     self.queue[str(ctx.guild.id)].pop(0)
    #     voice = get(self.client.voice_clients, guild=ctx.guild)
    #     if voice is None:
    #         self.queue[str(ctx.guild.id)] = []
    #         shutil.rmtree(f'./{ctx.guild.id}')
    #     elif voice and voice.is_connected():
    #         if self.queue[str(ctx.guild.id)] == []:
    #             print('Nothing more to play.')
    #             return
    #         else:
    #             print('now here')
    #             song = self.queue[str(ctx.guild.id)][0] + '.mp3'
    #             song_path = f'./{ctx.guild.id}/{song}'
    #             print('final place.')
    #             await ctx.send(f'Playing {self.queue[str(ctx.guild.id)][0]}')
    #             voice.play(discord.FFmpegPCMAudio(song_path), after=lambda e: self.after_song_complete(ctx))
    #             voice.source = discord.PCMVolumeTransformer(voice.source)
    #             voice.source.volume = 0.7


    @commands.command(pass_context=True)
    async def join(self, ctx):
        try:
            channel = ctx.message.author.voice.channel
        except AttributeError:
            await ctx.send('You are not connected to a voice channel')
            return
        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect(timeout=200,reconnect=False)
            self.queue[str(ctx.guild.id)] = []

        await ctx.send(f'Connected to {channel}')

    @commands.command(pass_context=True)
    async def leave(self, ctx):
        try:
            shutil.rmtree(str(ctx.guild.id))
        except FileNotFoundError:
            print('already deleted')
        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            await voice.disconnect()
            await ctx.send(f'Left {voice.channel}')
        else:
            await ctx.send('Not connected to a voice channel!')

    # Play command plays audio after downloading
    @commands.command(pass_context=True)
    async def play(self, ctx, url: str):
        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice is None:
            channel = ctx.message.author.voice.channel
            voice = await channel.connect(timeout=200,reconnect=False)
            self.queue[str(ctx.guild.id)] = []
        if not url.startswith('https:'):
            await ctx.send('Use youtube link like: https://www.youtube.com/watch?v=kOg1egIuOTo')
            return

        dir = str(ctx.guild.id)
        if not dir in os.listdir('../'):
            os.mkdir(str(ctx.guild.id))

        ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '320',
                    }],
                    'outtmpl': f'./{ctx.guild.id}/%(id)s.%(ext)s',
                    'noplaylist': True,
                }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            print("Downloading audio now")
            info_dict = ydl.extract_info(url, download=False)
            if info_dict['id']+'.mp3' in os.listdir(f'./{ctx.guild.id}'):
                print('Song already there! Added to queue')
            else:
                ydl.download([url])

        if voice.is_playing() or voice.is_paused():
            try:
                self.queue[str(ctx.guild.id)].append(info_dict['id'])
                print(f'Added {info_dict["title"]} to queue.')
                return
            except KeyError:
                print(f'Dictionary not found. Making new with name {ctx.guild.id}')
                self.queue[str(ctx.guild.id)] = [info_dict['id']]
                return
        self.queue[str(ctx.guild.id)] = [info_dict['id']]
        song_name = info_dict['id'] + '.mp3'
        song_path = f'./{ctx.guild.id}/{song_name}'
        print(song_path)
        async def after_song_complete(ctx):
            self.queue.pop(0)
            song_name = self.queue[str(ctx.guild.id)][0] + '.mp3'
            song_path = f'./{ctx.guild.id}/{song_name}'
            voice.play(discord.FFmpegPCMAudio(song_path), after=lambda e: after_song_complete(ctx))
            voice.source = discord.PCMVolumeTransformer(voice.source)
            voice.source.volume = 0.7

        voice.play(discord.FFmpegPCMAudio(song_path), after=lambda e: after_song_complete(ctx))
        voice.source = discord.PCMVolumeTransformer(voice.source)
        voice.source.volume = 0.7


    @commands.command(pass_context=True)
    async def queue(self, ctx):
        print('queue:')
        try:
            print(self.queue[str(ctx.guild.id)])
            await ctx.send(self.queue)
        except KeyError:
            print('no queue')
            await ctx.send('nothing in queue')

    @commands.command(pass_context=True)
    async def pause(self, ctx):
        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice.is_playing():
            voice.pause()
            await ctx.send('Player paused.')
        else:
            await ctx.send('Player is already paused.')

    @commands.command(pass_context=True)
    async def resume(self, ctx):
        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice.is_paused():
            voice.resume()
            await ctx.send('Player resumed.')
        else:
            await ctx.send('Player is not paused.')

    @commands.command(pass_context=True)
    async def stop(self, ctx):
        self.queue[str(ctx.guild.id)] = []
        voice = get(self.client.voice_clients, guild=ctx.guild)
        voice.stop()
        await ctx.send('Player stopped.')


def setup(client):
    client.add_cog(Voice(client))
