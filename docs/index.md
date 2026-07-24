# pyokbot

Python library for Odnoklassniki (ok.ru) bots. WebSocket, async, no polling.

pyokbot speaks the raw WebSocket protocol OK.ru's own clients use — messages arrive instantly, no HTTP polling, no delays. It's the only Python library for OK.ru bots.

```python
import asyncio
from pyokbot import Vanus

async def main():
    bot = Vanus("YOUR_AUTHCODE")
    await bot.run()

    @bot.on_message(commands=["ping"])
    async def ping(message):
        await bot.send_reply(message, "pong!")

    await bot.polling()

asyncio.run(main())
```

## Features

| Feature             | What it does                                                |
| ------------------- | ----------------------------------------------------------- |
| **Commands**        | `/start`, `/help`, `/ping` — any command you define         |
| **Filters**         | Route by user/bot, exact text, or content type              |
| **Media**           | Send photos, videos, files, voice messages                  |
| **HTML formatting** | Bold, italic, code, headings, links in messages             |
| **Chat admin**      | Pin, edit, delete, clear history, kick, rename              |
| **Typing indicator**| Show "bot is typing..." before responding                   |
| **Auto-reconnect**  | Exponential backoff on WebSocket disconnection              |
| **User info cache** | Profile data cached for 1 hour to avoid repeated lookups    |

## Why pyokbot?

- **One-of-a-kind** — the only Python library that talks to OK.ru's real-time messaging API
- **Instant** — WebSocket pushes messages the moment they're sent, no polling interval
- **Pure async** — built on `asyncio` + `aiohttp` from the ground up
- **Simple** — one class, one decorator, a handful of send methods; no 500-page manual

## Next steps

- [Installation](installation.md) — get your auth code and install the library
- [Quick Start](quickstart.md) — build your first bot in 5 minutes
- [Guide](guide/commands.md) — learn every feature step by step
- [Examples](examples.md) — ready-to-run bots in the repo
- [FAQ](faq.md) — common questions and troubleshooting
