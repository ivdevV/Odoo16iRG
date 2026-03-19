#!/usr/bin/env python3
"""Generador de CSV para importar excepciones de convenio en Odoo.

Uso:
  python prepare_exceptions_import.py input.csv output.csv

El CSV de entrada debe contener al menos las columnas:
  - product_ref  (Internal Reference / default_code)
  - price_exception  (precio numérico sin impuestos)
  - name (opcional)

El CSV de salida será compatible con la importación de Odoo (columna 'Product' debe mapearse a Internal Reference).
"""
import csv
import sys
from datetime import datetime


def main():
    if len(sys.argv) < 3:
        print("Usage: prepare_exceptions_import.py input.csv output.csv")
        sys.exit(1)
    infile = sys.argv[1]
    outfile = sys.argv[2]

    with open(infile, newline='', encoding='utf-8') as inf, open(outfile, 'w', newline='', encoding='utf-8') as outf:
        reader = csv.DictReader(inf)
        fieldnames = ['name', 'product', 'price_exception', 'active', 'date_from', 'date_to', 'note']
        writer = csv.DictWriter(outf, fieldnames=fieldnames)
        writer.writeheader()
        for r in reader:
            product_ref = r.get('product_ref') or r.get('default_code') or r.get('ref') or r.get('product')
            if not product_ref:
                continue
            price = r.get('price_exception') or r.get('convenio_price') or r.get('convenio')
            if not price:
                continue
            try:
                price_val = float(price)
            except Exception:
                continue
            name = r.get('name') or f"Excepción {product_ref}"
            note = r.get('note') or ''
            writer.writerow({
                'name': name,
                'product': product_ref,
                'price_exception': f"{price_val:.2f}",
                'active': 'True',
                'date_from': '',
                'date_to': '',
                'note': note,
            })


if __name__ == '__main__':
    main()
