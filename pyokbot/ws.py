"""
WebSocket connection handler for OK.ru messaging API.

Manages the WebSocket lifecycle, authentication, and message routing.
"""

import asyncio
import json
import logging
import time
from typing import Any, Callable, Dict, Optional

import websockets

from .logging_config import logger
from .opcodes import MessageOpcode

# Type alias for message handler functions
MessageHandler = Callable[[Dict[str, Any]], None]


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

    def __init__(self, login: "Login") -> None:
        """
        Initialize WebSocket connection handler.

        Args:
            login: Login instance containing authentication tokens and configuration.
        """
        self.login = login
        self.handles_list: list[Dict[str, Any]] = []
        self._msg_queue: asyncio.Queue = asyncio.Queue()
        self._rpc_queue: asyncio.Queue = asyncio.Queue()
        self.bot_info: Optional[Dict[str, Any]] = None
        self.authorized: bool = False
        self.authorized_event: asyncio.Event = asyncio.Event()
        self.socket_reconect_counter: int = 0
        self.login_token: Optional[str] = None
        self._conn: Optional[websockets.WebSocketClientProtocol] = None

    async def wait_for_message(
        self, opcode: int, timeout: float = 30.0
    ) -> Optional[Dict[str, Any]]:
        """
        Wait for a message with a specific opcode.

        Args:
            opcode: The MessageOpcode to wait for.
            timeout: Maximum time to wait in seconds. Defaults to 30.

        Returns:
            The message dict if received within timeout, None otherwise.

        Example:
            >>> response = await ws.wait_for_message(MessageOpcode.AUTH_RESPONSE)
        """
        deadline = time.time() + timeout
        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                logger.warning(f"Timeout waiting for opcode {opcode}")
                return None
            try:
                msg = await asyncio.wait_for(
                    self._rpc_queue.get(), timeout=remaining
                )
                if msg.get("opcode") == opcode:
                    return msg
            except asyncio.TimeoutError:
                logger.warning(f"Timeout waiting for opcode {opcode}")
                return None

    async def get_bot_info(self) -> Dict[str, Any]:
        """
        Get the bot's profile information.

        Waits for authorization first, then retrieves cached bot info.

        Returns:
            Dictionary containing bot profile data.

        Raises:
            TimeoutError: If bot info is not available after authorization.
        """
        await self.authorized_event.wait()
        # Wait for bot_info to be populated (max 5 seconds)
        for _ in range(100):
            if self.bot_info is not None:
                return self.bot_info
            await asyncio.sleep(0.05)
        raise TimeoutError("Bot info not received")

    async def start(self, authcode: str, okweb_token: str) -> None:
        """
        Start the WebSocket connection with automatic reconnection.

        Maintains connection to OK.ru WebSocket API and automatically reconnects
        on disconnection with exponential backoff.

        Args:
            authcode: The OK.ru AUTHCODE cookie value.
            okweb_token: The OKWEB authentication token.

        Note:
            This is a long-running coroutine that should be run in the background.
        """
        self.AUTHCODE = authcode
        self.okweb_token = okweb_token

        while True:
            try:
                await self._ws_loop()
            except asyncio.CancelledError:
                logger.info("WebSocket connection cancelled")
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")

            self.socket_reconect_counter += 1
            delay = min(
                60, self.RECONNECT_DELAY * (2 ** (self.socket_reconect_counter - 1))
            )
            logger.info(
                f"Reconnecting in {delay}s (attempt {self.socket_reconect_counter})"
            )
            await asyncio.sleep(delay)

    async def _ws_loop(self) -> None:
        """
        Main WebSocket connection loop.

        Handles authentication, message routing, and keep-alive pings.
        """
        self.seq = 0
        self.authorized = False
        self.authorized_event.clear()
        self.login_token = None

        # Clear queues
        while not self._msg_queue.empty():
            try:
                self._msg_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        while not self._rpc_queue.empty():
            try:
                self._rpc_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        send_lock = asyncio.Lock()

        async def send(ws: websockets.WebSocketClientProtocol, pkt: Dict) -> None:
            """Send a JSON packet with sequence number."""
            async with send_lock:
                self.seq += 1
                pkt["seq"] = self.seq
                await ws.send(
                    json.dumps(pkt, separators=(",", ":"), ensure_ascii=False)
                )

        try:
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
                logger.debug("WebSocket connected")

                # === PING LOOP ===
                async def ping_loop() -> None:
                    """Send ping messages to keep connection alive."""
                    nonlocal last_ping
                    try:
                        while True:
                            await asyncio.sleep(5)
                            if self.authorized and self.login_token:
                                if time.time() - last_ping >= self.PING_INTERVAL:
                                    ts = int(time.time() * 1000)
                                    msg = f"PING {self.login_token} {ts}"

                                    async with send_lock:
                                        await ws.send(msg)

                                    last_ping = time.time()
                                    logger.debug("Ping sent")
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:
                        logger.error(f"Ping loop error: {e}")

                # === ACTIVITY LOOP ===
                async def activ_loop() -> None:
                    """Send periodic activity notifications."""
                    try:
                        while True:
                            await asyncio.sleep(60)
                            if self.authorized and self.login_token:
                                await send(
                                    ws,
                                    {
                                        "ver": 10,
                                        "cmd": 0,
                                        "opcode": MessageOpcode.ACTIVITY,
                                        "payload": {"interactive": True},
                                    },
                                )
                                logger.debug("Activity update sent")
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:
                        logger.error(f"Activity loop error: {e}")

                ping_task = asyncio.create_task(ping_loop())
                activ_task = asyncio.create_task(activ_loop())

                try:
                    async for raw in ws:
                        text = (
                            raw if isinstance(raw, str) else raw.decode("utf-8", "ignore")
                        )

                        try:
                            msg = json.loads(text)
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON received: {text[:100]}")
                            continue

                        await self._msg_queue.put(msg)
                        await self._rpc_queue.put(msg)

                        op = msg.get("opcode")
                        p = msg.get("payload", {})

                        # === HELLO (opcode 6) ===
                        if op == MessageOpcode.HELLO:
                            logger.debug("Hello received from server")

                            if self.login_token:
                                ts = int(time.time() * 1000)
                                await ws.send(f"PING {self.login_token} {ts}")

                                await send(
                                    ws,
                                    {
                                        "ver": 10,
                                        "cmd": 0,
                                        "opcode": MessageOpcode.AUTH_RESPONSE,
                                        "payload": {
                                            "token": self.login_token,
                                            "chatsCount": 20,
                                            "userAgent": self.login.WS_USER_AGENT,
                                            "log": False,
                                            "chatsSync": int(time.time() * 1000),
                                            "contactsSync": int(time.time() * 1000),
                                            "presenceSync": int(time.time() * 1000),
                                            "interactive": True,
                                        },
                                    },
                                )

                            else:
                                await send(
                                    ws,
                                    {
                                        "ver": 10,
                                        "cmd": 0,
                                        "opcode": MessageOpcode.OKWEB_TOKEN_RESPONSE,
                                        "payload": {
                                            "token": self.okweb_token,
                                            "tokenType": "OKWEB",
                                            "deviceType": "OKWEB",
                                            "deviceId": "OKWEB:1",
                                        },
                                    },
                                )

                        # === TOKEN (opcode 23) ===
                        elif op == MessageOpcode.OKWEB_TOKEN_RESPONSE:
                            logger.debug("Token response received")
                            self.login_token = p.get("token")

                            ts = int(time.time() * 1000)
                            await ws.send(f"PING {self.login_token} {ts}")

                            await send(
                                ws,
                                {
                                    "ver": 10,
                                    "cmd": 0,
                                    "opcode": MessageOpcode.AUTH_RESPONSE,
                                    "payload": {
                                        "token": self.login_token,
                                        "chatsCount": 20,
                                        "userAgent": self.login.WS_USER_AGENT,
                                        "log": False,
                                        "chatsSync": 0,
                                        "contactsSync": 0,
                                        "presenceSync": 0,
                                        "interactive": True,
                                    },
                                },
                            )

                        # === AUTH (opcode 19) ===
                        elif op == MessageOpcode.AUTH_RESPONSE:
                            logger.debug("Auth response received")
                            if p.get("error"):
                                logger.error("Authentication failed")
                                raise Exception("AUTH FAILED")

                            self.authorized = True
                            self.socket_reconect_counter = 0
                            self.authorized_event.set()
                            await self._on_authorized(p)
                            logger.info("Bot authorized successfully")

                finally:
                    ping_task.cancel()
                    activ_task.cancel()
                    await asyncio.gather(ping_task, activ_task, return_exceptions=True)

        except websockets.exceptions.WebSocketException as e:
            logger.error(f"WebSocket exception: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in WebSocket loop: {e}")
            raise

    async def _on_authorized(self, message: Dict[str, Any]) -> None:
        """
        Handle authorization completion.

        Args:
            message: The authorization response message.
        """
        self.bot_info = message
