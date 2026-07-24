# pyokbot

**pyokbot** is an asynchronous Python library for creating bots in the **Odnoklassniki (ok.ru)** messenger. It communicates directly via the WebSocket protocol used by OK.ru's own clients — no HTTP polling, no browser automation, no third-party dependencies on unofficial APIs.

## Why pyokbot?

pyokbot is the **only Python library** for building bots on Odnoklassniki. If you want to automate OK.ru messaging with Python, this is it.

- **Real-time** — messages arrive instantly over a persistent WebSocket connection
- **Full feature parity** — send text, photos, videos, files, voice messages; manage chats; format with HTML
- **Async from the ground up** — built on `asyncio` and `aiohttp` for high concurrency
- **Auto-reconnect** — handles network drops with exponential backoff

## Quick example

```python
import asyncio
from pyokbot import Vanus

async def main():
    bot = Vanus("YOUR_AUTHCODE")
    await bot.run()

    @bot.on_message(filters="user")
    async def echo(message):
        await bot.send_reply(message, f"You said: {message.text}")

    await bot.polling()

asyncio.run(main())
```

## Next steps

- [Installation](installation.md) — get pyokbot up and running
- [Quick Start](quickstart.md) — build your first bot in 5 minutes
- [API Reference](api-reference.md) — full class and method documentation
- [Examples](examples.md) — ready-to-run bot scripts
- [FAQ](faq.md) — frequently asked questions
