# Chat Admin

Manage chats when your bot has admin rights.

## What you need

Your bot must be an administrator in the chat for most of these to work. If it isn't, the call will fail silently.

## Chat info

Fetch metadata about a chat — title, members, pinned message, and more.

```python
info = await bot.get_chat_info(chat_id)
```

Returns a dict with `title`, `status`, `link`, `owner`, `members` (count + list), `messages` (count + last message), `images`, and optionally `pinned`.

## Pin a message

```python
await bot.pin_chat_message(chat_id, message_id)
```

Get the message ID from `message.id` inside any handler.

## Edit a message

```python
await bot.edit_message_text(chat_id, message_id, "New text", parse_mode="html")
```

Edit any message your bot has sent. `parse_mode` is optional.

## Delete messages

```python
# One message
await bot.delete_message(chat_id, message_id=msg_id)

# Several at once
await bot.delete_message(chat_id, message_ids=[msg1, msg2, msg3])
```

## Clear chat history

```python
# For you only
await bot.clear_chat_history(chat_id)

# For everyone
await bot.clear_chat_history(chat_id, for_all=True)
```

## Rename a chat

```python
await bot.change_chat_title(chat_id, "New Chat Name")
```

## Change the chat photo

```python
await bot.change_chat_photo(chat_id, "/path/to/new_avatar.jpg")
```

Works with both URLs and local file paths — same as [sending media](media.md).

## Remove members

```python
# One person
await bot.delete_member(chat_id, member_id=user_id)

# Several at once
await bot.delete_member(chat_id, member_ids=[user1, user2])
```

## Full example

See [`examples/chat_admin_bot.py`](https://github.com/SangoAlgo/pyokbot/blob/main/examples/chat_admin_bot.py) — a bot with `/pin`, `/edit`, `/clear`, `/title`, and `/info` commands.
