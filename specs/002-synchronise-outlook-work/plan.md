# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

# Implementation Plan: Synchronise Outlook Calendar to CalDAV

**Branch**: `002-synchronise-outlook-work` | **Date**: 2025-09-22 | **Spec**: `/specs/002-synchronise-outlook-work/spec.md`
**Input**: Feature specification from `/specs/002-synchronise-outlook-work/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context
**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]  
**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]  
**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]  
**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]  
**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]
**Project Type**: [single/web/mobile - determines source structure]  
**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]  
**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]  
**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Technical Context
- **Language/Version**: Prefer Python 3.11 (scripting, available CalDAV libraries) or Swift/Objective-C for macOS-native automation. [DECISION: Python 3.11 chosen for initial PoC]
- **Primary Dependencies**: `pyobjc` (for macOS accessibility/AppleScript interop) or `osascript` wrappers, `pillow` for image handling, `pytesseract` or `vision` bindings for OCR, `caldav` or `requests` for CalDAV interactions.
- **Testing**: `pytest` for unit tests; integration tests will be best-effort due to UI automation flakiness; contract tests for CalDAV API interactions using a test CalDAV server.
- **Target Platform**: macOS (desktop, logged-in GUI session required for UI automation). Scheduler target: `cron` or `launchd`.
- **Project Type**: Single project (script/tool) — Option 1 structure.
- **Performance Goals**: N/A (low-frequency sync jobs, not high throughput).
- **Constraints**: MUST not contact Microsoft servers. Requires a logged-in macOS GUI session with Outlook available. Accessibility permissions must be granted to the tool for UI automation.
- **Scale/Scope**: Single-user desktop sync; not a multi-tenant server.

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Based on `/specify/memory/constitution.md` (v2.2.0):

- Principle III (Test-First): This feature involves fragile UI automation and OCR; tests MUST be defined for OCR parsing and CalDAV mapping. Integration tests requiring UI automation should be marked [FLAKY] and run separately.
- Principle IV (Integration & Contract Testing): Contract tests MUST validate CalDAV requests and responses against a test CalDAV server.
- Principle V (Observability): The tool MUST emit structured logs for every parsed event and CalDAV action.

Initial evaluation: PASS with deviations documented (UI automation fragility). Complexity Tracking entry will justify UI automation approach.

[Gates determined based on constitution file]

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure]
```

**Structure Decision**: [DEFAULT to Option 1 unless Technical Context indicates web/mobile app]

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - UI language/layouts to support: English (US) only.
   - Conflict resolution policy: Favor Outlook (Outlook's version always replaces CalDAV).
   - Research: Best OCR approach on macOS (Tesseract vs Vision) for Outlook List view
   - Research: Reliable macOS UI automation approach that works with Outlook (Accessibility API, AppleScript, or third-party tools)
   - Research: CalDAV client library options and authentication patterns for the target server

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

--

### Phase 0 Output (create `research.md`)

**Decision: OCR engine**: Use `pytesseract` for initial PoC; evaluate macOS Vision for production if higher accuracy needed.  
**Rationale**: Tesseract is open-source and scriptable; macOS Vision may give higher accuracy but has different bindings and licensing considerations.  

**Decision: Automation approach**: Use macOS Accessibility API via `pyobjc` and `osascript` fallback for basic operations; use `screencapture` to capture the application window.  
**Rationale**: Accessibility API provides more robust control than raw keystroke simulation; `osascript`/AppleScript is a practical fallback. Requires Accessibility permission.

**Decision: CalDAV client**: Use Python `caldav` library for CalDAV interactions and implement tests against a test CalDAV server (e.g., Radicale or a lightweight test server).  
**Rationale**: Existing libraries reduce protocol-level bugs and speed development.

**Open items**:
- UI localization/layouts: NEEDS CLARIFICATION from user (which Outlook locales/layouts to support)
- Conflict resolution policy: NEEDS CLARIFICATION


## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh copilot`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

--

### Phase 1 Output (create `data-model.md` and `quickstart.md`)

`data-model.md` (summary):
- `ParsedEvent`:
   - `start_datetime` (ISO8601)
   - `end_datetime` (ISO8601)
   - `title` (string)
   - `location` (string, optional)
   - `description` (string, optional)
   - `confidence_score` (float 0..1)

`quickstart.md` (summary):
- Prereqs: macOS with Outlook installed, Python 3.11, `tesseract` installed, Accessibility permission granted to the tool, configured CalDAV server credentials.
- Steps: install dependencies, configure `config.json` with CalDAV endpoint and credentials, run `python sync_outlook_caldav.py --dry-run` to preview syncs, then schedule via `launchd`/`cron`.

`contracts/` (summary):
- `caldav_contract.json`: minimal contract describing required CalDAV endpoints for event creation/update (UID, PUT/REPORT methods), will run against test CalDAV server.


## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each contract → contract test task [P]
- Each entity → model creation task [P] 
- Each user story → integration test task
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Tests before implementation 
- Dependency order: Models before services before UI
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 25-30 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [ ] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS (with documented deviation: UI automation fragility)
- [ ] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [ ] Complexity deviations documented

---
*Based on Constitution v2.2.0 - See `/memory/constitution.md`*
