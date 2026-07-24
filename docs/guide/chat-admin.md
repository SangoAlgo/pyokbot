# Chat Admin

Manage chats when your bot has admin rights.

## Requirements

Your bot must be an administrator in the chat for most of these methods to work. If it isn't, the call will fail silently.

## Chat info

Fetch metadata about a chat:

```python
info = await bot.get_chat_info(chat_id)
```

Returns a dict with `title`, `status`, `link`, `owner`, `members` (count + list), `messages` (count + last message), `images` (small + full icon), and optionally `pinned`.

## Pinning messages

```python
await bot.pin_chat_message(chat_id, message_id)
```

The message ID is available on `message.id` inside any handler.

## Editing messages

```python
await bot.edit_message_text(chat_id, message_id, "New text", parse_mode="html")
```

Edits the text of a previously sent message. `parse_mode` is optional.

## Deleting messages

```python
# Single message
await bot.delete_message(chat_id, message_id=msg_id)

# Multiple messages
await bot.delete_message(chat_id, message_ids=[msg1, msg2, msg3])
```

## Clearing history

```python
# Clear for yourself only
await bot.clear_chat_history(chat_id)

# Clear for everyone
await bot.clear_chat_history(chat_id, for_all=True)
```

## Renaming a chat

```python
await bot.change_chat_title(chat_id, "New Chat Name")
```

## Changing the chat photo

```python
await bot.change_chat_photo(chat_id, "/path/to/new_avatar.jpg")
```

Accepts both URLs and local file paths, just like [media sending](media.md).

## Removing members

```python
# Single member
await bot.delete_member(chat_id, member_id=user_id)

# Multiple members
await bot.delete_member(chat_id, member_ids=[user1, user2])
```

## Full example

See [`examples/chat_admin_bot.py`](https://github.com/SangoAlgo/pyokbot/blob/main/examples/chat_admin_bot.py) for a bot with `/pin`, `/edit`, `/clear`, `/title`, and `/info` commands.

## Notes

- `change_chat_photo` uploads the image file, so local paths or URLs both work.
- Clearing history with `for_all=True` affects every member of the chat.
