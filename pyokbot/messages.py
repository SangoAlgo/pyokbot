from __future__ import annotations

import json
import random
import time
from typing import TYPE_CHECKING, Any

import aiohttp
from sulguk import transform_html

from .errors import APIError, TimeoutError, UploadError
from .opcodes import MessageOpcode

if TYPE_CHECKING:
    from .ws import Ws

TYPE_BRIDGE: dict[str, str | None] = {
    "bold": "STRONG",
    "text_link": "LINK",
    "underline": "UNDERLINE",
    "code": "CODE",
    "pre": "MONOSPACED",
    "italic": "EMPHASIZED",
    "strikethrough": "STRIKETHROUGH",
    "heading": "HEADING",
}


class Messages:

    def __init__(self, bot_info: dict, session: aiohttp.ClientSession) -> None:
        self.bot_info = bot_info
        self._session = session

    @staticmethod
    def _to_ok(entities: list) -> list[dict]:
        parsed: list[dict] = []
        for entity in entities:
            t = entity.get("type")
            if t == "text_link":
                url = entity.get("url", "")
                if url.startswith("http"):
                    parsed.append({
                        "type": TYPE_BRIDGE.get(t),
                        "from": entity.get("offset"),
                        "length": entity.get("length"),
                        "attributes": {"url": url}
                    })
                else:
                    parsed.append({
                        "type": "USER_MENTION",
                        "from": entity.get("offset"),
                        "length": entity.get("length"),
                        "entityId": int(url)
                    })
            elif t == "bold":
                offset = entity.get("offset")
                last = parsed[-1] if parsed else None
                if last is not None and last.get("type") == "UNDERLINE" and last.get("from") == offset:
                    parsed.pop()
                    parsed.append({
                        "type": "HEADING",
                        "from": offset,
                        "length": entity.get("length"),
                    })
                else:
                    parsed.append({
                        "type": "STRONG",
                        "from": offset,
                        "length": entity.get("length"),
                    })
            else:
                parsed.append({
                    "type": TYPE_BRIDGE.get(t),
                    "from": entity.get("offset"),
                    "length": entity.get("length"),
                })
        return parsed

    async def parse_html(self, html: str) -> list:
        html_one = html.replace("\n", "<br>")
        has_heading = "<h1>" in html or "<h1 " in html
        has_monospaced = "<pre>" in html or "<pre " in html
        if has_heading:
            html_one = html_one.replace("<h1>", "<strong>").replace("</h1>", "</strong>")
        if has_monospaced:
            html_one = html_one.replace("<pre>", "<code>").replace("</pre>", "</code>")
        result = transform_html(html_one)
        parsed = self._to_ok(result.entities)
        if has_heading or has_monospaced:
            orig = transform_html(html)
            parsed_orig = self._to_ok(orig.entities)
            for i in range(len(parsed)):
                if parsed_orig[i].get("type") in ("HEADING", "MONOSPACED"):
                    parsed[i]["type"] = parsed_orig[i]["type"]
        return [parsed, result.text]

    @staticmethod
    def _clean_chat_id(chat_id: str | int) -> int | str:
        """Convert string chat IDs to int if numeric (including negative IDs for group chats)."""
        if isinstance(chat_id, str):
            if chat_id.isdigit() or (chat_id.startswith("-") and chat_id[1:].isdigit()):
                return int(chat_id)
        return chat_id

    def generate_message_object(self, message: dict) -> dict | None:
        if not (message.get("opcode") == MessageOpcode.INCOMING_MESSAGE
                and isinstance(message.get("payload"), dict)
                and isinstance(message["payload"].get("message"), dict)
                and message["payload"]["message"].get("sender") is not None):
            return None
        if message.get("ver") is not None and message.get("ver") < 10:
            return None
        payload = message["payload"]
        msg = payload["message"]
        sender = msg["sender"]
        user_type = "bot" if sender == self.bot_info.get("id") else "user"
        link = msg.get("link")
        is_reply = isinstance(link, dict) and isinstance(link.get("message"), dict)
        full_reply = None
        if is_reply:
            link_msg = link["message"]
            full_reply = {
                "text": link_msg.get("text"),
                "message": {
                    "id": link_msg.get("id"),
                    "time": link_msg.get("time"),
                    "cid": link_msg.get("cid"),
                },
                "user": {
                    "id": link_msg.get("sender"),
                    "name": None,
                    "url": f'https://m.ok.ru/profile/{link_msg.get("sender")}',
                },
                "attaches": link_msg.get("attaches"),
            }
        # Extract keyboards if present
        inline_keyboard = None
        reply_keyboard = None
        raw_attaches = msg.get("attaches") or []
        for att in raw_attaches:
            if isinstance(att, dict):
                atype = att.get("_type")
                if atype == "INLINE_KEYBOARD":
                    inline_keyboard = {
                        "callbackId": att.get("callbackId"),
                        "buttons": att.get("keyboard", {}).get("buttons", []),
                    }
                elif atype == "REPLY_KEYBOARD":
                    reply_keyboard = {
                        "buttons": att.get("keyboard", []),
                        "defaultInputDisabled": att.get("defaultInputDisabled", False),
                    }

        full_dict = {
            "type": user_type,
            "text": msg.get("text"),
            "is_reply": is_reply,
            "id": msg.get("id"),
            "message": {
                "prevMessageId": payload.get("prevMessageId"),
                "time": msg.get("time"),
                "ttl": payload.get("ttl"),
                "cid": msg.get("cid"),
            },
            "user": {
                "id": sender,
                "name": None,
                "avatar": None,
                "url": f'https://m.ok.ru/profile/{sender}',
            },
            "chat": {
                "id": payload.get("chatId"),
            },
            "reply": full_reply,
            "attaches": msg.get("attaches"),
            "inline_keyboard": inline_keyboard,
            "reply_keyboard": reply_keyboard,
            "buttons": inline_keyboard["buttons"] if inline_keyboard else (reply_keyboard["buttons"] if reply_keyboard else None),
        }
        return full_dict

    async def upload_file(
        self,
        file_path: str,
        upload_url: str,
        file_type: str = "",
        file_name: str | None = None,
        token: str | None = None,
    ) -> str:
        try:
            if file_path.startswith("http"):
                async with self._session.get(file_path) as resp:
                    blob = await resp.read()
            else:
                with open(file_path, "rb") as f:
                    blob = f.read()
        except (OSError, aiohttp.ClientError) as e:
            raise UploadError(f"Could not read file {file_path}: {e}") from e

        data = aiohttp.FormData()
        content_types = {
            "AUDIO": "audio/mpeg",
            "PHOTO": "image/jpeg",
            "VIDEO": "video/mp4",
        }
        ct = content_types.get(file_type, "application/octet-stream")
        data.add_field("file", blob, filename=file_name or "file", content_type=ct)
        if token is not None:
            data.add_field("token", token)
        try:
            async with self._session.post(upload_url, data=data) as resp:
                return await resp.text()
        except aiohttp.ClientError as e:
            raise UploadError(f"Upload to {upload_url} failed: {e}") from e

    async def send_message(
        self,
        ws: Ws,
        chat_id: str | int,
        message_text: str,
        parse_mode: str | None = None,
    ) -> int:
        parse_elements: list = []
        if parse_mode == "html":
            result = await self.parse_html(message_text)
            message_text = result[1]
            parse_elements = result[0]
        cid = int(chat_id) if isinstance(chat_id, str) and (chat_id.isdigit() or (chat_id.startswith("-") and chat_id[1:].isdigit())) else chat_id
        return await ws.send_packet(
            MessageOpcode.SEND_MESSAGE,
            {
                "notify": True,
                "type": "USER",
                "attachMEL": True,
                "chatId": cid,
                "message": {
                    "cid": int(time.time() * 1000),
                    "text": message_text,
                    "detectShare": False,
                    "elements": parse_elements,
                }
            }
        )

    async def send_reply(
        self,
        ws: Ws,
        message: dict,
        message_text: str,
        parse_mode: str | None = None,
        reply_to_repl: bool = False,
    ) -> int:
        parse_elements: list = []
        if parse_mode == "html":
            result = await self.parse_html(message_text)
            message_text = result[1]
            parse_elements = result[0]
        reply_id = (
            message.get("reply", {}).get("message", {}).get("id")
            if reply_to_repl
            else message.get("id")
        )
        chat_id = message.get("chat", {}).get("id")
        cid = self._clean_chat_id(chat_id)
        return await ws.send_packet(
            MessageOpcode.SEND_MESSAGE,
            {
                "notify": True,
                "type": "USER",
                "attachMEL": True,
                "chatId": cid,
                "message": {
                    "cid": int(time.time() * 1000),
                    "text": message_text,
                    "detectShare": False,
                    "elements": parse_elements,
                    "link": {"type": "REPLY", "messageId": str(reply_id)},
                },
            },
        )

    async def send_photo(
        self,
        ws: Ws,
        chat_id: str | int,
        photo_file_path: str,
        caption: str | None = None,
        repl_to_message: str | None = None,
        parse_mode: str | None = None,
    ) -> dict | None:
        parse_elements: list = []
        if caption:
            if parse_mode == "html":
                result = await self.parse_html(caption)
                caption = result[1]
                parse_elements = result[0]
        cid = self._clean_chat_id(chat_id)
        await ws.send_packet(
            MessageOpcode.REQUEST_UPLOAD, {"chatId": cid, "type": "PHOTO"}
        )
        await ws.send_packet(
            MessageOpcode.PHOTO_UPLOAD, {"count": 1, "profile": False}
        )
        msg = await ws.wait_for_message(MessageOpcode.PHOTO_UPLOAD, timeout=15)
        if msg is None:
            raise TimeoutError("Photo upload URL: server did not respond in time")
        payload = msg.get("payload")
        if not isinstance(payload, dict):
            raise APIError("Photo upload: server returned an unexpected response")
        upload_url = payload.get("url")
        if not upload_url:
            raise APIError("Photo upload: server did not provide an upload URL")
        response_text = await self.upload_file(photo_file_path, upload_url, file_type="PHOTO")
        try:
            photos = json.loads(response_text).get("photos")
        except json.JSONDecodeError as e:
            raise UploadError(f"Upload response was not valid JSON: {response_text[:200]}") from e
        if not photos:
            raise UploadError(f"No photo data in upload response: {response_text[:200]}")
        token = next(iter(photos.values())).get("token")
        if not token:
            raise UploadError("Photo upload finished but no token was returned")
        now_cid = int(time.time() * 1000)
        await ws.send_packet(
            MessageOpcode.TELEMETRY,
            {
                "events": [
                    {"type": "ACTION", "event": "ATTACH_PHOTO", "params": {}, "time": now_cid},
                    {"type": "ACTION", "event": "ATTACH_PHOTO", "params": {}, "time": now_cid + 100},
                ]
            },
        )
        pkt: dict[str, Any] = {
            "notify": True,
            "type": "USER",
            "attachMEL": True,
            "chatId": cid,
            "message": {
                "cid": now_cid,
                "text": caption or "",
                "detectShare": False,
                "elements": parse_elements,
                "attaches": [{"_type": "PHOTO", "photoToken": token}],
            },
        }
        if repl_to_message is not None:
            pkt["message"]["link"] = {"type": "REPLY", "messageId": str(repl_to_message)}
        await ws.send_packet(MessageOpcode.SEND_MESSAGE, pkt)
        confirmation = await ws.wait_for_message(MessageOpcode.SEND_MESSAGE, timeout=15)
        if confirmation is None:
            raise TimeoutError("Photo send: no confirmation from server")
        return confirmation

    async def send_video(
        self,
        ws: Ws,
        chat_id: str | int,
        video_file_path: str,
        caption: str | None = None,
        repl_to_message: str | None = None,
        parse_mode: str | None = None,
    ) -> bool:
        parse_elements: list = []
        if caption and parse_mode == "html":
            result = await self.parse_html(caption)
            caption = result[1]
            parse_elements = result[0]
        cid = self._clean_chat_id(chat_id)
        await ws.send_packet(
            MessageOpcode.REQUEST_UPLOAD, {"chatId": cid, "type": "VIDEO"}
        )
        await ws.send_packet(
            MessageOpcode.MEDIA_UPLOAD, {"count": 1, "audio": False}
        )
        msg = await ws.wait_for_message(MessageOpcode.MEDIA_UPLOAD)
        if msg is None:
            raise TimeoutError("Video upload URL: server did not respond in time")
        try:
            info = msg["payload"]["info"][0]
        except (KeyError, IndexError, TypeError) as e:
            raise APIError("Video upload: server returned an unexpected response") from e
        await self.upload_file(video_file_path, info["url"])
        now_cid = int(time.time() * 1000)
        pkt: dict[str, Any] = {
            "notify": True,
            "type": "USER",
            "attachMEL": True,
            "chatId": cid,
            "message": {
                "cid": now_cid,
                "text": caption or "",
                "detectsShare": False,
                "elements": parse_elements,
                "attaches": [{"_type": "VIDEO", "token": info["token"]}],
            },
        }
        if repl_to_message is not None:
            pkt["message"]["link"] = {"type": "REPLY", "messageId": str(repl_to_message)}
        await ws.send_packet(MessageOpcode.SEND_MESSAGE, pkt)
        return True

    async def send_file(
        self,
        ws: Ws,
        chat_id: str | int,
        file_path: str,
        title: str | None = None,
        repl_to_message: str | None = None,
    ) -> bool:
        cid = self._clean_chat_id(chat_id)
        await ws.send_packet(
            MessageOpcode.REQUEST_UPLOAD, {"chatId": cid, "type": "FILE"}
        )
        await ws.send_packet(
            MessageOpcode.FILE_UPLOAD, {"count": 1}
        )
        msg = await ws.wait_for_message(MessageOpcode.FILE_UPLOAD)
        if msg is None:
            raise TimeoutError("File upload URL: server did not respond in time")
        try:
            info = msg["payload"]["info"][0]
        except (KeyError, IndexError, TypeError) as e:
            raise APIError("File upload: server returned an unexpected response") from e
        await self.upload_file(file_path, info["url"], file_name=title, token=info["token"])
        publish = await ws.wait_for_message(MessageOpcode.FILE_PUBLISHED)
        if publish is None:
            raise TimeoutError("File upload: server did not confirm publication")
        now_cid = int(time.time() * 1000)
        pkt: dict[str, Any] = {
            "notify": True,
            "type": "USER",
            "attachMEL": True,
            "chatId": cid,
            "message": {
                "cid": now_cid,
                "text": "",
                "detectsShare": False,
                "elements": [],
                "attaches": [{"_type": "FILE", "token": info["token"]}],
            },
        }
        if repl_to_message is not None:
            pkt["message"]["link"] = {"type": "REPLY", "messageId": str(repl_to_message)}
        await ws.send_packet(MessageOpcode.SEND_MESSAGE, pkt)
        return True

    async def send_voice(
        self,
        ws: Ws,
        chat_id: str | int,
        voice_file_path: str,
        repl_to_message: str | None = None,
    ) -> bool:
        cid = self._clean_chat_id(chat_id)
        await ws.send_packet(
            MessageOpcode.REQUEST_UPLOAD, {"chatId": cid, "type": "AUDIO"}
        )
        await ws.send_packet(
            MessageOpcode.MEDIA_UPLOAD, {"count": 1, "audio": True}
        )
        msg = await ws.wait_for_message(MessageOpcode.MEDIA_UPLOAD)
        if msg is None:
            raise TimeoutError("Voice upload URL: server did not respond in time")
        try:
            info = msg["payload"]["info"][0]
        except (KeyError, IndexError, TypeError) as e:
            raise APIError("Voice upload: server returned an unexpected response") from e
        await self.upload_file(voice_file_path, info["url"])
        publish = await ws.wait_for_message(MessageOpcode.FILE_PUBLISHED)
        if publish is None:
            raise TimeoutError("Voice upload: server did not confirm publication")
        now_cid = int(time.time() * 1000)
        pkt: dict[str, Any] = {
            "notify": True,
            "type": "USER",
            "chatId": cid,
            "message": {
                "cid": now_cid,
                "text": "",
                "attaches": [{"_type": "AUDIO", "token": info["token"]}],
            },
        }
        if repl_to_message is not None:
            pkt["message"]["link"] = {"type": "REPLY", "messageId": str(repl_to_message)}
        await ws.send_packet(MessageOpcode.SEND_MESSAGE, pkt)
        return True

    async def writing_emulation(self, ws: Ws, chat_id: str | int) -> bool:
        cid = self._clean_chat_id(chat_id)
        await ws.send_packet(
            MessageOpcode.REQUEST_UPLOAD, {"chatId": cid, "type": "TEXT"}
        )
        return True

    async def edit_message_text(
        self,
        ws: Ws,
        chat_id: str | int,
        message_id: str,
        message_text: str,
        parse_mode: str | None = None,
    ) -> bool:
        parse_elements: list = []
        if parse_mode == "html":
            result = await self.parse_html(message_text)
            message_text = result[1]
            parse_elements = result[0]
        cid = self._clean_chat_id(chat_id)
        await ws.request(
            MessageOpcode.EDIT_MESSAGE,
            {
                "chatId": cid,
                "messageId": str(message_id),
                "text": message_text,
                "elements": parse_elements,
                "attachments": [],
            },
        )
        return True

    async def pin_chat_message(self, ws: Ws, chat_id: str | int, message_id: str) -> bool:
        cid = self._clean_chat_id(chat_id)
        await ws.send_packet(
            MessageOpcode.CHAT_SETTINGS,
            {"chatId": cid, "pinMessageId": str(message_id), "notifyPin": False},
        )
        return True

    async def change_chat_title(self, ws: Ws, chat_id: str | int, title: str) -> bool:
        cid = self._clean_chat_id(chat_id)
        await ws.send_packet(
            MessageOpcode.CHAT_SETTINGS, {"chatId": cid, "theme": title}
        )
        return True

    async def change_chat_photo(self, ws: Ws, chat_id: str | int, photo_file_path: str) -> bool:
        cid = self._clean_chat_id(chat_id)
        await ws.send_packet(
            MessageOpcode.PHOTO_UPLOAD, {"count": 1, "profile": False}
        )
        msg = await ws.wait_for_message(MessageOpcode.PHOTO_UPLOAD)
        if msg is None:
            raise TimeoutError("Chat photo upload: server did not respond in time")
        upload_url = msg.get("payload", {}).get("url")
        if not upload_url:
            raise APIError("Chat photo upload: server did not provide an upload URL")
        response = await self.upload_file(photo_file_path, upload_url)
        try:
            response = json.loads(response).get("photos")
        except json.JSONDecodeError as e:
            raise UploadError(f"Chat photo upload response was not JSON: {response[:200]}") from e
        token = next(iter(response.values())).get("token") if response else None
        if not token:
            raise UploadError("Chat photo upload: no token in response")
        now_cid = int(time.time() * 1000)
        await ws.send_packet(
            MessageOpcode.SEND_MESSAGE,
            {
                "chatId": cid,
                "message": {
                    "cid": now_cid,
                    "attaches": [{"_type": "CONTROL", "event": "icon", "photoToken": token}],
                },
            },
        )
        return True

    async def delete_member(
        self,
        ws: Ws,
        chat_id: str | int,
        member_ids: list[str | int] | None = None,
        member_id: str | int | None = None,
    ) -> bool:
        cid = self._clean_chat_id(chat_id)
        raw_ids = member_ids if member_ids is not None else [member_id]
        ids = [int(i) if str(i).isdigit() else i for i in raw_ids if i is not None]
        await ws.send_packet(
            MessageOpcode.BLOCK_MEMBER,
            {
                "operation": "add",
                "showHistory": True,
                "chatId": cid,
                "userIds": ids,
                "type": "BLOCKED_MEMBER",
                "cleanMsgPeriod": 0,
            },
        )
        return True

    async def delete_message(
        self,
        ws: Ws,
        chat_id: str | int,
        message_ids: list[str] | None = None,
        message_id: str | None = None,
    ) -> bool:
        cid = self._clean_chat_id(chat_id)
        raw_ids = message_ids if message_ids is not None else [str(message_id)]
        ids = [str(i) for i in raw_ids if i is not None]
        await ws.send_packet(
            MessageOpcode.DELETE_MESSAGE,
            {"chatId": cid, "messageIds": ids, "complaint": None, "forMe": False},
        )
        await ws.send_packet(
            MessageOpcode.DELETE_MESSAGE,
            {"chatId": cid, "messageIds": ids},
            cmd=1,
        )
        return True

    async def clear_chat_history(
        self, ws: Ws, chat_id: str | int, for_all: bool | None = None
    ) -> bool:
        cid = self._clean_chat_id(chat_id)
        await ws.send_packet(
            MessageOpcode.CLEAR_HISTORY,
            {
                "chatId": cid,
                "lastEventTime": int(time.time() * 1000),
                "forAll": for_all,
            },
        )
        return True

    # === REACTIONS ===

    async def set_reaction(
        self,
        ws: Ws,
        chat_id: str | int,
        message_id: str,
        reaction: str = "👍",
    ) -> dict:
        """Set an emoji reaction on a message in a chat."""
        cid = int(chat_id) if isinstance(chat_id, str) and (chat_id.isdigit() or (chat_id.startswith("-") and chat_id[1:].isdigit())) else chat_id
        return await ws.request(
            MessageOpcode.SET_REACTION,
            {
                "chatId": cid,
                "messageId": str(message_id),
                "reaction": {"reactionType": "EMOJI", "id": reaction},
            },
        )

    async def remove_reaction(
        self,
        ws: Ws,
        chat_id: str | int,
        message_id: str,
    ) -> dict:
        """Remove a reaction from a message."""
        cid = int(chat_id) if isinstance(chat_id, str) and (chat_id.isdigit() or (chat_id.startswith("-") and chat_id[1:].isdigit())) else chat_id
        return await ws.request(
            MessageOpcode.REMOVE_REACTION,
            {
                "chatId": cid,
                "messageId": str(message_id),
            },
        )

    async def get_reactions(
        self,
        ws: Ws,
        chat_id: str | int,
        message_ids: list[str],
    ) -> dict:
        """Fetch reactions for a list of message IDs."""
        cid = int(chat_id) if isinstance(chat_id, str) and (chat_id.isdigit() or (chat_id.startswith("-") and chat_id[1:].isdigit())) else chat_id
        return await ws.request(
            MessageOpcode.GET_REACTIONS,
            {
                "chatId": cid,
                "messageIds": [str(m) for m in message_ids],
            },
        )

    async def get_reacted_users(
        self,
        ws: Ws,
        chat_id: str | int,
        message_id: str,
        reaction: str = "👍",
        marker: int | None = None,
        count: int = 50,
    ) -> dict:
        """Fetch list of users who reacted to a message."""
        cid = int(chat_id) if isinstance(chat_id, str) and (chat_id.isdigit() or (chat_id.startswith("-") and chat_id[1:].isdigit())) else chat_id
        payload: dict[str, Any] = {
            "chatId": cid,
            "messageId": str(message_id),
            "reaction": reaction,
            "count": count,
        }
        if marker is not None:
            payload["marker"] = marker
        return await ws.request(MessageOpcode.GET_REACTED_USERS, payload)

    # === READ STATUS & CHAT HISTORY ===

    async def mark_as_read(
        self,
        ws: Ws,
        chat_id: str | int,
        message_id: str,
        mark: int | None = None,
    ) -> dict:
        """Mark a message as read."""
        cid = int(chat_id) if isinstance(chat_id, str) and (chat_id.isdigit() or (chat_id.startswith("-") and chat_id[1:].isdigit())) else chat_id
        return await ws.request(
            MessageOpcode.READ_MESSAGE,
            {
                "chatId": cid,
                "messageId": str(message_id),
                "mark": mark or int(time.time() * 1000),
                "type": "READ_MESSAGE",
            },
        )

    async def get_chat_history(
        self,
        ws: Ws,
        chat_id: str | int,
        from_time: int | None = None,
        count: int = 25,
        backward: int | None = None,
        forward: int = 0,
    ) -> dict:
        """Fetch message history for a chat."""
        cid = int(chat_id) if isinstance(chat_id, str) and (chat_id.isdigit() or (chat_id.startswith("-") and chat_id[1:].isdigit())) else chat_id
        limit = backward if backward is not None else count
        return await ws.request(
            MessageOpcode.CHAT_HISTORY,
            {
                "chatId": cid,
                "from": from_time or int(time.time() * 1000),
                "backward": limit,
                "forward": forward,
            },
        )

    # === CHAT INVITATIONS & PARTICIPANTS ===

    async def join_chat(self, ws: Ws, link: str) -> dict:
        """Join a chat via invite link."""
        return await ws.request(MessageOpcode.JOIN_CHAT, {"link": link})

    async def leave_chat(self, ws: Ws, chat_id: str | int) -> dict:
        """Leave a chat."""
        cid = int(chat_id) if isinstance(chat_id, str) and (chat_id.isdigit() or (chat_id.startswith("-") and chat_id[1:].isdigit())) else chat_id
        return await ws.request(MessageOpcode.LEAVE_CHAT, {"chatId": cid})

    async def add_chat_members(
        self,
        ws: Ws,
        chat_id: str | int,
        user_ids: list[str | int],
    ) -> dict:
        """Add users to a chat."""
        cid = int(chat_id) if isinstance(chat_id, str) and (chat_id.isdigit() or (chat_id.startswith("-") and chat_id[1:].isdigit())) else chat_id
        uids = [int(u) if str(u).isdigit() else u for u in user_ids]
        return await ws.request(MessageOpcode.ADD_MEMBERS, {"chatId": cid, "userIds": uids})

    async def get_chat_participants(
        self,
        ws: Ws,
        chat_id: str | int,
        last_event_time: int | None = None,
    ) -> dict:
        """Get participant list of a chat."""
        cid = int(chat_id) if isinstance(chat_id, str) and (chat_id.isdigit() or (chat_id.startswith("-") and chat_id[1:].isdigit())) else chat_id
        return await ws.request(
            MessageOpcode.CHAT_PARTICIPANTS,
            {"chatId": cid, "lastEventTime": last_event_time or 0},
        )

    async def subscribe_chat(self, ws: Ws, chat_id: str | int, subscribe: bool = True) -> dict:
        """Subscribe or unsubscribe to live chat events."""
        cid = int(chat_id) if isinstance(chat_id, str) and (chat_id.isdigit() or (chat_id.startswith("-") and chat_id[1:].isdigit())) else chat_id
        return await ws.request(
            MessageOpcode.SUBSCRIBE_CHAT,
            {"chatId": cid, "subscribe": subscribe},
        )

    # === CONTACTS, PRESENCE & PROFILES ===

    async def get_contacts(
        self,
        ws: Ws,
        contact_ids: list[str | int],
        contact_type: str = "USER",
    ) -> dict:
        """Fetch user contact/profile info for a list of user IDs via WebSocket (Opcode 32)."""
        uids = [int(u) if str(u).isdigit() else u for u in contact_ids]
        return await ws.request(
            MessageOpcode.GET_CONTACTS,
            {"contactIds": uids, "contactType": contact_type},
        )

    async def get_presence(
        self,
        ws: Ws,
        contact_ids: list[str | int],
    ) -> dict:
        """Fetch real-time presence/online status for user IDs via WebSocket (Opcode 35)."""
        uids = [int(u) if str(u).isdigit() else u for u in contact_ids]
        return await ws.request(
            MessageOpcode.GET_PRESENCE,
            {"contactIds": uids},
        )

    async def get_user_photos(
        self,
        ws: Ws,
        user_id: str | int,
        from_index: int = 0,
    ) -> dict:
        """Fetch all photo URLs for a user via WebSocket (Opcode 39)."""
        uid = int(user_id) if str(user_id).isdigit() else user_id
        return await ws.request(
            MessageOpcode.GET_USER_PHOTOS,
            {"contactId": uid, "from": from_index},
        )

    # === INTERACTIVE KEYBOARDS & BOT COMMANDS ===

    async def click_inline_button(
        self,
        ws: Ws,
        callback_id: str,
        payload: str,
        button_type: str = "CALLBACK",
        timeout: float = 5.0,
    ) -> dict:
        """Click an inline keyboard button (Opcode 118) in OK.ru messenger.

        Args:
            ws: Connected WebSocket instance.
            callback_id: callbackId from the message's INLINE_KEYBOARD attach.
            payload: Payload string associated with the button.
            button_type: Button type (default: 'CALLBACK').
            timeout: Response timeout in seconds.

        Returns:
            Server response (e.g. {'success': True}).
        """
        return await ws.request(
            MessageOpcode.CALLBACK_ANSWER,
            {
                "callbackId": callback_id,
                "type": button_type,
                "payload": payload,
            },
            timeout=timeout,
        )

    async def send_inline_keyboard(
        self,
        ws: Ws,
        chat_id: str | int,
        message_text: str,
        keyboard: Any,
        parse_mode: str | None = None,
        group_token: str | None = None,
    ) -> dict:
        """Send a message with an inline keyboard.

        If group_token is provided, dispatches via the official OK.ru Bot API gateway.
        Otherwise dispatches via WebSocket attachment.
        """
        cid = self._clean_chat_id(chat_id)
        attach = keyboard.to_attach() if hasattr(keyboard, "to_attach") else keyboard

        if group_token:
            url = f"https://api.ok.ru/graph.chat.messages?access_token={group_token}"
            bot_api_body = {
                "recipient": {"chat_id": f"chat:{cid}" if isinstance(cid, int) and cid < 0 else str(cid)},
                "message": {
                    "text": message_text,
                    "attachment": keyboard.to_bot_api() if hasattr(keyboard, "to_bot_api") else attach,
                },
            }
            async with self._session.post(url, json=bot_api_body) as resp:
                return await resp.json()

        now_cid = int(time.time() * 1000)
        elements = await self.parse_html(message_text) if parse_mode == "html" else None
        return await ws.request(
            MessageOpcode.SEND_MESSAGE,
            {
                "chatId": cid,
                "message": {
                    "cid": now_cid,
                    "text": message_text,
                    "elements": elements,
                    "attaches": [attach],
                },
            },
        )
