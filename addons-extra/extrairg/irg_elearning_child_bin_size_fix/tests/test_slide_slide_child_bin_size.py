import unittest
from pathlib import Path
from xml.etree import ElementTree as ET


class TestSlideSlideChildBinSize(unittest.TestCase):
    """Regresion estatica para no cargar binarios reales en hijos de secciones."""

    @classmethod
    def setUpClass(cls):
        cls.view_path = Path(__file__).resolve().parents[1] / 'views' / 'slide_slide_views.xml'
        cls.root = ET.parse(cls.view_path).getroot()

    def test_child_slide_ids_context_uses_bin_size_and_keeps_defaults(self):
        matches = []
        for xpath_node in self.root.findall('.//xpath'):
            if "field[@name='child_slide_ids']" in xpath_node.attrib.get('expr', ''):
                matches.append(xpath_node)

        self.assertEqual(len(matches), 1, 'Debe existir un unico xpath para child_slide_ids')
        self.assertEqual(matches[0].attrib.get('position'), 'attributes')

        context_nodes = matches[0].findall("attribute[@name='context']")
        self.assertEqual(len(context_nodes), 1, 'Debe existir un unico atributo context')
        context = context_nodes[0].text or ''
        compact = context.replace(' ', '')

        self.assertIn("'bin_size':True", compact)
        self.assertIn("'default_channel_id': channel_id", context)
        self.assertIn("'default_parent_slide_id': id", context)
        self.assertIn("'default_inherit_limitations_from_parent': True", context)


if __name__ == '__main__':
    unittest.main()
