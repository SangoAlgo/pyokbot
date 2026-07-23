"""
HTML formatting demo bot — shows all supported HTML tags.

Usage:
    python examples/html_demo_bot.py YOUR_AUTHCODE
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
            "/start, /help - this list\n"
            "/basic   - bold, italic, underline, strikethrough\n"
            "/code    - inline code and code block\n"
            "/heading - headings\n"
            "/link    - hyperlinks and mentions\n"
            "/mixed   - all tags combined\n"
            "/stop    - shutdown\n"
            "\nAll commands send formatted messages using parse_mode='html'."
        )
        await bot.send_message(message.chat.id, text)

    @bot.on_message(commands=["basic"])
    async def cmd_basic(message):
        html = (
            "<b>Bold text</b>\n"
            "<i>Italic text</i>\n"
            "<u>Underlined text</u>\n"
            "<s>Strikethrough text</s>\n"
            "\n"
            "<b>Bold <i>and italic</i></b>"
        )
        await bot.send_message(message.chat.id, html, parse_mode="html")

    @bot.on_message(commands=["code"])
    async def cmd_code(message):
        html = (
            "Inline <code>print('hello')</code> code\n\n"
            "Code block:\n"
            "<pre>def hello():\n"
            "    print('Hello, OK!')\n"
            "    return 42</pre>"
        )
        await bot.send_message(message.chat.id, html, parse_mode="html")

    @bot.on_message(commands=["heading"])
    async def cmd_heading(message):
        html = (
            "<h1>Main heading</h1>\n"
            "Content under main heading\n\n"
            "<b>Bold text that is NOT a heading</b>\n\n"
            "Regular paragraph text."
        )
        await bot.send_message(message.chat.id, html, parse_mode="html")

    @bot.on_message(commands=["link"])
    async def cmd_link(message):
        html = (
            "Hyperlink: <a href='https://ok.ru'>Odnoklassniki</a>\n"
            "User mention: <a href='{}'>your profile</a>\n"
            "\n"
            "Links open in the OK app browser."
        ).format(message.user.id)
        await bot.send_message(message.chat.id, html, parse_mode="html")

    @bot.on_message(commands=["mixed"])
    async def cmd_mixed(message):
        html = (
            "<h1>Welcome!</h1>\n"
            "This is a <b>formatted</b> message with <i>various</i> styles.\n\n"
            "Features:\n"
            "• <b>Bold</b> + <u>underline</u> combined\n"
            "• <i>Italic</i> with <s>strikethrough</s>\n"
            "• <code>inline code</code> and <pre>blocks</pre>\n"
            "• <a href='https://ok.ru'>Links</a> and <a href='{}'>mentions</a>\n\n"
            "All inside one message!"
        ).format(message.user.id)
        await bot.send_message(message.chat.id, html, parse_mode="html")

    @bot.on_message(commands=["stop"])
    async def cmd_stop(message):
        await bot.send_message(message.chat.id, "Bot stopped.")
        await bot.stop()

    @bot.on_message(filters="user")
    async def echo(message):
        if message.text:
            await bot.send_reply(message, "Use /help to see available commands.")

    await bot.polling()


if __name__ == "__main__":
    asyncio.run(main())
