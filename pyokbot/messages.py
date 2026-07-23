import asyncio
import json
import random
import time
import aiohttp
from sulguk import transform_html

TYPE_BRIDGE = {
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

    def __init__(self, bot_info, session):
        self.bot_info = bot_info
        self._session = session


    # === PARSE ===

    @staticmethod
    def _to_ok(entities):
        parsed_json = []
        for entity in entities:
            if entity.get("type") == "text_link":
                if entity.get("url")[:4] == "http":
                    parsed_json.append({
                        "type": TYPE_BRIDGE.get(entity.get("type")),
                        "from": entity.get("offset"),
                        "length": entity.get("length"),
                        "attributes": {"url": entity.get("url")}
                    })
                else:
                    parsed_json.append({
                        "type": "USER_MENTION",
                        "from": entity.get("offset"),
                        "length": entity.get("length"),
                        "entityId": int(entity.get("url"))
                    })
            elif entity.get("type") == "bold":
                _offset = entity.get("offset")
                last_element = parsed_json[-1] if parsed_json else None
                if last_element is not None:
                    if (last_element.get("type") == "UNDERLINE") and (last_element.get("from") == _offset):
                        parsed_json.pop(-1)
                        parsed_json.append({
                            "type": "HEADING",
                            "from": entity.get("offset"),
                            "length": entity.get("length"),
                        })
                    else:
                        parsed_json.append({
                            "type": "STRONG",
                            "from": entity.get("offset"),
                            "length": entity.get("length"),
                        })
                else:
                    parsed_json.append({
                        "type": "STRONG",
                        "from": entity.get("offset"),
                        "length": entity.get("length"),
                    })
            else:
                parsed_json.append({
                    "type": TYPE_BRIDGE.get(entity.get("type")),
                    "from": entity.get("offset"),
                    "length": entity.get("length"),
                })

        return parsed_json


    async def parse_html(self, html):
        html_one = html.replace("\n", "<br>")

        has_heading = "<h1>" in html or "<h1 " in html
        has_monospaced = "<pre>" in html or "<pre " in html

        if has_heading:
            html_one = html_one.replace("<h1>", "<strong>").replace("</h1>", "</strong>")
        if has_monospaced:
            html_one = html_one.replace("<pre>", "<code>").replace("</pre>", "</code>")

        result = transform_html(html_one)
        parsed_json = self._to_ok(result.entities)

        if has_heading or has_monospaced:
            result_orig = transform_html(html)
            parsed_orig = self._to_ok(result_orig.entities)
            for i in range(len(parsed_json)):
                if parsed_orig[i].get("type") in ("HEADING", "MONOSPACED"):
                    parsed_json[i]["type"] = parsed_orig[i]["type"]

        return [parsed_json, result.text]


    def generate_message_object(self, message: dict) -> list:

        if not (message.get("opcode") == 128 and isinstance(message.get("payload"), dict)
                and isinstance(message["payload"].get("message"), dict)
                and message["payload"]["message"].get("sender") is not None):
            return None

        if message.get("ver") == 10:

            if message["payload"]["message"]["sender"] == self.bot_info.get("id"):
                user_type = "bot"
            else:
                user_type = "user"

            payload = message["payload"]
            msg = payload["message"]
            link = msg.get("link")
            is_reply = isinstance(link, dict) and isinstance(link.get("message"), dict)

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
                    "id": msg.get("sender"),
                    "name": None,
                    "avatar": None,
                    "url": f'https://m.ok.ru/profile/{msg.get("sender")}',
                },
                "chat": {
                    "id": payload.get("chatId"),
                },
                "reply": full_reply if is_reply else None,
                "attaches": msg.get("attaches"),
            }

            return full_dict

        return None


    # === UPLOAD ===

    async def upload_file(self, file_path: str, upload_url: str, file_type: str, file_name: str = None, token: str = None):
        file_format = "WEB" if file_path.startswith("http") else "LOCAL"

        if file_format == "WEB":
            async with self._session.get(file_path) as file:
                blob = await file.read()
        else:
            with open(file_path, "rb") as f:
                blob = f.read()

        data = aiohttp.FormData()
        if file_type == "AUDIO":
            file_name = "file.mp3" if file_name is None else file_name
            data.add_field("file", blob, filename=file_name, content_type="audio/mpeg")
        elif file_type == "PHOTO":
            file_name = "file.png" if file_name is None else file_name
            data.add_field("file", blob, filename=file_name, content_type="image/jpeg")
        elif file_type == "VIDEO":
            file_name = "file.mp4" if file_name is None else file_name
            data.add_field("file", blob, filename=file_name, content_type="video/mp4")

        if token is not None:
            data.add_field("token", token)

        async with self._session.post(upload_url, data=data) as response:
            response_data = await response.text()
            return response_data


    # === SEND TEXT ===

    async def send_message(self, ws, chat_id: str, message_text: str, parse_mode: str = None):

        parse_elements = []

        if parse_mode == "html":
            parse_result = await self.parse_html(message_text)
            message_text = parse_result[1]
            parse_elements = parse_result[0]

        await ws._conn.send(json.dumps({
            "ver": 10,
            "cmd": 0,
            "seq": random.randint(0, 9999),
            "opcode": 64,
            "payload": {
                "notify": True,
                "type": "USER",
                "attachMEL": True,
                "chatId": chat_id,
                "message": {
                    "cid": int(time.time() * 1000),
                    "text": message_text,
                    "detectShare": False,
                    "elements": parse_elements
                }
            }
        }))


    async def send_reply(self, ws, message: dict, message_text: str, parse_mode: str = None, reply_to_repl: bool = False):

        parse_elements = []

        if parse_mode == "html":
            parse_result = await self.parse_html(message_text)
            message_text = parse_result[1]
            parse_elements = parse_result[0]

        if reply_to_repl:
            reply_message_id = message.reply.message.id
        else:
            reply_message_id = message["id"]
        chat_id = message["chat"]["id"]
        await ws._conn.send(json.dumps({
            "ver": 10,
            "cmd": 0,
            "seq": random.randint(0, 9999),
            "opcode": 64,
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
                    "link": {
                        "type": "REPLY",
                        "messageId": reply_message_id
                    }
                }
            }
        }))


    # === SEND MEDIA ===

    async def send_photo(self, ws, chat_id: int, photo_file_path: str, caption: str = None, repl_to_message: str = None, parse_mode: str = None):

        parse_elements = []
        if caption is not None:
            if parse_mode == "html":
                parse_result = await self.parse_html(caption)
                caption = parse_result[1]
                parse_elements = parse_result[0]

        reply_to_message_id = repl_to_message if repl_to_message is not None else None
        seq_base = random.randint(0, 9999)

        await ws._conn.send(json.dumps({
            "ver": 10,
            "cmd": 0,
            "seq": seq_base + 1,
            "opcode": 65,
            "payload": {
                "chatId": chat_id,
                "type": "PHOTO"
            }
        }))

        await ws._conn.send(json.dumps({
            "ver": 10,
            "cmd": 0,
            "seq": seq_base + 2,
            "opcode": 80,
            "payload": {
                "count": 1,
                "profile": False
            }
        }))

        msg = await ws.wait_for_message(80, timeout=15)
        if msg is None or not isinstance(msg.get("payload"), dict):
            raise RuntimeError("upload_url timeout or invalid response")
        upload_info = msg["payload"]

        photo_url = upload_info.get("url")
        if not photo_url:
            raise RuntimeError("no upload URL in server response")

        response_text = await self.upload_file(photo_file_path, photo_url, file_type="PHOTO")
        try:
            photos = json.loads(response_text).get("photos")
        except json.JSONDecodeError:
            raise RuntimeError(f"upload response not JSON: {response_text[:200]}")
        if not photos:
            raise RuntimeError(f"no 'photos' in upload response: {response_text[:200]}")

        photo_keys = list(photos.keys())
        if not photo_keys:
            raise RuntimeError("empty photos dict in upload response")
        token = photos[photo_keys[0]].get("token")
        if not token:
            raise RuntimeError("no token in photo metadata")

        cid = int(time.time() * 1000)

        await ws._conn.send(json.dumps({
            "ver": 10,
            "cmd": 0,
            "seq": seq_base + 3,
            "opcode": 5,
            "payload": {
                "events": [
                    {"type": "ACTION", "event": "ATTACH_PHOTO", "params": {}, "time": int(time.time() * 1000)},
                    {"type": "ACTION", "event": "ATTACH_PHOTO", "params": {}, "time": int(time.time() * 1000) + 100}
                ]
            }
        }))

        send_photo_msg = {
            "ver": 10,
            "cmd": 0,
            "seq": seq_base + 4,
            "opcode": 64,
            "payload": {
                "notify": True,
                "type": "USER",
                "attachMEL": True,
                "chatId": chat_id,
                "message": {
                    "cid": cid,
                    "text": caption if caption is not None else "",
                    "detectShare": False,
                    "elements": parse_elements,
                    "attaches": [{"_type": "PHOTO", "photoToken": token}]
                }
            }
        }

        if reply_to_message_id is not None:
            send_photo_msg["payload"]["message"]["link"] = {
                "type": "REPLY",
                "messageId": reply_to_message_id
            }

        await ws._conn.send(json.dumps(send_photo_msg))

        confirmation = await ws.wait_for_message(64, timeout=15)
        if confirmation is None:
            raise RuntimeError("no opcode 64 confirmation (timeout)")
        return confirmation


    async def send_video(self, ws, chat_id: int, video_file_path: str, caption: str = None, repl_to_message: str = None, parse_mode: str = None):

        parse_elements = []
        if caption is not None:
            if parse_mode == "html":
                parse_result = await self.parse_html(caption)
                caption = parse_result[1]
                parse_elements = parse_result[0]

        reply_to_message_id = repl_to_message if repl_to_message is not None else None
        seq_base = random.randint(0, 9999)

        await ws._conn.send(json.dumps({
            "ver": 10,
            "cmd": 0,
            "seq": seq_base + 1,
            "opcode": 65,
            "payload": {
                "chatId": chat_id,
                "type": "VIDEO"
            }
        }))

        await ws._conn.send(json.dumps({
            "ver": 10,
            "cmd": 0,
            "seq": seq_base + 2,
            "opcode": 82,
            "payload": {
                "count": 1,
                "audio": False
            }
        }))

        msg = await ws.wait_for_message(82)
        upload_info = msg["payload"]["info"][0]

        video_url = upload_info["url"]
        await self.upload_file(video_file_path, video_url)

        cid = int(time.time() * 1000)

        send_video_msg = {
            "ver": 10,
            "cmd": 0,
            "seq": seq_base + 3,
            "opcode": 64,
            "payload": {
                "notify": True,
                "type": "USER",
                "attachMEL": True,
                "chatId": chat_id,
                "message": {
                    "cid": cid,
                    "text": caption if caption is not None else "",
                    "detectsShare": False,
                    "elements": parse_elements,
                    "attaches": [
                        {"_type": "VIDEO", "token": upload_info["token"]}
                    ]
                }
            }
        }

        if reply_to_message_id is not None:
            send_video_msg["payload"]["message"]["link"] = {
                "type": "REPLY",
                "messageId": reply_to_message_id
            }

        await ws._conn.send(json.dumps(send_video_msg))

        return True


    async def send_file(self, ws, chat_id: int, file_path: str, title: str = None, repl_to_message: str = None):

        seq_base = random.randint(0, 9999)
        reply_to_message_id = repl_to_message if repl_to_message is not None else None

        await ws._conn.send(json.dumps({
            "ver": 10,
            "cmd": 0,
            "seq": seq_base + 1,
            "opcode": 65,
            "payload": {
                "chatId": chat_id,
                "type": "FILE"
            }
        }))

        await ws._conn.send(json.dumps({
            "ver": 10,
            "cmd": 0,
            "seq": seq_base + 2,
            "opcode": 87,
            "payload": {
                "count": 1
            }
        }))

        msg = await ws.wait_for_message(87)
        upload_info = msg["payload"]["info"][0]

        file_url = upload_info["url"]
        await self.upload_file(file_path, file_url, file_name=title, token=upload_info["token"])

        msg = await ws.wait_for_message(136)
        published = msg["payload"]["fileId"]

        cid = int(time.time() * 1000)

        send_file_msg = {
            "ver": 10,
            "cmd": 0,
            "seq": seq_base + 3,
            "opcode": 64,
            "payload": {
                "notify": True,
                "type": "USER",
                "attachMEL": True,
                "chatId": chat_id,
                "message": {
                    "cid": cid,
                    "text": "",
                    "detectsShare": False,
                    "elements": [],
                    "attaches": [
                        {"_type": "FILE", "token": upload_info["token"]}
                    ]
                }
            }
        }

        if reply_to_message_id is not None:
            send_file_msg["payload"]["message"]["link"] = {
                "type": "REPLY",
                "messageId": reply_to_message_id
            }

        await ws._conn.send(json.dumps(send_file_msg))

        return True


    async def send_voice(self, ws, chat_id: int, voice_file_path: str, repl_to_message: str = None):

        seq_base = random.randint(0, 9999)
        reply_to_message_id = repl_to_message if repl_to_message is not None else None

        await ws._conn.send(json.dumps({
            "ver": 10,
            "cmd": 0,
            "seq": seq_base + 1,
            "opcode": 65,
            "payload": {
                "chatId": chat_id,
                "type": "AUDIO"
            }
        }))

        await ws._conn.send(json.dumps({
            "ver": 10,
            "cmd": 0,
            "seq": seq_base + 2,
            "opcode": 82,
            "payload": {
                "count": 1,
                "audio": True
            }
        }))

        msg = await ws.wait_for_message(82)
        upload_info = msg["payload"]["info"][0]

        await self.upload_file(voice_file_path, upload_info["url"])

        msg = await ws.wait_for_message(136)
        audio_id = msg["payload"]["audioId"]

        cid = int(time.time() * 1000)

        msg_packet = {
            "ver": 10,
            "cmd": 0,
            "seq": seq_base + 3,
            "opcode": 64,
            "payload": {
                "notify": True,
                "type": "USER",
                "chatId": chat_id,
                "message": {
                    "cid": cid,
                    "text": "",
                    "attaches": [
                        {"_type": "AUDIO", "token": upload_info["token"]}
                    ]
                }
            }
        }

        if reply_to_message_id is not None:
            msg_packet["payload"]["message"]["link"] = {
                "type": "REPLY",
                "messageId": reply_to_message_id
            }

        await ws._conn.send(json.dumps(msg_packet))

        return True


    # === CHAT ===

    async def writing_emulation(self, ws, chat_id):

        seq_base = random.randint(0, 9999)

        await ws._conn.send(json.dumps({
            "ver": 10,
            "cmd": 0,
            "seq": seq_base,
            "opcode": 65,
            "payload": {
                "chatId": chat_id,
                "type": "TEXT"
            }
        }))

        return True


    async def edit_message_text(self, ws, chat_id, message_id: str, message_text: str, parse_mode: str = None):

        parse_elements = []

        if parse_mode == "html":
            parse_result = await self.parse_html(message_text)
            message_text = parse_result[1]
            parse_elements = parse_result[0]

        seq_base = random.randint(0, 9999)

        edit_message_msg = {
            "ver": 10,
            "cmd": 0,
            "seq": seq_base + 1,
            "opcode": 67,
            "payload": {
                "chatId": chat_id,
                "messageId": message_id,
                "text": message_text,
                "elements": parse_elements,
                "attachments": []
            }
        }

        await ws._conn.send(json.dumps(edit_message_msg))

        return True


    async def pin_chat_message(self, ws, chat_id, message_id: str):

        seq_base = random.randint(0, 9999)

        change_pin_msg = {
            "ver": 10,
            "cmd": 0,
            "seq": seq_base + 1,
            "opcode": 55,
            "payload": {
                "chatId": chat_id,
                "pinMessageId": message_id,
                "notifyPin": False
            }
        }

        await ws._conn.send(json.dumps(change_pin_msg))

        return True


    async def change_chat_title(self, ws, chat_id, title: str):

        seq_base = random.randint(0, 9999)

        change_chat_title_msg = {
            "ver": 10,
            "cmd": 0,
            "seq": seq_base + 1,
            "opcode": 55,
            "payload": {
                "chatId": chat_id,
                "theme": title
            }
        }

        await ws._conn.send(json.dumps(change_chat_title_msg))

        return True


    async def change_chat_photo(self, ws, chat_id: int, photo_file_path: str):

        seq_base = random.randint(0, 9999)

        await ws._conn.send(json.dumps({
            "ver": 10,
            "cmd": 0,
            "seq": seq_base + 2,
            "opcode": 80,
            "payload": {
                "count": 1,
                "profile": False
            }
        }))

        msg = await ws.wait_for_message(80)
        upload_info = msg["payload"]

        photo_url = upload_info["url"]
        response = await self.upload_file(photo_file_path, photo_url)
        response = json.loads(response).get("photos")
        first_key = list(response.keys())[0]
        token = response.get(first_key).get("token")

        cid = int(time.time() * 1000)

        send_chat_avatar = {
            "ver": 10,
            "cmd": 0,
            "seq": seq_base + 3,
            "opcode": 64,
            "payload": {
                "chatId": chat_id,
                "message": {
                    "cid": cid,
                    "attaches": [
                        {
                            "_type": "CONTROL",
                            "event": "icon",
                            "photoToken": token
                        }
                    ]
                }
            }
        }

        await ws._conn.send(json.dumps(send_chat_avatar))

        return True


    async def delete_member(self, ws, chat_id, member_ids: list = None, member_id: str = None):

        member_ids = member_ids if member_ids is not None else [member_id]
        seq_base = random.randint(0, 9999)

        block_packet = {
            "ver": 10,
            "cmd": 0,
            "seq": seq_base + 1,
            "opcode": 77,
            "payload": {
                "operation": "add",
                "showHistory": True,
                "chatId": chat_id,
                "userIds": member_ids,
                "type": "BLOCKED_MEMBER",
                "cleanMsgPeriod": 0
            }
        }

        await ws._conn.send(json.dumps(block_packet))

        return True


    async def delete_message(self, ws, chat_id, message_ids: list = None, message_id: str = None):

        message_ids = message_ids if message_ids is not None else [str(message_id)]
        if message_ids is not None:
            for i, _id in enumerate(message_ids):
                message_ids[i] = str(_id)

        seq_base = random.randint(0, 9999)

        delete_message_msg = {
            "ver": 10,
            "cmd": 0,
            "seq": seq_base + 1,
            "opcode": 66,
            "payload": {
                "chatId": chat_id,
                "messageIds": message_ids,
                "complaint": None,
                "forMe": False
            }
        }

        await ws._conn.send(json.dumps(delete_message_msg))

        server_ack = {
            "ver": 10,
            "cmd": 1,
            "seq": seq_base + 1,
            "opcode": 66,
            "payload": {
                "chatId": chat_id,
                "messageIds": message_ids
            }
        }

        await ws._conn.send(json.dumps(server_ack))

        return True


    async def clear_chat_history(self, ws, chat_id, for_all: bool = None):

        seq_base = random.randint(0, 9999)
        last_event_time = int(time.time() * 1000)

        clear_chat_history_msg = {
            "ver": 10,
            "cmd": 0,
            "seq": seq_base + 1,
            "opcode": 54,
            "payload": {
                "chatId": chat_id,
                "lastEventTime": last_event_time,
                "forAll": for_all
            }
        }

        await ws._conn.send(json.dumps(clear_chat_history_msg))

        return True