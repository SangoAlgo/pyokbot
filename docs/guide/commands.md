# Commands

Commands are messages that start with `/`. They're the simplest way to let users interact with your bot.

## Registering a command handler

Pass `commands` to `on_message()`:

```python
@bot.on_message(commands=["start", "help"])
async def on_help(message):
    await bot.send_reply(message, "Available: /start, /help, /ping")
```

`"start"` matches `/start`, `"help"` matches `/help`, and so on.

## Parameters

| Parameter  | Type         | Description                          |
|------------|--------------|--------------------------------------|
| `commands` | `list[str]`  | Command names — no `/` prefix needed |

You can combine commands with other filters. See [Filters](filters.md).

## Handler order

Handlers run in the order you register them. The first match wins:

```python
@bot.on_message(commands=["start"])    # checked first
@bot.on_message(commands=["help"])     # checked second
@bot.on_message(filters="user")        # catch-all, checked last
```

If you put a catch-all handler (no `commands`) after your command handlers, it fires for everything that doesn't match.

## Full example

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
        await bot.send_message(
            message.chat.id,
            "/start — welcome\n/help — this\n/ping — pong!"
        )

    @bot.on_message(commands=["ping"])
    async def cmd_ping(message):
        await bot.send_reply(message, "pong!")

    await bot.polling()

asyncio.run(main())
```

## A few things to know

- Commands are case-sensitive. `/Start` won't match `commands=["start"]`.
- Arguments after the command (`/start arg1 arg2`) are ignored by the matcher. Parse `message.text` manually if you need them.
