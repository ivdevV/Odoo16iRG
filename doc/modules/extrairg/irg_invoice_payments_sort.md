# irg_invoice_payments_sort

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `account`, `account_payment_return`

---

## ¿Qué hace este módulo?

Ordena las entradas del widget de pagos de facturas por fecha ascendente. En Odoo estándar, los pagos asociados a una factura se muestran en el orden en que se registraron; este módulo los reordena cronológicamente para facilitar la auditoría y el seguimiento del historial de cobros.

## Funcionalidades principales

- Override del widget de pagos de facturas para ordenar por fecha ascendente.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `account.move` | Herencia | Ordenación del widget de pagos |

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_invoice_payments_sort \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_invoice_payments_sort \
    --stop-after-init --db_host=pgodoo_latest
```
