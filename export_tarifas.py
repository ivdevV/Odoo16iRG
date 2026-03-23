#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para exportar tarifas base de productos (Opción 1: Descuentos Dinámicos)
Genera CSV con precios base y ejemplos de descuentos aplicados
"""

import os
import sys
import csv
from datetime import datetime

# Configuración de conexión a Odoo
ODOO_URL = os.environ.get('ODOO_URL', 'http://localhost:8069')
ODOO_DB = os.environ.get('ODOO_DB', 'odoo16')
ODOO_USER = os.environ.get('ODOO_USER', 'admin')
ODOO_PASS = os.environ.get('ODOO_PASS', 'admin')

try:
    import xmlrpc.client as xmlrpc
except ImportError:
    print("Error: xmlrpc no disponible. Usa: pip install xmlrpc")
    sys.exit(1)


def connect_to_odoo():
    """Conectar a Odoo via XML-RPC"""
    common = xmlrpc.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASS, {})
    if not uid:
        raise Exception("Autenticación fallida")
    
    models = xmlrpc.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
    return models, uid


def get_masters_with_variants(models, uid):
    """Obtener todos los Máster (product.template) con sus variantes"""
    
    # Buscar templates que sean Máster
    template_ids = models.execute_kw(
        ODOO_DB, uid, ODOO_PASS,
        'product.template', 'search',
        [('name', 'ilike', 'Máster')]
    )
    
    templates = models.execute_kw(
        ODOO_DB, uid, ODOO_PASS,
        'product.template', 'read',
        template_ids,
        ['id', 'name', 'list_price', 'product_variant_ids', 'attribute_line_ids']
    )
    
    result = []
    for template in templates:
        variant_ids = template.get('product_variant_ids', [])
        
        if variant_ids:
            # Leer variantes
            variants = models.execute_kw(
                ODOO_DB, uid, ODOO_PASS,
                'product.product', 'read',
                variant_ids,
                ['id', 'name', 'list_price', 'attribute_value_ids']
            )
            for var in variants:
                result.append({
                    'template_id': template['id'],
                    'template_name': template['name'],
                    'variant_id': var['id'],
                    'variant_name': var['name'],
                    'list_price': var.get('list_price', 0.0),
                })
        else:
            # Si no hay variantes, usar el template
            result.append({
                'template_id': template['id'],
                'template_name': template['name'],
                'variant_id': None,
                'variant_name': template['name'],
                'list_price': template.get('list_price', 0.0),
            })
    
    return result


def calculate_discount_prices(price_base, discounts=[10, 15, 20, 25]):
    """Calcular precios con descuentos aplicados"""
    return {
        f'precio_{pct}pct': round(price_base * (1 - pct/100), 2)
        for pct in discounts
    }


def export_to_csv(products, filename='tarifas_opcion1.csv'):
    """Exportar a CSV"""
    
    if not products:
        print("❌ No se encontraron productos")
        return
    
    # Preparar datos con descuentos
    rows = []
    for prod in products:
        row = {
            'ID Template': prod['template_id'],
            'Plantilla': prod['template_name'],
            'ID Variante': prod['variant_id'] or 'N/A',
            'Variante': prod['variant_name'],
            'Precio Base (Lista)': f"{prod['list_price']:.2f}",
            'Precio con -10%': f"{prod['list_price'] * 0.90:.2f}",
            'Precio con -15%': f"{prod['list_price'] * 0.85:.2f}",
            'Precio con -20%': f"{prod['list_price'] * 0.80:.2f}",
            'Precio con -25%': f"{prod['list_price'] * 0.75:.2f}",
        }
        rows.append(row)
    
    # Escribir CSV
    fieldnames = list(rows[0].keys())
    
    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✅ Exportado: {filename} ({len(rows)} productos)")
    return filename


def export_to_json(products, filename='tarifas_opcion1.json'):
    """Exportar a JSON"""
    import json
    
    if not products:
        print("❌ No se encontraron productos")
        return
    
    data = {
        'exportado': datetime.now().isoformat(),
        'total_productos': len(products),
        'descuentos_aplicables': [10, 15, 20, 25],
        'productos': []
    }
    
    for prod in products:
        data['productos'].append({
            'template_id': prod['template_id'],
            'plantilla': prod['template_name'],
            'variante_id': prod['variant_id'],
            'variante_nombre': prod['variant_name'],
            'precio_base': prod['list_price'],
            'precios_con_descuento': {
                '_10pct': round(prod['list_price'] * 0.90, 2),
                '_15pct': round(prod['list_price'] * 0.85, 2),
                '_20pct': round(prod['list_price'] * 0.80, 2),
                '_25pct': round(prod['list_price'] * 0.75, 2),
            }
        })
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Exportado: {filename}")
    return filename


def main():
    print("=" * 60)
    print("EXPORT TARIFAS - OPCIÓN 1 (Descuentos Dinámicos)")
    print("=" * 60)
    
    try:
        print("\n🔗 Conectando a Odoo...")
        models, uid = connect_to_odoo()
        print("✅ Conectado")
        
        print("\n📋 Leyendo productos (Máster)...")
        products = get_masters_with_variants(models, uid)
        print(f"✅ Encontrados {len(products)} productos/variantes")
        
        if products:
            print(f"\n📊 Primeros 5 productos:")
            for i, p in enumerate(products[:5], 1):
                print(f"  {i}. {p['variant_name']}: €{p['list_price']:.2f}")
        
        print(f"\n💾 Exportando...")
        csv_file = export_to_csv(products)
        json_file = export_to_json(products)
        
        print(f"\n✅ Completado:")
        print(f"   - {csv_file}")
        print(f"   - {json_file}")
        print("\n💡 Usa estos archivos para:")
        print("   - Validar precios base")
        print("   - Preparar estrategia de cupones")
        print("   - Importar a Excel/Sheets para análisis")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
