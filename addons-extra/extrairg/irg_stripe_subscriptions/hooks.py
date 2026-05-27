# -*- coding: utf-8 -*-
import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    """
    Se ejecuta antes de cargar los modelos en la base de datos.
    Prepara la columna sale_order.stripe_subscription_id limpiando su contenido varchar 
    para que Odoo pueda alterar su tipo a integer de forma segura sin lanzar errores de sintaxis en PostgreSQL.
    """
    _logger.info("Ejecutando pre_init_hook para irg_stripe_subscriptions: preparando base de datos.")
    
    # 1. Verificar si la columna existe en sale_order
    cr.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'sale_order' AND column_name = 'stripe_subscription_id';
    """)
    res = cr.fetchone()
    
    if res:
        col_type = res[1]
        # Si la columna es de tipo caracter/texto, necesitamos migrar sus datos a stripe_subscription_ref antes de vaciarla
        if col_type in ('character varying', 'text'):
            _logger.info("Migrando datos de la columna string stripe_subscription_id a stripe_subscription_ref en sale_order.")
            
            # Copiar datos a stripe_subscription_ref por si hay alguno que no estuviera duplicado
            cr.execute("""
                UPDATE sale_order 
                SET stripe_subscription_ref = stripe_subscription_id 
                WHERE stripe_subscription_ref IS NULL AND stripe_subscription_id IS NOT NULL;
            """)
            
            # Vaciamos la columna para que PostgreSQL permita cambiar su tipo de VARCHAR a INTEGER
            _logger.info("Vaciando sale_order.stripe_subscription_id para conversión a integer.")
            cr.execute("UPDATE sale_order SET stripe_subscription_id = NULL;")


def post_init_hook(cr, registry):
    """
    Se ejecuta después de que el módulo ha sido instalado y la columna ya es Many2one (integer).
    Reconstruye de forma retroactiva las relaciones Many2one a partir de stripe_subscription_ref.
    """
    _logger.info("Ejecutando post_init_hook para irg_stripe_subscriptions: asociando suscripciones existentes.")
    
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Buscamos órdenes que tengan la referencia de stripe pero no la suscripción Many2one enlazada
    orders = env['sale.order'].search([
        ('stripe_subscription_ref', '!=', False),
        ('stripe_subscription_id', '=', False)
    ])
    
    _logger.info("Se han encontrado %d presupuestos con referencia de Stripe para asociar.", len(orders))
    
    for order in orders:
        stripe_id = order.stripe_subscription_ref
        partner_id = order.partner_id.id if order.partner_id else False
        
        try:
            # Buscamos o creamos el registro local en stripe.subscription
            sub_record = env['stripe.subscription']._find_or_create_from_stripe_id(
                stripe_id, partner_id=partner_id
            )
            # Vinculamos la relación Many2one
            order.write({'stripe_subscription_id': sub_record.id})
            
            _logger.info("Asociada suscripción Stripe %s a la orden %s", stripe_id, order.name)
        except Exception:
            _logger.exception("Error asociando suscripción Stripe %s a la orden %s", stripe_id, order.name)
    _logger.info("post_init_hook completado con éxito.")
