# Changelog

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
