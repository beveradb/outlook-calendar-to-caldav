# calendar-sync Constitution
<!-- Sync Impact Report
Version change: v2.1.1 -> v2.2.0
Modified principles: none renamed; clarified descriptions and added explicit MUST/SHOULD language
Added sections: Development Workflow (mandatory sections clarified)
Removed sections: none
Templates requiring updates: /.specify/templates/plan-template.md ✅ updated
					   /.specify/templates/spec-template.md ⚠ pending
					   /.specify/templates/tasks-template.md ⚠ pending
Follow-up TODOs: TODO(RATIFICATION_DATE): confirm original adoption date if known
-->

## Core Principles

### I. Minimal, Interoperable Tools
All components MUST be small, focused, and interoperable. Design favors plain-text, stable interfaces
and small libraries that can be composed into larger workflows. Rationale: small surface areas
reduce integration friction and make reasoning about sync behavior easier.

### II. CLI-First Integration
Command-line interfaces and scriptable behavior SHOULD be provided for every subsystem. All
automations MUST support non-interactive usage (stdin/args → stdout, structured errors to stderr)
to enable CI, debugging, and user automation. Rationale: calendar syncing integrates with varied
environments and benefits from predictable text-based contracts.

### III. Test-First (NON-NEGOTIABLE)
Tests MUST be written before implementation for all production code paths. Contract tests and
integration tests are REQUIRED for any change that affects external behavior. Rationale: sync
logic correctness is critical; test-first prevents regressions and clarifies expectations.

### IV. Integration & Contract Testing
Integration tests MUST cover cross-system behaviors (auth, rate limits, idempotency, conflict
resolution). Contract tests MUST validate schema and I/O expectations with external systems.
Rationale: calendar-sync operates across APIs and clients where subtle mismatches cause data
loss.

### V. Observability, Versioning, Simplicity
Systems MUST emit structured logs and sufficient telemetry to diagnose failures. Release
artifacts MUST use semantic versioning; breaking changes require a MAJOR bump and a
documented migration plan. Keep designs as simple as possible; avoid premature optimization.


## Development Workflow

- Code reviews: All changes MUST be reviewed by at least one other maintainer. Reviews MUST
	validate tests and check the Constitution Check in the related plan.md.
- Branching: Feature work SHOULD use topic branches named `feat/<short-desc>` or
	`fix/<short-desc>`. Merge via pull request after CI passes.
- Releases: Tag releases with semantic versions and include migration notes for breaking changes.


## Security & Performance Constraints

- Authentication: Integrations with calendar providers MUST use secure OAuth flows where
	supported; secrets MUST not be committed to the repository.
- Performance: Sync operations SHOULD be designed to be resumable and rate-limit aware; high
	volume jobs MUST be batched and instrumented.


## Governance

- Constitution precedence: This document supersedes ad-hoc practices. Any deviation MUST be
	documented, justified in a complexity tracking entry, and approved by maintainers.
- Amendments: Changes to principles or governance require a PR with an implementation/migration
	plan and approval from at least two maintainers. Minor wording fixes MAY be applied via PR
	with a single maintainer approval.
- Compliance review: Every feature plan (`plan.md`) MUST include a `Constitution Check` section.

**Version**: 2.2.0 | **Ratified**: TODO(RATIFICATION_DATE): confirm adoption date | **Last Amended**: 2025-09-22