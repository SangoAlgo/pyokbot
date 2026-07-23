"""
Filter demo bot — demonstrates all filter types.

Usage:
    python examples/filter_demo_bot.py YOUR_AUTHCODE
"""
import asyncio
import sys
from pyokbot import Vanus


async def main():
    auth_code = sys.argv[1] if len(sys.argv) > 1 else input("AUTHCODE: ")

    bot = Vanus(auth_code)
    await bot.run()

    # === COMMAND FILTERS ===

    @bot.on_message(commands=["start", "help"])
    async def cmd_help(message):
        text = (
            "Commands:\n"
            "/start, /help - this list\n"
            "/me           - show your info\n"
            "/stop         - shutdown\n"
            "\n"
            "Text filters:\n"
            "Send 'hello' or 'bye' for text match\n\n"
            "Content filters:\n"
            "Send a photo, video, voice or file\n\n"
            "Filter chain:\n"
            "Send 'photo' in a message starting with /"
        )
        await bot.send_message(message.chat.id, text)

    @bot.on_message(commands=["me"])
    async def cmd_me(message):
        url = message.user.url
        await bot.send_reply(
            message,
            f"Your ID: {message.user.id}\nProfile: {url}",
        )

    @bot.on_message(commands=["stop"])
    async def cmd_stop(message):
        await bot.send_message(message.chat.id, "Bot stopped.")
        await bot.stop()

    # === TEXT FILTERS (exact match) ===

    @bot.on_message(filters="user", text="hello")
    async def on_hello(message):
        await bot.send_reply(message, "Hi there!")

    @bot.on_message(filters="user", text="bye")
    async def on_bye(message):
        await bot.send_reply(message, "See you later!")

    # === TEXT LIST FILTER ===

    @bot.on_message(filters="user", text=["thanks", "thx", "thank you"])
    async def on_thanks(message):
        await bot.send_reply(message, "You're welcome!")

    # === CONTENT TYPE FILTERS ===

    @bot.on_message(filters="user", content_types=["photo"])
    async def on_photo(message):
        await bot.send_reply(
            message,
            f"Photo received! Size: {len(message.photo)} file(s).",
        )

    @bot.on_message(filters="user", content_types=["video"])
    async def on_video(message):
        duration = message.video[0].get("duration", "unknown")
        await bot.send_reply(message, f"Video received! Duration: {duration}s.")

    @bot.on_message(filters="user", content_types=["audio"])
    async def on_audio(message):
        await bot.send_reply(message, "Voice message received!")

    @bot.on_message(filters="user", content_types=["document"])
    async def on_document(message):
        name = message.document.get("name", "unknown")
        size = message.document.get("size", 0)
        await bot.send_reply(
            message,
            f"File received: {name} ({size} bytes).",
        )

    # === MULTIPLE CONTENT TYPES ===

    @bot.on_message(filters="user", content_types=["photo", "video"])
    async def on_photo_or_video(message):
        await bot.writing_emulation(message.chat.id)
        await asyncio.sleep(0.5)
        await bot.send_reply(message, "Nice media!")

    # === COMBINED: COMMAND + TEXT (message starts with / but matches text too) ===

    @bot.on_message(filters="user", text="photo")
    async def on_photo_please(message):
        await bot.send_photo(
            message.chat.id,
            photo_file_path="https://img.olympics.com/images/image/private/t_1-1_300/f_auto/primary/pcxgwhoweqzzhiuqbwqw",
            caption="Here you go!",
        )

    # === FALLBACK: catch-all for user messages ===

    @bot.on_message(filters="user")
    async def fallback(message):
        if message.text:
            await bot.send_reply(
                message,
                f"You said: {message.text}\n"
                f"(send /help to see what I can do)",
            )

    await bot.polling()


if __name__ == "__main__":
    asyncio.run(main())
