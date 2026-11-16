import asyncio
from datetime import datetime
import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from pyokbot import Vanus
from pyokbot.messages import Messages
from pyokbot.opcodes import MessageOpcode
from pyokbot.ws import Ws
from pyokbot.login import Login


class MockConn:
    def __init__(self):
        self.sent: list[str] = []

    async def send(self, data: str) -> None:
        self.sent.append(data)


@pytest.fixture
def mock_ws():
    login = Login()
    ws = Ws(login)
    ws._conn = MockConn()
    return ws


def test_user_opcodes_registry():
    assert MessageOpcode.GET_CONTACTS == 32
    assert MessageOpcode.CONTACT_INFO == 32
    assert MessageOpcode.GET_PRESENCE == 35
    assert MessageOpcode.PRESENCE == 35
    assert MessageOpcode.GET_USER_PHOTOS == 39
    assert MessageOpcode.CONTACT_UPDATE == 131


@pytest.mark.asyncio
async def test_messages_get_contacts(mock_ws):
    messages = Messages({}, None)

    async def simulate_contacts_reply():
        await asyncio.sleep(0.01)
        mock_ws._pending_requests[1].set_result({
            "ver": 10,
            "cmd": 1,
            "seq": 1,
            "opcode": MessageOpcode.GET_CONTACTS,
            "payload": {
                "contacts": [
                    {
                        "id": 123456,
                        "names": [{"name": "Test User", "type": "OK"}],
                        "gender": 1,
                        "avatarUrl": "http://example.com/avatar.jpg",
                        "fullAvatarUrl": "http://example.com/full.jpg",
                    }
                ]
            }
        })

    asyncio.create_task(simulate_contacts_reply())
    res = await messages.get_contacts(mock_ws, [123456])
    contacts = res.get("payload", {}).get("contacts", [])
    assert len(contacts) == 1
    assert contacts[0]["id"] == 123456
    assert contacts[0]["names"][0]["name"] == "Test User"


@pytest.mark.asyncio
async def test_messages_get_presence(mock_ws):
    messages = Messages({}, None)

    async def simulate_presence_reply():
        await asyncio.sleep(0.01)
        mock_ws._pending_requests[1].set_result({
            "ver": 10,
            "cmd": 1,
            "seq": 1,
            "opcode": MessageOpcode.GET_PRESENCE,
            "payload": {
                "presence": {
                    "123456": {"on": "WEB", "seen": 1700000000}
                }
            }
        })

    asyncio.create_task(simulate_presence_reply())
    res = await messages.get_presence(mock_ws, [123456])
    presence = res.get("payload", {}).get("presence", {})
    assert "123456" in presence
    assert presence["123456"]["on"] == "WEB"


@pytest.mark.asyncio
async def test_messages_get_user_photos(mock_ws):
    messages = Messages({}, None)

    async def simulate_photos_reply():
        await asyncio.sleep(0.01)
        mock_ws._pending_requests[1].set_result({
            "ver": 10,
            "cmd": 1,
            "seq": 1,
            "opcode": MessageOpcode.GET_USER_PHOTOS,
            "payload": {
                "total": 2,
                "urls": ["http://example.com/1.jpg", "http://example.com/2.jpg"]
            }
        })

    asyncio.create_task(simulate_photos_reply())
    res = await messages.get_user_photos(mock_ws, 123456)
    assert res.get("payload", {}).get("total") == 2
    assert len(res.get("payload", {}).get("urls", [])) == 2


@pytest.mark.asyncio
async def test_vanus_get_user_info_via_ws():
    with patch("pyokbot.login.Login.start_login"):
        bot = Vanus("fake_auth")
    try:
        bot._fetch_user_via_ws = AsyncMock(return_value={
            "id": "123",
            "name": "Alice Bob",
            "first_name": "Alice",
            "last_name": "Bob",
            "avatar_url": "http://example.com/a.jpg",
            "full_avatar_url": "http://example.com/full.jpg",
            "gender": "female",
            "bday": "5.5",
            "profile_url": "https://ok.ru/profile/123",
            "last_update_time": str(datetime.now()),
        })

        info = await bot.get_user_info(123)
        assert info["id"] == "123"
        assert info["name"] == "Alice Bob"
        assert info["first_name"] == "Alice"
        assert info["last_name"] == "Bob"
        assert info["gender"] == "female"

        # Subsequent call should return cached without calling _fetch_user_via_ws again
        bot._fetch_user_via_ws.reset_mock()
        cached_info = await bot.get_user_info(123)
        assert cached_info["name"] == "Alice Bob"
        assert bot._fetch_user_via_ws.call_count == 0
    finally:
        await bot._session.close()


@pytest.mark.asyncio
async def test_vanus_batch_get_users_info():
    with patch("pyokbot.login.Login.start_login"):
        bot = Vanus("fake_auth")
    try:
        bot.messages.get_contacts = AsyncMock(return_value={
            "payload": {
                "contacts": [
                    {"id": 1, "names": [{"name": "User One"}]},
                    {"id": 2, "names": [{"name": "User Two"}]},
                ]
            }
        })
        results = await bot.get_users_info([1, 2], force_refresh=True)
        assert "1" in results
        assert "2" in results
        assert results["1"]["name"] == "User One"
        assert results["2"]["name"] == "User Two"
    finally:
        await bot._session.close()


@pytest.mark.asyncio
async def test_vanus_polling_auto_resolves_user():
    with patch("pyokbot.login.Login.start_login"):
        bot = Vanus("fake_auth", auto_resolve_users=True)
    try:
        # Prepopulate cache for sender 999
        bot.users_info_cache["999"] = {
            "name": "Super User",
            "avatar_url": "http://example.com/su.jpg",
            "full_avatar_url": "http://example.com/su_full.jpg",
            "gender": "male",
            "last_update_time": str(datetime.now()),
        }

        handled_messages = []

        @bot.on_message(filters=None)
        async def handler(msg):
            handled_messages.append(msg)

        # Enqueue an incoming message packet
        pkt = {
            "ver": 10,
            "opcode": MessageOpcode.INCOMING_MESSAGE,
            "payload": {
                "type": "USER",
                "chatId": 111,
                "message": {
                    "id": "msg_999",
                    "text": "Hello bot",
                    "sender": 999,
                    "cid": 12345,
                    "time": 1700000000,
                }
            }
        }
        await bot.ws._msg_queue.put(pkt)

        # Run polling for a brief tick
        poll_task = asyncio.create_task(bot.polling())
        await asyncio.sleep(0.15)
        poll_task.cancel()
        try:
            await poll_task
        except asyncio.CancelledError:
            pass

        assert len(handled_messages) == 1
        m = handled_messages[0]
        # Verify that user info was auto-resolved onto message.user!
        assert m.user.id == 999
        assert m.user.name == "Super User"
        assert m.user.avatar == "http://example.com/su.jpg"
        assert m.user.gender == "male"
    finally:
        await bot._session.close()
