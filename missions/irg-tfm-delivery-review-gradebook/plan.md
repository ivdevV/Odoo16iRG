# Mission plan: TFM delivery review and gradebook sync

- **Tier:** complex.
- **Base:** `origin/Dev_iRG` at `1701cfe9b`.
- **Module:** `addons-extra/extrairg/irg_tfm_convocatorias`.
- **Approved specification:** `docs/superpowers/specs/2026-09-14-tfm-delivery-review-gradebook-design.md`.
- **Implementation plan:** `docs/superpowers/plans/2026-09-14-tfm-delivery-review-gradebook.md`.
- **E2E trigger:** yes; the planned diff changes backend XML, QWeb portal and controller-facing data.
- **Runtime restriction:** do not run Docker or TestSprite while the user's explicit Docker prohibition remains active.
- **Publication restriction:** commit, push and PR each require separate explicit authorization.

## Acceptance criteria

1. Reviewer feedback is stored per immutable partial/final delivery version.
2. Only Revisor TFM can create or edit feedback; reviews cannot be deleted.
3. The owning student sees each published decision/comment in the portal.
4. The TFM grade target resolves only through Canal TFM, its HomeClass/Online family, `op.subject.slide_channel_id` and the exact gradebook line.
5. `points_fin` and the linked `app.gradebook.result.scoring_total` remain equal in both directions.
6. Missing or ambiguous configuration aborts atomically with an actionable error.
7. Upgrade does not rewrite existing deliveries, attachments or unrelated grades.
8. Public context/default values and client-supplied links can never authorize,
   bypass validation or create/reassign a TFM link, including thesis creation.
9. The initiating actor is authorized before narrow `sudo`; review metadata is
   server-only and delivery stage plus active thesis are always revalidated.
10. Both directions acquire enrollment → thesis → gradebook → line → existing
    results locks before mutation, reread after locks and preserve existing hooks.
11. Linked result and all identity-bearing parents reject server-side mutation,
    reassignment and deletion, including indirect relation commands.
12. Both inputs accept only finite `0` or `1..10` and atomically reject a
    gradebook/template that rounds, limits or transforms the requested note.
13. Each pair is resolved, validated, locked and reread inside a savepoint; a
    caller-caught error leaves grades, links, rows and chatter unchanged.
14. Every effective propagation/adoption creates one thesis-chatter audit entry
    with original actor, calculated origin, before/after values and result ID.

## Required roles and gates

`orchestrator → security-advisor → codifier/TDD → reviewer → validator → e2e-tester when authorized → documenter → authorized publisher`.

The Security Advisor must return `[YES]` before production code changes. Review
and Validation must be independent from the codifier. `verification.json` must
be `passed` before requesting publication authorization. The current first-pass
`[NO]` remains blocking: this amendment is not an approval and a fresh `[YES]`
is required before Task 2 changes production code.

## Security-amendment implementation gates

1. Public `create/write/unlink` tests first prove rejection of forged context,
   defaults and links; the private coordinator is the only recursion mechanism.
2. Before the first business mutation it must authorize actor, resolve/validate,
   lock enrollment → thesis → gradebook → line → existing results by ascending
   ID per phase, invalidate/rebrowse, then revalidate. The line is always locked
   to serialize adoption/creation. Existing hooks are traced and deferred only
   after both sides are normalized.
3. The same savepoint covers resolution, checks, locks, both mutations, link,
   hook effects and thesis audit. Integrity/validation exceptions propagate.
4. Static checks cover order and guards; runtime validation later includes the
   documented two-cursor conflict matrix. Docker/TestSprite remain forbidden
   until separately authorized, and no publication action is authorized here.

## Knowledge consulted

- `.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`
- `.agents/knowledge/odoo_development_modding/artifacts/irg_admission_auto_gradebook_templates.md`
- `.agents/knowledge/odoo_development_modding/artifacts/irg_gradebook_auto_close.md`
- `.agents/knowledge/odoo_development_modding/artifacts/irg_qweb_hasattr_unsafe.md`
