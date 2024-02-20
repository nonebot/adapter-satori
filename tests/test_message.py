import pytest

from nonebot.adapters.satori.element import parse
from nonebot.adapters.satori.message import Message, MessageSegment


@pytest.mark.asyncio
async def test_message_rich_expr():
    raw = """\
<message forward>
<message>Hello!</message>
</message>
"""
    msg1 = Message.from_satori_element(parse(raw))
    assert str(msg1) == "<message forward><message>Hello!</message></message>"
    msg2 = Message.from_satori_element(parse("<b>123<i>456</i>789</b>"))
    assert msg2[0] == MessageSegment.bold("123")
    assert msg2[1] == MessageSegment.bold(MessageSegment.italic("456"))
    assert msg2[2] == MessageSegment.bold("789")
    assert msg2.extract_plain_text() == "123456789"
    assert str(msg2) == "<b>123<i>456</i>789</b>"
    assert "".join(str(seg) for seg in msg2) == "<b>123</b><b><i>456</i></b><b>789</b>"
