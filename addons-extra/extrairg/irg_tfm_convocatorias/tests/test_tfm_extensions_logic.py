"""Pruebas de las reglas puras. Se ejecutan sin Odoo."""
import importlib.util
import pathlib
import unittest
from datetime import date


_MODULE_PATH = (
    pathlib.Path(__file__).resolve().parents[1] / 'models' / 'irg_tfm_logic.py'
)
_SPEC = importlib.util.spec_from_file_location('irg_tfm_logic', _MODULE_PATH)
logic = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(logic)


class WeightedPointsTest(unittest.TestCase):
    def test_thirty_thirty_forty(self):
        points = logic.weighted_points(
            {'tutor': 8, 'draft': 7, 'defense': 9},
            {'tutor': 30, 'draft': 30, 'defense': 40},
        )
        self.assertEqual(points, 8.1)

    def test_missing_note_does_not_score(self):
        points = logic.weighted_points(
            {'tutor': 8, 'draft': None, 'defense': 9},
            {'tutor': 30, 'draft': 30, 'defense': 40},
        )
        self.assertIsNone(points)

    def test_weights_must_sum_100(self):
        with self.assertRaises(logic.TfmRuleError):
            logic.weighted_points(
                {'tutor': 8, 'draft': 8, 'defense': 8},
                {'tutor': 30, 'draft': 30, 'defense': 30},
            )

    def test_zero_is_a_real_grade(self):
        points = logic.weighted_points(
            {'tutor': 0, 'draft': 0, 'defense': 0},
            {'tutor': 30, 'draft': 30, 'defense': 40},
        )
        self.assertEqual(points, 0.0)

    def test_score_between_zero_and_one_is_invalid(self):
        self.assertFalse(logic.score_is_valid(0.4))


class WindowTest(unittest.TestCase):
    def test_student_close_replaces_only_that_date(self):
        opening, closing = logic.effective_dates(
            date(2026, 6, 1), date(2026, 6, 15), None, date(2026, 6, 16),
        )
        self.assertEqual(opening, date(2026, 6, 1))
        self.assertEqual(closing, date(2026, 6, 16))
        self.assertTrue(logic.window_is_open(opening, closing, date(2026, 6, 16)))
        self.assertFalse(logic.window_is_open(
            date(2026, 6, 1), date(2026, 6, 15), date(2026, 6, 16),
        ))


class OutlineTextTest(unittest.TestCase):
    def test_renders_answers(self):
        text = logic.render_outline_text(2, [{
            'section': 'Propuesta',
            'title': 'Título',
            'answer': 'Un TFM',
        }])
        self.assertIn('Versión: 2', text)
        self.assertIn('Un TFM', text)

    def test_rejects_bad_feedback_file(self):
        with self.assertRaises(logic.TfmRuleError):
            logic.safe_feedback_name('notas.exe', 10)
        self.assertEqual(
            logic.safe_feedback_name('retro.pdf', 10),
            'retro.pdf',
        )


if __name__ == '__main__':
    unittest.main()
