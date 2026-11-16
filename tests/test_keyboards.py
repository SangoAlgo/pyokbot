import pytest
from unittest.mock import AsyncMock, MagicMock

from pyokbot import InlineButton, InlineKeyboard, ReplyButton, ReplyKeyboard, Vanus
from pyokbot.messages import Messages
from pyokbot.opcodes import MessageOpcode


def test_inline_keyboard_builder():
    kb = InlineKeyboard(callback_id="test_cb_123")
    kb.add_button("🔥 Тест 1", callback_data="btn_1", intent="POSITIVE")
    kb.add_url_button("🌐 Ссылка", url="https://ok.ru")
    kb.row(
        InlineButton("Кнопка 3", callback_data="btn_3", intent="NEGATIVE"),
        InlineButton("Кнопка 4", callback_data="btn_4"),
    )

    attach = kb.to_attach()
    assert attach["_type"] == "INLINE_KEYBOARD"
    assert attach["callbackId"] == "test_cb_123"
    grid = attach["keyboard"]["buttons"]
    assert len(grid) == 2
    assert len(grid[0]) == 2
    assert grid[0][0]["text"] == "🔥 Тест 1"
    assert grid[0][0]["type"] == "CALLBACK"
    assert grid[0][0]["payload"] == "btn_1"
    assert grid[0][0]["intent"] == "POSITIVE"

    assert grid[0][1]["text"] == "🌐 Ссылка"
    assert grid[0][1]["type"] == "LINK"
    assert grid[0][1]["url"] == "https://ok.ru"

    assert len(grid[1]) == 2
    assert grid[1][0]["intent"] == "NEGATIVE"


def test_inline_keyboard_bot_api():
    kb = InlineKeyboard()
    kb.add_button("Button 1", callback_data="payload_1")
    kb.add_url_button("Button 2", url="https://ok.ru")
    bot_api_dict = kb.to_bot_api()
    assert bot_api_dict["type"] == "inline_keyboard"
    buttons = bot_api_dict["payload"]["buttons"]
    assert len(buttons[0]) == 2
    assert buttons[0][0]["type"] == "callback"
    assert buttons[0][0]["payload"] == "payload_1"
    assert buttons[0][1]["type"] == "link"
    assert buttons[0][1]["url"] == "https://ok.ru"


def test_reply_keyboard_builder():
    rkb = ReplyKeyboard(default_input_disabled=True)
    rkb.add_button("Да", intent="POSITIVE")
    rkb.add_button("Нет", intent="NEGATIVE")
    rkb.row("Назад")

    attach = rkb.to_attach()
    assert attach["_type"] == "REPLY_KEYBOARD"
    assert attach["defaultInputDisabled"] is True
    grid = attach["keyboard"]
    assert len(grid) == 2
    assert grid[0][0]["text"] == "Да"
    assert grid[0][0]["intent"] == "POSITIVE"
    assert grid[0][0]["type"] == "message"
    assert grid[0][0]["message"]["detectShare"] is True
    assert grid[0][1]["text"] == "Нет"
    assert grid[0][1]["intent"] == "NEGATIVE"
    assert grid[1][0]["text"] == "Назад"


def test_generate_message_with_inline_keyboard():
    msgs = Messages(bot_info={"id": 123}, session=AsyncMock())
    raw_packet = {
        "ver": 10,
        "cmd": 0,
        "opcode": MessageOpcode.INCOMING_MESSAGE,
        "payload": {
            "chatId": -111055305091923,
            "message": {
                "id": "117627621301421839",
                "time": 1794855061362,
                "text": "Выберите действие:",
                "sender": 456,
                "attaches": [
                    {
                        "_type": "INLINE_KEYBOARD",
                        "callbackId": "cb_test",
                        "keyboard": {
                            "buttons": [
                                [
                                    {
                                        "text": "Создать",
                                        "type": "CALLBACK",
                                        "payload": "/new_set",
                                        "intent": "DEFAULT",
                                    }
                                ]
                            ]
                        },
                    }
                ],
            },
        },
    }

    parsed = msgs.generate_message_object(raw_packet)
    assert parsed is not None
    assert parsed["inline_keyboard"] is not None
    assert parsed["inline_keyboard"]["callbackId"] == "cb_test"
    assert len(parsed["inline_keyboard"]["buttons"]) == 1
    assert parsed["buttons"] is not None
    assert parsed["buttons"][0][0]["payload"] == "/new_set"


@pytest.mark.asyncio
async def test_click_inline_button_dispatches_opcode_118():
    msgs = Messages(bot_info={"id": 123}, session=AsyncMock())
    ws_mock = AsyncMock()
    ws_mock.request = AsyncMock(return_value={"success": True})

    res = await msgs.click_inline_button(
        ws=ws_mock,
        callback_id="cb_test_999",
        payload="/confirm",
        button_type="CALLBACK",
    )

    assert res == {"success": True}
    ws_mock.request.assert_awaited_once_with(
        MessageOpcode.CALLBACK_ANSWER,
        {
            "callbackId": "cb_test_999",
            "type": "CALLBACK",
            "payload": "/confirm",
        },
        timeout=5.0,
    )
