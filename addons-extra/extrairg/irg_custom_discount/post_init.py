# -*- coding: utf-8 -*-
import csv
import os
from odoo import api, SUPERUSER_ID


def _create_exception_from_row(env, row):
    Product = env['product.product']
    Template = env['product.template']
    Exception = env['irg.discount.exception']

    product_ref = (row.get('product_ref') or row.get('product') or '').strip()
    price = row.get('price_exception') or row.get('price')
    name = row.get('name') or ''
    active = row.get('active', 'True') in ('1', 'True', 'true', 'T')
    note = row.get('note') or ''

    try:
        price_val = float(price)
    except Exception:
        return False, 'invalid_price'

    product = None
    if product_ref:
        product = Product.search([('default_code', '=', product_ref)], limit=1)
        if not product:
            product = Product.search([('name', '=', product_ref)], limit=1)

    if product:
        # avoid duplicating identical exception
        exists = Exception.search([('product_id', '=', product.id), ('price_exception', '=', price_val)], limit=1)
        if exists:
            return False, 'exists'
        Exception.create({
            'name': name or ('Excepción %s' % (product.default_code or product.name)),
            'product_id': product.id,
            'price_exception': price_val,
            'active': active,
            'note': note,
        })
        return True, 'created'

    # try by template name
    if product_ref:
        tmpl = Template.search([('name', '=', product_ref)], limit=1)
        if tmpl:
            exists = Exception.search([('product_tmpl_id', '=', tmpl.id), ('price_exception', '=', price_val)], limit=1)
            if exists:
                return False, 'exists'
            Exception.create({
                'name': name or ('Excepción %s' % tmpl.name),
                'product_tmpl_id': tmpl.id,
                'price_exception': price_val,
                'active': active,
                'note': note,
            })
            return True, 'created'

    return False, 'not_found'


def irg_custom_discount_post_init(cr, registry):
    """Post-init hook: importa `data/price_exceptions.csv` si existe."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    module_path = os.path.dirname(__file__)
    data_path = os.path.join(module_path, 'data', 'price_exceptions.csv')
    if not os.path.exists(data_path):
        return

    created = 0
    skipped = 0
    with open(data_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            ok, reason = _create_exception_from_row(env, row)
            if ok:
                created += 1
            else:
                skipped += 1

    env.cr.commit()
    _msg = 'irg_custom_discount: import_exceptions post_init created=%s skipped=%s' % (created, skipped)
    env['ir.logging'].sudo().create({'type': 'server', 'name': 'irg_custom_discount', 'level': 'info', 'message': _msg})
