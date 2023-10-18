import re
from functools import partial
from typing_extensions import ParamSpec, Concatenate
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Type,
    Union,
    Generic,
    TypeVar,
    Callable,
    Optional,
    Awaitable,
    overload,
)

from pydantic import Field, BaseModel
from nonebot.utils import logger_wrapper

if TYPE_CHECKING:
    from .bot import Bot

B = TypeVar("B", bound="Bot")
R = TypeVar("R")
P = ParamSpec("P")
log = logger_wrapper("Satori")


def escape(text: str) -> str:
    return text.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def unescape(text: str) -> str:
    return text.replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


class Element(BaseModel):
    type: str
    attrs: Dict[str, Any] = Field(default_factory=dict)
    children: List["Element"] = Field(default_factory=list)
    source: Optional[str] = None

    def __str__(self):
        if self.source:
            return self.source
        if self.type == "text":
            return escape(self.attrs["text"])

        def _attr(key: str, value: Any):
            if value is True:
                return key
            if value is False:
                return f"no-{key}"
            if isinstance(value, (int, float)):
                return f"{key}={value}"
            return f'{key}="{escape(str(value))}"'

        attrs = " ".join(_attr(k, v) for k, v in self.attrs.items())
        if not self.children:
            return f"<{self.type} {attrs}/>"
        children = "".join(str(c) for c in self.children)
        return f"<{self.type} {attrs}>{children}</{self.type}>"


tag_pat = re.compile(r"<!--[\s\S]*?-->|<(/?)([^!\s>/]*)([^>]*?)\s*(/?)>")
attr_pat = re.compile(r"([^\s=]+)(?:=\"([^\"]*)\"|='([^']*)')?", re.S)


class Token(BaseModel):
    type: str
    close: str
    empty: str
    attrs: Dict[str, Any]
    source: str


def parse(src: str):
    tokens: List[Union[Token, Element]] = []

    def push_text(text: str):
        if text:
            tokens.append(Element(type="text", attrs={"text": text}))

    def parse_content(source: str):
        push_text(unescape(source))

    while tag_map := tag_pat.search(src):
        parse_content(src[: tag_map.start()])
        src = src[tag_map.end() :]
        if tag_map.group(0).startswith("<!--"):
            continue
        close, tag, attr_str, empty = tag_map.groups()
        tkn = Token(
            type=tag or "template",
            close=close,
            empty=empty,
            attrs={},
            source=tag_map.group(0),
        )
        while attr_map := attr_pat.search(attr_str):
            key, value1, value2 = attr_map.groups()
            value = value1 or value2
            if value:
                tkn.attrs[key] = unescape(value)
            elif key.startswith("no-"):
                tkn.attrs[key] = False
            else:
                tkn.attrs[key] = True
            attr_str = attr_str[attr_map.end() :]
        tokens.append(tkn)

    parse_content(src)

    stack = [Element(type="template")]

    def rollback(i: int):
        while i:
            child = stack.pop(0)
            source = stack[0].children.pop(-1)
            stack[0].children.append(Element(type="text", attrs={"text": source}))
            stack[0].children.extend(child.children)
            i -= 1

    for tkn in tokens:
        if isinstance(tkn, Element):
            stack[0].children.append(tkn)
        elif tkn.close:
            index = 0
            while index < len(stack) and stack[index].type != tkn.type:
                index += 1
            if index == len(stack):
                stack[0].children.append(Element(type="text", attrs={"text": tkn.source}))
            else:
                rollback(index)
                elm = stack.pop(0)
                elm.source = None
        else:
            elm = Element(type=tkn.type, attrs=tkn.attrs)
            stack[0].children.append(elm)
            if not tkn.empty:
                elm.source = tkn.source
                stack.insert(0, elm)

    rollback(len(stack) - 1)
    return stack[0].children


class API(Generic[B, P, R]):
    def __init__(self, func: Callable[Concatenate[B, P], Awaitable[R]]) -> None:
        self.func = func

    def __set_name__(self, owner: Type[B], name: str) -> None:
        self.name = name

    @overload
    def __get__(self, obj: None, objtype: Type[B]) -> "API[B, P, R]":
        ...

    @overload
    def __get__(self, obj: B, objtype: Optional[Type[B]]) -> Callable[P, Awaitable[R]]:
        ...

    def __get__(
        self, obj: Optional[B], objtype: Optional[Type[B]] = None
    ) -> "API[B, P, R] | Callable[P, Awaitable[R]]":
        if obj is None:
            return self

        return partial(obj.call_api, self.name)  # type: ignore

    async def __call__(self, inst: B, *args: P.args, **kwds: P.kwargs) -> R:
        return await self.func(inst, *args, **kwds)
