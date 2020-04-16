import discord
from discord.ext import commands

import datetime
import json
import aiohttp


class Anime(commands.Cog):
    def __init__(self, client):
        self.client = client


def setup(client):
    client.add_cog(Anime(client))
