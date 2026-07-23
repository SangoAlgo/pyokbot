# pyokbot

**pyokbot** — асинхронная Python-библиотека для создания ботов в мессенджере **Одноклассники (ok.ru)**. Работает через WebSocket (неофициальный протокол).

## Особенности

- Полностью асинхронная (`asyncio`)
- WebSocket-соединение с сервером сообщений OK
- Отправка текста, фото, видео, файлов, голосовых сообщений
- HTML-форматирование сообщений
- Система фильтров и декоратор `@bot.on_message()`
- Управление чатами (название, фото, закрепление, очистка)
- Кэширование информации о пользователях
- Автоматическое переподключение при обрыве

## Установка

```bash
pip install pyokbot
```

## Быстрый старт

```python
import asyncio
from pyokbot import Vanus

async def main():
    bot = Vanus("ВАШ_AUTHCODE")
    await bot.run()

    @bot.on_message(filters="user")
    async def handle_message(message):
        await bot.send_message(message.chat.id, f"Вы написали: {message.text}")

    await bot.polling()

asyncio.run(main())
```

## Примеры

```bash
# Базовый эхо-бот с командами
python examples/echobot.py ВАШ_AUTHCODE

# Отправка медиа (фото, видео, файлы, голос)
python examples/media_bot.py ВАШ_AUTHCODE

# Управление чатом (пин, редактирование, очистка)
python examples/chat_admin_bot.py ВАШ_AUTHCODE

# Демонстрация системы фильтров
python examples/filter_demo_bot.py ВАШ_AUTHCODE

# HTML-форматирование сообщений
python examples/html_demo_bot.py ВАШ_AUTHCODE
```

## Требования

- Python 3.9+
- AUTHCODE из куки `ok.ru`
