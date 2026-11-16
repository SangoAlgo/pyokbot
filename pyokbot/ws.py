from __future__ import annotations

import asyncio
import json
import time
from typing import TYPE_CHECKING, Any

import websockets

from .errors import APIError, AuthenticationError, TimeoutError, WebSocketError
from .logging_config import logger
from .opcodes import MessageOpcode

if TYPE_CHECKING:
    from .login import Login


class Ws:
    """
    WebSocket connection manager for OK.ru messaging API.

    Handles WebSocket lifecycle, authentication, correlated RPC requests,
    and routing of incoming messages and events. Includes automatic reconnection
    with exponential backoff.
    """

    PING_INTERVAL: int = 25
    """Seconds between OK.ru keepalive (opcode 1) frames."""

    RECONNECT_DELAY: int = 5
    """Base delay (seconds) for exponential backoff reconnection."""

    def __init__(self, login: Login) -> None:
        """
        Initialize WebSocket connection handler.

        Args:
            login: Login instance containing authentication tokens and configuration.
        """
        self.login = login
        self.handles_list: list[dict] = []
        self._msg_queue: asyncio.Queue = asyncio.Queue()
        self._pending_requests: dict[int, asyncio.Future] = {}
        self._opcode_waiters: dict[int, list[asyncio.Future]] = {}
        self.bot_info: dict | None = None
        self.authorized = False
        self.authorized_event = asyncio.Event()
        self.socket_reconect_counter = 0
        self.login_token: str | None = None
        self.PING_INTERVAL = 25
        self.RECONNECT_DELAY = 5
        self._conn: Any = None
        self._send_lock = asyncio.Lock()
        self.seq = 0

    async def send_packet(self, opcode: int, payload: dict | None = None, cmd: int = 0) -> int:
        """Send a JSON packet to OK.ru over WebSocket with automatic sequence numbering."""
        if not self._conn:
            raise WebSocketError("WebSocket is not connected")
        async with self._send_lock:
            self.seq += 1
            cur_seq = self.seq
            pkt: dict[str, Any] = {
                "ver": 10,
                "cmd": cmd,
                "seq": cur_seq,
                "opcode": opcode,
            }
            if payload is not None:
                pkt["payload"] = payload
            text = json.dumps(pkt, separators=(",", ":"), ensure_ascii=False)
            await self._conn.send(text)
            return cur_seq

    async def request(
        self,
        opcode: int,
        payload: dict | None = None,
        cmd: int = 0,
        timeout: float = 30.0,
    ) -> dict:
        """
        Send an RPC request over WebSocket and await its correlated response by sequence ID.

        Args:
            opcode: The OK.ru opcode to request.
            payload: Optional payload dictionary.
            cmd: Command flag (default 0 for request).
            timeout: Maximum seconds to wait for response.

        Returns:
            The parsed response message dictionary.

        Raises:
            APIError: If the server returned an error response (cmd == 3 or payload error).
            TimeoutError: If the server did not respond within the timeout.
            WebSocketError: If the connection dropped during the request.
        """
        if not self._conn:
            raise WebSocketError("WebSocket is not connected")
        loop = asyncio.get_running_loop()
        fut: asyncio.Future = loop.create_future()

        async with self._send_lock:
            self.seq += 1
            cur_seq = self.seq
            pkt: dict[str, Any] = {
                "ver": 10,
                "cmd": cmd,
                "seq": cur_seq,
                "opcode": opcode,
            }
            if payload is not None:
                pkt["payload"] = payload
            self._pending_requests[cur_seq] = fut
            text = json.dumps(pkt, separators=(",", ":"), ensure_ascii=False)
            await self._conn.send(text)

        try:
            res = await asyncio.wait_for(fut, timeout=timeout)
            p = res.get("payload", {})
            if res.get("cmd") == 3 or (isinstance(p, dict) and p.get("error")):
                err_msg = p.get("message") or p.get("error") if isinstance(p, dict) else str(p)
                raise APIError(f"OK.ru API error (opcode {opcode}): {err_msg}")
            return res
        except asyncio.TimeoutError:
            self._pending_requests.pop(cur_seq, None)
            raise TimeoutError(
                f"Timeout ({timeout}s) waiting for response to opcode {opcode} (seq {cur_seq})"
            )
        except Exception:
            self._pending_requests.pop(cur_seq, None)
            raise

    async def wait_for_message(self, opcode: int, timeout: float = 30.0) -> dict | None:
        """
        Wait for an unsolicited message or response matching opcode.
        Provided for backward compatibility. Returns None on timeout.
        """
        loop = asyncio.get_running_loop()
        fut: asyncio.Future = loop.create_future()
        if opcode not in self._opcode_waiters:
            self._opcode_waiters[opcode] = []
        self._opcode_waiters[opcode].append(fut)
        try:
            return await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for opcode {opcode}")
            return None
        finally:
            if opcode in self._opcode_waiters and fut in self._opcode_waiters[opcode]:
                self._opcode_waiters[opcode].remove(fut)

    async def start(self, authcode: str, okweb_token: str) -> None:
        """Start the WebSocket connection loop. Reconnects on disconnect."""
        self.AUTHCODE = authcode
        self.okweb_token = okweb_token
        while True:
            try:
                await self._ws_loop()
            except asyncio.CancelledError:
                logger.info("WebSocket connection cancelled")
                break
            except Exception as e:
                logger.warning(f"WS disconnected: {e}")
            self.socket_reconect_counter += 1
            delay = min(60, self.RECONNECT_DELAY * (2 ** (self.socket_reconect_counter - 1)))
            logger.info(f"Reconnecting in {delay}s (attempt {self.socket_reconect_counter})")
            await asyncio.sleep(delay)

    async def get_bot_info(self) -> dict:
        """Wait for authorization and return bot profile info."""
        await self.authorized_event.wait()
        while self.bot_info is None:
            await asyncio.sleep(0.05)
        return self.bot_info

    async def on_authorized(self, message: dict) -> None:
        self.bot_info = message

    async def _ws_loop(self) -> None:
        self.seq = 0
        self.authorized = False
        self.authorized_event.clear()
        self.login_token = None

        # Clean up any pending futures
        for fut in list(self._pending_requests.values()):
            if not fut.done():
                fut.set_exception(WebSocketError("WebSocket disconnected"))
        self._pending_requests.clear()

        for waiters in self._opcode_waiters.values():
            for fut in waiters:
                if not fut.done():
                    fut.set_exception(WebSocketError("WebSocket disconnected"))
        self._opcode_waiters.clear()

        # Clear message queue
        while not self._msg_queue.empty():
            try:
                self._msg_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        async def send(ws: Any, pkt: dict, cmd: int = 0) -> None:
            """Send a JSON packet with sequence number."""
            async with self._send_lock:
                self.seq += 1
                pkt["ver"] = 10
                pkt["cmd"] = cmd
                pkt["seq"] = self.seq
                await ws.send(
                    json.dumps(pkt, separators=(",", ":"), ensure_ascii=False)
                )

        async with websockets.connect(
            self.login.WS_URL,
            additional_headers={
                "Cookie": f"AUTHCODE={self.AUTHCODE}",
                "Origin": self.login.BASE_URL,
                "User-Agent": self.login.UA,
            },
            ping_interval=None,
            ping_timeout=None,
            close_timeout=5,
        ) as ws:
            self._conn = ws

            async def ping_loop() -> None:
                """Send keepalive frames every PING_INTERVAL seconds once authorized."""
                try:
                    while True:
                        await asyncio.sleep(self.PING_INTERVAL)
                        await send(ws, {
                            "opcode": MessageOpcode.PING,
                            "payload": {"interactive": True},
                        })
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.debug(f"Ping loop error: {e}")

            ping_task: asyncio.Task | None = None

            try:
                async for raw in ws:
                    text = raw if isinstance(raw, str) else raw.decode("utf-8", "ignore")
                    if text.strip() == "PONG":
                        logger.debug("Keepalive PONG received")
                        continue

                    try:
                        msg = json.loads(text)
                    except json.JSONDecodeError:
                        continue

                    op = msg.get("opcode")
                    cmd = msg.get("cmd")
                    seq = msg.get("seq")
                    p = msg.get("payload", {})

                    if op == MessageOpcode.PING:
                        continue

                    # Correlate RPC requests waiting on this sequence number
                    if seq in self._pending_requests:
                        fut = self._pending_requests.pop(seq)
                        if not fut.done():
                            fut.set_result(msg)

                    # Notify any listeners waiting by opcode
                    if op in self._opcode_waiters and self._opcode_waiters[op]:
                        waiter = self._opcode_waiters[op].pop(0)
                        if not waiter.done():
                            waiter.set_result(msg)

                    # Forward message to general message queue
                    await self._msg_queue.put(msg)

                    # Handle connection handshake steps
                    if op == MessageOpcode.HELLO:
                        if self.login_token:
                            now_ms = int(time.time() * 1000)
                            await send(ws, {
                                "opcode": MessageOpcode.AUTH,
                                "payload": {
                                    "token": self.login_token,
                                    "chatsCount": 50,
                                    "userAgent": self.login.WS_USER_AGENT,
                                    "log": False,
                                    "chatsSync": now_ms,
                                    "contactsSync": now_ms,
                                    "presenceSync": now_ms,
                                    "interactive": True,
                                },
                            })
                            await ws.send(f"PING {self.login_token} {now_ms}")
                        else:
                            await send(ws, {
                                "opcode": MessageOpcode.TOKEN,
                                "payload": {
                                    "token": self.okweb_token,
                                    "tokenType": "OKWEB",
                                    "deviceType": "OKWEB",
                                    "deviceId": "OKWEB:1",
                                },
                            })

                    elif op == MessageOpcode.TOKEN:
                        self.login_token = p.get("token")
                        now_ms = int(time.time() * 1000)
                        await send(ws, {
                            "opcode": MessageOpcode.AUTH,
                            "payload": {
                                "token": self.login_token,
                                "chatsCount": 50,
                                "userAgent": self.login.WS_USER_AGENT,
                                "log": False,
                                "chatsSync": now_ms,
                                "contactsSync": now_ms,
                                "presenceSync": now_ms,
                                "interactive": True,
                            },
                        })
                        # Essential raw keepalive frame required by OK.ru
                        await ws.send(f"PING {self.login_token} {now_ms}")

                    elif op == MessageOpcode.AUTH:
                        if p.get("error"):
                            raise AuthenticationError(f"OK.ru rejected auth: {p['error']}")
                        self.authorized = True
                        self.socket_reconect_counter = 0
                        self.authorized_event.set()
                        await self.on_authorized(p)
                        logger.info("WebSocket authorized successfully")

                        # Send initial application keepalive frame
                        await send(ws, {
                            "opcode": MessageOpcode.PING,
                            "payload": {"interactive": True},
                        })

                        # Start periodic keepalive
                        if ping_task is None or ping_task.done():
                            ping_task = asyncio.create_task(ping_loop())

                    elif op == MessageOpcode.INCOMING_MESSAGE:
                        chat_id = p.get("chatId")
                        message = p.get("message")
                        if (
                            chat_id is not None
                            and isinstance(message, dict)
                            and message.get("id")
                        ):
                            is_group = str(chat_id).startswith("-") if isinstance(chat_id, (int, str)) else False
                            await send(ws, {
                                "opcode": MessageOpcode.INCOMING_MESSAGE,
                                "payload": {
                                    "chatId": chat_id,
                                    "messageId": message["id"],
                                    "chatType": "CHAT" if is_group else "DIALOG",
                                },
                            }, cmd=1)

            finally:
                if ping_task:
                    ping_task.cancel()
                    await asyncio.gather(ping_task, return_exceptions=True)
