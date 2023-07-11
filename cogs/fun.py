import discord
from discord.ext import commands
from .utils import emojis

import random


class Fun(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.cooldown(rate=1, per=0.3, type=commands.BucketType.user)
    async def echo(self, ctx, *, msg):
        reply = f'{msg}'
        await ctx.send(reply)

    @commands.command()
    async def coinflip(self, ctx):
        possibilities = [f'Heads', f'Tails']
        await ctx.send(f'{ctx.author.mention} That is a {random.choice(possibilities)}')

    @commands.command()
    async def play(self, ctx, *, song):
        await ctx.send(f'{ctx.author.mention} Now Playing - {song}')

    @commands.command()
    async def reverse(self, ctx, *, msg):
        reverse = msg[::-1]
        await ctx.send(reverse)

    @commands.command()
    async def die(self, ctx):
        await ctx.send(f"{ctx.author.mention} HAH!! You are the one who's gonna die")

    @commands.command()
    async def date(self, ctx):
        if ctx.author.id == 310610159187525634:
            await ctx.send(f"{ctx.author.mention} Who said you could ask me out. I don't date ugly people like you!! GO AWAY!!")
        else:
            await ctx.send(f"{ctx.author.mention} Sure! I'd love to go out with you. I am free tomorrow from 11am to 6pm.")

    @commands.command()
    @commands.cooldown(rate=1, per=0.3, type=commands.BucketType.user)
    async def explosion(self, ctx):
        explosion_gifs = [
            'https://media1.tenor.com/images/a5200ff8939402e4e2bbda3a8107d2b1/tenor.gif',
            'https://media1.tenor.com/images/98caa6a5d6e5aec2c18006b447c031e7/tenor.gif',
        ]
        embed = discord.Embed()
        embed.set_image(url=random.choice(explosion_gifs))

        await ctx.send(embed=embed)

    @commands.command(description='Give one single retarded aqua GIF')
    @commands.cooldown(rate=1, per=0.3, type=commands.BucketType.user)
    async def aqua(self, ctx):
        aqua_gifs = [
            'https://media.giphy.com/media/yiqkf0clPXvAk/giphy.gif',
            'https://media1.tenor.com/images/7e13669d2de703cc241cb20f0d607132/tenor.gif',
            'https://media1.tenor.com/images/2c749faa36e9660aaf82857343673256/tenor.gif',
            'https://media1.tenor.com/images/9ebecefff04131fa2dead785d18d24c2/tenor.gif',
            'https://media1.tenor.com/images/ac316f9ae3b7daac3547ec75291d82a0/tenor.gif',
            'https://media1.tenor.com/images/1a97b46ae10696e276f90876cc3ac23c/tenor.gif',
        ]
        embed = discord.Embed()
        embed.set_image(url=random.choice(aqua_gifs))

        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(rate=1, per=0.3, type=commands.BucketType.user)
    async def darkness(self, ctx):
        darkness_gifs = [
            'https://media1.tenor.com/images/e62c7975a709acceac39c4bf62e21ca7/tenor.gif',
        ]
        embed = discord.Embed()
        embed.set_image(url=random.choice(darkness_gifs))

        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(rate=1, per=0.3, type=commands.BucketType.user)
    async def dance(self, ctx):
        dance_gifs = [
            'https://media1.tenor.com/images/171c5eafa75ac0bc0176c2d3f8bf347f/tenor.gif',
            'https://media1.tenor.com/images/8e672070f805dbc6876be09b71ce4406/tenor.gif',
        ]
        embed = discord.Embed()
        embed.set_image(url=random.choice(dance_gifs))

        await ctx.send(embed=embed)


async def setup(client):
    await client.add_cog(Fun(client))