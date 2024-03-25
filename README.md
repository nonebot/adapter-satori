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
```

或

```dotenv
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

`token` 由 Satori 服务端决定是否需要 (例如，对接 Chronocat 就需要此项)。

### 以对接 Chronocat 为例

你需要从 Chronocat 的配置文件 `~/.chronocat/config/chronocat.yml` 中获取 `port`、`token`、`host`。

在单账号下，
- `host` 与配置文件下的 `servers[X].listen` 一致
- `port` 与配置文件下的 `servers[X].port` 一致
- `token` 与配置文件下的 `servers[X].token` 一致

```yaml
# ~/.chronocat/config/chronocat.yml
servers:
  - type: satori
    # Chronocat 已经自动生成了随机 token。要妥善保存哦！
    # 客户端使用服务时需要提供这个 token！
    token: DEFINE_CHRONO_TOKEN  # token
    # Chronocat 开启 satori 服务的端口，默认为 5500。
    port: 5500  # port
    # 服务器监听的地址。 如果你不知道这是什么，那么不填此项即可！
    listen: localhost  # host
```

而多账号下，
- `host` 与配置文件下下的 `overrides[QQ].servers[X].listen` 一致
- `port` 与配置文件下下的 `overrides[QQ].servers[X].port` 一致，并且一个 `QQ` 只能对应一个 `port`
- `token` 与配置文件下下的 `overrides[QQ].servers[X].token` 一致

```yaml
# ~/.chronocat/config/chronocat.yml
overrides:
  1234567890:
    servers:
      - type: satori
        # Chronocat 已经自动生成了随机 token。要妥善保存哦！
        # 客户端使用服务时需要提供这个 token！
        token: DEFINE_CHRONO_TOKEN  # token
        # Chronocat 开启 satori 服务的端口，默认为 5500。
        port: 5501  # port
        # 服务器监听的地址。 如果你不知道这是什么，那么不填此项即可！
        listen: localhost
```

配置文件详细内容请参考 [Chronocat/config](https://chronocat.vercel.app/guide/config/)。

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
