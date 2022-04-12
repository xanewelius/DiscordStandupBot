import datetime as dt
from typing import List, Tuple, Union

from pydantic import BaseModel, Field

from . import root_path


class BaseBotConfig(BaseModel):
    __config_filenames__ = ("_config_dev.json", "config.json")

    bot_token: str = Field("OTYyMzI5NzUyODgwOTY3Njky.YlF9bA.psifzthGf6VJIt94ZK91rOxny8A")
    command_prefix: str = Field("!")

    @classmethod
    def load_any(cls):
        for filepath in cls.__config_filepaths__():
            if filepath.exists():
                return cls.parse_file(filepath)

    @classmethod
    def __config_filepaths__(cls):
        for filename in cls.__config_filenames__:
            yield root_path / filename


class OrmConfig(BaseModel):
    database_url: str = Field("sqlite://{sqlite_path}")


class StandupConfig(BaseModel):
    questions_start_time: dt.time = Field("10:00")
    questions_end_time: dt.time = Field("22:00")
    excluded_days: List[int] = Field((6, 7))


class BotConfig(BaseBotConfig):
    standup: StandupConfig = Field(StandupConfig())
    database: OrmConfig = Field(OrmConfig())
