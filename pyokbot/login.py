"""
User authentication and token management for OK.ru API.

Handles login flow, token extraction, and user profile fetching.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import aiohttp
import requests
from selectolax.lexbor import LexborHTMLParser

from .logging_config import logger


class Login:
    """
    Manages authentication with OK.ru API.

    Handles AUTHCODE validation, token extraction, and user profile fetching via HTML parsing.

    Attributes:
        BASE_URL: OK.ru base URL.
        WS_URL: WebSocket endpoint URL.
        UA: User-Agent string for HTTP requests.
        WS_USER_AGENT: User-Agent data for WebSocket protocol.
    """

    BASE_URL: str = "https://ok.ru"
    WS_URL: str = "wss://api-messages-ws.ok.ru/websocket?okweb=true&autoinit=true&version=1.10.16"
    PING_INTERVAL: int = 30
    RECONNECT_DELAY: int = 10

    UA: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )

    WS_USER_AGENT: Dict[str, Any] = {
        "deviceType": "OKWEB",
        "appVersion": "1.10.16",
        "osVersion": "Windows",
        "locale": "ru",
        "deviceName": "Chrome",
        "screen": "1024x768 2.0x",
        "headerUserAgent": UA,
    }

    def __init__(self) -> None:
        """Initialize Login handler."""
        self.session: Optional[requests.Session] = None
        self.AUTHCODE: Optional[str] = None
        self.tkn: Optional[str] = None
        self.okweb_token: Optional[str] = None

    def build_session(self, authcode: str) -> requests.Session:
        """
        Create an authenticated HTTP session.

        Args:
            authcode: The AUTHCODE cookie value from OK.ru.

        Returns:
            Configured requests.Session with headers and cookies.
        """
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
        """
        Extract the internal TKN token from OK.ru.

        Args:
            session: Authenticated requests.Session.

        Returns:
            TKN token string, or empty string if extraction failed.
        """
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
            tkn = r.headers.get("tkn", "")
            if tkn:
                logger.debug("TKN token extracted successfully")
                return tkn
            else:
                logger.warning("TKN token not found in response headers")
        except requests.RequestException as e:
            logger.error(f"Failed to get TKN token: {e}")
        return ""

    def get_okweb_token(self, session: requests.Session, tkn: str) -> str:
        """
        Extract the OKWEB authentication token.

        Args:
            session: Authenticated requests.Session.
            tkn: The TKN token from get_tkn().

        Returns:
            OKWEB token string, or empty string if extraction failed.
        """
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
                logger.debug("OKWEB token extracted successfully")
                return token
            else:
                logger.warning("OKWEB token not found in response")
        except (requests.RequestException, ValueError) as e:
            logger.error(f"Failed to get OKWEB token: {e}")
        return ""

    def start_login(self, authcode: str) -> None:
        """
        Initialize authentication process.

        Validates AUTHCODE and extracts necessary tokens.

        Args:
            authcode: The AUTHCODE cookie value from OK.ru.

        Raises:
            ValueError: If AUTHCODE is invalid or tokens cannot be extracted.
        """
        self.AUTHCODE = authcode

        self.session = self.build_session(self.AUTHCODE)
        self.tkn = self.get_tkn(self.session)
        self.okweb_token = self.get_okweb_token(self.session, self.tkn)

        if not self.tkn:
            raise ValueError(
                "TKN not received — check AUTHCODE validity. "
                "Make sure you're using a valid AUTHCODE cookie from ok.ru"
            )
        if not self.okweb_token:
            raise ValueError(
                "OKWEB token not received — check AUTHCODE validity. "
                "The authentication tokens may have expired."
            )

        logger.info("Login initialization successful")

    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Fetch user profile information.

        Retrieves user data by scraping their profile page.

        Args:
            user_id: The OK.ru user ID.

        Returns:
            Dictionary containing user info:
            - id: User ID
            - name: User full name
            - avatar_url: URL to user's avatar
            - last_visit: Last visit status
            - last_update_time: When this data was fetched

        Raises:
            ValueError: If user profile cannot be parsed.
        """
        try:
            async with aiohttp.ClientSession(
                headers=self.session.headers if self.session else {}
            ) as session:
                start_time = datetime.now()

                async with session.get(f"https://ok.ru/profile/{user_id}") as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch user {user_id}: HTTP {response.status}")
                        raise ValueError(f"HTTP {response.status}")

                    html = await response.text()

                    tree = LexborHTMLParser(html)

                    # Extract user name
                    title_elem = tree.css_first("title")
                    if not title_elem:
                        raise ValueError("Could not parse user name from page")
                    user_name = title_elem.text(strip=True).split(" | ")[0].strip()

                    # Extract avatar
                    avatar_elem = tree.css_first('img[alt*="Фотография"]')
                    user_avatar = (
                        avatar_elem.attributes.get("src", "")
                        if avatar_elem
                        else "https://m.ok.ru/mres/img/stb3/male_370.png"
                    )

                    # Extract last visit
                    visit_elem = tree.css_first("div.anonym_user_head_last-visit-mark")
                    last_visit = (
                        visit_elem.text(strip=True)
                        if visit_elem
                        else "Сейчас на сайте"
                    )

                    logger.debug(f"User info fetched for {user_id}")

                    return {
                        "id": user_id,
                        "name": user_name,
                        "avatar_url": user_avatar,
                        "last_visit": last_visit,
                        "last_update_time": str(start_time),
                    }
        except Exception as e:
            logger.error(f"Failed to get user info for {user_id}: {e}")
            raise

    async def tst_user(self, user_id: str) -> Dict[str, Any]:
        """
        Test user validity (reserved for future use).

        Args:
            user_id: The OK.ru user ID to test.

        Returns:
            Dictionary with test results.
        """
        # Placeholder for future implementation
        return {"user_id": user_id, "valid": True}
