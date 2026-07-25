# FAQ

## What's an AUTHCODE and how do I get one?

It's a cookie from ok.ru that authenticates your bot. See the [installation guide](installation.md) for step-by-step instructions.

## Can I run multiple bots?

Yes. Each `Vanus` instance creates its own WebSocket connection. Different auth codes, different bots.

## Does the bot need to be online 24/7?

It only responds while the Python process is running. For round-the-clock use, throw it on a VPS or a cloud server.

## What happens when the connection drops?

pyokbot reconnects automatically with exponential backoff — 5s, 10s, 20s, up to 60s. It picks up where it left off.

## Is there a rate limit?

OK.ru doesn't document rate limits. In practice, a few messages per second works fine.

## Can my bot send messages to any user?

No. The bot can only send to chats it's a member of. It can't start a conversation with someone who hasn't written to it first.

## How do I get a message ID for pinning?

Message IDs are available on `message.id` inside handlers.

## What HTML tags are supported?

`<b>`, `<i>`, `<u>`, `<s>`, `<code>`, `<pre>`, `<h1>`, `<a href="...">`. Pass `parse_mode="html"` when sending.

## Is this an official library?

No. pyokbot is an independent project based on reverse-engineering OK.ru's WebSocket protocol. Not affiliated with Odnoklassniki.
