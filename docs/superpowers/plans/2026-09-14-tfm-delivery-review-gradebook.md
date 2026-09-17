# TFM Delivery Review and Gradebook Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add reviewer feedback per immutable TFM delivery version and keep `tesis.model.points_fin` bidirectionally synchronized with the configured TFM subject in the student's gradebook.

**Architecture:** A new audited `irg.tfm.entrega.revision` model owns mutable reviewer feedback while `irg.tfm.entrega` remains immutable. A stable `irg_tfm_thesis_id` link on `app.gradebook.result` identifies the final TFM grade; deterministic resolvers follow `irg_tfm_channel_id` through its HomeClass/Online family to `op.subject.slide_channel_id`, then to the exact gradebook subject line.

**Tech Stack:** Odoo 16 ORM, Python, PostgreSQL constraints/row locks, XML backend views, QWeb portal templates, `HttpCase`, `TransactionCase`, `docker-compose.local.yml`, TestSprite E2E when Docker execution is authorized.

**Spec:** `docs/superpowers/specs/2026-09-14-tfm-delivery-review-gradebook-design.md`

## Global Constraints

- Extend only `addons-extra/extrairg/irg_tfm_convocatorias`; do not modify native, OCA, OpenEduCat, or pre-existing upstream addons.
- Keep `irg.tfm.entrega` attachment history immutable.
- Resolve the TFM subject only through the configured channel family and `op.subject.slide_channel_id`; never match names/codes or silently select the first candidate.
- Preserve 0 as “ungraded”; accepted final grades are 1 through 10 inclusive.
- All reviewer writes require `irg_tfm_convocatorias.group_tfm_reviewer` server-side.
- Portal reads must prove ownership before any `sudo()` traversal and grant no portal ACL to review or gradebook models.
- Treat every RPC context key, default and client-supplied relation as untrusted. Reserved sync/defer context is rejected at public `create/write` boundaries; it may only stop recursion inside a private coordinator that has already authorized the initiating actor. It must never authorize, grant `sudo`, disable a guard, or permit a relationship mutation.
- Before any business mutation, resolve, validate and acquire the complete common lock order: enrollment (`op.student.course`) → thesis → gradebook student → gradebook subject line → existing results; lock IDs ascending per phase, invalidate caches and resolve again. The subject line serializes creation/adoption when no result exists.
- Validate a finite score on both entries (`0` or `1..10`) and reject the entire operation when effective gradebook/template normalization rounds, clamps or otherwise transforms it. Read the effective values after hooks and require exact equality.
- Check the initiating actor's access/rules/group before any narrow `sudo`; protect all linked identity-bearing parents and indirect reassignment/deletion paths server-side. Each effective sync/link event must be auditable in the thesis chatter, and every paired operation is one savepoint with no suppressed integrity/validation error.
- Do not run Docker while the user's explicit prohibition remains active. Record runtime and E2E checks as justified skips and run the reproducible static checks instead.
- Do not commit, push, or open a PR without a separate explicit authorization for that exact action and scope.

## File Map

- Create `models/irg_tfm_entrega_revision.py`: persistent reviewer feedback, audit metadata, authorization and lifecycle invariants.
- Create `models/irg_tfm_grade_sync.py`: deterministic target resolution and bidirectional grade synchronization helpers.
- Modify `models/irg_tfm_entrega.py`: computed review summary and action opening the exact review.
- Modify `models/tesis_model.py`: trigger forward grade synchronization after `points_fin` writes.
- Modify `models/app_gradebook_result.py`: stable TFM link, reverse synchronization and link protection while preserving the existing progress trigger.
- Modify `models/__init__.py`: register the two focused model files.
- Modify `security/irg_tfm_security.xml` and `security/ir.model.access.csv`: reviewer-only record permissions and no-delete contract.
- Create `views/irg_tfm_entrega_revision_views.xml`: review form and action.
- Modify `views/tesis_model_views.xml`: review status, date and button per delivery; restrict editable final score to reviewers.
- Modify `views/tfm_portal_templates.xml`: show feedback beside the exact version.
- Modify `controllers/portal.py`: prepare review data only after owned-thesis resolution.
- Create `tests/test_tfm_delivery_reviews.py`: model, ACL and portal feedback regression tests.
- Create `tests/test_tfm_gradebook_sync.py`: channel-family resolution, grade synchronization and ambiguity tests.
- Modify `tests/__init__.py`: register new test modules.
- Modify `__manifest__.py`: load the new view and increment the addon version.
- Modify `README.md`: configuration, reviewer flow, student flow and test procedure.
- Create/update `missions/irg-tfm-delivery-review-gradebook/*`: execution log, evidence, changelog and final `verification.json`.

---

### Task 1: Mission bootstrap and mandatory security gate

**Files:**
- Create: `missions/irg-tfm-delivery-review-gradebook/plan.md`
- Create: `missions/irg-tfm-delivery-review-gradebook/execution.md`
- Create: `missions/irg-tfm-delivery-review-gradebook/artifacts/security-review.txt`

**Interfaces:**
- Consumes: approved design spec and repository `AGENTS.md`.
- Produces: approved security contract before production changes.

- [x] **Step 1: Record scope and acceptance criteria**

Write the mission plan with tier `complex`, required roles `orchestrator`, `security-advisor`, `codifier`, `reviewer`, `validator`, `e2e-tester`, and `documenter`, and these acceptance criteria:

```text
AC1 reviewer feedback is stored per immutable partial/final delivery version
AC2 only Revisor TFM can create or edit feedback; nobody can delete it
AC3 the owning student sees the published decision and comment in portal
AC4 Canal TFM -> channel family -> op.subject -> exact gradebook line is deterministic
AC5 points_fin and the linked gradebook result remain equal in both directions
AC6 missing/ambiguous configuration aborts atomically with an actionable error
AC7 no existing delivery, attachment or unrelated grade is rewritten on upgrade
```

- [ ] **Step 2: Dispatch the Security Advisor before implementation**

Ask the independent advisor to inspect portal ownership, ACLs, `sudo()` boundaries, row locks, one-to-one SQL constraints, link adoption, unlink/reassignment denial and rollback behavior. Require the final line:

```text
[YES] Reason: <why the implementation contract is safe>
```

Any `[NO]` blocks Task 2; amend the plan and request a fresh review.

- [x] **Step 2a: Incorporate security pass 1 before re-review**

The first pass returned `[NO]`. The amended specification and Tasks 2, 5, 6
and 7 now make context non-authoritative, actor checks pre-`sudo`, the full
lock hierarchy/re-read protocol, parent identity guards, exact-score policy,
savepoint rollback, thesis-chatter audit and review metadata invariants
testable requirements. This checkbox records only the planning amendment; it
does **not** approve implementation. Request a new independent verdict before
Task 2.

- [ ] **Step 3: Capture the gate**

Save the complete verdict to `artifacts/security-review.txt` and log the timestamp, reviewer and result in `execution.md`.

- [x] **Step 4: Verify the planning scope**

Run:

```powershell
git status --short -- docs/superpowers missions/irg-tfm-delivery-review-gradebook
```

Expected: only the approved spec, implementation plan and mission artifacts appear.

No commit is permitted at this checkpoint without a separate user authorization. Suggested future commit message: `docs(tfm): plan delivery reviews and grade sync`.

---

### Task 2: Reviewer feedback domain model and authorization

**Files:**
- Create: `addons-extra/extrairg/irg_tfm_convocatorias/models/irg_tfm_entrega_revision.py`
- Modify: `addons-extra/extrairg/irg_tfm_convocatorias/models/irg_tfm_entrega.py`
- Modify: `addons-extra/extrairg/irg_tfm_convocatorias/models/__init__.py`
- Modify: `addons-extra/extrairg/irg_tfm_convocatorias/security/irg_tfm_security.xml`
- Modify: `addons-extra/extrairg/irg_tfm_convocatorias/security/ir.model.access.csv`
- Create: `addons-extra/extrairg/irg_tfm_convocatorias/tests/test_tfm_delivery_reviews.py`
- Modify: `addons-extra/extrairg/irg_tfm_convocatorias/tests/__init__.py`

**Interfaces:**
- Consumes: `irg.tfm.entrega` immutable deliveries and `group_tfm_reviewer`.
- Produces: `irg.tfm.entrega.revision`, `irg.tfm.entrega.irg_tfm_review_id`, and `action_open_tfm_review()`.

- [ ] **Step 1: Write RED tests for state and immutability**

Add `TransactionCase` tests that create a partial delivery through `_irg_create_locked_submission()` and assert the wished-for API:

```python
review = self.env['irg.tfm.entrega.revision'].with_user(self.reviewer).create({
    'delivery_id': self.partial.id,
    'state': 'corrections',
    'comment': 'Corrige la metodología y vuelve a entregar.',
})
self.assertEqual(review.reviewed_by, self.reviewer)
self.assertTrue(review.reviewed_at)
self.assertEqual(self.partial.irg_tfm_review_id, review)
with self.assertRaises(ValidationError):
    review.with_user(self.reviewer).unlink()
```

Add separate assertions for duplicate reviews, `outline` stage, inactive thesis,
empty correction comment, delivery reassignment and a normal internal user
without the reviewer group. For `create` and `write`, forge `reviewed_by`,
`reviewed_at` (including `False`) and reserved context/default keys from an
internal and portal user; all must fail. Assert that only the private server path
stamps the original reviewer/time after validating stage and active thesis.

- [ ] **Step 2: Verify RED**

When runtime execution is authorized, run:

```powershell
docker compose -f docker-compose.local.yml run --rm odoo odoo --test-enable --stop-after-init -d odoo16irg_tfm_review_test -i irg_tfm_convocatorias --test-tags /irg_tfm_convocatorias:TestTfmDeliveryReview
```

Expected: failure because `irg.tfm.entrega.revision` does not exist. While Docker remains prohibited, extend the mission static validator first and capture a RED contract failure for the missing model, ACL and SQL constraint.

- [ ] **Step 3: Implement the minimal review model**

Implement:

```python
class IrgTfmEntregaRevision(models.Model):
    _name = 'irg.tfm.entrega.revision'
    _description = 'Revisión de entrega TFM'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    delivery_id = fields.Many2one(
        'irg.tfm.entrega', required=True, readonly=True, index=True,
        ondelete='restrict', tracking=True,
    )
    state = fields.Selection([
        ('pending', 'Pendiente de revisión'),
        ('corrections', 'Requiere correcciones'),
        ('approved', 'Aprobada'),
    ], required=True, default='pending', tracking=True)
    comment = fields.Text(tracking=True)
    reviewed_by = fields.Many2one('res.users', readonly=True, tracking=True)
    reviewed_at = fields.Datetime(readonly=True, tracking=True)

    _sql_constraints = [(
        'irg_tfm_review_delivery_unique', 'unique(delivery_id)',
        'Solo puede existir una revisión por versión de entrega.',
    )]
```

Override `create()` and `write()` to call `_irg_require_reviewer()` before any
elevated read or write; reject public reserved-context/default keys and every
client value for `reviewed_by`/`reviewed_at`; reject non-partial/final deliveries
and inactive theses in server code; prevent `delivery_id` changes; require a
stripped comment for `corrections`; and stamp the original user/time only inside
the private server path for published decisions. Override `unlink()` to always
raise `AccessError`. Record rules and readonly views are defense in depth, not
substitutes for these server-side checks.

On `irg.tfm.entrega`, add a non-stored computed Many2one `irg_tfm_review_id`, related display fields, and:

```python
def action_open_tfm_review(self):
    self.ensure_one()
    self.env['irg.tfm.entrega.revision']._irg_require_reviewer()
    if self.stage not in ('partial', 'final'):
        raise ValidationError(_('Solo se revisan entregas parciales o finales.'))
    review = self.irg_tfm_review_id
    if not review:
        review = self.env['irg.tfm.entrega.revision'].create({
            'delivery_id': self.id,
        })
    return {
        'type': 'ir.actions.act_window',
        'res_model': 'irg.tfm.entrega.revision',
        'res_id': review.id,
        'view_mode': 'form',
        'target': 'current',
    }
```

Grant reviewer read/create/write and deny unlink in CSV. Add a reviewer record rule restricted to reviews whose delivery belongs to an activated TFM thesis and whose stage is partial/final.

- [ ] **Step 4: Verify GREEN and regression scope**

Run the same targeted test or static contracts, then:

```powershell
python -m compileall addons-extra/extrairg/irg_tfm_convocatorias/models addons-extra/extrairg/irg_tfm_convocatorias/tests
git diff --check -- addons-extra/extrairg/irg_tfm_convocatorias
```

Expected: all targeted contracts pass; no whitespace errors.

No commit without explicit authorization. Suggested future commit message: `feat(tfm): add reviewer feedback per delivery`.

---

### Task 3: Reviewer backend interface

**Files:**
- Create: `addons-extra/extrairg/irg_tfm_convocatorias/views/irg_tfm_entrega_revision_views.xml`
- Modify: `addons-extra/extrairg/irg_tfm_convocatorias/views/tesis_model_views.xml`
- Modify: `addons-extra/extrairg/irg_tfm_convocatorias/__manifest__.py`
- Modify: `addons-extra/extrairg/irg_tfm_convocatorias/tests/test_tfm_delivery_reviews.py`

**Interfaces:**
- Consumes: Task 2 review fields and `action_open_tfm_review()`.
- Produces: reviewer form and per-version review button/status in the thesis record.

- [ ] **Step 1: Write RED view-contract tests**

Parse the XML views and assert that the delivery tree includes
`irg_tfm_review_state`, `irg_tfm_reviewed_at`, and an object button named
`action_open_tfm_review`; assert the review form contains only read-only delivery
identity plus editable `state` and `comment`. Assert `points_fin` is restricted
to `group_tfm_reviewer` in the inherited thesis view.

- [ ] **Step 2: Verify RED**

Run the targeted static validator. Expected: missing review view/action/button contracts.

- [ ] **Step 3: Implement the views**

Load `views/irg_tfm_entrega_revision_views.xml` after security and before
`tesis_model_views.xml`. Define a form with:

```xml
<form string="Revisión de entrega TFM" create="false" delete="false">
    <sheet>
        <group>
            <field name="delivery_id" readonly="1"/>
            <field name="state"/>
            <field name="comment" placeholder="Escribe la devolución para el alumno..."/>
            <field name="reviewed_by" readonly="1"/>
            <field name="reviewed_at" readonly="1"/>
        </group>
    </sheet>
    <div class="oe_chatter">
        <field name="message_follower_ids"/>
        <field name="activity_ids"/>
        <field name="message_ids"/>
    </div>
</form>
```

Extend the delivery tree with the two summary fields and the reviewer-only button.
Keep the One2many itself read-only so the upload history remains immutable.

- [ ] **Step 4: Verify GREEN**

Parse every module XML with `xml.etree.ElementTree`, run the view contracts and
`git diff --check` on the three view/manifest files.

No commit without explicit authorization. Suggested future commit message: `feat(tfm): expose delivery review workflow`.

---

### Task 4: Student portal feedback

**Files:**
- Modify: `addons-extra/extrairg/irg_tfm_convocatorias/controllers/portal.py`
- Modify: `addons-extra/extrairg/irg_tfm_convocatorias/views/tfm_portal_templates.xml`
- Modify: `addons-extra/extrairg/irg_tfm_convocatorias/tests/test_tfm_delivery_reviews.py`

**Interfaces:**
- Consumes: owned thesis resolution and `delivery.irg_tfm_review_id`.
- Produces: read-only review status/comment for the exact owned delivery version.

- [ ] **Step 1: Write RED HTTP tests**

Create two portal students and deliveries. Publish a correction for student A,
then assert A's `/campus/course/<course_id>/tfm` contains the decision/comment,
B's page does not, and no POST route or editable input exists for review fields:

```python
self.assertIn('Requiere correcciones', page_a.text)
self.assertIn('Corrige la metodología', page_a.text)
self.assertNotIn('Corrige la metodología', page_b.text)
self.assertNotRegex(page_a.text, r'name="(?:review_state|review_comment)"')
```

- [ ] **Step 2: Verify RED**

Run the `HttpCase` when authorized or the QWeb/static contract while Docker is
prohibited. Expected: feedback label/comment absent.

- [ ] **Step 3: Implement minimal portal rendering**

After `_irg_portal_owned_thesis()` succeeds, include review summaries in the
already-owned delivery records. In `tfm_submission_section`, render:

```xml
<div class="mt-2" t-if="delivery.irg_tfm_review_id">
    <span class="badge"
          t-att-class="'bg-warning text-dark' if delivery.irg_tfm_review_state == 'corrections' else ('bg-success' if delivery.irg_tfm_review_state == 'approved' else 'bg-secondary')">
        <t t-esc="dict(delivery.irg_tfm_review_id._fields['state'].selection).get(delivery.irg_tfm_review_state)"/>
    </span>
    <p t-if="delivery.irg_tfm_review_state != 'pending' and delivery.irg_tfm_review_id.comment"
       class="mb-1 mt-2" style="white-space: pre-wrap;">
        <t t-esc="delivery.irg_tfm_review_id.comment"/>
    </p>
</div>
<span t-else="" class="badge bg-secondary mt-2">Pendiente de revisión</span>
```

Prepare a server-side label mapping instead of calling arbitrary model methods
from QWeb if the final implementation needs translation-safe labels.

- [ ] **Step 4: Verify GREEN**

Run portal ownership tests/static contracts, parse QWeb XML and confirm that no
review mutation route or field is exposed.

No commit without explicit authorization. Suggested future commit message: `feat(tfm): show reviewer feedback in portal`.

---

### Task 5: Deterministic grade target and forward synchronization

**Files:**
- Create: `addons-extra/extrairg/irg_tfm_convocatorias/models/irg_tfm_grade_sync.py`
- Modify: `addons-extra/extrairg/irg_tfm_convocatorias/models/tesis_model.py`
- Modify: `addons-extra/extrairg/irg_tfm_convocatorias/models/app_gradebook_result.py`
- Modify: `addons-extra/extrairg/irg_tfm_convocatorias/models/__init__.py`
- Create: `addons-extra/extrairg/irg_tfm_convocatorias/tests/test_tfm_gradebook_sync.py`
- Modify: `addons-extra/extrairg/irg_tfm_convocatorias/tests/__init__.py`

**Interfaces:**
- Consumes: `slide.channel._irg_tfm_family_channels()`, exact `op.student.course`, and `app.gradebook.*` models.
- Produces: `_irg_tfm_resolve_grade_target()`, `_irg_tfm_sync_points_to_gradebook()`, and `app.gradebook.result.irg_tfm_thesis_id`.

- [ ] **Step 1: Write RED resolver tests**

Cover one HomeClass subject, one Online-family subject, and zero/multiple
candidates at every boundary. The happy-path contract is:

```python
target = thesis._irg_tfm_resolve_grade_target()
self.assertEqual(target, self.gradebook_subject)
```

The ambiguity tests must assert the exact actionable `ValidationError` messages
from the approved spec, not merely that an exception occurred.

- [ ] **Step 2: Write RED forward-sync tests**

Assert that `thesis.with_user(reviewer).write({'points_fin': 8.5})` creates one
exam result linked by `irg_tfm_thesis_id`, repeating the write updates rather
than duplicates it, 0 does not create a new result, a sole existing exam is
adopted, and multiple existing exams abort without changing `points_fin`.
Add creation-time cases (`tesis.model.create`) for explicit `points_fin` and
context/default values. Forge sync/defer context and `irg_tfm_thesis_id` in
thesis/result `create/write` as reviewer, ordinary internal, portal and
gradebook user: no client value may authorize propagation, bypass a relationship
guard or establish/adopt a link.

- [ ] **Step 3: Verify RED**

Run the targeted grade sync tests or static contracts. Expected: missing resolver,
missing link field and missing synchronization.

- [ ] **Step 4: Implement deterministic target resolution**

Add these methods on `tesis.model`:

```python
def _irg_tfm_resolve_subject(self):
    self.ensure_one()
    course = self.course_id.course_id
    channel = course.irg_tfm_channel_id
    if not channel:
        raise ValidationError(_('El curso no tiene configurado Canal TFM.'))
    family = channel.sudo()._irg_tfm_family_channels()
    subjects = course.subject_ids.filtered(
        lambda subject: subject.slide_channel_id in family
    )
    if len(subjects) != 1:
        raise ValidationError(_(
            'Debe existir una única asignatura del curso vinculada al Canal TFM.'
        ))
    return subjects
```

Resolve the gradebook by the exact enrollment's student/course/batch with a
two-record search and explicit cardinality check, then filter its
`gradebook_subject_ids` by the resolved subject and require exactly one.

Implement a private coordinator, not an RPC action, that records the initiating
user and checks the origin operation ACL/rules/group before a narrow `sudo`.
Inside one savepoint it resolves complete identity, validates finite score and
non-transforming template policy, gathers/locks rows in the global order,
invalidates/rebrowses, then resolves/revalidates before the first `super()`
business mutation. If re-resolution would require a preceding lock, abort; never
lock out of order or retry without a bound. Trace the gradebook normalization and
refresh MRO before choosing a defer point, preserving all existing `super()`
hooks.

- [ ] **Step 5: Implement stable link and forward sync**

Add on `app.gradebook.result`:

```python
irg_tfm_thesis_id = fields.Many2one(
    'tesis.model', string='Expediente TFM', index=True,
    copy=False, readonly=True, ondelete='restrict',
)
_sql_constraints = [(
    'irg_tfm_result_thesis_unique', 'unique(irg_tfm_thesis_id)',
    'El expediente TFM ya está vinculado a una calificación.',
)]
```

Implement `_irg_tfm_sync_points_to_gradebook()` only through the private
coordinator, with global locks, post-lock re-read, sole-exam adoption and
create/update of the calculated link. `irg_tfm_grade_sync_origin='thesis'` is
an internal recursion marker only, never an authorization exception. Call it for
`points_fin` in create or write, including same-value writes used to link
historical scores. A public thesis grade always requires Revisor TFM before
`sudo`; the private, already-authorized gradebook mirror may use field- and
record-scoped `sudo` after proving its exact link. Protect `survey_type`,
`gradebook_subject_id` and the link from client mutation, including `False`.
Before and after base/hook normalization require `math.isfinite(value)` and
`value == 0 or 1 <= value <= 10`; reject an effective template policy or reread
result that rounds, clamps or transforms the requested score.

- [ ] **Step 6: Verify GREEN and atomic rollback**

Run the targeted tests. Add a caller-caught error case (ambiguity, normalization
or integrity fault) that invalidates caches in the same transaction and proves
the old thesis/result/link/count/chatter state remains unchanged. Add audit
assertions for actor, server-calculated origin, before/after values and linked
result ID, with no duplicate message for a no-op/re-entrant write.

No commit without explicit authorization. Suggested future commit message: `feat(tfm): sync final grade to configured subject`.

---

### Task 6: Reverse synchronization and link protection

**Files:**
- Modify: `addons-extra/extrairg/irg_tfm_convocatorias/models/irg_tfm_grade_sync.py`
- Modify: `addons-extra/extrairg/irg_tfm_convocatorias/models/app_gradebook_result.py`
- Modify: `addons-extra/extrairg/irg_tfm_convocatorias/tests/test_tfm_gradebook_sync.py`

**Interfaces:**
- Consumes: Task 5 stable link/resolver and existing TFM gradebook progress hooks.
- Produces: `_irg_tfm_try_link_result()` and `scoring_total → points_fin` synchronization.

- [ ] **Step 1: Write RED reverse-sync tests**

Assert both paths:

```python
linked_result.write({'scoring_total': 9.0})
self.assertEqual(thesis.points_fin, 9.0)

new_result = self.env['app.gradebook.result'].create({
    'gradebook_subject_id': self.gradebook_subject.id,
    'survey_type': 'exam',
    'scoring_total': 7.5,
    'description': 'TFM',
})
self.assertEqual(new_result.irg_tfm_thesis_id, thesis)
self.assertEqual(thesis.points_fin, 7.5)
```

Also assert that ordinary subjects/results remain untouched, a second exam is
not silently linked, linked results cannot move to another subject or thesis,
and linked results cannot be deleted.
Cover linked-parent mutations: `survey_type`, result subject/link, subject
`op_subject_id` and gradebook student, gradebook student admission, enrollment
student/course/batch and thesis course; include direct writes, One2many commands
and deletion/cascade routes. Cover both entry points for `0`, `1`, `10`, valid
decimals, negatives, `0.5`, `10.1`, NaN and infinities, plus gradebook/template
rounding or clamping. Every caller-caught failure must leave grades, link,
result count and audit trail unchanged.

- [ ] **Step 2: Verify RED**

Run the focused tests/static contracts. Expected: gradebook writes do not update
the thesis and protection checks are absent.

- [ ] **Step 3: Implement reverse link discovery**

At the public boundary first reject forged sync/defer context and externally
supplied `irg_tfm_thesis_id` (including on `create`) and authorize the actor's
ACL/rules against the proposed parent before calling `super()`. The private
coordinator then acquires common locks and, after post-lock re-read, handles exam
results without a link:

1. resolve its gradebook student, subject, student/course/batch;
2. find the exact `op.student.course` and active `tesis.model`;
3. verify the result's subject channel belongs to that thesis course's TFM family;
4. link only when this is the sole exam on the line and the thesis has no other linked result.

Ignore only a result demonstrably unrelated to TFM: it is not an exam, or its
line is outside the configured Canal TFM family after the safe preliminary
lookup. Once it is a TFM candidate, do not suppress any authorization,
resolution/cardinality, scale, normalization, lock/re-read, integrity or
concurrency error during first-time selection, adoption or creation of its link;
propagate it through the savepoint. A record already linked also raises on any
invariant violation. Before linking, revalidate active thesis and the complete
enrollment/course/batch/channel/subject mapping under lock.

- [ ] **Step 4: Implement reverse value sync and protection**

On a linked result, or immediately after first-time selection/adoption/creation
has produced a verified link, invoke the private coordinator's super-scoped
inverse primitive inside the already-open savepoint:

```python
thesis._irg_tfm_apply_inverse_from_verified_gradebook(
    actor=initiating_user,
    verified_link=verified_link,
    value=result.scoring_total,
    sync_savepoint=sync_savepoint,
)
```

The primitive receives the already-authorized initiating actor and verified link
explicitly; it is not callable through RPC and must perform only the narrow,
field-scoped internal `sudo`/`super()` write permitted by the coordinator. It
must not call public thesis `create/write`, accept a context marker, or introduce
a context-based authorization exception. Reject server-side any effective
reassignment or deletion of a linked result or identity-bearing parent,
regardless of context, including `survey_type`, result subject/link, line
subject/student, admission/enrollment identity and thesis course. Lock parents
before checking for links, preserve `_irg_tfm_refresh_affected_enrollments()`,
and defer only that existing derived hook until the pair is normalized; never
skip validation, `super()` or refresh due to a public context key. Reread the
effective result, require exact equality, then post exactly one thesis-chatter
audit message with original actor, origin, before/after values and result
reference.

- [ ] **Step 5: Verify GREEN and no recursion**

Instrument the test with patched counters around the two sync helpers and assert
one forward and one reverse operation, not repeated recursion. Run all TFM module
tests/static contracts and `compileall`. Specify runtime-only two-cursor cases
with barriers/timeouts: thesis write vs gradebook write; two no-result creates;
adoption vs create; thesis creation vs activation; parent reassignment/delete vs
first link; and opposite-ID batches. Prove no deadlock/duplicate, post-lock
winner re-read and consistent grade/link/refresh state.

No commit without explicit authorization. Suggested future commit message: `feat(tfm): synchronize gradebook changes back to thesis`.

---

### Task 7: Integration, static validation and independent gates

**Files:**
- Create: `missions/irg-tfm-delivery-review-gradebook/artifacts/static_validator.py`
- Create: `missions/irg-tfm-delivery-review-gradebook/artifacts/static-validation.txt`
- Create: `missions/irg-tfm-delivery-review-gradebook/artifacts/code-review.txt`
- Create: `missions/irg-tfm-delivery-review-gradebook/artifacts/module-tests.txt`
- Create: `missions/irg-tfm-delivery-review-gradebook/artifacts/e2e-testsprite.txt`
- Create: `missions/irg-tfm-delivery-review-gradebook/verification.json`

**Interfaces:**
- Consumes: completed functional code and tests from Tasks 2–6.
- Produces: independent Review and Validation gates with machine-readable status.

- [ ] **Step 1: Build reproducible static contracts**

The validator must check model registration, manifest load order, ACL values,
SQL uniqueness, forbidden portal mutation routes, server-side group checks,
review metadata/stage/active-thesis guards, HomeClass/Online family resolution,
rejection of public sync/defer context and client links (including thesis
create), authorization-before-`sudo`, common lock order/post-lock re-read,
savepoint-without-suppression, finite-scale/no-transform checks, result/parent
relationship guards, deferred-hook preservation, chatter audit, QWeb feedback
rendering and explicit order-field loading in nested trees. It must label these
as static contracts, not runtime proof.

- [ ] **Step 2: Run local non-runtime validation**

Run:

```powershell
python missions/irg-tfm-delivery-review-gradebook/artifacts/static_validator.py
python -m compileall addons-extra/extrairg/irg_tfm_convocatorias
python -c "from pathlib import Path; import xml.etree.ElementTree as ET; [ET.parse(p) for p in Path('addons-extra/extrairg/irg_tfm_convocatorias').rglob('*.xml')]"
git diff --check -- addons-extra/extrairg/irg_tfm_convocatorias missions/irg-tfm-delivery-review-gradebook docs/superpowers
```

Expected: every command exits 0; persist concise output.

- [ ] **Step 3: Independent code review**

Dispatch a reviewer who did not implement the change. Review production code,
tests, security, data/configuration and runtime behavior only. Any blocking
finding returns to the codifier and requires a new Review and Validation cycle.

- [ ] **Step 4: Independent validation**

Dispatch a validator who does not edit production code. They rerun the static
commands. If Docker becomes authorized, they also run module tests through
`docker-compose.local.yml` against a disposable database, then run the
two-cursor scenarios from Task 6 with barriers/timeouts and clean all fixtures/
restore the service. Until then, runtime functional and concurrency checks are
skipped only with the explicit Docker-prohibition justification.

- [ ] **Step 5: Scope-triggered E2E**

Because controllers/QWeb/backend views changed, execute TestSprite only after
all earlier checks pass and only against the disposable local `8069` runtime.
Set `projectPath` to
`addons-extra/extrairg/irg_tfm_convocatorias`, never the repository root. If
Docker remains prohibited, record `skipped` with that exact user restriction.

- [ ] **Step 6: Emit verification.json**

Set `status` to `passed` only when no check failed and every skip has a non-empty
justification. Record base commit, branch, effective tier `complex`, commands,
results and evidence paths.

No commit without explicit authorization. Suggested future commit message: `test(tfm): cover delivery feedback and grade sync`.

---

### Task 8: Documentation and delivery preparation

**Files:**
- Modify: `addons-extra/extrairg/irg_tfm_convocatorias/README.md`
- Modify: `addons-extra/extrairg/irg_tfm_convocatorias/__manifest__.py`
- Create: `missions/irg-tfm-delivery-review-gradebook/CHANGELOG.md`
- Modify: `missions/irg-tfm-delivery-review-gradebook/execution.md`
- Modify: `missions/irg-tfm-delivery-review-gradebook/verification.json`
- Create only if reusable knowledge is discovered: `.agents/knowledge/odoo_development_modding/artifacts/irg_tfm_gradebook_sync.md`

**Interfaces:**
- Consumes: passed Review and Validation gates.
- Produces: administrator/reviewer/student instructions and a publication-ready exact diff.

- [ ] **Step 1: Document configuration**

Explain that each master course must have one **Canal TFM**, one course subject
whose `slide_channel_id` points to the HomeClass/Online family, one gradebook for
the exact student/course/batch and one matching gradebook subject line.

- [ ] **Step 2: Document reviewer and student tests**

Write the exact beta procedure: update module, open a partial delivery, publish
corrections, verify the comment as the student, set `points_fin`, inspect the TFM
subject result, then change that result and confirm `points_fin` changes back.

- [ ] **Step 3: Bump version and changelog**

Increment the manifest from `16.0.1.1.0` to the next compatible feature version
and record the new model, UI, portal feedback, grade link, permissions and known
runtime-test limitation.

- [ ] **Step 4: Final bounded repository check**

Run exact-path `git status --short`, `git diff --stat`, `git diff --check`, verify
mission artifacts agree with the final code, and confirm no unrelated file is
staged. Documentation-only corrections do not reopen Review/Validation; code or
runtime changes do.

- [ ] **Step 5: Request publication authorization**

Present the exact changed-file list, validation summary, skipped runtime/E2E
checks and suggested commit message. Ask separately for commit, then separately
for push to the named remote/branch. Do not infer either permission.
