# -*- coding: utf-8 -*-
"""Copia la consigna actual al texto de la alumna si ese texto aún está vacío.

No borra prompt ni reescribe un texto de alumna que ya sea distinto.
"""


def migrate(cr, version):
    cr.execute(
        """
        UPDATE irg_oral_case_segment
           SET student_text = prompt
         WHERE (student_text IS NULL OR btrim(student_text) = '')
           AND prompt IS NOT NULL
           AND btrim(prompt) <> ''
        """
    )
