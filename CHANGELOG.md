# Changelog

## [1.2.0] - 2026-11-16

### Added
- **Rate Limit & Flood Control Handling**:
  - Added `RateLimitError` inheriting from `APIError` with parsed `retry_after` seconds.
  - Automatic detection of OK.ru 60-requests-per-minute flood limits in `ws.request()` and `messages.edit_message_text`.
- **Text Animation Engine (Telegram Userbot Style)**:
  - `TextAnimator` engine (`pyokbot/animator.py`):
    - Configurable frame sequences, interval timing, and parse modes.
    - Automatic exponential/linear backoff and retry on `RateLimitError`.
    - Background execution (`anim.start_background()`) and cancellation (`anim.stop(final_text=...)`).
    - Skipping of identical frames (`ignore_identical=True`).
    - Custom per-frame hook (`on_frame(index, text)`).
  - Animation frame generators:
    - `typewriter_frames`: Smooth typewriter typing effect with customizable cursor glyph and step size.
    - `progress_frames`: Visual progress bars with percentage and customizable characters (`🟩▫️`, `█░`, etc.).
    - `spinner_frames`: Rotating loading spinners (braille, emoji clocks, ascii).
    - `reveal_frames`: Text reveal animations from masked strings.
- **Client Animation Convenience Methods**:
  - `bot.animate_text(chat_id, message_id, frames, interval=0.5, auto_retry=True)`
  - `bot.animate_typewriter(chat_id, message_id, text, interval=0.2, step=1, cursor="▌")`
  - `bot.animate_progress(chat_id, message_id, total_steps=10, interval=0.5, prefix="Progress: ")`
  - `bot.create_animator(...)` for custom scheduled or background animation tasks.
- **Test Suite**: Added `tests/test_animator.py` bringing total unit tests to 80 (100% passing).

## [1.1.0] - 2026-11-16

### Fixed
- **WebSocket Session Stability**: Fixed premature `PING` before auth handshake and added mandatory raw `PING <token> <timestamp>` frame after `AUTH` packet (prevents 15-second disconnection drops).
- **Keepalive Interval**: Set keepalive ping interval to 25s matching the official OK.ru web client.
- **Protocol Version**: Upgraded WebSocket connection URL to `version=1.10.28`.
- **RPC Sequence Correlation**: Replaced single-queue `wait_for_message` with sequence-correlated (`seq`) `asyncio.Future` mapping via `ws.request()`. Prevents race conditions, timeouts, and dropped packets in active group chats.
- **Memory Leak Protection**: Handled message IDs in `polling()` pruned to prevent unbounded memory growth.
- **Polling Crash Resilience**: Handled packet processing errors gracefully in `polling()` to prevent loop crashes on unexpected packets.

### Added
- **Reactions API**:
  - `set_reaction(chat_id, message_id, reaction="👍")` (Opcode 178)
  - `remove_reaction(chat_id, message_id)` (Opcode 179)
  - `get_reactions(chat_id, message_ids)` (Opcode 180)
  - `get_reacted_users(chat_id, message_id, reaction, marker, count)` (Opcode 181)
  - `@bot.on_reaction()` decorator for handling incoming reaction events (Opcodes 155, 156)
- **Chat Management**:
  - `join_chat(link)` (Opcode 57)
  - `leave_chat(chat_id)` (Opcode 58)
  - `add_chat_members(chat_id, user_ids)` (Opcode 59)
  - `get_chat_history(chat_id, from_time, count)` (Opcode 49)
  - `get_chat_participants(chat_id, last_event_time)` (Opcode 61)
  - `subscribe_chat(chat_id, subscribe)` (Opcode 75)
- **Real-Time Event Listeners**:
  - `@bot.on_typing()` decorator for user typing indicators (Opcode 129)
  - `@bot.on_read()` decorator for message read receipts (Opcode 130)
  - `@bot.on_presence()` decorator for user presence/online updates (Opcode 132)
  - `@bot.on_event(opcode)` decorator for custom raw opcode interception
  - `mark_as_read(chat_id, message_id)` (Opcode 50)
- **Opcode Registry**: Added 20+ newly documented opcodes to `MessageOpcode`.
- **Unit & Integration Tests**: Added test coverage in `tests/test_new_features.py` (67/67 tests passing).

## [0.2.0] - 2026-07-24

### Added
- Type hints for all public methods in client.py and messages.py
- Docstrings for all methods in client.py and messages.py
- MessageOpcode enum to replace magic numbers (opcodes.py)
- Python logging (logging_config.py) — replaces bare `print()` calls
- Auto-reconnect logging in ws.py

### Changed
- Version bumped from 0.1.0 to 0.2.0
- README rewritten in natural (non-template) style
- All mkdocs documentation pages rewritten for clarity
- `.gitignore` expanded with standard Python entries

### Fixed
- Bare `print()` calls replaced with proper logger in client.py
- Hardcoded opcode numbers replaced with `MessageOpcode.*` enum references

## [0.1.0] - 2026-07-24

### Added
- Initial release
- Vanus client with WebSocket connection to OK.ru
- Message sending (text, reply, photo, video, file, voice)
- HTML formatting support (bold, italic, code, headings, links)
- Chat management (pin, edit, delete, clear, change title/photo, kick)
- Handler system with filters (commands, content-type, text, user/bot)
- User info caching with TTL-based refresh
- Auto-reconnect with exponential backoff
- 61 pytest tests across 6 test files
- MkDocs documentation (6 pages)
- GitHub Actions CI (pytest on 3.9-3.12) and docs deployment
