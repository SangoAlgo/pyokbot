# pyokbot

Python library for Odnoklassniki bots. Async, WebSocket, no polling.

pyokbot talks the same WebSocket protocol OK.ru's own clients use. Messages arrive the moment they're sent — no HTTP polling, no delays. It's the only Python library for OK.ru bots.

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

## What you get

| Feature | What it does |
|---|---|
| **Commands** | `/start`, `/help`, `/ping` — anything you like |
| **Filters** | Route by sender, text, or content type |
| **Media** | Photos, videos, files, voice messages |
| **HTML formatting** | Bold, italic, code, headings, links |
| **Chat admin** | Pin, edit, delete, clear, kick, rename |
| **Typing indicator** | Show "bot is typing..." before you reply |
| **Auto-reconnect** | Exponential backoff when the connection drops |
| **User info cache** | Profile data cached for an hour |

## Why this exists

pyokbot is the only library that talks to OK.ru's real-time messaging API. It's pure async — built on `asyncio` and `aiohttp` from the ground up. One class, one decorator, a handful of send methods. That's it.

## Next steps

- [Installation](installation.md) — get your auth code and install the library
- [Quick Start](quickstart.md) — your first bot in 5 minutes
- [Guide](guide/commands.md) — learn every feature
- [Examples](examples.md) — ready-to-run bots
- [FAQ](faq.md) — common questions
