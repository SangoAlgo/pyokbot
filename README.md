<p align="center">
  <img src="https://placehold.co/600x200/EE8208/FFFFFF?text=pyokbot&font=montserrat" alt="pyokbot" width="600">
</p>

<p align="center">
  <em>Python library for Odnoklassniki (ok.ru) bots</em>
</p>

<p align="center">
  <a href="https://pypi.org/project/pyokbot/"><img src="https://img.shields.io/pypi/v/pyokbot?style=flat-square&logo=pypi&logoColor=white&color=3776AB" alt="PyPI"></a>
  <a href="https://pypi.org/project/pyokbot/"><img src="https://img.shields.io/pypi/pyversions/pyokbot?style=flat-square&logo=python&logoColor=white&color=3776AB" alt="Python"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License"></a>
  <a href="https://github.com/SangoAlgo/pyokbot/actions"><img src="https://img.shields.io/github/actions/workflow/status/SangoAlgo/pyokbot/ci.yml?style=flat-square&logo=github" alt="CI"></a>
  <a href="https://SangoAlgo.github.io/pyokbot"><img src="https://img.shields.io/badge/docs-mkdocs-1a73e8?style=flat-square&logo=readthedocs&logoColor=white" alt="Docs"></a>
</p>

---

## 📦 What is pyokbot?

**pyokbot** is the only Python library for building bots in Odnoklassniki (ok.ru). You just write handlers and send messages.

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

> A bot that replies to `/ping` with `pong!` in ~10 lines of code.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| ⚡ **Real-time** | Messages arrive as soon as they're sent |
| 🔧 **Commands** | `@bot.on_message(commands=["start"])` handles `/start` |
| 🎯 **Filters** | Route by content type, text, or sender (user/bot) |
| 👤 **User Profiles** | Auto-resolved `message.user.name`, avatar, gender; batch queries in ~120ms |
| 🖼️ **Media** | Send photos, videos, files, voice messages |
| 📝 **HTML** | Bold, italic, code, headings, links with `parse_mode="html"` |
| 👥 **Chat admin** | Pin, edit, delete, clear, change title/photo, kick, join/leave |
| 👍 **Reactions** | Set, remove, list reactions & `@bot.on_reaction()` listener |
| 🎬 **Animations** | Telegram userbot style text animations (typewriter, progress bars) |
| 🛡️ **Flood control** | Automatic detection, backoff & retry on OK.ru rate limits |
| 🔔 **Events** | Typing indicators, read receipts, presence & raw opcode listeners |
| ⌨️ **Typing** | Show "bot is typing..." before responding |
| 🔁 **Auto-reconnect** | Reconnects when connection drops (with raw PING keepalive) |
| 💾 **Cache** | User profiles cached with 1-hour TTL |
| 🧹 **Clean shutdown** | Ctrl+C handled gracefully |

---

## 🚀 Quick start

### Install

```bash
pip install pyokbot
```

Python 3.9+. You need an `AUTHCODE` cookie from ok.ru - [see the docs](https://SangoAlgo.github.io/pyokbot/installation/) for how to get one.

### Echo bot

```python
import asyncio
from pyokbot import Vanus

async def main():
    bot = Vanus("YOUR_AUTHCODE")
    await bot.run()

    @bot.on_message(filters="user")
    async def echo(message):
        await bot.send_reply(message, f"You said: {message.text}")

    await bot.polling()

asyncio.run(main())
```

```bash
python bot.py
```

---

## 🎮 What it can do

<details>
<summary><b>📋 Commands</b> - trigger on /start, /help, etc.</summary>

```python
@bot.on_message(commands=["start"])
async def start(message):
    await bot.send_message(message.chat.id, "Welcome!")

@bot.on_message(commands=["help"])
async def help(message):
    await bot.send_message(message.chat.id, "Available: /start, /help, /ping")
```
</details>

<details>
<summary><b>🎯 Filters</b> - route by content type or text</summary>

```python
@bot.on_message(filters="user", content_types=["photo"])
async def on_photo(message):
    await bot.send_reply(message, "Nice pic!")

@bot.on_message(filters="user", text="hello")
async def on_hello(message):
    await bot.send_reply(message, "Hi there!")
```
</details>

<details>
<summary><b>🖼️ Media</b> - send photos, videos, files, voice</summary>

```python
await bot.send_photo(message.chat.id, "https://example.com/cat.jpg", caption="cat")
await bot.send_video(message.chat.id, "video.mp4")
await bot.send_file(message.chat.id, "report.pdf", title="Report")
await bot.send_voice(message.chat.id, "message.ogg")
```
</details>

<details>
<summary><b>📝 HTML formatting</b> - bold, italic, code, links</summary>

```python
await bot.send_message(
    message.chat.id,
    "<b>bold</b> <i>italic</i> <code>code</code> <a href='https://ok.ru'>link</a>",
    parse_mode="html",
)
```
</details>

<details>
<summary><b>👥 Chat management</b> - pin, edit, kick, clear</summary>

```python
await bot.pin_chat_message(chat_id, msg_id)
await bot.edit_message_text(chat_id, msg_id, "new text")
await bot.clear_chat_history(chat_id, for_all=True)
await bot.change_chat_title(chat_id, "New Name")
await bot.delete_member(chat_id, member_id="12345")
```
</details>

<details>
<summary><b>⌨️ Typing indicator</b> - "bot is typing..."</summary>

```python
await bot.writing_emulation(message.chat.id)
await asyncio.sleep(1)
await bot.send_reply(message, "done!")
```
</details>

<details>
<summary><b>👍 Reactions</b> - emoji reactions on messages</summary>

```python
# Set or remove reactions
await bot.set_reaction(chat_id, message_id, reaction="🔥")
await bot.remove_reaction(chat_id, message_id)

# Fetch reactions
reactions = await bot.get_reactions(chat_id, [message_id])

# Listen for incoming reaction events
@bot.on_reaction()
async def handle_reaction(event):
    print(f"User {event.userId} reacted {event.reaction} to {event.messageId}")
```
</details>

<details>
<summary><b>🎬 Animations (Telegram Userbot Style)</b> - typewriter & progress bars</summary>

```python
# Typewriter effect
await bot.animate_typewriter(
    chat_id=message.chat.id,
    message_id=msg_id,
    text="Hello from pyokbot!",
    interval=0.2,
    step=2,
    cursor="▌",
)

# Animated progress bar
await bot.animate_progress(
    chat_id=message.chat.id,
    message_id=msg_id,
    total_steps=10,
    interval=0.4,
    prefix="Processing: ",
    filled_char="🟩",
    empty_char="▫️",
)
```
</details>

<details>
<summary><b>🔔 Real-Time Events</b> - typing, read receipts, presence</summary>

```python
@bot.on_typing()
async def on_typing(event):
    print(f"User {event.userId} is typing in {event.chatId}...")

@bot.on_read()
async def on_read(event):
    print(f"Message read receipt: {event}")

@bot.on_presence()
async def on_presence(event):
    print(f"User {event.userId} presence changed: {event.presence}")
```
</details>

<details>
<summary><b>👤 User Profiles & Auto-Resolution</b> - instant names, avatars, gender & batch queries</summary>

```python
# Automatic name & avatar on incoming messages (Telegram style)
@bot.on_message()
async def handle_message(message):
    print(f"{message.user.name} ({message.user.gender}): {message.text}")
    print(f"Avatar: {message.user.avatar}")

# Query single user profile via WebSocket (~120ms)
user = await bot.get_user_info(user_id, with_presence=True)
print(user["name"], user["online"], user["seen"])

# Batch query multiple users in a single request (~150ms)
users = await bot.get_users_info([user1, user2, user3])

# Get real-time presence or profile photos
presence = await bot.get_user_presence(user_id)
photos = await bot.get_user_photos(user_id)
```
</details>

---

## 🧠 How handlers work

Handlers are checked in **registration order**. The first match wins.

```python
@bot.on_message(commands=["start"])    # checked first
@bot.on_message(commands=["help"])     # checked second
@bot.on_message(filters="user")        # catch-all, checked last
```

The message object has attribute-style access:

| Field | Type | Description |
|-------|------|-------------|
| `message.text` | `str` | Text content |
| `message.chat.id` | `str` | Chat ID |
| `message.user.id` | `str` | Sender ID |
| `message.id` | `str` | Message ID |
| `message.photo` | `list` | Photo attachments |
| `message.video` | `list` | Video attachments |
| `message.audio` | `dict` | Voice attachment |
| `message.document` | `dict` | File attachment |
| `message.is_reply` | `bool` | Is this a reply? |
| `message.reply` | `dict` | Replied-to message |

---

## 🔧 Examples

Ready-to-run bots in the [`examples/`](examples/) directory:

| Bot | What it does |
|-----|-------------|
| [`echobot.py`](examples/echobot.py) | Echo commands, photos, videos, text |
| [`media_bot.py`](examples/media_bot.py) | Send photos, videos, files, voice |
| [`filter_demo_bot.py`](examples/filter_demo_bot.py) | All filter types (commands, text, content-type) |
| [`html_demo_bot.py`](examples/html_demo_bot.py) | HTML formatting with all tags |
| [`chat_admin_bot.py`](examples/chat_admin_bot.py) | Pin, edit, clear, kick, change title |
| [`animation_bot.py`](examples/animation_bot.py) | Telegram-style typewriter, progress bar & spinner animations |

```bash
python examples/echobot.py YOUR_AUTHCODE
```

---

## 📚 Documentation

Full docs: **[SangoAlgo.github.io/pyokbot](https://SangoAlgo.github.io/pyokbot)**

- [Installation guide](https://SangoAlgo.github.io/pyokbot/installation/)
- [Quick start](https://SangoAlgo.github.io/pyokbot/quickstart/)
- [API reference](https://SangoAlgo.github.io/pyokbot/api-reference/)
- [Examples](https://SangoAlgo.github.io/pyokbot/examples/)
- [FAQ](https://SangoAlgo.github.io/pyokbot/faq/)

---

## 📄 License

MIT - see [LICENSE](LICENSE).
