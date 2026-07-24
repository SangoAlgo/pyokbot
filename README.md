<p align="center">
  <img src="https://placehold.co/600x200/1a1a2e/e94560?text=pyokbot&font=montserrat" alt="pyokbot" width="600">
</p>

<p align="center">
  <b>Python library for creating bots in Odnoklassniki (ok.ru) messenger via WebSocket</b><br>
  <i>The only Python library for OK.ru bot development — async, fast, production-ready</i>
</p>

<p align="center">
  <a href="https://pypi.org/project/pyokbot/"><img src="https://img.shields.io/pypi/v/pyokbot?style=flat-square&logo=pypi&logoColor=white&color=3776AB" alt="PyPI"></a>
  <a href="https://pypi.org/project/pyokbot/"><img src="https://img.shields.io/pypi/pyversions/pyokbot?style=flat-square&logo=python&logoColor=white&color=3776AB" alt="Python versions"></a>
  <a href="LICENSE"><img src="https://img.shields.io/pypi/l/pyokbot?style=flat-square&color=green" alt="License"></a>
  <a href="https://github.com/SangoAlgo/pyokbot/actions"><img src="https://img.shields.io/github/actions/workflow/status/SangoAlgo/pyokbot/ci.yml?style=flat-square&logo=github" alt="CI"></a>
  <a href="https://SangoAlgo.github.io/pyokbot"><img src="https://img.shields.io/badge/docs-mkdocs-1a73e8?style=flat-square&logo=readthedocs&logoColor=white" alt="Docs"></a>
  <a href="https://github.com/SangoAlgo/pyokbot"><img src="https://img.shields.io/github/stars/SangoAlgo/pyokbot?style=flat-square&logo=github" alt="Stars"></a>
</p>

---

## Quick Start

```bash
pip install pyokbot
```

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

---

## Features

| Feature | Description |
|---------|-------------|
| **WebSocket protocol** | Direct connection to OK.ru messaging servers — no polling, real-time updates |
| **Async/await** | Built on `asyncio` and `aiohttp` for high concurrency |
| **Command system** | Decorate handlers with `@bot.on_message(commands=["start"])` |
| **Content-type filters** | Route photos, videos, audio, documents separately |
| **Text & regex filters** | Match exact text or lists of phrases |
| **HTML formatting** | Send styled messages with `<b>`, `<i>`, `<a>`, `<code>`, `<h1>` and more |
| **Media sending** | Upload and send photos, videos, files, voice messages |
| **Chat management** | Pin, edit, delete, clear history, change title/photo, kick members |
| **User info caching** | Auto-caches profiles with TTL-based refresh |
| **Auto-reconnect** | Handles disconnects with exponential backoff |

---

## Why pyokbot?

**pyokbot is the only Python library for building bots on Odnoklassniki (ok.ru) messenger.** There are no alternatives — no wrappers, no SDKs, no community ports. If you want to automate OK.ru messaging with Python, this is it.

The library speaks the raw WebSocket protocol that OK.ru's own clients use. This means:
- **Real-time** — messages arrive instantly, no HTTP polling
- **Full parity** — all message types, formatting, and chat features supported
- **Lightweight** — no browser automation, no reverse-engineered REST APIs

---

## Examples

Browse ready-to-run examples in the [`examples/`](examples/) directory:

| Bot | What it shows |
|-----|---------------|
| [`echobot.py`](examples/echobot.py) | Echo bot with commands (`/start`, `/help`, `/ping`, `/stop`) and media handlers |
| [`media_bot.py`](examples/media_bot.py) | Sending photos, videos, files, and voice messages |
| [`filter_demo_bot.py`](examples/filter_demo_bot.py) | All filter types: commands, text, content-type, combined |
| [`html_demo_bot.py`](examples/html_demo_bot.py) | HTML-formatted messages with all supported tags |
| [`chat_admin_bot.py`](examples/chat_admin_bot.py) | Chat management: pin, edit, clear, kick, change title/photo |

```bash
python examples/echobot.py YOUR_AUTHCODE
```

---

## Documentation

Full documentation is available at **[SangoAlgo.github.io/pyokbot](https://SangoAlgo.github.io/pyokbot)**.

- [Installation guide](https://SangoAlgo.github.io/pyokbot/installation/)
- [Quick start tutorial](https://SangoAlgo.github.io/pyokbot/quickstart/)
- [API reference](https://SangoAlgo.github.io/pyokbot/api-reference/)
- [Examples walkthrough](https://SangoAlgo.github.io/pyokbot/examples/)
- [FAQ](https://SangoAlgo.github.io/pyokbot/faq/)

---

## Requirements

- Python 3.9+
- A valid `AUTHCODE` cookie from ok.ru

---

## License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for details.
