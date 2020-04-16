import discord
from discord.ext import commands
from .utils import db, roles, emojis

import asyncio
import datetime


async def tag_or_alias_exist(name):
    query1 = f'SELECT tags.name FROM tags JOIN tag_alias ' \
            f'WHERE tags.name="{name}" or (tag_alias.alias="{name}" and tags.name=tag_alias.name)'
    tag = await db.retrieve(query1)
    if tag is None:
        return False
    else:
        return True


class Tag(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command()
    async def tag(self, ctx, *, tag_name='notag'):
        single_query = f'SELECT tags.name, tags.content FROM tags JOIN tag_alias ' \
                f'WHERE tags.name LIKE "{tag_name}" or ' \
                f'(tag_alias.alias LIKE "{tag_name}" and tags.name=tag_alias.name) '

        multi_query = f'SELECT tags.name, tags.content FROM tags JOIN tag_alias ' \
                      f'WHERE tags.name LIKE "%{tag_name}%" or ' \
                      f'(tag_alias.alias LIKE "%{tag_name}%" and tags.name=tag_alias.name) ' \
                      f'GROUP BY tags.name'
        data = await db.retrieve(single_query)
        if data is None:
            data = await db.retrieve(multi_query, 0)
        else:
            await ctx.send(f'{data[1]}')
            return
        if len(data) < 1:
            await ctx.send(f'{ctx.author.mention} No tag or tag alias with name {tag_name} exists. '
                           f'To add tag use ``k.addtag``')
            return
        elif len(data) > 1:
            found_tags = f''
            for tag in data:
                found_tags = f'{found_tags}{tag[0]}\n'
            await ctx.send(f'{ctx.author.mention} Multiple tags Found!\n{found_tags}')
        else:
            await ctx.send(f'{data[0][1]}')

    @commands.command()
    async def addtag(self, ctx):
        def check(msg):
            return ctx.author == msg.author and ctx.channel == msg.channel

        try:
            await ctx.send(f'{ctx.author.mention} What is the name of the tag?')
            tag_name_msg = await self.client.wait_for('message', check=check, timeout=60)
            tag_name = tag_name_msg.content
            if await tag_or_alias_exist(tag_name):
                await ctx.send(f'{ctx.author.mention} ``{tag_name}`` already exists as a tag or an alias.')
                return

            await ctx.send(f'{ctx.author.mention} Enter the content of the tag (type ``cancel`` to abort)')
            tag_content_msg = await self.client.wait_for('message', check=check, timeout=300)
            tag_content = tag_content_msg.content
            if tag_content.lower() == 'cancel':
                await ctx.send(f'{ctx.author.mention} {tag_name} was not added!')
                return
            tag_content = str(tag_content).replace('"', '\\"')
        except asyncio.TimeoutError:
            await ctx.send(f'{ctx.author.mention} You took too long to reply. Tag creation cancelled!')
            return
        now = datetime.datetime.now()
        date = now.strftime('%Y/%m/%d %H:%M:%S')
        user_id = ctx.author.id
        query = f'INSERT INTO tags(name, content, user, reg_ts, last_updated) ' \
                f'VALUES("{tag_name}", "{tag_content}", {user_id}, now(), now())'
        await db.update(query)
        await ctx.send(f'Tag: {tag_name} was successfully created with content: \n```{tag_content_msg.content}```')

    @commands.command()
    async def addalias(self, ctx):
        def check(msg):
            return ctx.author == msg.author and ctx.channel == msg.channel

        try:
            await ctx.send(f'{ctx.author.mention} What is the name of the tag?')
            tag_name_msg = await self.client.wait_for('message', check=check, timeout=60)
            tag_name = tag_name_msg.content
            if not await tag_or_alias_exist(tag_name):
                ctx.send(f'{ctx.author.mention} {tag_name} does not exist!')
                return

            await ctx.send(f'{ctx.author.mention} Enter the alias (type ``cancel`` to abort)')
            tag_alias_msg = await self.client.wait_for('message', check=check, timeout=300)
            tag_alias = tag_alias_msg.content
            if tag_alias.lower() == 'cancel':
                await ctx.send(f'{ctx.author.mention} Cancelled!! An alias for ``{tag_name}`` was not created!')
                return
            tag_alias = str(tag_alias).replace('"', '\\"')

            query = f'INSERT INTO tag_alias(name, alias) VALUES("{tag_name}", "{tag_alias}")'
            await db.update(query)

            await ctx.send(f'{ctx.author.mention} ``{tag_alias}`` was successfully created for tag ``{tag_name}``')
        except asyncio.TimeoutError:
            await ctx.send(f'{ctx.author.mention} You took too long to reply. Alias creation cancelled!')
            return

    @commands.command()
    async def removealias(self, ctx):
        def check(msg):
            return ctx.author == msg.author and ctx.channel == msg.channel

        try:
            await ctx.send(f'{ctx.author.mention} Enter the alias (type ``cancel`` to abort)')
            tag_alias_msg = await self.client.wait_for('message', check=check, timeout=300)
            tag_alias = tag_alias_msg.content
            if tag_alias.lower() == 'cancel':
                await ctx.send(f'{ctx.author.mention} Canceled! ``{tag_alias}`` alias was not deleted!')
                return
            tag_alias = str(tag_alias).replace('"', '\\"')

            query = f'DELETE FROM tag_alias WHERE alias="{tag_alias}"'
            await db.update(query)

            await ctx.send(f'{ctx.author.mention} ``{tag_alias}`` was successfully deleted.')
        except asyncio.TimeoutError:
            await ctx.send(f'{ctx.author.mention} You took too long to reply. Alias removal cancelled!')
            return

    @commands.command()
    @commands.is_owner()
    async def removetag(self, ctx, *, tag_name):
        if not await tag_or_alias_exist(tag_name):
            await ctx.send(f'{ctx.author.mention} {tag_name} does not exist!')
            return

        def check(msg):
            return ctx.author == msg.author and ctx.channel == msg.channel
        try:
            await ctx.send(f'{ctx.author.mention} Do you want to delete {tag_name}? Type CONFIRM')
            confirmation = await self.client.wait_for('message', check=check, timeout=15)
            if confirmation.content.lower() == 'confirm':

                data_query = f'SELECT tags.name, tags.content, tags.user, tags.reg_ts, tags.last_updated ' \
                             f'FROM tags JOIN tag_alias ' \
                             f'WHERE tags.name="{tag_name}" OR ' \
                             f'(tag_alias.alias="{tag_name}" AND tags.name=tag_alias.name)'
                data = await db.retrieve(data_query)
                alias_query = f'SELECT alias FROM tag_alias WHERE name="{tag_name}"'
                alias = await db.retrieve(alias_query, 0)
                aliases = [a[0] for a in alias]
                query = [
                    f'DELETE FROM tags WHERE name="{tag_name}"',
                    f'DELETE FROM tag_alias WHERE name="{tag_name}"'
                ]
                r = await db.update(*query)
                if r == 0:
                    embed = discord.Embed(
                        title=f'Tag Deleted',
                        color=discord.colour.Colour.from_rgb(255, 0, 0)
                    )
                    embed.add_field(name='Tag Name', value=f'{data[0]}')
                    embed.add_field(name='Tag Content', value=f'{data[1][0:1023]}', inline=False)
                    embed.add_field(name='Aliases', value=f'{aliases}', inline=False)
                    embed.add_field(name='Created by', value=f'{data[2]}', inline=False)
                    embed.add_field(name='Registered Date', value=f'{data[3]}', inline=False)
                    embed.add_field(name='Last updated', value=f'{data[4]}')
                    await ctx.send(embed=embed)
        except asyncio.TimeoutError:
            await ctx.send(f'{ctx.author.mention} You took too long to reply. {tag_name} not deleted')
            return

    @commands.command()
    @commands.is_owner()
    async def updatetag(self, ctx):

        def check(msg):
            return ctx.author == msg.author and ctx.channel == msg.channel

        try:
            await ctx.send(f'{ctx.author.mention} Enter the name of the tag to be updated')
            tag_name_msg = await self.client.wait_for('message', check=check, timeout=60)
            tag_name = tag_name_msg.content
            if not await tag_or_alias_exist(tag_name):
                await ctx.send(f'{ctx.author.mention} No tag with name {tag_name} found!')
                return

            await ctx.send(f'{ctx.author.mention} Enter the new content of the tag (type ``cancel`` to abort)')
            tag_content_msg = await self.client.wait_for('message', check=check, timeout=300)
            tag_content = tag_content_msg.content
            if tag_content.lower() == 'cancel':
                await ctx.send(f'{ctx.author.mention} {tag_name} was not updated!')
                return
            tag_content = str(tag_content).replace('"', '\\"')
        except asyncio.TimeoutError:
            await ctx.send(f'You took too long to reply. Tag creation cancelled!')
            return
        query = f'UPDATE tags SET content="{tag_content}", last_updated=now() WHERE name="{tag_name}"'
        await db.update(query)
        await ctx.send(f'Tag: {tag_name} was successfully updated with content: \n```{tag_content_msg.content}```')

    @commands.command()
    async def taginfo(self, ctx, *, tag_name):
        data_query = f'SELECT name, content, user, reg_ts, last_updated FROM tags WHERE name="{tag_name}"'
        data = await db.retrieve(data_query)
        if data is None:
            await ctx.send(f'{ctx.author.mention} No tag with name {tag_name} found!')
            return

        alias_query = f'SELECT alias FROM tag_alias WHERE name="{tag_name}"'
        alias = await db.retrieve(alias_query, 0)
        aliases = [a[0] for a in alias]

        embed = discord.Embed(
            title=f'Tag Info',
            color=discord.colour.Colour.from_rgb(100, 200, 0),
        )
        embed.add_field(name='Tag Name', value=f'{data[0]}')
        embed.add_field(name='Tag Content', value=f'{data[1][0:1023]}', inline=False)
        embed.add_field(name='Aliases', value=f'{aliases}', inline=False)
        embed.add_field(name='Created by', value=f'{ctx.guild.get_member(data[2]).mention}', inline=False)
        embed.add_field(name='Registered Date', value=f'{data[3]}', inline=False)
        embed.add_field(name='Last updated', value=f'{data[4]}', inline=False)
        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(Tag(client))
