# Tasks: Synchronise Outlook work calendar to CalDAV

**Input**: Design documents from `/specs/002-synchronise-outlook-work/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Extract: Python 3.11, pyobjc, pillow, pytesseract, caldav, macOS, single project
2. Load optional design documents:
   → data-model.md: ParsedEvent, SyncState, Config schema
   → contracts/: caldav_event_contract (PUT endpoint)
   → research.md: OCR (pytesseract), Automation (pyobjc/osascript), CalDAV (caldav lib)
   → quickstart.md: Installation, configuration, dry-run, scheduling
3. Generate tasks by category (Setup, Tests, Core, Integration, Polish)
4. Apply task rules (P for parallel, sequential for same file)
5. Order tasks by dependencies (Setup → Tests → Models → Services → Endpoints → Polish)
6. Number tasks sequentially (T001, T002...)
7. Create parallel execution examples
8. Validate task completeness
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/`, `tests/` at repository root

## Phase 3.1: Setup
- [x] T001 Create Python project structure (src/, tests/, config.json, sync_state.json)
- [x] T002 Initialize Python environment and install dependencies (`pillow`, `pytesseract`, `caldav`, `pyobjc`)
- [x] T003 [P] Configure linting (e.g., `flake8`, `black`) and formatting tools

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [x] T004 [P] Contract test CalDAV PUT operation in `tests/contract/test_caldav_put.py` (using a mock/test CalDAV server)
- [x] T005 [P] Unit test OCR parsing logic for event fields in `tests/unit/test_ocr_parsing.py`
- [x] T006 [P] Unit test event mapping to CalDAV format in `tests/unit/test_event_mapping.py`
- [x] T007 [FLAKY] Integration test Outlook UI automation (launch, navigate, screenshot) in `tests/integration/test_outlook_ui.py`
- [x] T008 [P] Unit test idempotency logic in `tests/unit/test_sync_state.py`
- [x] T009 [P] Unit test conflict resolution logic in `tests/unit/test_conflict_resolution.py`

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [x] T010 [P] Implement `ParsedEvent` and `SyncState` data models in `src/models/calendar_data.py`
- [x] T011 [P] Implement `config.json` loading and validation in `src/config.py`
- [x] T012 Implement macOS UI automation functions (launch, foreground, maximise, navigate Outlook) in `src/outlook_automation.py`
- [x] T013 Implement screenshot capture function in `src/outlook_automation.py`
- [x] T014 Implement OCR processing function in `src/ocr_processor.py`
- [x] T015 Implement event parsing from OCR output in `src/ocr_processor.py`
- [x] T016 Implement CalDAV client for event creation/update in `src/caldav_client.py`
- [x] T017 Implement main sync orchestration logic in `src/sync_tool.py`

## Phase 3.4: Integration
 - [x] T018 Implement logging for sync operations and errors in `src/utils/logger.py`
- [x] T019 Implement error handling and retry mechanisms in `src/sync_tool.py`
- [x] T020 Create `sync_outlook_caldav.py` CLI entry point
 - [x] T021 Create example `config.json` and `sync_state.json` files in `specs/002-synchronise-outlook-work/`
 - [x] T022 Draft `launchd` or `cron` script for scheduling in `scripts/`

## Phase 3.5: Polish
 - [x] T023 [P] Update `quickstart.md` with final installation and usage instructions
 - [x] T024 [P] Add comprehensive documentation and comments to all new code
 - [x] T025 Refactor code for clarity, maintainability, and remove duplication

## Dependencies
- T001-T003 before T004-T009
- T004-T009 before T010-T017
- T010-T011 before T017
- T012-T013 before T017
- T014-T015 before T017
- T016 before T017
- T017 before T018-T022
- T018-T022 before T023-T025

## Parallel Example
```bash
# Launch T004, T005, T006, T008, T009 together:
# Task: "Contract test CalDAV PUT operation in tests/contract/test_caldav_put.py"
# Task: "Unit test OCR parsing logic for event fields in tests/unit/test_ocr_parsing.py"
# Task: "Unit test event mapping to CalDAV format in tests/unit/test_event_mapping.py"
# Task: "Unit test idempotency logic in tests/unit/test_sync_state.py"
# Task: "Unit test conflict resolution logic in tests/unit/test_conflict_resolution.py"

# Launch T010, T011 together:
# Task: "Implement ParsedEvent and SyncState data models in src/models/calendar_data.py"
# Task: "Implement config.json loading and validation in src/config.py"

# Launch T023, T024 together:
# Task: "Update quickstart.md with final installation and usage instructions"
# Task: "Add comprehensive documentation and comments to all new code"
```

## Notes
- [P] tasks = different files, no dependencies
- [FLAKY] tasks are integration tests involving UI automation and may be unreliable; run with caution.
- Verify tests fail before implementing.
- Commit after each task.
- Avoid: vague tasks, same file conflicts.

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts**:
   - `caldav_event_contract.json` → T004 [P] Contract test CalDAV PUT operation
   
2. **From Data Model**:
   - `ParsedEvent`, `SyncState` → T010 [P] Implement data models
   - `Config schema` → T011 [P] Implement config loading/validation
   
3. **From User Stories/Requirements**:
   - FR-001, FR-002, FR-003 → T012, T013 Implement macOS UI automation and screenshot
   - FR-004 → T014, T015 Implement OCR processing and event parsing
   - FR-005 → T016 Implement CalDAV client
   - FR-006 (No MS servers) → Covered by overall design
   - FR-007 (Scheduler) → T022 Draft scheduler script
   - FR-008 (Idempotency) → T008 [P] Unit test idempotency, T017 Implement sync orchestration
   - FR-009 (Logging) → T018 Implement logging
   - FR-010 (Conflict resolution) → T009 [P] Unit test conflict resolution
   - Acceptance Scenarios → T007 [FLAKY] Integration test UI automation, T017 Implement sync orchestration
   
4. **Ordering**:
   - Setup → Tests → Models → Services → Endpoints → Polish
   - Dependencies block parallel execution

## Validation Checklist
*GATE: Checked by main() before returning*

- [ ] All contracts have corresponding tests
- [ ] All entities have model tasks
- [ ] All tests come before implementation
- [ ] Parallel tasks truly independent
- [ ] Each task specifies exact file path
- [ ] No task modifies same file as another [P] task
- [x] Corresponding `plan.md` contains `Constitution Check` and passes compliance review
