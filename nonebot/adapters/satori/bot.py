import re
import json
from typing_extensions import override
from typing import TYPE_CHECKING, Any, Union, Literal, Optional, overload

from yarl import URL
from nonebot.message import handle_event
from nonebot.drivers import Request, Response
from nonebot.compat import model_dump, type_validate_python

from nonebot.adapters import Bot as BaseBot

from .element import parse
from .utils import API, log
from .config import ClientInfo
from .event import Event, MessageEvent
from .models import MessageObject as SatoriMessage
from .models import MessageReceipt, PageDequeResult
from .message import Author, Message, RenderMessage, MessageSegment
from .models import Meta, Role, User, Guild, Login, Order, Member, Upload, Channel, Direction, PageResult
from .exception import (
    ActionFailed,
    NetworkError,
    NotFoundException,
    ForbiddenException,
    BadRequestException,
    UnauthorizedException,
    MethodNotAllowedException,
    ApiNotImplementedException,
)

if TYPE_CHECKING:
    from .adapter import Adapter


async def _check_reply(
    bot: "Bot",
    event: MessageEvent,
) -> None:
    """检查消息中存在的回复，赋值 `event.reply`, `event.to_me`。

    参数:
        bot: Bot 对象
        event: MessageEvent 对象
    """
    message = event.get_message()
    try:
        index = message.index("quote")
    except ValueError:
        return

    msg_seg = message[index]
    del message[index]
    if TYPE_CHECKING:
        assert isinstance(msg_seg, RenderMessage)
    event.reply = msg_seg  # type: ignore
    if "content" in msg_seg.data and (author_msg := msg_seg.children.get("author")):
        author_seg = author_msg[0]
        if TYPE_CHECKING:
            assert isinstance(author_seg, Author)
        event.to_me = author_seg.data.get("id") == bot.get_self_id()
    elif "id" not in event.reply.data or not event.channel:
        return
    else:
        msg = await bot.message_get(channel_id=event.channel.id, message_id=event.reply.data["id"])
        event.reply._children = Message.from_satori_element(parse(msg.content))
        if msg.user and msg.user.id == bot.get_self_id():
            event.to_me = True
        else:
            return
    if len(message) > index and message[index].type == "at" and message[index].data.get("id") == str(bot.get_self_id()):
        event.to_me = True
        del message[index]
    if len(message) > index and message[index].type == "text":
        message[index].data["text"] = message[index].data["text"].lstrip()
        if not message[index].data["text"]:
            del message[index]
    if not message:
        message.append(MessageSegment.text(""))


def _check_at_me(
    bot: "Bot",
    event: MessageEvent,
):
    def _is_at_me_seg(segment: MessageSegment) -> bool:
        return segment.type == "at" and segment.data.get("id") == str(bot.get_self_id())

    message = event.get_message()

    # ensure message is not empty
    if not message:
        message.append(MessageSegment.text(""))

    deleted = False
    if _is_at_me_seg(message[0]):
        message.pop(0)
        event.to_me = True
        deleted = True
        if message and message[0].type == "text":
            message[0].data["text"] = message[0].data["text"].lstrip("\xa0").lstrip()
            if not message[0].data["text"]:
                del message[0]

    if not deleted:
        # check the last segment
        i = -1
        last_msg_seg = message[i]
        if last_msg_seg.type == "text" and not last_msg_seg.data["text"].strip() and len(message) >= 2:
            i -= 1
            last_msg_seg = message[i]

        if _is_at_me_seg(last_msg_seg):
            event.to_me = True
            del message[i:]

    if not message:
        message.append(MessageSegment.text(""))


def _check_nickname(bot: "Bot", event: MessageEvent) -> None:
    """检查消息开头是否存在昵称，去除并赋值 `event.to_me`。

    参数:
        bot: Bot 对象
        event: MessageEvent 对象
    """
    message = event.get_message()
    first_msg_seg = message[0]
    if first_msg_seg.type != "text":
        return

    nicknames = {re.escape(n) for n in bot.config.nickname}
    if not nicknames:
        return

    # check if the user is calling me with my nickname
    nickname_regex = "|".join(nicknames)
    first_text = first_msg_seg.data["text"]
    if m := re.search(rf"^({nickname_regex})([\s,，]*|$)", first_text, re.IGNORECASE):
        log("DEBUG", f"User is calling me {m[1]}")
        event.to_me = True
        first_msg_seg.data["text"] = first_text[m.end() :]


class Bot(BaseBot):
    adapter: "Adapter"

    @override
    def __init__(self, adapter: "Adapter", self_id: str, login: Login, info: ClientInfo, proxy_urls: list[str]):
        self._self_id: str = self_id
        # Bot 配置信息
        self.info: ClientInfo = info
        # Bot 自身所属平台
        self.platform: str = login.platform or "satori"
        # Bot 自身信息
        self._self_info: Login = login
        self.proxy_urls = proxy_urls

        super().__init__(adapter, self.identity)

    def __getattr__(self, item):
        raise AttributeError(f"'Bot' object has no attribute '{item}'")

    @property
    def identity(self):
        return f"{self.platform}:{self.get_self_id()}"

    def get_self_id(self):
        if self._self_info.user:
            return self._self_info.user.id
        return self._self_id

    @property
    def support_features(self):
        """Bot 所连接平台的支持的功能列表"""
        return self._self_info.features

    @property
    def ready(self) -> bool:
        """Bot 是否已连接"""
        return self._self_info.user is not None

    @property
    def self_info(self) -> User:
        """Bot 自身信息，仅当 Bot 连接鉴权完成后可用"""
        if self._self_info.user is None:
            raise RuntimeError(f"Bot {self._self_id} of {self.platform} is not connected!")
        return self._self_info.user

    def _update(self, login: Login) -> None:
        self._self_info = login

    def get_authorization_header(self) -> dict[str, str]:
        """获取当前 Bot 的鉴权信息"""
        header = {
            "Authorization": f"Bearer {self.info.token}",
            "X-Self-ID": self.self_info.id,
            "X-Platform": self.platform,
            "Satori-Platform": self.platform,
            "Satori-User-ID": self.self_info.id,
        }
        if not self.info.token:
            del header["Authorization"]
        return header

    async def handle_event(self, event: Event) -> None:
        if isinstance(event, MessageEvent):
            await _check_reply(self, event)
            _check_at_me(self, event)
            _check_nickname(self, event)
        await handle_event(self, event)

    @overload
    def _handle_response(self, response: Response) -> dict: ...

    @overload
    def _handle_response(self, response: Response, noreturn: Literal[True]) -> None: ...

    def _handle_response(self, response: Response, noreturn=False) -> Any:
        if 200 <= response.status_code < 300:
            if noreturn:
                return
            return json.loads(response.content) if response.content else {}
        elif response.status_code == 400:
            raise BadRequestException(response)
        elif response.status_code == 401:
            raise UnauthorizedException(response)
        elif response.status_code == 403:
            raise ForbiddenException(response)
        elif response.status_code == 404:
            raise NotFoundException(response)
        elif response.status_code == 405:
            raise MethodNotAllowedException(response)
        elif response.status_code == 500:
            raise ApiNotImplementedException(response)
        else:
            raise ActionFailed(response)

    async def _request(self, request: Request) -> Any:
        request.headers.update(self.get_authorization_header())
        request.json = {k: v for k, v in request.json.items() if v is not None} if request.json else None
        try:
            response = await self.adapter.request(request)
        except Exception as e:
            raise NetworkError("API request failed") from e

        return self._handle_response(response)

    def ensure_url(self, url: str) -> URL:
        """确定链接形式。

        若链接符合以下条件之一，则返回链接的代理形式 ({host}/{path}/{version}/proxy/{url})：
            - 链接以 "upload://" 开头
            - 链接开头出现在 self_info.proxy_urls 中的某一项
        """
        if url.startswith("upload"):
            return self.info.api_base / "proxy" / url.lstrip("/")
        for proxy_url in self.proxy_urls:
            if url.startswith(proxy_url):
                return self.info.api_base / "proxy" / url.lstrip("/")
        return URL(url)

    async def download(self, url: str) -> bytes:
        """访问内部链接。"""
        request = Request("GET", self.ensure_url(url))
        try:
            response = await self.adapter.request(request)
        except Exception as e:
            raise NetworkError("API request failed") from e

        self._handle_response(response, noreturn=True)
        return response.content  # type: ignore

    async def request_internal(self, url: str, method: str = "GET", **kwargs) -> dict:
        """访问内部链接。"""
        request = Request(method, self.ensure_url(url), **kwargs)
        try:
            response = await self.adapter.request(request)
        except Exception as e:
            raise NetworkError("API request failed") from e
        return self._handle_response(response)

    @override
    async def send(
        self,
        event: Event,
        message: Union[str, Message, MessageSegment],
        **kwargs,
    ) -> list[MessageReceipt]:
        if not event.channel:
            raise RuntimeError("Event cannot be replied to!")
        return await self.send_message(event.channel.id, message)

    async def send_message(
        self,
        channel: Union[str, Channel],
        message: Union[str, Message, MessageSegment],
    ) -> list[MessageReceipt]:
        """发送消息

        参数:
            channel (str | Channel): 要发送的频道 ID
            message (str | Message | MessageSegment): 要发送的消息
        """
        channel_id = channel.id if isinstance(channel, Channel) else channel
        return await self.message_create(channel_id=channel_id, content=str(message))

    async def send_private_message(
        self,
        user: Union[str, User],
        message: Union[str, Message, MessageSegment],
    ) -> list[MessageReceipt]:
        """发送私聊消息

        参数:
            user (str | User): 要发送的用户 ID
            message (str | Message | MessageSegment): 要发送的消息
        """
        user_id = user.id if isinstance(user, User) else user
        channel = await self.user_channel_create(user_id=user_id)
        return await self.message_create(channel_id=channel.id, content=str(message))

    async def update_message(
        self,
        channel: Union[str, Channel],
        message_id: str,
        message: Union[str, Message, MessageSegment],
    ):
        """更新消息

        参数:
            channel (str | Channel): 要更新的频道 ID
            message_id (str): 要更新的消息 ID
            message (str | Message | MessageSegment): 更新后的消息
        """
        channel_id = channel.id if isinstance(channel, Channel) else channel
        await self.message_update(channel_id=channel_id, message_id=message_id, content=str(message))

    @API
    async def message_create(
        self,
        *,
        channel_id: str,
        content: str,
    ) -> list[MessageReceipt]:
        request = Request(
            "POST",
            self.info.api_base / "message.create",
            json={"channel_id": channel_id, "content": content},
        )
        res = await self._request(request)
        return [type_validate_python(MessageReceipt, i) for i in res]

    @API
    async def message_get(self, *, channel_id: str, message_id: str) -> SatoriMessage:
        request = Request(
            "POST",
            self.info.api_base / "message.get",
            json={"channel_id": channel_id, "message_id": message_id},
        )
        res = await self._request(request)
        return type_validate_python(SatoriMessage, res)

    @API
    async def message_delete(self, *, channel_id: str, message_id: str) -> None:
        request = Request(
            "POST",
            self.info.api_base / "message.delete",
            json={"channel_id": channel_id, "message_id": message_id},
        )
        await self._request(request)

    @API
    async def message_update(
        self,
        *,
        channel_id: str,
        message_id: str,
        content: str,
    ) -> None:
        request = Request(
            "POST",
            self.info.api_base / "message.update",
            json={
                "channel_id": channel_id,
                "message_id": message_id,
                "content": content,
            },
        )
        await self._request(request)

    @API
    async def message_list(
        self,
        *,
        channel_id: str,
        next_token: Optional[str] = None,
        direction: Direction = "before",
        limit: int = 50,
        order: Order = "asc",
    ) -> PageDequeResult[SatoriMessage]:
        if not next_token and direction != "before":
            raise ValueError("Invalid direction")
        request = Request(
            "POST",
            self.info.api_base / "message.list",
            json={
                "channel_id": channel_id,
                "next": next_token,
                "direction": direction,
                "limit": limit,
                "order": order,
            },
        )
        return type_validate_python(PageDequeResult[SatoriMessage], await self._request(request))

    @API
    async def channel_get(self, *, channel_id: str) -> Channel:
        request = Request(
            "POST",
            self.info.api_base / "channel.get",
            json={"channel_id": channel_id},
        )
        res = await self._request(request)
        return type_validate_python(Channel, res)

    @API
    async def channel_list(self, *, guild_id: str, next_token: Optional[str] = None) -> PageResult[Channel]:
        request = Request(
            "POST",
            self.info.api_base / "channel.list",
            json={"guild_id": guild_id, "next": next_token},
        )
        return type_validate_python(PageResult[Channel], await self._request(request))

    @API
    async def channel_create(self, *, guild_id: str, data: Channel) -> Channel:
        request = Request(
            "POST",
            self.info.api_base / "channel.create",
            json={"guild_id": guild_id, "data": model_dump(data)},
        )
        return type_validate_python(Channel, await self._request(request))

    @API
    async def channel_update(
        self,
        *,
        channel_id: str,
        data: Channel,
    ) -> None:
        request = Request(
            "POST",
            self.info.api_base / "channel.update",
            json={"channel_id": channel_id, "data": model_dump(data)},
        )
        await self._request(request)

    @API
    async def channel_delete(self, *, channel_id: str) -> None:
        request = Request(
            "POST",
            self.info.api_base / "channel.delete",
            json={"channel_id": channel_id},
        )
        await self._request(request)

    @API
    async def channel_mute(self, *, channel_id: str, duration: float = 0) -> None:
        request = Request(
            "POST",
            self.info.api_base / "channel.mute",
            json={"channel_id": channel_id, "duration": duration},
        )
        await self._request(request)

    @API
    async def user_channel_create(self, *, user_id: str, guild_id: Optional[str] = None) -> Channel:
        data = {"user_id": user_id}
        if guild_id is not None:
            data["guild_id"] = guild_id
        request = Request(
            "POST",
            self.info.api_base / "user.channel.create",
            json=data,
        )
        return type_validate_python(Channel, await self._request(request))

    @API
    async def guild_get(self, *, guild_id: str) -> Guild:
        request = Request(
            "POST",
            self.info.api_base / "guild.get",
            json={"guild_id": guild_id},
        )
        return type_validate_python(Guild, await self._request(request))

    @API
    async def guild_list(self, *, next_token: Optional[str] = None) -> PageResult[Guild]:
        request = Request(
            "POST",
            self.info.api_base / "guild.list",
            json={"next": next_token},
        )
        return type_validate_python(PageResult[Guild], await self._request(request))

    @API
    async def guild_approve(self, *, request_id: str, approve: bool, comment: str) -> None:
        request = Request(
            "POST",
            self.info.api_base / "guild.approve",
            json={"message_id": request_id, "approve": approve, "comment": comment},
        )
        await self._request(request)

    @API
    async def guild_member_list(self, *, guild_id: str, next_token: Optional[str] = None) -> PageResult[Member]:
        request = Request(
            "POST",
            self.info.api_base / "guild.member.list",
            json={"guild_id": guild_id, "next": next_token},
        )
        return type_validate_python(PageResult[Member], await self._request(request))

    @API
    async def guild_member_get(self, *, guild_id: str, user_id: str) -> Member:
        request = Request(
            "POST",
            self.info.api_base / "guild.member.get",
            json={"guild_id": guild_id, "user_id": user_id},
        )
        return type_validate_python(Member, await self._request(request))

    @API
    async def guild_member_kick(self, *, guild_id: str, user_id: str, permanent: bool = False) -> None:
        request = Request(
            "POST",
            self.info.api_base / "guild.member.kick",
            json={"guild_id": guild_id, "user_id": user_id, "permanent": permanent},
        )
        await self._request(request)

    @API
    async def guild_member_mute(self, *, guild_id: str, user_id: str, duration: float = 0) -> None:
        request = Request(
            "POST",
            self.info.api_base / "guild.member.mute",
            json={"guild_id": guild_id, "user_id": user_id, "duration": duration},
        )
        await self._request(request)

    @API
    async def guild_member_approve(self, *, request_id: str, approve: bool, comment: str) -> None:
        request = Request(
            "POST",
            self.info.api_base / "guild.member.approve",
            json={"message_id": request_id, "approve": approve, "comment": comment},
        )
        await self._request(request)

    @API
    async def guild_member_role_set(self, *, guild_id: str, user_id: str, role_id: str) -> None:
        request = Request(
            "POST",
            self.info.api_base / "guild.member.role.set",
            json={"guild_id": guild_id, "user_id": user_id, "role_id": role_id},
        )
        await self._request(request)

    @API
    async def guild_member_role_unset(self, *, guild_id: str, user_id: str, role_id: str) -> None:
        request = Request(
            "POST",
            self.info.api_base / "guild.member.role.unset",
            json={"guild_id": guild_id, "user_id": user_id, "role_id": role_id},
        )
        await self._request(request)

    @API
    async def guild_role_list(self, guild_id: str, next_token: Optional[str] = None) -> PageResult[Role]:
        request = Request(
            "POST",
            self.info.api_base / "guild.role.list",
            json={"guild_id": guild_id, "next": next_token},
        )
        return type_validate_python(PageResult[Role], await self._request(request))

    @API
    async def guild_role_create(
        self,
        *,
        guild_id: str,
        role: Role,
    ) -> Role:
        request = Request(
            "POST",
            self.info.api_base / "guild.role.create",
            json={"guild_id": guild_id, "role": model_dump(role)},
        )
        return type_validate_python(Role, await self._request(request))

    @API
    async def guild_role_update(
        self,
        *,
        guild_id: str,
        role_id: str,
        role: Role,
    ) -> None:
        request = Request(
            "POST",
            self.info.api_base / "guild.role.update",
            json={"guild_id": guild_id, "role_id": role_id, "role": model_dump(role)},
        )
        await self._request(request)

    @API
    async def guild_role_delete(self, *, guild_id: str, role_id: str) -> None:
        request = Request(
            "POST",
            self.info.api_base / "guild.role.delete",
            json={"guild_id": guild_id, "role_id": role_id},
        )
        await self._request(request)

    @API
    async def reaction_create(
        self,
        *,
        channel_id: str,
        message_id: str,
        emoji: str,
    ) -> None:
        request = Request(
            "POST",
            self.info.api_base / "reaction.create",
            json={"channel_id": channel_id, "message_id": message_id, "emoji": emoji},
        )
        await self._request(request)

    @API
    async def reaction_delete(
        self,
        *,
        channel_id: str,
        message_id: str,
        emoji: str,
        user_id: Optional[str] = None,
    ) -> None:
        data = {"channel_id": channel_id, "message_id": message_id, "emoji": emoji}
        if user_id is not None:
            data["user_id"] = user_id
        request = Request(
            "POST",
            self.info.api_base / "reaction.delete",
            json=data,
        )
        await self._request(request)

    @API
    async def reaction_clear(
        self,
        *,
        channel_id: str,
        message_id: str,
        emoji: Optional[str] = None,
    ) -> None:
        data = {"channel_id": channel_id, "message_id": message_id}
        if emoji is not None:
            data["emoji"] = emoji
        request = Request(
            "POST",
            self.info.api_base / "reaction.clear",
            json=data,
        )
        await self._request(request)

    @API
    async def reaction_list(
        self,
        *,
        channel_id: str,
        message_id: str,
        emoji: str,
        next_token: Optional[str] = None,
    ) -> PageResult[User]:
        request = Request(
            "POST",
            self.info.api_base / "reaction.list",
            json={
                "channel_id": channel_id,
                "message_id": message_id,
                "emoji": emoji,
                "next": next_token,
            },
        )
        return type_validate_python(PageResult[User], await self._request(request))

    @API
    async def login_get(self) -> Login:
        request = Request(
            "POST",
            self.info.api_base / "login.get",
        )
        return type_validate_python(Login, await self._request(request))

    @API
    async def user_get(self, *, user_id: str) -> User:
        request = Request(
            "POST",
            self.info.api_base / "user.get",
            json={"user_id": user_id},
        )
        return type_validate_python(User, await self._request(request))

    @API
    async def friend_list(self, *, next_token: Optional[str] = None) -> PageResult[User]:
        request = Request(
            "POST",
            self.info.api_base / "friend.list",
            json={"next": next_token},
        )
        return type_validate_python(PageResult[User], await self._request(request))

    @API
    async def friend_approve(self, *, request_id: str, approve: bool, comment: str) -> None:
        request = Request(
            "POST",
            self.info.api_base / "friend.approve",
            json={"message_id": request_id, "approve": approve, "comment": comment},
        )
        await self._request(request)

    @API
    async def internal(self, *, action: str, method: str = "POST", **kwargs) -> Any:
        """内部接口调用。

        参数:
            action (str): 内部接口名称
            method (str): HTTP 请求方法, 默认为 "POST"
            **kwargs: 参数
        """
        request = Request(
            method,
            self.info.api_base / "internal" / action,
            json=kwargs,
        )
        return await self._request(request)

    async def meta_get(self) -> Meta:
        """获取元信息。返回一个 `Meta` 对象。

        Returns:
            Meta: `Meta` 对象
        """
        request = Request(
            "POST",
            self.info.api_base / "meta",
        )
        return type_validate_python(Meta, await self._request(request))

    async def webhook_create(self, url: str, token: Optional[str] = None):
        """创建 Webhook。"""
        request = Request("POST", self.info.api_base / "meta/webhook.create", json={"url": url, "token": token})
        return await self._request(request)

    async def webhook_delete(self, url: str):
        """删除 Webhook。"""
        request = Request("POST", self.info.api_base / "meta/webhook.delete", json={"url": url})
        return await self._request(request)

    @overload
    async def upload(self, *uploads: Upload) -> list[str]: ...

    @overload
    async def upload(self, **uploads: Upload) -> dict[str, str]: ...

    async def upload(self, *args: Upload, **kwargs: Upload):
        """上传文件。

        如果要发送的消息中含有图片或其他媒体资源，\
            可以使用此 API 将文件上传至 Satori 服务器并转换为 URL，以便在消息编码中使用。
        """
        if args and kwargs:
            raise RuntimeError("upload can't accept both args and kwargs")
        if args:
            ids = []
            for upload in args:
                ids.append(str(id(upload)))

            resp = await self.upload_create(**dict(zip(ids, args)))
            return list(resp.values())
        return await self.upload_create(**kwargs)

    @API
    async def upload_create(self, **kwargs: Upload) -> dict[str, str]:
        request = Request("POST", self.info.api_base / "upload.create", files={k: v.dump() for k, v in kwargs.items()})
        return await self._request(request)
