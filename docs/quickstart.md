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

## Bot lifecycle

Every bot follows the same path:

1. **Create** — `Vanus(auth)` sets up the WebSocket and validates your auth code
2. **Connect** — `await bot.run()` opens the connection and fetches your bot's profile
3. **Register handlers** — `@bot.on_message(...)` defines what your bot reacts to
4. **Listen** — `await bot.polling()` runs forever, dispatching messages to handlers

Or use the context manager. It calls `run()` and `stop()` for you:

```python
async with Vanus("YOUR_AUTHCODE") as bot:
    @bot.on_message(commands=["ping"])
    async def ping(message):
        await bot.send_reply(message, "pong!")
    await bot.polling()
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
        await bot.send_message(message.chat.id, "/start — welcome\n/help — this\n/ping — pong!")

    @bot.on_message(commands=["ping"])
    async def cmd_ping(message):
        await bot.send_reply(message, "pong!")

    @bot.on_message(filters="user")
    async def fallback(message):
        await bot.send_reply(message, f"Echo: {message.text}")

    await bot.polling()

asyncio.run(main())
```

## Sending messages

| Method | When to use it |
|---|---|
| `send_message(chat_id, text)` | Send to any chat by ID |
| `send_reply(message, text)` | Reply to an incoming message |

Both accept `parse_mode="html"` for [HTML formatting](guide/formatting.md).

## The message object

Handlers receive a `Munch` object. You access fields as attributes:

```python
async def handler(message):
    message.text          # "hello world"
    message.chat.id       # "12345"
    message.user.id       # "67890"
    message.id            # "msg_001"
    message.photo         # list of photo dicts, if present
    message.video         # list of video dicts, if present
    message.audio         # audio dict, if present
    message.document      # file dict, if present
    message.is_reply      # True or False
    message.reply         # the replied-to message, if any
```

## Next steps

- [Commands](guide/commands.md) — add `/` handlers
- [Filters](guide/filters.md) — control which messages trigger what
- [Media](guide/media.md) — send photos, videos, files, voice
- [HTML Formatting](guide/formatting.md) — rich text
- [Chat Admin](guide/chat-admin.md) — manage chats
- [Typing Indicator](guide/typing.md) — show "typing..." before replies
