"""Static contracts for the TFM delivery review and gradebook mission.

This validator intentionally imports neither Odoo nor the addon. Runtime ORM,
ACL and PostgreSQL behavior remain covered by the written Odoo tests and must
be executed later in the authorized disposable runtime.
"""

import ast
import csv
import re
from pathlib import Path
from xml.etree import ElementTree


REPO = Path(__file__).resolve().parents[3]
ADDON = REPO / "addons-extra/extrairg/irg_tfm_convocatorias"


def source(relative):
    return (ADDON / relative).read_text(encoding="utf-8-sig")


python_files = sorted(ADDON.rglob("*.py"))
for path in python_files:
    ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
print(f"PASS python_ast: {len(python_files)} files")

xml_files = sorted(ADDON.rglob("*.xml"))
for path in xml_files:
    ElementTree.parse(path)
print(f"PASS xml_well_formed: {len(xml_files)} files")

text_files = python_files + xml_files + sorted(ADDON.rglob("*.csv")) + [Path(__file__)]
trailing_whitespace = []
long_python_lines = []
for path in text_files:
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8-sig").splitlines(), 1
    ):
        if line.rstrip(" \t") != line:
            trailing_whitespace.append((path, line_number))
        if path.suffix == ".py" and len(line) > 119:
            long_python_lines.append((path, line_number, len(line)))
assert not trailing_whitespace, trailing_whitespace
assert not long_python_lines, long_python_lines
print("PASS style: no trailing whitespace or Python lines over 119 columns")

with (ADDON / "security/ir.model.access.csv").open(
    encoding="utf-8-sig", newline=""
) as stream:
    acl_rows = list(csv.DictReader(stream))
review_acl_rows = [
    row for row in acl_rows
    if row["model_id:id"] == "model_irg_tfm_entrega_revision"
]

delivery = source("models/irg_tfm_entrega.py")
review = source("models/irg_tfm_entrega_revision.py")
models_init = source("models/__init__.py")
tests = source("tests/test_tfm_delivery_reviews.py")
delivery_tests = source("tests/test_tfm_deliveries.py")
tests_init = source("tests/__init__.py")
security = source("security/irg_tfm_security.xml")
manifest = source("__manifest__.py")
thesis_views = ElementTree.parse(ADDON / "views/tesis_model_views.xml").getroot()
review_view_path = ADDON / "views/irg_tfm_entrega_revision_views.xml"
review_views = (
    ElementTree.parse(review_view_path).getroot()
    if review_view_path.is_file() else None
)
portal = source("controllers/portal.py")
portal_templates = ElementTree.parse(
    ADDON / "views/tfm_portal_templates.xml"
).getroot()


def delivery_tree(root):
    return root.find(".//field[@name='irg_tfm_submission_ids']/tree")


def review_form(root):
    return root.find(".//field[@name='arch']/form") if root is not None else None


submission_tree = delivery_tree(thesis_views)
revision_form = review_form(review_views)

contracts = {
    "review_model_and_sql_uniqueness": all(term in review for term in (
        "_name = 'irg.tfm.entrega.revision'",
        "_inherit = ['mail.thread', 'mail.activity.mixin']",
        "irg_tfm_review_delivery_unique",
        "unique(delivery_id)",
    )),
    "review_acl_is_reviewer_only_without_unlink": (
        len(review_acl_rows) == 1
        and review_acl_rows[0]["group_id:id"] == "group_tfm_reviewer"
        and [review_acl_rows[0][name] for name in (
            "perm_read", "perm_write", "perm_create", "perm_unlink"
        )] == ["1", "1", "1", "0"]
    ),
    "review_rule_is_narrow": all(term in security for term in (
        "model_irg_tfm_entrega_revision",
        "delivery_id.stage",
        "delivery_id.thesis_id.irg_tfm_activated_at",
        "group_tfm_reviewer",
    )),
    "review_server_authorization_and_immutability": all(term in review for term in (
        "def _irg_require_reviewer",
        "has_group('irg_tfm_convocatorias.group_tfm_reviewer')",
        "def create(self, vals_list)",
        "def write(self, vals)",
        "def unlink(self)",
        "('partial', 'final')",
        "irg_tfm_activated_at",
        "if 'delivery_id' in vals",
    )),
    "review_metadata_is_server_owned": all(term in review for term in (
        "_RESERVED_REVIEW_CONTEXT_KEYS",
        "'reviewed_by', 'reviewed_at'",
        "def _irg_create_server_review",
        "def _irg_write_server_review",
        "reviewed_by=actor.id",
        "reviewed_at=fields.Datetime.now()",
    )),
    "delivery_review_interface_is_registered": all(term in delivery for term in (
        "irg_tfm_review_id = fields.Many2one",
        "irg_tfm_review_state = fields.Selection",
        "irg_tfm_reviewed_at = fields.Datetime",
        "def action_open_tfm_review",
    )) and all(term in review for term in (
        "attachment_id = fields.Many2one(",
        "related='delivery_id.attachment_id'",
        "student_id = fields.Many2one(",
        "related='delivery_id.thesis_id.course_id.student_id'",
        "version = fields.Integer(",
        "related='delivery_id.version'",
    )) and all(term in models_init for term in (
        "from . import irg_tfm_entrega",
        "from . import irg_tfm_entrega_revision",
    )) and "from . import test_tfm_delivery_reviews" in tests_init,
    "delivery_summary_uses_exact_narrow_elevation_without_review_link_leak": all(
        term in delivery for term in (
            "def _compute_irg_tfm_review_summary",
            "self.env['irg.tfm.entrega.revision'].sudo().search_read",
            "('delivery_id', 'in', self.ids)",
            "fields=['delivery_id', 'state', 'reviewed_at']",
            "can_read_review = self.env.su or self.env.user.has_group(",
            "Review.browse(values['id']) if can_read_review and values else False",
            "delivery.irg_tfm_review_state = values.get('state') or False",
            "delivery.irg_tfm_reviewed_at = values.get('reviewed_at') or False",
        )
    ),
    "delivery_summary_cache_is_partitioned_by_uid": (
        "@api.depends_context('uid')\n    def _compute_irg_tfm_review_summary" in delivery
        and all(term in tests for term in (
            "test_review_link_cache_is_isolated_for_internal_and_reviewer_in_both_orders",
            "((self.internal_user, False), (self.reviewer, review))",
            "((self.reviewer, review), (self.internal_user, False))",
            "self.partial.invalidate_recordset(summary_fields)",
        ))
    ),
    "runtime_tests_cover_review_security_and_summary": all(term in tests for term in (
        "test_internal_user_reads_only_delivery_summary_without_review_acl",
        "self.assertFalse(delivery.irg_tfm_review_id)",
        "with_user(self.internal_user).search([])",
        "for actor in (self.internal_user, self.portal_user, self.reviewer)",
        "test_create_rejects_all_client_review_metadata_values",
        "test_write_rejects_all_client_review_metadata_values",
        "test_reserved_context_and_defaults_never_authorize_public_create_or_write",
    )),
    "reviewer_backend_views_are_registered_in_dependency_order": (
        "'views/irg_tfm_entrega_revision_views.xml'" in manifest
        and manifest.index("'security/ir.model.access.csv'")
        < manifest.index("'views/irg_tfm_entrega_revision_views.xml'")
        < manifest.index("'views/tesis_model_views.xml'")
    ),
    "delivery_tree_exposes_reviewer_summary_and_action": (
        submission_tree is not None
        and submission_tree.get('create') == 'false'
        and submission_tree.get('delete') == 'false'
        and {'irg_tfm_review_state', 'irg_tfm_reviewed_at'}.issubset(
            field.get('name') for field in submission_tree.findall('field')
        )
        and any(
            button.get('name') == 'action_open_tfm_review'
            and button.get('type') == 'object'
            and button.get('string') == 'Revisar entrega'
            and button.get('groups') == 'irg_tfm_convocatorias.group_tfm_reviewer'
            and button.get('attrs') == (
                "{'invisible': [('stage', 'not in', ['partial', 'final'])]}"
            )
            for button in submission_tree.findall('button')
        )
    ),
    "review_form_is_limited_to_reviewer_feedback": (
        revision_form is not None
        and revision_form.get('create') == 'false'
        and revision_form.get('delete') == 'false'
        and [field.get('name') for field in revision_form.findall('.//sheet//field')]
        == [
            'delivery_id', 'attachment_id', 'student_id', 'version', 'state', 'comment',
            'reviewed_by', 'reviewed_at',
        ]
        and all(
            revision_form.find(".//field[@name='%s']" % name).get('readonly') == '1'
            for name in ('delivery_id', 'attachment_id', 'student_id', 'version',
                         'reviewed_by', 'reviewed_at')
        )
        and revision_form.find(".//field[@name='state']").get('readonly') is None
        and revision_form.find(".//field[@name='comment']").get('readonly') is None
        and [field.get('name') for field in revision_form.findall(".//div[@class='oe_chatter']/field")]
        == ['message_follower_ids', 'activity_ids', 'message_ids']
    ),
    "reviewer_only_action_keeps_server_guard": (
        any(
            button.get('name') == 'action_open_tfm_review'
            and button.get('groups') == 'irg_tfm_convocatorias.group_tfm_reviewer'
            for button in submission_tree.findall('button')
        )
        and "def _irg_require_reviewer" in review
    ),
    "points_fin_is_visually_reviewer_only_in_the_inherited_sheet": any(
        xpath.get('expr') == "//sheet/group/group/field[@name='points_fin']"
        and xpath.find("attribute[@name='groups']") is not None
        and xpath.find("attribute[@name='groups']").text
        == 'irg_tfm_convocatorias.group_tfm_reviewer'
        for xpath in thesis_views.findall('.//xpath')
    ),
    "delivery_history_columns_remain_compatible": all(term in delivery_tests for term in (
        "'submitted_by', 'submitted_at', 'internal_exception',",
        "'irg_tfm_review_state', 'irg_tfm_reviewed_at',",
    )),
}

failed = [name for name, result in contracts.items() if not result]
if not failed:
    print(f"PASS task_2_and_3_contracts: {len(contracts)} contracts")

submission_template = portal_templates.find(
    ".//template[@id='tfm_submission_section']"
)
submission_xml = ElementTree.tostring(
    submission_template, encoding="unicode"
)
editable_submission_names = {
    element.get("name")
    for element in submission_template.findall(".//*[@name]")
}
tfm_page_source = portal[
    portal.index("    def tfm_page("):
    portal.index("    def tfm_outline_start(")
]
task_4_portal_contract = (
    tfm_page_source.index("_irg_portal_owned_thesis(")
    < tfm_page_source.index("self._page_values(thesis)")
    and "('delivery_id', 'in', deliveries.ids)" in portal
    and "fields=['delivery_id', 'state', 'comment']" in portal
    and "'delivery_reviews': delivery_reviews" in portal
    and "'review_state_labels': review_state_labels" in portal
    and "delivery_reviews.get(delivery.id)" in submission_xml
    and "review_state_labels.get(review.get('state'))" in submission_xml
    and "t-esc=\"review.get('comment')\"" in submission_xml
    and "t-raw=" not in submission_xml
    and "message_ids" not in submission_xml
    and {"review_state", "review_comment"}.isdisjoint(
        editable_submission_names
    )
    and not re.search(
        r"['\"][^'\"]*/review(?:/[^'\"]*)?['\"]", portal
    )
)
if not task_4_portal_contract:
    failed.append("task_4_portal_contract")
else:
    print(
        "PASS task_4_portal_contract: ownership-scoped allowlist, primitive "
        "payload, escaped readonly UI"
    )

grade_sync_path = ADDON / "models/irg_tfm_grade_sync.py"
grade_sync = (
    grade_sync_path.read_text(encoding="utf-8-sig")
    if grade_sync_path.is_file() else ""
)
gradebook_result = source("models/app_gradebook_result.py")
thesis_model = source("models/tesis_model.py")
grade_sync_tests = source("tests/test_tfm_gradebook_sync.py")

lock_phases = (
    "op_student_course",
    "tesis_model",
    "app_gradebook_student",
    "app_gradebook_subject",
    "app_gradebook_result",
)
lock_positions = [grade_sync.find('"%s"' % phase) for phase in lock_phases]
create_coordinator = (
    grade_sync[grade_sync.index("    def _irg_tfm_coordinate_forward_create"):]
    if "    def _irg_tfm_coordinate_forward_create" in grade_sync else ""
)
write_coordinator = (
    grade_sync[grade_sync.index("    def _irg_tfm_coordinate_forward_write"):]
    if "    def _irg_tfm_coordinate_forward_write" in grade_sync else ""
)
write_after_business_mutation = (
    write_coordinator[
        write_coordinator.index("result = self.with_user(actor)._irg_tfm_write_business"):
    ]
    if "result = self.with_user(actor)._irg_tfm_write_business" in write_coordinator
    else ""
)
write_post_mutation_reread = write_after_business_mutation.find(
    "_irg_tfm_reresolve_after_locks"
)
write_post_mutation_apply = write_after_business_mutation.find(
    "_irg_tfm_apply_forward_result"
)
public_create = thesis_model[
    thesis_model.index("    def create(self, vals_list):"):
    thesis_model.index("    def _irg_tfm_create_business")
]
public_write = thesis_model[
    thesis_model.index("    def write(self, vals):"):
    thesis_model.index("    def _irg_tfm_write_business")
]
task_5_contracts = {
    "deterministic_target_resolution": all(term in grade_sync for term in (
        "def _irg_tfm_resolve_subject",
        "channel.sudo()._irg_tfm_family_channels()",
        "course.subject_ids.filtered(",
        "limit=2",
        "def _irg_tfm_resolve_grade_target",
        "El curso no tiene configurado Canal TFM.",
        "Debe existir una única asignatura del curso vinculada al Canal TFM.",
        "No se encontró una única libreta para el alumno, curso y lote.",
        "La libreta no contiene una única línea para la asignatura TFM.",
    )),
    "coordinator_owns_savepoint_lock_order_and_reread": (
        all(position >= 0 for position in lock_positions)
        and lock_positions == sorted(lock_positions)
        and "with self.env.cr.savepoint():" in grade_sync
        and "ORDER BY id FOR UPDATE" in grade_sync
        and "invalidate_recordset" in grade_sync
        and "_irg_tfm_assert_same_identity" in grade_sync
        and create_coordinator.index("with self.env.cr.savepoint():")
        < create_coordinator.index("_irg_tfm_create_business")
        < create_coordinator.index("_irg_tfm_apply_forward_result")
        and write_coordinator.index("with self.env.cr.savepoint():")
        < write_coordinator.index("_irg_tfm_write_business")
        < write_coordinator.index("_irg_tfm_apply_forward_result")
        and write_post_mutation_reread >= 0
        and write_post_mutation_apply >= 0
        and write_post_mutation_reread < write_post_mutation_apply
    ),
    "score_is_finite_exact_and_never_normalized": all(term in grade_sync for term in (
        "math.isfinite",
        "value == 0 or 1 <= value <= 10",
        "effective != value",
        "result.scoring_total != value",
        "La escala, precisión o límites de la libreta transformarían la nota TFM;",
    )),
    "stable_server_owned_result_link": all(term in gradebook_result for term in (
        "irg_tfm_thesis_id = fields.Many2one(",
        "ondelete='restrict'",
        "irg_tfm_result_thesis_unique",
        "unique(irg_tfm_thesis_id)",
        "_irg_tfm_reject_public_relationship_values",
        "'survey_type', 'gradebook_subject_id', 'irg_tfm_thesis_id'",
    )),
    "public_thesis_boundary_authorizes_before_coordinator": all(
        term in thesis_model for term in (
            "_irg_tfm_reject_reserved_public_input",
            "_irg_tfm_require_grade_actor",
            "_irg_tfm_sync_points_to_gradebook",
        )
    ) and public_create.index("_irg_tfm_require_grade_actor") < public_create.index(
        "_irg_tfm_sync_points_to_gradebook"
    ) and public_write.index("_irg_tfm_require_grade_actor") < public_write.index(
        "_irg_tfm_sync_points_to_gradebook"
    ),
    "effective_persisted_defaults_cross_the_public_guards": all(
        term in thesis_model + gradebook_result + grade_sync_tests for term in (
            "default_get(['points_fin'])",
            "default_get(['irg_tfm_thesis_id'])",
            "values['points_fin'] = 0.0",
            "effective_values['irg_tfm_thesis_id'] = False",
            "return self._irg_tfm_create_business(prepared_vals)",
            "test_create_without_effective_grade_default_keeps_zero_without_sync",
            "test_personal_ir_default_points_requires_reviewer_before_thesis_create",
            "test_personal_ir_default_cannot_create_server_owned_result_link",
        )
    ),
    "internal_defer_token_never_escapes_create": all(
        term in gradebook_result + grade_sync_tests for term in (
            "caller_context.pop(_TFM_DEFER_GRADE_TRIGGER, None)",
            "self.with_context(caller_context).browse(created.ids)",
            "test_public_result_create_returns_clean_context_and_link_write_is_rejected",
            "assertNotIn('irg_tfm_defer_grade_trigger', result.env.context)",
        )
    ),
    "post_lock_reread_uses_immutable_complete_snapshot": all(
        term in grade_sync + grade_sync_tests for term in (
            "identity['fingerprint'] =",
            "before['fingerprint'] != after['fingerprint']",
            "self.env['op.subject'].sudo().invalidate_model",
            "self.env['slide.channel'].sudo().invalidate_model",
            "self.env['op.admission'].sudo().invalidate_model",
            "test_reread_rejects_changed_enrollment_and_admission_batch_from_snapshot",
            "test_reread_invalidates_every_course_subject_candidate",
        )
    ),
    "forward_sync_preserves_hooks_and_audits_original_actor": all(
        term in grade_sync + gradebook_result for term in (
            "def _irg_tfm_sync_points_to_gradebook",
            "def _irg_tfm_apply_forward_result",
            "_irg_tfm_refresh_affected_enrollments",
            "origen=thesis",
            "actor.id",
            "result.id",
        )
    ),
    "derived_refresh_keeps_exact_enrollment_batch_identity": all(
        term in gradebook_result for term in (
            "subject.gradebook_student_id.batch_id.id",
            "('batch_id', 'in', batch_ids)",
            "enrollment.batch_id.id",
        )
    ) and (
        "test_forward_refresh_is_scoped_to_the_exact_enrollment_batch"
        in grade_sync_tests
    ),
    "runtime_contracts_cover_resolution_security_atomicity_and_audit": all(
        term in grade_sync_tests for term in (
            "test_resolver_returns_the_only_homeclass_gradebook_subject",
            "test_resolver_returns_the_only_online_family_gradebook_subject",
            "test_resolver_rejects_zero_or_multiple_subjects_with_exact_message",
            "test_resolver_rejects_zero_or_multiple_gradebooks_with_exact_message",
            "test_resolver_rejects_zero_or_multiple_lines_with_exact_message",
            "test_forward_write_creates_then_updates_one_stable_link",
            "test_same_value_write_adopts_the_only_existing_exam",
            "test_create_with_context_default_grade_synchronizes_and_zero_requires_reviewer",
            "test_public_thesis_grade_requires_reviewer_even_with_forged_context",
            "test_reserved_sync_and_defer_context_is_rejected_on_all_public_boundaries",
            "test_linked_result_relationships_are_server_owned_even_when_value_is_false",
            "test_clamp_policy_is_rejected_without_partial_state",
            "test_post_hook_score_discrepancy_rolls_back_all_mutations",
            "UPDATE app_gradebook_result SET scoring_total",
            "flush_recordset",
            "test_rounding_policy_rolls_back_grade_link_count_and_audit",
            "test_audit_uses_original_actor_server_origin_values_and_stable_result",
        )
    ) and "from . import test_tfm_gradebook_sync" in tests_init,
}

failed_task_5 = [
    name for name, result in task_5_contracts.items() if not result
]
failed.extend(failed_task_5)
if not failed_task_5:
    print(f"PASS task_5_grade_sync_contracts: {len(task_5_contracts)} contracts")


def optional_source(relative):
    path = ADDON / relative
    return path.read_text(encoding="utf-8-sig") if path.is_file() else ""


def section(text, start, end=None):
    """Slice a source block tolerantly so a missing anchor fails, never crashes."""
    if start not in text:
        return ""
    begin = text.index(start)
    if end and end in text[begin:]:
        return text[begin:text.index(end, begin)]
    return text[begin:]


def ordered(text, *terms):
    """True when every term appears strictly after the previous occurrence."""
    cursor = 0
    for term in terms:
        position = text.find(term, cursor)
        if position < 0:
            return False
        cursor = position + len(term)
    return True


gradebook_subject = optional_source("models/app_gradebook_subject.py")
gradebook_student = optional_source("models/app_gradebook_student.py")
op_admission = optional_source("models/op_admission.py")
op_student_course = source("models/op_student_course.py")

result_create = section(
    gradebook_result, "    def create(self, vals_list):", "    def write(self, values):"
)
result_write = section(
    gradebook_result, "    def write(self, values):", "    def unlink(self):"
)
result_unlink = section(gradebook_result, "    def unlink(self):")
reverse_create_coordinator = section(
    grade_sync,
    "    def _irg_tfm_coordinate_reverse_create",
    "    def _irg_tfm_coordinate_reverse_write",
)
reverse_write_coordinator = section(
    grade_sync,
    "    def _irg_tfm_coordinate_reverse_write",
    "    def _irg_tfm_apply_reverse_result",
)
inverse_primitive = section(
    grade_sync,
    "    def _irg_tfm_apply_inverse_from_verified_gradebook",
    "    def _irg_tfm_audit_reverse",
)

task_6_contracts = {
    "reverse_boundary_authorizes_the_proposed_parent_before_super": (
        all(term in gradebook_result for term in (
            "def _irg_tfm_reverse_candidate_line",
            "def _irg_tfm_authorize_reverse_parent",
            "def _irg_tfm_create_business",
            "def _irg_tfm_write_business",
            "check_access_rule('read')",
        ))
        and ordered(
            result_create,
            "_irg_tfm_reject_untrusted_sync_context",
            "_irg_tfm_reject_public_relationship_values",
            "_irg_tfm_materialize_protected_create_defaults",
            "_irg_tfm_reverse_candidate_line",
            "_irg_tfm_authorize_reverse_parent",
            "_irg_tfm_sync_gradebook_to_points",
        )
        and ordered(
            result_write,
            "_irg_tfm_reject_untrusted_sync_context",
            "_irg_tfm_reject_public_relationship_values",
            "_irg_tfm_reverse_candidate_line",
            "_irg_tfm_authorize_reverse_parent",
            "_irg_tfm_sync_gradebook_to_points",
        )
    ),
    "reverse_coordinator_reuses_task_5_resolution_locks_and_reread": (
        all(term in grade_sync for term in (
            "def _irg_tfm_sync_gradebook_to_points",
            "def _irg_tfm_resolve_reverse_identity",
            "def _irg_tfm_reresolve_reverse_after_mutation",
            "def _irg_tfm_assert_same_mapping",
            "_irg_tfm_resolve_subject_for_enrollment(",
            "No se encontró una única matrícula para el alumno, curso y lote de la libreta.",
            "No se encontró un único expediente TFM activo para la matrícula de la libreta.",
        ))
        and ordered(
            reverse_create_coordinator,
            "with self.env.cr.savepoint():",
            "_irg_tfm_resolve_reverse_identity",
            "_irg_tfm_validate_normalization",
            "_irg_tfm_lock_identities",
            "_irg_tfm_reresolve_after_locks",
            "_irg_tfm_create_business",
            "_irg_tfm_reresolve_reverse_after_mutation",
            "_irg_tfm_apply_reverse_result",
            "_irg_tfm_refresh_affected_enrollments",
            "_irg_tfm_audit_reverse",
        )
        and ordered(
            reverse_write_coordinator,
            "with self.env.cr.savepoint():",
            "_irg_tfm_resolve_reverse_identity",
            "_irg_tfm_validate_normalization",
            "_irg_tfm_lock_identities",
            "_irg_tfm_reresolve_after_locks",
            "_irg_tfm_write_business",
            "_irg_tfm_reresolve_reverse_after_mutation",
            "_irg_tfm_apply_reverse_result",
            "_irg_tfm_refresh_affected_enrollments",
            "_irg_tfm_audit_reverse",
        )
    ),
    "inverse_primitive_is_savepoint_bound_super_scoped_and_never_public": (
        all(term in grade_sync for term in (
            "class _TfmSyncSavepoint",
            "def _irg_tfm_apply_inverse_from_verified_gradebook",
        ))
        and all(term in inverse_primitive for term in (
            "isinstance(sync_savepoint, _TfmSyncSavepoint)",
            "sync_savepoint.assert_open(self.env.cr)",
            "verified_link.irg_tfm_thesis_id != self",
            "_irg_tfm_write_business({'points_fin': value})",
        ))
        and not any(term in inverse_primitive for term in (
            "with_context",
            "_TFM_DEFER_GRADE_TRIGGER",
            "_TFM_GRADE_SYNC_ORIGIN",
            ".create(",
            "self.write(",
        ))
        and "_irg_tfm_apply_inverse_from_verified_gradebook" not in gradebook_result
    ),
    "linked_identity_is_locked_and_protected_on_every_parent": (
        all(term in grade_sync for term in (
            "_TFM_LINK_GUARD_LOCK_PHASES",
            '"op_admission"',
            "def _irg_tfm_link_guard_scope",
            "def _irg_tfm_assert_no_linked_identity",
            "def _irg_tfm_guard_linked_identity",
            "No se puede modificar ni eliminar la identidad de una calificación TFM ",
        ))
        and ordered(
            section(grade_sync, "    def _irg_tfm_assert_no_linked_identity"),
            "_irg_tfm_link_guard_scope",
            "_irg_tfm_lock_rows",
            "_irg_tfm_invalidate_identity",
            "_irg_tfm_link_guard_scope",
            "raise AccessError",
        )
        and "_irg_tfm_guard_linked_identity(self, 'unlink')" in result_unlink
        and all(
            "_irg_tfm_guard_linked_identity" in text
            for text in (
                gradebook_result,
                gradebook_subject,
                gradebook_student,
                op_admission,
                op_student_course,
                thesis_model,
            )
        )
        and all(term in gradebook_subject for term in (
            "'op_subject_id', 'gradebook_student_id'",
            "def write(self, values)",
            "def unlink(self)",
        ))
        and "'admission_id'" in gradebook_student
        and "'student_id', 'course_id', 'batch_id'" in op_admission
        and "'student_id', 'course_id', 'batch_id'" in op_student_course
        and "'course_id'" in section(
            thesis_model, "    def write(self, vals):", "    def _irg_tfm_write_business"
        )
        and all(term in models_init for term in (
            "from . import app_gradebook_subject",
            "from . import app_gradebook_student",
            "from . import op_admission",
        ))
    ),
    "reverse_audit_keeps_actor_and_server_computed_gradebook_origin": all(
        term in section(grade_sync, "    def _irg_tfm_audit_reverse") for term in (
            "origen=gradebook",
            "author_id=actor.partner_id.id",
            "uid=%(uid)s",
            "state['link_changed']",
        )
    ),
    "runtime_contracts_cover_reverse_sync_and_parent_guards": all(
        term in grade_sync_tests for term in (
            "test_reverse_write_on_linked_result_updates_points_fin",
            "test_reverse_create_links_and_synchronizes_the_only_exam",
            "test_forward_and_reverse_sync_run_once_each_without_recursion",
            "self.assertEqual(counters, {'forward': 1, 'reverse': 1})",
            "test_ordinary_subject_results_stay_outside_the_reverse_sync",
            "test_second_exam_is_not_silently_linked_on_the_tfm_line",
            "test_unlinked_exam_ambiguity_is_not_silently_linked_on_create",
            "test_linked_result_cannot_move_to_another_subject_or_thesis",
            "test_linked_result_cannot_be_deleted_through_any_route",
            "'gradebook_result_ids': [(2, linked.id)]",
            "'gradebook_subject_ids': [(2, self.gradebook_subject.id)]",
            "test_linked_parent_identity_reassignment_is_rejected_server_side",
            "test_reverse_entry_point_enforces_the_exact_tfm_scale",
            "test_reverse_rounding_policy_rolls_back_grade_link_count_and_audit",
            "test_reverse_clamp_policy_rolls_back_without_partial_state",
            "test_reverse_failure_caught_by_the_caller_changes_nothing",
            "test_reverse_audit_uses_original_actor_gradebook_origin_and_values",
            "test_reverse_sync_refreshes_the_derived_enrollment_hook_once",
            "test_one2many_create_list_links_tfm_exam_and_keeps_ordinary_row",
            "self.env['app.gradebook.result'].with_user(",
            ").create([",
            "test_one2many_create_list_tfm_before_ordinary_still_links",
            "test_one2many_create_list_rejects_client_link_on_each_payload",
            "test_course_and_convocation_cannot_be_written_together",
            "test_mixed_result_write_is_rejected_without_partial_state",
            "test_link_guard_scope_uses_exact_enrollment_triples",
        )
    ),
}

result_create_multi = section(
    gradebook_result,
    "    def create(self, vals_list):",
    "    def write(self, values):",
)
create_business = section(
    gradebook_result,
    "    def _irg_tfm_create_business",
    "    def _irg_tfm_write_business",
)
thesis_public_write = section(
    thesis_model,
    "    def write(self, vals):",
    "    def unlink(self):",
)
link_guard_scope = section(
    grade_sync,
    "    def _irg_tfm_link_guard_scope",
    "    def _irg_tfm_assert_no_linked_identity",
)

task_6_review_fix_contracts = {
    "result_create_is_model_create_multi_and_list_safe": (
        "@api.model_create_multi\n    def create(self, vals_list):" in gradebook_result
        and ordered(
            result_create_multi,
            "for values in vals_list",
            "_irg_tfm_reject_public_relationship_values",
            "_irg_tfm_materialize_protected_create_defaults",
            "_irg_tfm_reverse_candidate_line",
        )
        and "dict(values)" not in create_business
        and "super(" in create_business
        and ".create(vals_list)" in create_business
    ),
    "ordinary_create_locks_enrollments_before_tfm_candidates": (
        "flush_ordinary" not in result_create
        and "created_by_index" in result_create
        and ordered(
            result_create,
            "ordinary_vals",
            "_irg_tfm_create_business",
            "_irg_tfm_authorize_reverse_parent",
            "_irg_tfm_sync_gradebook_to_points",
        )
        and "test_one2many_create_list_tfm_before_ordinary_still_links"
        in grade_sync_tests
        and "self.assertNotEqual(self.enrollment.id, other['enrollment'].id)"
        in grade_sync_tests
    ),
    "combined_course_and_convocation_write_is_rejected_before_locks": (
        "Cambie la matrícula y la convocatoria TFM en operaciones separadas."
        in thesis_model
        and ordered(
            thesis_public_write,
            "'course_id' in vals",
            "'irg_tfm_convocation_id' in vals",
            "ValidationError",
            "_irg_tfm_guard_linked_identity",
        )
    ),
    "mixed_tfm_and_ordinary_result_writes_are_rejected": (
        "No se puede sincronizar un conjunto mixto de " in gradebook_result
        and "resultados TFM y no TFM; edítelos por separado." in gradebook_result
        and ordered(
            result_write,
            "candidate_records",
            "ValidationError",
            "_irg_tfm_sync_gradebook_to_points",
        )
    ),
    "link_guard_scope_matches_exact_enrollment_triples": (
        "in pairs" in link_guard_scope
        and ordered(
            link_guard_scope,
            "if enrollments:",
            "pairs = {",
            "enrollment.student_id.id",
            "enrollment.course_id.id",
            "enrollment.batch_id.id",
            "Admission.search([",
            ".filtered(",
            "in pairs",
        )
    ),
}

failed_task_6 = [
    name for name, result in task_6_contracts.items() if not result
]
failed.extend(failed_task_6)
failed_review_fix = [
    name for name, result in task_6_review_fix_contracts.items() if not result
]
failed.extend(failed_review_fix)
if failed:
    raise AssertionError(f"Failed contracts: {failed}")

print(f"PASS task_6_reverse_sync_contracts: {len(task_6_contracts)} contracts")
print(
    f"PASS task_6_review_fix_contracts: {len(task_6_review_fix_contracts)} contracts"
)
print("SUMMARY: static validation passed; 0 failed")
