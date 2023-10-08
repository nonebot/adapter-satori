from dataclasses import field, dataclass
from typing_extensions import NotRequired, override
from typing import Any, List, Type, Union, Iterable, Optional, TypedDict

from nonebot.adapters import Message as BaseMessage
from nonebot.adapters import MessageSegment as BaseMessageSegment

from .utils import Element, parse, escape


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
        return f"<{self.type} {attrs} />"

    @classmethod
    @override
    def get_message_class(cls) -> Type["Message"]:
        return Message

    @staticmethod
    def text(content: str) -> "Text":
        return Text("text", {"text": content})

    @staticmethod
    def entity(content: str, style: str) -> "Entity":
        return Entity("entity", {"text": content, "style": style})

    @staticmethod
    def at(
        user_id: str,
        name: Optional[str] = None,
    ) -> "At":
        data = {"id": user_id}
        if name:
            data["name"] = name
        return At("at", data)

    @staticmethod
    def at_role(
        role: str,
        name: Optional[str] = None,
    ) -> "At":
        data = {"role": role}
        if name:
            data["name"] = name
        return At("at_role", data)

    @staticmethod
    def at_all(here: bool = False) -> "At":
        return At("at", {"type": "here" if here else "all"})

    @staticmethod
    def sharp(channel_id: str, name: Optional[str] = None) -> "Sharp":
        data = {"id": channel_id}
        if name:
            data["name"] = name
        return Sharp("sharp", data)

    @staticmethod
    def link(href: str) -> "Link":
        return Link("link", {"href": href})

    @staticmethod
    def image(
        src: str, cache: Optional[bool] = None, timeout: Optional[str] = None
    ) -> "Image":
        data = {"src": src}
        if cache is not None:
            data["cache"] = cache
        if timeout is not None:
            data["timeout"] = timeout
        return Image("img", data)

    @staticmethod
    def audio(
        src: str, cache: Optional[bool] = None, timeout: Optional[str] = None
    ) -> "Audio":
        data = {"src": src}
        if cache is not None:
            data["cache"] = cache
        if timeout is not None:
            data["timeout"] = timeout
        return Audio("audio", data)

    @staticmethod
    def video(
        src: str, cache: Optional[bool] = None, timeout: Optional[str] = None
    ) -> "Video":
        data = {"src": src}
        if cache is not None:
            data["cache"] = cache
        if timeout is not None:
            data["timeout"] = timeout
        return Video("video", data)

    @staticmethod
    def file(
        src: str, cache: Optional[bool] = None, timeout: Optional[str] = None
    ) -> "File":
        data = {"src": src}
        if cache is not None:
            data["cache"] = cache
        if timeout is not None:
            data["timeout"] = timeout
        return File("file", data)

    @staticmethod
    def br() -> "Br":
        return Br("br", {})

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
        return RenderMessage("message", data)

    @staticmethod
    def quote(
        mid: str,
        forward: Optional[bool] = None,
        content: Optional["Message"] = None,
    ) -> "RenderMessage":
        data = {"id": mid}
        if forward is not None:
            data["forward"] = forward
        if content:
            data["content"] = content
        return RenderMessage("quote", data)

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
        return Author("author", data)

    @override
    def is_text(self) -> bool:
        return self.type == "text"


class TextData(TypedDict):
    text: str


@dataclass
class Text(MessageSegment):
    data: TextData = field(default_factory=dict)

    @override
    def __str__(self) -> str:
        return escape(self.data["text"])


class EntityData(TypedDict):
    text: str
    style: str


@dataclass
class Entity(MessageSegment):
    data: EntityData = field(default_factory=dict)

    @override
    def __str__(self) -> str:
        style = self.data["style"]
        return f'<{style}>{escape(self.data["text"])}</{style}>'


class AtData(TypedDict):
    id: NotRequired[str]
    name: NotRequired[str]
    role: NotRequired[str]
    type: NotRequired[str]


@dataclass
class At(MessageSegment):
    data: AtData = field(default_factory=dict)


class SharpData(TypedDict):
    id: str
    name: NotRequired[str]


@dataclass
class Sharp(MessageSegment):
    data: SharpData = field(default_factory=dict)


class LinkData(TypedDict):
    href: str


@dataclass
class Link(MessageSegment):
    data: LinkData = field(default_factory=dict)

    @override
    def __str__(self):
        return f'<a href="{escape(self.data["href"])}"/>'


class ImageData(TypedDict):
    src: str
    cache: NotRequired[bool]
    timeout: NotRequired[str]
    width: NotRequired[int]
    height: NotRequired[int]


@dataclass
class Image(MessageSegment):
    data: ImageData = field(default_factory=dict)


class AudioData(TypedDict):
    src: str
    cache: NotRequired[bool]
    timeout: NotRequired[str]


@dataclass
class Audio(MessageSegment):
    data: AudioData = field(default_factory=dict)


class VideoData(TypedDict):
    src: str
    cache: NotRequired[bool]
    timeout: NotRequired[str]


@dataclass
class Video(MessageSegment):
    data: VideoData = field(default_factory=dict)


class FileData(TypedDict):
    src: str
    cache: NotRequired[bool]
    timeout: NotRequired[str]


@dataclass
class File(MessageSegment):
    data: FileData = field(default_factory=dict)


@dataclass
class Br(MessageSegment):
    @override
    def __str__(self):
        return "<br/>"


class ParagraphData(TypedDict):
    text: str


@dataclass
class Paragraph(MessageSegment):
    data: ParagraphData = field(default_factory=dict)

    @override
    def __str__(self):
        return f'<p>{escape(self.data["text"])}</p>'


class RenderMessageData(TypedDict):
    id: NotRequired[str]
    forward: NotRequired[bool]
    content: NotRequired["Message"]


@dataclass
class RenderMessage(MessageSegment):
    data: RenderMessageData = field(default_factory=dict)

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
    data: AuthorData = field(default_factory=dict)


ELEMENT_TYPE_MAP = {
    "text": (Text, "text"),
    "at": (At, "at"),
    "sharp": (Sharp, "sharp"),
    "a": (Link, "link"),
    "link": (Link, "link"),
    "img": (Image, "img"),
    "image": (Image, "img"),
    "audio": (Audio, "audio"),
    "video": (Video, "video"),
    "file": (File, "file"),
    "br": (Br, "br"),
    "author": (Author, "author"),
}


class Message(BaseMessage[MessageSegment]):
    @classmethod
    @override
    def get_segment_class(cls) -> Type[MessageSegment]:
        return MessageSegment

    @override
    def __add__(
        self, other: Union[str, MessageSegment, Iterable[MessageSegment]]
    ) -> "Message":
        return super().__add__(
            MessageSegment.text(other) if isinstance(other, str) else other
        )

    @override
    def __radd__(
        self, other: Union[str, MessageSegment, Iterable[MessageSegment]]
    ) -> "Message":
        return super().__radd__(
            MessageSegment.text(other) if isinstance(other, str) else other
        )

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
            elif elem.type in {
                "b",
                "strong",
                "i",
                "em",
                "u",
                "ins",
                "s",
                "del",
                "spl",
                "code",
                "sup",
                "sub",
            }:
                msg.append(
                    Entity(
                        "entity",
                        {"text": elem.children[0].attrs["text"], "style": elem.type},
                    )
                )
            elif elem.type in ("p", "paragraph"):
                msg.append(
                    Paragraph("paragraph", {"text": elem.children[0].attrs["text"]})
                )
            elif elem.type in ("message", "quote"):
                data = elem.attrs.copy()
                if elem.children:
                    data["content"] = Message.from_satori_element(elem.children)
                msg.append(RenderMessage(elem.type, data))
            else:
                msg.append(Text("text", {"text": str(elem)}))
        return msg

    def extract_content(self) -> str:
        return "".join(
            str(seg)
            for seg in self
            if seg.type in ("text", "entity", "at", "sharp", "link")
        )
