# -*- coding: utf-8 -*-
"""Mueve las observaciones previas a la entrega provisional del borrador."""


def migrate(cr, version):
    cr.execute(
        """
        SELECT 1
          FROM information_schema.columns
         WHERE table_name = 'irg_tfm_convocatoria'
           AND column_name = 'preliminary_open_date'
        """
    )
    if cr.fetchone():
        cr.execute(
            """
            UPDATE irg_tfm_convocatoria
               SET partial_provisional_open_date = COALESCE(
                       partial_provisional_open_date, preliminary_open_date
                   ),
                   partial_provisional_close_date = COALESCE(
                       partial_provisional_close_date, preliminary_close_date
                   )
             WHERE preliminary_open_date IS NOT NULL
                OR preliminary_close_date IS NOT NULL
            """
        )

    cr.execute(
        """
        SELECT 1
          FROM information_schema.tables
         WHERE table_name = 'irg_tfm_ventana_alumno'
        """
    )
    if cr.fetchone():
        cr.execute(
            """
            UPDATE irg_tfm_ventana_alumno AS provisional
               SET open_date = COALESCE(provisional.open_date, preliminary.open_date),
                   close_date = COALESCE(provisional.close_date, preliminary.close_date)
              FROM irg_tfm_ventana_alumno AS preliminary
             WHERE provisional.thesis_id = preliminary.thesis_id
               AND provisional.stage = 'partial_provisional'
               AND preliminary.stage = 'preliminary'
            """
        )
        cr.execute(
            """
            DELETE FROM irg_tfm_ventana_alumno AS preliminary
             WHERE stage = 'preliminary'
               AND EXISTS (
                    SELECT 1
                      FROM irg_tfm_ventana_alumno AS provisional
                     WHERE provisional.thesis_id = preliminary.thesis_id
                       AND provisional.stage = 'partial_provisional'
               )
            """
        )
        cr.execute(
            """
            UPDATE irg_tfm_ventana_alumno
               SET stage = 'partial_provisional'
             WHERE stage = 'preliminary'
            """
        )

    cr.execute(
        """
        UPDATE irg_tfm_entrega
           SET stage = 'partial_provisional'
         WHERE stage = 'preliminary'
        """
    )
