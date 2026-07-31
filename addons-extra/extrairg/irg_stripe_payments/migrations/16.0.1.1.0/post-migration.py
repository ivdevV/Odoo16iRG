# -*- coding: utf-8 -*-
"""Pasa los Customers del campo antiguo al modelo ``irg.stripe.customer``.

Sin esto, los contactos que ya tenían un ``irg_stripe_customer_id`` guardado serían
invisibles para la nueva resolución de identidad, y sus pagos dejarían de vincularse
solos justo después de actualizar. En beta ya hay datos así.

Se marca ``is_primary`` porque ese valor es, por definición, el que el campo antiguo
venía reflejando.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    # Un Customer pertenece a un solo contacto. Si el dato antiguo tiene el mismo
    # `cus_...` repartido entre varios contactos, eso es una incidencia real y no se
    # resuelve aquí: se importa el primero y se deja constancia del resto.
    cr.execute(
        """
        INSERT INTO irg_stripe_customer (stripe_id, partner_id, is_primary, source,
                                         create_uid, write_uid, create_date, write_date)
        SELECT DISTINCT ON (p.irg_stripe_customer_id)
               trim(p.irg_stripe_customer_id), p.id, TRUE, 'legacy',
               1, 1, now() AT TIME ZONE 'UTC', now() AT TIME ZONE 'UTC'
          FROM res_partner p
         WHERE p.irg_stripe_customer_id IS NOT NULL
           AND trim(p.irg_stripe_customer_id) <> ''
           AND NOT EXISTS (
               SELECT 1 FROM irg_stripe_customer c
                WHERE c.stripe_id = trim(p.irg_stripe_customer_id))
         ORDER BY p.irg_stripe_customer_id, p.id
        """
    )
    _logger.info(
        "IRG Stripe: %s Customers importados desde el campo antiguo del contacto.",
        cr.rowcount)

    cr.execute(
        """
        SELECT trim(irg_stripe_customer_id), count(*)
          FROM res_partner
         WHERE irg_stripe_customer_id IS NOT NULL AND trim(irg_stripe_customer_id) <> ''
         GROUP BY 1 HAVING count(*) > 1
        """
    )
    duplicated = cr.fetchall()
    for stripe_id, count in duplicated:
        _logger.warning(
            "IRG Stripe: el Customer %s aparecía en %s contactos distintos. Se ha "
            "vinculado al de menor id; revisa el resto a mano.", stripe_id, count)
