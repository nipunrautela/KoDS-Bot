import discord
from discord.ext import commands
from .utils import db, emojis, roles
import settings

import asyncio
import json
import aiohttp
import datetime
from datetime import datetime as dt
import typing


class General(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command()
    async def guildinfo(self, ctx):
        desc = '''Welcome to The Knights of the Dawned Sword Guild.
 To keep it brief we are a World//Zero guild focused primarily on progression and having fun with the game.
We were first created in the World//Zero alpha and have been going strong ever since.
Can't wait to see you in game!'''

        info_embed = discord.Embed(
            title='KoDS {World Zero} Guild Info',
            description=f'{desc}',
            timestamp=dt.utcnow()
        )
        info_embed.set_thumbnail(url=ctx.guild.icon_url)
        info_embed.set_footer(text=f'Knights of the Dawned Sword')

        info_embed.add_field(name='Roblox Group',
                             value='https://www.roblox.com/groups/5012815/Knights-of-the-Dawned-Sword#!/about',
                             inline=False)
        info_embed.add_field(name='Youtube Channel',
                             value='https://youtube.com/channel/UCA8tEQjQdqBDUcWlaSCf9hw',
                             inline=False)
        info_embed.add_field(name='Twitter Handle',
                             value='https://twitter.com/KotDSGuild',
                             inline=False)

        await ctx.send(embed=info_embed)

    @commands.command()
    @commands.is_owner()
    async def dmannounce(self, ctx):
        def check(msg):
            return msg.author == ctx.author and ctx.channel == msg.channel
        try:
            await ctx.send(f'{ctx.author.mention} Enter the announcement to send to DMs')
            announcement = await self.client.wait_for('message', check=check, timeout=60)
            if announcement.content.lower() == 'cancel':
                await ctx.send(f'{ctx.author.mention} Announcement Cancelled!')
                return
        except asyncio.TimeoutError:
            await ctx.send(f'{ctx.author.mention} You took too long to reply. Announcement Cancelled!')
            return
        announce_desc = f'{announcement.content}\n\n' \
                        f'If you do not want to receive DM announcement from this bot Use ``k.toggledmannounce`` or ' \
                        f'``k.tda`` in <#564538248458797067>'
        announce_embed = discord.Embed(
            title=f'Guild Announcement',
            description=announce_desc,
            color=discord.colour.Colour.green(),
            timestamp=datetime.datetime.utcnow()
        )
        announce_embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
        announce_embed.set_thumbnail(url=ctx.guild.icon_url)
        announce_embed.set_footer(text='KODS Bot by Arcane#0033', icon_url=self.client.user.avatar.url)
        guild = ctx.guild
        members = guild.fetch_members()
        announce_role = ctx.guild.get_role(roles.NO_ANNOUNCEMENT_ROLE)
        sending_msg = await ctx.send(f'Sending\n')
        count = 0
        async for member in members:
            if member.bot or member == self.client:
                continue
            count += 1
            if count > 98:
                count = 0
                sending_msg = await ctx.send(f'Sending\n')
            if announce_role not in member.roles:
                try:
                    await member.send(embed=announce_embed)
                    await sending_msg.edit(content=f'{sending_msg.content}\n{member.display_name} '
                                                   f'{emojis.CHECK_MARK_BUTTON}')
                except discord.errors.Forbidden:
                    await sending_msg.edit(content=f'{sending_msg.content}\n{member.display_name} '
                                                   f'{emojis.CROSS_MARK_BUTTON}')
            else:
                await sending_msg.edit(content=f'{sending_msg.content}\n{member.display_name} {emojis.CLOSED_BOOK}')

    @commands.command(aliases=['tda'])
    async def toggledmannounce(self, ctx):
        member = ctx.author
        announce_role = ctx.guild.get_role(roles.NO_ANNOUNCEMENT_ROLE)
        if announce_role in member.roles:
            await member.remove_roles(announce_role)
            await ctx.send(f'{ctx.author.mention} {emojis.CHECK_MARK_BUTTON} You will receive DM announcements now!')
        else:
            await member.add_roles(announce_role)
            await ctx.send(f'{ctx.author.mention} {emojis.CHECK_MARK_BUTTON} You won\'t receive DM announcements anymore! '
                           f'To continue receiving DM announcements use this command again.')

    @commands.command()
    @commands.max_concurrency(number=1, per=commands.BucketType.user)
    async def register(self, ctx):
        if await db.is_registered(ctx.author):
            await ctx.send(f'{ctx.author.mention} You are already registered.')
            return
        display_name = ctx.author.display_name
        async with aiohttp.ClientSession() as cs:
            async with cs.get(f'https://api.roblox.com/users/get-by-username?username={display_name}') as resp:
                text = await resp.text()
                await cs.close()
        data = dict(json.loads(text))

        if 'Username' in data.keys():
            name = data['Username']
            result = await db.register_member(ctx.author, name)
            if result == 0:
                await ctx.send(f'{ctx.author.mention} You are now registered as a guild member')
                await ctx.author.add_roles(ctx.guild.get_role(roles.GUILD_MEMBER_ROLE),
                                           ctx.guild.get_role(roles.D_RANK_ROLE),
                                           ctx.guild.get_role(roles.NOVICE_ROLE),
                                           reason='Registered to guild')
            else:
                await ctx.send(f'{ctx.author.mention} Sorry we failed to register you! Please contact Arcane#0033')
        elif not data['success']:
            def check(m):
                return m.author == ctx.author

            await ctx.send(f'{ctx.author.mention} Enter your roblox username')
            try:
                msg = await self.client.wait_for("message", check=check, timeout=60)
                async with aiohttp.ClientSession() as cs:
                    async with cs.get(f'https://api.roblox.com/users/get-by-username?username={msg.content}') as resp:
                        text = await resp.text()
                        await cs.close()
                data = json.loads(text)
                try:
                    name = data['Username']
                    result = await db.register_member(ctx.author, name)
                    if result == 0:
                        await ctx.author.edit(nick=f'{data["Username"]}')
                        await ctx.send(f'{ctx.author.mention} You are now registered as a guild member')
                        user_roles = ctx.author.roles
                        user_roles.pop(0)
                        await ctx.author.remove_roles(*[role for role in user_roles])
                        await ctx.author.add_roles(ctx.guild.get_role(roles.PLAYER_ROLE))
                        await ctx.author.add_roles(ctx.guild.get_role(roles.GUILD_MEMBER_ROLE),
                                                   ctx.guild.get_role(roles.D_RANK_ROLE),
                                                   reason='Registered to guild')
                    else:
                        await ctx.send(
                            f'{ctx.author.mention} Sorry we failed to register you! Please contact Arcane#0033')
                except KeyError:
                    await ctx.send(f'{ctx.author.mention} No Roblox account with name {msg.content} exists. '
                                   f'Registration process cancelled.')
            except asyncio.TimeoutError:
                await ctx.send(f'{ctx.author.mention} Timeout! Registration process was cancelled.')
                return
        else:
            await ctx.send('Some problems occurred! Report Arcane#0033')

    @commands.command()
    @commands.max_concurrency(number=1, per=commands.BucketType.user)
    async def unregister(self, ctx):
        if not (await db.is_registered(ctx.author)):
            await ctx.send(f'You are not registered with the guild!')
            return
        await ctx.send(f'Are you sure you want to unregister? Type CONFIRM to confirm')

        def check(m):
            return m.author == ctx.author and m.content.lower() == 'confirm'

        try:
            reply = await self.client.wait_for("message", check=check, timeout=60)
            await db.unregister_member(ctx.author)
            await ctx.send(f'You successfully unregistered from the guild!')
            user_roles = ctx.author.roles
            user_roles.pop(0)
            await ctx.author.remove_roles(*[role for role in user_roles])
            await ctx.author.add_roles(ctx.guild.get_role(roles.PLAYER_ROLE))
        except asyncio.TimeoutError:
            await ctx.send(f'{ctx.author.mention} Timeout. You did not unregister.')

    @commands.command()
    @commands.is_owner()
    @commands.max_concurrency(1, commands.BucketType.user, wait=True)
    async def promote(self, ctx, member: typing.Optional[discord.Member] = None, *, reason='No reason given'):
        target = member or ctx.author
        if not (await db.is_registered(target)):
            await ctx.send(f'{target.display_name} is not registered')
            return

        query = f"UPDATE members SET plr_rank=plr_rank+1 WHERE id={target.id}"
        await db.update(query)

        query2 = f"SELECT plr_rank FROM members WHERE id={target.id}"
        data = await db.retrieve(query2)

        roles_to_remove = [ctx.guild.get_role(role) for role in roles.RANK_ORDER[1:]]
        given_role = ctx.guild.get_role(roles.RANK_ORDER[data[0]])

        if data[0] in [3, 5, 7]:
            tier_roles_remove = [ctx.guild.get_role(role) for role in roles.TIER_ROLES]
            tier_role_add = ctx.guild.get_role(roles.TIER_ROLES[int(data[0] / 2)])
            await target.remove_roles(*roles_to_remove, *tier_roles_remove)
            await target.add_roles(given_role, tier_role_add)
        else:
            await target.remove_roles(*roles_to_remove)
            await target.add_roles(given_role)

        embed = discord.Embed(
            title='Rank-Up Message',
            description=f'Congratulations! You\'ve been promoted to ``{given_role.name}`` '
                        f'by {ctx.author.mention}\nReason: {reason}',
        )
        embed.colour = discord.colour.Colour.teal()
        await ctx.message.add_reaction(emojis.CHECK_MARK_BUTTON)
        try:
            sent = await target.send(embed=embed)
        except discord.errors.Forbidden:
            await ctx.channel.send(content=f'{target.mention}', embed=embed)

    @commands.command()
    @commands.is_owner()
    @commands.max_concurrency(1, commands.BucketType.user, wait=True)
    async def demote(self, ctx, member: typing.Optional[discord.Member] = None, *, reason="No reason given"):
        target = member or ctx.author
        if not (await db.is_registered(target)):
            await ctx.send(f'{target.display_name} is not registered')
            return

        query = f"UPDATE members SET plr_rank=plr_rank-1 WHERE id={target.id}"
        await db.update(query)
        query2 = f"SELECT plr_rank FROM members WHERE id={target.id}"
        data = await db.retrieve(query2)

        roles_to_remove = [ctx.guild.get_role(role) for role in roles.RANK_ORDER[1:]]
        given_role = ctx.guild.get_role(roles.RANK_ORDER[data[0]])

        if data[0] in [2, 4, 6]:
            tier_roles_remove = [ctx.guild.get_role(role) for role in roles.TIER_ROLES]
            tier_role_add = ctx.guild.get_role(roles.TIER_ROLES[int(data[0]/2 - 1)])
            await target.remove_roles(*roles_to_remove, *tier_roles_remove)
            await target.add_roles(given_role, tier_role_add)
        else:
            await target.remove_roles(*roles_to_remove)
            await target.add_roles(given_role)

        await ctx.message.add_reaction(emojis.CHECK_MARK_BUTTON)

        embed = discord.Embed(
            title='Demotion Message',
            description=f'Alert! You\'ve been demoted to ``{given_role.name}``\n**Reason**: {reason}'
        )
        embed.colour = discord.colour.Colour.red()
        try:
            sent = await target.send(embed=embed)
        except discord.errors.Forbidden:
            await ctx.channel.send(content=f'{target.mention}', embed=embed)


async def setup(client):
    await client.add_cog(General(client))
