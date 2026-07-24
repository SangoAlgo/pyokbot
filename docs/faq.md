# FAQ

## What is an AUTHCODE and how do I get it?

An `AUTHCODE` is a cookie from ok.ru that authenticates your bot. See the [Installation guide](installation.md#obtaining-an-authcode) for details.

## Can I run multiple bots?

Yes. Each `Vanus` instance maintains its own WebSocket connection. Create separate instances with different auth codes.

## Does the bot need to be online 24/7?

Your bot only responds while the Python process is running. For 24/7 operation, deploy it to a VPS or cloud server.

## What happens on disconnect?

pyokbot automatically reconnects with exponential backoff (5s, 10s, 20s, etc.). The bot resumes normal operation once the connection is restored.

## Is there a rate limit?

OK.ru's server-side rate limits are undocumented. In practice, sending a few messages per second works reliably.

## Can I send messages to any user?

Your bot can send messages to any chat it is a member of. It cannot initiate private conversations with users who haven't interacted with it.

## How do I get the message ID for pinning?

Message IDs are available on the `message.id` attribute in handlers.

## What HTML tags are supported?

`<b>`, `<i>`, `<u>`, `<s>`, `<code>`, `<pre>`, `<h1>`, `<a href="...">`. Use `parse_mode="html"` when sending.

## Is this an official library?

No. pyokbot is an independent implementation based on reverse-engineering the OK.ru WebSocket protocol. It is not affiliated with or endorsed by Odnoklassniki.
