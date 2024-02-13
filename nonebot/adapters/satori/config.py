from typing import List, Optional

from yarl import URL
from pydantic import Field, BaseModel


class ClientInfo(BaseModel):
    host: str = "localhost"
    """服务端的地址"""
    port: int
    """服务端的端口"""
    path: str = ""
    """服务端的自定义路径"""
    token: Optional[str] = None
    """服务端的 token"""

    @property
    def identity(self):
        return f"{self.host}:{self.port}#{self.token}"

    @property
    def api_base(self):
        return URL(f"http://{self.host}:{self.port}") / self.path.lstrip("/") / "v1"

    @property
    def ws_base(self):
        return URL(f"ws://{self.host}:{self.port}") / self.path.lstrip("/") / "v1"


class Config(BaseModel):
    satori_clients: List[ClientInfo] = Field(default_factory=list)
    """client 配置"""
