# Typing Indicator

Show a "bot is typing..." indicator before your bot responds. Makes the bot feel more responsive — like there's someone on the other end.

## Usage

Call `writing_emulation(chat_id)` before you send your reply:

```python
@bot.on_message(commands=["ping"])
async def cmd_ping(message):
    await bot.writing_emulation(message.chat.id)
    await asyncio.sleep(0.5)  # let the indicator show for a moment
    await bot.send_reply(message, "pong!")
```

## Parameters

| Parameter | Type   | Description      |
|-----------|--------|------------------|
| `chat_id` | `str`  | Target chat ID   |

The indicator lasts about 5 seconds and clears on its own.

## When to use it

- Before replying to a command that needs a moment to process
- When composing multi-part responses
- Any time you want to signal the bot is "working"

## One thing to know

You don't need to stop the indicator manually. OK.ru clears it after a few seconds. For instant replies — under a second — it's not visible long enough to matter.
