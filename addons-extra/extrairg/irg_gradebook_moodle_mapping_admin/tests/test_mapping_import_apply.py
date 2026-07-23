import csv
import io
from dataclasses import replace
from unittest.mock import patch

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from ..services.mapping_import import (
    ActivityOperation,
    CourseOperation,
    ImportPlan,
    MappingImportService,
    SubjectOperation,
)
from .common import MappingAdminCommon


@tagged("post_install", "-at_install")
class TestMappingImportApply(MappingAdminCommon):
    def _plan(self, course_specs, subject_specs):
        return ImportPlan(
            courses=tuple(
                CourseOperation(
                    self.course.id,
                    self.course.name,
                    moodle_id,
                    name,
                )
                for moodle_id, name in course_specs
            ),
            subjects=tuple(
                SubjectOperation(
                    self.course.id,
                    self.course.name,
                    moodle_id,
                    subject.id,
                    subject.name,
                    subject.code,
                    course_name,
                    tuple(
                        ActivityOperation(activity_id, activity_name)
                        for activity_id, activity_name in activities
                    ),
                )
                for moodle_id, subject, course_name, activities in subject_specs
            ),
            summary={},
        )

    @staticmethod
    def _csv_payload(fieldnames, rows):
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(
            stream,
            fieldnames=fieldnames,
            delimiter=";",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
        return stream.getvalue().encode("utf-8-sig")

    def _analyzed_plan(self, moodle_course_id, activity_id):
        moodle_course_name = "Curso concurrente %s HomeClass" % moodle_course_id
        return MappingImportService(self.env).analyze_bytes(
            self._csv_payload(
                [
                    "Moodle Course ID",
                    "Odoo Course Name",
                    "Odoo Course ID",
                    "Nombre del Curso",
                ],
                [
                    {
                        "Moodle Course ID": str(moodle_course_id),
                        "Odoo Course Name": self.course.name,
                        "Odoo Course ID": str(self.course.id),
                        "Nombre del Curso": moodle_course_name,
                    }
                ],
            ),
            self._csv_payload(
                [
                    "Curso Nombre",
                    "Odoo Course ID",
                    "Moodle Course ID",
                    "Odoo Subject Name",
                    "Odoo Subject ID",
                    "Odoo Subject Code",
                    "Moodle IDs List",
                    "Moodle Names Found",
                ],
                [
                    {
                        "Curso Nombre": moodle_course_name,
                        "Odoo Course ID": str(self.course.id),
                        "Moodle Course ID": str(moodle_course_id),
                        "Odoo Subject Name": self.subject.name,
                        "Odoo Subject ID": str(self.subject.id),
                        "Odoo Subject Code": self.subject.code,
                        "Moodle IDs List": str(activity_id),
                        "Moodle Names Found": "Actividad concurrente",
                    }
                ],
            ),
        )

    def _assert_no_application_records(self, moodle_course_id, activity_id):
        self.env.invalidate_all()
        self.assertFalse(
            self.env["irg.gradebook.moodle.course.map"]
            .with_context(active_test=False)
            .search([("moodle_course_id", "=", moodle_course_id)])
        )
        self.assertFalse(
            self.env["irg.gradebook.moodle.map"]
            .with_context(active_test=False)
            .search([("moodle_course_id", "=", moodle_course_id)])
        )
        self.assertFalse(
            self.env["irg.gradebook.moodle.map.line"]
            .with_context(active_test=False)
            .search([("moodle_activity_id", "=", activity_id)])
        )

    def _assert_preflight_rejected(self, plan):
        models = (
            "irg.gradebook.moodle.course.map",
            "irg.gradebook.moodle.map",
            "irg.gradebook.moodle.map.line",
        )
        before = {
            model: self.env[model]
            .with_context(active_test=False)
            .search_count([])
            for model in models
        }
        service = MappingImportService(self.env)
        with patch.object(
            service,
            "_revalidate_course",
            wraps=service._revalidate_course,
        ) as revalidate_course, patch.object(
            service,
            "_revalidate_subject",
            wraps=service._revalidate_subject,
        ) as revalidate_subject, patch.object(
            service,
            "_upsert_course",
            wraps=service._upsert_course,
        ) as upsert_course, patch.object(
            service,
            "_upsert_subject",
            wraps=service._upsert_subject,
        ) as upsert_subject, patch.object(
            service,
            "_upsert_activities",
            wraps=service._upsert_activities,
        ) as upsert_activities:
            with self.assertRaises(ValidationError):
                service.apply_plan(plan)
            revalidate_course.assert_not_called()
            revalidate_subject.assert_not_called()
            upsert_course.assert_not_called()
            upsert_subject.assert_not_called()
            upsert_activities.assert_not_called()
        self.env.invalidate_all()
        self.assertEqual(
            {
                model: self.env[model]
                .with_context(active_test=False)
                .search_count([])
                for model in models
            },
            before,
        )

    def _two_course_plan(self):
        course_specs = (
            (460001, "Curso Test Mapping Admin HomeClass"),
            (460002, "Curso Test Mapping Admin (ONLINE 2026)"),
        )
        subject_specs = (
            (
                460001,
                self.subject,
                course_specs[0][1],
                ((601, "Actividad HC uno"), (602, "Actividad HC dos")),
            ),
            (
                460002,
                self.subject,
                course_specs[1][1],
                ((701, "Actividad ONL uno"), (702, "Actividad ONL dos")),
            ),
        )
        return self._plan(course_specs, subject_specs)

    def test_preflight_rejects_invalid_root_and_containers(self):
        cases = (
            ("root", object()),
            ("courses_container", ImportPlan([], (), {})),
            ("subjects_container", ImportPlan((), [], {})),
        )
        for case, plan in cases:
            with self.subTest(case=case):
                self._assert_preflight_rejected(plan)

    def test_preflight_rejects_malformed_members_before_revalidation(self):
        valid_plan = self._plan(
            ((461001, "Curso preflight HomeClass"),),
            (
                (
                    461001,
                    self.subject,
                    "Curso preflight HomeClass",
                    ((611, "Actividad válida"),),
                ),
            ),
        )
        cases = (
            (
                "course_member",
                ImportPlan((object(),), (), {}),
            ),
            (
                "course_metadata_type",
                ImportPlan(
                    (
                        replace(
                            valid_plan.courses[0],
                            op_course_name=object(),
                        ),
                    ),
                    (),
                    {},
                ),
            ),
            (
                "subject_member",
                ImportPlan(valid_plan.courses, (object(),), {}),
            ),
            (
                "subject_metadata_type",
                ImportPlan(
                    valid_plan.courses,
                    (
                        replace(
                            valid_plan.subjects[0],
                            op_subject_name=object(),
                        ),
                    ),
                    {},
                ),
            ),
            (
                "activity_member",
                ImportPlan(
                    valid_plan.courses,
                    (replace(valid_plan.subjects[0], activities=(object(),)),),
                    {},
                ),
            ),
            (
                "activity_metadata_type",
                ImportPlan(
                    valid_plan.courses,
                    (
                        replace(
                            valid_plan.subjects[0],
                            activities=(ActivityOperation(611, object()),),
                        ),
                    ),
                    {},
                ),
            ),
        )
        for case, plan in cases:
            with self.subTest(case=case):
                self._assert_preflight_rejected(plan)

    def test_preflight_rejects_invalid_identifiers(self):
        valid_plan = self._plan(
            ((461002, "Curso IDs HomeClass"),),
            (
                (
                    461002,
                    self.subject,
                    "Curso IDs HomeClass",
                    ((612, "Actividad válida"),),
                ),
            ),
        )
        cases = (
            (
                "boolean_course_id",
                ImportPlan(
                    (replace(valid_plan.courses[0], op_course_id=True),),
                    (),
                    {},
                ),
            ),
            (
                "zero_subject_course_id",
                ImportPlan(
                    valid_plan.courses,
                    (replace(valid_plan.subjects[0], moodle_course_id=0),),
                    {},
                ),
            ),
            (
                "out_of_range_activity_id",
                ImportPlan(
                    valid_plan.courses,
                    (
                        replace(
                            valid_plan.subjects[0],
                            activities=(
                                ActivityOperation(2147483648, "Inválida"),
                            ),
                        ),
                    ),
                    {},
                ),
            ),
        )
        for case, plan in cases:
            with self.subTest(case=case):
                self._assert_preflight_rejected(plan)

    def test_preflight_rejects_duplicate_course_and_subject_keys(self):
        valid_plan = self._plan(
            ((461003, "Curso duplicados HomeClass"),),
            (
                (
                    461003,
                    self.subject,
                    "Curso duplicados HomeClass",
                    ((613, "Actividad válida"),),
                ),
            ),
        )
        cases = (
            (
                "course_key",
                ImportPlan(
                    (valid_plan.courses[0], valid_plan.courses[0]),
                    (),
                    {},
                ),
            ),
            (
                "subject_key",
                ImportPlan(
                    valid_plan.courses,
                    (valid_plan.subjects[0], valid_plan.subjects[0]),
                    {},
                ),
            ),
        )
        for case, plan in cases:
            with self.subTest(case=case):
                self._assert_preflight_rejected(plan)

    def test_preflight_rejects_parent_and_activity_contract_violations(self):
        valid_plan = self._plan(
            ((461004, "Curso contrato HomeClass"),),
            (
                (
                    461004,
                    self.subject,
                    "Curso contrato HomeClass",
                    ((614, "Actividad válida"),),
                ),
            ),
        )
        subject = valid_plan.subjects[0]
        cases = (
            (
                "missing_parent",
                ImportPlan(
                    valid_plan.courses,
                    (replace(subject, op_course_id=self.course.id + 100000),),
                    {},
                ),
            ),
            (
                "course_metadata",
                ImportPlan(
                    valid_plan.courses,
                    (replace(subject, op_course_name="Curso incoherente"),),
                    {},
                ),
            ),
            (
                "moodle_metadata",
                ImportPlan(
                    valid_plan.courses,
                    (
                        replace(
                            subject,
                            moodle_course_name="Otro curso HomeClass",
                        ),
                    ),
                    {},
                ),
            ),
            (
                "empty_activities",
                ImportPlan(
                    valid_plan.courses,
                    (replace(subject, activities=()),),
                    {},
                ),
            ),
            (
                "duplicate_activity_id",
                ImportPlan(
                    valid_plan.courses,
                    (
                        replace(
                            subject,
                            activities=(
                                subject.activities[0],
                                subject.activities[0],
                            ),
                        ),
                    ),
                    {},
                ),
            ),
        )
        for case, plan in cases:
            with self.subTest(case=case):
                self._assert_preflight_rejected(plan)

    def test_preflight_rejects_error_in_final_element_without_partial_writes(self):
        valid_plan = self._plan(
            (
                (461005, "Primer curso preflight HomeClass"),
                (461006, "Segundo curso preflight HomeClass"),
            ),
            (),
        )
        malformed_plan = ImportPlan(
            (valid_plan.courses[0], object()),
            (),
            {},
        )

        self._assert_preflight_rejected(malformed_plan)

    def test_creates_multiple_course_subject_and_activity_maps(self):
        result = MappingImportService(self.env).apply_plan(
            self._two_course_plan()
        )

        course_maps = self.env["irg.gradebook.moodle.course.map"].search(
            [("moodle_course_id", "in", [460001, 460002])], order="id"
        )
        subject_maps = self.env["irg.gradebook.moodle.map"].search(
            [("moodle_course_id", "in", [460001, 460002])], order="id"
        )
        self.assertEqual(
            result,
            {
                "course_maps": {"created": 2, "updated": 0},
                "subject_maps": {"created": 2, "updated": 0},
                "activities": {"created": 4, "updated": 0},
                "affected_course_map_ids": course_maps.ids,
                "affected_subject_map_ids": subject_maps.ids,
            },
        )
        self.assertEqual(course_maps.mapped("op_course_id"), self.course)
        self.assertEqual(
            subject_maps.mapped("course_map_id"), course_maps
        )
        self.assertEqual(
            subject_maps.mapped("line_ids.moodle_activity_id"),
            [601, 602, 701, 702],
        )

    def test_rerun_is_idempotent(self):
        service = MappingImportService(self.env)
        plan = self._two_course_plan()
        service.apply_plan(plan)
        course_maps = self.env["irg.gradebook.moodle.course.map"].search(
            [("moodle_course_id", "in", [460001, 460002])], order="id"
        )
        subject_maps = self.env["irg.gradebook.moodle.map"].search(
            [("moodle_course_id", "in", [460001, 460002])], order="id"
        )
        line_ids = subject_maps.mapped("line_ids").ids

        result = service.apply_plan(plan)

        self.assertEqual(result["course_maps"], {"created": 0, "updated": 2})
        self.assertEqual(result["subject_maps"], {"created": 0, "updated": 2})
        self.assertEqual(result["activities"], {"created": 0, "updated": 4})
        self.assertEqual(
            self.env["irg.gradebook.moodle.course.map"].search(
                [("moodle_course_id", "in", [460001, 460002])], order="id"
            ).ids,
            course_maps.ids,
        )
        rerun_subject_maps = self.env["irg.gradebook.moodle.map"].search(
            [("moodle_course_id", "in", [460001, 460002])], order="id"
        )
        self.assertEqual(rerun_subject_maps.ids, subject_maps.ids)
        self.assertEqual(rerun_subject_maps.mapped("line_ids").ids, line_ids)

    def test_reactivates_and_preserves_type_history_and_blank_names(self):
        expected_parent = self.env["irg.gradebook.moodle.course.map"].create(
            {
                "op_course_id": self.course.id,
                "moodle_course_id": 470001,
                "moodle_course_name": "Nombre anterior",
                "active": False,
            }
        )
        other_course = self.env["op.course"].create(
            {
                "name": "Curso padre anterior",
                "code": "CT-MAP-ANT",
                "lang": "en_US",
                "gradebook_id": self.gradebook.id,
                "subject_ids": [Command.link(self.subject.id)],
            }
        )
        previous_parent = self.env["irg.gradebook.moodle.course.map"].create(
            {
                "op_course_id": other_course.id,
                "moodle_course_id": 470001,
                "moodle_course_name": "Curso padre anterior",
            }
        )
        subject_map = self.env["irg.gradebook.moodle.map"].create(
            {
                "op_subject_id": self.subject.id,
                "moodle_course_id": 470001,
                "moodle_course_name": "Nombre anterior",
                "course_map_id": previous_parent.id,
                "active": False,
            }
        )
        retained = self.env["irg.gradebook.moodle.map.line"].create(
            {
                "map_id": subject_map.id,
                "moodle_activity_id": 801,
                "name": "Nombre previo",
                "activity_type": "assign",
            }
        )
        blank_source = self.env["irg.gradebook.moodle.map.line"].create(
            {
                "map_id": subject_map.id,
                "moodle_activity_id": 802,
                "name": "No vaciar",
                "activity_type": "assign",
            }
        )
        historical = self.env["irg.gradebook.moodle.map.line"].create(
            {
                "map_id": subject_map.id,
                "moodle_activity_id": 899,
                "name": "Histórica",
                "activity_type": "assign",
            }
        )
        course_name = "Curso Test Mapping Admin (ONLINE 2026)"
        plan = self._plan(
            ((470001, course_name),),
            (
                (
                    470001,
                    self.subject,
                    course_name,
                    (
                        (801, "Nombre actualizado"),
                        (802, ""),
                        (803, "Nueva actividad"),
                    ),
                ),
            ),
        )

        result = MappingImportService(self.env).apply_plan(plan)

        expected_parent.invalidate_recordset()
        subject_map.invalidate_recordset()
        retained.invalidate_recordset()
        blank_source.invalidate_recordset()
        historical.invalidate_recordset()
        self.assertTrue(expected_parent.active)
        self.assertEqual(expected_parent.moodle_course_name, course_name)
        self.assertTrue(subject_map.active)
        self.assertEqual(subject_map.course_map_id, expected_parent)
        self.assertEqual(subject_map.moodle_course_name, course_name)
        self.assertEqual(retained.name, "Nombre actualizado")
        self.assertEqual(retained.activity_type, "assign")
        self.assertEqual(blank_source.name, "No vaciar")
        self.assertEqual(blank_source.activity_type, "assign")
        self.assertEqual(historical.name, "Histórica")
        self.assertEqual(historical.activity_type, "assign")
        self.assertEqual(
            set(subject_map.line_ids.mapped("moodle_activity_id")),
            {801, 802, 803, 899},
        )
        self.assertEqual(result["course_maps"], {"created": 0, "updated": 1})
        self.assertEqual(result["subject_maps"], {"created": 0, "updated": 1})
        self.assertEqual(result["activities"], {"created": 1, "updated": 1})

    def test_revalidates_membership_and_parent_before_writes(self):
        plan = self._plan(
            ((480001, "Curso Test Mapping Admin HomeClass"),),
            (
                (
                    480001,
                    self.subject,
                    "Otro nombre Moodle",
                    ((901, "No debe crearse"),),
                ),
            ),
        )
        before = {
            model: self.env[model].with_context(active_test=False).search_count(
                [("moodle_course_id", "=", 480001)]
            )
            for model in (
                "irg.gradebook.moodle.course.map",
                "irg.gradebook.moodle.map",
            )
        }

        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            MappingImportService(self.env).apply_plan(plan)

        self.env.invalidate_all()
        after = {
            model: self.env[model].with_context(active_test=False).search_count(
                [("moodle_course_id", "=", 480001)]
            )
            for model in before
        }
        self.assertEqual(after, before)

        unrelated_course = self.env["op.course"].create(
            {
                "name": "Curso ajeno para revalidación",
                "code": "CT-MAP-REVALIDATE",
                "lang": "en_US",
                "gradebook_id": self.gradebook.id,
            }
        )
        unrelated_subject = self.env["op.subject"].create(
            {
                "name": "Asignatura ajena para revalidación",
                "code": "AT-MAP-REVALIDATE",
                "course_id": unrelated_course.id,
                "gradebook_id": self.gradebook.id,
            }
        )
        unrelated_course.write(
            {"subject_ids": [Command.link(unrelated_subject.id)]}
        )
        valid_name = "Curso Test Mapping Admin HomeClass"
        membership_plan = self._plan(
            ((480002, valid_name),),
            ((480002, unrelated_subject, valid_name, ((902, "No crear"),)),),
        )
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            MappingImportService(self.env).apply_plan(membership_plan)

    def test_rejects_concurrent_course_name_change_without_partial_writes(self):
        plan = self._analyzed_plan(481001, 1101)
        self.assertEqual(plan.courses[0].op_course_name, self.course.name)
        self.course.name = "Curso cambiado concurrentemente"

        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            MappingImportService(self.env).apply_plan(plan)

        self._assert_no_application_records(481001, 1101)

    def test_rejects_concurrent_subject_name_change_and_rolls_back_course(self):
        plan = self._analyzed_plan(481002, 1102)
        self.assertEqual(plan.subjects[0].op_subject_name, self.subject.name)
        self.subject.name = "Asignatura cambiada concurrentemente"

        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            MappingImportService(self.env).apply_plan(plan)

        self._assert_no_application_records(481002, 1102)

    def test_rejects_concurrent_subject_code_change_and_rolls_back_course(self):
        plan = self._analyzed_plan(481003, 1103)
        self.assertEqual(plan.subjects[0].op_subject_code, self.subject.code)
        self.subject.code = "CODIGO-CAMBIADO"

        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            MappingImportService(self.env).apply_plan(plan)

        self._assert_no_application_records(481003, 1103)

    def test_orm_failure_rolls_back_the_complete_application(self):
        second_subject = self.env["op.subject"].create(
            {
                "name": "Segunda Asignatura Test Mapping Admin",
                "code": "AT-MAP-ADMIN-2",
                "course_id": self.course.id,
                "gradebook_id": self.gradebook.id,
            }
        )
        self.course.write({"subject_ids": [Command.link(second_subject.id)]})
        course_name = "Curso transaccional HomeClass"
        plan = self._plan(
            ((490001, course_name),),
            (
                (490001, self.subject, course_name, ((1001, "Primera"),)),
                (490001, second_subject, course_name, ((1002, "Segunda"),)),
            ),
        )
        service = MappingImportService(self.env)
        original_upsert = service._upsert_activities
        calls = 0

        def fail_on_second_subject(activities, mapping, result):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise ValidationError("Fallo ORM simulado")
            return original_upsert(activities, mapping, result)

        with patch.object(
            service,
            "_upsert_activities",
            side_effect=fail_on_second_subject,
        ):
            with self.assertRaises(ValidationError), self.env.cr.savepoint():
                service.apply_plan(plan)

        self.env.invalidate_all()
        self.assertEqual(calls, 2)
        self.assertFalse(
            self.env["irg.gradebook.moodle.course.map"]
            .with_context(active_test=False)
            .search([("moodle_course_id", "=", 490001)])
        )
        self.assertFalse(
            self.env["irg.gradebook.moodle.map"]
            .with_context(active_test=False)
            .search([("moodle_course_id", "=", 490001)])
        )
        self.assertFalse(
            self.env["irg.gradebook.moodle.map.line"]
            .with_context(active_test=False)
            .search([("moodle_activity_id", "in", [1001, 1002])])
        )
