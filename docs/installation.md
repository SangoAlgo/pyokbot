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

## What gets installed

pyokbot comes with these dependencies:

- `aiohttp` — async HTTP client for API calls and file uploads
- `requests` — sync HTTP for token retrieval
- `websockets` — WebSocket client for the OK.ru protocol
- `munch` — dict-to-object conversion for message attributes
- `selectolax` — fast HTML parser for scraping profiles
- `sulguk` — HTML to OK.ru entity conversion

## Getting an AUTHCODE

To use pyokbot you need an `AUTHCODE` cookie from ok.ru:

1. Open a browser and log in to [ok.ru](https://ok.ru)
2. Open Developer Tools (F12) → Application → Cookies
3. Find the `AUTHCODE` cookie and copy its value

This is what authorizes your bot to use the messaging API.
