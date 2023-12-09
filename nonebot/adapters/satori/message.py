from io import BytesIO
from pathlib import Path
from base64 import b64encode
from dataclasses import InitVar, field, dataclass
from typing_extensions import NotRequired, override
from typing import Any, List, Type, Union, Iterable, Optional, TypedDict

from nonebot.adapters import Message as BaseMessage
from nonebot.adapters import MessageSegment as BaseMessageSegment

from .utils import Element, parse, escape


class RawData(TypedDict):
    data: Union[bytes, BytesIO]
    mime: str


class MessageSegment(BaseMessageSegment["Message"]):
    def __str__(self) -> str:
        def _attr(key: str, value: Any):
            if value is True:
                return key
            if value is False:
                return f"no-{key}"
            if isinstance(value, (int, float)):
                return f"{key}={value}"
            return f'{key}="{escape(str(value))}"'

        attrs = " ".join(_attr(k, v) for k, v in self.data.items())
        attrs = f" {attrs}" if attrs else ""
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
        raw: Optional[RawData] = None,
        extra: Optional[dict] = None,
        cache: Optional[bool] = None,
        timeout: Optional[str] = None,
    ) -> "Image":
        if url:
            data = {"src": url}
        elif path:
            data = {"src": Path(path).as_uri()}
        elif raw:
            bd = raw["data"] if isinstance(raw["data"], bytes) else raw["data"].getvalue()  # type: ignore
            data = {"src": f"data:{raw['mime']};base64,{b64encode(bd).decode()}"}
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
        raw: Optional[RawData] = None,
        extra: Optional[dict] = None,
        cache: Optional[bool] = None,
        timeout: Optional[str] = None,
    ) -> "Audio":
        if url:
            data = {"src": url}
        elif path:
            data = {"src": Path(path).as_uri()}
        elif raw:
            bd = raw["data"] if isinstance(raw["data"], bytes) else raw["data"].getvalue()  # type: ignore
            data = {"src": f"data:{raw['mime']};base64,{b64encode(bd).decode()}"}
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
        raw: Optional[RawData] = None,
        extra: Optional[dict] = None,
        cache: Optional[bool] = None,
        timeout: Optional[str] = None,
    ) -> "Video":
        if url:
            data = {"src": url}
        elif path:
            data = {"src": Path(path).as_uri()}
        elif raw:
            bd = raw["data"] if isinstance(raw["data"], bytes) else raw["data"].getvalue()  # type: ignore
            data = {"src": f"data:{raw['mime']};base64,{b64encode(bd).decode()}"}
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
        raw: Optional[RawData] = None,
        extra: Optional[dict] = None,
        cache: Optional[bool] = None,
        timeout: Optional[str] = None,
    ) -> "File":
        if url:
            data = {"src": url}
        elif path:
            data = {"src": Path(path).as_uri()}
        elif raw:
            bd = raw["data"] if isinstance(raw["data"], bytes) else raw["data"].getvalue()  # type: ignore
            data = {"src": f"data:{raw['mime']};base64,{b64encode(bd).decode()}"}
        else:
            raise ValueError("file need at least one of url, path and raw")
        if cache is not None:
            data["cache"] = cache  # type: ignore
        if timeout is not None:
            data["timeout"] = timeout
        return File("file", data, extra=extra)  # type: ignore

    @staticmethod
    def bold(text: str) -> "Bold":
        return Bold("bold", {"text": text})

    @staticmethod
    def italic(text: str) -> "Italic":
        return Italic("italic", {"text": text})

    @staticmethod
    def underline(text: str) -> "Underline":
        return Underline("underline", {"text": text})

    @staticmethod
    def strikethrough(text: str) -> "Strikethrough":
        return Strikethrough("strikethrough", {"text": text})

    @staticmethod
    def spoiler(text: str) -> "Spoiler":
        return Spoiler("spoiler", {"text": text})

    @staticmethod
    def code(text: str) -> "Code":
        return Code("code", {"text": text})

    @staticmethod
    def superscript(text: str) -> "Superscript":
        return Superscript("superscript", {"text": text})

    @staticmethod
    def subscript(text: str) -> "Subscript":
        return Subscript("subscript", {"text": text})

    @staticmethod
    def br() -> "Br":
        return Br("br", {"text": "\n"})

    @staticmethod
    def paragraph(text: str) -> "Paragraph":
        return Paragraph("paragraph", {"text": text})

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

    @override
    def is_text(self) -> bool:
        return False


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


@dataclass
class Bold(MessageSegment):
    data: TextData = field(default_factory=dict)  # type: ignore

    @override
    def __str__(self):
        return f'<b>{escape(self.data["text"])}</b>'

    @override
    def is_text(self) -> bool:
        return True


@dataclass
class Italic(MessageSegment):
    data: TextData = field(default_factory=dict)  # type: ignore

    @override
    def __str__(self):
        return f'<i>{escape(self.data["text"])}</i>'

    @override
    def is_text(self) -> bool:
        return True


@dataclass
class Underline(MessageSegment):
    data: TextData = field(default_factory=dict)  # type: ignore

    @override
    def __str__(self):
        return f'<u>{escape(self.data["text"])}</u>'

    @override
    def is_text(self) -> bool:
        return True


@dataclass
class Strikethrough(MessageSegment):
    data: TextData = field(default_factory=dict)  # type: ignore

    @override
    def __str__(self):
        return f'<s>{escape(self.data["text"])}</s>'

    @override
    def is_text(self) -> bool:
        return True


@dataclass
class Spoiler(MessageSegment):
    data: TextData = field(default_factory=dict)  # type: ignore

    @override
    def __str__(self):
        return f'<spl>{escape(self.data["text"])}</spl>'

    @override
    def is_text(self) -> bool:
        return True


@dataclass
class Code(MessageSegment):
    data: TextData = field(default_factory=dict)  # type: ignore

    @override
    def __str__(self):
        return f'<code>{escape(self.data["text"])}</code>'

    @override
    def is_text(self) -> bool:
        return True


@dataclass
class Superscript(MessageSegment):
    data: TextData = field(default_factory=dict)  # type: ignore

    @override
    def __str__(self):
        return f'<sup>{escape(self.data["text"])}</sup>'

    @override
    def is_text(self) -> bool:
        return True


@dataclass
class Subscript(MessageSegment):
    data: TextData = field(default_factory=dict)  # type: ignore

    @override
    def __str__(self):
        return f'<sub>{escape(self.data["text"])}</sub>'

    @override
    def is_text(self) -> bool:
        return True


@dataclass
class Br(MessageSegment):
    data: TextData = field(default_factory=dict)  # type: ignore

    @override
    def __str__(self):
        return "<br/>"

    @override
    def is_text(self) -> bool:
        return True


@dataclass
class Paragraph(MessageSegment):
    data: TextData = field(default_factory=dict)  # type: ignore

    @override
    def __str__(self):
        return f'<p>{escape(self.data["text"])}</p>'

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
            attr.append(f'id="{escape(self.data["id"])}"')
        if self.data.get("forward"):
            attr.append("forward")
        if "content" not in self.data:
            return f'<{self.type} {" ".join(attr)} />'
        else:
            return f'<{self.type} {" ".join(attr)}>{self.data["content"]}</{self.type}>'


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
    "b": (Bold, "bold"),
    "strong": (Bold, "bold"),
    "i": (Italic, "italic"),
    "em": (Italic, "italic"),
    "u": (Underline, "underline"),
    "ins": (Underline, "underline"),
    "s": (Strikethrough, "strikethrough"),
    "del": (Strikethrough, "strikethrough"),
    "spl": (Spoiler, "spoiler"),
    "code": (Code, "code"),
    "sup": (Superscript, "superscript"),
    "sub": (Subscript, "subscript"),
    "p": (Paragraph, "paragraph"),
}


class Message(BaseMessage[MessageSegment]):
    @classmethod
    @override
    def get_segment_class(cls) -> Type[MessageSegment]:
        return MessageSegment

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
        for elem in elements:
            if elem.type in ELEMENT_TYPE_MAP:
                seg_cls, seg_type = ELEMENT_TYPE_MAP[elem.type]
                msg.append(seg_cls(seg_type, elem.attrs.copy()))
            elif elem.type in ("a", "link"):
                if elem.children:
                    msg.append(
                        Link("link", {"text": elem.attrs["href"], "display": elem.children[0].attrs["text"]})
                    )
                else:
                    msg.append(Link("link", {"text": elem.attrs["href"]}))
            elif elem.type == "button":
                if elem.children:
                    msg.append(Button("button", {"display": elem.children[0].attrs["text"], **elem.attrs}))  # type: ignore
                else:
                    msg.append(Button("button", {**elem.attrs}))  # type: ignore
            elif elem.type in STYLE_TYPE_MAP:
                seg_cls, seg_type = STYLE_TYPE_MAP[elem.type]
                msg.append(seg_cls(seg_type, {"text": elem.children[0].attrs["text"]}))
            elif elem.type in ("br", "newline"):
                msg.append(Br("br", {"text": "\n"}))
            elif elem.type in ("message", "quote"):
                data = elem.attrs.copy()
                if elem.children:
                    data["content"] = Message.from_satori_element(elem.children)
                msg.append(RenderMessage(elem.type, data))  # type: ignore
            else:
                msg.append(Text("text", {"text": str(elem)}))
        return msg

    @override
    def extract_plain_text(self) -> str:
        return "".join(seg.data["text"] for seg in self if seg.is_text())
