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


class DeliveryStageTest(unittest.TestCase):
    def test_each_block_has_provisional_and_final(self):
        self.assertEqual(logic.DELIVERY_STAGES, (
            'partial_provisional',
            'partial',
            'final_provisional',
            'final',
        ))
        self.assertEqual(
            set(logic.DELIVERY_STAGE_DATES),
            set(logic.DELIVERY_STAGES),
        )


class BatchEligibilityTest(unittest.TestCase):
    def test_online_starts_at_second_convocation_of_2026(self):
        cases = {
            'ONL261': False,
            'ONL262': ('ONL', 262),
            'MPSCONL263': ('ONL', 263),
            'ONL264': ('ONL', 264),
            'ONL271': ('ONL', 271),
            'ONL254': False,
            'ONL2602': False,
            'MOPCONL2606': False,
            'MONLONL262': ('ONL', 262),
            'HC2509': False,
            'HC2511': ('HC', 2511),
            'MONLHC2511': False,
            'monlhc2601': ('HC', 2601),
            'PRS-ONL262': False,
            'PRS-HC2701': False,
            'other': False,
        }
        for code, result in cases.items():
            self.assertEqual(logic.irg_parse_tfm_batch_eligibility(code), result, code)


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
