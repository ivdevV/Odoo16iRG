# Task 1: Implement and test the complete safe-merge addon

Work only in `C:\tmp\Odoo16iRG-irg-partner-safe-merge`. Do not commit, push, or open a PR.

Read completely before editing:

- `AGENTS.md`
- `.agents/skills/odoo16_developer/SKILL.md`
- `missions/irg-partner-safe-merge/plan.md`
- `doc/micro-specs/2026-07-20-irg_partner_safe_merge.md`
- `docs/superpowers/plans/2026-07-20-irg-partner-safe-merge.md`

Implement the complete new addon under `addons-extra/extrairg/irg_partner_safe_merge` without modifying any existing addon. The approved micro-spec is authoritative.

Required product behavior:

1. Administrator-only contextual action and server-side enforcement for exactly two active personal contacts.
2. Explainable master recommendation, editable master/source choice, relation inventory, scalar conflict choices, prevalidation and explicit confirmation.
3. Closed static relation allowlist: metadata discovers/block unknown references but never authorizes dynamic transfers.
4. Atomic confirmation with deterministic locks, complete revalidation and preview hash comparison.
5. ORM transfers and recomputations exactly per micro-spec; preserve leads as independent records; never use standard `_merge()`, `cr.commit()`, or destructive conflict fallbacks.
6. Coherent `res.users`/`op.student` transfer, scalar conflict resolution, approved M2M/follower union, direct-partner polymorphic resources, and blocking for unknown/bank/accounting/payment/collision cases.
7. Archive source with protected `irg_merged_into_partner_id`, forbid direct marker writes/reactivation/deletion, and create an immutable administrator-only audit last.
8. Idempotent repeat confirmation and safe behavior under inverse/concurrent attempts.

TDD and verification:

- Write focused Odoo tests before production code and record a genuine RED command/result in `missions/irg-partner-safe-merge/execution.md`.
- If Docker is still unavailable, record that objective limitation before production edits and run the strongest static/unit substitute; do not claim the Odoo integration gate passed.
- Cover permissions/RPC tampering, selection/identity/company/hierarchy guards, recommendation, scalar decisions, a Camila-equivalent graph, allowlist blockers, category/follower union, preview changes, rollback injection, idempotency, merged-source protection and audit immutability.
- Run compilation, XML/CSV parsing, focused tests when possible, `git diff --check`, and `git status --short`.
- Use `apply_patch` for every source/documentation edit.

Create `missions/irg-partner-safe-merge/artifacts/task-1-report.md` with files created, RED/GREEN evidence, commands/results, deviations and remaining risks. Do not commit.
