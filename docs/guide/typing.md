# Typing Indicator

Show a "bot is typing..." indicator before your bot responds. Makes the bot feel more responsive and natural.

## Usage

Call `writing_emulation(chat_id)` before sending your reply:

```python
@bot.on_message(commands=["ping"])
async def cmd_ping(message):
    await bot.writing_emulation(message.chat.id)
    await asyncio.sleep(0.5)  # simulate thinking
    await bot.send_reply(message, "pong!")
```

## Parameters

| Parameter | Type  | Description       |
| --------- | ----- | ----------------- |
| `chat_id` | `str` | Target chat ID    |

The indicator lasts for about 5 seconds automatically.

## When to use it

- Before replying to a command that requires processing time
- When composing multi-part responses
- Anywhere you want to signal the bot is "working"

## Notes

- You don't need to stop the indicator manually — OK.ru clears it after a few seconds.
- For instant replies (under 1 second), the typing indicator isn't visible long enough to matter.
