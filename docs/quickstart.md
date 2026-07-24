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

Every bot follows the same pattern:

| Step                    | Method           | What happens                                      |
| ----------------------- | ---------------- | ------------------------------------------------- |
| Create instance         | `Vanus(auth)`    | Validates auth, sets up WebSocket                  |
| Connect                 | `await bot.run()` | Opens WebSocket, authorizes, fetches bot profile  |
| Register handlers       | `@bot.on_message` | Define what your bot responds to                  |
| Start listening         | `await bot.polling()` | Loop forever, process incoming messages     |
| Clean up (optional)     | `await bot.stop()` | Close WebSocket, cancel tasks                  |

Or use the context manager:

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
        await bot.send_message(message.chat.id, "Available: /start, /help, /ping")

    @bot.on_message(commands=["ping"])
    async def cmd_ping(message):
        await bot.send_reply(message, "pong!")

    # Catch-all for non-command messages
    @bot.on_message(filters="user")
    async def fallback(message):
        await bot.send_reply(message, f"Echo: {message.text}")

    await bot.polling()

asyncio.run(main())
```

## Sending messages

| Method                    | Use case                    |
| ------------------------- | --------------------------- |
| `send_message(chat_id, text)` | Send to any chat ID     |
| `send_reply(message, text)` | Reply to an incoming message |

Both accept `parse_mode="html"` for [HTML formatting](guide/formatting.md).

## The message object

Handlers receive a `Munch` object. Access fields as attributes:

```python
async def handler(message):
    message.text          # "hello world"
    message.chat.id       # "12345"
    message.user.id       # "67890"
    message.id            # "msg_001"
    message.photo         # list of photo dicts — if the message has photos
    message.video         # list of video dicts — if it has videos
    message.audio         # audio dict — if it has audio
    message.document      # file dict — if it has a file
    message.is_reply      # True/False
    message.reply         # the replied-to message, if any
```

## Next steps

- [Commands](guide/commands.md) — add `/` handlers to your bot
- [Filters](guide/filters.md) — control which messages trigger which handlers
- [Media](guide/media.md) — send photos, videos, files, voice
- [HTML Formatting](guide/formatting.md) — rich text in messages
- [Chat Admin](guide/chat-admin.md) — manage chats from your bot
- [Typing Indicator](guide/typing.md) — show "bot is typing..." before replies
