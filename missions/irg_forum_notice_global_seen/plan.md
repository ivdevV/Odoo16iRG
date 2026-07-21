# IRG Forum Notice Global Seen

## Mission scope

Implement the approved design in a new Odoo 16 extension addon,
`addons-extra/extrairg/irg_forum_notice_global_seen/`, so a forum notice is
shown at most once per authenticated user, independently of the course through
which it was discovered.  The authoritative seen identity is
`(user_id, post_id)`.

The implementation is limited to the new addon and its tests, mission
artifacts, and the related documentation/changelog required after successful
review and validation.  Existing addons, including `irg_forum_notice_popup`,
native Odoo addons, and OCA addons, are read-only.  Existing legacy
`irg.forum.notice.seen` rows are read-only compatibility data: they are checked
by `(user_id, post_id)`, without migration, update, or deletion.

## Approved design and constraints

- New model: `irg.forum.notice.global.seen`, with a SQL uniqueness constraint
  on `(user_id, post_id)`.
- The model has direct ACL access only for `base.group_system`; portal and
  internal users use authenticated JSON routes.
- Republished routes must reject the public user, verify that the post exists,
  and call `post.sudo()._is_visible_for_user(request.env.user)` before a
  technical `sudo()` lookup or write.
- `sudo()` is restricted to the technical seen lookup/write; it cannot bypass
  post visibility authorization.
- Global seen services are private `_irg_is_seen` and `_irg_mark_seen` methods
  called only by trusted server code. Their leading underscore makes them
  non-RPC-callable through generic Odoo RPC.
- The new addon adds `security/forum_notice_seen_rules.xml` without modifying
  the legacy addon. It scopes legacy `irg.forum.notice.seen` rows for both
  `base.group_user` and `base.group_portal` to `[('user_id', '=', user.id)]`,
  while a `base.group_system` rule allows all rows; the manifest loads this XML
  before the new global-model ACL.
- `models/forum_notice_seen_legacy.py` inherits `irg.forum.notice.seen` and
  raises `AccessError` from `create`, `write`, and `unlink` unless `env.su` or
  `base.group_system` is present. This makes mutations route-only, prevents an
  owner from reassigning an owned row's `user_id`, and keeps reads user-scoped
  through the record rules.
- The global seen write is idempotent and concurrency-safe through the SQL
  constraint and savepoint-protected create.
- The replacement frontend asset uses `notice.id` as local identity, suppresses
  a notice while its request is in flight, waits for persistence before close or
  navigation, and logs failures without treating client state as authoritative.
- Existing forum, post, course, batch, and exclusion visibility behavior is
  preserved.  `course_id` may be used for discovery but never for seen identity.
- Odoo 16 APIs only; addon version `16.0.1.0.0`; all runtime checks use
  `docker-compose.local.yml` and the isolated test database
  `test_irg_forum_global_seen`.

## Acceptance criteria

1. A forum post is displayed no more than once to each authenticated user.
2. Users with zero, one, or multiple courses have consistent notice behavior.
3. Both closing and opening a notice persist its global seen state.
4. Any legacy seen row for the same user and post suppresses the notice,
   regardless of its stored course; legacy rows remain unchanged.
5. Course, batch, post, and forum visibility behavior remains unchanged.
6. Public users and users without visibility cannot mark a notice as seen.
7. Repeated or concurrent writes create no duplicate global seen rows.
8. No existing addon is modified.
9. Internal and portal users cannot forge another user's legacy or global seen
   state through direct ORM or generic RPC, and generic RPC rejects both
   private global-seen service methods.
10. Internal and portal users cannot directly create, write, unlink, or
    reassign even their own legacy seen row; trusted sudo paths and necessary
    system-administrator management remain functional.

## Tier and capacity

Mission level: `full`; capacity tier: `complex`.

Justification: the change spans more than five files and crosses persistent
data, Odoo model semantics, server-side authorization, controller routing,
frontend asynchronous behavior, visibility enforcement, and runtime tests.
It also needs explicit concurrency handling and backward-compatible reads of
legacy data.  This requires maximum available reasoning for implementation and
independent review/validation; it is not a simple or localized change.

## Required roles and gates

| Phase | Required owner | Gate |
| --- | --- | --- |
| Plan | Orchestrator | This mission scope is recorded before functional code. |
| Security review | Independent Security Advisor | Must approve authorization, ACL, `sudo()`, persistent data, and concurrency before production code. |
| Implementation/TDD | Codifier | Preserve RED evidence before the smallest production implementation, then GREEN. |
| Review | Independent reviewer | No unresolved blocking findings. |
| Validation | Independent validator | Re-run checks without editing production code; emit `verification.json`. |
| Documentation | Documenter | Starts only after review and validation pass. |
| Publication | Delivery owner | Commit, push, and PR each require separate explicit user authorization. |

The codifier, reviewer, and validator must be distinct people or agents. The
first two Security Advisor reviews identified public sudo-backed service,
legacy-row scope, and owner-row reassignment risks; the plan was amended for
each. The third independent re-review approved the final controls with
`[YES] Reason: ...`. The Security Advisor gate has passed and Task 2 is
authorized to begin under the remaining implementation, review, validation,
and publication gates above.

## Test, validation, and cleanup plan

- Capture the Task 2 failing model-registration test (RED) before importing the
  new model; preserve concise evidence in `artifacts/red-model.txt`.
- Run Odoo `TransactionCase` and `HttpCase` coverage for global identity,
  legacy compatibility, multi-course discovery, users with no effective course,
  concurrency/idempotence, public/inaccessible route rejection, and batch
  inclusion/exclusion visibility.
- Add negative ORM and generic-RPC tests for internal and portal users that
  attempt to forge another user's legacy/global state, and tests proving
  `_irg_is_seen` and `_irg_mark_seen` cannot be generic-RPC-called. Each
  rejected operation must leave target rows unchanged.
- Add direct-ORM tests that reject internal/portal legacy create, write, unlink,
  and owned-row `user_id` reassignment, plus positive sudo/service and system
  administrator controls.
- Run appropriate Python compilation, XML and CSV parsing, and frontend asset
  resolution checks.
- Run all Odoo-dependent checks through `docker compose -f
  docker-compose.local.yml` against `test_irg_forum_global_seen`.
- Clean up test fixtures and isolated test data, restore any service state
  altered for validation, and record concise cleanup/restoration evidence.  No
  shared environment may be left pointing to a worktree.

## Final-review security and concurrency amendment

The final review reopens Implementation/TDD for one coordinated fix wave.  The
replacement frontend must use only a static HTML skeleton, assign notice title,
forum and preview through `textContent`, and create its link only after accepting
a same-origin relative or absolute HTTP(S) URL.  Unsafe schemes and cross-origin
URLs must not produce an open link.

By explicit user scope decision, the runtime suite proves SQL uniqueness
recovery with two synchronized independent database transactions executing the
real model method; a second-server authenticated HTTP race is not required.
The suite also covers a non-system user linked to `op.student` with no effective
academic association through the real discovery and mark routes, and proves
non-unique integrity failures propagate.
Final static scope validation must compare porcelain status to an exact
allowlist, verify every declared compose service is running, and reject any
ephemeral run container or port.  These changes invalidate the earlier final
verification until a distinct validator regenerates `verification.json`.

## Knowledge and references consulted

- Approved implementation plan:
  `docs/superpowers/plans/2026-07-20-irg-forum-notice-global-seen.md`
- Approved design:
  `docs/superpowers/specs/2026-07-20-irg-forum-notice-global-seen-design.md`
- Forum visibility contract:
  `.agents/knowledge/odoo_development_modding/artifacts/forum_post_batch_visibility_controls.md`
- Modding rules:
  `.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`
- Project workflow:
  `.agents/workflows/odoo16_codebase_knowledge.md`
- Planned implementation references:
  `addons-extra/extrairg/irg_forum_notice_popup/controllers/main.py`,
  `addons-extra/extrairg/irg_forum_notice_popup/static/src/js/forum_notice_popup.js`,
  and `addons-extra/extrairg/irg_forum_batch_visibility/models/forum_post.py`.

## Out of scope

- Altering which forum posts qualify as notices.
- Email or follower notification behavior.
- A UI to inspect or reset seen notices.
- Migrating, modifying, or deleting legacy seen records.
- Changes to existing addons, native Odoo addons, or OCA addons.
