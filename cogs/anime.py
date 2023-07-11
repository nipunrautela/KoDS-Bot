import discord
from discord.ext import commands

import datetime
import json
import aiohttp


class Anime(commands.Cog):
    def __init__(self, client):
        self.client = client


async def setup(client):
    await client.add_cog(Anime(client))
