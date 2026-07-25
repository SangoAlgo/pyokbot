# Filters

Filters route messages based on who sent them, what they contain, or their exact text.

## How they work

All filter parameters are optional. Pass more than one and they combine with **AND** — every condition must match.

### `filters` — sender type

| Value    | Effect                          |
|----------|---------------------------------|
| `"user"` | Only messages from real people  |
| `"bot"`  | Only messages from other bots   |
| `None`   | Both users and bots             |

```python
@bot.on_message(filters="user")
async def from_user(message):
    await bot.send_reply(message, "Hello, human!")
```

### `text` — exact match

```python
@bot.on_message(text="hello")
async def on_hello(message):
    await bot.send_reply(message, "Hi there!")
```

Pass a list to match any of several texts:

```python
@bot.on_message(text=["hi", "hey", "hello"])
async def on_greeting(message):
    await bot.send_reply(message, "Hey!")
```

### `content_types` — media type

| Value        | Matches                           |
|--------------|-----------------------------------|
| `"photo"`    | Messages with one or more photos  |
| `"video"`    | Messages with a video             |
| `"audio"`    | Voice messages                    |
| `"document"` | File attachments                  |
| `"text"`     | Plain text — no media             |
| `"commands"` | Any message starting with `/`     |

```python
@bot.on_message(filters="user", content_types=["photo"])
async def handle_photo(message):
    await bot.send_reply(message, "Nice photo!")
```

### Combining filters

Pass multiple parameters — they all must match:

```python
@bot.on_message(
    filters="user",
    commands=["start"],
    content_types=["text"],
)
async def combined(message):
    ...
```

This matches only when **all** conditions are true: the sender is a user, the message is `/start`, and there's no media attached.

### No filters = catch-all

```python
@bot.on_message()               # matches everything
@bot.on_message(filters="user") # matches all user messages
```

## Full example

See [`examples/filter_demo_bot.py`](https://github.com/SangoAlgo/pyokbot/blob/main/examples/filter_demo_bot.py) — it demonstrates every filter type in one bot.

## A couple of notes

- `content_types=["commands"]` only checks if the text starts with `/`. Use `commands=` (see [Commands](commands.md)) to match specific commands.
- The `text` filter is case-sensitive and must match the full message text.
