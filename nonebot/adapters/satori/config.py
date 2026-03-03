from yarl import URL
from pydantic import Field, BaseModel


class ClientInfo(BaseModel):
    host: str = "localhost"
    """服务端的地址"""
    port: int
    """服务端的端口"""
    path: str = ""
    """服务端的自定义路径"""
    token: str | None = None
    """服务端的 token"""
    timeout: float | None = None
    """API 请求超时时间"""
    secure: bool = False
    """是否使用 https 和 wss 连接"""

    @property
    def identity(self):
        return f"{self.host}:{self.port}#{self.token}"

    @property
    def api_base(self):
        return URL(f"http{'s' if self.secure else ''}://{self.host}:{self.port}") / self.path.lstrip("/") / "v1"

    @property
    def ws_base(self):
        return URL(f"ws{'s' if self.secure else ''}://{self.host}:{self.port}") / self.path.lstrip("/") / "v1"


class Config(BaseModel):
    satori_clients: list[ClientInfo] = Field(default_factory=list)
    """client 配置"""
