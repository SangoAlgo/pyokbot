# Examples

All examples live in the [`examples/`](https://github.com/SangoAlgo/pyokbot/tree/main/examples) directory.

## echobot.py

A classic echo bot.

```bash
python examples/echobot.py AUTHCODE
```

- `/start` — welcome message
- `/help` — list of commands
- `/info` — your name, ID, status
- `/ping` — bot replies `pong!`
- `/stop` — shuts the bot down
- Sends photos, videos, audio back with captions
- Echoes any text message

## media_bot.py

Sending different types of media.

```bash
python examples/media_bot.py AUTHCODE
```

- `/photo` — send a photo from URL
- `/video` — send a video file
- `/file` — send a PDF document
- `/voice` — send a voice message

## filter_demo_bot.py

Every filter type in one bot.

```bash
python examples/filter_demo_bot.py AUTHCODE
```

- `commands=["start"]` — `/start`
- `text="hello"` — exact match
- `text=["hi", "hey"]` — any of the listed
- `content_types=["photo"]` — photo messages
- `content_types=["video"]` — video messages
- `content_types=["audio"]` — voice messages
- `content_types=["document"]` — file messages
- `filters="user"` — catch-all fallback

## html_demo_bot.py

All supported HTML tags.

```bash
python examples/html_demo_bot.py AUTHCODE
```

```
<b>bold</b> <i>italic</i> <u>underline</u> <s>strikethrough</s>
<code>monospace</code> <pre>preformatted</pre> <h1>Heading</h1>
<a href="https://example.com">link</a>
```

## chat_admin_bot.py

Chat management commands (you need admin rights in the chat).

```bash
python examples/chat_admin_bot.py AUTHCODE
```

- `/pin <message_id>` — pin a message
- `/edit <id> <new text>` — edit a message
- `/clear` — clear history for everyone
- `/clear_me` — clear history for yourself
- `/title <new name>` — rename the chat
- `/info` — chat info (name, members, message count)
