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


class TestSlideChannelOnchangeBinSize(unittest.TestCase):
    """Regresion estatica para onchange de slide.channel con lineas slide.slide."""

    @classmethod
    def setUpClass(cls):
        cls.model_path = Path(__file__).resolve().parents[1] / 'models' / 'slide_channel.py'
        cls.source = cls.model_path.read_text(encoding='utf-8')

    def test_onchange_extends_slide_channel_and_forces_bin_size(self):
        self.assertIn("_inherit = 'slide.channel'", self.source)
        self.assertIn('def onchange', self.source)
        self.assertIn('with_context(bin_size=True)', self.source)
        self.assertIn("self.env.context.get('bin_size')", self.source)
        self.assertIn('super', self.source)

    def test_onchange_is_limited_to_slide_relations(self):
        self.assertIn('SLIDE_RELATION_FIELD_NAMES', self.source)
        self.assertIn("'slide_ids'", self.source)
        self.assertIn("'irg_native_section_ids'", self.source)
        self.assertIn("'irg_online_slide_ids'", self.source)
        self.assertIn("'irg_online_section_ids'", self.source)
        self.assertIn('_is_slide_relation_onchange', self.source)

    def test_onchange_filters_binary_fields_by_relation_prefix(self):
        self.assertIn('_filter_slide_relation_binary_field_onchange', self.source)
        self.assertIn('_is_slide_relation_binary_field_onchange', self.source)
        self.assertIn('field_onchange.items()', self.source)
        self.assertIn("name.split('.')", self.source)
        self.assertIn('parts[0] in SLIDE_RELATION_FIELD_NAMES', self.source)
        self.assertIn('parts[-1] in BINARY_FIELD_ONCHANGE_NAMES', self.source)
        self.assertIn("'binary_content'", self.source)
        self.assertIn("'image_binary_content'", self.source)
        self.assertIn("'image_1920'", self.source)


if __name__ == '__main__':
    unittest.main()
