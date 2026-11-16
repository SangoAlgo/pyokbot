"""Interactive keyboard models and builders for OK.ru messenger bots.

Supports:
- InlineKeyboard (buttons attached directly to messages: CALLBACK, LINK, etc.)
- ReplyKeyboard (quick-reply buttons replacing or overlaying the input field)
"""

from __future__ import annotations

from typing import Any, Literal

IntentType = Literal["DEFAULT", "POSITIVE", "NEGATIVE"]
ButtonType = Literal["CALLBACK", "LINK", "REQUEST_CONTACT", "REQUEST_GEO_LOCATION"]


class InlineButton:
    """Represents a single inline keyboard button."""

    def __init__(
        self,
        text: str,
        callback_data: str | None = None,
        url: str | None = None,
        intent: IntentType = "DEFAULT",
        button_type: ButtonType | None = None,
    ) -> None:
        self.text = text
        self.intent = intent.upper()
        if url:
            self.type = "LINK"
            self.url = url
            self.payload = None
        else:
            self.type = button_type or "CALLBACK"
            self.payload = callback_data or text
            self.url = None

    def to_dict(self) -> dict[str, Any]:
        """Convert button to OK.ru API JSON dictionary."""
        data: dict[str, Any] = {
            "type": self.type,
            "text": self.text,
            "intent": self.intent,
        }
        if self.type == "LINK" and self.url:
            data["url"] = self.url
        elif self.payload is not None:
            data["payload"] = self.payload
        return data

    def __repr__(self) -> str:
        return f"<InlineButton text={self.text!r} type={self.type!r} intent={self.intent!r}>"


class InlineKeyboard:
    """Builder for inline keyboards (displayed directly under messages)."""

    def __init__(self, callback_id: str | None = None) -> None:
        self.rows: list[list[InlineButton]] = []
        self.callback_id = callback_id

    def add_button(
        self,
        text: str,
        callback_data: str | None = None,
        intent: IntentType = "DEFAULT",
    ) -> InlineKeyboard:
        """Add a callback button to the current or new row."""
        btn = InlineButton(text=text, callback_data=callback_data, intent=intent)
        if not self.rows:
            self.rows.append([])
        self.rows[-1].append(btn)
        return self

    def add_url_button(
        self,
        text: str,
        url: str,
        intent: IntentType = "DEFAULT",
    ) -> InlineKeyboard:
        """Add a URL link button."""
        btn = InlineButton(text=text, url=url, intent=intent)
        if not self.rows:
            self.rows.append([])
        self.rows[-1].append(btn)
        return self

    def row(self, *buttons: InlineButton) -> InlineKeyboard:
        """Add a complete row of buttons."""
        if buttons:
            self.rows.append(list(buttons))
        else:
            self.rows.append([])
        return self

    def to_attach(self) -> dict[str, Any]:
        """Convert keyboard into OK.ru message attachment format."""
        buttons_grid = [
            [b.to_dict() for b in row]
            for row in self.rows
            if row
        ]
        attach: dict[str, Any] = {
            "_type": "INLINE_KEYBOARD",
            "buttons": buttons_grid,
        }
        if self.callback_id:
            attach["callbackId"] = self.callback_id
        return attach

    def to_bot_api(self) -> dict[str, Any]:
        """Convert to official OK.ru / TamTam Bot API attachment schema."""
        buttons_grid = [
            [
                {
                    "type": b.type.lower(),
                    "text": b.text,
                    **({"url": b.url} if b.url else {"payload": b.payload, "intent": b.intent.lower()}),
                }
                for b in row
            ]
            for row in self.rows
            if row
        ]
        return {
            "type": "inline_keyboard",
            "payload": {
                "buttons": buttons_grid,
            },
        }


class ReplyButton:
    """Represents a single reply keyboard button."""

    def __init__(
        self,
        text: str,
        intent: IntentType = "DEFAULT",
    ) -> None:
        self.text = text
        self.intent = intent.upper()

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "type": "message",
            "message": {
                "text": self.text,
                "detectShare": True,
            },
            "intent": self.intent,
        }


class ReplyKeyboard:
    """Builder for reply keyboards (bottom input overlay)."""

    def __init__(self, default_input_disabled: bool = False) -> None:
        self.rows: list[list[ReplyButton]] = []
        self.default_input_disabled = default_input_disabled

    def add_button(self, text: str, intent: IntentType = "DEFAULT") -> ReplyKeyboard:
        btn = ReplyButton(text=text, intent=intent)
        if not self.rows:
            self.rows.append([])
        self.rows[-1].append(btn)
        return self

    def row(self, *buttons: ReplyButton | str) -> ReplyKeyboard:
        row_btns: list[ReplyButton] = []
        for b in buttons:
            if isinstance(b, str):
                row_btns.append(ReplyButton(b))
            else:
                row_btns.append(b)
        self.rows.append(row_btns)
        return self

    def to_attach(self) -> dict[str, Any]:
        grid = [
            [b.to_dict() for b in row]
            for row in self.rows
            if row
        ]
        return {
            "_type": "REPLY_KEYBOARD",
            "keyboard": grid,
            "defaultInputDisabled": self.default_input_disabled,
        }
