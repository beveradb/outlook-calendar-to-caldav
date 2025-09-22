# Research Notes: OCR + macOS automation for Outlook → CalDAV

## Unknowns / Questions
- UI localization/layouts: Only English (US) UI/layouts need to be supported.
- Conflict resolution policy: Favor Outlook (Outlook's version always replaces CalDAV).

## OCR Options
- Tesseract (`pytesseract`): Open-source, easy to script, cross-platform. Good for initial PoC.
- macOS Vision framework: High-quality OCR on macOS, better on stylized fonts, but requires macOS-specific bindings.

Decision: Start with `pytesseract` for PoC; evaluate macOS Vision for production if accuracy insufficient.

## macOS Automation Options
- Accessibility API via `pyobjc`: Directly interact with UI elements; requires Accessibility permission.
- AppleScript / `osascript`: Useful for basic window operations; less granular than Accessibility API.
- `cliclick` / keyboard/mouse simulation: Simple but brittle.

Decision: Use Accessibility API (`pyobjc`) with `osascript` fallbacks and `screencapture` for screenshots.

## CalDAV Client
- `caldav` Python library: Implement create/update operations and handle UID/ETag.
- Alternative: Use direct `requests` with RFC 4791-compliant XML bodies for precise control.

Decision: Use `caldav` library for speed; fall back to raw HTTP if necessary.

## Test CalDAV Server Options
- Radicale (lightweight Python CalDAV server) for local testing.
- Baikal or other lightweight server for integration tests.

Decision: Use Radicale for local integration tests.

## Security & Permissions
- Tool requires Accessibility permission on macOS.
- CalDAV credentials must be stored securely (recommend: macOS Keychain or environment variables; PoC: `config.json` with clear warnings).

## Summary & Next Steps
- Implement PoC script using Python 3.11, `pyobjc`, `pytesseract`, `pillow`, and `caldav`.
- Create sample `config.json` schema and local state file design.
- Build unit tests for OCR parsing logic and CalDAV mapping.

