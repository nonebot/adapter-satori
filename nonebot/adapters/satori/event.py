from enum import Enum
from copy import deepcopy
from typing_extensions import override
from typing import TYPE_CHECKING, TypeVar, Optional

from nonebot.utils import escape_tag
from nonebot.compat import model_dump, type_validate_python

from nonebot.adapters import Event as BaseEvent

from .element import parse
from .models import Role, User
from .compat import model_validator
from .models import Event as SatoriEvent
from .message import Message, RenderMessage
from .models import MessageObject as SatoriMessage
from .models import ArgvInteraction, ButtonInteraction
from .models import Guild, Login, Member, Channel, ChannelType

E = TypeVar("E", bound="Event")


class EventType(str, Enum):
    FRIEND_REQUEST = "friend-request"
    GUILD_ADDED = "guild-added"
    GUILD_MEMBER_ADDED = "guild-member-added"
    GUILD_MEMBER_REMOVED = "guild-member-removed"
    GUILD_MEMBER_REQUEST = "guild-member-request"
    GUILD_MEMBER_UPDATED = "guild-member-updated"
    GUILD_REMOVED = "guild-removed"
    GUILD_REQUEST = "guild-request"
    GUILD_ROLE_CREATED = "guild-role-created"
    GUILD_ROLE_DELETED = "guild-role-deleted"
    GUILD_ROLE_UPDATED = "guild-role-updated"
    GUILD_UPDATED = "guild-updated"
    LOGIN_ADDED = "login-added"
    LOGIN_REMOVED = "login-removed"
    LOGIN_UPDATED = "login-updated"
    MESSAGE_CREATED = "message-created"
    MESSAGE_DELETED = "message-deleted"
    MESSAGE_UPDATED = "message-updated"
    REACTION_ADDED = "reaction-added"
    REACTION_REMOVED = "reaction-removed"
    INTERNAL = "internal"
    INTERACTION_BUTTON = "interaction/button"
    INTERACTION_COMMAND = "interaction/command"


class Event(BaseEvent, SatoriEvent):
    __type__: EventType

    @override
    def get_type(self) -> str:
        return ""

    @override
    def get_event_name(self) -> str:
        return self.type

    @override
    def get_event_description(self) -> str:
        return escape_tag(str(model_dump(self)))

    @override
    def get_message(self) -> Message:
        raise ValueError("Event has no message!")

    @override
    def get_user_id(self) -> str:
        if self.user:
            return self.user.id
        raise ValueError("Event has no context!")

    @override
    def get_session_id(self) -> str:
        if self.channel:
            if self.guild:
                return f"{self.guild.id}/{self.channel.id}"
            return self.channel.id
        raise ValueError("Event has no context!")

    @override
    def is_tome(self) -> bool:
        return False


EVENT_CLASSES: dict[str, type[Event]] = {}


def register_event_class(event_class: type[E]) -> type[E]:
    EVENT_CLASSES[event_class.__type__.value] = event_class
    return event_class


class NoticeEvent(Event):
    @override
    def get_type(self) -> str:
        return "notice"


class FriendEvent(NoticeEvent):
    user: User  # type: ignore

    @override
    def get_user_id(self) -> str:
        return self.user.id

    @override
    def get_session_id(self) -> str:
        return self.user.id


@register_event_class
class FriendRequestEvent(FriendEvent):
    __type__ = EventType.FRIEND_REQUEST


class GuildEvent(NoticeEvent):
    guild: Guild  # type: ignore

    @override
    def get_session_id(self) -> str:
        return self.guild.id


@register_event_class
class GuildAddedEvent(GuildEvent):
    __type__ = EventType.GUILD_ADDED


@register_event_class
class GuildRemovedEvent(GuildEvent):
    __type__ = EventType.GUILD_REMOVED


@register_event_class
class GuildRequestEvent(GuildEvent):
    __type__ = EventType.GUILD_REQUEST


@register_event_class
class GuildUpdatedEvent(GuildEvent):
    __type__ = EventType.GUILD_UPDATED


class GuildMemberEvent(GuildEvent):
    user: User  # type: ignore

    @override
    def get_user_id(self) -> str:
        return self.user.id

    @override
    def get_session_id(self) -> str:
        return f"{self.guild.id}/{self.get_user_id()}"


@register_event_class
class GuildMemberAddedEvent(GuildMemberEvent):
    __type__ = EventType.GUILD_MEMBER_ADDED


@register_event_class
class GuildMemberRemovedEvent(GuildMemberEvent):
    __type__ = EventType.GUILD_MEMBER_REMOVED


@register_event_class
class GuildMemberRequestEvent(GuildMemberEvent):
    __type__ = EventType.GUILD_MEMBER_REQUEST

    member: Member  # type: ignore


@register_event_class
class GuildMemberUpdatedEvent(GuildMemberEvent):
    __type__ = EventType.GUILD_MEMBER_UPDATED

    member: Member  # type: ignore


class GuildRoleEvent(GuildEvent):
    role: Role  # type: ignore

    @override
    def get_session_id(self) -> str:
        return f"{self.guild.id}/{self.role.id}"


@register_event_class
class GuildRoleCreatedEvent(GuildRoleEvent):
    __type__ = EventType.GUILD_ROLE_CREATED


@register_event_class
class GuildRoleDeletedEvent(GuildRoleEvent):
    __type__ = EventType.GUILD_ROLE_DELETED


@register_event_class
class GuildRoleUpdatedEvent(GuildRoleEvent):
    __type__ = EventType.GUILD_ROLE_UPDATED


class LoginEvent(NoticeEvent):
    login: Login  # type: ignore


@register_event_class
class LoginAddedEvent(LoginEvent):
    __type__ = EventType.LOGIN_ADDED


@register_event_class
class LoginRemovedEvent(LoginEvent):
    __type__ = EventType.LOGIN_REMOVED


@register_event_class
class LoginUpdatedEvent(LoginEvent):
    __type__ = EventType.LOGIN_UPDATED


class MessageEvent(Event):
    channel: Channel  # type: ignore
    user: User  # type: ignore
    message: SatoriMessage  # type: ignore
    to_me: bool = False
    reply: Optional[RenderMessage] = None

    if TYPE_CHECKING:
        _message: Message
        original_message: Message

    @override
    def get_type(self) -> str:
        return "message"

    @override
    def is_tome(self) -> bool:
        return self.to_me

    @override
    def get_message(self) -> Message:
        return self._message

    @model_validator(mode="before")
    def generate_message(cls, values):
        if isinstance(values, dict):
            values["_message"] = Message.from_satori_element(parse(values["message"]["content"]))
            values["original_message"] = deepcopy(values["_message"])
        return values

    @property
    def msg_id(self) -> str:
        return self.message.id

    def convert(self) -> "MessageEvent":
        raise NotImplementedError


@register_event_class
class MessageCreatedEvent(MessageEvent):
    __type__ = EventType.MESSAGE_CREATED

    def convert(self):
        if self.channel.type == ChannelType.DIRECT:
            return type_validate_python(PrivateMessageCreatedEvent, model_dump(self))
        else:
            return type_validate_python(PublicMessageCreatedEvent, model_dump(self))


@register_event_class
class MessageDeletedEvent(MessageEvent):
    __type__ = EventType.MESSAGE_DELETED

    @override
    def get_type(self) -> str:
        return "notice"

    def convert(self):
        if self.channel.type == ChannelType.DIRECT:
            return type_validate_python(PrivateMessageDeletedEvent, model_dump(self))
        else:
            return type_validate_python(PublicMessageDeletedEvent, model_dump(self))


@register_event_class
class MessageUpdatedEvent(MessageEvent):
    __type__ = EventType.MESSAGE_UPDATED

    @override
    def get_type(self) -> str:
        return "notice"

    def convert(self):
        if self.channel.type == ChannelType.DIRECT:
            return type_validate_python(PrivateMessageUpdatedEvent, model_dump(self))
        else:
            return type_validate_python(PublicMessageUpdatedEvent, model_dump(self))


class PrivateMessageEvent(MessageEvent):
    @override
    def is_tome(self) -> bool:
        return True

    @override
    def get_session_id(self) -> str:
        return self.channel.id

    @override
    def get_user_id(self) -> str:
        return self.user.id


class PublicMessageEvent(MessageEvent):
    member: Member  # type: ignore

    @override
    def get_session_id(self) -> str:
        s = f"{self.channel.id}/{self.user.id}"
        if self.guild:
            s = f"{self.guild.id}/{s}"
        return s

    @override
    def get_user_id(self) -> str:
        return self.user.id


class PrivateMessageCreatedEvent(MessageCreatedEvent, PrivateMessageEvent):
    @override
    def get_event_description(self) -> str:
        return escape_tag(
            f"Message {self.msg_id} from "
            f"{self.user.name or self.user.nick or ''}({self.channel.id}): {self.get_message()!r}"
        )


class PublicMessageCreatedEvent(MessageCreatedEvent, PublicMessageEvent):
    @override
    def get_event_description(self) -> str:
        return escape_tag(
            f"Message {self.msg_id} from "
            f"{(self.member.nick if self.member else None) or (self.user.name or self.user.nick or '')}({self.user.id})"
            f"@[{self.channel.name or ''}:{self.channel.id}]"
            f": {self.get_message()!r}"
        )


class PrivateMessageDeletedEvent(MessageDeletedEvent, PrivateMessageEvent):
    @override
    def get_event_description(self) -> str:
        return escape_tag(
            f"Message {self.msg_id} from " f"{self.user.name or self.user.nick or ''}({self.channel.id}) deleted"
        )


class PublicMessageDeletedEvent(MessageDeletedEvent, PublicMessageEvent):
    @override
    def get_event_description(self) -> str:
        return escape_tag(
            f"Message {self.msg_id} from "
            f"{(self.member.nick if self.member else None) or (self.user.name or self.user.nick or '')}({self.user.id})"
            f"@[{self.channel.name or ''}:{self.channel.id}] deleted"
        )


class PrivateMessageUpdatedEvent(MessageUpdatedEvent, PrivateMessageEvent):
    @override
    def get_event_description(self) -> str:
        return escape_tag(
            f"Message {self.msg_id} from "
            f"{self.user.name or self.user.nick or ''}({self.channel.id}) updated"
            f": {self.get_message()!r}"
        )


class PublicMessageUpdatedEvent(MessageUpdatedEvent, PublicMessageEvent):
    @override
    def get_event_description(self) -> str:
        return escape_tag(
            f"Message {self.msg_id} from "
            f"{(self.member.nick if self.member else None) or (self.user.name or self.user.nick or '')}({self.user.id})"
            f"@[{self.channel.name or ''}:{self.channel.id}] updated"
            f": {self.get_message()!r}"
        )


class ReactionEvent(NoticeEvent):
    guild: Guild  # type: ignore
    user: User  # type: ignore
    message: SatoriMessage  # type: ignore

    if TYPE_CHECKING:
        _message: Message

    @override
    def get_user_id(self) -> str:
        return self.user.id

    @override
    def get_session_id(self) -> str:
        return f"{self.guild.id}_{self.user.id}"

    @model_validator(mode="before")
    def generate_message(cls, values):
        if isinstance(values, dict):
            if "message" in values and values["message"] and "content" in values["message"]:
                values["_message"] = Message.from_satori_element(parse(values["message"]["content"]))
            else:
                values["_message"] = Message()
            if "message" not in values or not values["message"]:
                message_id = values.get("_data", {}).get("message_id", "None")
                values["message"] = SatoriMessage(id=str(message_id), content="")
        return values

    @property
    def msg_id(self) -> str:
        return self.message.id


@register_event_class
class ReactionAddedEvent(ReactionEvent):
    __type__ = EventType.REACTION_ADDED

    @override
    def get_event_description(self) -> str:
        return escape_tag(f"Reaction added to msg {self.msg_id} by {self.user.name}({self.guild.id})")


@register_event_class
class ReactionRemovedEvent(ReactionEvent):
    __type__ = EventType.REACTION_REMOVED

    @override
    def get_event_description(self) -> str:
        return escape_tag(f"Reaction removed from msg {self.msg_id}")


@register_event_class
class InternalEvent(Event):
    __type__ = EventType.INTERNAL

    @override
    def get_event_name(self) -> str:
        return getattr(self, "_type", "internal")


class InteractionEvent(NoticeEvent):
    def convert(self) -> "InteractionEvent":
        raise NotImplementedError

    @override
    def is_tome(self) -> bool:
        return True


@register_event_class
class InteractionButtonEvent(InteractionEvent):
    __type__ = EventType.INTERACTION_BUTTON

    button: ButtonInteraction  # type: ignore

    @override
    def get_event_description(self) -> str:
        return escape_tag(f"Button interacted with button#{self.button.id}")

    def convert(self):
        if self.channel and self.user and self.channel.type != ChannelType.DIRECT:
            return type_validate_python(PublicInteractionButtonEvent, model_dump(self))
        if self.user:
            return type_validate_python(PrivateInteractionButtonEvent, model_dump(self))
        return self


class PrivateInteractionButtonEvent(InteractionButtonEvent):
    user: User  # type: ignore

    @override
    def get_session_id(self) -> str:
        return self.channel.id if self.channel else self.user.id

    @override
    def get_user_id(self) -> str:
        return self.user.id


class PublicInteractionButtonEvent(InteractionButtonEvent):
    user: User  # type: ignore
    channel: Channel  # type: ignore

    @override
    def get_session_id(self) -> str:
        s = f"{self.channel.id}/{self.user.id}"
        if self.guild:
            s = f"{self.guild.id}/{s}"
        return s

    @override
    def get_user_id(self) -> str:
        return self.user.id


@register_event_class
class InteractionCommandEvent(InteractionEvent):
    __type__ = EventType.INTERACTION_COMMAND

    if TYPE_CHECKING:
        _message: Message
        original_message: Message

    @override
    def get_type(self) -> str:
        return "message"

    @override
    def get_message(self) -> Message:
        return self._message

    def convert(self):
        if self.argv:
            return InteractionCommandArgvEvent.convert(self)  # type: ignore
        return InteractionCommandMessageEvent.convert(self)  # type: ignore


class InteractionCommandArgvEvent(InteractionCommandEvent):
    argv: ArgvInteraction  # type: ignore

    @override
    def get_event_description(self) -> str:
        return escape_tag(f"Command interacted with {self.argv}")

    @model_validator(mode="before")
    def generate_message(cls, values):
        if isinstance(values, dict):
            cmd = values["argv"]["name"]
            if values["argv"].get("arguments", []):
                cmd += " ".join(values["argv"]["arguments"])
            values["_message"] = Message(cmd)
            values["original_message"] = deepcopy(values["_message"])
        return values

    def convert(self):
        if self.channel and self.user and self.channel.type != ChannelType.DIRECT:
            return type_validate_python(PublicInteractionCommandArgvEvent, model_dump(self))
        if self.user:
            return type_validate_python(PrivateInteractionCommandArgvEvent, model_dump(self))
        return self


class PrivateInteractionCommandArgvEvent(InteractionCommandArgvEvent):
    user: User  # type: ignore

    @override
    def get_session_id(self) -> str:
        return self.channel.id if self.channel else self.user.id

    @override
    def get_user_id(self) -> str:
        return self.user.id


class PublicInteractionCommandArgvEvent(InteractionCommandArgvEvent):
    user: User  # type: ignore
    channel: Channel  # type: ignore

    @override
    def get_session_id(self) -> str:
        s = f"{self.channel.id}/{self.user.id}"
        if self.guild:
            s = f"{self.guild.id}/{s}"
        return s

    @override
    def get_user_id(self) -> str:
        return self.user.id


class InteractionCommandMessageEvent(InteractionCommandEvent):
    message: SatoriMessage  # type: ignore
    to_me: bool = False
    reply: Optional[RenderMessage] = None

    @model_validator(mode="before")
    def generate_message(cls, values):
        if isinstance(values, dict):
            values["_message"] = Message.from_satori_element(parse(values["message"]["content"]))
            values["original_message"] = deepcopy(values["_message"])
        return values

    @override
    def get_event_description(self) -> str:
        return escape_tag(f"Command interacted with {self.get_message()}")

    def convert(self):
        if self.channel and self.user and self.channel.type != ChannelType.DIRECT:
            return type_validate_python(PublicInteractionCommandMessageEvent, model_dump(self))
        if self.user:
            return type_validate_python(PrivateInteractionCommandMessageEvent, model_dump(self))
        return self


class PrivateInteractionCommandMessageEvent(InteractionCommandMessageEvent):
    user: User  # type: ignore

    @override
    def get_session_id(self) -> str:
        return self.channel.id if self.channel else self.user.id

    @override
    def get_user_id(self) -> str:
        return self.user.id


class PublicInteractionCommandMessageEvent(InteractionCommandMessageEvent):
    user: User  # type: ignore
    channel: Channel  # type: ignore

    @override
    def get_session_id(self) -> str:
        s = f"{self.channel.id}/{self.user.id}"
        if self.guild:
            s = f"{self.guild.id}/{s}"
        return s

    @override
    def get_user_id(self) -> str:
        return self.user.id
