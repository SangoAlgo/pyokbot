"""
Echo bot — replies to messages, handles basic commands.

Usage:
    python examples/echobot.py YOUR_AUTHCODE
"""
import asyncio
import sys
from pyokbot import Vanus


async def main():
    auth_code = sys.argv[1] if len(sys.argv) > 1 else input("AUTHCODE: ")

    bot = Vanus(auth_code)
    await bot.run()

    @bot.on_message(commands=["start"])
    async def cmd_start(message):
        await bot.send_message(
            message.chat.id,
            "Hi! I'm an echo bot. Send me anything and I'll repeat it.",
        )

    @bot.on_message(commands=["help"])
    async def cmd_help(message):
        text = (
            "/start - welcome message\n"
            "/help  - this list\n"
            "/info  - your user info\n"
            "/ping  - pong check\n"
            "/stop  - shutdown the bot\n"
            "\nJust send any text — I'll echo it back."
        )
        await bot.send_message(message.chat.id, text)

    @bot.on_message(commands=["info"])
    async def cmd_info(message):
        user_info = await bot.get_user_info(message.user.id)
        await bot.send_reply(
            message,
            f"Name: {user_info['name']}\n"
            f"ID: {user_info['id']}\n"
            f"Status: {user_info['last_visit']}",
        )

    @bot.on_message(commands=["ping"])
    async def cmd_ping(message):
        await bot.writing_emulation(message.chat.id)
        await asyncio.sleep(1)
        await bot.send_reply(message, "pong!")

    @bot.on_message(commands=["stop"])
    async def cmd_stop(message):
        await bot.send_message(message.chat.id, "Bot stopped.")
        await bot.stop()

    @bot.on_message(filters="user", content_types=["photo"])
    async def handle_photo(message):
        if message.photo:
            await bot.send_photo(
                message.chat.id,
                message.photo[0].url,
                caption="Here's your photo back!",
                repl_to_message=message.id,
            )

    @bot.on_message(filters="user", content_types=["video"])
    async def handle_video(message):
        await bot.send_reply(message, "Got a video!")

    @bot.on_message(filters="user", content_types=["audio"])
    async def handle_audio(message):
        await bot.send_reply(message, "Got a voice message!")

    @bot.on_message(filters="user")
    async def echo(message):
        if message.text:
            await bot.send_reply(message, message.text)

    await bot.polling()


if __name__ == "__main__":
    asyncio.run(main())
