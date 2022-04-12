import asyncio

import aioschedule

from .utils.base_cog import BaseCog


class Schedule(BaseCog):
    DELAY_SECONDS = 60

    async def on_startup(self):
        await self.bot.wait_until_ready()
        self.bot.loop.create_task(self.pending_jobs_loop())

    async def pending_jobs_loop(self):
        while True:
            await asyncio.sleep(self.DELAY_SECONDS)
            await aioschedule.run_pending()


def setup(bot):
    bot.add_cog(Schedule(bot))
