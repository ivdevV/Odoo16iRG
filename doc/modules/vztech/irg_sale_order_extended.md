# irg_sale_order_extended

**Categoría:** vztech
**Versión:** 0.1
**Licencia:** No especificada
**Instalable:** Sí
**Autor:** DFVZ TECH
**Depende de:** `base`, `hr`, `product`, `website_slides`, `sale_management`, `account_accountant`, `account_payment_mode`, `account_payment_sale`, `account_payment_order`, `account_payment_partner`, `account_payment_term_extension`, `account_banking_mandate`, `account_banking_pain_base`, `account_banking_sepa_direct_debit`

---

## ¿Qué hace este módulo?

Extiende el pedido de venta de Odoo con las integraciones bancarias necesarias para el sistema SEPA de ISEP/IRG: mandatos bancarios, órdenes de pago SEPA, modo de pago y extensiones del plazo de pago. Es la base que habilita los cobros domiciliados SEPA para los alumnos.

## Funcionalidades principales

- Integración de mandatos bancarios SEPA en el pedido de venta.
- Modo de pago y órdenes de pago SEPA.
- Extensión del plazo de pago.
- Integración con `website_slides` para vincular el pedido al alumno.
- Integración con `hr` para empleados/docentes.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `sale.order` | Herencia | Mandato bancario, modo de pago, adeudo SEPA |

## Notas técnicas

- Este módulo es prerequisito de muchos módulos de suscripción de ISEP.
- Requiere los módulos OCA de banca (`account_banking_*`).

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_sale_order_extended \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_sale_order_extended \
    --stop-after-init --db_host=pgodoo_latest
```
