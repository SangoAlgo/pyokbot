<p align="center">
  <img src="https://placehold.co/600x200/1a1a2e/e94560?text=pyokbot&font=montserrat" alt="pyokbot" width="600">
</p>

<p align="center">
  Python library for Odnoklassniki (ok.ru) bots.<br>
  WebSocket, async, no polling.
</p>

<p align="center">
  <a href="https://pypi.org/project/pyokbot/"><img src="https://img.shields.io/pypi/v/pyokbot?style=flat-square&logo=pypi&logoColor=white&color=3776AB" alt="PyPI"></a>
  <a href="https://pypi.org/project/pyokbot/"><img src="https://img.shields.io/pypi/pyversions/pyokbot?style=flat-square&logo=python&logoColor=white&color=3776AB" alt="Python versions"></a>
  <a href="LICENSE"><img src="https://img.shields.io/pypi/l/pyokbot?style=flat-square&color=green" alt="License"></a>
  <a href="https://SangoAlgo.github.io/pyokbot"><img src="https://img.shields.io/badge/docs-mkdocs-1a73e8?style=flat-square&logo=readthedocs&logoColor=white" alt="Docs"></a>
</p>

<p align="center">
  ⚠️ Alpha — works, expect rough edges
</p>

```python
import asyncio
from pyokbot import Vanus

async def main():
    bot = Vanus("YOUR_AUTHCODE")
    await bot.run()

    @bot.on_message(commands=["ping"])
    async def ping(message):
        await bot.send_reply(message, "pong!")

    await bot.polling()

asyncio.run(main())
```

Ten lines and you have a bot that replies to /ping with pong.

Whats the deal with okru bots

OK.ru doesn't have a public API for bots. This library speaks the same WebSocket protocol their messenger uses. So messages come through instantly no HTTP polling no waiting around.

Its the only Python library for OK.ru bots. Theres nothing else like it.

How it works

You write handlers with a decorator. Tell it what to listen for.

```python
@bot.on_message(commands=["start"])
async def start(message):
    await bot.send_message(message.chat.id, "Hey Im alive")
```

Want to only catch photos from users

```python
@bot.on_message(filters="user", content_types=["photo"])
async def on_photo(message):
    await bot.send_reply(message, "Nice pic")
```

You can filter by command name text content type photo video audio file or who sent it user/bot.

Sending stuff

Photos videos files voice messages. Works with a URL or a local path.

```python
await bot.send_photo(message.chat.id, "https://example.com/cat.jpg", caption="cat")
await bot.send_video(message.chat.id, "video.mp4")
await bot.send_file(message.chat.id, "report.pdf", title="Report")
```

Messages can have bold italic code headings links. Just pass parse_mode="html".

```python
await bot.send_message(
    message.chat.id,
    "<b>bold</b> <i>italic</i> <code>code</code> <a href='https://ok.ru'>link</a>",
    parse_mode="html",
)
```

Chat stuff

Pin messages edit delete clear history change the name or photo kick people. You need admin rights for most of it.

```python
await bot.pin_chat_message(chat_id, msg_id)
await bot.edit_message_text(chat_id, msg_id, "new text")
await bot.clear_chat_history(chat_id, for_all=True)
await bot.change_chat_title(chat_id, "New Name")
```

Theres also a typing indicator so it looks like the bot is typing before it answers.

```python
await bot.writing_emulation(message.chat.id)
await asyncio.sleep(1)
await bot.send_reply(message, "done")
```

Under the hood

Persistent WebSocket so no polling. Auto reconnects if the connection drops. User info gets cached and refreshes every hour. Ctrl+C shuts it down cleanly.

Install

```bash
pip install pyokbot
```

Python 3.9 and up. You need an AUTHCODE cookie from ok.ru the docs tell you how to get it.

Examples

Ready to run bots in the examples folder

- echobot.py — echo bot with commands and media
- media_bot.py — send photos videos files voice
- filter_demo_bot.py — shows all the filter types
- html_demo_bot.py — HTML formatting demo
- chat_admin_bot.py — manage chats pin edit kick

```bash
python examples/echobot.py YOUR_AUTHCODE
```

Docs

Full docs at SangoAlgo.github.io/pyokbot

License

MIT.
