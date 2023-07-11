import discord
from . import emojis

import asyncio
from datetime import datetime

number_reactions = [
    emojis.KEYCAP_1,
    emojis.KEYCAP_2,
    emojis.KEYCAP_3,
    emojis.KEYCAP_4,
    emojis.KEYCAP_5,
    emojis.KEYCAP_6,
]


class Paginator:

    def __init__(self, client, ctx, data: list):
        self.client = client
        self.ctx = ctx
        self.data = data
        self.pages = []
        self.cur_page = 0
        self.create_pages()

    def create_pages(self):
        count = 0
        page = []
        for item in self.data:
            page.append(item)
            count += 1
            if count > 5:
                self.pages.append(page)
                page = []
                count = 0
        self.pages.append(page)

    def check(self, reaction, user):
        return self.ctx.author == user

    def basic_embed(self, item=None):
        time = datetime.now().astimezone()
        if item:
            time = item['timestamp']
        basic_embed = discord.Embed(
            title=f'{str(self.ctx.command.name).upper()}',
            description=f'',
            color=discord.colour.Colour.purple(),
            timestamp=time
        )
        basic_embed.set_thumbnail(url=self.ctx.guild.icon_url)
        basic_embed.set_footer(text=f'Page {self.cur_page+1}/{len(self.pages)} |')
        if item is None:
            i = 0
            page = self.pages[self.cur_page]
            for item in page:
                basic_embed.add_field(name=f"{item['i']}) **{item['name']}** {number_reactions[i]}",
                                      value=f"{item['value']}", inline=False)
                i += 1
        else:
            basic_embed.set_footer(text=f'Page {self.cur_page + 1}/{len(self.pages)} | {item["ts_data"]}')
            for key in item['info']:
                basic_embed.add_field(name=f"__**{key}**__", value=item['info'][key], inline=False)

        return basic_embed

    def shop_embed(self, data=None):
        shop_embed = discord.Embed(
            title='KODS GUILD SHOP',
            description=f'Do ``k.shop order [item code]`` to order/buy items.\n'
                        f'The Items can be purchased using credits. To check your credit do ``k.profile``\n',
            color=discord.colour.Colour.orange(),
            timestamp=datetime.now().astimezone()
        )
        shop_embed.set_thumbnail(url=self.ctx.guild.icon.url)
        shop_embed.set_footer(text=f'Page {self.cur_page+1}/{len(self.pages)} |')
        if data is None:
            i = 0
            page = self.pages[self.cur_page]
            for item in page:
                shop_embed.add_field(name=f"{item['i']}) **{item['name']}** {number_reactions[i]}",
                                     value=f"{item['value']}", inline=False)
                i += 1
        else:
            item = data['info']
            field_value = f"\n{item['description']}\n\n**Item Code:** {item['code']}\n**Price:** {item['price']}\n" \
                          f"**Remaining:** {item['quantity']}\n**Type:** {item['type']}\n" \
                          f"**Category:** {item['category']}\n**On Order:** {bool(item['on_order'])}"
            shop_embed.add_field(name=f"__**{item['name']}**__", value=field_value, inline=False)

        return shop_embed

    def empty_embed(self):
        empty_embed = discord.Embed(
            title='KODS GUILD SHOP',
            description=f'Nothing to See here!',
            color=discord.colour.Colour.dark_blue(),
        )
        empty_embed.set_thumbnail(url=self.ctx.guild.icon.url)
        return empty_embed

    async def paginate_shop(self):
        msg = await self.ctx.send('...Opening')
        close_embed = discord.Embed(
            title='Shop Closed...',
            description='To open shop type ``k.shop``',
            color=discord.colour.Colour.red()
        )
        await msg.add_reaction(emojis.CROSS_MARK)
        await msg.add_reaction(emojis.LEFT_ARROW)
        await msg.add_reaction(emojis.RIGHT_ARROW)
        try:
            for r in range(len(self.pages[self.cur_page])):
                await msg.add_reaction(number_reactions[r])
        except IndexError:
            pass
        await msg.edit(content=' ', embed=self.shop_embed())
        try:
            while True:

                reaction, user = await self.client.wait_for('reaction_add', check=self.check, timeout=60)
                await msg.remove_reaction(reaction.emoji, self.ctx.author)
                if reaction.emoji == emojis.RIGHT_ARROW:
                    await self.next_page(msg, self.shop_embed)
                elif reaction.emoji == emojis.LEFT_ARROW:
                    await self.prev_page(msg, self.shop_embed)
                elif reaction.emoji == emojis.CROSS_MARK:
                    raise asyncio.TimeoutError
                elif reaction.emoji in number_reactions:
                    await msg.remove_reaction(reaction.emoji, self.ctx.author)
                    idx = number_reactions.index(reaction.emoji)
                    await self.item_data(msg, self.pages[self.cur_page][idx], self.shop_embed)
                elif reaction.emoji == emojis.RIGHT_ARROW_CURVING_LEFT:
                    await msg.remove_reaction(emojis.RIGHT_ARROW_CURVING_LEFT, self.ctx.author)
                    await msg.remove_reaction(emojis.RIGHT_ARROW_CURVING_LEFT, msg.author)
                    await self.current_page(msg, self.shop_embed)
                else:
                    continue

        except asyncio.TimeoutError:
            await msg.clear_reactions()
            await msg.edit(embed=close_embed)
            return

    async def paginate(self):
        msg = await self.ctx.send('...Opening')
        close_embed = discord.Embed(
            title='Page Closed...',
            description='',
            color=discord.colour.Colour.red()
        )
        await msg.add_reaction(emojis.CROSS_MARK)
        await msg.add_reaction(emojis.LEFT_ARROW)
        await msg.add_reaction(emojis.RIGHT_ARROW)
        try:
            for r in range(len(self.pages[self.cur_page])):
                await msg.add_reaction(number_reactions[r])
        except IndexError:
            pass
        await msg.edit(content=' ', embed=self.basic_embed())
        try:
            while True:

                reaction, user = await self.client.wait_for('reaction_add', check=self.check, timeout=40)
                await msg.remove_reaction(reaction.emoji, self.ctx.author)
                if reaction.emoji == emojis.RIGHT_ARROW:
                    await self.next_page(msg, self.basic_embed)
                elif reaction.emoji == emojis.LEFT_ARROW:
                    await self.prev_page(msg, self.basic_embed)
                elif reaction.emoji in number_reactions:
                    await msg.remove_reaction(reaction.emoji, self.ctx.author)
                    idx = number_reactions.index(reaction.emoji)
                    try:
                        await self.item_data(msg, self.pages[self.cur_page][idx], self.basic_embed)
                    except IndexError:
                        await msg.edit(embed=self.empty_embed())
                elif reaction.emoji == emojis.RIGHT_ARROW_CURVING_LEFT:
                    await msg.remove_reaction(emojis.RIGHT_ARROW_CURVING_LEFT, self.ctx.author)
                    await msg.remove_reaction(emojis.RIGHT_ARROW_CURVING_LEFT, msg.author)
                    await self.current_page(msg, self.basic_embed)
                elif reaction.emoji == emojis.CROSS_MARK:
                    raise asyncio.TimeoutError

        except asyncio.TimeoutError:
            await msg.clear_reactions()
            await msg.edit(embed=close_embed)
            return

    async def current_page(self, msg, display_embed):
        try:
            await msg.edit(embed=display_embed())
        except IndexError:
            await msg.edit(embed=self.empty_embed())

    async def next_page(self, msg, display_embed):
        try:
            self.cur_page += 1
            await msg.edit(embed=display_embed())
        except IndexError:
            self.cur_page -= 1
            await msg.edit(embed=self.empty_embed())

    async def prev_page(self, msg, display_embed):
        try:
            self.cur_page -= 1
            await msg.edit(embed=display_embed())
        except IndexError:
            self.cur_page += 1
            await msg.edit(embed=self.empty_embed())

    async def item_data(self, msg, item, display_embed):
        try:
            await msg.add_reaction(emojis.RIGHT_ARROW_CURVING_LEFT)
            await msg.edit(embed=display_embed(item))
        except IndexError:
            await msg.edit(embed=self.empty_embed())
