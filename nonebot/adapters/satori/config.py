from typing import List, Optional

from yarl import URL
from pydantic import Extra, Field, BaseModel


class ClientInfo(BaseModel):
    host: str = "localhost"
    port: int
    token: Optional[str] = None

    @property
    def identity(self):
        return f"{self.host}:{self.port}#{self.token}"

    @property
    def api_base(self):
        return URL(f"http://{self.host}:{self.port}") / "v1"

    @property
    def ws_base(self):
        return URL(f"ws://{self.host}:{self.port}") / "v1"


class Config(BaseModel, extra=Extra.ignore):
    satori_clients: List[ClientInfo] = Field(default_factory=list)
    """client 配置"""
