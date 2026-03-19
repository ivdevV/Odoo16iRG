#!/usr/bin/env python3
"""Genera un CSV listo para importar excepciones (`price_exceptions.csv`).

Uso:
  python generate_exceptions_import_from_tarifario.py tarifario.csv output.csv --price-column "1 Mes" [--mapping mapping.csv]

Descripción:
- `tarifario.csv` debe tener columnas que incluyan al menos el nombre del producto y columnas de precio (ej.: '1 Mes').
- `mapping.csv` (opcional) debe contener dos columnas: `tarifa_name,default_code`. Si se proporciona se usará `default_code` (más seguro).
- Si no hay mapping para una fila, se pone el nombre del producto en la columna `product` (fallback, frágil).
"""
import csv
import sys
import argparse


def load_mapping(path):
    m = {}
    with open(path, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            name = (row.get('tarifa_name') or row.get('name') or row.get('product'))
            if name:
                name = name.strip()
            code = (row.get('default_code') or row.get('product_ref') or '')
            if code:
                code = code.strip()
            if name and code:
                m[name] = code
    return m


def parse_number(s):
    if s is None:
        return None
    s = s.strip()
    if s == '':
        return None
    # remove thousands separator and replace comma decimal
    s = s.replace('.', '').replace(',', '.')
    try:
        return float(s)
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('tarifario')
    parser.add_argument('output')
    parser.add_argument('--price-column', required=True, help='Nombre exacto de la columna de precio a usar (ej. "1 Mes")')
    parser.add_argument('--mapping', help='CSV con columnas tarifa_name,default_code para usar default_code en lugar de nombre')
    args = parser.parse_args()

    mapping = {}
    if args.mapping:
        mapping = load_mapping(args.mapping)

    with open(args.tarifario, newline='', encoding='utf-8') as inf, open(args.output, 'w', newline='', encoding='utf-8') as outf:
        reader = csv.DictReader(inf)
        fieldnames = ['product_ref', 'product', 'price_exception', 'name', 'active', 'note']
        writer = csv.DictWriter(outf, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            # get product identifier from tarifario row: prefer 'Product' or 'Tipo de Tarifa' or first column
            tarifa_name = None
            for k in ('Product', 'product', 'Tipo de Tarifa', 'Tipo de tarifa', 'Categoría', 'Modalidad'):
                if k in row and row[k] and row[k].strip():
                    tarifa_name = row[k].strip()
                    break
            if not tarifa_name:
                # fallback to first non-empty cell
                for v in row.values():
                    if v and v.strip():
                        tarifa_name = v.strip()
                        break
            price_raw = row.get(args.price_column)
            price = parse_number(price_raw)
            if price is None:
                continue
            default_code = mapping.get(tarifa_name)
            writer.writerow({
                'product_ref': default_code or '',
                'product': '' if default_code else tarifa_name,
                'price_exception': '%.2f' % price,
                'name': 'Excepción %s' % tarifa_name,
                'active': 'True',
                'note': '',
            })


if __name__ == '__main__':
    main()
