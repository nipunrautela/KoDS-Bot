import discord
from discord.ext import commands
from .utils import emojis
from .utils.roles import PARTY_PERM_ROLES
import settings

import json
import typing
import datetime
import asyncio
import os


class Party:

    def __init__(self, pname: str, leader: discord.Member, category: discord.CategoryChannel,
                 infochannel: discord.TextChannel, chat: discord.TextChannel, vc: discord.VoiceChannel,
                 created_at: datetime.datetime):
        self.name = pname
        self.leader = leader
        self.category = category
        self.infochannel = infochannel
        self.chat = chat
        self.vc = vc
        self.members = []
        self.created_at = created_at
        self.info_msg = discord.Message

    async def info_embed(self):
        embed = discord.Embed(
            title=f'{self.name}\'s Info',
            description=f'This is {self.leader.display_name}\'s party! \nCreated at: {self.created_at.date()}',
            color=discord.colour.Colour.dark_gold(),
        )
        embed.set_footer(text='KODS Bot by Arcane#0033')
        embed.set_thumbnail(url=self.leader.avatar_url)
        member_list = ' '
        if len(self.members) > 0:
            for member in self.members:
                member_list = f'{member_list}{str(member.display_name)}\n'
        else:
            member_list = 'one man party'
        embed.add_field(
            name='Members',
            value=member_list
        )
        return embed

    async def invite_embed(self):
        embed = discord.Embed(
            title=f'Party Invitation',
            description=f'{self.leader.display_name} invited you to his party. You have 5 minutes to join?\n\
            click {emojis.CHECK_MARK_BUTTON} to join \nclick {emojis.CROSS_MARK_BUTTON} to reject invite',
            color=discord.colour.Colour.dark_gold(),
        )
        embed.set_footer(text='KODS Bot by Arcane#0033')
        embed.set_thumbnail(url=self.leader.avatar_url)
        return embed

    async def set_info(self):
        embed = await self.info_embed()
        self.info_msg = await self.infochannel.send(embed=embed)

    async def update_info(self):
        await self.info_msg.delete()
        embed = await self.info_embed()
        self.info_msg = await self.infochannel.send(embed=embed)

    async def disband(self):
        await self.infochannel.delete()
        await self.chat.delete()
        await self.vc.delete()
        await self.category.delete()

    async def add_member(self, member: discord.Member):
        await self.infochannel.set_permissions(member, read_messages=True, send_messages=False)
        await self.chat.set_permissions(member, read_messages=True, send_messages=True)
        await self.vc.set_permissions(member, view_channel=True, connect=True, speak=True)
        self.members.append(member)
        await self.update_info()

    async def remove_member(self, member: discord.Member):
        await self.category.set_permissions(member, read_messages=False, send_messages=False)
        await self.infochannel.set_permissions(member, read_messages=False, send_messages=False)
        await self.chat.set_permissions(member, read_messages=False, send_messages=False)
        await self.vc.set_permissions(member, view_channel=False, connect=False, speak=False)
        self.members.remove(member)
        await self.update_info()

    def has_member(self, member: discord.Member):
        if self.leader == member or member in self.members:
            return True
        else:
            return False

    def get_id_dict(self):
        members = list()
        for member in self.members:
            members.append(member.id)

        id_dict = {
            'name': self.name,
            'leader_id': self.leader.id,
            'category_id': self.category.id,
            'infochannel_id': self.infochannel.id,
            'chat_id': self.chat.id,
            'vc_id': self.vc.id,
            'member_ids': members,
            'created_at': str(self.created_at),
            'infomsg_id': self.info_msg.id
        }

        return id_dict


class PartyCog(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.parties = {}

    async def save_parties(self):
        data = {}
        for key in self.parties:
            party = self.parties[key]
            id_dict = party.get_id_dict()
            data[key] = id_dict
        cur_dir = os.curdir
        os.chdir(f'{settings.BOT_DIR}/cogs/data')
        os.remove('parties.json')
        with open("parties.json", "w+") as f:
            f.write(' ')
            json.dump(data, f, indent=2)
        os.chdir(cur_dir)

    async def load_parties(self):
        guild = self.client.get_guild(settings.GUILD_ID)
        cur_dir = os.getcwd()
        os.chdir(f'{settings.BOT_DIR}/cogs/data')
        with open("parties.json", "r+") as f:
            o_data = json.load(f)
            for key in o_data:
                data = o_data[key]
                name = data['name']
                leader = await guild.fetch_member(data['leader_id'])
                category = await self.client.fetch_channel(data['category_id'])
                infochannel = await self.client.fetch_channel(data['infochannel_id'])
                chat = await self.client.fetch_channel(data['chat_id'])
                vc = await self.client.fetch_channel(data['vc_id'])
                p_members = []
                for member_id in data['member_ids']:
                    p_members.append(await guild.fetch_member(member_id))
                c_at = datetime.datetime.strptime(data['created_at'], "%Y-%m-%d %H:%M:%S.%f")
                info_msg = await infochannel.fetch_message(data['infomsg_id'])
                self.parties[key] = Party(pname=name, leader=leader, category=category,
                                          infochannel=infochannel, chat=chat, vc=vc, created_at=c_at)
                self.parties[key].info_msg = info_msg
                self.parties[key].members = p_members
        os.chdir(cur_dir)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.load_parties()

    def in_party(self, member: discord.Member):
        # checks if the person is in a party
        for party in self.parties:
            if self.parties[party].has_member(member):
                return True, self.parties[party]

        return False, None

    @commands.group()
    async def party(self, ctx):
        pass

    @party.command(aliases=['make', 'form'])
    @commands.has_any_role(*PARTY_PERM_ROLES)
    async def create(self, ctx, *, name: typing.Optional[str]):
        condition, party = self.in_party(ctx.author)
        if condition:
            await ctx.send(content=f'You are already in a party.', embed=await party.info_embed())
            return

        guild = ctx.guild
        category_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True),
            await guild.fetch_member(ctx.author.id): discord.PermissionOverwrite(read_messages=True)
        }
        pname = name or f'{ctx.author.display_name}\'s Party'
        leader = ctx.author
        category = await guild.create_category(f'{pname}', overwrites=category_overwrites)
        await category.edit(position=2)
        infochannel = await category.create_text_channel('Party Info')
        chat = await category.create_text_channel('Party Chat')
        vc = await category.create_voice_channel('Party VC')

        party = Party(pname, leader, category, infochannel, chat, vc, ctx.message.created_at)
        self.parties[f'{ctx.author.id}'] = party
        await self.parties[f'{ctx.author.id}'].set_info()

        await ctx.send(f'Your party {pname} has been created.\n Check {infochannel.mention} for party info')

        await self.save_parties()

    @create.error
    async def createparty_handler(self, ctx, error):
        if isinstance(error, commands.MissingAnyRole):
            await ctx.send(f'You don\'t have the role to create a party')
        else:
            print(error)

    @party.command(aliases=['fuck', 'destroy', 'break'])
    async def disband(self, ctx):
        try:
            party = self.parties[f'{ctx.author.id}']
            await party.disband()
            self.parties.pop(f'{ctx.author.id}')
            await ctx.send(f'POOF! Your party is disbanded.')

            await self.save_parties()
        except KeyError:
            await ctx.send(f'You don\'t lead a party')
        except discord.errors.NotFound:
            party = self.parties[f'{ctx.author.id}']
            await party.disband()
            self.parties.pop(f'{ctx.author.id}')
            await ctx.author.send(f'{ctx.author.mention} POOF! Your party is disbanded.')

            await self.save_parties()
        except Exception as e:
            print(f'Error: Type: {type(e).__name__} \nInfo: {e}')

    @party.command()
    async def invite(self, ctx, member: discord.Member):
        party = self.parties[f'{ctx.author.id}']

        # check if the member is already in a party or owns a party
        condition, cparty = self.in_party(member)
        if condition:
            await ctx.send(content=f'{member.display_name} is already in a {cparty.leader.display_name}\'s party.')
            return

        embed = await party.invite_embed()
        try:
            invite = await member.send(embed=embed)
        except discord.errors.Forbidden:
            invite = await ctx.send(f'{member.mention}', embed=embed)

        await invite.add_reaction(emojis.CHECK_MARK_BUTTON)
        await invite.add_reaction(emojis.CROSS_MARK_BUTTON)

        await ctx.send(f'{ctx.author.mention}\n{member.display_name} has been sent an invitation to your party!')

        def check(reaction, user):
            return user == member

        try:
            reaction, user = await self.client.wait_for('reaction_add', timeout=300.0, check=check)
            if str(reaction.emoji) == emojis.CHECK_MARK_BUTTON:
                await invite.channel.send(f'{member.mention}\nYou have joined {ctx.author.display_name}\'s Party')
                await party.add_member(member)
            elif str(reaction.emoji) == emojis.CROSS_MARK_BUTTON:
                await invite.channel.send(f'{member.mention}\nYou have chosen not to join {ctx.author.display_name}\'s Party')
                await ctx.send(f'{ctx.author.mention}. {member.display_name} has rejected your party invite.')
            else:
                await invite.channel.send(f'Please react with {emojis.CHECK_MARK_BUTTON} or {emojis.CROSS_MARK_BUTTON}')
        except asyncio.TimeoutError:
            await invite.channel.send(f'{member.mention}\nTimeout! You did not join {ctx.author.display_name}\'s Party')
        finally:
            await self.save_parties()

    @party.command()
    async def remove(self, ctx, member: discord.Member):
        try:
            party = self.parties[f'{ctx.author.id}']
            if not party.has_member(member):
                await ctx.send(f'{member.display_name} is not in your party')
                return
            await party.remove_member(member)

            await self.save_parties()
        except KeyError:
            ctx.send(f'You don\'t lead a party.')

    @party.command()
    @commands.is_owner()
    async def members(self, ctx, leader: discord.Member):
        try:
            party = self.parties[f'{leader.id}'].members
            await ctx.send(f'Party Members: {party}')
        except KeyError:
            await ctx.send(f'{leader.display_name}\'s party doesn\'t exist, just like their waifu')

    @party.command()
    @commands.is_owner()
    async def forcedisband(self, ctx, leader: discord.Member):
        try:
            party = self.parties[f'{leader.id}']
            await party.disband()
            self.parties.pop(f'{leader.id}')

            await self.save_parties()
        except KeyError:
            await ctx.send(f'{leader.display_name} don\'t have a party')
        except Exception as e:
            print(f'Error: Type: {type(e).__name__} \nInfo: {e}')

    @party.command(name='list')
    async def _list(self, ctx):
        if len(self.parties) == 0:
            active_parties = f'No active data found'
        else:
            active_parties = f' '
        i = 1
        for party in self.parties:
            party_r = self.parties[party]
            active_parties += f'{i}. **{party_r.name}** led by {party_r.leader}\n'
            i += 1

        embed = discord.Embed(
            title='List of Active Parties',
            description=active_parties,
        )

        await ctx.send(embed=embed)

    @party.command()
    @commands.is_owner()
    async def load(self, ctx):
        msg = await ctx.send(f'BREH WORKING ON IT!!!')
        await self.load_parties()
        await msg.edit(content= f'BREH DONE!!')


async def setup(client):
    await client.add_cog(PartyCog(client))
