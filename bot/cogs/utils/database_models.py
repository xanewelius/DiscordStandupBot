from tortoise import Model, fields


class GuildSettings(Model):
    id = fields.IntField(pk=True, unique=True)
    standup_channel_id = fields.IntField(null=True, default=None)
    standup_message_id = fields.IntField(null=True, default=None)
    standup_thread_id = fields.IntField(null=True, default=None)


class StandupMember(Model):
    id = fields.IntField(pk=True, unique=True)
    guild_id = fields.IntField()
    # is_hooligan = fields.BooleanField(default=False)
    replies: fields.ReverseRelation["Reply"]

    @property
    def reply(self):
        return self.replies[0]


class Reply(Model):
    member: fields.ForeignKeyRelation[StandupMember] = fields.ForeignKeyField(
        "models.StandupMember", "replies"
    )
    content = fields.TextField()
    created_at = fields.DatetimeField()
    created_at_date = fields.DateField()

    @property
    def formatted_content(self):
        escaped_content = self.content.strip("`")
        return f"```{escaped_content}```"
