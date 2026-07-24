from pyokbot.messages import Messages


class TestToOk:
    def setup_method(self):
        self.messages = Messages({"id": "bot123"}, None)

    def test_empty_entities(self):
        result = self.messages._to_ok([])
        assert result == []

    def test_bold(self):
        entities = [{"type": "bold", "offset": 0, "length": 4}]
        result = self.messages._to_ok(entities)
        assert result[0]["type"] == "STRONG"

    def test_italic(self):
        entities = [{"type": "italic", "offset": 0, "length": 4}]
        result = self.messages._to_ok(entities)
        assert result[0]["type"] == "EMPHASIZED"

    def test_text_link(self):
        entities = [{"type": "text_link", "offset": 0, "length": 4, "url": "https://example.com"}]
        result = self.messages._to_ok(entities)
        assert result[0]["type"] == "LINK"
        assert result[0]["attributes"]["url"] == "https://example.com"

    def test_user_mention(self):
        entities = [{"type": "text_link", "offset": 0, "length": 4, "url": "12345"}]
        result = self.messages._to_ok(entities)
        assert result[0]["type"] == "USER_MENTION"
        assert result[0]["entityId"] == 12345

    def test_underline(self):
        entities = [{"type": "underline", "offset": 0, "length": 4}]
        result = self.messages._to_ok(entities)
        assert result[0]["type"] == "UNDERLINE"

    def test_code(self):
        entities = [{"type": "code", "offset": 0, "length": 4}]
        result = self.messages._to_ok(entities)
        assert result[0]["type"] == "CODE"

    def test_pre(self):
        entities = [{"type": "pre", "offset": 0, "length": 4}]
        result = self.messages._to_ok(entities)
        assert result[0]["type"] == "MONOSPACED"

    def test_strikethrough(self):
        entities = [{"type": "strikethrough", "offset": 0, "length": 4}]
        result = self.messages._to_ok(entities)
        assert result[0]["type"] == "STRIKETHROUGH"

    def test_heading(self):
        entities = [{"type": "bold", "offset": 0, "length": 6}]
        result = self.messages._to_ok(entities)
        assert result[0]["type"] == "STRONG"

    def test_bold_after_underline_same_offset_creates_heading(self):
        entities = [
            {"type": "underline", "offset": 0, "length": 6},
            {"type": "bold", "offset": 0, "length": 6},
        ]
        result = self.messages._to_ok(entities)
        assert result[0]["type"] == "HEADING"
        assert len(result) == 1

    def test_unknown_type(self):
        entities = [{"type": "unknown_type", "offset": 0, "length": 4}]
        result = self.messages._to_ok(entities)
        assert result[0]["type"] is None
