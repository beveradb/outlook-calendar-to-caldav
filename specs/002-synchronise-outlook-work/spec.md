# Feature Specification: Synchronise Outlook Calendar to CalDAV

**Feature Branch**: `002-synchronise-outlook-work`  
**Created**: 2025-09-22
**Status**: Draft  
**Input**: User description: "Synchronise Outlook Calendar events to a CalDAV server by manipulating the Outlook macOS application window, extracting events via screenshots+OCR, and writing them to a configured CalDAV server. Tool should launch Outlook, foreground and maximise the window, open calendar view, go to Today, switch to Work Week, then List view, screenshot, OCR, parse events, and create corresponding CalDAV entries. Must not communicate with Microsoft servers; runs via scheduler."

## Execution Flow (main)
```
1. Parse user description from Input
	→ If empty: ERROR "No feature description provided"
2. Extract key concepts from description
	→ Identify: actors (scheduled runner, user), actions (launch app, screenshot, OCR, CalDAV write), data (event fields), constraints (no MS servers)
3. For each unclear aspect:
	→ Mark with [NEEDS CLARIFICATION: specific question]
4. Fill User Scenarios & Testing section
	→ If no clear user flow: ERROR "Cannot determine user scenarios"
5. Generate Functional Requirements
	→ Each requirement must be testable
6. Identify Key Entities (calendars, events)
7. Run Review Checklist
	→ If any [NEEDS CLARIFICATION]: WARN "Spec has uncertainties"
	→ If implementation details found: ERROR "Remove tech details"
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT the tool must achieve and WHY (synchronisation without contacting Microsoft servers)
- ❌ Avoid embedding platform-only implementation details in requirements (those belong to the plan/implementation)

### Section Requirements
- **Mandatory sections**: User Scenarios & Testing, Functional Requirements, Key Entities, Review & Acceptance Checklist

### For AI Generation
1. **Mark all ambiguities**: Use [NEEDS CLARIFICATION: specific question] for any assumption you'd need to make
2. **Don't guess**: If the description doesn't specify something (e.g., retention, calendar mapping), mark it

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
As a user who has been granted permission, I want my Outlook Calendar events to be mirrored to a configured CalDAV calendar so that events created or updated in Outlook are available to the CalDAV clients without exposing Microsoft account credentials or contacting Microsoft servers directly.

### Acceptance Scenarios
1. Given Outlook is installed and the user account is logged in, when the tool runs, then Outlook is launched (if not running), the Calendar view is shown in List view for Today, a screenshot is taken, OCR extracts event start, end, title, location and notes, and corresponding events are created/updated on the configured CalDAV calendar.
2. Given an event already synced previously, when the event is unchanged, then no duplicate entry is created on the CalDAV calendar.
3. Given a conflict (event edited in both places), when conflict resolution policy applies, then the configured policy (e.g., favor Outlook or favor CalDAV) is applied and documented.

### Edge Cases
- What if Outlook's UI language or layout differs? → Tool MUST assume English (US) UI and layouts only.
- What if OCR fails to parse critical fields? → Tool MUST log parse failures and skip problematic events.
- What if the CalDAV server rejects authentication? → Tool MUST surface error and retry according to a backoff policy.

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: Tool MUST launch Microsoft Outlook on macOS and bring its main window to the foreground and maximised.
- **FR-002**: Tool MUST programmatically switch Outlook to Calendar view, navigate to Today, switch to Work Week view, then List view using keyboard shortcuts or UI automation.
- **FR-003**: Tool MUST capture a screenshot of the Outlook application window in List view for the current day.
- **FR-004**: Tool MUST run OCR on the screenshot and extract event records with at minimum: start datetime, end datetime (or duration), title/summary, location, and notes/description when present.
- **FR-005**: Tool MUST map parsed events to CalDAV entries and create or update events on a configured CalDAV server using standard CalDAV methods.
- **FR-006**: Tool MUST NOT communicate with Microsoft servers for data access (explicit constraint).
- **FR-007**: Tool MUST be runnable from a scheduler (cron/launchd) and operate headlessly where possible; acceptable to run with a logged-in macOS GUI session available.
- **FR-008**: Tool MUST be idempotent: repeated runs with no changes MUST not create duplicates.
- **FR-009**: Tool MUST log all sync operations and parsing errors; logs MUST include enough context to map a parsed entry to the CalDAV operation attempted.

*Example of marking unclear requirements:*
- **FR-010**: Conflict resolution policy MUST be to favor Outlook (Outlook's version always replaces CalDAV).

### Key Entities *(include if feature involves data)*
- **Event (Parsed)**: start_datetime, end_datetime (or duration), title, location, description, original_source_id (opaque hash derived from parsed OCR fields), confidence_score
- **CalDAVEntry**: UID, start, end, summary, location, description, etag/last_modified

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [ ] No implementation details that bind to an internal library
- [ ] Focused on user value and business needs
- [ ] All mandatory sections completed

### Constitution Compliance
- [ ] Plan includes a `Constitution Check` referencing `/specify/memory/constitution.md`

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Requirements are testable and unambiguous
- [ ] Success criteria are measurable (see Acceptance Scenarios)

---

## Execution Status
*Updated by main() during processing*

- [ ] User description parsed
- [ ] Key concepts extracted
- [ ] Ambiguities marked
- [ ] User scenarios defined
- [ ] Requirements generated
- [ ] Entities identified
- [ ] Review checklist passed

---

**Notes / Implementation considerations (for planning, not requirements)**
- On macOS, window automation may use AppleScript / Accessibility API / third-party tools (e.g., `osascript`, `cliclick`, `osascript` + `screencapture`) to control Outlook and capture screenshots.
- OCR engines: Tesseract or macOS Vision framework; choose one matching licensing and reliability needs.
- CalDAV interactions: use an existing CalDAV client library (e.g., `caldav` in Python) or implement minimal RFC 4791-compliant requests if library constraints exist.

