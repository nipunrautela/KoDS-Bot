import asyncio

import discord
from discord.ext import commands
import settings


initial_cogs = [
    'cogs.owner',
    'cogs.general',
    'cogs.utility',
    'cogs.party',
    'cogs.fun',
    'cogs.profile',
    'cogs.tags',
    'cogs.shop',
]


class KodsBot(commands.Bot):
    async def setup_hook(self):
        print(f'\nLogged in as: {self.user.name} - {self.user.id}\nVersion: {discord.__version__}\n')
        for cog in initial_cogs:
            try:
                await self.load_extension(cog)
                print(f'Cog: {cog} Loaded!')
            except Exception as e:
                print(f'Error: \nType: {type(e).__name__} \nInfo - {e}')


intents = discord.Intents.all()
intents.message_content = True
client = KodsBot(command_prefix=['k.', 'K.', 'alexa '], case_insensitive=True, intents=intents,
                 help_command=commands.DefaultHelpCommand())

# @client.check
# async def bot_check(ctx):
#     check1 = not ctx.author.bot
#     check2 = ctx.guild == client.get_guild(settings.GUILD_ID)
#     check3 = (ctx.channel.id not in settings.BLACKLIST_CHANNELS) or client.is_owner(ctx.author)
#     if not check3:
#         await ctx.send(f'{ctx.author.mention} Bot commands cant be used in this channel!')
#     return check1 and check2 and check3

client.run(settings.TOKEN)
