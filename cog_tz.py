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
        e.add_field(name="Converted Timezone", value=str(datetime2.tzinfo) + ', ' + datetime2.strftime("UTC%z"),
                    inline=True)

        e.add_field(name="", value="", inline=False)

        e.add_field(name="Original Time", value=datetime1.strftime("%H:%M:%S**\n**%d/%m/%Y"), inline=True)
        e.add_field(name="Original Timezone", value=str(datetime1.tzinfo) + ', ' + datetime1.strftime("UTC%z"),
                    inline=True)

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

    @staticmethod
    def get_list_page(ls: list, page: int, items_in_page: int):
        """
        :param ls:
        :param page: starting at 0
        :param items_in_page: starting at 1
        :return:
        """

        if page > Time.get_max_page(ls, items_in_page):
            raise IndexError('Page number is too high')
        if page < 0:
            raise IndexError('Page number is too low')
        start_index = page * items_in_page
        end_index = start_index + items_in_page
        ret = ls[start_index:end_index]
        return ret

    @staticmethod
    def get_max_page(ls: list, items_in_page: int):
        """
        Max page index (number - 1)
        :param ls:
        :param items_in_page:
        :return:
        """
        len_ls = len(ls)
        res = len_ls // items_in_page
        if len_ls % items_in_page != 0:
            res += 1

        return res - 1

    @app_commands.command(name='list', description='List all valid timezones')
    @app_commands.describe(search='Search the timezone list',
                           page='Get a specific page')
    async def time_list(self, intr: discord.Interaction, search: str = None, page: int = None):
        await intr.response.defer()

        if page is None:
            page = 1
        if search is not None:
            ls = [item for item in pytz.all_timezones
                  if search.lower().replace(' ', '_') in item.lower()]
        else:
            ls = [item for item in pytz.all_timezones]

        items_in_page = 25

        try:
            sliced = self.get_list_page(ls, page - 1, items_in_page)
        except IndexError as e:
            await intr.followup.send(e.args[0])
            return

        formatted = '\n'.join(
            [f'{i + 1}. `{sliced[i]}`' for i in range(0, len(sliced))]
        )

        ret = f"""\
==== PAGE {page}/{self.get_max_page(ls, items_in_page) + 1} ({len(sliced)} items) ====

{formatted}\
"""
        if search is None:
            ret += """

> ### TIP:
> Use `/time list search:[search term]` to narrow down search results!
."""
        v = discord.ui.View()
        v.add_item(discord.ui.Button(label='Read externally', style=discord.ButtonStyle.url,
                                     url='https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List'))
        await intr.followup.send(ret, view=v)

    @app_commands.command(name='set', description='Set your timezone')
    @app_commands.describe(timezone='Timezone\'s name',
                           user='Set others\' timezone. Author only')
    async def set_time(self, intr: discord.Interaction, timezone: str, user: discord.User = None):
        if user is not None:
            if not Time.has_permission(intr.user):
                await intr.response.send_message('No permission')
                return

        if user is None:
            user = intr.user

        if timezone not in pytz.all_timezones:
            await intr.response.send_message(
                'Error: invalid timezone!\nPlease use `/time list` to look up valid timezones')
            return

        if self.db.add_user(user.id, timezone):
            await intr.response.send_message(f'Successfully set `@{user.name}`\'s timezone to {timezone}')
        else:
            await intr.response.send_message(f'Failed to set `@{user.name}`\'s timezone')

    @app_commands.command(name='get', description='Get a user\'s time')
    @app_commands.describe(user='User to get timezone of. Leave empty to get yours.')
    async def get_time(self, intr: discord.Interaction, user: discord.User = None):
        if user is None:
            user = intr.user

        tz_str = self.db.get_user_timezone(user.id)

        if tz_str is None:
            await intr.response.send_message(f'User `@{user.name}` has not set their timezone yet')
            return

        await intr.response.send_message(embed=TimeEmbedFactory.simple_embed(user, tz_str))

    @app_commands.command(name='clear', description='Remove your assigned data')
    async def time_clear(self, intr: discord.Interaction, confirmation: str = None):
        if confirmation is None:
            await intr.response.send_message("Are you sure you would like to clear your data?\n"
                                             "This action is irreversible!\n"
                                             f"Please run `/time clear {intr.user.name}` to confirm.")
            return

        if confirmation != intr.user.name:
            await intr.response.send_message('Invalid confirmation string.')
            return

        await intr.response.defer()
        self.db.remove_user(intr.user.id)
        await intr.followup.send(f"Successfully removed user `@{intr.user.name}` from TimeSync")

    @app_commands.command(name='convert', description='Convert a time from one timezone to another')
    @app_commands.describe(timezone1='Timezone 1\'s name (Use /time list for a list)',
                           timezone2='Timezone 2\'s name (Use /time list for a list)',
                           time='Format: HH:MM:SS',
                           date='Format: YYYY-MM-DD')
    async def time_convert(self, intr: discord.Interaction, timezone1: str, timezone2: str, time: str = None,
                           date: str = None):

        if timezone1 not in pytz.all_timezones:
            await intr.response.send_message(
                f'Invalid timezone: "{timezone1}"\nFor a list of all valid timezones use `/time list`')
            return

        if timezone2 not in pytz.all_timezones:
            await intr.response.send_message(
                f'Invalid timezone: "{timezone2}"\nFor a list of all valid timezones use `/time list`')
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
