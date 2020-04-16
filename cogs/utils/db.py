import discord

import aiomysql
import asyncio
import datetime
import typing


async def update(*query):
    loop = asyncio.get_event_loop()

    conn = await aiomysql.connect(host='localhost', port=3306,
                                  user='root', password='nipun1209',
                                  db='kods', loop=loop)

    async with conn.cursor() as cur:
        for q in query:
            await cur.execute(q)
        await conn.commit()
        conn.close()
        return 0


async def retrieve(query: str, size: int = 1):
    loop = asyncio.get_event_loop()
    conn = await aiomysql.connect(host='localhost', port=3306,
                                  user='root', password='nipun1209',
                                  db='kods', loop=loop)

    async with conn.cursor() as cur:
        await cur.execute(query)    
        if size == 0:
            result = await cur.fetchall()
        elif size == 1:
            result = await cur.fetchone()
        else:
            result = await cur.fetchmany(size)
        conn.close()
        return result


async def row_count(query: str):
    loop = asyncio.get_event_loop()
    conn = await aiomysql.connect(host='localhost', port=3306,
                                  user='root', password='nipun1209',
                                  db='kods', loop=loop)

    async with conn.cursor() as cur:
        await cur.execute(query)
        result = cur.rowcount
        conn.close()
        return result


async def register_member(member: discord.Member, rbx_name: str):
    user_id = member.id
    query = f'INSERT INTO members(id, rbx_name, credit, bio) VALUES({user_id}, "{rbx_name}", 200, "No Bio")'
    r = await update(query)
    return r


async def unregister_member(member: discord.Member):
    user_id = member.id
    query1 = f'DELETE FROM members WHERE id={user_id}'
    query2 = f'DELETE FROM reps WHERE repped={user_id}'
    r = await update(query1, query2)
    return r


async def is_registered(member: discord.Member):
    user_id = member.id
    query = f'SELECT * FROM members WHERE id={user_id}'
    row_num = await row_count(query)
    if row_num > 0:
        return True
    else:
        return False


async def found(query):
    row_num = await row_count(query)
    if row_num > 0:
        return True
    else:
        return False