# HTML Formatting

Add bold, italic, links, headings, and code blocks to your messages.

## Supported tags

| Tag | Effect |
|-----|--------|
| `<b>text</b>` | **Bold** |
| `<i>text</i>` | *Italic* |
| `<u>text</u>` | Underline |
| `<s>text</s>` | ~~Strikethrough~~ |
| `<code>text</code>` | `Monospace` (inline) |
| `<pre>text</pre>` | Preformatted block |
| `<h1>text</h1>` | Heading |
| `<a href="url">text</a>` | Clickable link |

## How to use it

Pass `parse_mode="html"` to any method that sends text:

```python
await bot.send_message(
    chat_id,
    "<b>bold</b> <i>italic</i> <a href='https://ok.ru'>link</a>",
    parse_mode="html"
)
```

HTML works in replies and captions too:

```python
await bot.send_reply(message, "<b>bold reply</b>", parse_mode="html")
await bot.send_photo(chat_id, url, caption="<i>caption</i>", parse_mode="html")
```

## Full example

```python
@bot.on_message(commands=["html"])
async def cmd_html(message):
    text = """
<b>Bold</b>
<i>Italic</i>
<u>Underline</u>
<s>Strikethrough</s>
<code>inline code</code>
<pre>preformatted
block</pre>
<h1>Heading</h1>
<a href="https://ok.ru">OK.ru</a>
    """
    await bot.send_reply(message, text.strip(), parse_mode="html")
```

See [`examples/html_demo_bot.py`](https://github.com/SangoAlgo/pyokbot/blob/main/examples/html_demo_bot.py) for a live demo.

## Under the hood

pyokbot uses `sulguk` to convert your HTML into OK.ru's entity format. `<b>` becomes `STRONG`, `<i>` becomes `EMPHASIZED`, `<a>` becomes `LINK`, and so on.

## Notes

- Tags must be properly closed. Unclosed tags get ignored.
- `parse_mode` defaults to `None` (plain text). You have to set it to `"html"` explicitly.
- You can nest tags: `<b><i>bold italic</i></b>` works fine.
