from dataclasses import dataclass
from typing import *

import nextcord
from nextcord import ui
from nextcord.interactions import Interaction

from bot.context import BotContext


@dataclass
class Page:
    content: str = None
    embed: nextcord.Embed = None


class BasePaginator:
    def __init__(self, pages: List[Page]):
        self.pages = pages
        self.current_page_index = 0

    def current_page(self) -> Page:
        return self.pages[self.current_page_index]

    def next_page(self) -> Page:
        self.current_page_index = (self.current_page_index + 1) % len(self.pages)
        return self.current_page()

    def prev_page(self) -> Page:
        self.current_page_index = (self.current_page_index - 1) % len(self.pages)
        return self.current_page()

    async def paginate(ctx: BotContext):
        return NotImplemented


class ValidatedButton(ui.Button):
    def validate_interaction(self, interaction: nextcord.Interaction):
        return True

    async def callback(self, interaction: Interaction):
        if not self.validate_interaction(interaction):
            return

        return await self.validated_callback(interaction)

    async def validated_callback(self, interaction: Interaction):
        return NotImplemented


class UserButton(ValidatedButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.view: ArrowsView

    def validate_interaction(self, interaction: nextcord.Interaction):
        return interaction.user == self.view.user


class PrevButton(UserButton):
    async def validated_callback(self, interaction: nextcord.Interaction):
        view: ArrowsView = self.view
        current_page = view.paginator.prev_page()

        await interaction.response.edit_message(
            content=current_page.content, embed=current_page.embed
        )


class NextButton(UserButton):
    async def validated_callback(self, interaction: nextcord.Interaction):
        view: ArrowsView = self.view
        current_page = view.paginator.next_page()

        await interaction.response.edit_message(
            content=current_page.content, embed=current_page.embed
        )


class ArrowsView(ui.View):
    ARROW_LEFT = "⬅️"
    ARROW_RIGHT = "➡️"

    def __init__(
        self, paginator: "ButtonsPaginator", user: nextcord.User, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.user = user
        self.paginator = paginator

        self.add_item(PrevButton(emoji=self.ARROW_LEFT))
        self.add_item(NextButton(emoji=self.ARROW_RIGHT))


class ButtonsPaginator(BasePaginator):
    async def paginate(self, ctx: BotContext):
        arrow_view = ArrowsView(self, ctx.author)
        current_page = self.current_page()
        await ctx.send(current_page.content, embed=current_page.embed, view=arrow_view)
