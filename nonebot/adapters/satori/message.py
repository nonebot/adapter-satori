import re
from io import BytesIO
from pathlib import Path
from base64 import b64encode
from dataclasses import InitVar, field, dataclass
from typing_extensions import NotRequired, override
from typing import Any, List, Type, Union, Iterable, Optional, TypedDict

from nonebot.adapters import Message as BaseMessage
from nonebot.adapters import MessageSegment as BaseMessageSegment

from .element import Element, parse, escape, param_case


class MessageSegment(BaseMessageSegment["Message"]):
    def __str__(self) -> str:
        def _attr(key: str, value: Any):
            if value is None:
                return ""
            key = param_case(key)
            if value is True:
                return f" {key}"
            if value is False:
                return f" no-{key}"
            return f' {key}="{escape(str(value), True)}"'

        attrs = "".join(_attr(k, v) for k, v in self.data.items())
        if self.type == "text" and "text" in self.data:
            return escape(self.data["text"])
        return f"<{self.type}{attrs}/>"

    @classmethod
    @override
    def get_message_class(cls) -> Type["Message"]:
        return Message

    @staticmethod
    def text(content: str) -> "Text":
        return Text("text", {"text": content})

    @staticmethod
    def at(
        user_id: str,
        name: Optional[str] = None,
    ) -> "At":
        data = {"id": user_id}
        if name:
            data["name"] = name
        return At("at", data)  # type: ignore

    @staticmethod
    def at_role(
        role: str,
        name: Optional[str] = None,
    ) -> "At":
        data = {"role": role}
        if name:
            data["name"] = name
        return At("at_role", data)  # type: ignore

    @staticmethod
    def at_all(here: bool = False) -> "At":
        return At("at", {"type": "here" if here else "all"})

    @staticmethod
    def sharp(channel_id: str, name: Optional[str] = None) -> "Sharp":
        data = {"id": channel_id}
        if name:
            data["name"] = name
        return Sharp("sharp", data)  # type: ignore

    @staticmethod
    def link(href: str, display: Optional[str] = None) -> "Link":
        if display:
            return Link("link", {"text": href, "display": display})
        return Link("link", {"text": href})

    @staticmethod
    def image(
        url: Optional[str] = None,
        path: Optional[Union[str, Path]] = None,
        raw: Optional[Union[bytes, BytesIO]] = None,
        mime: Optional[str] = None,
        extra: Optional[dict] = None,
        cache: Optional[bool] = None,
        timeout: Optional[str] = None,
    ) -> "Image":
        if url:
            data = {"src": url}
        elif path:
            data = {"src": Path(path).absolute().as_uri()}
        elif raw and mime:
            bd = raw["data"] if isinstance(raw, bytes) else raw.getvalue()  # type: ignore
            data = {"src": f"data:{mime};base64,{b64encode(bd).decode()}"}
        else:
            raise ValueError("image need at least one of url, path and raw")
        if cache is not None:
            data["cache"] = cache  # type: ignore
        if timeout is not None:
            data["timeout"] = timeout
        return Image("img", data, extra=extra)  # type: ignore

    @staticmethod
    def audio(
        url: Optional[str] = None,
        path: Optional[Union[str, Path]] = None,
        raw: Optional[Union[bytes, BytesIO]] = None,
        mime: Optional[str] = None,
        extra: Optional[dict] = None,
        cache: Optional[bool] = None,
        timeout: Optional[str] = None,
    ) -> "Audio":
        if url:
            data = {"src": url}
        elif path:
            data = {"src": Path(path).absolute().as_uri()}
        elif raw and mime:
            bd = raw["data"] if isinstance(raw, bytes) else raw.getvalue()  # type: ignore
            data = {"src": f"data:{mime};base64,{b64encode(bd).decode()}"}
        else:
            raise ValueError("audio need at least one of url, path and raw")
        if cache is not None:
            data["cache"] = cache  # type: ignore
        if timeout is not None:
            data["timeout"] = timeout
        return Audio("audio", data, extra=extra)  # type: ignore

    @staticmethod
    def video(
        url: Optional[str] = None,
        path: Optional[Union[str, Path]] = None,
        raw: Optional[Union[bytes, BytesIO]] = None,
        mime: Optional[str] = None,
        extra: Optional[dict] = None,
        cache: Optional[bool] = None,
        timeout: Optional[str] = None,
    ) -> "Video":
        if url:
            data = {"src": url}
        elif path:
            data = {"src": Path(path).absolute().as_uri()}
        elif raw and mime:
            bd = raw["data"] if isinstance(raw, bytes) else raw.getvalue()  # type: ignore
            data = {"src": f"data:{mime};base64,{b64encode(bd).decode()}"}
        else:
            raise ValueError("video need at least one of url, path and raw")
        if cache is not None:
            data["cache"] = cache  # type: ignore
        if timeout is not None:
            data["timeout"] = timeout
        return Video("video", data, extra=extra)  # type: ignore

    @staticmethod
    def file(
        url: Optional[str] = None,
        path: Optional[Union[str, Path]] = None,
        raw: Optional[Union[bytes, BytesIO]] = None,
        mime: Optional[str] = None,
        extra: Optional[dict] = None,
        cache: Optional[bool] = None,
        timeout: Optional[str] = None,
    ) -> "File":
        if url:
            data = {"src": url}
        elif path:
            data = {"src": Path(path).absolute().as_uri()}
        elif raw and mime:
            bd = raw["data"] if isinstance(raw, bytes) else raw.getvalue()  # type: ignore
            data = {"src": f"data:{mime};base64,{b64encode(bd).decode()}"}
        else:
            raise ValueError("file need at least one of url, path and raw")
        if cache is not None:
            data["cache"] = cache  # type: ignore
        if timeout is not None:
            data["timeout"] = timeout
        return File("file", data, extra=extra)  # type: ignore

    @staticmethod
    def message(
        mid: Optional[str] = None,
        forward: Optional[bool] = None,
        content: Optional["Message"] = None,
    ) -> "RenderMessage":
        data = {}
        if mid:
            data["id"] = mid
        if forward is not None:
            data["forward"] = forward
        if content:
            data["content"] = content
        return RenderMessage("message", data)  # type: ignore

    @staticmethod
    def quote(
        mid: str,
        forward: Optional[bool] = None,
        content: Optional["Message"] = None,
    ) -> "RenderMessage":
        data = {"id": mid}
        if forward is not None:
            data["forward"] = forward  # type: ignore
        if content:
            data["content"] = content  # type: ignore
        return RenderMessage("quote", data)  # type: ignore

    @staticmethod
    def author(
        user_id: str,
        nickname: Optional[str] = None,
        avatar: Optional[str] = None,
    ) -> "Author":
        data = {"id": user_id}
        if nickname:
            data["nickname"] = nickname
        if avatar:
            data["avatar"] = avatar
        return Author("author", data)  # type: ignore

    @staticmethod
    def action_button(button_id: str, display: Optional[str] = None, theme: Optional[str] = None):
        data = {"type": "action", "id": button_id}
        if display:
            data["display"] = display
        if theme:
            data["theme"] = theme
        return Button("button", data)  # type: ignore

    @staticmethod
    def link_button(url: str, display: Optional[str] = None, theme: Optional[str] = None):
        data = {"type": "link", "href": url}
        if display:
            data["display"] = display
        if theme:
            data["theme"] = theme
        return Button("button", data)  # type: ignore

    @staticmethod
    def input_button(text: str, display: Optional[str] = None, theme: Optional[str] = None):
        data = {"type": "input", "text": text}
        if display:
            data["display"] = display
        if theme:
            data["theme"] = theme
        return Button("button", data)  # type: ignore

    @staticmethod
    def raw(content: str) -> "Raw":
        return Raw("raw", {"raw": content})

    @staticmethod
    def br() -> "Br":
        return Br("br", {"text": "\n"})

    @staticmethod
    def bold(text: Union[str, "Text", "Style"]) -> "Style":
        if isinstance(text, str):
            return Style("style", {"text": text, "styles": ["b"]})
        if isinstance(text, Text):
            return Style("style", {"text": text.data["text"], "styles": ["b"]})
        text.data["styles"].insert(0, "b")
        return text

    @staticmethod
    def italic(text: Union[str, "Text", "Style"]) -> "Style":
        if isinstance(text, str):
            return Style("style", {"text": text, "styles": ["i"]})
        if isinstance(text, Text):
            return Style("style", {"text": text.data["text"], "styles": ["i"]})
        text.data["styles"].insert(0, "i")
        return text

    @staticmethod
    def underline(text: Union[str, "Text", "Style"]) -> "Style":
        if isinstance(text, str):
            return Style("style", {"text": text, "styles": ["u"]})
        if isinstance(text, Text):
            return Style("style", {"text": text.data["text"], "styles": ["u"]})
        text.data["styles"].insert(0, "u")
        return text

    @staticmethod
    def strikethrough(text: Union[str, "Text", "Style"]) -> "Style":
        if isinstance(text, str):
            return Style("style", {"text": text, "styles": ["s"]})
        if isinstance(text, Text):
            return Style("style", {"text": text.data["text"], "styles": ["s"]})
        text.data["styles"].insert(0, "s")
        return text

    @staticmethod
    def spoiler(text: Union[str, "Text", "Style"]) -> "Style":
        if isinstance(text, str):
            return Style("style", {"text": text, "styles": ["spl"]})
        if isinstance(text, Text):
            return Style("style", {"text": text.data["text"], "styles": ["spl"]})
        text.data["styles"].insert(0, "spl")
        return text

    @staticmethod
    def code(text: Union[str, "Text", "Style"]) -> "Style":
        if isinstance(text, str):
            return Style("style", {"text": text, "styles": ["code"]})
        if isinstance(text, Text):
            return Style("style", {"text": text.data["text"], "styles": ["code"]})
        text.data["styles"].insert(0, "code")
        return text

    @staticmethod
    def superscript(text: Union[str, "Text", "Style"]) -> "Style":
        if isinstance(text, str):
            return Style("style", {"text": text, "styles": ["sup"]})
        if isinstance(text, Text):
            return Style("style", {"text": text.data["text"], "styles": ["sup"]})
        text.data["styles"].insert(0, "sup")
        return text

    @staticmethod
    def subscript(text: Union[str, "Text", "Style"]) -> "Style":
        if isinstance(text, str):
            return Style("style", {"text": text, "styles": ["sub"]})
        if isinstance(text, Text):
            return Style("style", {"text": text.data["text"], "styles": ["sub"]})
        text.data["styles"].insert(0, "sub")
        return text

    @staticmethod
    def paragraph(text: Union[str, "Text", "Style"]) -> "Style":
        if isinstance(text, str):
            return Style("style", {"text": text, "styles": ["p"]})
        if isinstance(text, Text):
            return Style("style", {"text": text.data["text"], "styles": ["p"]})
        text.data["styles"].insert(0, "p")
        return text

    @override
    def is_text(self) -> bool:
        return False


class RawData(TypedDict):
    raw: str


@dataclass
class Raw(MessageSegment):
    data: RawData = field(default_factory=dict)  # type: ignore

    @override
    def __str__(self) -> str:
        return self.data["raw"]

    @override
    def is_text(self) -> bool:
        return True


class TextData(TypedDict):
    text: str


@dataclass
class Text(MessageSegment):
    data: TextData = field(default_factory=dict)  # type: ignore

    @override
    def __str__(self) -> str:
        return escape(self.data["text"])

    @override
    def is_text(self) -> bool:
        return True


class AtData(TypedDict):
    id: NotRequired[str]
    name: NotRequired[str]
    role: NotRequired[str]
    type: NotRequired[str]


@dataclass
class At(MessageSegment):
    data: AtData = field(default_factory=dict)  # type: ignore


class SharpData(TypedDict):
    id: str
    name: NotRequired[str]


@dataclass
class Sharp(MessageSegment):
    data: SharpData = field(default_factory=dict)  # type: ignore


class LinkData(TypedDict):
    text: str
    display: NotRequired[str]


@dataclass
class Link(MessageSegment):
    data: LinkData = field(default_factory=dict)  # type: ignore

    @override
    def __str__(self):
        if "display" in self.data:
            return f'<a href="{escape(self.data["text"])}">{escape(self.data["display"])}</a>'
        return f'<a href="{escape(self.data["text"])}"/>'

    @override
    def is_text(self) -> bool:
        return True


class ImageData(TypedDict):
    src: str
    cache: NotRequired[bool]
    timeout: NotRequired[str]
    width: NotRequired[int]
    height: NotRequired[int]


@dataclass
class Image(MessageSegment):
    data: ImageData = field(default_factory=dict)  # type: ignore
    extra: InitVar[Optional[dict]] = None

    def __post_init__(self, extra: Optional[dict]):
        if extra:
            self.data.update(extra)  # type: ignore


class AudioData(TypedDict):
    src: str
    cache: NotRequired[bool]
    timeout: NotRequired[str]


@dataclass
class Audio(MessageSegment):
    data: AudioData = field(default_factory=dict)  # type: ignore
    extra: InitVar[Optional[dict]] = None

    def __post_init__(self, extra: Optional[dict]):
        if extra:
            self.data.update(extra)  # type: ignore


class VideoData(TypedDict):
    src: str
    cache: NotRequired[bool]
    timeout: NotRequired[str]


@dataclass
class Video(MessageSegment):
    data: VideoData = field(default_factory=dict)  # type: ignore
    extra: InitVar[Optional[dict]] = None

    def __post_init__(self, extra: Optional[dict]):
        if extra:
            self.data.update(extra)  # type: ignore


class FileData(TypedDict):
    src: str
    cache: NotRequired[bool]
    timeout: NotRequired[str]


@dataclass
class File(MessageSegment):
    data: FileData = field(default_factory=dict)  # type: ignore
    extra: InitVar[Optional[dict]] = None

    def __post_init__(self, extra: Optional[dict]):
        if extra:
            self.data.update(extra)  # type: ignore


class Br(MessageSegment):
    @override
    def __str__(self):
        return "<br/>"

    @override
    def is_text(self) -> bool:
        return True


class StyleData(TypedDict):
    text: str
    styles: List[str]


@dataclass
class Style(MessageSegment):
    data: StyleData = field(default_factory=dict)  # type: ignore

    @override
    def __str__(self):
        prefix = "".join(f"<{style}>" for style in self.data["styles"])
        suffix = "".join(f"</{style}>" for style in reversed(self.data["styles"]))
        return f"{prefix}{escape(self.data['text'])}{suffix}"

    @override
    def is_text(self) -> bool:
        return True


class RenderMessageData(TypedDict):
    id: NotRequired[str]
    forward: NotRequired[bool]
    content: NotRequired["Message"]


@dataclass
class RenderMessage(MessageSegment):
    data: RenderMessageData = field(default_factory=dict)  # type: ignore

    @override
    def __str__(self):
        attr = []
        if "id" in self.data:
            attr.append(f' id="{escape(self.data["id"])}"')
        if self.data.get("forward"):
            attr.append(" forward")
        if "content" not in self.data:
            return f'<{self.type}{"".join(attr)} />'
        else:
            return f'<{self.type}{"".join(attr)}>{self.data["content"]}</{self.type}>'


class AuthorData(TypedDict):
    id: str
    nickname: NotRequired[str]
    avatar: NotRequired[str]


@dataclass
class Author(MessageSegment):
    data: AuthorData = field(default_factory=dict)  # type: ignore


class ButtonData(TypedDict, total=False):
    type: str
    display: NotRequired[str]
    id: NotRequired[str]
    href: NotRequired[str]
    text: NotRequired[str]
    theme: NotRequired[str]


@dataclass
class Button(MessageSegment):
    data: ButtonData = field(default_factory=dict)  # type: ignore

    @override
    def __str__(self):
        attr = [f'type="{escape(self.data["type"])}"']  # type: ignore
        if self.data["type"] == "action":  # type: ignore
            attr.append(f'id="{escape(self.data["id"])}"')  # type: ignore
        if self.data["type"] == "link":  # type: ignore
            attr.append(f'href="{escape(self.data["href"])}"')  # type: ignore
        if self.data["type"] == "input":  # type: ignore
            attr.append(f'text="{escape(self.data["text"])}"')  # type: ignore
        if "theme" in self.data:
            attr.append(f'theme="{escape(self.data["theme"])}"')
        if "display" in self.data:
            return f'<button {" ".join(attr)}>{escape(self.data["display"])}</button>'
        return f'<button {" ".join(attr)} />'


ELEMENT_TYPE_MAP = {
    "text": (Text, "text"),
    "at": (At, "at"),
    "sharp": (Sharp, "sharp"),
    "img": (Image, "img"),
    "image": (Image, "img"),
    "audio": (Audio, "audio"),
    "video": (Video, "video"),
    "file": (File, "file"),
    "author": (Author, "author"),
}

STYLE_TYPE_MAP = {
    "b": "b",
    "strong": "b",
    "i": "i",
    "em": "i",
    "u": "u",
    "ins": "u",
    "s": "s",
    "del": "s",
    "spl": "spl",
    "code": "code",
    "sup": "sup",
    "sub": "sub",
    "p": "p",
}


class Message(BaseMessage[MessageSegment]):
    @classmethod
    @override
    def get_segment_class(cls) -> Type[MessageSegment]:
        return MessageSegment

    @override
    def __str__(self) -> str:
        text = "".join(str(seg) for seg in self)

        def calc_depth(msg: "Message") -> int:
            depth = 0
            for seg in msg:
                if seg.type == "style":
                    depth = max(depth, len(seg.data["styles"]))
                if seg.type == "message" or seg.type == "quote":
                    depth = max(depth, calc_depth(seg.data["content"]))
            return depth

        pat = re.compile(r"</(\w+)(?<!/p)><\1>")
        for _ in range(calc_depth(self)):
            text = pat.sub("", text)
        return text

    @override
    def __add__(self, other: Union[str, MessageSegment, Iterable[MessageSegment]]) -> "Message":
        return super().__add__(MessageSegment.text(other) if isinstance(other, str) else other)

    @override
    def __radd__(self, other: Union[str, MessageSegment, Iterable[MessageSegment]]) -> "Message":
        return super().__radd__(MessageSegment.text(other) if isinstance(other, str) else other)

    @staticmethod
    @override
    def _construct(msg: str) -> Iterable[MessageSegment]:
        yield from Message.from_satori_element(parse(msg))

    @classmethod
    def from_satori_element(cls, elements: List[Element]) -> "Message":
        msg = Message()

        # make nested style elements into a single element:
        # e.g.
        # make <b>123<i>456</i>789</b>:
        # Element(
        #     "b", {}, [
        #         Element("text", {"text": "123"}),
        #         Element(
        #             "i", {}, [
        #                  Element("text", {"text": "456"})
        #              ]
        #         ),
        #         Element("text", {"text": "789"})
        #      ]
        # )
        # to <b>123</b><b><i>456</i></b><b>789</b>:
        # [
        #     Style("style", {"text": "123", "styles": ["b"]}),
        #     Style("style", {"text": "456", "styles": ["b", "i"]}),
        #     Style("style", {"text": "789", "styles": ["b"]})
        # ]
        # or
        # [
        #     ms.bold("123"),
        #     ms.bold(ms.italic("456")),
        #     ms.bold("789")
        # ]
        # Notice: if empty element like <at/>, <img/>, split them into two elements:
        # e.g.
        # Element("b", {}, [Element("text", {"text": "123"}), Element("at", {"id": "123"})])
        # -> Style("style", {"text": "123", "styles": ["b"]}), At("at", {"id": "123"})

        def handle(element: Element, upper_styles: Optional[List[str]] = None):
            tag = element.tag()
            if tag in ELEMENT_TYPE_MAP:
                seg_cls, seg_type = ELEMENT_TYPE_MAP[tag]
                yield seg_cls(seg_type, element.attrs.copy())
            elif tag in ("a", "link"):
                if element.children:
                    yield Link(
                        "link", {"text": element.attrs["href"], "display": element.children[0].attrs["text"]}
                    )
                else:
                    yield Link("link", {"text": element.attrs["href"]})
            elif tag == "button":
                if element.children:
                    yield Button("button", {"display": element.children[0].attrs["text"], **element.attrs})  # type: ignore
                else:
                    yield Button("button", {**element.attrs})  # type: ignore
            elif tag in STYLE_TYPE_MAP:
                style = STYLE_TYPE_MAP[tag]
                for child in element.children:
                    child_tag = child.tag()
                    if child_tag == "text":
                        yield Style(
                            "style", {"text": child.attrs["text"], "styles": [*(upper_styles or []), style]}
                        )
                    else:
                        yield from handle(child, [*(upper_styles or []), style])
            elif tag in ("br", "newline"):
                yield Br("br", {"text": "\n"})
            elif tag in ("message", "quote"):
                data = element.attrs.copy()
                if element.children:
                    data["content"] = Message.from_satori_element(element.children)
                yield RenderMessage(element.tag(), data)  # type: ignore
            else:
                yield Raw("raw", {"raw": str(element)})

        for elem in elements:
            msg.extend(handle(elem))

        return msg

    @override
    def extract_plain_text(self) -> str:
        return "".join(seg.data["text"] for seg in self if seg.is_text())
