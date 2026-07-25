# Installation

## Requirements

Python 3.9 or newer.

## Install from PyPI

```bash
pip install pyokbot
```

## Install from source

```bash
git clone https://github.com/SangoAlgo/pyokbot.git
cd pyokbot
pip install -e .
```

## Dependencies

These install automatically:

| Package | What it does |
|---|---|
| `aiohttp` | Async HTTP client for API calls and uploads |
| `requests` | Sync HTTP for token retrieval |
| `websockets` | WebSocket client for the OK.ru protocol |
| `munch` | Turns dicts into objects for message attributes |
| `selectolax` | Fast HTML parser for profile scraping |
| `sulguk` | Converts HTML to OK.ru's entity format |

## Getting an AUTHCODE

You need the `AUTHCODE` cookie from ok.ru:

1. Log in to [ok.ru](https://ok.ru) in your browser
2. Open Developer Tools (F12) → Application → Cookies
3. Find the `AUTHCODE` cookie and copy its value

This cookie is what authorizes your bot. Keep it private — anyone with your AUTHCODE can send messages as your bot.
