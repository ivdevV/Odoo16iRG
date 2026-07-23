from odoo.tests import tagged

from .common import MappingAdminCommon


@tagged("post_install", "-at_install")
class TestMappingAdminModels(MappingAdminCommon):
    def test_course_and_subject_context_fields(self):
        self.assertEqual(self.course_map.irg_op_course_database_id, self.course.id)
        self.assertEqual(self.course_map.irg_subject_map_ids, self.subject_map)
        self.assertEqual(self.course_map.irg_subject_map_count, 1)
        self.assertEqual(self.subject_map.irg_op_course_id, self.course)
        self.assertEqual(
            self.subject_map.irg_op_course_database_id, self.course.id
        )
        self.assertEqual(
            self.subject_map.irg_op_subject_database_id, self.subject.id
        )
        self.assertEqual(self.subject_map.irg_op_subject_name, self.subject.name)
        self.assertEqual(self.subject_map.irg_op_subject_code, self.subject.code)
        self.assertEqual(self.subject_map.irg_activity_count, 2)
        self.assertEqual(self.subject_map.irg_activity_ids_display, "395, 397")
        self.assertEqual(
            self.subject_map._fields["irg_activity_count"].string,
            "N.º de actividades",
        )
        self.assertNotEqual(
            self.subject_map._fields["irg_activity_count"].string,
            self.subject_map._fields["line_ids"].string,
        )
