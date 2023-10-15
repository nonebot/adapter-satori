from enum import Enum
from copy import deepcopy
from typing_extensions import override
from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar, Optional

from pydantic import root_validator
from nonebot.utils import escape_tag

from nonebot.adapters import Event as BaseEvent

from .models import Role, User
from .models import Event as SatoriEvent
from .message import Message, RenderMessage
from .models import InnerMessage as SatoriMessage
from .models import Guild, Login, Channel, ChannelType, InnerMember

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
        return escape_tag(str(self.dict()))

    @override
    def get_message(self) -> Message:
        raise ValueError("Event has no message!")

    @override
    def get_user_id(self) -> str:
        raise ValueError("Event has no context!")

    @override
    def get_session_id(self) -> str:
        raise ValueError("Event has no context!")

    @override
    def is_tome(self) -> bool:
        return False


EVENT_CLASSES: Dict[str, Type[Event]] = {}


def register_event_class(event_class: Type[E]) -> Type[E]:
    EVENT_CLASSES[event_class.__type__.value] = event_class
    return event_class


class NoticeEvent(Event):
    @override
    def get_type(self) -> str:
        return "notice"


class FriendEvent(NoticeEvent):
    user: User

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
    guild: Guild

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


class GuildInnerMemberEvent(GuildEvent):
    member: InnerMember
    user: User

    @override
    def get_user_id(self) -> str:
        return self.user.id

    @override
    def get_session_id(self) -> str:
        return f"{self.guild.id}/{self.get_user_id()}"


@register_event_class
class GuildInnerMemberAddedEvent(GuildInnerMemberEvent):
    __type__ = EventType.GUILD_MEMBER_ADDED


@register_event_class
class GuildInnerMemberRemovedEvent(GuildInnerMemberEvent):
    __type__ = EventType.GUILD_MEMBER_REMOVED


@register_event_class
class GuildInnerMemberRequestEvent(GuildInnerMemberEvent):
    __type__ = EventType.GUILD_MEMBER_REQUEST


@register_event_class
class GuildInnerMemberUpdatedEvent(GuildInnerMemberEvent):
    __type__ = EventType.GUILD_MEMBER_UPDATED


class GuildRoleEvent(GuildEvent):
    role: Role

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
    login: Login


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
    channel: Channel
    user: User
    message: SatoriMessage
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

    @root_validator
    def generate_message(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        values["_message"] = Message.from_satori_element(values["message"].content)
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
            return PrivateMessageCreatedEvent.parse_obj(self)
        else:
            return PublicMessageCreatedEvent.parse_obj(self)


@register_event_class
class MessageDeletedEvent(MessageEvent):
    __type__ = EventType.MESSAGE_DELETED

    def convert(self):
        if self.channel.type == ChannelType.DIRECT:
            return PrivateMessageDeletedEvent.parse_obj(self)
        else:
            return PublicMessageDeletedEvent.parse_obj(self)


@register_event_class
class MessageUpdatedEvent(MessageEvent):
    __type__ = EventType.MESSAGE_UPDATED

    def convert(self):
        if self.channel.type == ChannelType.DIRECT:
            return PrivateMessageUpdatedEvent.parse_obj(self)
        else:
            return PublicMessageUpdatedEvent.parse_obj(self)


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
    member: InnerMember

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
            f"{self.user.name or ''}({self.channel.id}): {self.get_message()!r}"
        )


class PublicMessageCreatedEvent(MessageCreatedEvent, PublicMessageEvent):
    @override
    def get_event_description(self) -> str:
        return escape_tag(
            f"Message {self.msg_id} from "
            f"{self.user.name or ''}({self.channel.id})"
            f"@[{self.channel.name or ''}:{self.channel.id}]"
            f": {self.get_message()!r}"
        )


class PrivateMessageDeletedEvent(MessageDeletedEvent, PrivateMessageEvent):
    @override
    def get_event_description(self) -> str:
        return escape_tag(f"Message {self.msg_id} from " f"{self.user.name or ''}({self.channel.id}) deleted")


class PublicMessageDeletedEvent(MessageDeletedEvent, PublicMessageEvent):
    @override
    def get_event_description(self) -> str:
        return escape_tag(
            f"Message {self.msg_id} from "
            f"{self.user.name or ''}({self.channel.id})"
            f"@[{self.channel.name or ''}:{self.channel.id}] deleted"
        )


class PrivateMessageUpdatedEvent(MessageUpdatedEvent, PrivateMessageEvent):
    @override
    def get_event_description(self) -> str:
        return escape_tag(
            f"Message {self.msg_id} from "
            f"{self.user.name or ''}({self.channel.id}) updated"
            f": {self.get_message()!r}"
        )


class PublicMessageUpdatedEvent(MessageUpdatedEvent, PublicMessageEvent):
    @override
    def get_event_description(self) -> str:
        return escape_tag(
            f"Message {self.msg_id} from "
            f"{self.user.name or ''}({self.channel.id})"
            f"@[{self.channel.name or ''}:{self.channel.id}] updated"
            f": {self.get_message()!r}"
        )


class ReactionEvent(NoticeEvent):
    channel: Channel
    user: User
    message: SatoriMessage

    if TYPE_CHECKING:
        _message: Message

    @override
    def get_user_id(self) -> str:
        return self.user.id

    @override
    def get_session_id(self) -> str:
        return f"{self.channel.id}/{self.user.id}"

    @root_validator
    def generate_message(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        values["_message"] = Message.from_satori_element(values["message"]["content"])
        return values

    @property
    def msg_id(self) -> str:
        return self.message.id


@register_event_class
class ReactionAddedEvent(ReactionEvent):
    __type__ = EventType.REACTION_ADDED

    @override
    def get_event_description(self) -> str:
        return escape_tag(f"Reaction added to {self.msg_id} by {self.user.name}({self.channel.id})")


@register_event_class
class ReactionRemovedEvent(ReactionEvent):
    __type__ = EventType.REACTION_REMOVED

    @override
    def get_event_description(self) -> str:
        return escape_tag(f"Reaction removed from {self.msg_id}")
