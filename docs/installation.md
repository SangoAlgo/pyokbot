# Installation

## Requirements

- Python 3.9 or newer

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

pyokbot relies on these packages — they install automatically:

| Package        | Role                                          |
| -------------- | --------------------------------------------- |
| `aiohttp`      | Async HTTP client for API calls and uploads   |
| `requests`     | Synchronous HTTP for token retrieval          |
| `websockets`   | WebSocket client for the OK.ru protocol       |
| `munch`        | Dict-to-object conversion for messages        |
| `selectolax`   | Fast HTML parser for profile scraping         |
| `sulguk`       | HTML to OK.ru entity format conversion        |

## Getting an AUTHCODE

To use pyokbot you need the `AUTHCODE` cookie from ok.ru:

1. Open a browser and log in to [ok.ru](https://ok.ru)
2. Open Developer Tools (F12) → Application → Cookies
3. Find the `AUTHCODE` cookie and copy its value

This cookie authorizes your bot to use the messaging API. Keep it private — anyone with your AUTHCODE can send messages as your bot.
