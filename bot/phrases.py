from typing import Dict, List

from pydantic import BaseModel, Field

from bot import root_path


class DefaultPhrases(BaseModel):
    bot_started: str = Field("Бот {bot.user} успешно запущен")


class BaseBotPhrases(BaseModel):
    default: DefaultPhrases = Field(DefaultPhrases())

    @classmethod
    def load_all(cls) -> List["BotPhrases"]:
        parsed_phrases: List[BotPhrases] = []

        for phrases_path in cls.__phrases_filepaths__():
            phrases = BotPhrases.parse_file(phrases_path)
            parsed_phrases.append(phrases)

        return parsed_phrases

    @classmethod
    def __phrases_filepaths__(cls):
        yield from (root_path / "phrases").glob("*.json")


class StandupPhrases(BaseModel):
    standup_channel_set: str = Field(
        "Standup channel has been set to {channel.mention}"
    )

    standup_title: str = Field("Daily Standup")
    standup_description: str = Field(
        "This is the newly generated text channel used for daily standups!"
    )
    standup_fields: Dict[str, str] = Field(
        {
            "Introduction": "Hi! I'm {bot.user.name} and I will be facilitating your daily standups from now on. To view all available commands, try `!help`",
        }
    )

    standup_thread_name: str = Field("archive")
    member_added: str = Field("You are now participating in standup")

    standup_questions: List[str] = Field(
        [
            "I have done it!",
            "What are your goals for today?",
            "Is there anything stopping you from completing your tasks?",
        ]
    )

    questions_message_fmt: str = Field(
        """Here is your daily standup prompt:
```
{questions}```
Please make sure you have thought about your response **very carefully** as standups are more for *the entire team*.
Once you are ready to respond, simply DM me with `!reply ...` where `...` represents your response."""
    )

    cant_reply: str = Field("You can't send a reply at this time")
    not_in_standup: str = Field("You are not participating in the standup right now")
    updated_response: str = Field("Updated response")
    already_replied: str = Field("You have already replied to the questions")
    thread_reply_fmt: str = Field("<@{reply.member.id}>\n{reply.formatted_content}")
    standup_results_description_fmt: str = Field("Hooligans: {hooligans}\n\n{replies}")
    page_description_fmt: str = Field("{replies}")
    member_reply_fmt: str = Field("<@{member.id}>\n{member.reply.formatted_content}")
    no_hooligans: str = Field("No")
    list_title: str = Field("Standup members")
    no_longer_a_member: str = Field("You're no longer participating in standup")
    reset_message: str = Field("All standup data has been reset")
    no_reply: str = Field("You haven't sent a reply yet")


class BotPhrases(BaseBotPhrases):
    standup: StandupPhrases = Field(StandupPhrases())
