from odoo import Command
from odoo.tests import TransactionCase


class MappingAdminCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.gradebook = cls.env["app.gradebook"].create(
            {
                "name": "Plantilla Test Mapping Admin",
                "grading_scale": 10,
                "gradebook_template_ids": [
                    Command.create({"type": "exam", "weight": 100, "qty": 1})
                ],
            }
        )
        cls.course = cls.env["op.course"].create(
            {
                "name": "Curso Test Mapping Admin",
                "code": "CT-MAP-ADMIN",
                "lang": "en_US",
                "gradebook_id": cls.gradebook.id,
            }
        )
        cls.subject = cls.env["op.subject"].create(
            {
                "name": "Asignatura Test Mapping Admin",
                "code": "AT-MAP-ADMIN",
                "course_id": cls.course.id,
                "gradebook_id": cls.gradebook.id,
            }
        )
        cls.course.write({"subject_ids": [Command.link(cls.subject.id)]})
        cls.course_map = cls.env["irg.gradebook.moodle.course.map"].create(
            {
                "op_course_id": cls.course.id,
                "moodle_course_id": 350001,
                "moodle_course_name": "Curso Test Mapping Admin",
            }
        )
        cls.subject_map = cls.env["irg.gradebook.moodle.map"].create(
            {
                "op_subject_id": cls.subject.id,
                "moodle_course_id": cls.course_map.moodle_course_id,
                "course_map_id": cls.course_map.id,
            }
        )
        cls.env["irg.gradebook.moodle.map.line"].create(
            [
                {
                    "map_id": cls.subject_map.id,
                    "moodle_activity_id": 395,
                    "activity_type": "quiz",
                },
                {
                    "map_id": cls.subject_map.id,
                    "moodle_activity_id": 397,
                    "activity_type": "quiz",
                },
            ]
        )
