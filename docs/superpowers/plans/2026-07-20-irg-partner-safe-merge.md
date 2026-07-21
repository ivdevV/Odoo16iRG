# Implementation Plan: IRG Partner Safe Merge

> **Worktree:** `C:\tmp\Odoo16iRG-irg-partner-safe-merge`
>
> **Mission:** `missions/irg-partner-safe-merge/`
>
> **Rule:** do not commit, push, or open a PR. Those actions require separate user authorization.

## Goal

Implement the new Odoo 16 addon `irg_partner_safe_merge` exactly as defined by the approved micro-spec in `doc/micro-specs/2026-07-20-irg_partner_safe_merge.md`, without modifying existing addons or touching the unrelated diplomado work in the primary checkout.

## Constraints

- Use `apply_patch` for all source and documentation edits.
- Follow TDD: add automated tests first, record RED evidence, then implement the minimum production code and record GREEN evidence. If Docker remains unavailable, record the objective limitation before production edits and use the strongest executable static/unit substitute; the Odoo integration gate remains mandatory before completion.
- Never call the standard partner `_merge()`, never call `cr.commit()`, and never delete business records to resolve conflicts.
- Transfer only the closed allowlist from the micro-spec. Unknown references, bank/accounting/payment references, or semantic collisions must block atomically.
- Enforce `base.group_system` on the server for opening, preview, and confirmation. Never trust wizard input.
- Keep the audit immutable and merged-source protections server-side.
- Do not expose credentials or query/write the read-only mirror during implementation.

### Task 1: Implement and test the complete safe-merge addon

**Read first:**

- `AGENTS.md`
- `.agents/skills/odoo16_developer/SKILL.md`
- `missions/irg-partner-safe-merge/plan.md`
- `doc/micro-specs/2026-07-20-irg_partner_safe_merge.md`

**Create:**

- `addons-extra/extrairg/irg_partner_safe_merge/__init__.py`
- `addons-extra/extrairg/irg_partner_safe_merge/__manifest__.py`
- `addons-extra/extrairg/irg_partner_safe_merge/models/__init__.py`
- `addons-extra/extrairg/irg_partner_safe_merge/models/res_partner.py`
- `addons-extra/extrairg/irg_partner_safe_merge/models/merge_audit.py`
- `addons-extra/extrairg/irg_partner_safe_merge/wizard/__init__.py`
- `addons-extra/extrairg/irg_partner_safe_merge/wizard/partner_safe_merge_wizard.py`
- `addons-extra/extrairg/irg_partner_safe_merge/security/ir.model.access.csv`
- `addons-extra/extrairg/irg_partner_safe_merge/views/res_partner_views.xml`
- `addons-extra/extrairg/irg_partner_safe_merge/views/partner_safe_merge_wizard_views.xml`
- `addons-extra/extrairg/irg_partner_safe_merge/views/merge_audit_views.xml`
- `addons-extra/extrairg/irg_partner_safe_merge/tests/__init__.py`
- focused test modules under `addons-extra/extrairg/irg_partner_safe_merge/tests/`

**Implement:**

1. Add the installable addon and exact dependencies needed for Contacts, CRM, Sales, subscriptions, OpenEduCat students/admissions, gradebooks, website slides, mail, and the optional relations actually present in this repository. Optional absent models must be detected without forcing unavailable addons.
2. Extend `res.partner` with the protected `irg_merged_into_partner_id` marker, SQL/Python constraints preventing self/cycles, and server-side guards that reject direct marker mutation, reactivation, and deletion of merged sources. Permit marker mutation only through a private, narrowly scoped `sudo` service context.
3. Add immutable model `irg.partner.safe.merge.audit`, administrator-only read access, unique origin, JSON snapshots/decisions/actions, actor/date/master/origin, and create/write/unlink guards.
4. Add an admin-only contextual action for exactly two active personal contacts and a multi-step wizard that shows the recommendation reason, relation inventory, field conflicts, prevalidation status, and explicit final confirmation. The administrator may swap master/source.
5. Implement deterministic recommendation scoring in the approved priority order. Use metadata for discovery/blocking only; execute transfers solely through the static allowlist.
6. Normalize and validate identity, company and hierarchy; inventory Many2one, polymorphic, M2M, payment/accounting/bank and unknown references. Classify each approved relation as transfer/recalculate/conserve/union/block exactly as specified.
7. At confirmation, lock the two partners in ascending order and all planned dependent rows in stable order, rerun the complete preflight, compare a deterministic preview hash, and abort if anything changed.
8. Apply scalar choices and ORM transfers atomically, preserve four distinct leads, maintain user/student coherence, union categories/followers safely, transfer only direct `res.partner` polymorphic resources, recompute stored related gradebook/order fields, archive the source, and create the immutable audit last. Any exception must roll back the entire request.
9. Make repeat confirmation idempotent by returning the existing audit for the same archived source; block inverse/concurrent conflicting merges.
10. Keep user-facing validation messages actionable and translated with `_()`.

**Tests first (RED):**

- permissions and RPC tampering;
- exact-two, identity, hierarchy, company, archived/already-merged guards;
- recommendation by subscription/confirmed sale;
- scalar empty-copy and explicit conflicts;
- Camila-equivalent graph: one master, user/student moved, four leads distinct, two orders, two admissions, subscription schedule intact;
- unknown relation, bank/accounting/payment, duplicate user/student and business collisions block;
- category and follower subtype union without message/activity/attachment loss;
- preview hash change and stable locking behavior;
- injected exceptions after each mutation phase prove rollback;
- idempotent double confirmation and inverse merge;
- direct marker write, reactivation, deletion and audit mutation are rejected.

Run the first available focused test command before production code and append its command and failing reason to `missions/irg-partner-safe-merge/execution.md`. Do not weaken assertions to obtain GREEN.

**Verification during implementation:**

- Run Python compilation over the addon.
- Parse every XML and CSV file.
- Run the focused Odoo test tag through `docker-compose.local.yml` with an overlay mounting this worktree when Docker is available.
- Inspect `git diff --check` and `git status --short`.

**Report:**

Append a concise implementation report to `missions/irg-partner-safe-merge/artifacts/task-1-report.md` containing files created, RED/GREEN commands and results, design deviations (if any), remaining risks, and full verification output references. Do not commit.
