import datetime as dt
from typing import List, Optional

import aioschedule
import nextcord
import pytz
from bot.context import BotContext
from nextcord.ext import commands
from tortoise.queryset import Prefetch

from .utils.base_cog import BaseCog
from .utils.database_models import GuildSettings, Reply, StandupMember


class Standup(BaseCog):
    def __init__(self, *args):
        super().__init__(*args)
        aioschedule.every().day.at(
            self.bot.config.standup.questions_start_time.strftime("%H:%M")
        ).do(self.ask_questions_job)
        aioschedule.every().day.at(
            self.bot.config.standup.questions_end_time.strftime("%H:%M")
        ).do(self.send_results_job)

    def is_excluded_day(self):
        now = dt.datetime.now()
        return now.isoweekday() in self.bot.config.standup.excluded_days

    async def ask_questions_job(self):
        if self.is_excluded_day():
            return

        standup_members = await StandupMember.all()

        for standup_member in standup_members:
            user = self.bot.get_user(standup_member.id)

            try:
                await user.send(
                    self.bot.default_phrases.standup.questions_message_fmt.format(
                        questions="\n".join(
                            f"{i + 1}. {name}"
                            for i, name in enumerate(
                                self.bot.default_phrases.standup.standup_questions
                            )
                        )
                    )
                )
            except Exception:
                continue

    async def send_results_job(self):
        if self.is_excluded_day():
            return

        for guild in self.bot.guilds:
            settings = await GuildSettings.get_or_none(id=guild.id)
            standup_channel = (
                guild.get_channel(settings.standup_channel_id) if settings else None
            )

            if settings is None or standup_channel is None:
                continue

            utc_now = dt.datetime.utcnow()
            standup_members = await StandupMember.filter().prefetch_related(
                Prefetch(
                    "replies",
                    Reply.filter(created_at_date=utc_now.date()),
                )
            )

            if not standup_members:
                continue

            hooligans: List[StandupMember] = []
            passed_members: List[StandupMember] = []

            for standup_member in standup_members:
                if standup_member.replies:
                    passed_members.append(standup_member)
                else:
                    hooligans.append(standup_member)

            await self.send_standup_results_message(
                standup_channel, hooligans, passed_members
            )

    async def send_standup_results_message(
        self,
        channel: nextcord.TextChannel,
        hooligans: List[StandupMember],
        members: List[StandupMember],
    ):
        MEMBERS_PER_PAGE = 10
        members_chunks = list(nextcord.utils.as_chunks(members, MEMBERS_PER_PAGE))

        try:
            first_page_members_chunk = members_chunks.pop(0)
        except IndexError:
            first_page_members_chunk = ()

        first_embed = nextcord.Embed(
            title=self.bot.default_phrases.standup.standup_title,
            description=self.bot.default_phrases.standup.standup_results_description_fmt.format(
                hooligans=" ".join(f"<@{m.id}>" for m in hooligans)
                if hooligans
                else self.bot.default_phrases.standup.no_hooligans,
                replies="\n\n".join(
                    self.bot.default_phrases.standup.member_reply_fmt.format(member=m)
                    for m in first_page_members_chunk
                ),
            ),
            colour=nextcord.Colour.dark_theme(),
        )

        await channel.send(embed=first_embed)

        for chunk in members_chunks:
            page_embed = nextcord.Embed(
                colour=nextcord.Colour.dark_theme(),
                description=self.bot.default_phrases.standup.page_description_fmt.format(
                    replies="\n\n".join(
                        self.bot.default_phrases.standup.member_reply_fmt.format(
                            member=m
                        )
                        for m in chunk
                    )
                ),
            )

            await channel.send(embed=page_embed)

    def get_standup_embed(self, ctx: BotContext):
        embed = nextcord.Embed(
            title=ctx.phrases.standup.standup_title,
            description=ctx.phrases.standup.standup_description.format(bot=ctx.bot),
            colour=nextcord.Colour.dark_theme(),
        )

        for name, value in ctx.phrases.standup.standup_fields.items():
            embed.add_field(name=name, value=value.format(bot=ctx.bot), inline=False)

        return embed

    def get_standup_datetime(self, now: dt.datetime):
        start_datetime = now.replace(
            hour=self.bot.config.standup.questions_start_time.hour,
            minute=self.bot.config.standup.questions_start_time.minute,
        )
        end_datetime = now.replace(
            hour=self.bot.config.standup.questions_end_time.hour,
            minute=self.bot.config.standup.questions_end_time.minute,
        )
        return start_datetime, end_datetime

    @commands.has_permissions(administrator=True)
    @commands.command(name="standup-channel")
    async def standup_channel(self, ctx: BotContext, channel: nextcord.TextChannel):
        await ctx.answer(
            ctx.phrases.standup.standup_channel_set.format(channel=channel)
        )
        standup_message = await channel.send(embed=self.get_standup_embed(ctx))
        thread = await standup_message.create_thread(
            name=ctx.phrases.standup.standup_thread_name
        )
        await GuildSettings.update_or_create(
            dict(
                standup_channel_id=channel.id,
                standup_message_id=standup_message.id,
                standup_thread_id=thread.id,
            ),
            id=ctx.guild.id,
        )

    @commands.command(aliases=["am"])
    async def addmember(self, ctx: BotContext):
        await StandupMember.get_or_create(id=ctx.author.id, guild_id=ctx.guild.id)
        await ctx.answer(ctx.phrases.standup.member_added)

    @commands.command()
    async def reply(
        self, ctx: BotContext, guild: Optional[nextcord.Guild], *, message: str
    ):
        if ctx.guild is not None:
            guild = ctx.guild

        if self.is_excluded_day():
            return await ctx.answer(ctx.phrases.standup.cant_reply)

        now = dt.datetime.now()
        start_datetime, end_datetime = self.get_standup_datetime(now)

        if now < start_datetime or now > end_datetime:
            return await ctx.answer(ctx.phrases.standup.cant_reply)

        if guild is None:
            standup_member = await StandupMember.filter(id=ctx.author.id).first()
        else:
            standup_member = await StandupMember.get_or_none(
                id=ctx.author.id, guild_id=guild.id
            )

        if standup_member is None:
            return await ctx.answer(ctx.phrases.standup.not_in_standup)

        utc_now = dt.datetime.utcnow()

        if await Reply.exists(member=standup_member, created_at_date=utc_now.date()):
            return await ctx.answer(ctx.phrases.standup.already_replied)

        await ctx.answer(ctx.phrases.standup.updated_response)
        reply = await Reply.create(
            member=standup_member,
            content=message,
            created_at=utc_now,
            created_at_date=utc_now.date(),
        )

        settings = await GuildSettings.get_or_none(id=standup_member.guild_id)

        try:
            guild = self.bot.get_guild(settings.id)
            thread = guild.get_thread(settings.standup_thread_id)
            embed = nextcord.Embed(
                description=ctx.phrases.standup.thread_reply_fmt.format(reply=reply),
                colour=nextcord.Colour.dark_theme(),
            )
            await thread.send(embed=embed)
        except Exception:
            return

    @commands.command()
    async def list(self, ctx: BotContext):
        standup_members = await StandupMember.filter(guild_id=ctx.guild.id).all()
        embed = nextcord.Embed(
            title=ctx.phrases.standup.list_title,
            colour=nextcord.Colour.dark_theme(),
            description=" ".join(f"<@{m.id}>" for m in standup_members),
        )

        await ctx.answer(embed=embed)

    @commands.command(aliases=["rm"])
    async def removemember(self, ctx: BotContext):
        await StandupMember.filter(id=ctx.author.id, guild_id=ctx.guild.id).delete()
        await ctx.answer(ctx.phrases.standup.no_longer_a_member)

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def reset(self, ctx: BotContext):
        await ctx.answer(ctx.phrases.standup.reset_message)
        settings = await GuildSettings.get_or_none(id=ctx.guild.id)
        await StandupMember.filter(guild_id=ctx.guild.id).delete()

        standup_channel: nextcord.TextChannel = (
            ctx.guild.get_channel(settings.standup_channel_id) if settings else None
        )

        if settings is None or standup_channel is None:
            return

        await standup_channel.purge(
            limit=None, check=lambda m: m.id != settings.standup_message_id
        )

    @commands.command()
    async def show(self, ctx: BotContext):
        await ctx.answer(embed=self.get_standup_embed(ctx))

    @commands.command()
    async def view(self, ctx: BotContext, guild: Optional[nextcord.Guild]):
        utc_now = dt.datetime.utcnow()
        prefetch = Prefetch("replies", Reply.filter(created_at_date=utc_now.date()))

        if guild is None:
            standup_member = (
                await StandupMember.filter(id=ctx.author.id)
                .prefetch_related(prefetch)
                .first()
            )
        else:
            standup_member = (
                await StandupMember.filter(id=ctx.author.id, guild_id=guild.id)
                .prefetch_related(prefetch)
                .first()
            )

        if standup_member is None:
            return await ctx.answer(ctx.phrases.standup.not_in_standup)

        try:
            embed = nextcord.Embed(
                description=ctx.phrases.standup.member_reply_fmt.format(
                    member=standup_member
                ),
                colour=nextcord.Colour.dark_theme(),
            )

            await ctx.answer(embed=embed)
        except (IndexError, AttributeError):
            await ctx.answer(ctx.phrases.standup.no_reply)


def setup(bot):
    bot.add_cog(Standup(bot))
