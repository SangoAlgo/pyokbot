import pytest


def make_filter(filters="user", text=None, content_types=None, commands=None):
    return {"filters": filters, "text": text, "content_types": content_types, "commands": commands}


class TestMessageFilter:
    def test_no_filters_matches_anything(self, sample_vanus, text_message):
        f = make_filter(filters=None, text=None, content_types=None, commands=None)
        result = sample_vanus.message_filter(f, text_message)
        assert result is not None
        assert result.text == "hello world"

    def test_user_filter_matches_user(self, sample_vanus, text_message):
        f = make_filter(filters="user")
        result = sample_vanus.message_filter(f, text_message)
        assert result is not None

    def test_user_filter_rejects_bot(self, sample_vanus, bot_message):
        f = make_filter(filters="user")
        result = sample_vanus.message_filter(f, bot_message)
        assert result is None

    def test_bot_filter_matches_bot(self, sample_vanus, bot_message):
        f = make_filter(filters="bot")
        result = sample_vanus.message_filter(f, bot_message)
        assert result is not None

    def test_bot_filter_rejects_user(self, sample_vanus, text_message):
        f = make_filter(filters="bot")
        result = sample_vanus.message_filter(f, text_message)
        assert result is None

    def test_text_exact_match(self, sample_vanus, text_message):
        f = make_filter(text="hello world")
        result = sample_vanus.message_filter(f, text_message)
        assert result is not None

    def test_text_no_match(self, sample_vanus, text_message):
        f = make_filter(text="goodbye")
        result = sample_vanus.message_filter(f, text_message)
        assert result is None

    def test_text_list_match(self, sample_vanus, text_message):
        f = make_filter(text=["hi", "hello world", "bye"])
        result = sample_vanus.message_filter(f, text_message)
        assert result is not None

    def test_text_list_no_match(self, sample_vanus, text_message):
        f = make_filter(text=["hi", "bye"])
        result = sample_vanus.message_filter(f, text_message)
        assert result is None

    def test_command_match(self, sample_vanus, command_message):
        f = make_filter(commands=["start"])
        result = sample_vanus.message_filter(f, command_message)
        assert result is not None

    def test_command_no_match(self, sample_vanus, command_message):
        f = make_filter(commands=["help"])
        result = sample_vanus.message_filter(f, command_message)
        assert result is None

    def test_command_no_text_does_not_crash(self, sample_vanus, photo_message):
        f = make_filter(commands=["start"])
        result = sample_vanus.message_filter(f, photo_message)
        assert result is None

    def test_content_type_photo(self, sample_vanus, photo_message):
        f = make_filter(content_types=["photo"])
        result = sample_vanus.message_filter(f, photo_message)
        assert result is not None

    def test_content_type_video(self, sample_vanus, video_message):
        f = make_filter(content_types=["video"])
        result = sample_vanus.message_filter(f, video_message)
        assert result is not None

    def test_content_type_audio(self, sample_vanus, audio_message):
        f = make_filter(content_types=["audio"])
        result = sample_vanus.message_filter(f, audio_message)
        assert result is not None

    def test_content_type_text(self, sample_vanus, text_message):
        f = make_filter(content_types=["text"])
        result = sample_vanus.message_filter(f, text_message)
        assert result is not None

    def test_content_type_commands(self, sample_vanus, command_message):
        f = make_filter(content_types=["commands"])
        result = sample_vanus.message_filter(f, command_message)
        assert result is not None

    def test_content_type_no_match(self, sample_vanus, text_message):
        f = make_filter(content_types=["photo"])
        result = sample_vanus.message_filter(f, text_message)
        assert result is None

    def test_combined_user_and_command(self, sample_vanus, command_message):
        f = make_filter(filters="user", commands=["start"])
        result = sample_vanus.message_filter(f, command_message)
        assert result is not None

    def test_combined_bot_rejects_command(self, sample_vanus, command_message):
        f = make_filter(filters="bot", commands=["start"])
        result = sample_vanus.message_filter(f, command_message)
        assert result is None

    def test_combined_text_and_content_type(self, sample_vanus, photo_message):
        f = make_filter(text="", content_types=["photo"])
        result = sample_vanus.message_filter(f, photo_message)
        assert result is not None

    def test_does_not_mutate_original_message(self, sample_vanus, photo_message):
        original = dict(photo_message)
        sample_vanus.message_filter(make_filter(content_types=["photo"]), photo_message)
        assert "attaches" in photo_message
        assert photo_message["attaches"] == original["attaches"]

    def test_multiple_commands(self, sample_vanus, command_message):
        f = make_filter(commands=["help", "start", "stop"])
        result = sample_vanus.message_filter(f, command_message)
        assert result is not None

    def test_multiple_commands_no_match(self, sample_vanus, command_message):
        f = make_filter(commands=["help", "stop"])
        result = sample_vanus.message_filter(f, command_message)
        assert result is None

    def test_text_with_commands_filter_no_text(self, sample_vanus, photo_message):
        f = make_filter(filters="user", commands=["photo"])
        result = sample_vanus.message_filter(f, photo_message)
        assert result is None
