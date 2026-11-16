from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Callable, Iterable, Sequence

from .errors import RateLimitError
from .logging_config import logger

if TYPE_CHECKING:
    from .client import Vanus


# Default spinner frames (braille dots)
DEFAULT_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

# Emoji clocks spinner
CLOCK_SPINNER_FRAMES = [
    "🕐", "🕑", "🕒", "🕓", "🕔", "🕕",
    "🕖", "🕗", "🕘", "🕙", "🕚", "🕛",
]


def typewriter_frames(
    text: str,
    step: int = 1,
    cursor: str = "▌",
    keep_cursor_at_end: bool = False,
) -> list[str]:
    """
    Generate sequential frames emulating a typewriter typing effect.

    Args:
        text: Target text to type out.
        step: Number of characters to advance per frame (default: 1).
        cursor: Cursor character appended to the current typed substring.
        keep_cursor_at_end: If False (default), the final frame has no cursor.

    Returns:
        List of string frames.
    """
    if not text:
        return [text]

    frames: list[str] = []
    step = max(1, step)
    for i in range(step, len(text), step):
        frames.append(f"{text[:i]}{cursor}")

    if keep_cursor_at_end:
        frames.append(f"{text}{cursor}")
    else:
        frames.append(text)

    return frames


def progress_frames(
    total_steps: int = 10,
    prefix: str = "",
    suffix: str = "",
    filled_char: str = "🟩",
    empty_char: str = "▫️",
    show_percentage: bool = True,
) -> list[str]:
    """
    Generate progress bar animation frames.

    Args:
        total_steps: Number of blocks in the progress bar (default: 10).
        prefix: Optional text preceding the bar (e.g. 'Processing: ').
        suffix: Optional text following the bar or percentage.
        filled_char: Character for completed progress.
        empty_char: Character for remaining progress.
        show_percentage: Whether to append percentage (e.g. ' 50%').

    Returns:
        List of formatted progress strings.
    """
    total_steps = max(1, total_steps)
    frames: list[str] = []
    for step in range(total_steps + 1):
        pct = int(step / total_steps * 100)
        bar = filled_char * step + empty_char * (total_steps - step)
        parts = [prefix] if prefix else []
        parts.append(f"[{bar}]")
        if show_percentage:
            parts.append(f" {pct}%")
        if suffix:
            parts.append(f" {suffix}")
        frames.append("".join(parts))
    return frames


def spinner_frames(
    text: str,
    spinner: Sequence[str] | None = None,
    loops: int = 2,
    position: str = "prefix",
) -> list[str]:
    """
    Generate frames with an animated rotating spinner alongside text.

    Args:
        text: Base text to display with the spinner.
        spinner: Sequence of glyphs/emojis for the spinner.
        loops: Number of full rotation cycles to generate.
        position: 'prefix' (spinner before text) or 'suffix' (spinner after).

    Returns:
        List of animation frames.
    """
    glyphs = spinner or DEFAULT_SPINNER_FRAMES
    frames: list[str] = []
    for _ in range(max(1, loops)):
        for glyph in glyphs:
            if position == "suffix":
                frames.append(f"{text} {glyph}".strip())
            else:
                frames.append(f"{glyph} {text}".strip())
    return frames


def reveal_frames(
    text: str,
    mask_char: str = "*",
    step: int = 1,
) -> list[str]:
    """
    Generate frames that reveal text character by character from a mask.

    Args:
        text: Final string to reveal.
        mask_char: Masking character.
        step: Number of characters to unmask per frame.

    Returns:
        List of frames.
    """
    if not text:
        return [text]
    frames: list[str] = []
    n = len(text)
    step = max(1, step)
    for i in range(0, n, step):
        revealed = text[:i]
        masked = mask_char * (n - i)
        frames.append(f"{revealed}{masked}")
    frames.append(text)
    return frames


class TextAnimator:
    """
    Engine for animating message text edits in OK.ru chats (similar to Telegram userbots).

    Handles rate limit detection, automatic backoff and retry, interval delays,
    and background execution.

    Example:
        anim = TextAnimator(bot, chat_id, msg_id, typewriter_frames("Hello, world!"), interval=0.3)
        await anim.run()

    Background example:
        anim = TextAnimator(bot, chat_id, msg_id, spinner_frames("Generating..."))
        anim.start_background()
        # ... do heavy work ...
        await anim.stop(final_text="Done!")
    """

    def __init__(
        self,
        bot: Vanus,
        chat_id: str | int,
        message_id: str,
        frames: Iterable[str],
        interval: float = 0.5,
        auto_retry: bool = True,
        max_retries: int = 5,
        parse_mode: str | None = None,
        ignore_identical: bool = True,
        on_frame: Callable[[int, str], Any] | None = None,
    ) -> None:
        """
        Initialize the animator.

        Args:
            bot: Pyokbot Vanus client instance.
            chat_id: Target chat ID.
            message_id: ID of the message to animate.
            frames: Sequence of text frames to cycle through.
            interval: Delay in seconds between frames (default 0.5s).
            auto_retry: Automatically wait and retry on OK.ru RateLimitError.
            max_retries: Maximum consecutive rate limit retries per frame.
            parse_mode: 'html' or None.
            ignore_identical: Skip sending frames if text is identical to current.
            on_frame: Optional callback invoked after each frame: on_frame(index, frame_text).
        """
        self.bot = bot
        self.chat_id = chat_id
        self.message_id = str(message_id)
        self.frames = list(frames)
        self.interval = max(0.05, float(interval))
        self.auto_retry = auto_retry
        self.max_retries = max_retries
        self.parse_mode = parse_mode
        self.ignore_identical = ignore_identical
        self.on_frame = on_frame

        self._current_text: str | None = None
        self._bg_task: asyncio.Task | None = None
        self._stopped = False

    @property
    def is_running(self) -> bool:
        """True if the animator is currently executing in the background."""
        return self._bg_task is not None and not self._bg_task.done()

    async def run(self) -> None:
        """
        Run the animation sequentially through all frames.
        """
        self._stopped = False
        for idx, frame in enumerate(self.frames):
            if self._stopped:
                break

            if self.ignore_identical and frame == self._current_text:
                continue

            await self._send_frame_with_retry(frame)
            self._current_text = frame

            if self.on_frame:
                try:
                    res = self.on_frame(idx, frame)
                    if asyncio.iscoroutine(res):
                        await res
                except Exception as e:
                    logger.debug(f"Error in on_frame callback: {e}")

            if idx < len(self.frames) - 1 and not self._stopped:
                await asyncio.sleep(self.interval)

    async def _send_frame_with_retry(self, frame: str) -> None:
        retries = 0
        while not self._stopped:
            try:
                await self.bot.edit_message_text(
                    chat_id=self.chat_id,
                    message_id=self.message_id,
                    message_text=frame,
                    parse_mode=self.parse_mode,
                )
                return
            except RateLimitError as e:
                if not self.auto_retry or retries >= self.max_retries:
                    logger.error(
                        f"TextAnimator rate limit exceeded: {e} (retries={retries}/{self.max_retries})"
                    )
                    raise
                retries += 1
                backoff = max(1.0, float(e.retry_after)) + 0.3
                logger.warning(
                    f"TextAnimator encountered rate limit: waiting {backoff:.1f}s (retry {retries}/{self.max_retries})"
                )
                await asyncio.sleep(backoff)

    def start_background(self) -> asyncio.Task:
        """
        Launch the animation as an asynchronous background task.

        Returns:
            The created asyncio.Task.
        """
        if self._bg_task and not self._bg_task.done():
            return self._bg_task
        self._stopped = False
        self._bg_task = asyncio.create_task(self.run())
        return self._bg_task

    async def stop(self, final_text: str | None = None) -> None:
        """
        Stop the animation immediately, cancelling any background task,
        and optionally set final message text.

        Args:
            final_text: If provided, edits the message to this text upon stopping.
        """
        self._stopped = True
        if self._bg_task and not self._bg_task.done():
            self._bg_task.cancel()
            try:
                await self._bg_task
            except asyncio.CancelledError:
                pass
            self._bg_task = None

        if final_text is not None and final_text != self._current_text:
            try:
                await self.bot.edit_message_text(
                    chat_id=self.chat_id,
                    message_id=self.message_id,
                    message_text=final_text,
                    parse_mode=self.parse_mode,
                )
                self._current_text = final_text
            except Exception as e:
                logger.warning(f"Failed to set final animation text: {e}")
