import asyncio

import pytest
from nonebug import App
from fake_server import ws_handlers

import nonebot
from nonebot.adapters.satori import Adapter


@pytest.mark.asyncio
async def test_ws(app: App):
    adapter: Adapter = nonebot.get_adapter(Adapter)

    for client in adapter.satori_config.satori_clients:
        adapter.tasks.append(asyncio.create_task(adapter.ws(client)))

    @ws_handlers.put
    def identify(json: dict) -> dict:
        assert json["op"] == 3
        assert json["body"]["token"] == "test_token"
        return {
            "op": 4,
            "body": {
                "logins": [
                    {
                        "user": {
                            "id": "0",
                            "nick": "test",
                        },
                        "self_id": "0",
                        "platform": "test",
                        "status": 1,
                    }
                ]
            },
        }

    await asyncio.sleep(5)
    bots = nonebot.get_bots()
    assert "0" in bots
    await adapter.shutdown()
    assert "0" not in nonebot.get_bots()
