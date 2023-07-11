from discord.ext import commands
import time


class Utility(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command()
    async def ping(self, ctx):
        start = time.perf_counter()
        message = await ctx.send("Ping...")
        end = time.perf_counter()
        duration = (end - start) * 1000
        await message.edit(content=f'Pong! \nhttp - {round(duration)}ms \nWS - {round(self.client.latency * 1000)} ms')


async def setup(client):
    await client.add_cog(Utility(client))
