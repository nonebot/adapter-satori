from datetime import datetime

import pytest
from nonebug import App
from nonebot.compat import type_validate_python

import nonebot
from nonebot.adapters.satori import Bot, Adapter
from nonebot.adapters.satori.event import PublicMessageCreatedEvent
from nonebot.adapters.satori.models import User, Login, LoginStatus


@pytest.mark.asyncio()
async def test_adapter(app: App):

    cmd = nonebot.on_command("test")

    @cmd.handle()
    async def handle(bot: Bot):
        await bot.send_message(channel="67890", message="hello")

    async with app.test_matcher(cmd) as ctx:
        adapter: Adapter = nonebot.get_adapter(Adapter)
        bot: Bot = ctx.create_bot(
            base=Bot,
            adapter=adapter,
            self_id="12345",
            login=Login(
                sn=0, adapter="test", status=LoginStatus.ONLINE, platform="test", user=User(id="12345", name="test")
            ),
            info=None,
            proxy_urls=[],
        )

        ctx.receive_event(
            bot,
            type_validate_python(
                PublicMessageCreatedEvent,
                {
                    "sn": 1,
                    "type": "message-created",
                    "timestamp": 1000 * int(datetime.now().timestamp()),
                    "login": {
                        "sn": 0,
                        "adapter": "test",
                        "platform": "test",
                        "status": 1,
                        "user": {
                            "id": "12345",
                            "nick": "test",
                        },
                    },
                    "channel": {
                        "id": "67890",
                        "type": 0,
                        "name": "test",
                    },
                    "user": {
                        "id": "12345",
                        "nick": "test",
                    },
                    "member": {
                        "user": {
                            "id": "12345",
                            "nick": "test",
                        },
                        "nick": "test",
                        "joined_at": 1000 * int(datetime.now().timestamp()),
                    },
                    "message": {"id": "abcde", "content": "/test"},
                },
            ),
        )
        ctx.should_call_api(
            "message_create",
            {
                "channel_id": "67890",
                "content": "hello",
            },
        )
