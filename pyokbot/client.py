from __future__ import annotations

import asyncio
import json
import os
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

import aiohttp
from munch import Munch

from .animator import (
    TextAnimator,
    progress_frames,
    reveal_frames,
    spinner_frames,
    typewriter_frames,
)
from .logging_config import logger
from .login import Login
from .messages import Messages
from .opcodes import MessageOpcode
from .ws import Ws


class Vanus:
    """Main client for OK.ru bot.

    Usage:
        bot = Vanus("AUTHCODE")
        await bot.run()
        await bot.polling()
    """

    def __init__(self, auth_code: str, auto_resolve_users: bool = True):
        self.login = Login()
        self.auto_resolve_users = auto_resolve_users
        self._session = aiohttp.ClientSession()
        self._ws_task: asyncio.Task | None = None
        self._cache_path = str(Path.home() / ".pyokbot_cache.json")
        self.users_info_cache: dict = self.get_cache_and_update(self._cache_path)
        self._handled_msg_ids: set = set()
        self.reaction_handlers: list[Callable] = []
        self.typing_handlers: list[Callable] = []
        self.read_handlers: list[Callable] = []
        self.presence_handlers: list[Callable] = []
        self.event_handlers: dict[int, list[Callable]] = {}
        self.login.start_login(auth_code)
        self.ws = Ws(self.login)
        self.bot_info: dict = {}
        self.messages = Messages(self.bot_info, self._session)

    # === LIFECYCLE ===

    async def run(self) -> None:
        """Connect to OK.ru and wait for authorization."""
        self._ws_task = asyncio.create_task(
            self.ws.start(self.login.AUTHCODE, self.login.okweb_token)
        )
        await self.ws.authorized_event.wait()
        profile = await self.ws.get_bot_info()
        self.bot_info = profile.get("profile") or {}
        self.messages = Messages(self.bot_info, self._session)

    async def stop(self) -> None:
        """Disconnect and clean up."""
        if self.ws and getattr(self.ws, '_conn', None):
            await self.ws._conn.close()
        if self._ws_task:
            self._ws_task.cancel()
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> Vanus:
        await self.run()
        return self

    async def __aexit__(self, *args) -> None:
        await self.stop()

    async def polling(self) -> None:
        """Start processing messages and events from the WebSocket queue.

        Handlers are checked in registration order and the first match wins.
        """

        async def safe_call(func: Callable, data: Any) -> None:
            try:
                await func(data)
            except Exception:
                logger.error(f"[HANDLER ERROR] {traceback.format_exc()}")

        try:
            while True:
                try:
                    msg = await self.ws._msg_queue.get()
                except asyncio.CancelledError:
                    break

                if not msg:
                    continue

                op = msg.get("opcode")
                p = msg.get("payload", {})

                # 1. Custom raw opcode event handlers
                if op in self.event_handlers:
                    for h in self.event_handlers[op]:
                        asyncio.create_task(safe_call(h, Munch.fromDict(msg) if isinstance(msg, dict) else msg))

                # 2. Reactions
                if op in (MessageOpcode.INCOMING_REACTION, MessageOpcode.YOUR_REACTION):
                    if self.reaction_handlers:
                        reaction_data = Munch.fromDict(p) if isinstance(p, dict) else p
                        for h in self.reaction_handlers:
                            asyncio.create_task(safe_call(h, reaction_data))
                    continue

                # 3. User Typing
                if op == MessageOpcode.USER_TYPING:
                    if self.typing_handlers:
                        typing_data = Munch.fromDict(p) if isinstance(p, dict) else p
                        for h in self.typing_handlers:
                            asyncio.create_task(safe_call(h, typing_data))
                    continue

                # 4. Read Receipt
                if op == MessageOpcode.READ_RECEIPT:
                    if self.read_handlers:
                        read_data = Munch.fromDict(p) if isinstance(p, dict) else p
                        for h in self.read_handlers:
                            asyncio.create_task(safe_call(h, read_data))
                    continue

                # 5. Presence Update
                if op == MessageOpcode.PRESENCE_UPDATE:
                    if self.presence_handlers:
                        presence_data = Munch.fromDict(p) if isinstance(p, dict) else p
                        for h in self.presence_handlers:
                            asyncio.create_task(safe_call(h, presence_data))
                    continue

                # 6. Incoming Messages
                if op == MessageOpcode.INCOMING_MESSAGE:
                    try:
                        original_message = self.messages.generate_message_object(msg)
                    except Exception as e:
                        logger.warning(f"Failed to parse incoming message: {e}")
                        continue
                    if original_message is None:
                        continue
                    msg_id = original_message.get("id")
                    if msg_id and msg_id in self._handled_msg_ids:
                        continue
                    if msg_id:
                        self._handled_msg_ids.add(msg_id)
                        if len(self._handled_msg_ids) > 10000:
                            # Prune to prevent memory leaks
                            self._handled_msg_ids = set(list(self._handled_msg_ids)[-5000:])

                    # Auto-resolve sender user info (instant from cache, or ~120ms via WS)
                    sender_id = original_message.get("user", {}).get("id")
                    if sender_id:
                        uid_str = str(sender_id)
                        uinfo = self.users_info_cache.get(uid_str)
                        if not uinfo and self.auto_resolve_users:
                            try:
                                uinfo = await self.get_user_info(sender_id)
                            except Exception as e:
                                logger.debug(f"Failed to auto-resolve user {sender_id}: {e}")
                        if uinfo and "user" in original_message:
                            original_message["user"]["name"] = uinfo.get("name")
                            original_message["user"]["avatar"] = uinfo.get("avatar_url")
                            original_message["user"]["avatar_url"] = uinfo.get("avatar_url")
                            original_message["user"]["full_avatar_url"] = uinfo.get("full_avatar_url")
                            original_message["user"]["gender"] = uinfo.get("gender")

                    # Auto-resolve replied user info if present
                    if original_message.get("is_reply") and original_message.get("reply"):
                        reply_user = original_message["reply"].get("user") or {}
                        reply_sender_id = reply_user.get("id")
                        if reply_sender_id:
                            r_uid_str = str(reply_sender_id)
                            r_uinfo = self.users_info_cache.get(r_uid_str)
                            if not r_uinfo and self.auto_resolve_users:
                                try:
                                    r_uinfo = await self.get_user_info(reply_sender_id)
                                except Exception as e:
                                    logger.debug(f"Failed to auto-resolve reply user {reply_sender_id}: {e}")
                            if r_uinfo and "user" in original_message["reply"]:
                                original_message["reply"]["user"]["name"] = r_uinfo.get("name")
                                original_message["reply"]["user"]["avatar"] = r_uinfo.get("avatar_url")
                                original_message["reply"]["user"]["avatar_url"] = r_uinfo.get("avatar_url")
                    if not self.ws.handles_list:
                        continue
                    for handler in self.ws.handles_list:
                        func = handler.get("func")
                        _filter = handler.get("filters")
                        if func is None or _filter is None:
                            continue
                        try:
                            filtered_message = self.message_filter(_filter, original_message)
                        except Exception as e:
                            logger.warning(f"Filter error in handler {func}: {e}")
                            continue
                        if filtered_message is None:
                            continue
                        asyncio.create_task(safe_call(func, filtered_message))
                        break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"[POLLING ERROR] {e}")
        finally:
            await self.stop()

    # === SEND MESSAGE ===

    async def writing_emulation(self, chat_id: str) -> None:
        """Show 'typing...' indicator in a chat."""
        await self.messages.writing_emulation(self.ws, chat_id)

    async def send_message(
        self,
        chat_id: str,
        message_text: str,
        parse_mode: str | None = None,
    ) -> None:
        """Send a text message to a chat.

        Args:
            chat_id: target chat ID.
            message_text: message body.
            parse_mode: set to "html" to enable HTML formatting.
        """
        await self.messages.send_message(self.ws, chat_id, message_text, parse_mode)

    async def send_reply(
        self,
        message: dict,
        message_text: str,
        parse_mode: str | None = None,
        reply_to_repl: bool = False,
    ) -> None:
        """Reply to a message.

        Args:
            message: the message object to reply to.
            message_text: reply body.
            parse_mode: set to "html" for HTML formatting.
            reply_to_repl: if True, reply to the original replied-to message instead.
        """
        await self.messages.send_reply(self.ws, message, message_text, parse_mode, reply_to_repl)

    async def send_voice(
        self,
        chat_id: str,
        voice_file_path: str,
        repl_to_message: str | None = None,
    ) -> None:
        """Send a voice message."""
        await self.messages.send_voice(self.ws, chat_id, voice_file_path, repl_to_message)

    async def send_photo(
        self,
        chat_id: str,
        photo_file_path: str,
        caption: str | None = None,
        repl_to_message: str | None = None,
        parse_mode: str | None = None,
    ) -> dict | None:
        """Send a photo.

        Args:
            photo_file_path: URL or local file path.
            caption: optional caption text.
            repl_to_message: message ID to reply to.
            parse_mode: set to "html" for HTML in caption.
        """
        return await self.messages.send_photo(
            self.ws, chat_id, photo_file_path, caption, repl_to_message, parse_mode
        )

    async def send_video(
        self,
        chat_id: str,
        video_file_path: str,
        caption: str | None = None,
        repl_to_message: str | None = None,
        parse_mode: str | None = None,
    ) -> None:
        """Send a video file."""
        await self.messages.send_video(
            self.ws, chat_id, video_file_path, caption, repl_to_message, parse_mode
        )

    async def send_file(
        self,
        chat_id: str,
        file_path: str,
        title: str | None = None,
        repl_to_message: str | None = None,
    ) -> None:
        """Send a file."""
        await self.messages.send_file(self.ws, chat_id, file_path, title, repl_to_message)

    # === CHAT MANAGEMENT ===

    async def get_chat_info(self, chat_id: str | int) -> dict:
        """Fetch chat metadata (title, members, messages, pinned message)."""
        cid = int(chat_id) if isinstance(chat_id, str) and (chat_id.isdigit() or (chat_id.startswith("-") and chat_id[1:].isdigit())) else chat_id
        response = await self.ws.request(
            MessageOpcode.CHAT_INFO,
            {"chatIds": [cid]}
        )
        chats = response.get("payload", {}).get("chats", [{}])
        if not chats:
            return {}
        resp = chats[0]
        participants = resp.get("participants") or {}
        last_msg = resp.get("lastMessage") or {}
        attaches = self.parse_attaches_to_obj(last_msg.get("attaches"))
        result: dict = {
            "chat_id": str(chat_id),
            "title": resp.get("title"),
            "status": resp.get("status"),
            "link": resp.get("link"),
            "created_time": resp.get("created"),
            "owner": resp.get("owner") if resp.get("owner") != 0 else "unavailable",
            "images": {
                "small": resp.get("iconUrl"),
                "full": resp.get("fullIconUrl"),
            },
            "members": {
                "count": resp.get("participantsCount"),
                "list": list(participants.keys()),
            },
            "messages": {
                "last": {
                    **attaches,
                    "id": last_msg.get("id"),
                    "text": last_msg.get("text"),
                    "sender_id": last_msg.get("sender"),
                },
                "count": resp.get("messagesCount"),
            },
        }
        pinned = resp.get("pinnedMessage")
        if pinned is not None:
            result["pinned"] = {
                "id": pinned.get("id"),
                "text": pinned.get("text"),
                "sender_id": pinned.get("sender"),
            }
        return result

    async def change_chat_photo(self, chat_id: str, photo_file_path: str) -> None:
        """Change the chat avatar."""
        await self.messages.change_chat_photo(self.ws, chat_id, photo_file_path)

    async def change_chat_title(self, chat_id: str, title: str) -> None:
        """Rename a chat."""
        await self.messages.change_chat_title(self.ws, chat_id, title)

    async def delete_member(
        self,
        chat_id: str,
        member_ids: list[str] | None = None,
        member_id: str | None = None,
    ) -> None:
        """Remove a member from a chat."""
        await self.messages.delete_member(self.ws, chat_id, member_ids, member_id)

    async def delete_message(
        self,
        chat_id: str,
        message_ids: list[str] | None = None,
        message_id: str | None = None,
    ) -> None:
        """Delete a message."""
        await self.messages.delete_message(self.ws, chat_id, message_ids, message_id)

    async def clear_chat_history(self, chat_id: str, for_all: bool | None = None) -> None:
        """Clear chat history.

        Args:
            for_all: if True, clears for everyone; if False, only for the bot.
        """
        await self.messages.clear_chat_history(self.ws, chat_id, for_all)

    async def edit_message_text(
        self,
        chat_id: str | int,
        message_id: str,
        message_text: str,
        parse_mode: str | None = None,
    ) -> bool:
        """Edit a sent message."""
        return await self.messages.edit_message_text(
            self.ws, chat_id, message_id, message_text, parse_mode
        )

    async def pin_chat_message(self, chat_id: str, message_id: str) -> None:
        """Pin a message in a chat."""
        await self.messages.pin_chat_message(self.ws, chat_id, message_id)

    async def tst_user(self, user_id: str) -> dict:
        """Check if a user is currently logged in."""
        return await self.login.tst_user(user_id)

    # === REACTIONS ===

    async def set_reaction(
        self,
        chat_id: str | int,
        message_id: str,
        reaction: str = "👍",
    ) -> dict:
        """Add an emoji reaction to a message."""
        return await self.messages.set_reaction(self.ws, chat_id, message_id, reaction)

    async def remove_reaction(
        self,
        chat_id: str | int,
        message_id: str,
    ) -> dict:
        """Remove a reaction from a message."""
        return await self.messages.remove_reaction(self.ws, chat_id, message_id)

    async def get_reactions(
        self,
        chat_id: str | int,
        message_ids: list[str],
    ) -> dict:
        """Get reactions for messages."""
        return await self.messages.get_reactions(self.ws, chat_id, message_ids)

    async def get_reacted_users(
        self,
        chat_id: str | int,
        message_id: str,
        reaction: str = "👍",
        marker: int | None = None,
        count: int = 50,
    ) -> dict:
        """Get users who reacted to a message."""
        return await self.messages.get_reacted_users(
            self.ws, chat_id, message_id, reaction, marker, count
        )

    # === READ STATUS & CHAT HISTORY ===

    async def mark_as_read(
        self,
        chat_id: str | int,
        message_id: str,
        mark: int | None = None,
    ) -> dict:
        """Mark a message as read."""
        return await self.messages.mark_as_read(self.ws, chat_id, message_id, mark)

    async def get_chat_history(
        self,
        chat_id: str | int,
        from_time: int | None = None,
        count: int = 25,
    ) -> dict:
        """Get chat message history."""
        return await self.messages.get_chat_history(self.ws, chat_id, from_time, backward=count)

    # === CHAT INVITATIONS & PARTICIPANTS ===

    async def join_chat(self, link: str) -> dict:
        """Join a chat by invite link."""
        return await self.messages.join_chat(self.ws, link)

    async def leave_chat(self, chat_id: str | int) -> dict:
        """Leave a chat."""
        return await self.messages.leave_chat(self.ws, chat_id)

    async def add_chat_members(
        self,
        chat_id: str | int,
        user_ids: list[str | int],
    ) -> dict:
        """Add participants to a chat."""
        return await self.messages.add_chat_members(self.ws, chat_id, user_ids)

    async def get_chat_participants(
        self,
        chat_id: str | int,
        last_event_time: int | None = None,
    ) -> dict:
        """Get chat participants."""
        return await self.messages.get_chat_participants(self.ws, chat_id, last_event_time)

    async def subscribe_chat(self, chat_id: str | int, subscribe: bool = True) -> dict:
        """Subscribe or unsubscribe from live chat updates."""
        return await self.messages.subscribe_chat(self.ws, chat_id, subscribe)

    # === USER INFO & PROFILES ===

    async def get_user_info(
        self,
        user_id: str | int,
        with_presence: bool = False,
        force_refresh: bool = False,
    ) -> dict:
        """Get user profile info via fast native WebSocket RPC (Opcode 32).

        Results are cached in memory and on disk with 1-hour TTL.
        Fetches in ~120ms (over 8x faster than HTTP HTML scraping).

        Args:
            user_id: The target user's numeric OK.ru ID.
            with_presence: If True, also fetch real-time presence/online status (Opcode 35).
            force_refresh: If True, bypass cache and fetch fresh data from OK.ru.

        Returns:
            Dictionary with user fields: id, name, first_name, last_name,
            avatar_url, full_avatar_url, gender, bday, profile_url, and optionally online, seen.
        """
        uid = str(user_id)
        if not force_refresh and uid in self.users_info_cache:
            cached = self.users_info_cache[uid]
            last_update = cached.get("last_update_time")
            if last_update:
                try:
                    now = datetime.now()
                    last = datetime.strptime(last_update, "%Y-%m-%d %H:%M:%S.%f")
                    if now - last < timedelta(seconds=3600):
                        if not with_presence or "online" in cached:
                            return cached
                except Exception:
                    pass

        # Fetch via WebSocket
        info = await self._fetch_user_via_ws(user_id, with_presence=with_presence)
        if info:
            self.users_info_cache[uid] = info
            self.get_cache_and_update(self._cache_path, "UPDATE")
            return info

        # Fallback to HTTP scraper if WS returned empty or failed
        try:
            http_info = await self.login.get_user_info(uid)
            if http_info:
                self.users_info_cache[uid] = http_info
                self.get_cache_and_update(self._cache_path, "UPDATE")
                return http_info
        except Exception as e:
            logger.debug(f"HTTP fallback get_user_info failed: {e}")

        return {
            "id": uid,
            "name": None,
            "avatar_url": None,
            "profile_url": f"https://ok.ru/profile/{uid}",
        }

    async def _fetch_user_via_ws(
        self, user_id: str | int, with_presence: bool = False
    ) -> dict | None:
        try:
            uid_int = int(user_id)
        except (ValueError, TypeError):
            return None

        try:
            if with_presence:
                contacts_fut = self.messages.get_contacts(self.ws, [uid_int])
                presence_fut = self.messages.get_presence(self.ws, [uid_int])
                res32, res35 = await asyncio.gather(contacts_fut, presence_fut)
            else:
                res32 = await self.messages.get_contacts(self.ws, [uid_int])
                res35 = {}

            contacts = res32.get("payload", {}).get("contacts", [])
            if not contacts:
                return None
            c = contacts[0]
            name = c.get("names", [{}])[0].get("name", "") if c.get("names") else ""
            parts = name.split(" ", 1)
            first_name = parts[0] if parts else ""
            last_name = parts[1] if len(parts) > 1 else ""
            gender = "male" if c.get("gender") == 1 else "female" if c.get("gender") == 2 else "unknown"
            default_avatar = (
                "https://m.ok.ru/mres/img/stb3/female_370.png"
                if gender == "female"
                else "https://m.ok.ru/mres/img/stb3/male_370.png"
            )
            avatar = c.get("avatarUrl") or default_avatar
            full_avatar = c.get("fullAvatarUrl") or avatar

            presence_data = res35.get("payload", {}).get("presence", {}).get(str(uid_int), {})

            info = {
                "id": str(c.get("id", uid_int)),
                "name": name,
                "first_name": first_name,
                "last_name": last_name,
                "avatar_url": avatar,
                "full_avatar_url": full_avatar,
                "gender": gender,
                "bday": c.get("bday"),
                "profile_url": c.get("profileUrl") or f"https://ok.ru/profile/{uid_int}",
                "last_update_time": str(datetime.now()),
            }
            if with_presence:
                info["online"] = presence_data.get("on")
                info["seen"] = presence_data.get("seen")
                info["last_visit"] = "Сейчас на сайте" if presence_data.get("on") else "Был(а) недавно"
            return info
        except Exception as e:
            logger.debug(f"WS _fetch_user_via_ws failed for {user_id}: {e}")
            return None

    async def get_users_info(
        self,
        user_ids: list[str | int],
        with_presence: bool = False,
        force_refresh: bool = False,
    ) -> dict[str, dict]:
        """Batch fetch user profiles for multiple users in a single WebSocket query.

        Args:
            user_ids: List of user IDs.
            with_presence: If True, also fetch real-time presence.
            force_refresh: If True, bypass cache.

        Returns:
            Dictionary mapping user_id string to user info dictionary.
        """
        results: dict[str, dict] = {}
        missing_ids: list[int] = []

        now = datetime.now()
        for uid in user_ids:
            uid_str = str(uid)
            if not force_refresh and uid_str in self.users_info_cache:
                cached = self.users_info_cache[uid_str]
                last_update = cached.get("last_update_time")
                if last_update:
                    try:
                        last = datetime.strptime(last_update, "%Y-%m-%d %H:%M:%S.%f")
                        if now - last < timedelta(seconds=3600):
                            if not with_presence or "online" in cached:
                                results[uid_str] = cached
                                continue
                    except Exception:
                        pass
            if str(uid).isdigit():
                missing_ids.append(int(uid))

        if not missing_ids:
            return results

        # Query in chunks of up to 100 users per WebSocket request
        for i in range(0, len(missing_ids), 100):
            chunk = missing_ids[i : i + 100]
            try:
                if with_presence:
                    c_fut = self.messages.get_contacts(self.ws, chunk)
                    p_fut = self.messages.get_presence(self.ws, chunk)
                    res32, res35 = await asyncio.gather(c_fut, p_fut)
                else:
                    res32 = await self.messages.get_contacts(self.ws, chunk)
                    res35 = {}

                contacts = res32.get("payload", {}).get("contacts", [])
                presence_map = res35.get("payload", {}).get("presence", {})

                for c in contacts:
                    cid_str = str(c.get("id"))
                    name = c.get("names", [{}])[0].get("name", "") if c.get("names") else ""
                    parts = name.split(" ", 1)
                    first_name = parts[0] if parts else ""
                    last_name = parts[1] if len(parts) > 1 else ""
                    gender = (
                        "male"
                        if c.get("gender") == 1
                        else "female"
                        if c.get("gender") == 2
                        else "unknown"
                    )
                    default_avatar = (
                        "https://m.ok.ru/mres/img/stb3/female_370.png"
                        if gender == "female"
                        else "https://m.ok.ru/mres/img/stb3/male_370.png"
                    )
                    avatar = c.get("avatarUrl") or default_avatar
                    full_avatar = c.get("fullAvatarUrl") or avatar
                    pres = presence_map.get(cid_str, {})

                    info = {
                        "id": cid_str,
                        "name": name,
                        "first_name": first_name,
                        "last_name": last_name,
                        "avatar_url": avatar,
                        "full_avatar_url": full_avatar,
                        "gender": gender,
                        "bday": c.get("bday"),
                        "profile_url": c.get("profileUrl") or f"https://ok.ru/profile/{cid_str}",
                        "last_update_time": str(datetime.now()),
                    }
                    if with_presence:
                        info["online"] = pres.get("on")
                        info["seen"] = pres.get("seen")
                        info["last_visit"] = (
                            "Сейчас на сайте" if pres.get("on") else "Был(а) недавно"
                        )
                    self.users_info_cache[cid_str] = info
                    results[cid_str] = info
            except Exception as e:
                logger.error(f"Failed to batch fetch contacts: {e}")

        self.get_cache_and_update(self._cache_path, "UPDATE")
        return results

    async def get_user_presence(self, user_id: str | int) -> dict:
        """Fetch real-time online status and last seen timestamp of a user."""
        uid_int = int(user_id) if str(user_id).isdigit() else user_id
        res = await self.messages.get_presence(self.ws, [uid_int])
        pres_dict = res.get("payload", {}).get("presence", {})
        return pres_dict.get(str(uid_int), {})

    async def get_user_photos(self, user_id: str | int, from_index: int = 0) -> list[str]:
        """Fetch all photo URLs from a user's profile album."""
        res = await self.messages.get_user_photos(self.ws, user_id, from_index)
        return res.get("payload", {}).get("urls", [])

    async def socket_reconect_count(self) -> int:
        """Return the number of WebSocket reconnections."""
        return self.ws.socket_reconect_counter

    # === CACHE ===

    def get_cache_and_update(self, cache_path: str, method: str = "GET") -> dict:
        """Read or write the user info cache file."""
        if method == "GET":
            try:
                if os.path.exists(cache_path):
                    with open(cache_path, encoding="utf-8") as f:
                        data = json.load(f)
                        return data if data is not None else {}
                return {}
            except Exception:
                return {}
        if method == "UPDATE":
            try:
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(self.users_info_cache, f, ensure_ascii=False, indent=4)
            except Exception as e:
                logger.warning(f"Failed to write cache: {e}")
        return {}

    # === FILTERS & HANDLERS ===

    @staticmethod
    def parse_attaches_to_obj(attaches: dict | None) -> dict:
        """Convert raw attachment data into structured dicts."""
        photo: list = []
        video: list = []
        audio: dict | None = None
        document: dict | None = None
        if not attaches:
            return {}
        for attach in attaches:
            t = attach.get("_type")
            if t == "PHOTO":
                photo.append({
                    "token": attach.get("photoToken"),
                    "url": attach.get("url"),
                    "height": attach.get("height"),
                    "width": attach.get("width"),
                })
            elif t == "VIDEO":
                video.append({
                    "token": attach.get("token"),
                    "url": attach.get("thumbnail"),
                    "height": attach.get("height"),
                    "width": attach.get("width"),
                    "duration": attach.get("duration"),
                })
            elif t == "FILE":
                preview = attach.get("preview", {})
                ptype = preview.get("_type")
                preview_data = {}
                if ptype == "PHOTO":
                    preview_data = {
                        "url": preview.get("url"),
                        "height": preview.get("height"),
                        "width": preview.get("width"),
                    }
                elif ptype == "VIDEO":
                    preview_data = {
                        "url": preview.get("thumbnail"),
                        "height": preview.get("height"),
                        "width": preview.get("width"),
                        "duration": preview.get("duration"),
                    }
                document = {
                    **preview_data,
                    "name": attach.get("name"),
                    "type": ptype.lower() if ptype else None,
                    "size": attach.get("size"),
                }
            elif t == "AUDIO":
                audio = {
                    "duration": attach.get("duration"),
                    "url": attach.get("url"),
                    "token": attach.get("token"),
                }
        return {"photo": photo, "video": video, "document": document, "audio": audio}

    def message_filter(self, filter: dict, message: dict) -> Munch | None:
        """Apply a handler filter to a message.

        Returns a Munch if the message matches, None otherwise.
        """
        message = dict(message)
        f = filter.get("filters")
        text = filter.get("text")
        content_types = filter.get("content_types")
        commands = filter.get("commands")
        attaches = self.parse_attaches_to_obj(message.get("attaches"))
        if message.get("attaches"):
            message.pop("attaches")
        message = {**message, **attaches}
        from_bot_ok = f is None
        text_ok = text is None
        content_ok = content_types is None
        cmd_ok = commands is None
        if not content_ok and content_types is not None:
            for ct in content_types:
                if ct == "text" and message.get("text"):
                    content_ok = True
                    break
                if ct == "commands" and message.get("text", "").startswith("/"):
                    content_ok = True
                    break
                if ct == "video" and attaches.get("video"):
                    content_ok = True
                    break
                if ct == "photo" and attaches.get("photo"):
                    content_ok = True
                    break
                if ct == "audio" and attaches.get("audio") is not None:
                    content_ok = True
                    break
                if ct == "document" and attaches.get("document") is not None:
                    content_ok = True
                    break
        if not from_bot_ok:
            if message.get("type") == str(f):
                from_bot_ok = True
        if not text_ok:
            msg_text = message.get("text")
            if isinstance(text, list):
                text_ok = msg_text in text
            else:
                text_ok = msg_text == text
        if not cmd_ok and commands is not None:
            msg_text = message.get("text")
            if msg_text:
                for cmd in commands:
                    if "/" + cmd == msg_text.split(" ")[0]:
                        cmd_ok = True
                        break
        if from_bot_ok and text_ok and content_ok and cmd_ok:
            return Munch.fromDict(message)
        return None

    def on_message(
        self,
        filters: str = "user",
        text: str | list | None = None,
        content_types: list | None = None,
        commands: list | None = None,
    ) -> Callable:
        """Decorator to register a message handler.

        Args:
            filters: "user" or "bot". None means both.
            text: exact text to match, or list of strings.
            content_types: list of content types ("photo", "video", "audio",
                "document", "text", "commands").
            commands: list of command names. "start" matches /start.
        """
        def decorator(func: Callable) -> Callable:
            self.ws.handles_list.append({
                "func": func,
                "filters": {
                    "filters": filters,
                    "text": text,
                    "content_types": content_types,
                    "commands": commands,
                }
            })
            return func
        return decorator

    def on_reaction(self) -> Callable:
        """Decorator to register a reaction event handler.

        Callback receives the reaction payload (Munch) containing
        chatId, messageId, reactionInfo (counters, yourReaction, totalCount).
        """
        def decorator(func: Callable) -> Callable:
            self.reaction_handlers.append(func)
            return func
        return decorator

    def on_typing(self) -> Callable:
        """Decorator to register a user typing indicator event handler.

        Callback receives the typing payload (Munch) containing chatId, userId.
        """
        def decorator(func: Callable) -> Callable:
            self.typing_handlers.append(func)
            return func
        return decorator

    def on_read(self) -> Callable:
        """Decorator to register a read receipt event handler.

        Callback receives the read receipt payload (Munch) containing chatId, userId, mark.
        """
        def decorator(func: Callable) -> Callable:
            self.read_handlers.append(func)
            return func
        return decorator

    def on_presence(self) -> Callable:
        """Decorator to register a user presence / online event handler.

        Callback receives presence payload (Munch) containing userId, presence.
        """
        def decorator(func: Callable) -> Callable:
            self.presence_handlers.append(func)
            return func
        return decorator

    def on_event(self, opcode: int) -> Callable:
        """Decorator to register a custom raw opcode event handler.

        Callback receives the full raw packet message.
        """
        def decorator(func: Callable) -> Callable:
            if opcode not in self.event_handlers:
                self.event_handlers[opcode] = []
            self.event_handlers[opcode].append(func)
            return func
        return decorator

    # === ANIMATION (TELEGRAM USERBOT STYLE) ===

    def create_animator(
        self,
        chat_id: str | int,
        message_id: str,
        frames: Any,
        interval: float = 0.5,
        auto_retry: bool = True,
        max_retries: int = 5,
        parse_mode: str | None = None,
        ignore_identical: bool = True,
        on_frame: Any = None,
    ) -> TextAnimator:
        """Create a TextAnimator instance without running it immediately."""
        return TextAnimator(
            bot=self,
            chat_id=chat_id,
            message_id=message_id,
            frames=frames,
            interval=interval,
            auto_retry=auto_retry,
            max_retries=max_retries,
            parse_mode=parse_mode,
            ignore_identical=ignore_identical,
            on_frame=on_frame,
        )

    async def animate_text(
        self,
        chat_id: str | int,
        message_id: str,
        frames: Any,
        interval: float = 0.5,
        auto_retry: bool = True,
        max_retries: int = 5,
        parse_mode: str | None = None,
    ) -> TextAnimator:
        """Animate message text through a sequence of frames.

        Handles OK.ru rate limits automatically with backoff and retry.
        """
        anim = self.create_animator(
            chat_id=chat_id,
            message_id=message_id,
            frames=frames,
            interval=interval,
            auto_retry=auto_retry,
            max_retries=max_retries,
            parse_mode=parse_mode,
        )
        await anim.run()
        return anim

    async def animate_typewriter(
        self,
        chat_id: str | int,
        message_id: str,
        text: str,
        interval: float = 0.2,
        step: int = 1,
        cursor: str = "▌",
        auto_retry: bool = True,
    ) -> TextAnimator:
        """Animate text with a typewriter effect, progressively revealing characters."""
        frames = typewriter_frames(text, step=step, cursor=cursor)
        return await self.animate_text(
            chat_id=chat_id,
            message_id=message_id,
            frames=frames,
            interval=interval,
            auto_retry=auto_retry,
        )

    async def animate_progress(
        self,
        chat_id: str | int,
        message_id: str,
        total_steps: int = 10,
        interval: float = 0.5,
        prefix: str = "",
        suffix: str = "",
        filled_char: str = "🟩",
        empty_char: str = "▫️",
        auto_retry: bool = True,
    ) -> TextAnimator:
        """Animate a progress bar in a message."""
        frames = progress_frames(
            total_steps=total_steps,
            prefix=prefix,
            suffix=suffix,
            filled_char=filled_char,
            empty_char=empty_char,
        )
        return await self.animate_text(
            chat_id=chat_id,
            message_id=message_id,
            frames=frames,
            interval=interval,
            auto_retry=auto_retry,
        )

    # === INTERACTIVE KEYBOARDS & BOT COMMANDS ===

    async def click_inline_button(
        self,
        callback_id: str,
        payload: str,
        button_type: str = "CALLBACK",
        timeout: float = 5.0,
    ) -> dict:
        """Click an inline keyboard button (Opcode 118)."""
        return await self.messages.click_inline_button(
            self.ws,
            callback_id=callback_id,
            payload=payload,
            button_type=button_type,
            timeout=timeout,
        )

    async def send_inline_keyboard(
        self,
        chat_id: str | int,
        text: str,
        keyboard: Any,
        parse_mode: str | None = None,
        group_token: str | None = None,
    ) -> dict:
        """Send a message with an inline keyboard."""
        return await self.messages.send_inline_keyboard(
            self.ws,
            chat_id=chat_id,
            message_text=text,
            keyboard=keyboard,
            parse_mode=parse_mode,
            group_token=group_token,
        )
