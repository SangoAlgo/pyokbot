from __future__ import annotations

import asyncio
import json
import time
from typing import TYPE_CHECKING

import websockets

from .errors import AuthenticationError
from .logging_config import logger
from .opcodes import MessageOpcode

if TYPE_CHECKING:
    from .login import Login


class Ws:
    """
    WebSocket connection manager for OK.ru messaging API.

    Handles WebSocket lifecycle, authentication, and routing of incoming messages
    to registered handlers. Includes automatic reconnection with exponential backoff.

    Attributes:
        handles_list: List of registered message handlers.
        authorized: Whether the bot is currently authenticated.
        socket_reconect_counter: Number of reconnection attempts.
    """

    PING_INTERVAL: int = 30
    """Seconds between ping messages to keep connection alive."""

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
        self._rpc_queue: asyncio.Queue = asyncio.Queue()
        self.bot_info: dict | None = None
        self.authorized = False
        self.authorized_event = asyncio.Event()
        self.socket_reconect_counter = 0
        self.login_token: str | None = None
        self.PING_INTERVAL = 30
        self.RECONNECT_DELAY = 5

    async def wait_for_message(self, opcode: int, timeout: float = 30) -> dict | None:
        """Wait for a message with a specific opcode. Returns None on timeout."""
        deadline = time.time() + timeout
        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                logger.warning(f"Timeout waiting for opcode {opcode}")
                return None
            try:
                msg = await asyncio.wait_for(self._rpc_queue.get(), timeout=remaining)
                if msg.get("opcode") == opcode:
                    return msg
            except asyncio.TimeoutError:
                logger.warning(f"Timeout waiting for opcode {opcode}")
                return None

    async def start(self, authcode: str, okweb_token: str):
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

    async def on_authorized(self, message: dict):
        self.bot_info = message

    async def _ws_loop(self):
        self.seq = 0
        self.authorized = False
        self.authorized_event.clear()
        self.login_token = None
        for q in (self._msg_queue, self._rpc_queue):
            while not q.empty():
                try:
                    q.get_nowait()
                except asyncio.QueueEmpty:
                    break
        send_lock = asyncio.Lock()

        async def send(ws, pkt: dict) -> None:
            """Send a JSON packet with sequence number."""
            async with send_lock:
                self.seq += 1
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
            ping_interval=20,
            ping_timeout=10,
            close_timeout=5,
        ) as ws:
            self._conn = ws
            last_ping = time.time()

            async def ping_loop():
                nonlocal last_ping
                try:
                    while True:
                        await asyncio.sleep(5)
                        if self.authorized and self.login_token:
                            if time.time() - last_ping >= self.PING_INTERVAL:
                                ts = int(time.time() * 1000)
                                async with send_lock:
                                    await ws.send(f"PING {self.login_token} {ts}")
                                last_ping = time.time()
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.debug(f"Ping loop error: {e}")

            async def activ_loop():
                try:
                    while True:
                        await asyncio.sleep(60)
                        if self.authorized and self.login_token:
                            await send(ws, {
                                "ver": 10, "cmd": 0,
                                "opcode": MessageOpcode.ACTIVITY,
                                "payload": {"interactive": True}
                            })
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.debug(f"Activity loop error: {e}")

            ping_task = asyncio.create_task(ping_loop())
            activ_task = asyncio.create_task(activ_loop())

            try:
                async for raw in ws:
                    text = raw if isinstance(raw, str) else raw.decode("utf-8", "ignore")
                    try:
                        msg = json.loads(text)
                    except json.JSONDecodeError:
                        continue
                    await self._msg_queue.put(msg)
                    await self._rpc_queue.put(msg)
                    op = msg.get("opcode")
                    p = msg.get("payload", {})

                    if op == MessageOpcode.HELLO:
                        if self.login_token:
                            ts = int(time.time() * 1000)
                            await ws.send(f"PING {self.login_token} {ts}")
                            await send(ws, {
                                "ver": 10, "cmd": 0, "opcode": MessageOpcode.AUTH,
                                "payload": {
                                    "token": self.login_token,
                                    "chatsCount": 20,
                                    "userAgent": self.login.WS_USER_AGENT,
                                    "log": False,
                                    "chatsSync": int(time.time() * 1000),
                                    "contactsSync": int(time.time() * 1000),
                                    "presenceSync": int(time.time() * 1000),
                                    "interactive": True,
                                }
                            })
                        else:
                            await send(ws, {
                                "ver": 10, "cmd": 0, "opcode": MessageOpcode.TOKEN,
                                "payload": {
                                    "token": self.okweb_token,
                                    "tokenType": "OKWEB",
                                    "deviceType": "OKWEB",
                                    "deviceId": "OKWEB:1",
                                }
                            })

                    elif op == MessageOpcode.TOKEN:
                        self.login_token = p.get("token")
                        ts = int(time.time() * 1000)
                        await ws.send(f"PING {self.login_token} {ts}")
                        await send(ws, {
                            "ver": 10, "cmd": 0, "opcode": MessageOpcode.AUTH,
                            "payload": {
                                "token": self.login_token,
                                "chatsCount": 20,
                                "userAgent": self.login.WS_USER_AGENT,
                                "log": False,
                                "chatsSync": 0,
                                "contactsSync": 0,
                                "presenceSync": 0,
                                "interactive": True,
                            }
                        })

                    elif op == MessageOpcode.AUTH:
                        if p.get("error"):
                            raise AuthenticationError(f"OK.ru rejected auth: {p['error']}")
                        self.authorized = True
                        self.socket_reconect_counter = 0
                        self.authorized_event.set()
                        await self.on_authorized(p)
                        logger.info("WebSocket authorized successfully")

            finally:
                ping_task.cancel()
                activ_task.cancel()
                await asyncio.gather(ping_task, activ_task, return_exceptions=True)
