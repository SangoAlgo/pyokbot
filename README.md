<!-- markdownlint-disable-file -->
<div align="center">

# 🤖 pyokbot

### Python SDK для Одноклассников — создавайте ботов через WebSocket

[![PyPI](https://img.shields.io/pypi/v/pyokbot?style=flat-square&logo=pypi&logoColor=white&color=3776AB)](https://pypi.org/project/pyokbot/)
[![Python](https://img.shields.io/pypi/pyversions/pyokbot?style=flat-square&logo=python&logoColor=white&color=3776AB)](https://pypi.org/project/pyokbot/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Status](https://img.shields.io/badge/status-Alpha-orange?style=flat-square)](https://github.com/SangoAlgo/pyokbot)

**Единственная Python-библиотека для разработки ботов в OK.ru через прямое WebSocket-соединение**

[🚀 Начать](#-quick-start) • [📚 Документация](#-документация) • [💬 Примеры](#-примеры) • [❓ FAQ](#-faq)

</div>

---

## ✨ Возможности

| 🎯 Возможность | 📝 Описание |
|---|---|
| ⚡ **Реал-тайм** | Прямое WebSocket-соединение — сообщения приходят мгновенно |
| 🔄 **Полная функциональность** | Все, что может официальный клиент OK.ru |
| 💬 **Текст и медиа** | Отправка фото, видео, файлов, голосовых сообщений |
| 🏷️ **Форматирование** | HTML-теги: `<b>`, `<i>`, `<code>`, `<h1>` и другие |
| 🎮 **Фильтры** | Команды, текст, типы контента — гибкая маршрутизация |
| 👥 **Управление чатом** | Пин-сообщения, удаление, редактирование, кик участников |
| 🔒 **Асинхронность** | Async/await на `asyncio` — обрабатывает 1000+ сообщений/сек |
| 💾 **Кэширование** | Автоматическое кэширование профилей с TTL |
| 🔁 **Автопереподключение** | Экспоненциальная задержка при разрывах соединения |
| 📊 **Логирование** | Структурированное логирование всех операций |

---

## 🚀 Quick Start

### Установка

```bash
pip install pyokbot
```

### Минимальный пример

```python
import asyncio
from pyokbot import Vanus

async def main():
    # Создаём бота с вашим AUTHCODE
    bot = Vanus("YOUR_AUTHCODE")
    await bot.run()

    # Регистрируем обработчик команды
    @bot.on_message(commands=["start"])
    async def cmd_start(message):
        await bot.send_message(
            message.chat.id,
            "👋 Привет! Я бот. Отправь мне /help"
        )

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

---

## 📖 Документация

**Полная документация:** https://SangoAlgo.github.io/pyokbot

- 📘 [Установка и настройка](https://SangoAlgo.github.io/pyokbot/installation/)
- 🚀 [Быстрый старт](https://SangoAlgo.github.io/pyokbot/quickstart/)
- 📚 [API Справочник](https://SangoAlgo.github.io/pyokbot/api-reference/)
- 💡 [Примеры кода](https://SangoAlgo.github.io/pyokbot/examples/)
- ❓ [FAQ](https://SangoAlgo.github.io/pyokbot/faq/)

---

## 🔐 Получение AUTHCODE

1. Откройте [ok.ru](https://ok.ru) в браузере
2. Откройте **DevTools** (F12 → Application/Storage → Cookies)
3. Найдите cookie `AUTHCODE`
4. Скопируйте его значение
5. Используйте в коде:

```python
bot = Vanus("ваш_authcode_здесь")
```

⚠️ **ВАЖНО:** Храните AUTHCODE как пароль! Не коммитьте в git.

Рекомендуется использовать переменные окружения:

```bash
export OK_AUTHCODE="ваш_authcode"
```

```python
import os
bot = Vanus(os.getenv("OK_AUTHCODE"))
```

---

## 📋 Требования

- **Python 3.9+**
- Активный аккаунт в OK.ru
- Стабильное интернет-соединение

---

## 🛠️ Зависимости

```
aiohttp       # Асинхронный HTTP
websockets    # WebSocket клиент
requests      # HTTP запросы (для логина)
munch         # Удобный доступ к dict
selectolax    # Парсинг HTML (для профилей)
sulguk        # HTML-форматирование
```

---

## ❓ FAQ

### Вопрос: Что такое AUTHCODE?

**Ответ:** Это cookie сессии OK.ru, которая позволяет боту действовать от вашего имени. Без неё бот не сможет подключиться.

---

### Вопрос: Безопасно ли делиться AUTHCODE?

**Ответ:** ❌ **НЕ БЕЗОПАСНО!** AUTHCODE — это как пароль. Если его украдут, смогут:
- Читать все ваши сообщения
- Отправлять сообщения от вашего имени
- Присоединяться к вашим чатам
- Удалять сообщения

Никогда не выкладывайте его в интернете.

---

### Вопрос: Может ли бот работать 24/7?

**Ответ:** ✅ Да! Бот может работать столько, сколько нужно. Рекомендуется развернуть на VPS или облаке:
- DigitalOcean, Heroku, AWS
- Дешёвый VPS: ~2-3$/месяц
- Docker контейнеризация поддерживается

---

### Вопрос: Поддерживаются ли группы?

**Ответ:** ✅ Да, полностью. Бот может:
- Читать сообщения в группах
- Отправлять сообщения
- Управлять участниками
- Реагировать на события

---

### Вопрос: Что если аккаунт заблокирует OK.ru?

**Ответ:** OK.ru редко блокирует за ботов. Рекомендуется:
- Использовать отдельный аккаунт для бота
- Не спамить сообщения
- Делать задержки между запросами
- Соблюдать политику платформы

---

### Вопрос: Можно ли обновить AUTHCODE без перезагрузки?

**Ответ:** ✅ Да:
```python
# Получить новый AUTHCODE
new_authcode = "новый_код"

# Остановить старого бота
await bot.stop()

# Создать нового с новым кодом
bot = Vanus(new_authcode)
await bot.run()
```

---

### Вопрос: Как обработать ошибки?

**Ответ:** Используйте try/except:
```python
@bot.on_message(filters="user")
async def handler(message):
    try:
        await bot.send_reply(message, "Привет!")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await bot.send_reply(message, "❌ Ошибка обработки")
```

---

## 🤝 Вклад

Нашли баг или есть идея? 🎉

1. Fork репозитория
2. Создайте ветку (`git checkout -b feature/amazing-feature`)
3. Коммитьте изменения (`git commit -m 'Add amazing feature'`)
4. Пушьте ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

---

## 📝 Лицензия

Распространяется под лицензией **MIT**. Подробнее см. [LICENSE](LICENSE).

---

## ⚠️ Дисклеймер

pyokbot — это **неофициальная** библиотека. Она использует публичный WebSocket API OK.ru, используемый официальным клиентом.

**Использование на свой риск!** Автор не несёт ответственность за:
- Блокировку аккаунта OK.ru
- Потерю данных
- Нарушение политики платформы

---

## 📞 Контакты

- **GitHub Issues**: [Сообщить об ошибке](https://github.com/SangoAlgo/pyokbot/issues)
- **Email**: [SangoAlgo](https://github.com/SangoAlgo)

---

## 🎓 Образовательные ресурсы

Если вы новичок в Python и asyncio, вот полезные ссылки:

- 🐍 [Python Docs](https://docs.python.org/3/)
- ⚡ [asyncio Tutorial](https://docs.python.org/3/library/asyncio.html)
- 🤖 [Telegram Bot API](https://core.telegram.org/bots/api) (похожая концепция)
- 📚 [Real Python](https://realpython.com/)

---

<div align="center">

### Сделано ❤️ для Одноклассников

⭐ **Если нравится проект — дайте звёзду!**

</div>
