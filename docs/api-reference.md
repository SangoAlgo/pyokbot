# API Reference

## Vanus

Main bot client. Every interaction with OK.ru goes through this class.

---

### Vanus(auth_code)

Create a new bot instance.

| Parameter    | Type   | Description                            |
| ------------ | ------ | -------------------------------------- |
| `auth_code`  | `str`  | The `AUTHCODE` cookie value from ok.ru |

The constructor validates the auth code and sets up the WebSocket connection. Nothing happens yet — call `run()` for that.

```python
bot = Vanus("YOUR_AUTHCODE")
```

---

### Lifecycle

#### `await run()`

Connect to OK.ru, authenticate via WebSocket, and fetch the bot's profile.

- Opens a persistent WebSocket connection
- Waits for authorization confirmation
- Retrieves bot profile info (available as `bot.bot_info`)
- Initializes the internal messages module

Must be called once before `polling()`.

```python
await bot.run()
print(bot.bot_info)      # bot's profile data
```

---

#### `await polling()`

Start the main event loop. Listens for incoming messages and dispatches them to registered handlers.

- Runs forever (until cancelled or an error occurs)
- Deduplicates messages by ID
- Checks handlers in registration order — first match wins
- Errors inside handlers are logged but don't crash the loop

```python
await bot.polling()
```

Each incoming message goes through:

1. **Opcode check** — only `INCOMING_MESSAGE` type is processed
2. **Parsing** — raw WebSocket data is converted into a structured message object
3. **Deduplication** — messages already handled are skipped
4. **Filter matching** — each handler's filters are checked against the message
5. **Dispatch** — the first matching handler runs

---

#### `await stop()`

Disconnect from OK.ru and clean up.

- Closes the WebSocket connection
- Cancels the polling task
- Closes the HTTP client session

```python
await bot.stop()
```

---

#### Context manager

Use `async with` instead of manual lifecycle calls:

```python
async with Vanus("AUTHCODE") as bot:
    @bot.on_message(commands=["ping"])
    async def ping(msg):
        await bot.send_reply(msg, "pong!")
    await bot.polling()
```

This calls `run()` on enter and `stop()` on exit.

---

### Handlers

#### `@bot.on_message(...)`

Decorator that registers a message handler. All parameters are optional and combine with AND logic.

```python
@bot.on_message(filters="user", commands=["start"])
async def handler(message):
    ...
```

**Parameters:**

| Parameter        | Type                  | Default  | Description                                              |
| ---------------- | --------------------- | -------- | -------------------------------------------------------- |
| `filters`        | `str` or `None`       | `"user"` | `"user"` — only from real users; `"bot"` — only from bots; `None` — both |
| `text`           | `str` or `list[str]`  | `None`   | Match exact message text. Pass a list to match any of several texts |
| `content_types`  | `list[str]`           | `None`   | Filter by media type. See table below                    |
| `commands`       | `list[str]`           | `None`   | Match commands by name — `"start"` matches `/start`      |

**`content_types` values:**

| Value        | Matches                          |
| ------------ | -------------------------------- |
| `"photo"`    | Messages containing photos       |
| `"video"`    | Messages containing a video      |
| `"audio"`    | Voice messages                   |
| `"document"` | File attachments                 |
| `"text"`     | Plain text — no media            |
| `"commands"` | Any message starting with `/`    |

**Handler order:** Handlers run in the order you register them. The first match wins — remaining handlers are skipped.

```python
@bot.on_message(commands=["start"])   # checked first
@bot.on_message(commands=["help"])    # checked second
@bot.on_message(filters="user")       # catch-all, checked last
```

---

### Sending Messages

#### `await send_message(chat_id, message_text, parse_mode=None)`

Send a text message to a chat.

| Parameter      | Type   | Description                                |
| -------------- | ------ | ------------------------------------------ |
| `chat_id`      | `str`  | Target chat ID                             |
| `message_text` | `str`  | Message body                               |
| `parse_mode`   | `str`  | Set to `"html"` to enable HTML formatting  |

```python
await bot.send_message("12345", "Hello!")
await bot.send_message("12345", "<b>Bold</b> text", parse_mode="html")
```

---

#### `await send_reply(message, message_text, parse_mode=None, reply_to_repl=False)`

Reply to an incoming message.

| Parameter       | Type    | Description                                              |
| --------------- | ------- | -------------------------------------------------------- |
| `message`       | `dict`  | The message object received in a handler                 |
| `message_text`  | `str`   | Reply body                                               |
| `parse_mode`    | `str`   | Set to `"html"` for HTML formatting                      |
| `reply_to_repl` | `bool`  | If `True`, reply to the original message in a reply chain|

```python
@bot.on_message(filters="user")
async def handler(msg):
    await bot.send_reply(msg, "I got your message!")
    await bot.send_reply(msg, "HTML reply", parse_mode="html")
```

---

### Sending Media

#### `await send_photo(chat_id, photo_file_path, caption=None, repl_to_message=None, parse_mode=None)`

Send a photo. Returns the sent message data.

| Parameter          | Type     | Description                                |
| ------------------ | -------- | ------------------------------------------ |
| `chat_id`          | `str`    | Target chat ID                             |
| `photo_file_path`  | `str`    | URL or local file path                     |
| `caption`          | `str`    | Optional caption text                      |
| `repl_to_message`  | `str`    | Message ID to reply to                     |
| `parse_mode`       | `str`    | `"html"` for HTML in caption               |

```python
await bot.send_photo(chat_id, "https://example.com/photo.jpg")
await bot.send_photo(chat_id, "/local/photo.png", caption="<b>Look!</b>", parse_mode="html")
```

---

#### `await send_video(chat_id, video_file_path, caption=None, repl_to_message=None, parse_mode=None)`

Send a video.

| Parameter          | Type     | Description                                |
| ------------------ | -------- | ------------------------------------------ |
| `chat_id`          | `str`    | Target chat ID                             |
| `video_file_path`  | `str`    | URL or local file path                     |
| `caption`          | `str`    | Optional caption text                      |
| `repl_to_message`  | `str`    | Message ID to reply to                     |
| `parse_mode`       | `str`    | `"html"` for HTML in caption               |

```python
await bot.send_video(chat_id, "https://example.com/video.mp4")
```

---

#### `await send_file(chat_id, file_path, title=None, repl_to_message=None)`

Send any file type — PDF, ZIP, whatever.

| Parameter         | Type     | Description                                |
| ----------------- | -------- | ------------------------------------------ |
| `chat_id`         | `str`    | Target chat ID                             |
| `file_path`       | `str`    | URL or local file path                     |
| `title`           | `str`    | Optional display name for the file         |
| `repl_to_message` | `str`    | Message ID to reply to                     |

```python
await bot.send_file(chat_id, "/path/to/report.pdf", title="Monthly Report")
```

---

#### `await send_voice(chat_id, voice_file_path, repl_to_message=None)`

Send a voice message.

| Parameter          | Type     | Description                                |
| ------------------ | -------- | ------------------------------------------ |
| `chat_id`          | `str`    | Target chat ID                             |
| `voice_file_path`  | `str`    | URL or local file path                     |
| `repl_to_message`  | `str`    | Message ID to reply to                     |

```python
await bot.send_voice(chat_id, "/path/to/message.ogg")
```

---

### Chat Management

Requires admin rights in the target chat.

#### `await get_chat_info(chat_id)`

Fetch detailed chat metadata.

| Parameter | Type   | Description    |
| --------- | ------ | -------------- |
| `chat_id` | `str`  | Target chat ID |

Returns a dict with:

| Field              | Type              | Description                         |
| ------------------ | ----------------- | ----------------------------------- |
| `chat_id`          | `str`             | Chat ID                             |
| `title`            | `str`             | Chat name                           |
| `status`           | `str`             | Chat status                         |
| `link`             | `str`             | Invite link                         |
| `created_time`     | `str`             | Creation timestamp                  |
| `owner`            | `str`             | Owner user ID or `"unavailable"`    |
| `images`           | `dict`            | `small` and `full` icon URLs        |
| `members`          | `dict`            | `count` (int) and `list` (user IDs) |
| `messages`         | `dict`            | `count` and `last` (message data)   |
| `pinned`           | `dict` or absent  | Pinned message (id, text, sender_id)|

```python
info = await bot.get_chat_info(chat_id)
print(info["title"], info["members"]["count"])
```

---

#### `await change_chat_title(chat_id, title)`

Rename a chat.

| Parameter | Type   | Description       |
| --------- | ------ | ----------------- |
| `chat_id` | `str`  | Target chat ID    |
| `title`   | `str`  | New chat name     |

```python
await bot.change_chat_title(chat_id, "New Name")
```

---

#### `await change_chat_photo(chat_id, photo_file_path)`

Change the chat's avatar.

| Parameter          | Type     | Description                |
| ------------------ | -------- | -------------------------- |
| `chat_id`          | `str`    | Target chat ID             |
| `photo_file_path`  | `str`    | URL or local file path     |

```python
await bot.change_chat_photo(chat_id, "/path/to/avatar.jpg")
```

---

#### `await delete_member(chat_id, member_ids=None, member_id=None)`

Remove one or more members from a chat.

| Parameter    | Type          | Description                  |
| ------------ | ------------- | ---------------------------- |
| `chat_id`    | `str`         | Target chat ID               |
| `member_ids` | `list[str]`   | List of user IDs to remove   |
| `member_id`  | `str`         | Single user ID to remove     |

Use either `member_id` for one user or `member_ids` for several.

```python
await bot.delete_member(chat_id, member_id="12345")
await bot.delete_member(chat_id, member_ids=["123", "456"])
```

---

#### `await delete_message(chat_id, message_ids=None, message_id=None)`

Delete one or more messages.

| Parameter     | Type          | Description                      |
| ------------- | ------------- | -------------------------------- |
| `chat_id`     | `str`         | Target chat ID                   |
| `message_ids` | `list[str]`   | List of message IDs to delete    |
| `message_id`  | `str`         | Single message ID to delete      |

```python
await bot.delete_message(chat_id, message_id="msg_001")
await bot.delete_message(chat_id, message_ids=["msg_001", "msg_002"])
```

---

#### `await clear_chat_history(chat_id, for_all=None)`

Clear message history in a chat.

| Parameter | Type    | Description                                        |
| --------- | ------- | -------------------------------------------------- |
| `chat_id` | `str`   | Target chat ID                                     |
| `for_all` | `bool`  | `True` — clear for everyone; `False` — clear for bot only; `None` — bot only |

```python
await bot.clear_chat_history(chat_id)              # clear for bot only
await bot.clear_chat_history(chat_id, for_all=True) # clear for everyone
```

---

#### `await edit_message_text(chat_id, message_id, message_text, parse_mode=None)`

Edit a previously sent message.

| Parameter      | Type    | Description                                |
| -------------- | ------- | ------------------------------------------ |
| `chat_id`      | `str`   | Target chat ID                             |
| `message_id`   | `str`   | ID of the message to edit                  |
| `message_text` | `str`   | New text                                   |
| `parse_mode`   | `str`   | `"html"` for HTML formatting               |

```python
await bot.edit_message_text(chat_id, "msg_001", "Updated text")
await bot.edit_message_text(chat_id, "msg_001", "<b>Updated</b>", parse_mode="html")
```

---

#### `await pin_chat_message(chat_id, message_id)`

Pin a message in a chat.

| Parameter    | Type    | Description              |
| ------------ | ------- | ------------------------ |
| `chat_id`    | `str`   | Target chat ID           |
| `message_id` | `str`   | ID of the message to pin |

Message IDs are available from `message.id` inside handlers.

```python
await bot.pin_chat_message(chat_id, message_id)
```

---

### Utilities

#### `await writing_emulation(chat_id)`

Show a "bot is typing..." indicator in a chat. Lasts about 5 seconds and clears on its own.

| Parameter | Type   | Description       |
| --------- | ------ | ----------------- |
| `chat_id` | `str`  | Target chat ID    |

Call this before sending a reply to signal the bot is working:

```python
await bot.writing_emulation(message.chat.id)
await asyncio.sleep(0.5)
await bot.send_reply(message, "Done!")
```

---

#### `await get_user_info(user_id)`

Fetch a user's profile. Results are cached for an hour to avoid repeated lookups.

| Parameter | Type   | Description        |
| --------- | ------ | ------------------ |
| `user_id` | `str`  | OK.ru user ID      |

Returns a dict with:

| Field             | Type     | Description                         |
| ----------------- | -------- | ----------------------------------- |
| `id`              | `str`    | User ID                             |
| `name`            | `str`    | Display name                        |
| `avatar_url`      | `str`    | Profile photo URL                   |
| `last_visit`      | `str`    | Last visit description              |
| `last_update_time`| `str`    | Timestamp of last cache update      |

The cache lives in `~/.pyokbot_cache.json` and persists across restarts.

```python
info = await bot.get_user_info("12345")
print(info["name"], info["avatar_url"])
```

---

#### `await tst_user(user_id)`

Check if a user is currently logged in to OK.ru.

| Parameter | Type   | Description        |
| --------- | ------ | ------------------ |
| `user_id` | `str`  | OK.ru user ID      |

Returns a dict (may be empty depending on endpoint availability).

```python
status = await bot.tst_user("12345")
```

---

#### `await socket_reconect_count()`

Return the total number of WebSocket reconnections this session.

```python
count = await bot.socket_reconect_count()
print(f"Reconnected {count} times")
```

Useful for monitoring connection stability.
