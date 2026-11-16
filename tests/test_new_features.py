import asyncio
import json
import pytest
from pyokbot.opcodes import MessageOpcode
from pyokbot.ws import Ws
from pyokbot.login import Login
from pyokbot.messages import Messages
from pyokbot.errors import APIError, TimeoutError


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


def test_new_opcodes_registry():
    assert MessageOpcode.SET_REACTION == 178
    assert MessageOpcode.REMOVE_REACTION == 179
    assert MessageOpcode.GET_REACTIONS == 180
    assert MessageOpcode.GET_REACTED_USERS == 181
    assert MessageOpcode.INCOMING_REACTION == 155
    assert MessageOpcode.YOUR_REACTION == 156
    assert MessageOpcode.USER_TYPING == 129
    assert MessageOpcode.READ_RECEIPT == 130
    assert MessageOpcode.PRESENCE_UPDATE == 132
    assert MessageOpcode.CHAT_HISTORY == 49
    assert MessageOpcode.READ_MESSAGE == 50
    assert MessageOpcode.JOIN_CHAT == 57
    assert MessageOpcode.LEAVE_CHAT == 58
    assert MessageOpcode.ADD_MEMBERS == 59
    assert MessageOpcode.CHAT_PARTICIPANTS == 61
    assert MessageOpcode.SUBSCRIBE_CHAT == 75


@pytest.mark.asyncio
async def test_ws_request_success(mock_ws):
    async def simulate_response():
        await asyncio.sleep(0.01)
        # Server responds to seq 1 with cmd=1
        mock_ws._pending_requests[1].set_result({
            "ver": 10,
            "cmd": 1,
            "seq": 1,
            "opcode": MessageOpcode.SET_REACTION,
            "payload": {"reactionInfo": {"totalCount": 1}}
        })

    asyncio.create_task(simulate_response())
    res = await mock_ws.request(
        MessageOpcode.SET_REACTION,
        {"chatId": 123, "messageId": "msg1", "reaction": {"reactionType": "EMOJI", "id": "👍"}},
        timeout=1.0
    )
    assert res.get("opcode") == MessageOpcode.SET_REACTION
    assert res.get("payload", {}).get("reactionInfo", {}).get("totalCount") == 1
    assert len(mock_ws._conn.sent) == 1
    sent_data = json.loads(mock_ws._conn.sent[0])
    assert sent_data["seq"] == 1
    assert sent_data["opcode"] == 178


@pytest.mark.asyncio
async def test_ws_request_api_error(mock_ws):
    async def simulate_error():
        await asyncio.sleep(0.01)
        # Server responds with cmd=3 or error payload
        mock_ws._pending_requests[1].set_result({
            "ver": 10,
            "cmd": 3,
            "seq": 1,
            "opcode": MessageOpcode.SET_REACTION,
            "payload": {"error": "proto.payload", "message": "Expected map at 11"}
        })

    asyncio.create_task(simulate_error())
    with pytest.raises(APIError) as exc_info:
        await mock_ws.request(MessageOpcode.SET_REACTION, timeout=1.0)
    assert "Expected map at 11" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ws_request_timeout(mock_ws):
    with pytest.raises(TimeoutError):
        await mock_ws.request(MessageOpcode.CHAT_INFO, timeout=0.05)


@pytest.mark.asyncio
async def test_messages_reaction_and_chat_methods(mock_ws):
    messages = Messages({}, None)

    async def mock_auto_reply():
        while True:
            await asyncio.sleep(0.005)
            for s, fut in list(mock_ws._pending_requests.items()):
                if not fut.done():
                    fut.set_result({"ver": 10, "cmd": 1, "seq": s, "payload": {"success": True}})

    task = asyncio.create_task(mock_auto_reply())
    try:
        # Test set_reaction
        r1 = await messages.set_reaction(mock_ws, "-100", "m1", "👍")
        assert r1.get("payload", {}).get("success") is True

        # Test remove_reaction
        r2 = await messages.remove_reaction(mock_ws, "-100", "m1")
        assert r2.get("payload", {}).get("success") is True

        # Test get_reactions
        r3 = await messages.get_reactions(mock_ws, "-100", ["m1", "m2"])
        assert r3.get("payload", {}).get("success") is True

        # Test mark_as_read
        r4 = await messages.mark_as_read(mock_ws, "-100", "m1")
        assert r4.get("payload", {}).get("success") is True

        # Test join_chat
        r5 = await messages.join_chat(mock_ws, "https://ok.ru/messages/join/xyz")
        assert r5.get("payload", {}).get("success") is True

        # Test leave_chat
        r6 = await messages.leave_chat(mock_ws, "-100")
        assert r6.get("payload", {}).get("success") is True

        # Test add_chat_members
        r7 = await messages.add_chat_members(mock_ws, "-100", ["111", "222"])
        assert r7.get("payload", {}).get("success") is True

        # Test get_chat_history
        r8 = await messages.get_chat_history(mock_ws, "-100", count=10)
        assert r8.get("payload", {}).get("success") is True
    finally:
        task.cancel()


def test_vanus_event_decorators(sample_vanus):
    @sample_vanus.on_reaction()
    async def reaction_handler(event):
        pass

    @sample_vanus.on_typing()
    async def typing_handler(event):
        pass

    @sample_vanus.on_read()
    async def read_handler(event):
        pass

    @sample_vanus.on_presence()
    async def presence_handler(event):
        pass

    @sample_vanus.on_event(MessageOpcode.CHATS_LIST)
    async def raw_event_handler(event):
        pass

    assert reaction_handler in sample_vanus.reaction_handlers
    assert typing_handler in sample_vanus.typing_handlers
    assert read_handler in sample_vanus.read_handlers
    assert presence_handler in sample_vanus.presence_handlers
    assert raw_event_handler in sample_vanus.event_handlers[MessageOpcode.CHATS_LIST]
