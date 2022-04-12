import logging
from typing import List

import nextcord
from nextcord.ext import commands

from .config import BotConfig
from .context import BotContext
from .phrases import BotPhrases


class Bot(commands.AutoShardedBot):
    def __init__(self, config: BotConfig, phrases: List[BotPhrases]):
        super().__init__(
            command_prefix=get_command_prefix, intents=nextcord.Intents.all()
        )
        self.logger = logging.getLogger("bot")
        self.config = config
        self.phrases = phrases

    @property
    def default_phrases(self) -> BotPhrases:
        return self.phrases[0]

    def run(self):
        super().run(self.config.bot_token)

    async def close(self):
        for cog in self.cogs.values():
            await cog.on_shutdown()

        await super().close()

    async def get_context(self, message: nextcord.Message) -> BotContext:
        return await super().get_context(message, cls=BotContext)

    async def process_commands(self, message: nextcord.Message):
        ctx = await self.get_context(message)

        if ctx.command is None:
            return

        await self.invoke(ctx)

    async def on_message(self, message: nextcord.Message):
        if message.author.bot:
            return

        await self.process_commands(message)

    async def on_ready(self):
        print(self.default_phrases.default.bot_started.format(bot=self))


async def get_command_prefix(bot: Bot, message: nextcord.Message) -> str:
    return bot.config.command_prefix
