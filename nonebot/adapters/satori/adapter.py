import json
import asyncio
from collections import defaultdict
from typing_extensions import override
from typing import Any, Literal, Optional

from nonebot.utils import escape_tag
from nonebot.exception import WebSocketClosed
from nonebot.compat import PYDANTIC_V2, model_dump, type_validate_python
from nonebot.drivers import Driver, Request, WebSocket, HTTPClientMixin, WebSocketClientMixin

from nonebot import get_plugin_config
from nonebot.adapters import Adapter as BaseAdapter

from .bot import Bot
from .utils import API, log
from .config import Config, ClientInfo
from .exception import ApiNotAvailable
from .models import Event as SatoriEvent
from .event import (
    EVENT_CLASSES,
    Event,
    MessageEvent,
    LoginAddedEvent,
    InteractionEvent,
    LoginRemovedEvent,
    LoginUpdatedEvent,
)
from .models import (
    Opcode,
    Payload,
    Identify,
    LoginStatus,
    MetaPayload,
    PayloadType,
    PingPayload,
    PongPayload,
    EventPayload,
    ReadyPayload,
    IdentifyPayload,
)


class Adapter(BaseAdapter):
    bots: dict[str, Bot]

    @override
    def __init__(self, driver: Driver, **kwargs: Any):
        super().__init__(driver, **kwargs)
        # 读取适配器所需的配置项
        self.satori_config: Config = get_plugin_config(Config)
        self.tasks: set[asyncio.Task] = set()  # 存储 ws 任务等
        self.sequences: dict[str, int] = {}  # 存储 连接序列号
        self.proxys: dict[str, list[str]] = {}  # 存储 proxy_url
        self._bots: defaultdict[str, set[str]] = defaultdict(set)  # 存储 identity 和 bot_id 的映射
        self.setup()

    @classmethod
    @override
    def get_name(cls) -> str:
        """适配器名称"""
        return "Satori"

    def setup(self) -> None:
        if not isinstance(self.driver, HTTPClientMixin):
            # 判断用户配置的Driver类型是否符合适配器要求，不符合时应抛出异常
            raise RuntimeError(
                f"Current driver {self.config.driver} "
                f"doesn't support http client requests!"
                f"{self.get_name()} Adapter need a HTTPClient Driver to work."
            )
        if not isinstance(self.driver, WebSocketClientMixin):
            raise RuntimeError(
                f"Current driver {self.config.driver} does not support "
                "websocket client! "
                f"{self.get_name()} Adapter need a WebSocketClient Driver to work."
            )
        # 在 NoneBot 启动和关闭时进行相关操作
        self.on_ready(self.startup)
        self.driver.on_shutdown(self.shutdown)

    async def startup(self) -> None:
        """定义启动时的操作，例如和平台建立连接"""
        for client in self.satori_config.satori_clients:
            t = asyncio.create_task(self.ws(client))
            self.tasks.add(t)
            t.add_done_callback(self.tasks.discard)

    async def shutdown(self) -> None:
        for task in self.tasks:
            if not task.done():
                task.cancel()

        await asyncio.gather(
            *(asyncio.wait_for(task, timeout=10) for task in self.tasks),
            return_exceptions=True,
        )
        self.tasks.clear()
        self.sequences.clear()
        self._bots.clear()

    @staticmethod
    def payload_to_json(payload: Payload) -> str:
        if PYDANTIC_V2:
            return payload.model_dump_json(by_alias=True)
        return payload.json(by_alias=True)

    async def receive_payload(self, info: ClientInfo, ws: WebSocket) -> Payload:
        data = json.loads(await ws.receive())
        payload = type_validate_python(PayloadType, data)
        if isinstance(payload, EventPayload):
            self.sequences[info.identity] = payload.body["id"]
        return payload

    async def _authenticate(self, info: ClientInfo, ws: WebSocket) -> Optional[Literal[True]]:
        """鉴权连接"""
        payload = IdentifyPayload(
            op=Opcode.IDENTIFY,
            body=Identify(
                token=info.token,
            ),
        )
        if info.identity in self.sequences:
            payload.body.sn = self.sequences[info.identity]

        try:
            await ws.send(self.payload_to_json(payload))
        except Exception as e:
            log(
                "ERROR",
                "<r><bg #f8bbd0>Error while sending " + "Identify event</bg #f8bbd0></r>",
                e,
            )
            return

        resp = await self.receive_payload(info, ws)
        if not isinstance(resp, ReadyPayload):
            log(
                "ERROR",
                "Received unexpected payload while authenticating: " f"{escape_tag(repr(resp))}",
            )
            return
        for login in resp.body.logins:
            if not login.user:
                continue
            if login.identity not in self.bots:
                bot = Bot(self, login.user.id, login, info, resp.body.proxy_urls)
                self._bots[info.identity].add(bot.identity)
                self.bot_connect(bot)
                log("INFO", f"<y>Bot {bot.identity}</y> connected")
            else:
                bot = self.bots[login.identity]
                self._bots[info.identity].add(bot.identity)
                bot._update(login)
        if not self.bots:
            log("WARNING", "No bots connected!")
        self.proxys[info.identity] = resp.body.proxy_urls
        return True

    async def _heartbeat(self, info: ClientInfo, ws: WebSocket):
        """心跳"""
        while True:
            log("TRACE", f"Heartbeat {self.sequences.get(info.identity, 0)}")
            payload = PingPayload(op=Opcode.PING, body={})
            try:
                await ws.send(self.payload_to_json(payload))
            except Exception as e:
                log("WARNING", "Error while sending heartbeat, Ignored!", e)
            await asyncio.sleep(9)

    async def ws(self, info: ClientInfo) -> None:
        ws_url = info.ws_base / "events"
        req = Request("GET", ws_url, timeout=60.0)
        heartbeat_task: Optional["asyncio.Task"] = None
        while True:
            try:
                async with self.websocket(req) as ws:
                    log(
                        "DEBUG",
                        f"WebSocket Connection to " f"{escape_tag(str(ws_url))} established",
                    )
                    try:
                        if not await self._authenticate(info, ws):
                            await asyncio.sleep(3)
                            continue
                        heartbeat_task = asyncio.create_task(self._heartbeat(info, ws))
                        self.tasks.add(heartbeat_task)
                        heartbeat_task.add_done_callback(self.tasks.discard)
                        await self._loop(info, ws)
                    except WebSocketClosed as e:
                        log(
                            "ERROR",
                            "<r><bg #f8bbd0>WebSocket Closed</bg #f8bbd0></r>",
                            e,
                        )
                    except Exception as e:
                        log(
                            "ERROR",
                            "<r><bg #f8bbd0>Error while process data from websocket "
                            f"{escape_tag(str(ws_url))}. "
                            f"Trying to reconnect...</bg #f8bbd0></r>",
                            e,
                        )
                    finally:
                        if heartbeat_task:
                            heartbeat_task.cancel()
                            heartbeat_task = None
                        bots = [self.bots[bot_id] for bot_id in self._bots[info.identity]]
                        for bot in bots:
                            self.bot_disconnect(bot)
                        bots.clear()
                        self._bots[info.identity].clear()
            except Exception as e:
                log(
                    "ERROR",
                    (
                        "<r><bg #f8bbd0>"
                        "Error while setup websocket to "
                        f"{escape_tag(str(ws_url))}. Trying to reconnect..."
                        "</bg #f8bbd0></r>"
                    ),
                    e,
                )
                await asyncio.sleep(3)  # 重连间隔

    async def _loop(self, info: ClientInfo, ws: WebSocket):
        while True:
            payload = await self.receive_payload(info, ws)
            log(
                "TRACE",
                f"Received payload: {escape_tag(repr(payload))}",
            )
            if isinstance(payload, EventPayload):
                try:
                    event = self.payload_to_event(type_validate_python(Event, payload.body))
                except Exception as e:
                    log(
                        "WARNING",
                        f"Failed to parse event {escape_tag(repr(payload))}",
                        e if payload.body["type"] != "internal" else None,
                    )
                else:
                    if isinstance(event, LoginAddedEvent):
                        login = event.login
                        if not login.user:
                            log("WARNING", f"Received login-added event without user: {login}")
                            continue
                        bot = Bot(self, login.user.id, login, info, self.proxys[info.identity])
                        self._bots[info.identity].add(bot.self_id)
                        self.bot_connect(bot)
                        log("INFO", f"<y>Bot {bot.self_id}</y> connected")
                    elif isinstance(event, LoginRemovedEvent):
                        login = event.login
                        if not login.user:
                            log("WARNING", f"Received login-removed event without user: {login}")
                            continue
                        bot = self.bots.get(login.identity)
                        if bot:
                            self.bot_disconnect(bot)
                            self._bots[info.identity].discard(bot.self_id)
                            log("INFO", f"<y>Bot {bot.self_id}</y> disconnected")
                        else:
                            log(
                                "WARNING",
                                f"Received login-removed event for unknown bot {login}",
                            )
                            continue
                    elif isinstance(event, LoginUpdatedEvent):
                        login = event.login
                        if not login.user:
                            log("WARNING", f"Received login-updated event without user: {login}")
                            continue
                        bot = self.bots.get(login.identity)
                        if bot:
                            bot._update(login)
                        else:
                            if login.status != LoginStatus.ONLINE:
                                log(
                                    "WARNING",
                                    f"Received login-updated event for unknown bot {login}",
                                )
                                continue
                            bot = Bot(self, login.user.id, login, info, self.proxys[info.identity])
                            self._bots[info.identity].add(bot.self_id)
                            self.bot_connect(bot)
                            log("INFO", f"<y>Bot {bot.self_id}</y> connected")
                    else:
                        bot = self.bots.get(event.login.identity)
                        if not bot:
                            log("WARNING", f"Received event for unknown bot {event.login}")
                            continue

                    if isinstance(event, (MessageEvent, InteractionEvent)):
                        event = event.convert()
                    _t = asyncio.create_task(bot.handle_event(event))
                    self.tasks.add(_t)
                    _t.add_done_callback(self.tasks.discard)
            elif isinstance(payload, PongPayload):
                log("TRACE", "Pong")
                continue
            elif isinstance(payload, MetaPayload):
                log("TRACE", f"Meta: {payload.body}")
                self.proxys[info.identity] = payload.body.proxy_urls
                for bot_id in self._bots[info.identity]:
                    bot = self.bots[bot_id]
                    bot.proxy_urls = payload.body.proxy_urls
            else:
                log(
                    "WARNING",
                    f"Unknown payload from server: {escape_tag(repr(payload))}",
                )

    @staticmethod
    def payload_to_event(payload: SatoriEvent) -> Event:
        EventClass = EVENT_CLASSES.get(payload.type, None)
        if EventClass is None:
            log("WARNING", f"Unknown payload type: {payload.type}")
            event = type_validate_python(Event, model_dump(payload))
            event.__type__ = payload.type  # type: ignore
            return event
        return type_validate_python(EventClass, model_dump(payload))

    @override
    async def _call_api(self, bot: Bot, api: str, **data: Any) -> Any:
        log("DEBUG", f"Bot {bot.identity} calling API <y>{api}</y>")
        api_handler: Optional[API] = getattr(bot.__class__, api, None)
        if api_handler is None:
            raise ApiNotAvailable(api)
        return await api_handler(bot, **data)
