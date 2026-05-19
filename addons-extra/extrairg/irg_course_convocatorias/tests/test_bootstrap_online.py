from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'irg_course_convocatorias')
class TestBootstrapOnlineFromHomeClass(TransactionCase):
    """Verifica la rutina de bootstrap HomeClass -> Online del módulo
    irg_course_convocatorias.

    Cubre los tres síntomas reportados antes del rediseño:
      * que las copias NO modifiquen los slides HomeClass originales,
      * que se respete la jerarquía (categorías, parent, secciones iRG),
      * que se copie todo el contenido HomeClass elegible.
    """

    def setUp(self):
        super().setUp()
        self.Channel = self.env['slide.channel']
        self.Slide = self.env['slide.slide']
        self.Section = self.env['irg.slide.section']

        self.channel = self.Channel.create({
            'name': 'Curso iRG bootstrap test',
            'channel_type': 'training',
        })

        # Sección iRG con y sin slides asociados.
        self.section_with_slides = self.Section.create({
            'name': 'Sección con slides',
            'sequence': 10,
            'channel_id': self.channel.id,
        })
        self.section_empty = self.Section.create({
            'name': 'Sección vacía',
            'sequence': 20,
            'channel_id': self.channel.id,
        })

        # Categoría + 2 slides (uno con padre, otro sin) + 1 slide suelto.
        self.category = self.Slide.create({
            'name': 'Bloque 1',
            'channel_id': self.channel.id,
            'is_category': True,
            'sequence': 10,
        })
        self.slide_in_cat = self.Slide.create({
            'name': 'Lección 1',
            'channel_id': self.channel.id,
            'sequence': 20,
            'slide_category': 'article',
            'category_id': self.category.id,
            'irg_section_id': self.section_with_slides.id,
        })
        self.slide_child = self.Slide.create({
            'name': 'Lección 1.1',
            'channel_id': self.channel.id,
            'sequence': 30,
            'slide_category': 'article',
            'parent_slide_id': self.slide_in_cat.id,
        })
        self.slide_loose = self.Slide.create({
            'name': 'Lección suelta',
            'channel_id': self.channel.id,
            'sequence': 40,
            'slide_category': 'article',
        })

        # Snapshot de HomeClass para comparar después del bootstrap.
        self._homeclass_ids = self.channel.slide_ids.ids
        self._homeclass_sequences = {s.id: s.sequence for s in self.channel.slide_ids}
        self._homeclass_section_ids = self.channel.irg_section_ids.ids

    def _homeclass_slides(self):
        return self.channel.slide_ids.filtered(
            lambda s: s.irg_content_modality in (False, 'homeclass')
        )

    def _online_slides(self):
        return self.channel.slide_ids.filtered(
            lambda s: s.irg_content_modality == 'online'
        )

    def test_bootstrap_creates_independent_online_copies(self):
        result = self.channel.action_copy_homeclass_to_online()
        self.assertEqual(result['type'], 'ir.actions.client')

        online = self._online_slides()
        self.assertEqual(
            len(online), len(self._homeclass_ids),
            "Se debe copiar un slide Online por cada slide HomeClass elegible",
        )

        # HomeClass intacto: mismos ids y mismas secuencias.
        homeclass = self._homeclass_slides()
        self.assertEqual(set(homeclass.ids), set(self._homeclass_ids))
        self.assertEqual(
            set(self.channel.irg_homeclass_slide_ids.ids),
            set(self._homeclass_ids),
            "La pestaña HomeClass no debe listar las copias Online",
        )
        for slide in homeclass:
            self.assertEqual(
                slide.sequence, self._homeclass_sequences[slide.id],
                "La secuencia de los slides HomeClass no debe cambiar",
            )

    def test_bootstrap_remaps_hierarchy_within_online(self):
        self.channel.action_copy_homeclass_to_online()
        online = self._online_slides()

        copy_of_category = online.filtered(lambda s: s.name == 'Bloque 1' and s.is_category)
        copy_of_lesson = online.filtered(lambda s: s.name == 'Lección 1')
        copy_of_child = online.filtered(lambda s: s.name == 'Lección 1.1')
        self.assertEqual(len(copy_of_category), 1)
        self.assertEqual(len(copy_of_lesson), 1)
        self.assertEqual(len(copy_of_child), 1)
        self.assertEqual(
            copy_of_category.slide_category, 'article',
            "La sección Online debe conservar la categoría técnica de sección, no document",
        )
        self.assertEqual(
            copy_of_category.irg_content_modality, 'online',
            "La sección copiada debe quedar fuera del dominio HomeClass",
        )

        self.assertEqual(
            copy_of_lesson.category_id, copy_of_category,
            "La categoría de la copia debe apuntar a la copia de la categoría, no al original",
        )
        self.assertEqual(
            copy_of_child.parent_slide_id, copy_of_lesson,
            "El parent_slide_id debe remapearse a la copia online",
        )
        self.assertNotIn(
            copy_of_lesson.id, self._homeclass_ids,
            "La lección copiada no debe ser el original",
        )

    def test_bootstrap_clones_all_irg_sections(self):
        self.channel.action_copy_homeclass_to_online()
        all_sections = self.env['irg.slide.section'].search([
            ('channel_id', '=', self.channel.id),
        ])
        # Originales + copias (todas las secciones del canal, no sólo las referenciadas).
        self.assertEqual(
            len(all_sections),
            len(self._homeclass_section_ids) * 2,
            "Se deben clonar todas las secciones iRG del canal, también las vacías",
        )

    def test_bootstrap_empty_when_no_homeclass(self):
        empty_channel = self.Channel.create({
            'name': 'Canal vacío',
            'channel_type': 'training',
        })
        result = empty_channel.action_copy_homeclass_to_online()
        self.assertEqual(result['params']['type'], 'warning')
        self.assertFalse(empty_channel.slide_ids)

    def test_bootstrap_idempotent_append(self):
        self.channel.action_copy_homeclass_to_online()
        first_online = self._online_slides()
        self.channel.action_copy_homeclass_to_online()
        second_online = self._online_slides()
        self.assertEqual(
            len(second_online), len(first_online) * 2,
            "La segunda ejecución debe añadir un segundo lote sin tocar el primero",
        )
