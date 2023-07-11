import discord
from discord.ext import commands
from .utils import db, roles, image, emojis
import settings

import typing
import asyncio
import os
import datetime
import random


class Profile(commands.Cog):

    user_cd = {}

    def __init__(self, client):
        self.client = client
        self.name_count = 0
        self.max_give_rep = 2  # max rep that can be given every day
        self.max_get_rep = 5  # max rep that can be received every day

    async def can_rep(self, repper, repped, date):
        repper_query = f'SELECT count(*) FROM reps WHERE repper={repper.id} and dor="{date}"'
        given = await db.retrieve(repper_query)
        if given[0] >= self.max_give_rep:
            return False, f'{repper.mention}You have already used all of you rep points today!'

        repeat_query = f'SELECT count(*) FROM reps WHERE repper={repper.id} and repped={repped.id} and dor="{date}"'
        already_repped = await db.retrieve(repeat_query)
        if already_repped[0] >= 1:
            return False, f'You\'ve already repped {repped.display_name} once. You can only rep a person once a day'

        repped_query = f'SELECT count(*) FROM reps WHERE repped={repped.id} and dor="{date}"'
        got = await db.retrieve(repped_query)
        if got[0] >= self.max_get_rep:
            return False, f'{repper.mention} {repped.display_name} has received maximum rep for one day! ' \
                          f'They can\'t gain anymore today.'

        return True, "No message"

    async def cog_check(self, ctx):
        if not (await db.is_registered(ctx.author)):
            await ctx.send(f'You are not registered with the guild! Do ``k.register`` to register')
        return await db.is_registered(ctx.author)

    @commands.Cog.listener()
    async def on_message(self, msg):
        await asyncio.sleep(1)
        if not await db.is_registered(msg.author):
            return
        rank = await db.retrieve(f'SELECT plr_rank FROM members WHERE id={msg.author.id}')
        try:
            if Profile.user_cd[msg.author.id] == 1:
                Profile.user_cd[msg.author.id] = 0
                money = ((60//random.randint(5, 7)) * random.randint(1, 3)) * (rank[0])
                query = f'UPDATE members SET credit=credit+{money} WHERE id={msg.author.id}'
                await db.update(query)
                await asyncio.sleep(60)
                Profile.user_cd[msg.author.id] = 1
        except KeyError:
            Profile.user_cd[msg.author.id] = 1

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        old_nick = before.nick
        new_nick = after.nick
        if old_nick != new_nick:
            nick_update_query = f'UPDATE members SET nickname="{new_nick}" WHERE id={before.id}'
            await db.update(nick_update_query)

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(1)
        guild = self.client.get_guild(settings.GUILD_ID)
        for member in guild.members:
            Profile.user_cd[member.id] = 1

    @commands.command(case_insensitive=True)
    async def profile(self, ctx, member: typing.Optional[discord.Member]):
        target = member or ctx.author
        if not (await db.is_registered(target)):
            await ctx.send(f'{target.display_name} is not registered with the guild. Do ``k.register`` to register.')
            return
        query = f'SELECT rbx_name, plr_rank, credit, bio FROM members WHERE id={target.id}'
        result = await db.retrieve(query)
        name, rank_no, credit, bio = result
        rep_query = f'SELECT SUM(amount) FROM reps WHERE repped={target.id}'
        rep = (await db.retrieve(rep_query))[0]
        image_name = 'image' + str(self.name_count) + '.png'
        if self.name_count > 8:
            self.name_count = 0
        else:
            self.name_count += 1
        rank = ctx.guild.get_role(roles.RANK_ORDER[rank_no])
        cur_dir = os.getcwd()
        os.chdir(f'{settings.BOT_DIR}/cogs/assets/profile/image_cache')
        async with ctx.channel.typing():
            avatar_asset = target.avatar_url_as(format='png')
            await avatar_asset.save(f'{target.id}_avatar.jpg')
            os.chdir(cur_dir)
            avatar = f'{target.id}_avatar.jpg'
            await self.client.loop.run_in_executor(None, image.create_profile, avatar,
                                                   name, rank.name, str(rep), str(credit), bio, image_name)
            image_file = discord.File(f'{settings.BOT_DIR}/cogs/assets/profile/image_cache/{image_name}')
            await ctx.send(file=image_file)

    @commands.command()
    @commands.max_concurrency(1, commands.BucketType.user)
    async def setbio(self, ctx, *, bio: str = ' '):
        final_bio = bio
        if bio is None:
            await ctx.send(f'Enter your bio: ')

            def check(msg):
                return ctx.author == msg.author and ctx.channel == msg.channel
            try:
                reply = await self.client.wait_for('message', check=check, timeout=60)
                final_bio = reply.content
            except asyncio.TimeoutError:
                await ctx.send(f'{ctx.author.mention} You took too long to reply. Bio not updated.')
                return

        fixed_bio = final_bio.replace('"', '\\"')
        query = f'UPDATE members SET bio="{fixed_bio}" WHERE id={ctx.author.id}'
        r = await db.update(query)
        if r == 0:
            await ctx.send(f'{ctx.author.mention} Your bio has been change to:\n```{bio}``` ')
        else:
            await ctx.send(f'{ctx.author.mention} There was some problem updating your bio.')

    @commands.command()
    @commands.max_concurrency(1, commands.BucketType.user)
    async def give(self, ctx, target: discord.Member = None, amount=None):
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel
        receiver = target
        if target == ctx.author:
            await ctx.send(f'{ctx.author.mention} You can\'t give credits to yourself!!')
            return
        if target is None:
            await ctx.send(f'{ctx.author.mention}Who do you want to give credits?')
            try:
                reply = await self.client.wait_for('message', check=check, timeout=30)
                receiver = reply.mentions[0]
                if receiver == ctx.author:
                    await ctx.send(f'{ctx.author.mention} You can give credits to yourself!!')
                    return
            except asyncio.TimeoutError:
                await ctx.send(f'{ctx.author.mention} Took too long to reply.')
                return
            except ValueError:
                await ctx.send(f'{ctx.author.mention} You can only enter number values. Process stopped')
                return
            except IndexError:
                await ctx.send(f'{ctx.author.mention} You didn\'t mention anyone. Process stopped')
                return

        if not await db.is_registered(receiver):
            await ctx.send(f'{receiver.display_name} is not registered with guild.')
            return

        if amount is None:
            await ctx.send(f'{ctx.author.mention}How much do you want to give to {receiver.display_name}?')
            try:
                reply = await self.client.wait_for('message', check=check, timeout=30)
                new_amount = int(reply.content)
            except asyncio.TimeoutError:
                await ctx.send(f'{ctx.author.mention} Took too long to reply.')
                return
            except ValueError:
                await ctx.send(f'{ctx.author.mention} You can only enter number values. Process stopped')
                return
        elif int(amount) < 1:
            await ctx.send(f'{ctx.author.mention} Amount to be given can\'t be less than 1')
            return
        else:
            new_amount = int(amount)

        check_query = f'SELECT credit FROM members WHERE id={ctx.author.id}'
        result = await db.retrieve(check_query)
        if result[0] < new_amount:
            await ctx.send(f'{ctx.author.mention} You don\'t have enough '
                           f'credit.\nYour balance is ``{result[0]} credits``')
            return

        query1 = f'UPDATE members SET credit=credit-{new_amount} WHERE id={ctx.author.id}'
        query2 = f'UPDATE members SET credit=credit+{new_amount} WHERE id={receiver.id}'
        await db.update(query1, query2)
        await ctx.send(f'{ctx.author.mention} {new_amount} credits have been given to ``{receiver.display_name}``\n'
                       f'Your balance is ``{result[0]-new_amount} credits``')

    @commands.command()
    async def leaderboard(self, ctx, *, order_by='rank'):
        leaderboard_embed = discord.Embed(
            title=f'Guild Leaderboard',
            description=f'This leaderboard is in order of decreasing {order_by} for the top 10 members',
            color=discord.colour.Colour.green(),
            timestamp=datetime.datetime.now()
        )
        leaderboard_embed.set_footer(text=f'At')
        leaderboard_embed.set_thumbnail(url=ctx.guild.icon_url)
        if 'rank' in order_by:
            top_query = f'SELECT nickname, plr_rank FROM members ORDER BY plr_rank DESC, nickname LIMIT 10'
            top = await db.retrieve(top_query, size=0)
            for member in top:
                leaderboard_embed.add_field(name=f'{member[0]}', value=f'Rank - {member[1]}', inline=False)
            await ctx.send(embed=leaderboard_embed)
        elif 'credit' in order_by:
            top_query = f'SELECT nickname, credit FROM members ORDER BY credit DESC, nickname LIMIT 10'
            top = await db.retrieve(top_query, size=0)
            for member in top:
                leaderboard_embed.add_field(name=f'{member[0]}', value=f'Credits - {member[1]}', inline=False)
            await ctx.send(embed=leaderboard_embed)

    @commands.command()
    @commands.max_concurrency(1, commands.BucketType.user)
    async def rep(self, ctx, member: discord.Member = None, *, reason=None):
        def check(msg):
            return ctx.author == msg.author and ctx.channel == msg.channel
        target = member

        if member is None:
            await ctx.send(f'{ctx.author.mention} Who do you want to rep?')
            try:
                reply = await self.client.wait_for('message', check=check, timeout=30)
                target = reply.mentions[0]
            except asyncio.TimeoutError:
                await ctx.send(f'{ctx.author.mention} You took too long to reply. Process Cancelled')
                return
            except IndexError:
                await ctx.send(f'You need to mention the member. Process cancelled.')
                return
        if target == ctx.author:
            await ctx.send(f'{ctx.author.mention} BREH!! You can\'t rep yourself')
            return
        if not await db.is_registered(target):
            await ctx.send(f'{ctx.author.mention} {target.display_name} is not registered with the guild.')
            return
        final_reason = reason
        if reason is None:
            await ctx.send(f'{ctx.author.mention} Enter the reason for repping {target.display_name}')
            try:
                reply = await self.client.wait_for('message', check=check, timeout=30)
                final_reason = reply.content
            except asyncio.TimeoutError:
                await ctx.send(f'{ctx.author.mention} You took too long to reply. Process Cancelled')
                return
        final_reason = final_reason.replace('"', '\\"')

        repper = ctx.author
        repped = target
        date_of_rep = datetime.datetime.now().date().strftime('%Y/%m/%d')

        can_rep, message = await self.can_rep(repper, repped, date_of_rep)
        if can_rep:
            rep_query = f'INSERT INTO reps(repper, repped, reason, dor, amount) ' \
                        f'VALUES({repper.id}, {repped.id}, "{final_reason}", "{date_of_rep}", 1)'
            await db.update(rep_query)
            await ctx.send(f'{ctx.author.mention} just repped {target.display_name}!!\n**reason:** {final_reason}')
        else:
            await ctx.send(message)
            return

    @commands.command()
    @commands.max_concurrency(1, commands.BucketType.user)
    async def negrep(self, ctx, member: discord.Member = None, *, reason=None):
        def check(msg):
            return ctx.author == msg.author and ctx.channel == msg.channel

        target = member

        if member is None:
            await ctx.send(f'{ctx.author.mention} Who do you want to negative rep?')
            try:
                reply = await self.client.wait_for('message', check=check, timeout=30)
                target = reply.mentions[0]
            except asyncio.TimeoutError:
                await ctx.send(f'{ctx.author.mention} You took too long to reply. Process Cancelled')
                return
            except IndexError:
                await ctx.send(f'You need to mention the member. Process cancelled.')
                return
        if target == ctx.author:
            await ctx.send(f'{ctx.author.mention} BREH!! You why would you negative rep yourself!!')
            return
        if not await db.is_registered(target):
            await ctx.send(f'{ctx.author.mention} {target.display_name} is not registered with the guild.')
            return
        final_reason = reason
        if reason is None:
            await ctx.send(f'{ctx.author.mention} Enter the reason for negative repping {target.display_name}')
            try:
                reply = await self.client.wait_for('message', check=check, timeout=30)
                final_reason = reply.content
            except asyncio.TimeoutError:
                await ctx.send(f'{ctx.author.mention} You took too long to reply. Process Cancelled')
                return
        final_reason = final_reason.replace('"', '\\"')

        repper = ctx.author
        repped = target
        date_of_rep = datetime.datetime.now().date().strftime('%Y/%m/%d')

        can_rep, message = await self.can_rep(repper, repped, date_of_rep)
        if can_rep:
            rep_query = f'INSERT INTO reps(repper, repped, reason, dor, amount) ' \
                        f'VALUES({repper.id}, {repped.id}, "{final_reason}", "{date_of_rep}", -1)'
            await db.update(rep_query)
            await ctx.send(f'{ctx.author.mention} just negative repped {target.display_name}!!\n'
                           f'**reason:** {final_reason}')
        else:
            await ctx.send(message)
            return

    @commands.command(aliases=['swzp'])
    async def setworldzeroprofile(self, ctx):
        image_dir = f'{settings.BOT_DIR}/cogs/assets/profile/wz_profile_images'
        async with ctx.channel.typing():
            try:
                wz_screenshot = ctx.message.attachments[0]
                await wz_screenshot.save(f'{image_dir}/{ctx.author.id}_wz_profile.png')
                await ctx.send(f'{ctx.author.id} Successfully updated your world zero image in the database!')
            except IndexError:
                await ctx.send(f'{ctx.author.mention} Please upload the world zero screenshot')
                try:
                    reply = await self.client.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60)
                    wz_screenshot = reply.attachments[0]
                    if wz_screenshot is not None:
                        await wz_screenshot.save(f'{image_dir}/{ctx.author.id}_wz_profile.png')
                    await ctx.send(f'{ctx.author.mention} Successfully updated your world zero image in the database!')
                except asyncio.TimeoutError:
                    await ctx.send(f'{ctx.author.mention} You took too long to reply! Command cancelled!')
                    return
                except IndexError:
                    await ctx.send(f'{ctx.author.mention} Command Failed. You did not upload an image.')

    @commands.command(aliases=['gwzp'])
    async def getworldzeroprofile(self, ctx, member: discord.Member = None):
        image_dir = f'{settings.BOT_DIR}/cogs/assets/profile/wz_profile_images'
        async with ctx.channel.typing():
            try:
                if member is None:
                    image_file = discord.File(f'{image_dir}/{ctx.author.id}_wz_profile.png')
                    await ctx.send(file=image_file)
                else:
                    image_file = discord.File(f'{image_dir}/{member.id}_wz_profile.png')
                    await ctx.send(file=image_file)
            except FileNotFoundError:
                await ctx.send(f'{ctx.author.mention} Not Found! Upload your world zero screenshot '
                               f'using ``k.setworldzeroprofile``')
                return

    @commands.command(aliases=['requestpromote', 'rankrequest', 'requestrank'])
    async def promoterequest(self, ctx):
        if ctx.channel.id != settings.RANK_REQUEST_CHANNEL:
            await ctx.send(f'You can only request promotion in <#{settings.RANK_REQUEST_CHANNEL}>')
            return

        def check(msg):
            return ctx.author == msg.author and msg.channel == ctx.channel
        try:
            await ctx.send('Which rank do you want to request?')
            rank = await self.client.wait_for('message', check=check, timeout=30)
            rank_name = rank.content
            await ctx.send(f'Why apply for this rank? (Type the reason for your request)')
            reason = await self.client.wait_for('message', check=check, timeout=100)
            reason_text = reason.content
        except asyncio.TimeoutError:
            await ctx.send(f'{ctx.author.mention} You took too long to reply. Request process cancelled.')
            return
        desc = f'**Requester**: {ctx.author.mention}\n**Requested Rank**: {rank_name}'
        embed = discord.Embed(
            title=f'Rank-Up Request',
            description=desc,
            color=discord.colour.Colour.green()
        )
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.add_field(name="**Reason**", value=reason_text)

        request_redirect = ctx.guild.get_channel(settings.RANK_REQUEST_REDIRECT)
        await request_redirect.send(embed=embed)
        await ctx.send(f'{ctx.author.mention} Your request has been sent. The staff team will report back to you soon')


def setup(client):
    client.add_cog(Profile(client))
