import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from pyokbot import (
    APIError,
    PyokbotError,
    RateLimitError,
    TextAnimator,
    Vanus,
    progress_frames,
    reveal_frames,
    spinner_frames,
    typewriter_frames,
)


def test_typewriter_frames():
    frames = typewriter_frames("Hello", step=1, cursor="▌")
    assert frames == ["H▌", "He▌", "Hel▌", "Hell▌", "Hello"]

    frames_kept = typewriter_frames("Hi", step=1, cursor="▌", keep_cursor_at_end=True)
    assert frames_kept == ["H▌", "Hi▌"]

    empty = typewriter_frames("")
    assert empty == [""]


def test_typewriter_frames_step():
    frames = typewriter_frames("123456", step=2, cursor="|")
    assert frames == ["12|", "1234|", "123456"]


def test_progress_frames():
    frames = progress_frames(total_steps=5, prefix="Loading: ", filled_char="=", empty_char="-")
    assert len(frames) == 6
    assert frames[0] == "Loading: [-----] 0%"
    assert frames[-1] == "Loading: [=====] 100%"
    assert frames[2] == "Loading: [==---] 40%"


def test_spinner_frames():
    custom_spinner = ["|", "/", "-", "\\"]
    frames = spinner_frames("Loading", spinner=custom_spinner, loops=2, position="prefix")
    assert len(frames) == 8
    assert frames[0] == "| Loading"
    assert frames[1] == "/ Loading"

    suffix_frames = spinner_frames("Loading", spinner=["*"], loops=1, position="suffix")
    assert suffix_frames == ["Loading *"]


def test_reveal_frames():
    frames = reveal_frames("ABC", mask_char="#")
    assert frames[0] == "###"
    assert frames[1] == "A##"
    assert frames[2] == "AB#"
    assert frames[-1] == "ABC"


def test_rate_limit_error_hierarchy():
    err = RateLimitError("Too many requests, retry after 3 seconds", retry_after=3)
    assert isinstance(err, APIError)
    assert isinstance(err, PyokbotError)
    assert err.retry_after == 3
    assert "Too many requests" in str(err)


@pytest.mark.asyncio
async def test_text_animator_run():
    mock_bot = MagicMock()
    mock_bot.edit_message_text = AsyncMock(return_value=True)

    frames = ["Frame 1", "Frame 2", "Frame 3"]
    anim = TextAnimator(
        bot=mock_bot,
        chat_id="123",
        message_id="msg_1",
        frames=frames,
        interval=0.01,
    )
    await anim.run()

    assert mock_bot.edit_message_text.call_count == 3
    calls = [c.kwargs["message_text"] for c in mock_bot.edit_message_text.call_args_list]
    assert calls == ["Frame 1", "Frame 2", "Frame 3"]


@pytest.mark.asyncio
async def test_text_animator_ignore_identical():
    mock_bot = MagicMock()
    mock_bot.edit_message_text = AsyncMock(return_value=True)

    frames = ["Frame 1", "Frame 1", "Frame 2"]
    anim = TextAnimator(
        bot=mock_bot,
        chat_id="123",
        message_id="msg_1",
        frames=frames,
        interval=0.01,
        ignore_identical=True,
    )
    await anim.run()

    # Second identical frame should be skipped
    assert mock_bot.edit_message_text.call_count == 2
    calls = [c.kwargs["message_text"] for c in mock_bot.edit_message_text.call_args_list]
    assert calls == ["Frame 1", "Frame 2"]


@pytest.mark.asyncio
async def test_text_animator_auto_retry_on_rate_limit():
    mock_bot = MagicMock()

    # Fail on first call with RateLimitError, succeed on second call
    rate_err = RateLimitError("Too many requests, retry after 1 seconds", retry_after=1)
    mock_bot.edit_message_text = AsyncMock(side_effect=[rate_err, True, True])

    frames = ["Frame 1", "Frame 2"]
    anim = TextAnimator(
        bot=mock_bot,
        chat_id="123",
        message_id="msg_1",
        frames=frames,
        interval=0.01,
        auto_retry=True,
    )

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        await anim.run()

    # Called 3 times total: (Frame 1 failed -> Frame 1 retry ok -> Frame 2 ok)
    assert mock_bot.edit_message_text.call_count == 3
    # Check that backoff sleep was called
    assert mock_sleep.called


@pytest.mark.asyncio
async def test_text_animator_max_retries_exceeded():
    mock_bot = MagicMock()
    rate_err = RateLimitError("Too many requests, retry after 1 seconds", retry_after=1)
    mock_bot.edit_message_text = AsyncMock(side_effect=rate_err)

    frames = ["Frame 1"]
    anim = TextAnimator(
        bot=mock_bot,
        chat_id="123",
        message_id="msg_1",
        frames=frames,
        interval=0.01,
        auto_retry=True,
        max_retries=2,
    )

    with patch("asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(RateLimitError):
            await anim.run()

    assert mock_bot.edit_message_text.call_count == 3  # initial + 2 retries


@pytest.mark.asyncio
async def test_text_animator_background_and_stop():
    mock_bot = MagicMock()
    mock_bot.edit_message_text = AsyncMock(return_value=True)

    frames = ["1", "2", "3", "4", "5"]
    anim = TextAnimator(
        bot=mock_bot,
        chat_id="123",
        message_id="msg_1",
        frames=frames,
        interval=10.0,  # Long interval
    )

    task = anim.start_background()
    assert anim.is_running
    await asyncio.sleep(0.02)  # Let first frame run

    await anim.stop(final_text="Stopped!")
    assert not anim.is_running

    # Final call should be "Stopped!"
    last_call = mock_bot.edit_message_text.call_args_list[-1]
    assert last_call.kwargs["message_text"] == "Stopped!"


@pytest.mark.asyncio
async def test_vanus_animation_helpers():
    with patch("pyokbot.login.Login.start_login"):
        bot = Vanus("fake_auth")
    try:
        bot.edit_message_text = AsyncMock(return_value=True)

        # Test create_animator
        anim = bot.create_animator("chat_1", "msg_1", ["A", "B"], interval=0.01)
        assert isinstance(anim, TextAnimator)

        # Test animate_typewriter
        await bot.animate_typewriter("chat_1", "msg_1", "Hi", interval=0.01)
        assert bot.edit_message_text.call_count >= 2

        # Test animate_progress
        bot.edit_message_text.reset_mock()
        await bot.animate_progress("chat_1", "msg_1", total_steps=3, interval=0.01)
        assert bot.edit_message_text.call_count == 4
    finally:
        await bot._session.close()
