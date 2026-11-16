"""
Example bot demonstrating Telegram-style text animations on OK.ru.

Commands:
    /typewriter <text> - Animates typing text character by character
    /progress          - Animates a visual progress bar
    /spinner           - Animates a rotating spinner while doing async work

Usage:
    python examples/animation_bot.py YOUR_AUTHCODE
"""

import asyncio
import sys

from pyokbot import Vanus, spinner_frames


async def main():
    if len(sys.argv) < 2:
        print("Usage: python animation_bot.py <AUTHCODE>")
        return

    auth_code = sys.argv[1]
    bot = Vanus(auth_code)
    await bot.run()

    @bot.on_message(commands=["typewriter"])
    async def typewriter_handler(message):
        text = message.text.replace("/typewriter", "").strip() or "Hello from pyokbot userbot animation!"
        chat_id = message.chat.id
        msg_id = message.id

        await bot.animate_typewriter(
            chat_id=chat_id,
            message_id=msg_id,
            text=text,
            interval=0.2,
            step=2,
            cursor="▌",
        )

    @bot.on_message(commands=["progress"])
    async def progress_handler(message):
        chat_id = message.chat.id
        msg_id = message.id

        await bot.animate_progress(
            chat_id=chat_id,
            message_id=msg_id,
            total_steps=10,
            interval=0.35,
            prefix="Downloading: ",
            suffix="KB",
            filled_char="🟩",
            empty_char="▫️",
        )
        await asyncio.sleep(0.5)
        await bot.edit_message_text(chat_id, msg_id, "✅ Download complete! [🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩] 100%")

    @bot.on_message(commands=["spinner"])
    async def spinner_handler(message):
        chat_id = message.chat.id
        msg_id = message.id

        frames = spinner_frames("Processing request...", loops=2)
        anim = bot.create_animator(chat_id, msg_id, frames, interval=0.2)
        anim.start_background()

        # Simulate heavy background work
        await asyncio.sleep(3.0)

        # Stop animation and set final result
        await anim.stop(final_text="✨ Request completed successfully!")

    print("Animation bot running. Send /typewriter, /progress, or /spinner in chat.")
    await bot.polling()


if __name__ == "__main__":
    asyncio.run(main())
