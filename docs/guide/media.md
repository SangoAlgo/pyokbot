# Media

Send photos, videos, files, and voice messages from URLs or local files.

## Common behavior

All media methods accept a file path — either a public URL or a local file on disk. The library handles downloading and uploading automatically.

You can reply to a message by passing its ID via `repl_to_message`.

## Photos

```python
# From a URL
await bot.send_photo(chat_id, "https://example.com/photo.jpg", caption="Look at this!")

# From a local file
await bot.send_photo(chat_id, "/path/to/photo.jpg")
```

| Parameter         | Type     | Description                    |
| ----------------- | -------- | ------------------------------ |
| `chat_id`         | `str`    | Target chat ID                 |
| `photo_file_path` | `str`   | URL or local file path         |
| `caption`         | `str`    | Optional caption               |
| `repl_to_message` | `str`    | Message ID to reply to         |
| `parse_mode`      | `str`    | `"html"` for HTML in caption   |

## Videos

```python
await bot.send_video(chat_id, "https://example.com/video.mp4", caption="Great video!")
```

Same parameters as `send_photo` — URL/local path, optional caption with HTML support.

## Files

Send any document type:

```python
await bot.send_file(chat_id, "/path/to/report.pdf", title="Monthly Report")
```

| Parameter   | Type     | Description                    |
| ----------- | -------- | ------------------------------ |
| `chat_id`   | `str`    | Target chat ID                 |
| `file_path` | `str`    | URL or local file path         |
| `title`     | `str`    | Optional file name to display  |
| `repl_to_message` | `str` | Message ID to reply to    |

## Voice messages

```python
await bot.send_voice(chat_id, "https://example.com/message.ogg")
```

| Parameter          | Type     | Description                    |
| ------------------ | -------- | ------------------------------ |
| `chat_id`          | `str`    | Target chat ID                 |
| `voice_file_path`  | `str`    | URL or local file path         |
| `repl_to_message`  | `str`    | Message ID to reply to         |

## Full example

See [`examples/media_bot.py`](https://github.com/SangoAlgo/pyokbot/blob/main/examples/media_bot.py) for a working bot with `/photo`, `/video`, `/file`, and `/voice` commands.

## Notes

- Local files must exist at the path you provide.
- For large files, make sure your server has enough upload bandwidth — the file is uploaded to OK.ru's servers before sending.
