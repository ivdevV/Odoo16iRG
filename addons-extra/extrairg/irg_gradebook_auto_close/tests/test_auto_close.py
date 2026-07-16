# -*- coding: utf-8 -*-

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestGradebookAutoClose(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Gradebook = cls.env["app.gradebook"]
        cls.GradebookStudent = cls.env["app.gradebook.student"]
        cls.GradebookSubject = cls.env["app.gradebook.subject"]
        cls.GradebookResult = cls.env["app.gradebook.result"]

        cls.product = cls.env["product.product"].create(
            {
                "name": "IRG Gradebook Auto Close Product",
                "type": "service",
            }
        )
        cls.course_index = 0

    def _create_gradebook_template(self, line_values):
        return self.Gradebook.create(
            {
                "name": "IRG Auto Close Template",
                "gradebook_template_ids": [
                    (0, 0, values) for values in line_values
                ],
            }
        )

    def _create_student_gradebook(self, template, subject_count=1):
        type(self).course_index += 1
        index = type(self).course_index
        course = self.env["op.course"].create(
            {
                "name": "IRG Auto Close Course %s" % index,
                "code": "IRGAC%03d" % index,
                "gradebook_id": template.id,
            }
        )
        partner = self.env["res.partner"].create(
            {"name": "IRG Auto Close Student %s" % index}
        )
        student = self.env["op.student"].create(
            {
                "partner_id": partner.id,
                "first_name": "IRG",
                "last_name": "Auto Close %s" % index,
                "gender": "m",
            }
        )
        register = self.env["op.admission.register"].create(
            {
                "name": "IRG Auto Close Register %s" % index,
                "course_id": course.id,
                "product_id": self.product.id,
                "start_date": fields.Date.today(),
                "end_date": fields.Date.today(),
                "min_count": 1,
                "max_count": 100,
            }
        )
        admission = self.env["op.admission"].create(
            {
                "name": "IRG Auto Close Admission %s" % index,
                "first_name": "IRG",
                "last_name": "Auto Close %s" % index,
                "birth_date": "2000-01-01",
                "gender": "m",
                "email": "irg.auto.close.%s@example.com" % index,
                "partner_id": partner.id,
                "student_id": student.id,
                "course_id": course.id,
                "register_id": register.id,
            }
        )
        gradebook = self.GradebookStudent.create(
            {
                "admission_id": admission.id,
                "state": "in_progress",
            }
        )
        lines = self.GradebookSubject.browse()
        for subject_index in range(1, subject_count + 1):
            subject = self.env["op.subject"].create(
                {
                    "name": "IRG Auto Close Subject %s-%s"
                    % (index, subject_index),
                    "code": "IRGAC-%s-%s" % (index, subject_index),
                    "subject_type": "compulsory",
                    "course_id": course.id,
                }
            )
            lines |= self.GradebookSubject.create(
                {
                    "gradebook_student_id": gradebook.id,
                    "op_subject_id": subject.id,
                }
            )
        return gradebook, lines

    def _template_exam_and_assignment(self):
        return self._create_gradebook_template(
            [
                {"type": "exam", "weight": 50.0, "qty": 1},
                {"type": "assignment", "weight": 50.0, "qty": 1},
            ]
        )

    def _add_result(self, line, survey_type, score):
        return self.GradebookResult.create(
            {
                "gradebook_subject_id": line.id,
                "survey_type": survey_type,
                "scoring_total": score,
            }
        )

    def _flush_gradebook(self, gradebook):
        self.env.flush_all()
        gradebook.invalidate_recordset()
        gradebook.gradebook_subject_ids.invalidate_recordset()

    def test_last_grade_write_closes_complete_gradebook(self):
        """Scenario 1: the last positive grade closes every complete line."""
        gradebook, lines = self._create_student_gradebook(
            self._template_exam_and_assignment(), subject_count=2
        )
        for line in lines:
            self._add_result(line, "assignment", 8.0)
        self._add_result(lines[0], "exam", 9.0)
        last_result = self._add_result(lines[1], "exam", 0.0)

        last_result.write({"scoring_total": 9.0})
        self._flush_gradebook(gradebook)

        self.assertEqual(gradebook.state, "done")

    def test_zero_final_grade_keeps_gradebook_in_progress(self):
        """Scenario 2: a line whose final grade is zero prevents closure."""
        gradebook, lines = self._create_student_gradebook(
            self._template_exam_and_assignment(), subject_count=2
        )
        for line in lines:
            self._add_result(line, "assignment", 8.0)
        self._add_result(lines[0], "exam", 9.0)
        zero_result = self._add_result(lines[1], "exam", 0.0)

        zero_result.write({"scoring_total": 0.0})
        self._flush_gradebook(gradebook)

        self.assertEqual(gradebook.state, "in_progress")

    def test_line_without_assignments_can_close(self):
        """Scenario 3: an exam-only line does not require assignment average."""
        template = self._create_gradebook_template(
            [{"type": "exam", "weight": 100.0, "qty": 1}]
        )
        gradebook, lines = self._create_student_gradebook(template)
        result = self._add_result(lines, "exam", 0.0)

        result.write({"scoring_total": 9.0})
        self._flush_gradebook(gradebook)

        self.assertFalse(lines.show_assignment)
        self.assertEqual(gradebook.state, "done")

    def test_reopened_gradebook_waits_for_next_result_write(self):
        """Scenario 4: reopening alone never triggers an immediate re-close."""
        template = self._create_gradebook_template(
            [{"type": "exam", "weight": 100.0, "qty": 1}]
        )
        gradebook, lines = self._create_student_gradebook(template)
        result = self._add_result(lines, "exam", 0.0)
        result.write({"scoring_total": 9.0})
        self.assertEqual(gradebook.state, "done")

        gradebook.state_to_in_progress()
        self.assertEqual(gradebook.state, "in_progress")

        result.write({"scoring_total": 9.0})
        self.assertEqual(gradebook.state, "done")

    def test_template_validation_error_does_not_abort_grade_write(self):
        """Scenario 5: missing template evaluations leave the book open."""
        template = self._create_gradebook_template(
            [
                {"type": "exam", "weight": 45.0, "qty": 1},
                {"type": "assignment", "weight": 45.0, "qty": 1},
                {"type": "interaction", "weight": 10.0, "qty": 1},
            ]
        )
        gradebook, lines = self._create_student_gradebook(template)
        self._add_result(lines, "assignment", 8.0)
        result = self._add_result(lines, "exam", 0.0)

        result.write({"scoring_total": 9.0})
        self._flush_gradebook(gradebook)

        self.assertEqual(gradebook.state, "in_progress")

    def test_ready_condition_accepts_complete_lines(self):
        """Direct condition: all required positive averages are ready."""
        gradebook, lines = self._create_student_gradebook(
            self._template_exam_and_assignment()
        )
        self._add_result(lines, "assignment", 8.0)
        self._add_result(lines, "exam", 9.0)
        self._flush_gradebook(gradebook)
        gradebook.state_to_in_progress()

        self.assertTrue(gradebook._irg_is_ready_to_close())

    def test_ready_condition_rejects_zero_grade(self):
        """Direct condition: zero final grade is not ready."""
        gradebook, lines = self._create_student_gradebook(
            self._template_exam_and_assignment()
        )
        self._add_result(lines, "assignment", 8.0)
        self._add_result(lines, "exam", 0.0)
        self._flush_gradebook(gradebook)

        self.assertFalse(gradebook._irg_is_ready_to_close())

    def test_ready_condition_skips_assignments_when_hidden(self):
        """Direct condition: hidden assignment averages are ignored."""
        template = self._create_gradebook_template(
            [{"type": "exam", "weight": 100.0, "qty": 1}]
        )
        gradebook, lines = self._create_student_gradebook(template)
        self._add_result(lines, "exam", 9.0)
        self._flush_gradebook(gradebook)
        gradebook.state_to_in_progress()

        self.assertFalse(lines.show_assignment)
        self.assertTrue(gradebook._irg_is_ready_to_close())

    def test_multi_record_write_closes_each_affected_gradebook(self):
        """A write batch spanning templates is handled record by record."""
        first_template = self._create_gradebook_template(
            [{"type": "exam", "weight": 100.0, "qty": 1}]
        )
        second_template = self._create_gradebook_template(
            [{"type": "exam", "weight": 100.0, "qty": 1}]
        )
        first_gradebook, first_line = self._create_student_gradebook(
            first_template
        )
        second_gradebook, second_line = self._create_student_gradebook(
            second_template
        )
        first_result = self._add_result(first_line, "exam", 0.0)
        second_result = self._add_result(second_line, "exam", 0.0)

        (first_result | second_result).write({"scoring_total": 9.0})

        self.assertEqual(first_gradebook.state, "done")
        self.assertEqual(second_gradebook.state, "done")

    def test_create_last_positive_result_closes_gradebook(self):
        """Creating the last positive result triggers automatic closure."""
        template = self._create_gradebook_template(
            [{"type": "exam", "weight": 100.0, "qty": 1}]
        )
        gradebook, line = self._create_student_gradebook(template)

        self._add_result(line, "exam", 9.0)

        self.assertEqual(gradebook.state, "done")

    def test_unlink_blocking_result_rechecks_after_super_and_closes(self):
        """Removing an excess zero result leaves valid template quantities."""
        template = self._create_gradebook_template(
            [{"type": "exam", "weight": 100.0, "qty": 1}]
        )
        gradebook, line = self._create_student_gradebook(template)
        blocking_result = self._add_result(line, "exam", 0.0)
        self._add_result(line, "exam", 9.0)
        self.assertEqual(gradebook.state, "in_progress")

        blocking_result.unlink()

        self.assertEqual(len(line.gradebook_result_ids), 1)
        self.assertEqual(line.gradebook_result_ids.scoring_total, 9.0)
        self.assertEqual(gradebook.state, "done")

    def test_write_subject_move_rechecks_previous_and_current_gradebooks(self):
        """Moving a result can complete both its previous and current books."""
        template = self._create_gradebook_template(
            [{"type": "exam", "weight": 100.0, "qty": 1}]
        )
        previous_gradebook, previous_line = self._create_student_gradebook(
            template
        )
        current_gradebook, current_line = self._create_student_gradebook(
            template
        )
        previous_gradebook.action_draft()
        current_gradebook.action_draft()
        moving_result = self._add_result(previous_line, "exam", 8.0)
        self._add_result(previous_line, "exam", 9.0)
        previous_gradebook.state_to_in_progress()
        current_gradebook.state_to_in_progress()

        moving_result.write({"gradebook_subject_id": current_line.id})

        self.assertEqual(previous_gradebook.state, "done")
        self.assertEqual(current_gradebook.state, "done")

    def test_batch_create_defers_nested_rounding_write_auto_close(self):
        """Nested rounding writes must not close a partially created batch."""
        template = self._create_gradebook_template(
            [{"type": "exam", "weight": 100.0, "qty": 1}]
        )
        template.round_subject_result = True
        gradebook, line = self._create_student_gradebook(template)

        results = self.GradebookResult.create(
            [
                {
                    "gradebook_subject_id": line.id,
                    "survey_type": "exam",
                    "scoring_total": 9.0,
                },
                {
                    "gradebook_subject_id": line.id,
                    "survey_type": "exam",
                    "scoring_total": 0.0,
                },
            ]
        )
        self._flush_gradebook(gradebook)

        self.assertEqual(len(results), 2)
        self.assertNotIn(
            "irg_gradebook_auto_close_skip_nested_write_auto_close",
            results.env.context,
        )
        self.assertEqual(gradebook.state, "in_progress")
        self.assertEqual(line.point_average_exam, 0.0)
        self.assertEqual(line.final_subject_note, 4.5)
