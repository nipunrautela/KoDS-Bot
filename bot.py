import discord
from discord.ext import commands
import settings

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix=['k.', 'K.', 'alexa '],
                      case_insensitive=True, intents=intents)

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

for cog in initial_cogs:
    try:
        await client.load_extension(cog)
        print(f'Cog: {cog} Loaded!')
    except Exception as e:
        print(f'Error: \nType: {type(e).__name__} \nInfo - {e}')


@client.event
async def on_ready():
    print(f'\nLogged in as: {client.user.name} - {client.user.id}\nVersion: {discord.__version__}\n')


@client.check
async def bot_check(ctx):
    check1 = not ctx.author.bot
    check2 = ctx.guild == client.get_guild(settings.GUILD_ID)
    check3 = (ctx.channel.id not in settings.BLACKLIST_CHANNELS) or client.is_owner(ctx.author)
    if not check3:
        await ctx.send(f'{ctx.author.mention} Bot commands cant be used in this channel!')
    return check1 and check2 and check3


client.run(settings.TOKEN)
