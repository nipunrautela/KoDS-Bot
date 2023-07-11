import discord
from discord.ext import commands
from .utils import paginator, db, emojis
import settings

import asyncio
from datetime import datetime


class Shop(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.tax = 0.9

    async def add_item(self, data: list):
        query = f'INSERT INTO items(item_code, item_name, price, type, description, quantity, category, on_order) ' \
                f'VALUES("{data[0]}", "{data[1]}", {data[2]}, "{data[3]}", ' \
                f'"{data[4]}", "{data[5]}", "{data[6]}", {data[7]})'
        await db.update(query)

    async def cog_check(self, ctx):
        if not (await db.is_registered(ctx.author)):
            await ctx.send(f'You are not registered with the guild! Do ``k.register`` to register')
        return await db.is_registered(ctx.author)

    @commands.group(invoke_without_command=True)
    @commands.max_concurrency(1, commands.BucketType.user, wait=False)
    async def shop(self, ctx):
        items_query = f'SELECT item_code, item_name, price, type, description, quantity, category, on_order FROM items'\
                      f' WHERE quantity>0'
        data_set = await db.retrieve(items_query, 0)
        complete_data = []
        count = 0
        for data in data_set:
            item_dict = dict()
            count += 1
            item_dict['i'] = count
            item_dict['name'] = data[1]
            desc = f'-  Item Code: {data[0]}\n-  Price: {data[2]}\n-  Remaining: {data[5]}'
            item_dict['value'] = desc
            info = {
                'code': data[0],
                'name': data[1],
                'price': data[2],
                'type': data[3],
                'description': data[4],
                'quantity': data[5],
                'category': data[6],
                'on_order': data[7]
            }
            item_dict['info'] = info
            complete_data.append(item_dict)

        shop = paginator.Paginator(self.client, ctx, complete_data)
        await shop.paginate_shop()

    @shop.command()
    async def order(self, ctx, *, item=None):
        if item is None:
            await ctx.send(f'{ctx.author.mention} You need to type the name of the item to order. '
                           f'``k.shop order [name of item]``')
            return
        find_item_query = f'SELECT item_code, item_name, price, type, quantity, category, on_order FROM items '\
                          f'WHERE (item_name LIKE "%{item}%" OR item_code LIKE "%{item}%") AND quantity>0'
        found_items = await db.retrieve(find_item_query, 0)
        if len(found_items) == 0:
            await ctx.send(f'{ctx.author.mention} Item not found or Out of Stock!')
        elif len(found_items) == 1:
            item = found_items[0]
            money_check_query = f'SELECT credit FROM members WHERE id={ctx.author.id}'
            money = await db.retrieve(money_check_query)
            if money[0] < item[2]:
                await ctx.send(f'{ctx.author.mention} You don\'t have enough money to order this product')
                return
            if item[4] < 1:
                await ctx.send(f'{ctx.author.mention} Sorry. The item(``{item[1]}``) is currently out of stock')
                return
            found_msg = f'Name: `{item[1]}`\nCode: `{item[0]}`\nPrice: `{item[2]}`\nRemaining: `{item[4]}`'
            embed = discord.Embed(
                title='__Item Found:__',
                description=f'React with {emojis.CHECK_MARK_BUTTON} to Buy\n{found_msg}',
                color=discord.colour.Colour.green()
            )
            item_found_msg = await ctx.send(embed=embed)

            def check(r, u):
                return r.emoji in (emojis.CHECK_MARK_BUTTON, emojis.CROSS_MARK_BUTTON) and u == ctx.author
            try:
                await item_found_msg.add_reaction(emojis.CHECK_MARK_BUTTON)
                await item_found_msg.add_reaction(emojis.CROSS_MARK_BUTTON)
                reaction, user = await self.client.wait_for('reaction_add', check=check, timeout=30)
                now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                if reaction.emoji == emojis.CHECK_MARK_BUTTON:
                    if item[6]:  # on order items
                        buy_query = f'UPDATE members SET credit=credit-{item[2]} WHERE id={ctx.author.id}'
                        order_query = f'INSERT INTO orders(user_id, item_code, date, status) ' \
                                      f'VALUES({ctx.author.id}, "{item[0]}", "{now}", "PENDING")'
                        item_query = f'UPDATE items SET quantity=quantity-1 WHERE item_code="{item[0]}"'
                        await db.update(buy_query, order_query, item_query)
                        order_no_query = f'SELECT order_no FROM orders WHERE user_id={ctx.author.id} AND date="{now}"'
                        order_no = (await db.retrieve(order_no_query))[0]
                        order_desc = f'__Order Info:__\n\n```Order No: {order_no}\nItem Code: {item[0]}\n' \
                                     f'Item Name: {item[1]}\n```'
                        order_embed = discord.Embed(
                            title='Order Placed',
                            description=f'{order_desc}',
                            timestamp=datetime.now().astimezone()
                        )
                        order_embed.set_thumbnail(url=ctx.author.avatar_url)
                        order_embed.set_footer(text='Ordered At: ')
                        await ctx.send(f'{ctx.author.mention} You order had been placed.', embed=order_embed)
                        order_receive_embed = discord.Embed(
                            title='New Order',
                            timestamp=datetime.now().astimezone()
                        )
                        order_receive_embed.set_thumbnail(url=ctx.author.avatar_url)
                        order_receive_embed.add_field(name='Order No', value=f'{order_no}')
                        order_receive_embed.add_field(name='Item Code', value=f'{item[0]}')
                        order_receive_embed.add_field(name='Item Name', value=f'{item[1]}')
                        order_receive_embed.add_field(name='Order Date/Time',
                                                      value=f'{now}')
                        order_receive_embed.add_field(name='Placed By', value=f'{ctx.author.mention}')
                        await ctx.guild.get_channel(settings.ORDER_CHANEL).send(embed=order_receive_embed)
                    else:
                        buy_query = f'UPDATE members SET credit=credit-{item[2]} WHERE id={ctx.author.id}'
                        inventory_query = f'INSERT INTO inventory(id, item_code) VALUES({ctx.author.id}, {item[0]})'
                        item_query = f'UPDATE items SET quantity=quantity-1 WHERE item_code="{item[0]}"'
                        await db.update(buy_query, inventory_query, item_query)
                        order_no_query = f'SELECT order_no FROM orders WHERE id={ctx.author.id} AND date={now}'
                        order_no = (await db.retrieve(order_no_query))[0]
                        bought_desc = f'__Item Info:__\n\n```Order No: {order_no}\nItem Code: {item[0]}\n' \
                                      f'Item Name: {item[1]}```'
                        bought_embed = discord.Embed(
                            title='Item Purchased',
                            description=f'{bought_desc}',
                            timestamp=datetime.now().astimezone()
                        )
                        bought_embed.set_footer(text='Purchased At: ')
                        await ctx.send(f'{ctx.author.mention} Purchase Successful!', embed=bought_embed)
                elif reaction.emoji == emojis.CROSS_MARK_BUTTON:
                    await ctx.send(f'{ctx.author.mention} Purchase Cancelled! {emojis.THUMBS_UP}')
                    return
            except asyncio.TimeoutError:
                await ctx.send(f'{ctx.author.mention} You took too long to react. Purchase Cancelled!')
                return
        elif len(found_items) > 1:
            name_of_found = []
            for item in found_items:
                name_of_found.append(item[1])
            multiple_items = f'Multiple Items Found:\n'
            for name in name_of_found:
                multiple_items += f'{name}\n'
            multiple_items += f'\nDo ``k.shop order [item name]`` to order an item'
            await ctx.send(multiple_items)

    @shop.command()
    async def cancelorder(self, ctx, order_no=None):
        order_number = order_no
        if order_no is None:
            def check(msg):
                return msg.author == ctx.author and msg.channel == ctx.channel
            try:
                await ctx.send(f'{ctx.author.mention} Enter the order number')
                order = await self.client.wait_for('message', check=check, timeout=30)
                order_number = order.content
            except asyncio.TimeoutError:
                await ctx.send(f'{ctx.author.mention} Took too long to reply. Order not cancelled')

        info_query = f'SELECT orders.item_code, orders.date, items.item_name, items.price FROM orders JOIN items ' \
                     f'WHERE orders.user_id={ctx.author.id} AND orders.item_code=items.item_code ' \
                     f'AND orders.order_no={order_number} AND orders.status="PENDING"'
        order_info = await db.retrieve(info_query)
        if order_info is None:
            await ctx.send(f'{ctx.author.mention} You do not have a pending order with order number {order_number}!')
            return
        order_cancel_query = f'UPDATE orders SET status="CANCELLED" ' \
                             f'WHERE order_no={order_number} AND user_id={ctx.author.id}'
        refund_amount = self.tax * order_info[3]
        refund_query = f'UPDATE members SET credit=credit+{refund_amount} WHERE id={ctx.author.id}'
        await db.update(order_cancel_query, refund_query)
        order_embed = discord.Embed(
            title='Order Cancelled',
            description=f'',
            timestamp=order_info[1],
            color=discord.colour.Colour.red()
        )
        order_embed.set_thumbnail(url=ctx.author.avatar_url)
        order_embed.set_footer(text='Ordered At: ')
        order_embed.add_field(name=f'Order No', value=f'{order_number}')
        order_embed.add_field(name=f'Item Code', value=f'{order_info[0]}')
        order_embed.add_field(name=f'Item Name', value=f'{order_info[2]}')
        order_embed.add_field(name=f'Refunded', value=f'{refund_amount} Credits')
        order_embed.add_field(name=f'Ordered By', value=f'{ctx.author.mention}')
        await ctx.send(f'{ctx.author.mention} You order had been cancelled.', embed=order_embed)
        await ctx.guild.get_channel(settings.ORDER_CHANEL).send(embed=order_embed)

    @shop.command()
    @commands.is_owner()
    async def completeorder(self, ctx, order_no):
        order_info_query = f'SELECT user_id, item_code, date FROM orders WHERE order_no={order_no} AND status="PENDING"'
        order_info = await db.retrieve(order_info_query)
        if order_info is None:
            await ctx.send(f'{ctx.author.mention} No pending order with order number {order_no} found!!')
            return
        item_info_query = f'SELECT item_name, price, type, category FROM items WHERE item_code="{order_info[1]}"'
        item_info = await db.retrieve(item_info_query)

        verify_embed = discord.Embed(
            title=f'Order Completion Confirmation',
            description=f'Is your following order complete?\nReact with {emojis.CHECK_MARK_BUTTON} if complete',
            color=discord.colour.Colour.teal(),
            timestamp=datetime.utcnow()
        )
        verify_embed.add_field(name=f'Order Number', value=f'{order_no}')
        verify_embed.add_field(name=f'Item Code', value=f'{order_info[1]}')
        verify_embed.add_field(name=f'Item Name', value=f'{item_info[0]}')
        verify_embed.add_field(name=f'Price', value=f'{item_info[1]}')
        verify_embed.add_field(name=f'Item Type', value=f'{item_info[2]}')
        verify_embed.add_field(name=f'Item Category', value=f'{item_info[3]}')
        verify_embed.add_field(name=f'Ordered On', value=f'{order_info[2]}')
        try:
            confirmation = await ctx.guild.get_member(order_info[0]).send(embed=verify_embed)
            await ctx.send(f'{ctx.author.mention} Member has been sent confirmation. Order No-{order_no}')
        except discord.errors.Forbidden:
            confirmation = await ctx.guild.get_channel(settings.RANK_REQUEST_CHANNEL).send(embed=verify_embed)
        await confirmation.add_reaction(emojis.CHECK_MARK_BUTTON)
        await confirmation.add_reaction(emojis.CROSS_MARK_BUTTON)

        def check(r, u):
            return ctx.author == u and r.emoji in [emojis.CHECK_MARK_BUTTON, emojis.CROSS_MARK_BUTTON]
        try:
            reaction, user = await self.client.wait_for('reaction_add', check=check, timeout=30)
            if reaction.emoji == emojis.CHECK_MARK_BUTTON:
                await confirmation.channel.send(f'<@{order_info[0]}> Order completed')
            else:
                await confirmation.channel.send(f'<@{order_info[0]}> Confirmation has been rejected')
                await ctx.send(f'{ctx.author.mention} The confirmation was rejected by the member. Order No-{order_no}')
                return
        except asyncio.TimeoutError:
            await confirmation.channel.send(f'<@{order_info[0]}> You took too long to react! Your order has been '
                                            f'marked ``completed``! Contact Arcane#0033 if you have any queries.')

        mark_complete_query = f'UPDATE orders SET status="COMPLETED" WHERE order_no={order_no}'
        await db.update(mark_complete_query)
        await ctx.send(f'{ctx.author.mention} The order confirmation had been completed.')

    @shop.command()
    async def myorders(self, ctx, *, status='PENDING'):
        order_query = f'SELECT orders.order_no, orders.user_id, orders.item_code, orders.date, items.item_name ' \
                      f'FROM orders JOIN items ' \
                      f'WHERE orders.status="{status}" AND orders.user_id={ctx.author.id} ' \
                      f'AND items.item_code=orders.item_code'
        data_set = await db.retrieve(order_query, 0)
        if len(data_set) == 0:
            await ctx.send(f'You have no pending orders.')
            return
        complete_data = []
        count = 0
        for data in data_set:
            item_dict = dict()
            count += 1
            item_dict['i'] = count
            item_dict['name'] = f'{data[4]}'
            desc = f'Item Code: {data[2]}'
            item_dict['value'] = desc
            item_dict['timestamp'] = data[3]
            item_dict['ts_data'] = 'Ordered on'
            info = {
                'Order No': data[0],
                'Placed By': f'<@{data[1]}>',
                'Item Code': data[2],
                'Status': status
            }
            item_dict['info'] = info
            complete_data.append(item_dict)

        shop = paginator.Paginator(self.client, ctx, complete_data)
        await shop.paginate()

    @shop.command()
    @commands.is_owner()
    async def additem(self, ctx):
        info_req = [
            f'{ctx.author.mention} Enter the Item Code',
            f'{ctx.author.mention} Enter the Item Name',
            f'{ctx.author.mention} Enter the Item Price',
            f'{ctx.author.mention} Enter the Item Type',
            f'{ctx.author.mention} Enter the Item Description',
            f'{ctx.author.mention} Enter the Item Quantity',
            f'{ctx.author.mention} Enter the Item Category',
            f'{ctx.author.mention} Is the item On Order?'
        ]
        data = []

        def msg_check(msg):
            return ctx.author == msg.author and ctx.channel == msg.channel
        try:
            for i in range(8):
                await ctx.send(info_req[i])
                reply = await self.client.wait_for('message', check=msg_check, timeout=60)
                data.append(reply.content)
                continue
        except asyncio.TimeoutError:
            await ctx.send(f'{ctx.author.mention} You took too long to reply. Item not added.')
            return

        await self.add_item(data)
        await ctx.send(f'{ctx.author.mention} Item added.\nName: {data[1]}\nCode: {data[0]}\nPrice: {data[2]}')

    @commands.command()
    @commands.is_owner()
    async def orders(self, ctx, *, status='PENDING'):
        order_query = f'SELECT order_no, user_id, item_code, date FROM orders ' \
                      f'WHERE status="{status}"'
        data_set = await db.retrieve(order_query, 0)
        complete_data = []
        count = 0
        for data in data_set:
            item_dict = dict()
            count += 1
            item_dict['i'] = count
            item_dict['name'] = f'{ctx.guild.get_member(data[1]).display_name}'
            desc = f'Item Code: {data[2]}'
            item_dict['value'] = desc
            item_dict['timestamp'] = data[3]
            item_dict['ts_data'] = 'Ordered on'
            info = {
                'Order No': data[0],
                'Placed By': f'<@{data[1]}>',
                'Item Code': data[2],
                'Status': status
            }
            item_dict['info'] = info
            complete_data.append(item_dict)

        shop = paginator.Paginator(self.client, ctx, complete_data)
        await shop.paginate()

    @commands.command()
    async def iteminfo(self, ctx, *, item=None):
        if item is None:
            await ctx.send(f'{ctx.author.mention} Missing item name/code. Usage: ``k.iteminfo [name/code of item]``')
            return

        single_info_query = f'SELECT item_code, item_name, price, type, description, quantity, category, on_order ' \
                            f'  FROM items WHERE item_name LIKE "{item}" OR item_code LIKE "{item}"'
        single_item_found = await db.retrieve(single_info_query)
        if single_item_found:
            item_info = single_item_found
            info_embed = discord.Embed(
                title=f'',
                description=f'{item_info[4]}',
                color=discord.colour.Colour.green()
            )
            info_embed.set_author(name=f'{item_info[1]}')
            info_embed.set_thumbnail(url=ctx.guild.icon_url)
            info_embed.add_field(name=f'Item Code', value=f'{item_info[0]}')
            info_embed.add_field(name=f'Price', value=f'{item_info[2]} credits')
            info_embed.add_field(name=f'Quantity', value=f'{item_info[5]}')
            info_embed.add_field(name=f'Type', value=f'{item_info[3]}')
            info_embed.add_field(name=f'Category', value=f'{item_info[6]}')
            info_embed.add_field(name=f'On Order', value=f'{bool(item_info[7])}')
            await ctx.send(embed=info_embed)
            return

        info_query = f'SELECT item_code, item_name, price, type, description, quantity, category, on_order FROM items '\
                     f'WHERE item_name LIKE "%{item}%" OR item_code LIKE "%{item}%"'
        found_items = await db.retrieve(info_query, 0)
        if len(found_items) == 0:
            await ctx.send(f'{ctx.author.mention} No item found!')
            return
        elif len(found_items) == 1:
            item_info = found_items[0]
            info_embed = discord.Embed(
                title=f'',
                description=f'{item_info[4]}',
                color=discord.colour.Colour.green()
            )
            info_embed.set_author(name=f'{item_info[1]}')
            info_embed.set_thumbnail(url=ctx.guild.icon_url)
            info_embed.add_field(name=f'Item Code', value=f'{item_info[0]}')
            info_embed.add_field(name=f'Price', value=f'{item_info[2]} credits')
            info_embed.add_field(name=f'Quantity', value=f'{item_info[5]}')
            info_embed.add_field(name=f'Type', value=f'{item_info[3]}')
            info_embed.add_field(name=f'Category', value=f'{item_info[6]}')
            info_embed.add_field(name=f'On Order', value=f'{bool(item_info[7])}')
            await ctx.send(embed=info_embed)
        elif len(found_items) > 1:
            name_of_found = []
            for item in found_items:
                name_of_found.append(item[1])
            multiple_items = f'Multiple Items Found:\n'
            for name in name_of_found:
                multiple_items += f'{name}\n'
            multiple_items += f'\nDo ``k.iteminfo [item name]`` to get info of an item'
            await ctx.send(multiple_items)


async def setup(client):
    await client.add_cog(Shop(client))
