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

## What it can do

- **Commands** — `@bot.on_message(commands=["start", "help"])` catches `/start` and `/help`
- **Filters** — route by content type (photo, video, audio, document, text), exact text, or user/bot
- **Media** — send photos, videos, files, voice messages from URLs or local files
- **HTML** — bold, italic, code, headings, links, mentions with `parse_mode="html"`
- **Chat admin** — pin, edit, delete, clear history, change title/photo, kick members
- **Typing indicator** — show "bot is typing..." before responding
- **Persistent WebSocket** — instant delivery, auto-reconnect with backoff, user info cache

## Next steps

- [Installation](installation.md)
- [Quick Start](quickstart.md)
- [API Reference](api-reference.md)
- [Examples](examples.md)
- [FAQ](faq.md)
