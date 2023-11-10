<div align="center">

# NoneBot-Adapter-Satori

_✨ NoneBot2 Satori Protocol适配器 / Satori Protocol Adapter for NoneBot2 ✨_

</div>

## 协议介绍

[Satori Protocol](https://satori.js.org/zh-CN/)

### 协议端

目前提供了 `satori` 协议实现的有：
- [Chronocat](https://chronocat.vercel.app)
- Koishi （搭配 `@koishijs/plugin-server`）

## 配置

修改 NoneBot 配置文件 `.env` 或者 `.env.*`。

### Driver

参考 [driver](https://nonebot.dev/docs/appendices/config#driver) 配置项，添加 `HTTPClient` 和 `WebSocketClient` 支持。

如：

```dotenv
DRIVER=~httpx+~websockets
DRIVER=~aiohttp
```

### SATORI_CLIENTS

配置连接配置，如：

```dotenv
SATORI_CLIENTS='
[
  {
    "host": "localhost",
    "port": "5500",
    "path": "",
    "token": "xxx"
  }
]
'
```

`host` 与 `port` 为 Satori 服务端的监听地址与端口，

`path` 为 Satori 服务端自定义的监听路径，如 `"/satori"`，默认为 `""`

`token` 由 Satori 服务端决定是否需要。


## 示例

```python
from nonebot import on_command
from nonebot.adapters.satori import Bot
from nonebot.adapters.satori.event import MessageEvent
from nonebot.adapters.satori.message import MessageSegment


matcher = on_command("test")

@matcher.handle()
async def handle_receive(bot: Bot, event: MessageEvent):
    if event.is_private:
        await bot.send(event, MessageSegment.text("Hello, world!"))
```
