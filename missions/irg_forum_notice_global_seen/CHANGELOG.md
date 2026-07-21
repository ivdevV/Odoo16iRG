# Changelog — IRG Forum Notice Global Seen

## 16.0.1.0.0 — 2026-07-20

- Added `irg_forum_notice_global_seen`, an extension of
  `irg_forum_notice_popup` that records notice state globally by user and
  forum post rather than by course.
- Added guarded, idempotent global seen persistence and route checks that
  authorize post visibility before technical `sudo()` operations.
- Hardened legacy seen-row access: owner-scoped reads for internal and portal
  users, route-only mutations, and system-administrator management paths.
- Replaced the parent frontend popup asset with a race-safe implementation
  that suppresses a notice during one shared persistence request and waits
  before closing or navigating.
- Rendered untrusted notice text through DOM `textContent` and accepted popup
  links only when they resolve to same-origin HTTP(S) URLs.
- Narrowed concurrent duplicate recovery to PostgreSQL `UniqueViolation`, so
  unrelated integrity errors still propagate, and added a deterministic
  two-transaction regression for the duplicate race.
- Covered a linked non-system student with no course, batch, enrollment or
  admission through discovery, marking and subsequent suppression routes.
- Preserved legacy compatibility: any existing legacy row for the same user
  and post suppresses the notice regardless of its stored course.
- No legacy records are migrated, modified, or deleted.
