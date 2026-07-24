# API Reference

## Vanus

The main client. Everything goes through this class.

### Lifecycle

```python
bot = Vanus(auth_code)
await bot.run()        # connect to OK.ru, get bot info
await bot.polling()    # start listening for messages
await bot.stop()       # disconnect and clean up
```

Or use it as a context manager:

```python
async with Vanus(auth_code) as bot:
    @bot.on_message(commands=["ping"])
    async def ping(message):
        await bot.send_reply(message, "pong!")
    await bot.polling()
```

### Registering handlers

```python
@bot.on_message(filters="user", text="hello", content_types=["photo"], commands=["start"])
```

All parameters are optional. If you pass more than one, they're combined with AND — all must match.

- `filters` — `"user"` or `"bot"`. `None` means both.
- `text` — exact text to match, or a list of strings.
- `content_types` — list: `"photo"`, `"video"`, `"audio"`, `"document"`, `"text"`, `"commands"`.
- `commands` — list of command names. `"start"` matches `/start`.

### Sending messages

```python
await bot.send_message(chat_id, text, parse_mode=None)
await bot.send_reply(message, text, parse_mode=None, reply_to_repl=False)
```

`parse_mode="html"` enables HTML formatting.

### Sending media

```python
await bot.send_photo(chat_id, photo_file_path, caption=None, repl_to_message=None, parse_mode=None)
await bot.send_video(chat_id, video_file_path, caption=None, repl_to_message=None, parse_mode=None)
await bot.send_file(chat_id, file_path, title=None, repl_to_message=None)
await bot.send_voice(chat_id, voice_file_path, repl_to_message=None)
```

`photo_file_path` / `video_file_path` / `file_path` can be a URL or a local file path.

### Chat management

```python
await bot.get_chat_info(chat_id)
await bot.change_chat_title(chat_id, title)
await bot.change_chat_photo(chat_id, photo_file_path)
await bot.delete_member(chat_id, member_id=...)
await bot.delete_message(chat_id, message_id=...)
await bot.clear_chat_history(chat_id, for_all=False)
await bot.edit_message_text(chat_id, message_id, text, parse_mode=None)
await bot.pin_chat_message(chat_id, message_id)
```

### Utilities

```python
await bot.writing_emulation(chat_id)    # shows "typing..." indicator
await bot.get_user_info(user_id)         # cached user profile
await bot.tst_user(user_id)              # check if user is logged in
await bot.socket_reconect_count()        # how many times WS reconnected
```

## Messages

All methods for parsing, formatting, uploading and sending data.

::: pyokbot.messages.Messages
    options:
      show_root_heading: true

## Ws (WebSocket)

Connection management — connect, reconnect, ping, message queues.

::: pyokbot.ws.Ws
    options:
      show_root_heading: true

## Login

Authentication and session handling.

::: pyokbot.login.Login
    options:
      show_root_heading: true
