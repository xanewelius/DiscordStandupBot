import os
import re
import sys
from pathlib import Path
from typing import Type

import typer
from pydantic import BaseModel

from bot import root_path
from bot.config import BotConfig
from bot.phrases import BotPhrases

app = typer.Typer()


@app.command()
def dev():
    for config_filepath in BotConfig.__config_filepaths__():
        create_json_file(config_filepath)
        fill_file_from_model(config_filepath, BotConfig)


@app.command()
def update():
    for config_filepath in BotConfig.__config_filepaths__():
        if not config_filepath.exists():
            continue

        update_file_from_model(config_filepath, BotConfig)

    for phrases_filepath in BotPhrases.__phrases_filepaths__():
        update_file_from_model(phrases_filepath, BotPhrases)


@app.command()
def refresh():
    for config_filepath in BotConfig.__config_filepaths__():
        if not config_filepath.exists() or config_filepath.name.startswith("_"):
            continue

        fill_file_from_model(config_filepath, BotConfig)

    for phrases_filepath in BotPhrases.__phrases_filepaths__():
        fill_file_from_model(phrases_filepath, BotPhrases)

    os.system(f"{sys.executable} -m pip freeze > requirements.txt")


@app.command()
def cog(name: str, jump: bool = False):
    cogs_dirpath = root_path / "bot/cogs"
    cog_filepath = create_cog(cogs_dirpath, name)

    if jump:
        os.system(f"code {cog_filepath.absolute()}")


def create_json_file(filepath: Path) -> bool:
    if filepath.exists():
        return False

    filepath.write_text(r"{}", encoding="utf-8")
    return True


def fill_file_from_model(filepath: Path, model_cls: Type[BaseModel]):
    model_object = model_cls()
    model_json = model_object.json(ensure_ascii=False, indent=2)
    filepath.write_text(model_json, encoding="utf-8")


def update_file_from_model(filepath: Path, model_cls: Type[BaseModel]):
    model_object = model_cls.parse_file(filepath)
    model_json = model_object.json(ensure_ascii=False, indent=2)
    filepath.write_text(model_json, encoding="utf-8")


def cog_path_from_name(cogs_dirpath: Path, cog_name: str) -> Path:
    name_words = re.findall("[A-Z][^A-Z]*", cog_name)
    cog_filename = "_".join(map(str.lower, name_words)) + ".py"
    return cogs_dirpath / cog_filename


def create_cog(cogs_dirpath: Path, cog_name: str) -> Path:
    cog_path = cog_path_from_name(cogs_dirpath, cog_name)

    if cog_path.exists():
        return cog_path

    cog_code = f"""import nextcord

from nextcord.ext import commands

from bot.context import BotContext
from .utils.base_cog import BaseCog


class {cog_name}(BaseCog):
    pass


def setup(bot):
    bot.add_cog({cog_name}(bot))"""

    cog_path.write_text(cog_code, encoding="utf-8")
    return cog_path


if __name__ == "__main__":
    app()
