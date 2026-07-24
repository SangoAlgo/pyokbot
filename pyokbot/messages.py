from __future__ import annotations

import asyncio
import json
import random
import time
from typing import Any, Dict, List, Optional

import aiohttp
from sulguk import transform_html

from .opcodes import MessageOpcode
from .logging_config import logger

TYPE_BRIDGE: Dict[str, str] = {
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

    def __init__(self, bot_info: dict, session: aiohttp.ClientSession):
        self.bot_info = bot_info
        self._session = session

    @staticmethod
    def _to_ok(entities: list) -> list:
        parsed: list = []
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

    def generate_message_object(self, message: dict) -> Optional[dict]:
        if not (message.get("opcode") == MessageOpcode.INCOMING_MESSAGE
                and isinstance(message.get("payload"), dict)
                and isinstance(message["payload"].get("message"), dict)
                and message["payload"]["message"].get("sender") is not None):
            return None
        if message.get("ver") == 10:
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
            }
            return full_dict
        return None

    async def upload_file(
        self,
        file_path: str,
        upload_url: str,
        file_type: str,
        file_name: Optional[str] = None,
        token: Optional[str] = None,
    ) -> str:
        if file_path.startswith("http"):
            async with self._session.get(file_path) as resp:
                blob = await resp.read()
        else:
            with open(file_path, "rb") as f:
                blob = f.read()
        data = aiohttp.FormData()
        if file_type == "AUDIO":
            data.add_field("file", blob, filename=file_name or "file.mp3", content_type="audio/mpeg")
        elif file_type == "PHOTO":
            data.add_field("file", blob, filename=file_name or "file.png", content_type="image/jpeg")
        elif file_type == "VIDEO":
            data.add_field("file", blob, filename=file_name or "file.mp4", content_type="video/mp4")
        if token is not None:
            data.add_field("token", token)
        async with self._session.post(upload_url, data=data) as resp:
            return await resp.text()

    async def send_message(
        self,
        ws,
        chat_id: str,
        message_text: str,
        parse_mode: Optional[str] = None,
    ) -> None:
        parse_elements: list = []
        if parse_mode == "html":
            result = await self.parse_html(message_text)
            message_text = result[1]
            parse_elements = result[0]
        await ws._conn.send(json.dumps({
            "ver": 10,
            "cmd": 0,
            "seq": random.randint(0, 9999),
            "opcode": MessageOpcode.SEND_MESSAGE,
            "payload": {
                "notify": True,
                "type": "USER",
                "attachMEL": True,
                "chatId": chat_id,
                "message": {
                    "cid": int(time.time() * 1000),
                    "text": message_text,
                    "detectShare": False,
                    "elements": parse_elements,
                }
            }
        }))

    async def send_reply(
        self,
        ws,
        message: dict,
        message_text: str,
        parse_mode: Optional[str] = None,
        reply_to_repl: bool = False,
    ) -> None:
        parse_elements: list = []
        if parse_mode == "html":
            result = await self.parse_html(message_text)
            message_text = result[1]
            parse_elements = result[0]
        reply_id = message.reply.message.id if reply_to_repl else message["id"]
        chat_id = message["chat"]["id"]
        await ws._conn.send(json.dumps({
            "ver": 10,
            "cmd": 0,
            "seq": random.randint(0, 9999),
            "opcode": MessageOpcode.SEND_MESSAGE,
            "payload": {
                "notify": True,
                "type": "USER",
                "attachMEL": True,
                "chatId": chat_id,
                "message": {
                    "cid": int(time.time() * 1000),
                    "text": message_text,
                    "detectShare": False,
                    "elements": parse_elements,
                    "link": {"type": "REPLY", "messageId": reply_id},
                }
            }
        }))

    async def send_photo(
        self,
        ws,
        chat_id: int,
        photo_file_path: str,
        caption: Optional[str] = None,
        repl_to_message: Optional[str] = None,
        parse_mode: Optional[str] = None,
    ) -> Optional[dict]:
        parse_elements: list = []
        if caption:
            if parse_mode == "html":
                result = await self.parse_html(caption)
                caption = result[1]
                parse_elements = result[0]
        seq_base = random.randint(0, 9999)
        await ws._conn.send(json.dumps({
            "ver": 10, "cmd": 0, "seq": seq_base + 1,
            "opcode": MessageOpcode.REQUEST_UPLOAD,
            "payload": {"chatId": chat_id, "type": "PHOTO"}
        }))
        await ws._conn.send(json.dumps({
            "ver": 10, "cmd": 0, "seq": seq_base + 2,
            "opcode": MessageOpcode.PHOTO_UPLOAD,
            "payload": {"count": 1, "profile": False}
        }))
        msg = await ws.wait_for_message(MessageOpcode.PHOTO_UPLOAD, timeout=15)
        if msg is None or not isinstance(msg.get("payload"), dict):
            raise RuntimeError("upload_url timeout or invalid response")
        upload_url = msg["payload"].get("url")
        if not upload_url:
            raise RuntimeError("no upload URL in server response")
        response_text = await self.upload_file(photo_file_path, upload_url, file_type="PHOTO")
        try:
            photos = json.loads(response_text).get("photos")
        except json.JSONDecodeError:
            raise RuntimeError(f"upload response not JSON: {response_text[:200]}")
        if not photos:
            raise RuntimeError(f"no 'photos' in upload response: {response_text[:200]}")
        token = next(iter(photos.values())).get("token")
        if not token:
            raise RuntimeError("no token in photo metadata")
        cid = int(time.time() * 1000)
        await ws._conn.send(json.dumps({
            "ver": 10, "cmd": 0, "seq": seq_base + 3, "opcode": 5,
            "payload": {
                "events": [
                    {"type": "ACTION", "event": "ATTACH_PHOTO", "params": {}, "time": cid},
                    {"type": "ACTION", "event": "ATTACH_PHOTO", "params": {}, "time": cid + 100}
                ]
            }
        }))
        pkt = {
            "ver": 10, "cmd": 0, "seq": seq_base + 4,
            "opcode": MessageOpcode.SEND_MESSAGE,
            "payload": {
                "notify": True, "type": "USER", "attachMEL": True, "chatId": chat_id,
                "message": {
                    "cid": cid, "text": caption or "", "detectShare": False,
                    "elements": parse_elements,
                    "attaches": [{"_type": "PHOTO", "photoToken": token}]
                }
            }
        }
        if repl_to_message is not None:
            pkt["payload"]["message"]["link"] = {"type": "REPLY", "messageId": repl_to_message}
        await ws._conn.send(json.dumps(pkt))
        confirmation = await ws.wait_for_message(MessageOpcode.SEND_MESSAGE, timeout=15)
        if confirmation is None:
            raise RuntimeError("no send confirmation (timeout)")
        return confirmation

    async def send_video(
        self,
        ws,
        chat_id: int,
        video_file_path: str,
        caption: Optional[str] = None,
        repl_to_message: Optional[str] = None,
        parse_mode: Optional[str] = None,
    ) -> bool:
        parse_elements: list = []
        if caption and parse_mode == "html":
            result = await self.parse_html(caption)
            caption = result[1]
            parse_elements = result[0]
        seq_base = random.randint(0, 9999)
        await ws._conn.send(json.dumps({
            "ver": 10, "cmd": 0, "seq": seq_base + 1,
            "opcode": MessageOpcode.REQUEST_UPLOAD,
            "payload": {"chatId": chat_id, "type": "VIDEO"}
        }))
        await ws._conn.send(json.dumps({
            "ver": 10, "cmd": 0, "seq": seq_base + 2,
            "opcode": MessageOpcode.MEDIA_UPLOAD,
            "payload": {"count": 1, "audio": False}
        }))
        msg = await ws.wait_for_message(MessageOpcode.MEDIA_UPLOAD)
        info = msg["payload"]["info"][0]
        await self.upload_file(video_file_path, info["url"])
        cid = int(time.time() * 1000)
        pkt = {
            "ver": 10, "cmd": 0, "seq": seq_base + 3,
            "opcode": MessageOpcode.SEND_MESSAGE,
            "payload": {
                "notify": True, "type": "USER", "attachMEL": True, "chatId": chat_id,
                "message": {
                    "cid": cid, "text": caption or "", "detectsShare": False,
                    "elements": parse_elements,
                    "attaches": [{"_type": "VIDEO", "token": info["token"]}]
                }
            }
        }
        if repl_to_message is not None:
            pkt["payload"]["message"]["link"] = {"type": "REPLY", "messageId": repl_to_message}
        await ws._conn.send(json.dumps(pkt))
        return True

    async def send_file(
        self,
        ws,
        chat_id: int,
        file_path: str,
        title: Optional[str] = None,
        repl_to_message: Optional[str] = None,
    ) -> bool:
        seq_base = random.randint(0, 9999)
        await ws._conn.send(json.dumps({
            "ver": 10, "cmd": 0, "seq": seq_base + 1,
            "opcode": MessageOpcode.REQUEST_UPLOAD,
            "payload": {"chatId": chat_id, "type": "FILE"}
        }))
        await ws._conn.send(json.dumps({
            "ver": 10, "cmd": 0, "seq": seq_base + 2,
            "opcode": MessageOpcode.FILE_UPLOAD,
            "payload": {"count": 1}
        }))
        msg = await ws.wait_for_message(MessageOpcode.FILE_UPLOAD)
        info = msg["payload"]["info"][0]
        await self.upload_file(file_path, info["url"], file_name=title, token=info["token"])
        msg = await ws.wait_for_message(MessageOpcode.FILE_PUBLISHED)
        cid = int(time.time() * 1000)
        pkt = {
            "ver": 10, "cmd": 0, "seq": seq_base + 3,
            "opcode": MessageOpcode.SEND_MESSAGE,
            "payload": {
                "notify": True, "type": "USER", "attachMEL": True, "chatId": chat_id,
                "message": {
                    "cid": cid, "text": "", "detectsShare": False,
                    "elements": [], "attaches": [{"_type": "FILE", "token": info["token"]}]
                }
            }
        }
        if repl_to_message is not None:
            pkt["payload"]["message"]["link"] = {"type": "REPLY", "messageId": repl_to_message}
        await ws._conn.send(json.dumps(pkt))
        return True

    async def send_voice(
        self,
        ws,
        chat_id: int,
        voice_file_path: str,
        repl_to_message: Optional[str] = None,
    ) -> bool:
        seq_base = random.randint(0, 9999)
        await ws._conn.send(json.dumps({
            "ver": 10, "cmd": 0, "seq": seq_base + 1,
            "opcode": MessageOpcode.REQUEST_UPLOAD,
            "payload": {"chatId": chat_id, "type": "AUDIO"}
        }))
        await ws._conn.send(json.dumps({
            "ver": 10, "cmd": 0, "seq": seq_base + 2,
            "opcode": MessageOpcode.MEDIA_UPLOAD,
            "payload": {"count": 1, "audio": True}
        }))
        msg = await ws.wait_for_message(MessageOpcode.MEDIA_UPLOAD)
        info = msg["payload"]["info"][0]
        await self.upload_file(voice_file_path, info["url"])
        await ws.wait_for_message(MessageOpcode.FILE_PUBLISHED)
        cid = int(time.time() * 1000)
        pkt = {
            "ver": 10, "cmd": 0, "seq": seq_base + 3,
            "opcode": MessageOpcode.SEND_MESSAGE,
            "payload": {
                "notify": True, "type": "USER", "chatId": chat_id,
                "message": {
                    "cid": cid, "text": "",
                    "attaches": [{"_type": "AUDIO", "token": info["token"]}]
                }
            }
        }
        if repl_to_message is not None:
            pkt["payload"]["message"]["link"] = {"type": "REPLY", "messageId": repl_to_message}
        await ws._conn.send(json.dumps(pkt))
        return True

    async def writing_emulation(self, ws, chat_id: str) -> bool:
        await ws._conn.send(json.dumps({
            "ver": 10, "cmd": 0, "seq": random.randint(0, 9999),
            "opcode": MessageOpcode.REQUEST_UPLOAD,
            "payload": {"chatId": chat_id, "type": "TEXT"}
        }))
        return True

    async def edit_message_text(
        self,
        ws,
        chat_id: str,
        message_id: str,
        message_text: str,
        parse_mode: Optional[str] = None,
    ) -> bool:
        parse_elements: list = []
        if parse_mode == "html":
            result = await self.parse_html(message_text)
            message_text = result[1]
            parse_elements = result[0]
        await ws._conn.send(json.dumps({
            "ver": 10, "cmd": 0, "seq": random.randint(0, 9999),
            "opcode": MessageOpcode.EDIT_MESSAGE,
            "payload": {
                "chatId": chat_id,
                "messageId": message_id,
                "text": message_text,
                "elements": parse_elements,
                "attachments": []
            }
        }))
        return True

    async def pin_chat_message(self, ws, chat_id: str, message_id: str) -> bool:
        await ws._conn.send(json.dumps({
            "ver": 10, "cmd": 0, "seq": random.randint(0, 9999),
            "opcode": MessageOpcode.CHAT_SETTINGS,
            "payload": {
                "chatId": chat_id,
                "pinMessageId": message_id,
                "notifyPin": False
            }
        }))
        return True

    async def change_chat_title(self, ws, chat_id: str, title: str) -> bool:
        await ws._conn.send(json.dumps({
            "ver": 10, "cmd": 0, "seq": random.randint(0, 9999),
            "opcode": MessageOpcode.CHAT_SETTINGS,
            "payload": {"chatId": chat_id, "theme": title}
        }))
        return True

    async def change_chat_photo(self, ws, chat_id: int, photo_file_path: str) -> bool:
        seq_base = random.randint(0, 9999)
        await ws._conn.send(json.dumps({
            "ver": 10, "cmd": 0, "seq": seq_base + 2,
            "opcode": MessageOpcode.PHOTO_UPLOAD,
            "payload": {"count": 1, "profile": False}
        }))
        msg = await ws.wait_for_message(MessageOpcode.PHOTO_UPLOAD)
        upload_url = msg["payload"]["url"]
        response = await self.upload_file(photo_file_path, upload_url)
        response = json.loads(response).get("photos")
        token = next(iter(response.values())).get("token")
        cid = int(time.time() * 1000)
        await ws._conn.send(json.dumps({
            "ver": 10, "cmd": 0, "seq": seq_base + 3,
            "opcode": MessageOpcode.SEND_MESSAGE,
            "payload": {
                "chatId": chat_id,
                "message": {
                    "cid": cid,
                    "attaches": [{"_type": "CONTROL", "event": "icon", "photoToken": token}]
                }
            }
        }))
        return True

    async def delete_member(
        self,
        ws,
        chat_id: str,
        member_ids: Optional[list] = None,
        member_id: Optional[str] = None,
    ) -> bool:
        ids = member_ids if member_ids is not None else [member_id]
        await ws._conn.send(json.dumps({
            "ver": 10, "cmd": 0, "seq": random.randint(0, 9999),
            "opcode": MessageOpcode.BLOCK_MEMBER,
            "payload": {
                "operation": "add", "showHistory": True, "chatId": chat_id,
                "userIds": ids, "type": "BLOCKED_MEMBER", "cleanMsgPeriod": 0
            }
        }))
        return True

    async def delete_message(
        self,
        ws,
        chat_id: str,
        message_ids: Optional[list] = None,
        message_id: Optional[str] = None,
    ) -> bool:
        ids = message_ids if message_ids is not None else [str(message_id)]
        ids = [str(i) for i in ids]
        seq_base = random.randint(0, 9999)
        await ws._conn.send(json.dumps({
            "ver": 10, "cmd": 0, "seq": seq_base + 1,
            "opcode": MessageOpcode.DELETE_MESSAGE,
            "payload": {"chatId": chat_id, "messageIds": ids, "complaint": None, "forMe": False}
        }))
        await ws._conn.send(json.dumps({
            "ver": 10, "cmd": 1, "seq": seq_base + 1,
            "opcode": MessageOpcode.DELETE_MESSAGE,
            "payload": {"chatId": chat_id, "messageIds": ids}
        }))
        return True

    async def clear_chat_history(self, ws, chat_id: str, for_all: Optional[bool] = None) -> bool:
        await ws._conn.send(json.dumps({
            "ver": 10, "cmd": 0, "seq": random.randint(0, 9999),
            "opcode": MessageOpcode.CLEAR_HISTORY,
            "payload": {
                "chatId": chat_id,
                "lastEventTime": int(time.time() * 1000),
                "forAll": for_all
            }
        }))
        return True
