import nextcord
from nextcord.ext import commands

from . import bot


class BotContext(commands.Context):
    def __init__(self, **attrs):
        super().__init__(**attrs)
        self.bot: bot.Bot
        self.message: nextcord.Message
        self.phrases = self.bot.default_phrases

    async def answer(self, *args, **kwargs) -> nextcord.Message:
        ref = self.message.to_reference(fail_if_not_exists=False)
        return await self.send(*args, **kwargs, reference=ref, mention_author=True)
