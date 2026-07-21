# -*- coding: utf-8 -*-
from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestGradebookPartialAverages(TransactionCase):
    """
    Verifica que compute_point_average calcule promedios parciales de
    "assignment" y "exam" en lugar de forzarlos a 0 cuando el nº de
    resultados registrados no coincide con la "qty" de la plantilla, y que
    compute_total_percent (isep_gradebook) no sume pesos de varias
    plantillas en un recompute multi-registro.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Gradebook = cls.env["app.gradebook"]
        cls.GradebookStudent = cls.env["app.gradebook.student"]
        cls.GradebookSubject = cls.env["app.gradebook.subject"]
        cls.GradebookResult = cls.env["app.gradebook.result"]

        cls.product = cls.env["product.product"].create(
            {
                "name": "IRG Gradebook Partial Averages Product",
                "type": "service",
            }
        )
        cls.course_index = 0

    def _create_gradebook_template(self, line_values):
        return self.Gradebook.create(
            {
                "name": "IRG Partial Averages Template",
                "gradebook_template_ids": [
                    (0, 0, values) for values in line_values
                ],
            }
        )

    def _create_student_gradebook(self, template, subject_template=None):
        type(self).course_index += 1
        index = type(self).course_index
        course = self.env["op.course"].create(
            {
                "name": "IRG Partial Averages Course %s" % index,
                "code": "IRGPA%03d" % index,
                "gradebook_id": template.id,
                "lang": "en_US",
            }
        )
        partner = self.env["res.partner"].create(
            {"name": "IRG Partial Averages Student %s" % index}
        )
        student = self.env["op.student"].create(
            {
                "partner_id": partner.id,
                "first_name": "IRG",
                "last_name": "Partial Averages %s" % index,
                "gender": "m",
            }
        )
        register = self.env["op.admission.register"].create(
            {
                "name": "IRG Partial Averages Register %s" % index,
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
                "name": "IRG Partial Averages Admission %s" % index,
                "first_name": "IRG",
                "last_name": "Partial Averages %s" % index,
                "birth_date": "2000-01-01",
                "gender": "m",
                "email": "irg.partial.averages.%s@example.com" % index,
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
        op_subject = self.env["op.subject"].create(
            {
                "name": "IRG Partial Averages Subject %s" % index,
                "code": "IRGPA-%s" % index,
                "subject_type": "compulsory",
                "course_id": course.id,
                "gradebook_id": subject_template.id if subject_template else False,
            }
        )
        line = self.GradebookSubject.create(
            {
                "gradebook_student_id": gradebook.id,
                "op_subject_id": op_subject.id,
            }
        )
        return gradebook, line, course, op_subject

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

    def test_partial_average_exam_qty_mismatch(self):
        """qty=3 en la plantilla pero solo 2 resultados exam -> promedio parcial, no 0."""
        template = self._create_gradebook_template(
            [{"type": "exam", "weight": 100.0, "qty": 3}]
        )
        gradebook, line, _course, _subject = self._create_student_gradebook(template)
        self._add_result(line, "exam", 8.0)
        self._add_result(line, "exam", 6.0)
        self._flush_gradebook(gradebook)

        self.assertEqual(line.point_average_exam, 7.0)

    def test_partial_average_assignment_qty_mismatch(self):
        """Mismo caso análogo para assignment."""
        template = self._create_gradebook_template(
            [{"type": "assignment", "weight": 100.0, "qty": 3}]
        )
        gradebook, line, _course, _subject = self._create_student_gradebook(template)
        self._add_result(line, "assignment", 8.0)
        self._add_result(line, "assignment", 6.0)
        self._flush_gradebook(gradebook)

        self.assertEqual(line.point_average_assignment, 7.0)

    def test_zero_results_keeps_zero(self):
        """Sin resultados exam registrados, el promedio sigue siendo 0."""
        template = self._create_gradebook_template(
            [{"type": "exam", "weight": 100.0, "qty": 1}]
        )
        gradebook, line, _course, _subject = self._create_student_gradebook(template)
        self._flush_gradebook(gradebook)

        self.assertEqual(line.point_average_exam, 0.0)

    def test_template_change_does_not_zeroize(self):
        """Cambiar la plantilla efectiva (qty distinta) no pone a 0 los promedios ya calculados.

        Nota: `app.gradebook.subject.compute_gradebook_id` (isep_gradebook)
        declara `@api.depends('op_subject_id', 'admission_id')`, SIN incluir
        `'op_subject_id.gradebook_id'`, así que reasignar
        `op_subject.gradebook_id` no dispara por sí solo el recompute de
        `subject.gradebook_id` (bug de staleness separado, fuera del alcance
        de esta misión: solo cubre el 00-spec.md el forzado a 0 de los
        promedios, no la precedencia/staleness de plantillas, ya tratada en
        la misión fix-gradebook-template-precedence). Para simular en el test
        el efecto de "cambiar la plantilla y guardar" se fuerza el recompute
        del campo `gradebook_id` de la asignatura llamando directamente a
        `compute_gradebook_id()`, replicando lo que el guardado real
        provocaría si esa dependencia estuviese completa.
        """
        template_a = self._create_gradebook_template(
            [{"type": "exam", "weight": 100.0, "qty": 2}]
        )
        gradebook, line, _course, op_subject = self._create_student_gradebook(
            template_a, subject_template=template_a
        )
        self._add_result(line, "exam", 8.0)
        self._add_result(line, "exam", 6.0)
        self._flush_gradebook(gradebook)

        self.assertEqual(line.point_average_exam, 7.0)

        template_b = self._create_gradebook_template(
            [{"type": "exam", "weight": 100.0, "qty": 5}]
        )
        op_subject.gradebook_id = template_b.id
        line.compute_gradebook_id()
        self._flush_gradebook(gradebook)

        self.assertEqual(line.gradebook_id, template_b)
        self.assertEqual(line.point_average_exam, 7.0)

    def test_interaction_and_foro_unchanged(self):
        """interaction y foro conservan su lógica original (exactamente 1 resultado)."""
        template = self._create_gradebook_template(
            [
                {"type": "interaction", "weight": 50.0, "qty": 1},
                {"type": "foro", "weight": 50.0, "qty": 1},
            ]
        )
        gradebook, line, _course, _subject = self._create_student_gradebook(template)
        self._add_result(line, "interaction", 9.0)
        self._add_result(line, "foro", 7.0)
        self._flush_gradebook(gradebook)

        self.assertEqual(line.point_average_interaction, 9.0)
        self.assertEqual(line.point_average_foro, 7.0)

    def test_rounding_preserved(self):
        """round_subject_avg sigue redondeando el promedio parcial calculado."""
        template = self._create_gradebook_template(
            [{"type": "exam", "weight": 100.0, "qty": 3}]
        )
        template.round_subject_avg = True
        gradebook, line, _course, _subject = self._create_student_gradebook(template)
        self._add_result(line, "exam", 8.0)
        self._add_result(line, "exam", 7.0)
        self._flush_gradebook(gradebook)

        # (8.0 + 7.0) / 2 = 7.5 -> round_custom(7.5) == 8
        self.assertEqual(line.point_average_exam, 8)

    def test_info_shows_partial_count(self):
        """info_exam sigue mostrando el conteo parcial "[ 2 de 3 ]"."""
        template = self._create_gradebook_template(
            [{"type": "exam", "weight": 100.0, "qty": 3}]
        )
        gradebook, line, _course, _subject = self._create_student_gradebook(template)
        self._add_result(line, "exam", 8.0)
        self._add_result(line, "exam", 6.0)
        self._flush_gradebook(gradebook)

        self.assertIn("[ 2 de 3 ]", line.info_exam)

    def test_total_percent_per_record_multi(self):
        """compute_total_percent no debe sumar pesos de varias plantillas en un recompute multi-registro."""
        gradebooks = self.Gradebook.create(
            [
                {
                    "name": "IRG Partial Averages Multi 1",
                    "gradebook_template_ids": [
                        (0, 0, {"type": "exam", "weight": 60.0, "qty": 1}),
                        (0, 0, {"type": "assignment", "weight": 40.0, "qty": 1}),
                    ],
                },
                {
                    "name": "IRG Partial Averages Multi 2",
                    "gradebook_template_ids": [
                        (0, 0, {"type": "exam", "weight": 50.0, "qty": 1}),
                        (0, 0, {"type": "interaction", "weight": 50.0, "qty": 1}),
                    ],
                },
            ]
        )
        gradebook1, gradebook2 = gradebooks[0], gradebooks[1]

        # Forzar el recompute sobre el recordset conjunto (multi-registro).
        (gradebook1 | gradebook2).invalidate_recordset(["total_percent"])
        (gradebook1 | gradebook2).mapped("total_percent")

        self.assertEqual(gradebook1.total_percent, 100.0)
        self.assertEqual(gradebook2.total_percent, 100.0)
