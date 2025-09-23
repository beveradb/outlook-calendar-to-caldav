# Tasks: Pushbullet Notification Integration for Sync Success/Error

**Input**: Design documents from `/specs/003-add-functionality-to/`
**Prerequisites**: plan.md (required)

## Execution Flow (main)
```
1. Load plan.md from feature directory
2. Generate tasks by category:
   → Setup: project init, dependencies
   → Tests: contract/integration/unit tests
   → Core: models, services, CLI commands
   → Integration: logging, external API
   → Polish: unit tests, docs
3. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
4. Number tasks sequentially (T001, T002...)
5. Validate task completeness
```

## Phase 3.1: Setup
 [X] T001 Ensure project structure matches plan.md (src/, tests/, config.json)
 [X] T002 Add 'requests' to dependencies in pyproject.toml

- [ ] T004 [P] Unit test: config loads Pushbullet API key correctly (tests/unit/test_config.py)
- [ ] T005 [P] Contract test: Pushbullet notification sends correct message on success (tests/contract/test_pushbullet_success.py)
- [ ] T006 [P] Contract test: Pushbullet notification sends correct message on error (tests/contract/test_pushbullet_error.py)
- [ ] T007 [P] Integration test: Sync tool triggers Pushbullet notification on success (tests/integration/test_sync_pushbullet_success.py)
- [ ] T008 [P] Integration test: Sync tool triggers Pushbullet notification on error (tests/integration/test_sync_pushbullet_error.py)

## Phase 3.3: Core Implementation
- [ ] T009 Implement Pushbullet notification logic in src/lib/pushbullet_notify.py
- [ ] T010 Integrate Pushbullet notification into sync flow in src/sync_tool.py
- [ ] T011 Update error handling in src/sync_tool.py to send notification on failure
- [ ] T012 Ensure notification is sent only once per sync run
- [ ] T013 Log notification attempts and errors in src/utils/logger.py

## Phase 3.4: Polish
- [ ] T014 [P] Add unit tests for edge cases (invalid API key, network error) in tests/unit/test_pushbullet_notify.py
- [ ] T015 [P] Update documentation in README.md to describe Pushbullet notification setup
- [ ] T016 [P] Review code for security (API key handling) and performance (notification timing)

## Dependencies
- Setup (T001-T003) before tests (T004-T008)
- Tests (T004-T008) before implementation (T009-T013)
- Implementation before polish (T014-T016)
- [P] tasks can run in parallel if in different files

## Parallel Example
```
# Launch T004-T008 together:
Task: "Unit test: config loads Pushbullet API key correctly in tests/unit/test_config.py"
Task: "Contract test: Pushbullet notification sends correct message on success in tests/contract/test_pushbullet_success.py"
Task: "Contract test: Pushbullet notification sends correct message on error in tests/contract/test_pushbullet_error.py"
Task: "Integration test: Sync tool triggers Pushbullet notification on success in tests/integration/test_sync_pushbullet_success.py"
Task: "Integration test: Sync tool triggers Pushbullet notification on error in tests/integration/test_sync_pushbullet_error.py"
```

## Validation Checklist
- [ ] All entities have model tasks
- [ ] All tests come before implementation
- [ ] Parallel tasks truly independent
- [ ] Each task specifies exact file path
- [ ] No task modifies same file as another [P] task
- [ ] Corresponding `plan.md` contains `Constitution Check` and passes compliance review
