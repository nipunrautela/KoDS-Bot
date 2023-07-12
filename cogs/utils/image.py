import discord
import settings

import PIL
from PIL import Image, ImageDraw, ImageFont
import asyncio
import os

market = ImageFont.truetype(font=f'{settings.BOT_DIR}/cogs/assets/profile/MarketingScript-Inline.ttf', size=100)
cs = ImageFont.truetype(font=f'{settings.BOT_DIR}/cogs/assets/profile/ComicSansMSRegular.ttf', size=80)


def create_profile(avatar_img: str, name: str, rank: str, rep: str, credit: str, bio, image_name):
    main_path = f"{settings.BOT_DIR}/cogs/assets/profile/"
    bg = Image.open(os.path.join(main_path, 'background.png'))
    avatar = Image.open(os.path.join(main_path, f'image_cache/{avatar_img}'))
    avatar = avatar.resize((230, 230))
    box = (1700, 40)
    bg.paste(avatar, box)
    if os.path.exists(os.path.join(main_path, f'image_cache/{avatar_img}')):
        os.remove(os.path.join(main_path, f'image_cache/{avatar_img}'))
    font = ImageFont.truetype(font=os.path.join(main_path, 'ComicSansMSRegular.ttf'), size=80)
    bio_font = ImageFont.truetype(font=os.path.join(main_path, 'ComicSansMSRegular.ttf'), size=60)

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

    bg.save(os.path.join(main_path, f'image_cache/{image_name}'), "PNG")

    return 1


