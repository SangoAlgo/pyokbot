from __future__ import annotations

import time
from datetime import datetime
from typing import Optional

import aiohttp
import requests


class Login:

    def __init__(self):
        self.BASE_URL = "https://ok.ru"
        self.WS_URL = "wss://api-messages-ws.ok.ru/websocket?okweb=true&autoinit=true&version=1.10.16"
        self.PING_INTERVAL = 30
        self.RECONNECT_DELAY = 10
        self.UA = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
        self.WS_USER_AGENT = {
            "deviceType": "OKWEB",
            "appVersion": "1.10.16",
            "osVersion": "Windows",
            "locale": "ru",
            "deviceName": "Chrome",
            "screen": "1024x768 2.0x",
            "headerUserAgent": self.UA,
        }

    def build_session(self, authcode: str) -> requests.Session:
        s = requests.Session()
        s.headers.update({
            "User-Agent": self.UA,
            "Accept-Language": "ru-RU,ru;q=0.9",
            "Origin": self.BASE_URL,
            "Referer": self.BASE_URL + "/",
        })
        s.cookies.set("AUTHCODE", authcode, domain=".ok.ru")
        return s

    def get_tkn(self, session: requests.Session) -> str:
        try:
            r = session.post(
                f"{self.BASE_URL}/web-api/upms",
                headers={
                    "accept": "application/json, text/javascript, */*; q=0.01",
                    "content-type": "application/json",
                    "x-requested-with": "XMLHttpRequest",
                },
                json=[{"alias": "test", "hash": "0"}],
                timeout=15,
            )
            return r.headers.get("tkn", "")
        except Exception:
            return ""

    def get_okweb_token(self, session: requests.Session, tkn: str) -> str:
        try:
            r = session.post(
                f"{self.BASE_URL}/web-api/v2/messages/credentials",
                headers={
                    "accept": "application/json, text/javascript, */*; q=0.01",
                    "content-type": "text/plain;charset=UTF-8",
                    "tkn": tkn,
                    "strd": "true",
                    "strv": "ADAPTIVE_FOUR_COLUMN",
                    "x-requested-with": "XMLHttpRequest",
                    "ok-screen": "messages",
                    "ok-prevscreen": "userMain",
                },
                json={"id": 5},
                timeout=15,
            )
            data = r.json()
            token = (data.get("result") or {}).get("token") or data.get("token", "")
            if token:
                return token
        except Exception:
            pass
        return ""

    def start_login(self, authcode: str):
        self.AUTHCODE = authcode
        self.session = self.build_session(self.AUTHCODE)
        self.tkn = self.get_tkn(self.session)
        self.okweb_token = self.get_okweb_token(self.session, self.tkn)
        if not self.tkn:
            raise ValueError("TKN not received — check AUTHCODE validity")
        if not self.okweb_token:
            raise ValueError("OKWEB token not received — check AUTHCODE validity")

    async def get_user_info(self, user_id: str) -> dict:
        from selectolax.lexbor import LexborHTMLParser

        async with aiohttp.ClientSession(headers=self.session.headers) as session:
            async with session.get(f"https://ok.ru/profile/{user_id}") as response:
                html = await response.text()
                tree = LexborHTMLParser(html)
                user_name = tree.css_first("title").text(strip=True).split(" | ")[0].strip()
                avatar = tree.css_first('img[alt*="Фотография"]')
                user_avatar = avatar.attributes.get("src", "") if avatar else ""
                if not user_avatar:
                    user_avatar = "https://m.ok.ru/mres/img/stb3/male_370.png"
                visit = tree.css_first("div.anonym_user_head_last-visit-mark")
                last_visit = visit.text(strip=True) if visit else "Сейчас на сайте"
                return {
                    "id": user_id,
                    "name": user_name,
                    "avatar_url": user_avatar,
                    "last_visit": last_visit,
                    "last_update_time": str(datetime.now()),
                }

    async def tst_user(self, user_id: str) -> dict:
        return {}
