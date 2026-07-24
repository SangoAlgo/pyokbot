# Quick Start

## Echo bot

Create a file `bot.py`:

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

Run it:

```bash
python bot.py
```

## Bot with commands

```python
import asyncio
from pyokbot import Vanus

async def main():
    bot = Vanus("YOUR_AUTHCODE")
    await bot.run()

    @bot.on_message(commands=["start"])
    async def cmd_start(message):
        await bot.send_message(message.chat.id, "Welcome!")

    @bot.on_message(commands=["help"])
    async def cmd_help(message):
        await bot.send_message(message.chat.id, "Available: /start, /help, /ping")

    @bot.on_message(commands=["ping"])
    async def cmd_ping(message):
        await bot.send_reply(message, "pong!")

    @bot.on_message(filters="user")
    async def fallback(message):
        await bot.send_reply(message, f"Echo: {message.text}")

    await bot.polling()

asyncio.run(main())
```

## Handling media

```python
@bot.on_message(filters="user", content_types=["photo"])
async def handle_photo(message):
    await bot.send_reply(message, "Nice photo!")

@bot.on_message(filters="user", content_types=["video"])
async def handle_video(message):
    await bot.send_message(message.chat.id, "Got a video!")

@bot.on_message(filters="user", content_types=["audio"])
async def handle_audio(message):
    await bot.send_message(message.chat.id, "Voice message received!")
```

## How handlers work

Handlers are checked **in registration order**. The **first matching handler** wins — subsequent handlers are skipped. This is the same model used by aiogram and python-telegram-bot.

```python
@bot.on_message(commands=["start"])    # checked first
@bot.on_message(commands=["help"])     # checked second
@bot.on_message(filters="user")        # checked last (catch-all)
```

## Message object

When a handler fires, it receives a `Munch` object with attribute-style access:

```python
async def handler(message):
    message.text          # "hello world"
    message.chat.id       # "12345"
    message.user.id       # "67890"
    message.id            # "msg_001"
    message.photo         # [{"token": "...", "url": "...", ...}] — if photo
    message.video         # [{"token": "...", ...}] — if video
    message.audio         # {"token": "...", ...} — if audio
    message.document      # {"name": "...", ...} — if file
```
