"""Importador de excepciones desde productos '(Convenio)'.

Uso recomendado (dentro del servidor Odoo):
  odoo-bin shell -d <db> -c <config>
  >>> exec(open('addons-extra/extrairg/irg_custom_discount/scripts/import_exceptions_from_convenio.py').read())

También puede ejecutarse remotamente vía XML-RPC estableciendo las variables de entorno
ODDO_RPC_HOST, ODOO_RPC_PORT, ODOO_RPC_DB, ODOO_RPC_USER, ODOO_RPC_PASS

Comportamiento:
 - Busca productos cuya referencia de nombre contenga '(Convenio)'.
 - Busca su homólogo base (removiendo ' (Convenio)') por plantilla o nombre del producto.
 - Crea un registro `irg.discount.exception` con el precio convenio (list_price) si difiere del precio base.
 - Imprime un resumen de cambios.
"""
from __future__ import print_function
import os
import re
import sys


def _run_in_env(env):
    Product = env['product.product']
    Template = env['product.template']
    Exception = env['irg.discount.exception']

    convenio_products = Product.search([('name', 'ilike', '(Convenio)')])
    if not convenio_products:
        convenio_products = Product.search([('product_tmpl_id.name', 'ilike', '(Convenio)')])

    created = 0
    skipped = 0
    for p in convenio_products:
        # nombre base: quitar "(Convenio)" y variaciones
        base_name = re.sub(r"\s*\(Convenio\)\s*", '', p.product_tmpl_id.name or p.name, flags=re.IGNORECASE).strip()

        # intentar encontrar plantilla base por nombre exacto
        tmpl = Template.search([('name', '=', base_name)], limit=1)
        product = None
        if tmpl:
            # preferir variante única o primera variante
            product = Product.search([('product_tmpl_id', '=', tmpl.id)], limit=1)
        else:
            # buscar producto por nombre
            product = Product.search([('name', '=', base_name)], limit=1)

        convenio_price = getattr(p, 'list_price', None) or getattr(p, 'lst_price', None) or getattr(p, 'price', None)
        if convenio_price is None:
            print('WARNING: no se encontró precio para', p.display_name)
            skipped += 1
            continue

        if product:
            # si ya existe excepción activa exacta, saltar
            existing = Exception.search([
                ('active', '=', True),
                '|', ('product_id', '=', product.id), ('product_tmpl_id', '=', product.product_tmpl_id.id),
                ('price_exception', '=', convenio_price)
            ], limit=1)
            if existing:
                skipped += 1
                continue

            name = 'Excepción convenio %s' % (product.default_code or product.name)
            Exception.create({
                'name': name,
                'product_id': product.id,
                'product_tmpl_id': False,
                'price_exception': float(convenio_price),
                'active': True,
            })
            created += 1
        else:
            # si no se encontró variante, intentar crear por plantilla con product_tmpl_id
            tmpl_exact = Template.search([('name', '=', base_name)], limit=1)
            if tmpl_exact:
                existing = Exception.search([
                    ('active', '=', True), ('product_tmpl_id', '=', tmpl_exact.id), ('price_exception', '=', convenio_price)
                ], limit=1)
                if existing:
                    skipped += 1
                    continue
                Exception.create({
                    'name': 'Excepción convenio %s' % tmpl_exact.name,
                    'product_tmpl_id': tmpl_exact.id,
                    'price_exception': float(convenio_price),
                    'active': True,
                })
                created += 1
            else:
                print('No se encontró homólogo para', p.display_name, 'base_name=', base_name)
                skipped += 1

    print('Summary: created=%s skipped=%s total_convenio=%s' % (created, skipped, len(convenio_products)))


def _run_via_xmlrpc(host, port, db, user, password):
    import xmlrpc.client
    url = 'http://%s:%s/xmlrpc/2/common' % (host, port)
    common = xmlrpc.client.ServerProxy(url)
    uid = common.authenticate(db, user, password, {})
    if not uid:
        print('Authentication failed')
        return
    models = xmlrpc.client.ServerProxy('http://%s:%s/xmlrpc/2/object' % (host, port))

    # buscar productos convenio
    convenio_ids = models.execute_kw(db, uid, password, 'product.product', 'search', [[['name', 'ilike', '(Convenio)']]])
    total = len(convenio_ids)
    created = 0
    skipped = 0
    for pid in convenio_ids:
        p = models.execute_kw(db, uid, password, 'product.product', 'read', [pid], {'fields': ['id', 'name', 'product_tmpl_id', 'list_price', 'default_code']})
        if isinstance(p, list):
            p = p[0]
        base_name = p.get('product_tmpl_id') and p['product_tmpl_id'][1] or p.get('name')
        base_name = re.sub(r"\s*\(Convenio\)\s*", '', base_name, flags=re.IGNORECASE).strip()

        # buscar plantilla base
        tmpl_ids = models.execute_kw(db, uid, password, 'product.template', 'search', [[['name', '=', base_name]]])
        product_id = None
        if tmpl_ids:
            prod_ids = models.execute_kw(db, uid, password, 'product.product', 'search', [[['product_tmpl_id', '=', tmpl_ids[0]]]], {'limit': 1})
            if prod_ids:
                product_id = prod_ids[0]
        else:
            prod_ids = models.execute_kw(db, uid, password, 'product.product', 'search', [[['name', '=', base_name]]], {'limit': 1})
            if prod_ids:
                product_id = prod_ids[0]

        convenio_price = p.get('list_price')
        if not convenio_price:
            skipped += 1
            continue

        if product_id:
            # comprobar existencia
            exists = models.execute_kw(db, uid, password, 'irg.discount.exception', 'search', [[['active', '=', True], ['product_id', '=', product_id], ['price_exception', '=', convenio_price]]], {'limit': 1})
            if exists:
                skipped += 1
                continue
            vals = {'name': 'Excepción convenio %s' % (p.get('default_code') or p.get('name')), 'product_id': product_id, 'price_exception': float(convenio_price), 'active': True}
            models.execute_kw(db, uid, password, 'irg.discount.exception', 'create', [vals])
            created += 1
        else:
            if tmpl_ids:
                exists = models.execute_kw(db, uid, password, 'irg.discount.exception', 'search', [[['active', '=', True], ['product_tmpl_id', '=', tmpl_ids[0]], ['price_exception', '=', convenio_price]]], {'limit': 1})
                if exists:
                    skipped += 1
                    continue
                vals = {'name': 'Excepción convenio %s' % base_name, 'product_tmpl_id': tmpl_ids[0], 'price_exception': float(convenio_price), 'active': True}
                models.execute_kw(db, uid, password, 'irg.discount.exception', 'create', [vals])
                created += 1
            else:
                skipped += 1

    print('Summary: created=%s skipped=%s total_convenio=%s' % (created, skipped, total))


if __name__ == '__main__':
    # If run inside odoo-bin shell, 'env' is available in globals()
    if 'env' in globals():
        _run_in_env(env)
        sys.exit(0)

    # else try XML-RPC using environment variables
    host = os.environ.get('ODOO_RPC_HOST') or os.environ.get('ODOO_HOST') or 'localhost'
    port = os.environ.get('ODOO_RPC_PORT') or os.environ.get('ODOO_PORT') or '8069'
    db = os.environ.get('ODOO_RPC_DB') or os.environ.get('ODOO_DB')
    user = os.environ.get('ODOO_RPC_USER') or os.environ.get('ODOO_USER')
    password = os.environ.get('ODOO_RPC_PASS') or os.environ.get('ODOO_PASS')

    if not (db and user and password):
        print('XML-RPC credentials not provided in environment and not running inside Odoo shell. Exiting.')
        sys.exit(2)

    _run_via_xmlrpc(host, port, db, user, password)
