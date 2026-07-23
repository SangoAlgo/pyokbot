"""
Media bot — sends photos, videos, files and voice messages.

Usage:
    python examples/media_bot.py YOUR_AUTHCODE
"""
import asyncio
import sys
from pyokbot import Vanus


async def main():
    auth_code = sys.argv[1] if len(sys.argv) > 1 else input("AUTHCODE: ")

    bot = Vanus(auth_code)
    await bot.run()

    @bot.on_message(commands=["start", "help"])
    async def cmd_help(message):
        text = (
            "/photo  - send a sample photo\n"
            "/video  - send a short video\n"
            "/file   - send a PDF file\n"
            "/voice  - send a voice message\n"
            "/stop   - shutdown the bot\n"
            "\nReply to a message with any command to attach it as a reply."
        )
        await bot.send_message(message.chat.id, text)

    @bot.on_message(commands=["photo"])
    async def cmd_photo(message):
        await bot.writing_emulation(message.chat.id)
        await bot.send_photo(
            message.chat.id,
            photo_file_path="https://img.olympics.com/images/image/private/t_1-1_300/f_auto/primary/pcxgwhoweqzzhiuqbwqw",
            caption="Sample photo",
            repl_to_message=message.id if message.is_reply else None,
        )

    @bot.on_message(commands=["video"])
    async def cmd_video(message):
        await bot.send_message(message.chat.id, "Sending a video... (use a local file path)")

        video_path = "sample.mp4"
        try:
            await bot.send_video(
                message.chat.id,
                video_file_path=video_path,
                caption="Sample video",
                repl_to_message=message.id if message.is_reply else None,
            )
        except FileNotFoundError:
            await bot.send_message(
                message.chat.id,
                f"Place a video file at '{video_path}' and try again.",
            )

    @bot.on_message(commands=["file"])
    async def cmd_file(message):
        file_path = "sample.pdf"
        try:
            await bot.send_file(
                message.chat.id,
                file_path=file_path,
                title="Sample document",
                repl_to_message=message.id if message.is_reply else None,
            )
        except FileNotFoundError:
            await bot.send_message(
                message.chat.id,
                f"Place a file at '{file_path}' and try again.",
            )

    @bot.on_message(commands=["voice"])
    async def cmd_voice(message):
        voice_path = "sample.ogg"
        try:
            await bot.send_voice(
                message.chat.id,
                voice_file_path=voice_path,
                repl_to_message=message.id if message.is_reply else None,
            )
        except FileNotFoundError:
            await bot.send_message(
                message.chat.id,
                f"Place a voice file at '{voice_path}' and try again.",
            )

    @bot.on_message(commands=["stop"])
    async def cmd_stop(message):
        await bot.send_message(message.chat.id, "Bot stopped.")
        await bot.stop()

    await bot.polling()


if __name__ == "__main__":
    asyncio.run(main())
