from enum import IntEnum
from datetime import datetime
from typing import Any, Dict, List, Union, Literal, Optional

from pydantic import Field, BaseModel, validator

from .utils import Element, parse


class ChannelType(IntEnum):
    TEXT = 0
    VOICE = 1
    CATEGORY = 2
    DIRECT = 3


class Channel(BaseModel):
    id: str
    name: str
    type: ChannelType
    parent_id: Optional[str] = None


class Guild(BaseModel):
    id: str
    name: str
    avatar: Optional[str] = None


class User(BaseModel):
    id: str
    name: Optional[str] = None
    avatar: Optional[str] = None
    is_bot: Optional[bool] = None


class InnerMember(BaseModel):
    user: Optional[User] = None
    name: Optional[str] = None
    avatar: Optional[str] = None
    joined_at: Optional[datetime] = None

    @validator("joined_at", pre=True)
    def parse_joined_at(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        try:
            timestamp = int(v)
        except ValueError:
            raise ValueError(f"invalid timestamp: {v}")
        return datetime.fromtimestamp(timestamp / 1000)


class OuterMember(InnerMember):
    user: User
    joined_at: datetime


class Role(BaseModel):
    id: str
    name: str


class LoginStatus(IntEnum):
    OFFLINE = 0
    ONLINE = 1
    CONNECT = 2
    DISCONNECT = 3
    RECONNECT = 4


class InnerLogin(BaseModel):
    user: Optional[User] = None
    self_id: Optional[str] = None
    platform: Optional[str] = None
    status: LoginStatus


class OuterLogin(InnerLogin):
    user: User
    self_id: str
    platform: str


class Opcode(IntEnum):
    EVENT = 0
    PING = 1
    PONG = 2
    IDENTIFY = 3
    READY = 4


class Payload(BaseModel):
    op: Opcode = Field(...)
    body: Optional[Dict[str, Any]] = Field(None)


class Identify(BaseModel):
    token: Optional[str] = None
    sequence: Optional[int] = None


class Ready(BaseModel):
    logins: List[OuterLogin]


class IdentifyPayload(Payload):
    op: Literal[Opcode.IDENTIFY] = Field(Opcode.IDENTIFY)
    body: Identify


class ReadyPayload(Payload):
    op: Literal[Opcode.READY] = Field(Opcode.READY)
    body: Ready


class PingPayload(Payload):
    op: Literal[Opcode.PING] = Field(Opcode.PING)


class PongPayload(Payload):
    op: Literal[Opcode.PONG] = Field(Opcode.PONG)


class InnerMessage(BaseModel):
    id: str
    content: Optional[List[Element]] = None
    channel: Optional[Channel] = None
    guild: Optional[Guild] = None
    member: Optional[InnerMember] = None
    user: Optional[User] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @validator("content", pre=True)
    def parse_content(cls, v):
        if isinstance(v, list):
            return v
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("content must be str")
        return parse(v)

    @validator("created_at", pre=True)
    def parse_created_at(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        try:
            timestamp = int(v)
        except ValueError:
            raise ValueError(f"invalid timestamp: {v}")
        return datetime.fromtimestamp(timestamp / 1000)

    @validator("updated_at", pre=True)
    def parse_updated_at(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        try:
            timestamp = int(v)
        except ValueError:
            raise ValueError(f"invalid timestamp: {v}")
        return datetime.fromtimestamp(timestamp / 1000)


class OuterMessage(InnerMessage):
    channel: Channel
    guild: Guild
    member: InnerMember
    user: User
    created_at: datetime
    updated_at: datetime


class Event(BaseModel):
    id: int
    type: str
    platform: str
    self_id: str
    timestamp: datetime
    channel: Optional[Channel] = None
    guild: Optional[Guild] = None
    login: Optional[InnerLogin] = None
    member: Optional[InnerMember] = None
    message: Optional[InnerMessage] = None
    operator: Optional[User] = None
    role: Optional[Role] = None
    user: Optional[User] = None

    @validator("timestamp", pre=True)
    def parse_timestamp(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        try:
            timestamp = int(v)
        except ValueError:
            raise ValueError(f"invalid timestamp: {v}")
        return datetime.fromtimestamp(timestamp / 1000)


class EventPayload(Payload):
    op: Literal[Opcode.EVENT] = Field(Opcode.EVENT)
    body: Event


PayloadType = Union[
    Union[EventPayload, PingPayload, PongPayload, IdentifyPayload, ReadyPayload],
    Payload,
]
