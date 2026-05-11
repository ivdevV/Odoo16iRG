# -*- coding: utf-8 -*-


def _name_text_expression(cr, table_name, column_name, alias):
    cr.execute(
        """
        SELECT data_type
          FROM information_schema.columns
         WHERE table_schema = 'public'
           AND table_name = %s
           AND column_name = %s
        """,
        (table_name, column_name),
    )
    result = cr.fetchone()
    if result and result[0] == 'jsonb':
        return """
            COALESCE(
                {alias}.{column}->>'es_ES',
                {alias}.{column}->>'en_US',
                (
                    SELECT value
                      FROM jsonb_each_text({alias}.{column})
                     ORDER BY CASE
                         WHEN key = 'es_ES' THEN 0
                         WHEN key = 'en_US' THEN 1
                         ELSE 2
                     END
                     LIMIT 1
                )
            )
        """.format(alias=alias, column=column_name)
    return "{alias}.{column}::text".format(alias=alias, column=column_name)


def migrate(cr, version):
    cr.execute("""
        SELECT to_regclass('public.irg_scholarship_type'),
               to_regclass('public.res_partner'),
               to_regclass('public.op_scholarship_type')
    """)
    old_type_table, partner_table, openeducat_type_table = cr.fetchone()
    if not old_type_table or not partner_table or not openeducat_type_table:
        return

    old_type_name = _name_text_expression(
        cr, 'irg_scholarship_type', 'name', 'old_type'
    )
    openeducat_type_name = _name_text_expression(
        cr, 'op_scholarship_type', 'name', 'openeducat_type'
    )

    cr.execute("""
        UPDATE res_partner partner
           SET irg_scholarship_type_id = openeducat_type.id
          FROM irg_scholarship_type old_type
          JOIN op_scholarship_type openeducat_type
            ON lower(trim({openeducat_type_name})) = lower(trim({old_type_name}))
         WHERE partner.irg_scholarship_type_id = old_type.id
    """.format(
        openeducat_type_name=openeducat_type_name,
        old_type_name=old_type_name,
    ))
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