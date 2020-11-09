# pylint: disable=W0201
# Discord Packages
import discord
from discord.ext import commands

# Bot Utilities
from cogs.utils.logging import Logger
from cogs.utils.server import Server
from cogs.utils.settings import Settings

import os
import threading
import time
import traceback
from argparse import ArgumentParser, RawTextHelpFormatter

from pymongo import MongoClient

intents = discord.Intents.none()
intents.emojis = True
intents.guild_typing = True
intents.guilds = True
intents.members = True
intents.messages = True
intents.presences = True
intents.reactions = True


def _get_prefix(bot, message):
    if not message.guild:
        prefixes = settings.prefix
        return commands.when_mentioned_or(*prefixes)(bot, message)
    prefixes = settings.prefix
    return commands.when_mentioned_or(*prefixes)(bot, message)


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=_get_prefix, intents=intents)
        self.logger = logger
        self.logger.debug("Logging level: %s", level.upper())
        self.data_dir = data_dir
        self.settings = settings.extra
        self.client = MongoClient('localhost', 27017)

    async def on_message(self, message):
        if message.author.bot:
            return
        await self.process_commands(message)

    async def on_ready(self):
        if not hasattr(self, "uptime"):
            self.uptime = time.time()
        if not hasattr(self, "appinfo"):
            self.appinfo = await self.application_info()

        print(f"Logged in as: {self.user.name} in {len(self.guilds)} servers.")
        print(f"Version: {discord.__version__}")
        self.logger.debug("Bot Ready")

        #extensions = ["cogs.misc", "cogs.poeng", "cogs.errors", "cogs.github", "cogs.jobb", "cogs.broder"]
        extensions = ["cogs.errors", "cogs.misc", "cogs.jobb"]
        for extension in extensions:
            try:
                self.logger.debug("Loading extension %s", extension)
                self.load_extension(extension)
            except Exception as e:
                self.logger.exception("Loading of extension %s failed: %s", extension, e)

    def run(self):
        try:
            super().run(settings.token)
        except Exception as e:
            tb = e.__traceback__
            self.logger.error(traceback.extract_tb(tb))
            print(e)


if __name__ == "__main__":
    parser = ArgumentParser(prog="Roxedus' ProgBott",
                            description="Programmeringsbot",
                            formatter_class=RawTextHelpFormatter)

    parser.add_argument("-D", "--debug", action="store_true", help="Sets debug to true")
    parser.add_argument("-l", "--level", help="Sets debug level",
                        choices=["critical", "error", "warning", "info", "debug"], default="warning")
    parser.add_argument("-d", "--data-directory", help="Define an alternate data directory location", default="data")
    parser.add_argument("-f", "--log-to-file", action="store_true", help="Save log to file", default=True)

    args = parser.parse_args()

    level = args.level
    data_dir = args.data_directory

    if args.debug or os.environ.get("debug"):
        level = "debug"

    if args.data_directory:
        data_dir = str(args.data_directory)

    logger = Logger(location=data_dir, level=level, to_file=args.log_to_file).logger
    logger.debug("Data folder: %s", data_dir)

    settings = Settings(data_dir=data_dir)

    bot = Bot()

    server = threading.Thread(target=Server, kwargs={"data_dir": data_dir, "settings": settings, "bot": bot})
    server.start()

    bot.run()
