# Data Model

## ParsedEvent
- `start_datetime` (string, ISO8601)
- `end_datetime` (string, ISO8601)
- `title` (string)
- `location` (string, optional)
- `description` (string, optional)
- `confidence_score` (float 0..1)

## Config schema (config.json)
- `caldav`:
  - `url` (string)
  - `username` (string)
  - `password` (string) or instruction to use Keychain
  - `calendar_path` (string)
- `ocr`:
  - `engine` (string: tesseract|vision)
  - `language` (string, optional)
- `sync`:
  - `conflict_policy` (string: favor_outlook|favor_caldav|timestamp)
  - `dry_run` (bool)

