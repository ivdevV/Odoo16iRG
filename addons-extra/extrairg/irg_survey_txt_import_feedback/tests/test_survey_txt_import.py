import base64
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestSurveyTxtImport(TransactionCase):

    def setUp(self):
        super().setUp()
        self.survey = self.env['survey.survey'].create({
            'title': 'Test Survey',
            'survey_type': 'exam',
        })
        self.wizard_model = self.env['irg.survey.txt.import.wizard']

    def _create_wizard(self, txt_content):
        return self.wizard_model.create({
            'survey_id': self.survey.id,
            'txt_file': base64.b64encode(txt_content.encode('utf-8')),
            'txt_filename': 'test.txt',
        })

    def test_parse_valid_4_options(self):
        txt = (
            "P: ¿Qué es Odoo?\n"
            "A: CRM\n"
            "B: ERP modular\n"
            "C: Navegador\n"
            "D: Hoja de cálculo\n"
            "RC: B\n"
            "FG: Feedback general"
        )
        wizard = self._create_wizard(txt)
        parsed = wizard._parse_file()
        self.assertEqual(len(parsed), 1)
        q = parsed[0]
        self.assertEqual(q['P'], '¿Qué es Odoo?')
        self.assertEqual(q['A'], 'CRM')
        self.assertEqual(q['B'], 'ERP modular')
        self.assertEqual(q['C'], 'Navegador')
        self.assertEqual(q['D'], 'Hoja de cálculo')
        self.assertEqual(q['RC'], 'B')
        self.assertEqual(q['FG'], 'Feedback general')

    def test_parse_valid_3_options(self):
        txt = (
            "P: ¿Cuánto es 1 + 1?\n"
            "A: 1\n"
            "B: 2\n"
            "C: 3\n"
            "RC: B"
        )
        wizard = self._create_wizard(txt)
        parsed = wizard._parse_file()
        self.assertEqual(len(parsed), 1)
        q = parsed[0]
        self.assertEqual(q['P'], '¿Cuánto es 1 + 1?')
        self.assertEqual(q['A'], '1')
        self.assertEqual(q['B'], '2')
        self.assertEqual(q['C'], '3')
        self.assertNotIn('D', q)
        self.assertEqual(q['RC'], 'B')

    def test_parse_valid_5_options(self):
        txt = (
            "P: Pregunta de prueba 5 opciones\n"
            "A: Op1\n"
            "B: Op2\n"
            "C: Op3\n"
            "D: Op4\n"
            "E: Op5\n"
            "RC: E"
        )
        wizard = self._create_wizard(txt)
        parsed = wizard._parse_file()
        self.assertEqual(len(parsed), 1)
        q = parsed[0]
        self.assertEqual(q['P'], 'Pregunta de prueba 5 opciones')
        self.assertEqual(q['A'], 'Op1')
        self.assertEqual(q['E'], 'Op5')
        self.assertEqual(q['RC'], 'E')

    def test_parse_invalid_non_consecutive_options(self):
        txt = (
            "P: Pregunta incorrecta\n"
            "A: Op1\n"
            "C: Op3\n"
            "RC: A"
        )
        wizard = self._create_wizard(txt)
        with self.assertRaises(ValidationError) as e:
            wizard._parse_file()
        self.assertIn("deben ser consecutivas empezando por la A", str(e.exception))

    def test_parse_invalid_not_starting_with_a(self):
        txt = (
            "P: Pregunta incorrecta\n"
            "B: Op1\n"
            "C: Op2\n"
            "RC: B"
        )
        wizard = self._create_wizard(txt)
        with self.assertRaises(ValidationError) as e:
            wizard._parse_file()
        self.assertIn("deben ser consecutivas empezando por la A", str(e.exception))

    def test_parse_invalid_missing_p(self):
        txt = (
            "A: Op1\n"
            "B: Op2\n"
            "RC: A"
        )
        wizard = self._create_wizard(txt)
        with self.assertRaises(ValidationError) as e:
            wizard._parse_file()
        self.assertIn("faltan campos obligatorios", str(e.exception))

    def test_parse_invalid_missing_rc(self):
        txt = (
            "P: Pregunta\n"
            "A: Op1\n"
            "B: Op2\n"
        )
        wizard = self._create_wizard(txt)
        with self.assertRaises(ValidationError) as e:
            wizard._parse_file()
        self.assertIn("faltan campos obligatorios", str(e.exception))

    def test_parse_invalid_rc_not_in_options(self):
        txt = (
            "P: Pregunta\n"
            "A: Op1\n"
            "B: Op2\n"
            "RC: C"
        )
        wizard = self._create_wizard(txt)
        with self.assertRaises(ValidationError) as e:
            wizard._parse_file()
        self.assertIn("RC invalida", str(e.exception))

    def test_action_preview_content(self):
        txt = (
            "P: Q1\n"
            "A: O1\n"
            "B: O2\n"
            "C: O3\n"
            "RC: A"
        )
        wizard = self._create_wizard(txt)
        wizard.action_preview()
        expected_preview = (
            "1. Q1\n"
            "   A) O1\n"
            "   B) O2\n"
            "   C) O3\n"
            "   RC: A"
        )
        self.assertEqual(wizard.preview_text, expected_preview)
        self.assertEqual(wizard.parsed_count, 1)

    def test_action_import_saves_records(self):
        txt = (
            "P: Pregunta a guardar\n"
            "A: Opcion A\n"
            "B: Opcion B\n"
            "C: Opcion C\n"
            "RC: B\n"
            "FG: Retroalimentacion"
        )
        wizard = self._create_wizard(txt)
        wizard.action_import()

        # Verify the question was created
        questions = self.env['survey.question'].search([('survey_id', '=', self.survey.id)])
        self.assertEqual(len(questions), 1)
        question = questions[0]
        self.assertEqual(question.title, 'Pregunta a guardar')
        self.assertEqual(question.question_type, 'simple_choice')
        self.assertEqual(question.x_feedback_generic, 'Retroalimentacion')

        # Verify answers were created
        answers = question.suggested_answer_ids
        self.assertEqual(len(answers), 3)
        self.assertEqual(set(answers.mapped('value')), {'Opcion A', 'Opcion B', 'Opcion C'})

        # Verify correct answer configuration
        correct_answers = answers.filtered(lambda a: a.value == 'Opcion B')
        incorrect_answers = answers.filtered(lambda a: a.value != 'Opcion B')

        for ans in correct_answers:
            if 'is_correct' in ans._fields:
                self.assertTrue(ans.is_correct)
            if 'answer_score' in ans._fields:
                self.assertTrue(ans.answer_score > 0.0)

        for ans in incorrect_answers:
            if 'is_correct' in ans._fields:
                self.assertFalse(ans.is_correct)
            if 'answer_score' in ans._fields:
                self.assertEqual(ans.answer_score, 0.0)
