# Examples

All examples live in the [`examples/`](https://github.com/SangoAlgo/pyokbot/tree/main/examples) directory. Run any of them with your AUTHCODE:

```bash
python examples/echobot.py YOUR_AUTHCODE
```

## echobot.py

A classic echo bot. Commands, media replies, catch-all echo.

- `/start` — welcome message
- `/help` — command list
- `/info` — your name, ID, status
- `/ping` — bot replies `pong!`
- `/stop` — shuts the bot down
- Sends photos, videos, audio back with captions
- Echoes any text message

## media_bot.py

Send different types of media on command.

- `/photo` — send a photo from URL
- `/video` — send a video file
- `/file` — send a PDF document
- `/voice` — send a voice message

## filter_demo_bot.py

Every filter type in action — shows how to combine filters and what matches.

- `commands=["start"]` — `/start`
- `text="hello"` — exact match
- `text=["hi", "hey"]` — any of the listed
- `content_types=["photo"]` — photo messages
- `content_types=["video"]` — video messages
- `content_types=["audio"]` — voice messages
- `content_types=["document"]` — file messages
- `filters="user"` — catch-all fallback

## html_demo_bot.py

All supported HTML tags in one bot.

```
<b>bold</b> <i>italic</i> <u>underline</u> <s>strikethrough</s>
<code>monospace</code> <pre>preformatted</pre> <h1>Heading</h1>
<a href="https://example.com">link</a>
```

## chat_admin_bot.py

Chat management commands. You'll need admin rights in the chat for these to work.

- `/pin <message_id>` — pin a message
- `/edit <id> <new text>` — edit a message
- `/clear` — clear history for everyone
- `/clear_me` — clear history for yourself
- `/title <new name>` — rename the chat
- `/info` — chat info (name, members, message count)
