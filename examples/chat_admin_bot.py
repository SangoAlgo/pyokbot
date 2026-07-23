"""
Chat admin bot — manage chat settings via commands.

Usage:
    python examples/chat_admin_bot.py YOUR_AUTHCODE
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
            "/pin <message_id>  - pin a message\n"
            "/edit <id> <text>  - edit a message\n"
            "/clear             - clear chat history (all)\n"
            "/clear_me          - clear chat history (me)\n"
            "/title <name>      - change chat title\n"
            "/info              - show chat info\n"
            "/stop              - shutdown the bot\n"
            "\nYou need admin rights in the chat for most commands."
        )
        await bot.send_message(message.chat.id, text)

    @bot.on_message(commands=["info"])
    async def cmd_info(message):
        chat_info = await bot.get_chat_info(message.chat.id)
        title = chat_info.get("title") or "(no title)"
        text = (
            f"Title: {title}\n"
            f"ID: {chat_info['chat_id']}\n"
            f"Members: {chat_info['members']['count']}\n"
            f"Messages: {chat_info['messages']['count']}\n"
            f"Status: {chat_info['status']}\n"
            f"Link: {chat_info.get('link', 'none')}"
        )
        pinned = chat_info.get("pinned")
        if pinned:
            text += f"\nPinned: {pinned['text']} (by {pinned['sender_id']})"
        await bot.send_message(message.chat.id, text)

    @bot.on_message(commands=["pin"])
    async def cmd_pin(message):
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await bot.send_message(message.chat.id, "Usage: /pin <message_id>")
            return

        msg_id = parts[1]
        try:
            await bot.pin_chat_message(message.chat.id, msg_id)
            await bot.send_message(message.chat.id, f"Message {msg_id} pinned.")
        except Exception as e:
            await bot.send_message(message.chat.id, f"Pin failed: {e}")

    @bot.on_message(commands=["edit"])
    async def cmd_edit(message):
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            await bot.send_message(message.chat.id, "Usage: /edit <message_id> <new text>")
            return

        _, msg_id, new_text = parts
        try:
            await bot.edit_message_text(message.chat.id, msg_id, new_text)
            await bot.send_message(message.chat.id, "Message edited.")
        except Exception as e:
            await bot.send_message(message.chat.id, f"Edit failed: {e}")

    @bot.on_message(commands=["clear"])
    async def cmd_clear(message):
        try:
            await bot.clear_chat_history(message.chat.id, for_all=True)
            await bot.send_message(message.chat.id, "History cleared for everyone.")
        except Exception as e:
            await bot.send_message(message.chat.id, f"Clear failed: {e}")

    @bot.on_message(commands=["clear_me"])
    async def cmd_clear_me(message):
        try:
            await bot.clear_chat_history(message.chat.id, for_all=False)
            await bot.send_message(message.chat.id, "History cleared for me.")
        except Exception as e:
            await bot.send_message(message.chat.id, f"Clear failed: {e}")

    @bot.on_message(commands=["title"])
    async def cmd_title(message):
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await bot.send_message(message.chat.id, "Usage: /title <new name>")
            return

        new_title = parts[1]
        try:
            await bot.change_chat_title(message.chat.id, new_title)
            await bot.send_message(message.chat.id, f"Title changed to '{new_title}'.")
        except Exception as e:
            await bot.send_message(message.chat.id, f"Title change failed: {e}")

    @bot.on_message(commands=["stop"])
    async def cmd_stop(message):
        await bot.send_message(message.chat.id, "Bot stopped.")
        await bot.stop()

    await bot.polling()


if __name__ == "__main__":
    asyncio.run(main())
