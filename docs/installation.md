# Installation

## Python version

pyokbot requires **Python 3.9 or later**.

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

pyokbot installs these packages automatically:

| Package | Purpose |
|---------|---------|
| `aiohttp` | Async HTTP client for API calls and file uploads |
| `requests` | Synchronous HTTP client for token retrieval |
| `websockets` | WebSocket client for the OK.ru messaging protocol |
| `munch` | Dict-to-object conversion for message attributes |
| `selectolax` | Fast HTML parser for scraping user profiles |
| `sulguk` | HTML-to-OK messenger entity conversion |

## Obtaining an AUTHCODE

To use pyokbot, you need an `AUTHCODE` cookie from ok.ru:

1. Open a browser and log in to [ok.ru](https://ok.ru)
2. Open Developer Tools (F12) → Application/Storage → Cookies
3. Copy the value of the `AUTHCODE` cookie

This token grants your bot access to the OK.ru messaging API.
