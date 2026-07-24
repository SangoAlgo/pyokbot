# Examples

All examples are in the [`examples/`](https://github.com/SangoAlgo/pyokbot/tree/main/examples) directory.

## echobot.py

A classic echo bot with command handling:

```bash
python examples/echobot.py AUTHCODE
```

- `/start` — welcome message
- `/help` — command list
- `/info` — your user info (name, ID, status)
- `/ping` → `pong!`
- `/stop` — shuts down the bot
- Sends photos, videos, audio back with captions
- Echoes any text message

## media_bot.py

Demonstrates sending different media types:

```bash
python examples/media_bot.py AUTHCODE
```

- `/photo` — sends a sample photo from URL
- `/video` — sends a sample video
- `/file` — sends a PDF document
- `/voice` — sends a voice message

## filter_demo_bot.py

Showcases every filter type in the library:

```bash
python examples/filter_demo_bot.py AUTHCODE
```

| Filter | Triggers on |
|--------|-------------|
| `commands=["start"]` | `/start` |
| `text="hello"` | Exact match "hello" |
| `text=["hi", "hey"]` | Any of the listed texts |
| `content_types=["photo"]` | Photo messages |
| `content_types=["video"]` | Video messages |
| `content_types=["audio"]` | Audio messages |
| `content_types=["document"]` | File messages |
| `filters="user"` (no other filters) | Catch-all fallback |

## html_demo_bot.py

Shows all supported HTML formatting tags:

```bash
python examples/html_demo_bot.py AUTHCODE
```

```
<b>bold</b> <i>italic</i> <u>underline</u> <s>strikethrough</s>
<code>monospace</code> <pre>preformatted</pre> <h1>Heading</h1>
<a href="https://example.com">link</a>
```

## chat_admin_bot.py

Chat management commands (requires admin rights in the chat):

```bash
python examples/chat_admin_bot.py AUTHCODE
```

- `/pin <message_id>` — pins a message
- `/edit <message_id> <new_text>` — edits a message
- `/clear` — clears chat history for all
- `/clear_me` — clears chat history for yourself
- `/title <new_name>` — renames the chat
- `/info` — shows chat info (name, members, message count)
