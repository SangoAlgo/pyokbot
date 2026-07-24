import pytest
from pyokbot.messages import Messages


@pytest.fixture
def messages():
    return Messages({"id": "bot123"}, None)


class TestGenerateMessageObject:
    def test_valid_user_message(self, messages, raw_opcode128_message):
        result = messages.generate_message_object(raw_opcode128_message)
        assert result is not None
        assert result["type"] == "user"
        assert result["text"] == "hello"
        assert result["id"] == "msg_100"
        assert result["user"]["id"] == "12345"
        assert result["chat"]["id"] == "67890"

    def test_bot_own_message(self, messages):
        msg = {
            "opcode": 128,
            "ver": 10,
            "payload": {
                "chatId": "67890",
                "message": {
                    "id": "msg_200",
                    "text": "bot reply",
                    "sender": "bot123",
                    "time": 1234567890,
                    "cid": "cid_200",
                },
            },
        }
        result = messages.generate_message_object(msg)
        assert result is not None
        assert result["type"] == "bot"

    def test_wrong_opcode(self, messages):
        msg = {"opcode": 64, "payload": {"message": {"sender": "12345"}}}
        result = messages.generate_message_object(msg)
        assert result is None

    def test_no_message_in_payload(self, messages):
        msg = {"opcode": 128, "payload": {}}
        result = messages.generate_message_object(msg)
        assert result is None

    def test_no_sender(self, messages):
        msg = {"opcode": 128, "payload": {"message": {}}}
        result = messages.generate_message_object(msg)
        assert result is None

    def test_payload_not_dict(self, messages):
        msg = {"opcode": 128, "payload": "not dict"}
        result = messages.generate_message_object(msg)
        assert result is None

    def test_ver_9_not_supported(self, messages, raw_opcode128_message):
        msg = dict(raw_opcode128_message)
        msg["ver"] = 9
        result = messages.generate_message_object(msg)
        assert result is None

    def test_photo_message_attaches(self, messages, raw_opcode128_photo_message):
        result = messages.generate_message_object(raw_opcode128_photo_message)
        assert result is not None
        assert result["attaches"] is not None
        assert len(result["attaches"]) == 1
        assert result["attaches"][0]["_type"] == "PHOTO"

    def test_has_reply_fields(self, messages, raw_opcode128_message):
        result = messages.generate_message_object(raw_opcode128_message)
        assert result["is_reply"] is False
        assert result["reply"] is None
        assert result["message"]["time"] is not None
        assert result["message"]["cid"] is not None

    def test_user_url_format(self, messages, raw_opcode128_message):
        result = messages.generate_message_object(raw_opcode128_message)
        assert result["user"]["url"] == "https://m.ok.ru/profile/12345"
