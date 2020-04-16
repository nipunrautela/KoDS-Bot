import discord
import settings

import PIL
from PIL import Image, ImageDraw, ImageFont
import asyncio
import os

curdir = os.getcwd()
os.chdir(f'{settings.BOT_DIR}/cogs/assets/profile')

market = ImageFont.truetype(font='MarketingScript-Inline.ttf', size=100)
cs = ImageFont.truetype(font='ComicSansMSRegular.ttf', size=80)
os.chdir(curdir)


def create_profile(avatar_img: str, name: str, rank: str, rep: str, credit: str, bio, image_name):
    cur_dir = os.getcwd()
    os.chdir(f'{settings.BOT_DIR}/cogs/assets/profile')
    bg = Image.open('background.png')
    avatar = Image.open(f'image_cache/{avatar_img}')
    avatar = avatar.resize((230, 230))
    box = (1700, 40)
    bg.paste(avatar, box)
    os.remove(f'image_cache/{avatar_img}')
    font = ImageFont.truetype(font='ComicSansMSRegular.ttf', size=80)
    bio_font = ImageFont.truetype(font='ComicSansMSRegular.ttf', size=60)

    split_text = bio.split(" ")
    bio = ""
    count = 0
    for i in split_text:
        bio += i + ' '
        count += len(i) + 1
        if count > 30:
            bio += '\n'
            count = 0

    draw = ImageDraw.Draw(bg)
    draw.text((400, 320), name, font=font, fill=(0, 255, 0, 255))
    draw.text((400, 450), rank, font=font, fill=(0, 255, 0, 255))
    draw.text((400, 570), rep, font=font, fill=(0, 255, 0, 255))
    draw.text((400, 850), credit, font=font, fill=(0, 255, 0, 255))
    draw.multiline_text((980, 430), bio, font=bio_font, fill=(0, 255, 0, 255), align='center')

    image = bg.save(f'image_cache/{image_name}', "PNG")
    os.chdir(cur_dir)

    return 1


