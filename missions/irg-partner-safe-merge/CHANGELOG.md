# Changelog — IRG Partner Safe Merge

## 2026-07-20

- Added `irg_partner_safe_merge`, an administrator-only workflow to safely consolidate exactly two duplicate personal contacts.
- Added server-side preflight, closed relation policies, scalar conflict choices, preview hashing, deterministic locks, idempotent confirmation, and immutable merge audits.
- Preserved lead records while reassigning permitted relations; archives and protects the source contact after a successful merge.
- Added focused Odoo and static-contract coverage, including rollback, blockers, manipulated RPC, and concurrent confirmation scenarios.
