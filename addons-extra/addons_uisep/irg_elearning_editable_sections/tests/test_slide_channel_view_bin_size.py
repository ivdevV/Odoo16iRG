import unittest
from pathlib import Path
from xml.etree import ElementTree as ET


class TestSlideChannelViewBinSize(unittest.TestCase):
    """Regresión estática para no leer adjuntos binarios en onchanges de slides."""

    @classmethod
    def setUpClass(cls):
        cls.view_path = Path(__file__).resolve().parents[1] / 'views' / 'slide_channel_view.xml'
        cls.root = ET.parse(cls.view_path).getroot()

    def _context_attribute_for_xpath(self, field_name):
        matches = []
        needle = "field[@name='%s']" % field_name
        for xpath_node in self.root.findall('.//xpath'):
            if needle not in xpath_node.attrib.get('expr', ''):
                continue
            for attr_node in xpath_node.findall("attribute[@name='context']"):
                matches.append(attr_node.text or '')
        self.assertEqual(len(matches), 1, 'Debe existir un único context para %s' % field_name)
        return matches[0]

    def _field_context(self, field_name):
        fields = self.root.findall(".//field[@name='%s']" % field_name)
        self.assertEqual(len(fields), 1, 'Debe existir un único field %s' % field_name)
        return fields[0].attrib.get('context', '')

    def _assert_bin_size_true(self, context):
        compact = context.replace(' ', '')
        self.assertIn("'bin_size':True", compact)

    def test_slide_ids_context_uses_bin_size_and_keeps_default_channel(self):
        context = self._context_attribute_for_xpath('slide_ids')
        self._assert_bin_size_true(context)
        self.assertIn("'default_channel_id': active_id", context)

    def test_native_sections_context_uses_bin_size_and_keeps_defaults(self):
        context = self._field_context('irg_native_section_ids')
        self._assert_bin_size_true(context)
        self.assertIn("'default_channel_id': active_id", context)
        self.assertIn("'default_is_category': True", context)
        self.assertIn("'default_slide_category': 'article'", context)


if __name__ == '__main__':
    unittest.main()
