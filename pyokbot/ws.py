import json
import asyncio
import time
import websockets


class Ws:

    def __init__(self, login):
        self.login = login

        self.handles_list = []
        self._msg_queue = asyncio.Queue()
        self._rpc_queue = asyncio.Queue()
        self.bot_info = None
        self.authorized = False
        self.authorized_event = asyncio.Event()
        self.socket_reconect_counter = 0
        self.login_token = None

        self.PING_INTERVAL = 30
        self.RECONNECT_DELAY = 5


    # === WAIT ===
    async def wait_for_message(self, opcode: int, timeout: float = 30):
        deadline = time.time() + timeout
        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                return None
            try:
                msg = await asyncio.wait_for(
                    self._rpc_queue.get(), timeout=remaining
                )
                if msg.get("opcode") == opcode:
                    return msg
            except asyncio.TimeoutError:
                return None


    # === START ===
    async def start(self, AUTHCODE: str, okweb_token: str):
        self.AUTHCODE = AUTHCODE
        self.okweb_token = okweb_token

        while True:
            try:
                await self._ws_loop()
            except asyncio.CancelledError:
                break
            except Exception:
                pass

            self.socket_reconect_counter += 1
            delay = min(60, self.RECONNECT_DELAY * (2 ** (self.socket_reconect_counter - 1)))
            await asyncio.sleep(delay)


    # === INFO ===
    async def get_bot_info(self):
        await self.authorized_event.wait()
        while self.bot_info is None:
            await asyncio.sleep(0.05)
        return self.bot_info


    async def on_authorized(self, message: dict):
        self.bot_info = message


    # === WS LOOP ===
    async def _ws_loop(self):
        self.seq = 0
        self.authorized = False
        self.authorized_event.clear()
        self.login_token = None

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

        async def send(ws, pkt: dict):
            async with send_lock:
                self.seq += 1
                pkt["seq"] = self.seq
                await ws.send(json.dumps(pkt, separators=(",", ":"), ensure_ascii=False))

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

            # === PING ===
            async def ping_loop():
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
                except asyncio.CancelledError:
                    pass
                except Exception:
                    pass

            # === ACTIVITY ===
            async def activ_loop():
                try:
                    while True:
                        await asyncio.sleep(60)
                        if self.authorized and self.login_token:
                            await send(ws, {
                                "ver": 10,
                                "cmd": 0,
                                "opcode": 1,
                                "payload": {"interactive": True}
                            })
                except asyncio.CancelledError:
                    pass
                except Exception:
                    pass

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

                    # === HELLO ===
                    if op == 6:

                        if self.login_token:
                            ts = int(time.time() * 1000)
                            await ws.send(f"PING {self.login_token} {ts}")

                            await send(ws, {
                                "ver": 10,
                                "cmd": 0,
                                "opcode": 19,
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
                                "ver": 10,
                                "cmd": 0,
                                "opcode": 23,
                                "payload": {
                                    "token": self.okweb_token,
                                    "tokenType": "OKWEB",
                                    "deviceType": "OKWEB",
                                    "deviceId": "OKWEB:1",
                                }
                            })

                    # === TOKEN ===
                    elif op == 23:
                        self.login_token = p.get("token")

                        ts = int(time.time() * 1000)
                        await ws.send(f"PING {self.login_token} {ts}")

                        await send(ws, {
                            "ver": 10,
                            "cmd": 0,
                            "opcode": 19,
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

                    # === AUTH ===
                    elif op == 19:
                        if p.get("error"):
                            raise Exception("AUTH FAILED")

                        self.authorized = True
                        self.socket_reconect_counter = 0
                        self.authorized_event.set()
                        await self.on_authorized(p)

            finally:
                ping_task.cancel()
                activ_task.cancel()
                await asyncio.gather(ping_task, activ_task, return_exceptions=True)