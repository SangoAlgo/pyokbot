import pytest


@pytest.fixture
def sample_vanus():
    from pyokbot.client import Vanus
    from pyokbot.ws import Ws
    from pyokbot.login import Login

    login = Login()
    login.AUTHCODE = "test_auth"
    login.okweb_token = "test_token"

    vanus = Vanus.__new__(Vanus)
    vanus.login = login
    vanus.ws = Ws.__new__(Ws)
    vanus.ws.handles_list = []
    vanus._session = None
    vanus._ws_task = None
    vanus._handled_msg_ids = set()
    vanus._cache_path = "/tmp/test_cache.json"
    vanus.users_info_cache = {}
    return vanus


@pytest.fixture
def text_message():
    return {
        "type": "user",
        "text": "hello world",
        "id": "msg_001",
        "user": {"id": "12345"},
        "chat": {"id": "67890"},
        "attaches": None,
    }


@pytest.fixture
def command_message():
    return {
        "type": "user",
        "text": "/start hello",
        "id": "msg_002",
        "user": {"id": "12345"},
        "chat": {"id": "67890"},
        "attaches": None,
    }


@pytest.fixture
def photo_message():
    return {
        "type": "user",
        "text": "",
        "id": "msg_003",
        "user": {"id": "12345"},
        "chat": {"id": "67890"},
        "attaches": [
            {"_type": "PHOTO", "photoToken": "abc123", "url": "https://example.com/photo.jpg", "height": 300, "width": 400},
        ],
    }


@pytest.fixture
def video_message():
    return {
        "type": "user",
        "text": "",
        "id": "msg_004",
        "user": {"id": "12345"},
        "chat": {"id": "67890"},
        "attaches": [
            {"_type": "VIDEO", "token": "vid123", "thumbnail": "https://example.com/thumb.jpg", "height": 720, "width": 1280, "duration": 30},
        ],
    }


@pytest.fixture
def audio_message():
    return {
        "type": "user",
        "text": "",
        "id": "msg_005",
        "user": {"id": "12345"},
        "chat": {"id": "67890"},
        "attaches": [
            {"_type": "AUDIO", "token": "aud123", "url": "https://example.com/audio.mp3", "duration": 120},
        ],
    }


@pytest.fixture
def bot_message():
    return {
        "type": "bot",
        "text": "I am a bot",
        "id": "msg_006",
        "user": {"id": "12345"},
        "chat": {"id": "67890"},
        "attaches": None,
    }


@pytest.fixture
def raw_opcode128_message():
    return {
        "opcode": 128,
        "ver": 10,
        "payload": {
            "chatId": "67890",
            "prevMessageId": "prev_001",
            "message": {
                "id": "msg_100",
                "text": "hello",
                "sender": "12345",
                "time": 1234567890,
                "cid": "cid_001",
            },
        },
    }


@pytest.fixture
def raw_opcode128_photo_message():
    return {
        "opcode": 128,
        "ver": 10,
        "payload": {
            "chatId": "67890",
            "prevMessageId": "prev_002",
            "message": {
                "id": "msg_101",
                "text": "",
                "sender": "12345",
                "time": 1234567891,
                "cid": "cid_002",
                "attaches": [
                    {"_type": "PHOTO", "photoToken": "abc123", "url": "https://example.com/p.jpg", "height": 300, "width": 400},
                ],
            },
        },
    }
