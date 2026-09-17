# Execution log

## 2026-09-14 — Plan

- Classified the feature as `complex`: it crosses a new audited model, ACLs,
  portal QWeb, reviewer UI, gradebook hooks, concurrency and existing data.
- Created isolated worktree `C:/tmp/Odoo16iRG-tfm-review-gradebook` on branch
  `codex/tfm-review-gradebook`, based on `origin/Dev_iRG` `1701cfe9b`.
- Confirmed `irg_tfm_convocatorias` already depends on `isep_gradebook` and
  owns the canonical HomeClass/Online TFM channel-family resolver.
- Confirmed `op.subject.slide_channel_id` is the canonical bridge between an
  OpenEduCat subject and its eLearning channel.
- User approved the architecture and bidirectional grade synchronization.
- Wrote and self-reviewed the design and implementation plan.
- No production code, commit, push, PR, Docker or TestSprite action performed.

## 2026-09-14 — Security gate, pass 1

- Independent Security Advisor reviewed authorization, portal ownership,
  relationship integrity, concurrency, rollback and historical-data behavior.
- Result: `[NO]`; implementation remains blocked until the architecture is
  amended and approved on a fresh pass.
- Required amendments: never trust context for authorization, acquire a common
  lock hierarchy before mutations, protect all identity-bearing parent
  relationships, reject gradebook configurations that transform the TFM grade,
  place paired writes in an explicit savepoint, and add narrow sudo plus audit.
- Evidence: `artifacts/security-review.txt`.

## 2026-09-15 — Security gate, pass 2

- The amended contract resolved the initial findings but retained two stale
  instructions: an inverse-sync example calling the public thesis boundary with
  reserved context and `sudo`, and wording that could suppress failures during
  first TFM result adoption.
- Result: `[NO]`; a scoped documentation fix was returned to the plan author.
- No production code changed.

## 2026-09-15 — Security gate, pass 3

- Scoped independent re-review confirmed both residual findings addressed.
- Result: `[YES]`; production implementation may begin under the amended
  contract.
- Runtime semantics remain subject to independent validation; Docker and
  TestSprite remain prohibited.

## 2026-09-15 — Security-plan amendment

- Amended the design, implementation plan and mission gate; no functional code
  or runtime configuration changed.
- Made public context/default values and client supplied links explicitly
  untrusted, including `tesis.model.create()`. Context is now specified only as
  a private anti-recursion/defer marker after authorization, never as authority.
- Required original-actor authorization before narrow `sudo`, a single lock
  hierarchy (`enrollment → thesis → gradebook → line → existing results`),
  post-lock invalidation/re-resolution and compatibility with current hooks.
- Added server-side identity guards for result and parent relationships,
  finite `0` or `1..10` validation, atomic rejection of score normalization,
  whole-operation savepoints, rollback assertions and thesis-chatter audit.
- Expanded RED/static/runtime-future tests, including forged contexts/links,
  captured-error no-partial-state checks and two-cursor scenarios. Docker and
  TestSprite were not run and remain prohibited; no commit, push or PR occurred.
- The Security Advisor pass remains `[NO]`; a fresh independent `[YES]` is the
  next mandatory gate before production implementation.

## 2026-09-15 — Task 3 reviewer backend interface

- Confirmed the Task 3 RED with the static validator: the reviewer view,
  manifest ordering, delivery tree action/summary fields and `points_fin`
  reviewer restriction were absent.
- Added the readonly review form with editable `state`/`comment`, reviewer-only
  delivery action and summaries, and the inherited `points_fin` group guard.
  Kept `irg_tfm_submission_ids` readonly with create/delete disabled.
- Registered the review view after security and before `tesis_model_views.xml`.
- Added the One2many readonly assertion to the view-contract test.
- Static validator GREEN: 13 contracts passed; all 12 TFM XML files parsed;
  `git diff --check` passed. Odoo tests, Docker and TestSprite were not run per
  the explicit mission restriction. No commit, push or PR performed.

## 2026-09-15 — Task 3 fix round 1

- Added RED contracts for exact reviewer button text and stage visibility,
  readonly identity fields, tree/form create-delete flags, compatible delivery
  columns and deferred `points_fin` XPath.
- Added readonly related/display fields for attachment, student and version;
  hardened the button and form; updated the existing delivery-tree column
  assertion; removed the Task 3 `points_fin` XPath for Task 5.
- GREEN: static validator passed 15 contracts, 12 XML files parsed and
  `git diff --check` passed. Odoo tests, Docker and TestSprite remain skipped by
  explicit restriction; no commit, push or PR performed.

## 2026-09-16 — Task 5 deterministic forward grade sync

- Wrote runtime contracts and a failing static Task 5 gate before production;
  the initial RED listed seven absent contracts, including deterministic
  resolution, lock/savepoint handling, exact-score policy, stable link,
  authorization and audit.
- Implemented the private forward coordinator, server-owned result link,
  reviewer-only public thesis boundary and scoped `points_fin` view XPath.
- Self-review found and fixed under new RED contracts: exact batch identity in
  derived enrollment refresh, and post-`super().write()` identity revalidation
  before result propagation.
- Expanded runtime contracts for forged sync/defer/default-link inputs across
  thesis/result create/write and reviewer/internal/portal/gradebook actors.
- Final GREEN: 8 Task 5 static contracts, 29 Python AST files, 12 XML files,
  explicit XML parse, external-cache `compileall` and `git diff --check` pass.
- Odoo ORM tests and two-cursor concurrency remain unexecuted because Docker is
  prohibited. TestSprite was not used. No commit, push or PR performed.

## 2026-09-16 — Task 5 I-A fix (post-mutation rollback test)

- Re-review I-A: `test_post_hook_score_discrepancy_rolls_back_all_mutations`
  injected SQL after ORM write without flushing; coordinator
  `invalidate_recordset(..., flush=True)` overwrote the injection so
  `assertRaises(ValidationError)` never fired.
- TDD RED: added `flush_recordset` to Task 5 runtime contract in
  `static_validator.py`; validator failed on
  `runtime_contracts_cover_resolution_security_atomicity_and_audit`.
- TDD GREEN: added `records.flush_recordset(['scoring_total'])` in the patch
  wrapper before the raw SQL injection; static validator passed 11 Task 5
  contracts.
- Commands:
  `python missions/irg-tfm-delivery-review-gradebook/artifacts/static_validator.py`
  (RED exit=1, GREEN exit=0);
  `python -X pycache_prefix=C:\Users\admin\AppData\Local\Temp\tfm-grade-task5-pycache -m compileall addons-extra/extrairg/irg_tfm_convocatorias`
  (exit=0). No Docker, TestSprite, commit, push or PR.

## 2026-09-16 — Task 6 reverse synchronization and link protection

- `task-6-context.md` does not exist in the mission folder; the earlier-task
  interfaces were derived from `task-5-report.md`, `task-5-rereview-2.md` and
  the Task 5 code itself. Reported as a concern, not guessed.
- TDD RED: wrote the reverse-sync and parent-guard runtime tests plus six Task 6
  static contracts before any production change. Validator exit=1 with
  `Failed contracts: ['reverse_boundary_authorizes_the_proposed_parent_before_super',
  'reverse_coordinator_reuses_task_5_resolution_locks_and_reread',
  'inverse_primitive_is_savepoint_bound_super_scoped_and_never_public',
  'linked_identity_is_locked_and_protected_on_every_parent',
  'reverse_audit_keeps_actor_and_server_computed_gradebook_origin']`.
  `runtime_contracts_cover_reverse_sync_and_parent_guards` passed from the start
  because the tests are the RED artifact.
- Hardened the contract helper `ordered()` to scan forward instead of using the
  first occurrence of each term, so a repeated anchor cannot satisfy an order
  check. Re-ran the validator: the same five contracts still failed (exit=1).
- Implemented: reverse candidate lookup and parent authorization at the public
  result boundary; private reverse coordinator for `create`/`write` reusing the
  Task 5 resolver, normalization policy, lock order and post-lock reread; the
  savepoint-bound inverse primitive
  `_irg_tfm_apply_inverse_from_verified_gradebook`; `origen=gradebook` audit with
  the original actor as message author; and linked-identity guards on result,
  line, gradebook, admission, enrollment and thesis, each locking the hierarchy
  before checking for a link.
- Self-review found and fixed two real defects: an already linked result was
  ignored when the Canal TFM configuration disappeared (it is now always a
  candidate, so the pair can only be rejected, never silently drift), and the
  reverse audit reported the post-mutation gradebook value as the previous one
  (the pre-mutation score is now captured under lock, with `sin resultado` for a
  first-time creation).
- Two Task 5 tests encoded the pre-Task-6 behavior and were updated: the
  `_create_exam` fixture now builds an unlinked historical row through the
  super-scoped business helper, and
  `test_public_result_create_returns_clean_context_and_link_write_is_rejected`
  now asserts the server-computed link instead of its absence, keeping both
  original security assertions.
- TDD GREEN: 6 Task 6 static contracts, 11 Task 5 contracts, 32 Python AST
  files, 12 XML files, style, `compileall` (external pycache prefix) and
  `git diff --check` all pass.
- Commands:
  `python -X pycache_prefix=C:\Users\admin\AppData\Local\Temp\tfm-grade-task6-pycache missions/irg-tfm-delivery-review-gradebook/artifacts/static_validator.py`
  (RED exit=1, GREEN exit=0);
  `python -X pycache_prefix=C:\Users\admin\AppData\Local\Temp\tfm-grade-task6-pycache -m compileall -q addons-extra/extrairg/irg_tfm_convocatorias missions/irg-tfm-delivery-review-gradebook/artifacts`
  (exit=0); `git diff --check` (exit=0, only pre-existing LF→CRLF warnings).
- Odoo ORM tests, ACL, PostgreSQL locking and the two-cursor concurrency matrix
  remain unexecuted: Docker is prohibited on this machine. TestSprite was not
  used. HEAD stayed at `1701cfe9b`; no commit, push or PR.

## 2026-09-16 — Independent Review (Tasks 2-6)

- Reviewer distinct from the Task 6 coder. Artifact:
  `artifacts/code-review.txt`.
- Verdict: not ready for Validation. Blocking: C1 plus I1, I2, I3.
- C1 verified against Odoo 16.0 `odoo/fields.py:4438-4441`
  (`comodel.create(to_create)` with a list) and isep_gradebook's editable
  `gradebook_result_ids` tree. I1-I3 verified in production source.
- Minors M1-M8 recorded, not blocking. Docker absence not counted as a defect.

## 2026-09-16 — Review-fix pass (C1, I1, I2, I3)

- TDD RED: added runtime tests and four static contracts; validator exit=1
  with `result_create_is_model_create_multi_and_list_safe`,
  `combined_course_and_convocation_write_is_rejected_before_locks`,
  `mixed_tfm_and_ordinary_result_writes_are_rejected`,
  `link_guard_scope_matches_exact_enrollment_triples`.
- GREEN: `app.gradebook.result.create` is `@api.model_create_multi` and
  processes each payload; `tesis.model.write` rejects combined
  `course_id`+`irg_tfm_convocation_id` before locks; mixed TFM/ordinary
  result writes are rejected; link-guard admission expansion uses exact
  enrollment triples.
- Commands:
  `python missions/irg-tfm-delivery-review-gradebook/artifacts/static_validator.py`
  (RED exit=1, GREEN exit=0, 4 review-fix contracts);
  `python -X pycache_prefix=%TEMP%\tfm-grade-review-fix-pycache -m compileall -q addons-extra/extrairg/irg_tfm_convocatorias missions/irg-tfm-delivery-review-gradebook/artifacts`
  (exit=0). Docker, TestSprite, commit, push and PR were not used.

## 2026-09-16 — Review-fix pass (I4)

- Re-review of C1/I1/I2/I3 accepted those four and opened Important I4:
  `flush_ordinary()` in `app.gradebook.result.create` refreshed without
  `locked_enrollments` after a TFM coordinator already held phases 1–6, so
  `create([{tfm},{ordinary}])` took a phase-1 `op_student_course` lock last.
- TDD RED: contract `ordinary_create_locks_enrollments_before_tfm_candidates`
  plus `test_one2many_create_list_tfm_before_ordinary_still_links` with two
  distinct enrollments and input order `[{tfm},{ordinary}]`. Validator exit=1,
  only that contract failed.
- GREEN: public `create` classifies the list with no side effects, creates and
  refreshes every ordinary payload first, then dispatches TFM candidates, and
  returns the recordset in original payload order via `created_by_index`.
  Restored `test_one2many_create_list_rejects_client_link_on_each_payload`.
- Commands:
  `python -X pycache_prefix=%TEMP%\tfm-grade-i4-pycache missions/irg-tfm-delivery-review-gradebook/artifacts/static_validator.py`
  (RED exit=1 I4 only; GREEN exit=0, 5 review-fix contracts);
  `python -X pycache_prefix=%TEMP%\tfm-grade-i4-pycache -m compileall -q addons-extra/extrairg/irg_tfm_convocatorias missions/irg-tfm-delivery-review-gradebook/artifacts`
  (exit=0); `git diff --check` (exit=0, only pre-existing LF→CRLF warnings).
- Docker, TestSprite, commit, push and PR were not used. HEAD stayed at
  `1701cfe9b`.

## 2026-09-16 — Independent Review (third pass, I4)

- Reviewer distinct from the I4 coder (same independent reviewer as passes 1–2).
  Artifact: `artifacts/code-review.txt`.
- Verdict: ready for Validation. Blocking: none. I4 resolved. C1/I1/I2/I3 still
  resolved. Security contract unchanged. New Minor M12 (non-ascending phase-1
  ids across independent reverse-create chains) recorded, not blocking.
- Docker absence not counted as a defect.

## 2026-09-16 — Independent Validation

- Independent validator reran the static validator (exit 0), external-pycache
  `compileall -q` (exit 0), explicit parsing of all 12 XML files (exit 0), and
  scoped `git diff --check` (exit 0; only LF-to-CRLF warnings).
- Confirmed HEAD `1701cfe9b5475c7c5eed82a65e3304477bc70e93` and branch
  `codex/tfm-review-gradebook`. Scoped Git status records uncommitted functional
  work relative to `1701cfe9b`; addon status was unchanged by validation.
- Odoo module and integration/concurrency tests were skipped because the user
  does not have Docker and explicitly prohibited starting, querying, or using
  Docker; `docker-compose.local.yml` and a disposable database were unavailable.
- E2E would be triggered by the views/QWeb/portal/controller scope, but
  TestSprite and Docker were explicitly prohibited, so `e2e_testsprite` was
  skipped. Evidence is under `artifacts/`; `verification.json` status is
  `passed` because all executed checks passed and every skip is justified.

## 2026-09-16 — Documentation

- README: revisión de entregas, sync de nota, R1 (examen TFM exige expediente
  activo) y procedimiento beta. Versión esperada `16.0.1.2.0`.
- Manifest `16.0.1.1.0` → `16.0.1.2.0`. Changelog de misión. Knowledge
  `irg_tfm_gradebook_sync.md` (One2many list-create, lock order, guardas de
  padre). Doc de módulo: secciones 7–8.
- M8 recorded as intentional: identity guards live in
  `op_admission.py`, `app_gradebook_student.py` and `app_gradebook_subject.py`.
- No production behaviour change after Validation other than the version string.
  Review/Validation were not reopened.
- Final bounded Git check: HEAD `1701cfe9b`, branch `codex/tfm-review-gradebook`,
  `git diff --check` exit 0 (LF→CRLF warnings only). No unrelated path staged.

## 2026-09-17 — Publicación autorizada (commit + push de feature)

- El usuario autorizó commit y push. El push de este paso es
  `origin/codex/tfm-review-gradebook`, no `origin/Dev_iRG`.
- Beta despliega la rama Dev (`Dev_iRG`); integrar ahí exige un OK explícito
  nuevo. No se hace merge ni push a `Dev_iRG` en este paso.

