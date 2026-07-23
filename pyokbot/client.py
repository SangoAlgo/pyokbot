import asyncio
import json
import time
import traceback
import aiohttp
from datetime import datetime, timedelta
import os
from pathlib import Path
from munch import Munch

from .login import Login
from .ws import Ws
from .messages import Messages


class Vanus:

    def __init__(self, auth_code):
        self.login = Login()
        self._session = aiohttp.ClientSession()
        self._ws_task = None
        self._cache_path = str(Path.home() / ".pyokbot_cache.json")
        self.users_info_cache: dict = self.get_cache_and_update(self._cache_path)
        self._handled_msg_ids = set()
        self.login.start_login(auth_code)
        self.ws = Ws(self.login)


    # === LIFECYCLE ===

    async def run(self):
        self._ws_task = asyncio.create_task(
            self.ws.start(self.login.AUTHCODE, self.login.okweb_token)
        )

        await self.ws.authorized_event.wait()

        self.bot_info = await self.ws.get_bot_info()
        self.bot_info = self.bot_info.get("profile")
        self.messages = Messages(self.bot_info, self._session)


    async def stop(self):
        if self.ws and getattr(self.ws, '_conn', None):
            await self.ws._conn.close()
        if self._ws_task:
            self._ws_task.cancel()
        if self._session and not self._session.closed:
            await self._session.close()


    async def __aenter__(self):
        await self.run()
        return self


    async def __aexit__(self, *args):
        await self.stop()


    async def polling(self):

        async def safe_call(func, msg):
            try:
                await func(msg)
            except Exception as e:
                print(f"[HANDLER ERROR] {traceback.format_exc()}")

        try:
            while True:
                msg = await self.ws._msg_queue.get()

                if not msg or msg.get("opcode") != 128:
                    continue
                try:
                    original_message = self.messages.generate_message_object(msg)
                except Exception:
                    continue

                if original_message is None:
                    continue

                msg_id = original_message.get("id")
                if msg_id and msg_id in self._handled_msg_ids:
                    continue
                if msg_id:
                    self._handled_msg_ids.add(msg_id)

                if not self.ws.handles_list:
                    continue

                for handler in self.ws.handles_list:
                    func = handler.get("func")
                    _filter = handler.get("filters")

                    try:
                        filtered_message = self.message_filter(_filter, original_message)
                    except Exception:
                        continue

                    if filtered_message is None:
                        continue

                    asyncio.create_task(safe_call(func, filtered_message))
                    break

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print("[POLLING ERROR]", e)
        finally:
            await self.stop()


    # === SEND MESSAGE ===

    async def writing_emulation(self, chat_id: str):
        await self.messages.writing_emulation(self.ws, chat_id)


    async def send_message(self, chat_id: str, message_text: str, parse_mode: str = None):
        await self.messages.send_message(self.ws, chat_id, message_text, parse_mode)


    async def send_reply(self, message: dict, message_text: str, parse_mode: str = None, reply_to_repl: bool = False):
        await self.messages.send_reply(self.ws, message, message_text, parse_mode, reply_to_repl)


    async def send_voice(self, chat_id: int, voice_file_path: str, repl_to_message: str = None):
        await self.messages.send_voice(self.ws, chat_id, voice_file_path, repl_to_message)


    async def send_photo(self, chat_id: int, photo_file_path: str, caption: str = None, repl_to_message: str = None, parse_mode: str = None):
        return await self.messages.send_photo(self.ws, chat_id, photo_file_path, caption, repl_to_message, parse_mode)


    async def send_video(self, chat_id: int, video_file_path: str, caption: str = None, repl_to_message: str = None, parse_mode: str = None):
        await self.messages.send_video(self.ws, chat_id, video_file_path, caption, repl_to_message, parse_mode)


    async def send_file(self, chat_id: int, file_path: str, title: str = None, repl_to_message: str = None):
        await self.messages.send_file(self.ws, chat_id, file_path, title, repl_to_message)


    # === CHAT MANAGEMENT ===

    async def get_chat_info(self, chat_id: str):
        await self.ws._conn.send(json.dumps({
            "ver": 10,
            "cmd": 0,
            "seq": 24,
            "opcode": 48,
            "payload": {"chatIds": [chat_id]}
        }))

        response = await self.ws.wait_for_message(48)
        response = response.get("payload").get("chats")[0]
        participants = response.get("participants") or {}
        participants_list = list(participants.keys())

        last_msg = response.get("lastMessage") or {}
        attaches_last_message = self.parse_attaches_to_obj(last_msg.get("attaches"))

        result = {
            "chat_id": chat_id,
            "title": response.get("title"),
            "status": response.get("status"),
            "link": response.get("link"),
            "created_time": response.get("created"),
            "owner": response.get("owner") if response.get("owner") != 0 else "unavailable",
            "images": {
                "small": response.get("iconUrl"),
                "full": response.get("fullIconUrl"),
            },
            "members": {
                "count": response.get("participantsCount"),
                "list": participants_list,
            },
            "messages": {
                "last": {
                    **attaches_last_message,
                    "id": last_msg.get("id"),
                    "text": last_msg.get("text"),
                    "sender_id": last_msg.get("sender")
                },
                "count": response.get("messagesCount")
            }
        }

        if response.get("pinnedMessage") is not None:
            result["pinned"] = {
                "id": response.get("pinnedMessage").get("id"),
                "text": response.get("pinnedMessage").get("text"),
                "sender_id": response.get("pinnedMessage").get("sender")
            }

        return result


    async def change_chat_photo(self, chat_id: int, photo_file_path: str):
        await self.messages.change_chat_photo(self.ws, chat_id, photo_file_path)


    async def change_chat_title(self, chat_id, title: str):
        await self.messages.change_chat_title(self.ws, chat_id, title)


    async def delete_member(self, chat_id, member_ids: list = None, member_id: str = None):
        await self.messages.delete_member(self.ws, chat_id, member_ids, member_id)


    async def delete_message(self, chat_id, message_ids: list = None, message_id: str = None):
        await self.messages.delete_message(self.ws, chat_id, message_ids, message_id)


    async def clear_chat_history(self, chat_id, for_all: bool = None):
        await self.messages.clear_chat_history(self.ws, chat_id, for_all)


    async def edit_message_text(self, chat_id, message_id: str, message_text: str, parse_mode: str = None):
        await self.messages.edit_message_text(self.ws, chat_id, message_id, message_text, parse_mode)


    async def pin_chat_message(self, chat_id, message_id: str):
        await self.messages.pin_chat_message(self.ws, chat_id, message_id)


    async def tst_user(self, user_id: str) -> dict:
        return await self.login.tst_user(user_id)


    # === USER INFO ===

    async def get_user_info(self, user_id: str):

        if str(user_id) not in self.users_info_cache:
            response = await self.login.get_user_info(user_id)
            self.users_info_cache[str(user_id)] = response
            self.get_cache_and_update(self._cache_path, "UPDATE")
            return response
        else:
            user_info_data = self.users_info_cache.get(str(user_id))
            if user_info_data.get("last_update_time") is not None:
                current_time = datetime.now()
                time_obj = datetime.strptime(user_info_data.get("last_update_time"), "%Y-%m-%d %H:%M:%S.%f")
                time_diff = current_time - time_obj
                if time_diff >= timedelta(seconds=3600):
                    response = await self.login.get_user_info(user_id)
                    self.users_info_cache[str(user_id)] = response
                    self.get_cache_and_update(self._cache_path, "UPDATE")
                    return response
                else:
                    return user_info_data


    async def socket_reconect_count(self):
        return self.ws.socket_reconect_counter


    # === CACHE ===

    def get_cache_and_update(self, cache_path: str, method: str = "GET"):

        if method == "GET":
            try:
                if os.path.exists(cache_path):
                    with open(cache_path, "r", encoding="utf-8") as cache:
                        cache_data = json.load(cache)
                        return cache_data if cache_data is not None else dict()
                else:
                    return dict()
            except Exception:
                return dict()

        if method == "UPDATE":
            try:
                with open(cache_path, "w", encoding="utf-8") as cache:
                    json.dump(self.users_info_cache, cache, ensure_ascii=False, indent=4)
                    return True
            except Exception:
                pass
        return False


    # === FILTERS & HANDLERS ===

    @staticmethod
    def parse_attaches_to_obj(attaches: dict):
        photo: list = []
        video: list = []
        audio: dict = None
        document: dict = None

        if not attaches:
            return {}

        for attach in attaches:
            if attach.get("_type") == "PHOTO":
                photo.append({
                    "token": attach.get("photoToken"),
                    "url": attach.get("url"),
                    "height": attach.get("height"),
                    "width": attach.get("width")
                })
            elif attach.get("_type") == "VIDEO":
                video.append({
                    "token": attach.get("token"),
                    "url": attach.get("thumbnail"),
                    "height": attach.get("height"),
                    "width": attach.get("width"),
                    "duration": attach.get("duration")
                })
            elif attach.get("_type") == "FILE":
                preview = {}
                if attach.get("preview").get("_type") == "PHOTO":
                    preview = {
                        "url": attach.get("preview").get("url"),
                        "height": attach.get("preview").get("height"),
                        "width": attach.get("preview").get("width")
                    }
                elif attach.get("preview").get("_type") == "VIDEO":
                    preview = {
                        "url": attach.get("preview").get("thumbnail"),
                        "height": attach.get("preview").get("height"),
                        "width": attach.get("preview").get("width"),
                        "duration": attach.get("preview").get("duration")
                    }

                document = {
                    **preview,
                    "name": attach.get("name"),
                    "type": attach.get("preview").get("_type").lower(),
                    "size": attach.get("size")
                }
            elif attach.get("_type") == "AUDIO":
                audio = {
                    "duration": attach.get("duration"),
                    "url": attach.get("url"),
                    "token": attach.get("token")
                }

        return {
            "photo": photo,
            "video": video,
            "document": document,
            "audio": audio
        }


    def message_filter(self, filter: dict, message: dict):
        message = dict(message)
        filters = filter.get("filters")
        text = filter.get("text")
        content_types = filter.get("content_types")
        commands = filter.get("commands")

        message_attaches_obj = self.parse_attaches_to_obj(message.get("attaches"))
        if message.get("attaches"):
            message.pop("attaches")
        message = {**message, **message_attaches_obj}

        from_bot_filter = filters is None
        text_filter = text is None
        content_types_filter = content_types is None
        commands_filter = commands is None

        if not content_types_filter:
            for content_type in content_types:
                if content_type == "text":
                    if message.get("text"):
                        content_types_filter = True
                        break
                elif content_type == "commands":
                    if message.get("text", "").startswith("/"):
                        content_types_filter = True
                        break
                elif content_type == "video":
                    if message_attaches_obj.get("video"):
                        content_types_filter = True
                        break
                elif content_type == "photo":
                    if message_attaches_obj.get("photo"):
                        content_types_filter = True
                        break
                elif content_type == "audio":
                    if message_attaches_obj.get("audio") is not None:
                        content_types_filter = True
                        break
                elif content_type == "document":
                    if message_attaches_obj.get("document") is not None:
                        content_types_filter = True
                        break

        if not from_bot_filter:
            if message.get("type") == str(filters):
                from_bot_filter = True

        if not text_filter:
            if text == message.get("text"):
                text_filter = True
            elif isinstance(text, list):
                for one_text in text:
                    if one_text == message.get("text"):
                        text_filter = True
                        break

        if not commands_filter:
            msg_text = message.get("text")
            if msg_text:
                for command in commands:
                    command = "/" + command
                    if command == msg_text.split(" ")[0]:
                        commands_filter = True
                        break

        if from_bot_filter and text_filter and content_types_filter and commands_filter:
            return Munch.fromDict(message)


    def on_message(self, filters: str = "user", text=None, content_types: list = None, commands=None):

        def decorator(func):
            self.ws.handles_list.append({
                "func": func,
                "filters": {
                    "filters": filters,
                    "text": text,
                    "content_types": content_types,
                    "commands": commands
                }
            })
            return func
        return decorator