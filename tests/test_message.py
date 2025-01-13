from nonebot.adapters.satori.element import parse
from nonebot.adapters.satori.message import Message, MessageSegment


def test_message():
    code = """\
<quote id="123456789" chronocat:seq="1">
    <author id="123456789"/>
    Hello, World!
</quote> 
"""
    assert Message.from_satori_element(parse(code))[0].data["chronocat:seq"] == "1"
    assert Message("<b test:aaa>1234</b>")[0].data["test:aaa"] is True
    assert (
        Message.from_satori_element(parse("<img src='url' test:bbb='foo' width='123'/>"))[0].data["test:bbb"] == "foo"
    )
    assert Message.from_satori_element(parse("<chronocat:face id='265' name='[辣眼睛]' platform='chronocat'/>"))[
        0
    ].data == {"id": "265", "name": "[辣眼睛]", "platform": "chronocat"}

    test_message1 = MessageSegment(type="chronocat:face", data={"id": 12}) + "\n" + "Hello Yoshi"
    assert str(test_message1) == '<chronocat:face id="12"/>\nHello Yoshi'

    assert (Message() + "123").extract_plain_text() == "123"


def test_message_rich_expr():
    raw = """\
<message forward>
<message>Hello!</message>
</message>
"""
    msg1 = Message.from_satori_element(parse(raw))
    assert str(msg1) == "<message forward><message>Hello!</message></message>"
    msg2 = Message.from_satori_element(parse("<b>123<i>456</i>789</b>"))
    assert len(msg2) == 1
    assert msg2[0].data["styles"] == {(0, 3): ["b"], (3, 6): ["b", "i"], (6, 9): ["b"]}
    assert msg2.extract_plain_text() == "123456789"
    assert str(msg2) == "<b>123<i>456</i>789</b>"
    ms = MessageSegment
    msg3 = ms.bold("123456789").mark(3, 6, "italic")
    assert msg3 == msg2[0]
    msg4 = ms.bold("123456").mark(3, 6, "italic") + ms.image("url") + ms.bold("789abc").mark(0, 3, "italic")
    assert str(msg4) == '<b>123<i>456</i></b><img src="url"/><b><i>789</i>abc</b>'
    assert Message.from_satori_element(parse(str(msg4))) == msg4
    assert msg4.extract_plain_text() == "123456789abc"


def test_message_fallback():
    code = """\
<video src="http://aa.com/a.mp4">
  当前平台不支持发送视频，请在
  <a href="http://aa.com/a.mp4">这里</a>
  观看视频！
</video>
"""
    msg = Message.from_satori_element(parse(code))
    assert str(msg[0].children) == '当前平台不支持发送视频，请在<a href="http://aa.com/a.mp4">这里</a>观看视频！'
    assert msg.extract_plain_text() == "当前平台不支持发送视频，请在这里观看视频！"
    assert list(msg.query("link"))[0].data["text"] == "http://aa.com/a.mp4"
