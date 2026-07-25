# Media

Send photos, videos, files, and voice messages. You can use a URL or a local file path — the library handles downloading and uploading.

## Common behavior

All media methods accept a file path. It can be a URL (`https://...`) or a path on disk (`/path/to/file.jpg`). You can reply to a message by passing its ID via `repl_to_message`.

## Photos

```python
# From a URL
await bot.send_photo(chat_id, "https://example.com/photo.jpg", caption="Look at this!")

# From a local file
await bot.send_photo(chat_id, "/path/to/photo.jpg")
```

| Parameter         | Type   | Description                        |
|-------------------|--------|------------------------------------|
| `chat_id`         | `str`  | Target chat ID                     |
| `photo_file_path` | `str`  | URL or local file path             |
| `caption`         | `str`  | Optional caption                   |
| `repl_to_message` | `str`  | Message ID to reply to             |
| `parse_mode`      | `str`  | `"html"` for HTML in the caption   |

## Videos

Same parameters as `send_photo`. URL or local path, optional caption with HTML support.

```python
await bot.send_video(chat_id, "https://example.com/video.mp4", caption="Great video!")
```

## Files

Send any document type — PDFs, ZIPs, whatever you need.

```python
await bot.send_file(chat_id, "/path/to/report.pdf", title="Monthly Report")
```

| Parameter         | Type   | Description                        |
|-------------------|--------|------------------------------------|
| `chat_id`         | `str`  | Target chat ID                     |
| `file_path`       | `str`  | URL or local file path             |
| `title`           | `str`  | Optional display name              |
| `repl_to_message` | `str`  | Message ID to reply to             |

## Voice messages

```python
await bot.send_voice(chat_id, "https://example.com/message.ogg")
```

| Parameter          | Type   | Description                        |
|--------------------|--------|------------------------------------|
| `chat_id`          | `str`  | Target chat ID                     |
| `voice_file_path`  | `str`  | URL or local file path             |
| `repl_to_message`  | `str`  | Message ID to reply to             |

## Full example

See [`examples/media_bot.py`](https://github.com/SangoAlgo/pyokbot/blob/main/examples/media_bot.py) — a working bot with `/photo`, `/video`, `/file`, and `/voice` commands.

## One thing to keep in mind

Local files must exist at the path you provide. For large files, make sure your server has enough upload bandwidth — the file gets uploaded to OK.ru's servers before it's sent.
