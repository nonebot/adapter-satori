from datetime import datetime

import pytest
from nonebug import App
from nonebot.compat import type_validate_python

import nonebot
from nonebot.adapters.satori import Bot, Adapter
from nonebot.adapters.satori.event import PublicMessageCreatedEvent


@pytest.mark.asyncio
async def test_adapter(app: App):

    cmd = nonebot.on_command("test")

    @cmd.handle()
    async def handle(bot: Bot):
        await bot.send_message(
            channel_id="67890",
            message="hello",
        )

    async with app.test_matcher(cmd) as ctx:
        adapter: Adapter = nonebot.get_adapter(Adapter)
        bot: Bot = ctx.create_bot(base=Bot, adapter=adapter, self_id="0", platform="test", info=None)

        ctx.receive_event(
            bot,
            type_validate_python(
                PublicMessageCreatedEvent,
                {
                    "id": 1,
                    "type": "message-created",
                    "platform": "test",
                    "self_id": "0",
                    "timestamp": 1000 * int(datetime.now().timestamp()),
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
