# import threading
from typing import Any
from pathlib import Path

import pytest

# from nonebot.drivers import URL
# from fake_server import request_handler
from nonebug import NONEBOT_INIT_KWARGS
from pytest_asyncio import is_async_test

import nonebot
import nonebot.adapters

# from collections.abc import Generator

# from werkzeug.serving import BaseWSGIServer, make_server


nonebot.adapters.__path__.append(str((Path(__file__).parent.parent / "nonebot" / "adapters").resolve()))  # type: ignore

from nonebot.adapters.satori import Adapter as SatoriAdapter


def pytest_configure(config: pytest.Config) -> None:
    config.stash[NONEBOT_INIT_KWARGS] = {
        "driver": "~httpx+~websockets",
        "log_level": "DEBUG",
        # "satori_clients": [{"host": "localhost", "port": "5500", "path": "", "token": "test_token"}],
    }


def pytest_collection_modifyitems(items: Any):
    pytest_asyncio_tests = (item for item in items if is_async_test(item))
    session_scope_marker = pytest.mark.asyncio(loop_scope="session")
    for async_test in pytest_asyncio_tests:
        async_test.add_marker(session_scope_marker, append=False)


@pytest.fixture(scope="session", autouse=True)
async def after_nonebot_init(after_nonebot_init: None):
    driver = nonebot.get_driver()
    driver.register_adapter(SatoriAdapter)


# @pytest.fixture(scope="session", autouse=True)
# def server() -> Generator[BaseWSGIServer, None, None]:
#     server = make_server("127.0.0.1", 5500, app=request_handler)
#     thread = threading.Thread(target=server.serve_forever)
#     thread.start()
#     try:
#         yield server
#     finally:
#         server.shutdown()
#         thread.join()


# @pytest.fixture(scope="session")
# def server_url(server: BaseWSGIServer) -> URL:
#     return URL(f"http://{server.host}:{server.port}")
