import logging
import os
import sys

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

import cog_tz
import errlogging

logger = logging.Logger('General Log')
load_dotenv()
TOKEN = os.getenv('TOKEN')
AUTHOR_ID = int(os.getenv('AUTHOR_ID'))

handler = logging.StreamHandler()
logger.addHandler(handler)

bot = commands.Bot('!', intents=discord.Intents.all())
tree = bot.tree


@bot.event
async def on_message(msg: discord.Message):
    # Special command to sync messages
    if msg.content == '/sync_tz' and msg.author.id == AUTHOR_ID:
        print('syncing')
        await msg.reply('Syncing...', delete_after=3)
        synced = await tree.sync()
        print('synced')
        await msg.reply('Synced!', delete_after=3)

        for cmd in synced:
            print(cmd.name)


async def reload_cogs():
    if bot.get_cog('Time') is None:
        cog = cog_tz.Time.setup(bot, handler)
        print(f'adding cog {cog.__cog_name__}')
        await bot.add_cog(cog)


@bot.event
async def on_resume():
    await reload_cogs()


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(name='startup...', type=discord.ActivityType.playing),
                              status=discord.Status.dnd)

    errlogging.generate_errlog_folder()
    await reload_cogs()

    await bot.change_presence(activity=discord.Activity(name='time go by.', type=discord.ActivityType.watching))


@bot.event
async def on_error(event, *args, **kwargs):
    logger.error('An error has occurred! Check the latest ERRLOG for more info')
    errlogging.new_errlog(sys.exc_info()[1])

bot.run(token=TOKEN, log_handler=handler)
