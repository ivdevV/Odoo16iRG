# irg_portal_invoice_hide_pay_now

**Categoría:** Accounting
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `account`, `account_payment`

---

## ¿Qué hace este módulo?

Oculta los botones de "Pagar ahora" del portal de facturas para todos los usuarios. Esto incluye:

- El botón "Pagar ahora" en la lista de facturas (`/my/invoices`)
- El botón "Pagar ahora" en el detalle de cada factura
- El bloque de checkout de pago online

## Funcionalidades principales

- Hereda las vistas de `account_payment` para eliminar los elementos de pago del portal
- No modifica módulos base, solo oculta elementos mediante herencia de vistas
- Aplica a todos los usuarios del portal (alumnos y clientes)

## Modelos

| Modelo | Tipo | Descripción |
|--------|------|-------------|
| N/A | Solo vistas | No añade ni modifica modelos |

## Instalación / Actualización

```bash
# Instalar
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf \
    -d odoo16irg_local -i irg_portal_invoice_hide_pay_now \
    --stop-after-init --db_host=pgodoo16irg_local

# Actualizar
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf \
    -d odoo16irg_local -u irg_portal_invoice_hide_pay_now \
    --stop-after-init --db_host=pgodoo16irg_local
```

## Pruebas realizadas

- [x] Instalación exitosa en Odoo 16 local
- [x] Sin errores de XML al cargar las vistas
- [ ] Verificación visual en `/my/invoices` (pendiente revisión usuario)
- [ ] Verificación visual en detalle de factura (pendiente revisión usuario)

## Criterios de uso

- Instalar cuando se quiera deshabilitar el pago online desde el portal
- Compatible con cualquier configuración de proveedores de pago
- No afecta al backend, solo al portal público

## Limitaciones conocidas

- Si se desinstala este módulo, los botones volverán a aparecer
- No deshabilita los proveedores de pago en sí, solo oculta los botones del portal

## Changelog

### 16.0.1.0.0 (2026-06-02)
- Versión inicial
- Oculta botón "Pagar ahora" en lista de facturas
- Oculta botón "Pagar ahora" en detalle de factura
- Oculta bloque de checkout de pago
