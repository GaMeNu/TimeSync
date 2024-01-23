import time
import datetime as dt
from datetime import datetime
import logging
import os

import pytz

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

import db_api

load_dotenv()

AUTHOR_ID = int(os.getenv('AUTHOR_ID'))


class TimeEmbedFactory:

    @staticmethod
    def simple_embed(user: discord.User, timezone: str) -> discord.Embed:
        tz = pytz.timezone(timezone)
        time = datetime.now(tz)

        e = discord.Embed()
        e.colour = discord.Colour.fuchsia()
        e.title = f"{user.display_name}'s time"
        e.set_thumbnail(url=user.display_avatar.url)

        e.add_field(name="Current time", value=time.strftime("**%H:%M:%S**"), inline=False)
        e.add_field(name="Current date", value=time.strftime("%d/%m/%Y"), inline=False)
        e.add_field(name="Timezone", value=time.strftime(f"{timezone}, UTC%z"))

        return e

    @staticmethod
    def convert_embed(datetime1: datetime, datetime2: datetime):

        diff_h = int((datetime2.utcoffset() - datetime1.utcoffset()).total_seconds() // 3600)

        e = discord.Embed()
        e.colour = discord.Colour.fuchsia()
        e.title = f"Time conversion"

        e.add_field(name="Converted Time", value=datetime2.strftime("**%H:%M:%S**\n**%d/%m/%Y**"), inline=True)
        e.add_field(name="Converted Timezone", value=str(datetime2.tzinfo) + ', ' + datetime2.strftime("UTC%z"), inline=True)

        e.add_field(name="", value="", inline=False)

        e.add_field(name="Original Time", value=datetime1.strftime("%H:%M:%S**\n**%d/%m/%Y"), inline=True)
        e.add_field(name="Original Timezone", value=str(datetime1.tzinfo) + ', ' + datetime1.strftime("UTC%z"), inline=True)

        e.add_field(name="", value="", inline=False)

        e.add_field(name="Time difference", value=f'{diff_h} hours', inline=True)
        e.add_field(name="Unix timestamp", value=datetime1.timestamp())

        return e


# noinspection PyUnresolvedReferences
class Time(commands.GroupCog):

    def __init__(self, bot, handler):
        self.bot = bot
        self.handler = handler
        self.log = logging.Logger('TIME')
        self.log.addHandler(handler)
        self.db = db_api.DB_API()

    @staticmethod
    def has_permission(user: discord.User):
        return user.id == AUTHOR_ID

    @app_commands.command(name='list', description='List all valid timezones')
    async def time_list(self, intr: discord.Interaction):
        intr.response.send_message('List of all valid timezones: https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568')

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

    @app_commands.command(name='convert', description='Convert a time from one timezone to another')
    @app_commands.describe(time='Format: HH:MM:SS',
                           date='Format: YYYY-MM-DD')
    async def time_convert(self, intr: discord.Interaction, timezone1: str, timezone2: str, time: str = None, date: str = None):

        if timezone1 not in pytz.all_timezones:
            await intr.response.send_message(f'Invalid timezone: "{timezone1}"\nFor a list of all valid timezones use /time list')
            return

        if timezone2 not in pytz.all_timezones:
            await intr.response.send_message(f'Invalid timezone: "{timezone2}"\nFor a list of all valid timezones use /time list')
            return

        await intr.response.defer()

        tz1 = pytz.timezone(timezone1)
        tz2 = pytz.timezone(timezone2)

        if time is not None:
            try:
                time_obj = datetime.strptime(time, "%H:%M:%S")
            except ValueError:
                await intr.followup.send('Error: failed to convert time')
                return
        else:
            time_obj = datetime.now(tz1)

        if date is not None:
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                await intr.followup.send('Error: failed to convert date')
                return
        else:
            date_obj = datetime.now(tz1)

        datetime1 = datetime.now(tz1).replace(
            year=date_obj.year,
            month=date_obj.month,
            day=date_obj.day,
            hour=time_obj.hour,
            minute=time_obj.minute,
            second=time_obj.second
        )

        try:
            datetime2 = datetime1.astimezone(tz2)
        except OverflowError:
            await intr.followup.send('Error: Failed to calculate date difference')
            return

        await intr.followup.send(embed=TimeEmbedFactory.convert_embed(datetime1, datetime2))


    @classmethod
    def setup(cls, bot: commands.Bot, handler: logging.Handler):
        return cls(bot, handler)
