import datetime
import logging
import os

import pytz

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

import db_api
import errlogging

load_dotenv()

AUTHOR_ID = int(os.getenv('AUTHOR_ID'))


class TimeEmbedFactory:

    @staticmethod
    def simple_embed(user: discord.User, timezone: str) -> discord.Embed:
        tz = pytz.timezone(timezone)
        time = datetime.datetime.now(tz)
        e = discord.Embed()
        e.colour = discord.Colour.fuchsia()
        e.title = f"{user.display_name}'s time"
        e.set_thumbnail(url=user.display_avatar.url)
        e.add_field(name="Current time", value=time.strftime("**%H:%M:%S**"), inline=False)
        e.add_field(name="Current date", value=time.strftime("%d/%m/%Y"), inline=False)
        e.add_field(name="Timezone", value=time.strftime(f"{timezone}, UTC%z"))
        return e


# noinspection PyUnresolvedReferences
class Time(commands.GroupCog):

    def __init__(self, bot, handler):
        self.bot = bot
        self.handler = handler
        self.log = logging.Logger('TZ_CONVERT')
        self.log.addHandler(handler)
        self.db = db_api.DB_API()

    @staticmethod
    def has_permission(user: discord.User):
        return user.id == AUTHOR_ID

    @app_commands.command(name='set', description='Set your timezone')
    async def set_time(self, intr: discord.Interaction, timezone: str, user: discord.User = None):
        if user is not None:
            if not Time.has_permission(intr.user):
                await intr.response.send_message('No permission')
                return

        if user is None:
            user = intr.user

        if timezone not in pytz.all_timezones:
            await intr.response.send_message(
                'Error: invalid timezone!\nList of all valid timezones: https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568')
            return

        if self.db.add_user(user.id, timezone):
            await intr.response.send_message(f'Successfully set `@{user.name}`\'s timezone to {timezone}')
        else:
            await intr.response.send_message(f'Failed to set `@{user.name}`\'s timezone')

    @app_commands.command(name='get', description='Get a user\'s time')
    async def get_time(self, intr: discord.Interaction, user: discord.User = None):
        if user is None:
            user = intr.user

        tz_str = self.db.get_user_timezone(user.id)

        if tz_str is None:
            await intr.response.send_message(f'User `@{user.name}` has not set their timezone yet')
            return

        await intr.response.send_message(embed=TimeEmbedFactory.simple_embed(user, tz_str))

    @classmethod
    def setup(cls, bot: commands.Bot, handler: logging.Handler):
        return cls(bot, handler)
