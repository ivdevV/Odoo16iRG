# -*- coding: utf-8 -*-


def migrate(cr, version):
    cr.execute("""
        SELECT to_regclass('public.irg_scholarship_type'),
               to_regclass('public.res_partner'),
               to_regclass('public.op_scholarship_type')
    """)
    old_type_table, partner_table, openeducat_type_table = cr.fetchone()
    if not old_type_table or not partner_table or not openeducat_type_table:
        return

    cr.execute("""
        UPDATE res_partner partner
           SET irg_scholarship_type_id = openeducat_type.id
          FROM irg_scholarship_type old_type
          JOIN op_scholarship_type openeducat_type
            ON lower(trim(openeducat_type.name)) = lower(trim(old_type.name))
         WHERE partner.irg_scholarship_type_id = old_type.id
    """)
    cr.execute("""
        UPDATE res_partner partner
           SET irg_scholarship_type_id = NULL
         WHERE irg_scholarship_type_id IS NOT NULL
           AND NOT EXISTS (
               SELECT 1
                 FROM op_scholarship_type openeducat_type
                WHERE openeducat_type.id = partner.irg_scholarship_type_id
           )
    """)