from nextcord.ext import commands

from bot.bot import Bot


class BaseCog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.bot.loop.create_task(self.on_startup())

    async def on_shutdown(self):
        pass

    async def on_startup(self):
        pass
