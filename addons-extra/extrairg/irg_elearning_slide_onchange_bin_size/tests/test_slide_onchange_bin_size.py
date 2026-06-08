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

    def test_onchange_filters_binary_field_onchange_entries(self):
        self.assertIn('_filter_binary_field_onchange', self.source)
        self.assertIn('field_onchange.items()', self.source)
        self.assertIn("name.split('.')[-1]", self.source)
        self.assertIn('BINARY_FIELD_ONCHANGE_NAMES', self.source)
        self.assertIn("'binary_content'", self.source)
        self.assertIn("'image_binary_content'", self.source)


if __name__ == '__main__':
    unittest.main()
