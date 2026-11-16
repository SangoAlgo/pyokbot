class PyokbotError(Exception):
    """Something went wrong inside pyokbot."""


class AuthenticationError(PyokbotError):
    """OK.ru rejected the auth code or tokens.

    Double-check your AUTHCODE cookie — it might be expired.
    """


class UploadError(PyokbotError):
    """File upload to OK.ru's servers failed.

    Could be a network issue, an invalid file path, or
    the server didn't like what you sent.
    """


class APIError(PyokbotError):
    """OK.ru sent back something unexpected.

    Usually means the internal protocol changed
    or a request was malformed.
    """


class RateLimitError(APIError):
    """Raised when OK.ru rate limit / flood control is encountered.

    Attributes:
        retry_after: Suggested seconds to wait before retrying.
    """

    def __init__(self, message: str, retry_after: int = 2) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class WebSocketError(PyokbotError):
    """The WebSocket connection dropped or refused."""


class TimeoutError(PyokbotError):
    """pyokbot waited for a server reply and none came."""
