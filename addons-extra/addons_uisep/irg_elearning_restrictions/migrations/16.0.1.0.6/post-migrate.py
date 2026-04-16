"""
Migración 16.0.1.0.5 → 16.0.1.0.6
Copia los datos de restriction_slide_id (Many2one) a restriction_slide_ids (Many2many).
La tabla de relación es slide_restriction_rel (slide_id, required_slide_id).
"""


def migrate(cr, version):
    if not version:
        return

    # Insertar en la tabla M2M los pares que existían en el campo Many2one
    cr.execute("""
        INSERT INTO slide_restriction_rel (slide_id, required_slide_id)
        SELECT id, restriction_slide_id
        FROM slide_slide
        WHERE restriction_slide_id IS NOT NULL
        ON CONFLICT DO NOTHING
    """)
    cr.execute("SELECT COUNT(*) FROM slide_restriction_rel")
    count = cr.fetchone()[0]
    import logging
    _logger = logging.getLogger(__name__)
    _logger.info(
        "irg_elearning_restrictions migration: %d prerequisite relation(s) migrated "
        "from restriction_slide_id to restriction_slide_ids.", count
    )
