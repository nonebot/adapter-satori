import re
from io import BytesIO
from pathlib import Path
from base64 import b64encode
from dataclasses import InitVar, field, dataclass
from typing_extensions import Self, Required, NotRequired, override
from typing import Any, Dict, List, Type, Tuple, Union, Iterable, Optional, TypedDict

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
        return Text("text", {"text": content, "styles": {}})

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
        name: Optional[str] = None,
        extra: Optional[dict] = None,
        cache: Optional[bool] = None,
        timeout: Optional[str] = None,
    ) -> "Image":
        if url:
            data = {"src": url}
        elif path:
            data = {"src": Path(path).absolute().as_uri()}
        elif raw and mime:
            bd = raw if isinstance(raw, bytes) else raw.getvalue()  # type: ignore
            data = {"src": f"data:{mime};base64,{b64encode(bd).decode()}"}
        else:
            raise ValueError("image need at least one of url, path and raw")
        if name:
            data["title"] = name
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
        name: Optional[str] = None,
        poster: Optional[str] = None,
        extra: Optional[dict] = None,
        cache: Optional[bool] = None,
        timeout: Optional[str] = None,
    ) -> "Audio":
        if url:
            data = {"src": url}
        elif path:
            data = {"src": Path(path).absolute().as_uri()}
        elif raw and mime:
            bd = raw if isinstance(raw, bytes) else raw.getvalue()  # type: ignore
            data = {"src": f"data:{mime};base64,{b64encode(bd).decode()}"}
        else:
            raise ValueError("audio need at least one of url, path and raw")
        if name:
            data["title"] = name
        if poster:
            data["poster"] = poster
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
        name: Optional[str] = None,
        poster: Optional[str] = None,
        extra: Optional[dict] = None,
        cache: Optional[bool] = None,
        timeout: Optional[str] = None,
    ) -> "Video":
        if url:
            data = {"src": url}
        elif path:
            data = {"src": Path(path).absolute().as_uri()}
        elif raw and mime:
            bd = raw if isinstance(raw, bytes) else raw.getvalue()  # type: ignore
            data = {"src": f"data:{mime};base64,{b64encode(bd).decode()}"}
        else:
            raise ValueError("video need at least one of url, path and raw")
        if name:
            data["title"] = name
        if poster:
            data["poster"] = poster
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
        name: Optional[str] = None,
        poster: Optional[str] = None,
        extra: Optional[dict] = None,
        cache: Optional[bool] = None,
        timeout: Optional[str] = None,
    ) -> "File":
        if url:
            data = {"src": url}
        elif path:
            data = {"src": Path(path).absolute().as_uri()}
        elif raw and mime:
            bd = raw if isinstance(raw, bytes) else raw.getvalue()  # type: ignore
            data = {"src": f"data:{mime};base64,{b64encode(bd).decode()}"}
        else:
            raise ValueError("file need at least one of url, path and raw")
        if name:
            data["title"] = name
        if poster:
            data["poster"] = poster
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
        name: Optional[str] = None,
        avatar: Optional[str] = None,
    ) -> "Author":
        data = {"id": user_id}
        if name:
            data["name"] = name
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
    def bold(text: Union[str, "Text"]) -> "Text":
        if isinstance(text, str):
            return Text("text", {"text": text, "styles": {(0, len(text)): ["b"]}})
        text.data["styles"].setdefault((0, len(text.data["text"])), []).insert(0, "b")
        return text

    @staticmethod
    def italic(text: Union[str, "Text"]) -> "Text":
        if isinstance(text, str):
            return Text("text", {"text": text, "styles": {(0, len(text)): ["i"]}})
        text.data["styles"].setdefault((0, len(text.data["text"])), []).insert(0, "i")
        return text

    @staticmethod
    def underline(text: Union[str, "Text"]) -> "Text":
        if isinstance(text, str):
            return Text("text", {"text": text, "styles": {(0, len(text)): ["u"]}})
        text.data["styles"].setdefault((0, len(text.data["text"])), []).insert(0, "u")
        return text

    @staticmethod
    def strikethrough(text: Union[str, "Text"]) -> "Text":
        if isinstance(text, str):
            return Text("text", {"text": text, "styles": {(0, len(text)): ["s"]}})
        text.data["styles"].setdefault((0, len(text.data["text"])), []).insert(0, "s")
        return text

    @staticmethod
    def spoiler(text: Union[str, "Text"]) -> "Text":
        if isinstance(text, str):
            return Text("text", {"text": text, "styles": {(0, len(text)): ["spl"]}})
        text.data["styles"].setdefault((0, len(text.data["text"])), []).insert(0, "spl")
        return text

    @staticmethod
    def code(text: Union[str, "Text"]) -> "Text":
        if isinstance(text, str):
            return Text("text", {"text": text, "styles": {(0, len(text)): ["code"]}})
        text.data["styles"].setdefault((0, len(text.data["text"])), []).insert(0, "code")
        return text

    @staticmethod
    def superscript(text: Union[str, "Text"]) -> "Text":
        if isinstance(text, str):
            return Text("text", {"text": text, "styles": {(0, len(text)): ["sup"]}})
        text.data["styles"].setdefault((0, len(text.data["text"])), []).insert(0, "sup")
        return text

    @staticmethod
    def subscript(text: Union[str, "Text"]) -> "Text":
        if isinstance(text, str):
            return Text("text", {"text": text, "styles": {(0, len(text)): ["sub"]}})
        text.data["styles"].setdefault((0, len(text.data["text"])), []).insert(0, "sub")
        return text

    @staticmethod
    def paragraph(text: Union[str, "Text"]) -> "Text":
        if isinstance(text, str):
            return Text("text", {"text": text, "styles": {(0, len(text)): ["p"]}})
        text.data["styles"].setdefault((0, len(text.data["text"])), []).insert(0, "p")
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
    styles: Dict[Tuple[int, int], List[str]]


@dataclass
class Text(MessageSegment):
    data: TextData = field(default_factory=dict)  # type: ignore

    def __post_init__(self):
        if "styles" not in self.data:
            self.data["styles"] = {}

    def __merge__(self):
        data = {}
        styles = self.data["styles"]
        if not styles:
            return
        for scale, _styles in styles.items():
            for i in range(*scale):
                if i not in data:
                    data[i] = _styles[:]
                else:
                    data[i].extend(s for s in _styles if s not in data[i])
        styles.clear()
        data1 = {}
        for i, _styles in data.items():
            key = "\x01".join(_styles)
            data1.setdefault(key, []).append(i)
        data.clear()
        for key, indexes in data1.items():
            start = indexes[0]
            end = start
            for i in indexes[1:]:
                if i - end == 1:
                    end = i
                else:
                    data[(start, end + 1)] = key.split("\x01")
                    start = end = i
            if end >= start:
                data[(start, end + 1)] = key.split("\x01")
        for scale in sorted(data.keys()):
            styles[scale] = data[scale]

    def mark(self, start: int, end: int, *styles: str) -> Self:
        _styles = self.data["styles"].setdefault((start, end), [])
        for sty in styles:
            sty = STYLE_TYPE_MAP.get(sty, sty)
            if sty not in _styles:
                _styles.append(sty)
        self.__merge__()
        return self

    @override
    def __str__(self) -> str:
        result = []
        text = self.data["text"]
        styles = self.data["styles"]
        if not styles:
            return escape(self.data["text"])
        self.__merge__()
        scales = sorted(styles.keys(), key=lambda x: x[0])
        left = scales[0][0]
        result.append(escape(text[:left]))
        for scale in scales:
            prefix = "".join(f"<{style}>" for style in styles[scale])
            suffix = "".join(f"</{style}>" for style in reversed(styles[scale]))
            result.append(prefix + escape(text[scale[0] : scale[1]]) + suffix)
        right = scales[-1][1]
        result.append(escape(text[right:]))
        text = "".join(result)
        pat = re.compile(r"</(\w+)(?<!/p)><\1>")
        for _ in range(max(map(len, styles.values()))):
            text = pat.sub("", text)
        return text

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
    title: NotRequired[str]
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
    title: NotRequired[str]
    duration: NotRequired[float]
    poster: NotRequired[str]
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
    title: NotRequired[str]
    width: NotRequired[int]
    height: NotRequired[int]
    duration: NotRequired[float]
    poster: NotRequired[str]
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
    title: NotRequired[str]
    poster: NotRequired[str]
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
    name: NotRequired[str]
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


class CustomData(TypedDict, total=False):
    _children: Required[List["MessageSegment"]]


@dataclass
class Custom(MessageSegment):
    data: CustomData = field(default_factory=dict)  # type: ignore

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

        attrs = "".join(_attr(k, v) for k, v in self.data.items() if k != "_children")
        if self.type == "text" and "text" in self.data:
            return escape(self.data["text"])
        inner = "".join(str(c) for c in self.data["_children"])
        if not inner:
            return f"<{self.type}{attrs}/>"
        return f"<{self.type}{attrs}>{inner}</{self.type}>"


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
    "bold": "b",
    "i": "i",
    "em": "i",
    "italic": "i",
    "u": "u",
    "ins": "u",
    "underline": "u",
    "s": "s",
    "del": "s",
    "strike": "s",
    "spl": "spl",
    "spoiler": "spl",
    "code": "code",
    "sup": "sup",
    "superscript": "sup",
    "sub": "sub",
    "subscript": "sub",
    "p": "p",
    "paragraph": "p",
}


def handle(element: Element, upper_styles: Optional[List[str]] = None):
    tag = element.tag()
    if tag in ELEMENT_TYPE_MAP:
        seg_cls, seg_type = ELEMENT_TYPE_MAP[tag]
        yield seg_cls(seg_type, element.attrs.copy())
    elif tag in ("a", "link"):
        if element.children:
            yield Link("link", {"text": element.attrs["href"], "display": element.children[0].attrs["text"]})
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
                yield Text(
                    "text",
                    {
                        **element.attrs,  # type: ignore
                        "text": child.attrs["text"],
                        "styles": {(0, len(child.attrs["text"])): [*(upper_styles or []), style]},
                    },
                )
            else:
                yield from handle(child, [*(upper_styles or []), style])
    elif tag in ("br", "newline"):
        yield Br("br", {"text": "\n"})
    elif tag in ("message", "quote"):
        data = element.attrs.copy()
        if element.children:
            data["content"] = Message.from_satori_element(element.children)
        yield RenderMessage(tag, data)  # type: ignore
    else:
        custom = Custom(element.tag(), {**element.attrs, "_children": []})  # type: ignore
        for child in element.children:
            custom.data["_children"].extend(handle(child))
        yield custom


class Message(BaseMessage[MessageSegment]):
    @classmethod
    @override
    def get_segment_class(cls) -> Type[MessageSegment]:
        return MessageSegment

    @override
    def __add__(self, other: Union[str, MessageSegment, Iterable[MessageSegment]]) -> "Message":
        result = self.copy()
        result += MessageSegment.text(other) if isinstance(other, str) else other
        return result.__merge_text__()

    @override
    def __radd__(self, other: Union[str, MessageSegment, Iterable[MessageSegment]]) -> "Message":
        result = self.__class__(MessageSegment.text(other) if isinstance(other, str) else other)
        result = result + self
        return result.__merge_text__()

    @staticmethod
    @override
    def _construct(msg: str) -> Iterable[MessageSegment]:
        yield from Message.from_satori_element(parse(msg))

    @classmethod
    def from_satori_element(cls, elements: List[Element]) -> "Message":
        msg = Message()

        for elem in elements:
            msg.extend(handle(elem))

        return msg.__merge_text__()

    @override
    def extract_plain_text(self) -> str:
        return "".join(seg.data["text"] for seg in self if seg.is_text())

    def __merge_text__(self) -> Self:
        if not self:
            return self
        result = []
        last = self[0]
        for seg in self[1:]:
            if last.type == "text" and seg.type == "text":
                assert isinstance(last, Text)
                _len = len(last.data["text"])
                last.data["text"] += seg.data["text"]
                for scale, styles in seg.data["styles"].items():
                    last.data["styles"][(scale[0] + _len, scale[1] + _len)] = styles[:]
            else:
                result.append(last)
                last = seg
        result.append(last)
        self.clear()
        self.extend(result)
        return self
