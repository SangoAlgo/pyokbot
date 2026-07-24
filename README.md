<!-- markdownlint-disable-file -->
<div align="center">

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

### Минимальный пример

```python
import asyncio
from pyokbot import Vanus

async def main():
    # Создаём бота с вашим AUTHCODE
    bot = Vanus("YOUR_AUTHCODE")
    await bot.run()

    @bot.on_message(commands=["ping"])
    async def ping(message):
        await bot.send_reply(message, "pong!")

    @bot.on_message(commands=["help"])
    async def cmd_help(message):
        text = """
        Доступные команды:
        /start  — приветствие
        /help   — этот текст
        /ping   — проверка
        /stop   — остановить бота
        """
        await bot.send_message(message.chat.id, text)

    # Обработчик всех текстовых сообщений
    @bot.on_message(filters="user", content_types=["text"])
    async def echo(message):
        await bot.send_reply(message, f"Ты написал: {message.text}")

    # Запускаем polling (слушаем сообщения)
    await bot.polling()

if __name__ == "__main__":
    asyncio.run(main())
```

**Запуск:**
```bash
python bot.py YOUR_AUTHCODE
```

---

## 📚 Примеры

### 🖼️ Отправка фото с подписью

```python
@bot.on_message(commands=["photo"])
async def send_photo_cmd(message):
    await bot.send_photo(
        message.chat.id,
        photo_file_path="path/to/photo.jpg",
        caption="<b>Вот ваше фото!</b>",
        parse_mode="html"
    )
```

### 🎬 Отправка видео

```python
@bot.on_message(commands=["video"])
async def send_video_cmd(message):
    await bot.send_video(
        message.chat.id,
        video_file_path="path/to/video.mp4",
        caption="Смотри видео!"
    )
```

### 🎙️ Отправка голосового сообщения

```python
@bot.on_message(commands=["voice"])
async def send_voice_cmd(message):
    await bot.send_voice(
        message.chat.id,
        voice_file_path="path/to/audio.mp3"
    )
```

### 🏷️ HTML-форматирование

```python
@bot.on_message(commands=["format"])
async def formatted_message(message):
    html_text = """
    <b>Жирный текст</b>
    <i>Курсив</i>
    <code>моноширинный</code>
    <a href="https://ok.ru">Ссылка</a>
    <h1>Заголовок</h1>
    """
    await bot.send_message(
        message.chat.id,
        html_text,
        parse_mode="html"
    )
```

### 🎯 Фильтры по типам контента

```python
# Только фото
@bot.on_message(filters="user", content_types=["photo"])
async def handle_photo(message):
    count = len(message.photo)
    await bot.send_reply(message, f"📸 Получено {count} фото")

# Только видео
@bot.on_message(filters="user", content_types=["video"])
async def handle_video(message):
    await bot.send_reply(message, "🎬 Получено видео")

# Только голос
@bot.on_message(filters="user", content_types=["audio"])
async def handle_audio(message):
    await bot.send_reply(message, "🎙️ Получено голосовое сообщение")
```

### 👥 Управление чатом

```python
@bot.on_message(commands=["chatinfo"])
async def get_chat_info(message):
    info = await bot.get_chat_info(message.chat.id)
    text = f"""
    📌 <b>Информация о чате:</b>
    
    Название: {info['title']}
    Участников: {info['members']['count']}
    Сообщений: {info['messages']['count']}
    """
    await bot.send_message(message.chat.id, text, parse_mode="html")

# Пин-сообщение
@bot.on_message(commands=["pin"])
async def pin_message(message):
    await bot.pin_chat_message(message.chat.id, message.id)
    await bot.send_reply(message, "📌 Сообщение закреплено")

# Редактировать сообщение
@bot.on_message(commands=["edit"])
async def edit_msg(message):
    await bot.edit_message_text(
        message.chat.id,
        message.id,
        "✏️ <i>Отредактированное сообщение</i>",
        parse_mode="html"
    )
```

### 👤 Информация о пользователе

```python
@bot.on_message(commands=["whoami"])
async def who_am_i(message):
    user_info = await bot.get_user_info(message.user.id)
    text = f"""
    👤 <b>Ваш профиль:</b>
    
    Имя: {user_info['name']}
    ID: {user_info['id']}
    Статус: {user_info['last_visit']}
    Аватар: {user_info['avatar_url']}
    """
    await bot.send_message(message.chat.id, text, parse_mode="html")
```

### ⌨️ Эмуляция печатания

```python
@bot.on_message(commands=["wait"])
async def typing_effect(message):
    chat_id = message.chat.id
    
    # Показываем "печатает..."
    await bot.writing_emulation(chat_id)
    
    # Имитируем обработку
    await asyncio.sleep(2)
    
    await bot.send_message(chat_id, "✅ Готово!")
```

### 🔄 Контекстный менеджер

```python
# Автоматически вызовет bot.run() и bot.stop()
async def main():
    async with Vanus("YOUR_AUTHCODE") as bot:
        @bot.on_message(filters="user")
        async def handler(message):
            await bot.send_reply(message, message.text)
        
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
export OK_AUTHCODE="ваш_authcode"
```

```python
import os
bot = Vanus(os.getenv("OK_AUTHCODE"))
```

Docs

Full docs at SangoAlgo.github.io/pyokbot

License

MIT.
