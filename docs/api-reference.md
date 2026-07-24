# API Reference

## Vanus

The main client class. All bot functionality is accessed through this class.

### Lifecycle

```python
bot = Vanus(auth_code)
await bot.run()
await bot.polling()
await bot.stop()
```

### Message filters

::: pyokbot.client.Vanus.on_message

### Message filtering logic

::: pyokbot.client.Vanus.message_filter

### Media sending

```python
await bot.send_message(chat_id, text, parse_mode=None)
await bot.send_reply(message, text, parse_mode=None)
await bot.send_photo(chat_id, photo_file_path, caption=None, repl_to_message=None, parse_mode=None)
await bot.send_video(chat_id, video_file_path, caption=None, repl_to_message=None, parse_mode=None)
await bot.send_file(chat_id, file_path, title=None, repl_to_message=None)
await bot.send_voice(chat_id, voice_file_path, repl_to_message=None)
```

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
await bot.writing_emulation(chat_id)
await bot.get_user_info(user_id)
await bot.tst_user(user_id)
await bot.socket_reconect_count()
```

## Messages

::: pyokbot.messages.Messages
    options:
      show_root_heading: true

## Ws (WebSocket)

::: pyokbot.ws.Ws
    options:
      show_root_heading: true

## Login

::: pyokbot.login.Login
    options:
      show_root_heading: true
