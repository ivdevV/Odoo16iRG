import unittest
from pathlib import Path


class TestSlideOnchangeBinSize(unittest.TestCase):
    """Regresion estatica para forzar bin_size en onchange de slide.slide."""

    @classmethod
    def setUpClass(cls):
        cls.model_path = Path(__file__).resolve().parents[1] / 'models' / 'slide_slide.py'
        cls.source = cls.model_path.read_text(encoding='utf-8')

    def test_onchange_forces_bin_size_context(self):
        self.assertIn('def onchange', self.source)
        self.assertIn('with_context(bin_size=True)', self.source)
        self.assertIn("self.env.context.get('bin_size')", self.source)
        self.assertIn('super', self.source)


if __name__ == '__main__':
    unittest.main()
