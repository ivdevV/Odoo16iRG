# Code review brief — irg-tfm-delivery-review-gradebook

Read-only. Do not mutate the worktree, index, HEAD or branches.

## Checkout

- Worktree: `C:/tmp/Odoo16iRG-tfm-review-gradebook`
- Branch: `codex/tfm-review-gradebook`
- Base commit: `1701cfe9b` (`fix(tfm): load answer list order field`)
- Head: uncommitted working tree (no commit authorized)

## Scope to review (production + tests only)

Review only `addons-extra/extrairg/irg_tfm_convocatorias/` (models, views, controllers, security, tests, manifest).

Do **not** review `plan.md`, `execution.md`, `verification.json`, changelogs, README or knowledge docs unless they contain executable product code.

## Requirements

Primary spec: `docs/superpowers/specs/2026-09-14-tfm-delivery-review-gradebook-design.md`

Implementation plan (Tasks 2–6): `docs/superpowers/plans/2026-09-14-tfm-delivery-review-gradebook.md`

Global constraints that bind this review:

- Extend only `irg_tfm_convocatorias`; do not modify native/OCA/OpenEduCat/upstream addons.
- `irg.tfm.entrega` attachment history stays immutable.
- TFM subject resolves only through Canal TFM family and `op.subject.slide_channel_id`; never names/codes/`limit=1`.
- Score scale: finite `0` or `1..10`; reject transforming gradebook/template policy.
- Reviewer writes require `group_tfm_reviewer` server-side.
- Portal reads prove ownership before `sudo()`; no portal ACL on review/gradebook models.
- Public context/defaults/client links are untrusted. Reserved sync/defer context is rejected at public `create/write`.
- Lock order before mutation: enrollment → thesis → gradebook student → subject line → existing results; IDs ascending per phase; invalidate and re-resolve after locks.
- Narrow `sudo` only after actor ACL/rules/group checks.
- Linked identity parents reject reassignment/deletion, including One2many/cascade routes.
- Each paired operation is one savepoint; inverse path must not call public `tesis.model.create/write`.
- Inverse primitive is private, savepoint-bound, original-actor + verified-link explicit.
- Docker is prohibited; runtime Odoo tests and two-cursor concurrency are not executed. Do not treat missing Docker evidence as a code defect. Static contracts + written TransactionCase/HttpCase tests are the available proof. Label runtime-only gaps as limitations, not merge blockers, unless the production code itself is missing the contract.

## What was implemented

1. `irg.tfm.entrega.revision` with reviewer-only ACL, no unlink, server-owned `reviewed_by`/`reviewed_at`.
2. Backend review form/button and portal read-only feedback after owned-thesis resolution.
3. Forward coordinator: `points_fin` → linked `app.gradebook.result.scoring_total`.
4. Reverse coordinator: gradebook exam create/write → `points_fin`, plus linked-identity guards on result, line, gradebook student, admission, enrollment and thesis.

## Output

Write the full review to:

`missions/irg-tfm-delivery-review-gradebook/artifacts/code-review.txt`

Use this structure:

### Strengths
### Issues
#### Critical (Must Fix)
#### Important (Should Fix)
#### Minor (Nice to Have)
### Recommendations
### Assessment
**Ready to proceed to Validation?** Yes | No
**Blocking findings open?** Yes | No

Return in chat only: status, counts of Critical/Important/Minor, and the Assessment lines.
