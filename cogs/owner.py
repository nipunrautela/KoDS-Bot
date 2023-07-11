from discord.ext import commands


class Owner(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.is_owner()
    async def load(self, ctx, cog):
        try:
            await self.client.load_extension(f'cogs.{cog}')
        except Exception as e:
            print(f'Error: Type: {type(e).__name__} \nInfo: {e}')
        else:
            await ctx.send(f'Cog: {cog} loaded successfully!')

    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx, cog):
        try:
            await self.client.unload_extension(f'cogs.{cog}')
        except Exception as e:
            print(f'Error: \nType: {type(e).__name__} Info: {e}')
        else:
            await ctx.send(f'Cog: {cog} unloaded successfully!')

    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx, cog):
        try:
            await self.client.reload_extension(f'cogs.{cog}')
        except Exception as e:
            print(f'Error: \nType: {type(e).__name__} Info: {e}')
        else:
            await ctx.send(f'Cog: {cog} reloaded successfully!')


async def setup(client):
    await client.add_cog(Owner(client))
