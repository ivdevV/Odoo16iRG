# Módulos: account_related15

Carpeta con módulos OCA del repositorio `bank-payment` para Odoo 16, especializado en pagos bancarios, órdenes de pago, modos de pago y adeudos SEPA. Son la base del sistema de cobros domiciliados SEPA de ISEP/IRG.

Todos son módulos de terceros (OCA) y no deben modificarse directamente.

---

## Índice de módulos

| Módulo | Descripción |
|--------|-------------|
| account_banking_pain_base | Base de mensajes PAIN (ISO 20022) para SEPA |
| account_banking_sepa_credit_transfer | Transferencias SEPA (SCT) |
| account_due_list | Lista de deudas de partner |
| account_due_list_payment_mode | Lista de deudas por modo de pago |
| account_invoice_payment_term_date_due | Fecha de vencimiento desde el plazo de pago |
| account_payment_mode | Modos de pago (domiciliación, transferencia, etc.) |
| account_payment_order | Órdenes de pago batch |
| account_payment_order_return | Devoluciones de órdenes de pago |
| account_payment_partner | Modo de pago predeterminado por partner |
| account_payment_purchase | Modo de pago en órdenes de compra |
| account_payment_return | Devoluciones de pagos (gestion de impagados) |
| account_payment_term_extension | Extensión del plazo de pago (múltiples vencimientos) |
| product_analytic | Cuenta analítica en productos |
| server_action_mass_edit | Edición masiva mediante acciones de servidor |
| user_log_view | Vista del log de usuario |

---

## Rol en la arquitectura ISEP/IRG

Los módulos `account_banking_*` son prerequisito directo de `irg_sale_order_extended`, que habilita los cobros domiciliados SEPA para los alumnos matriculados. La cadena de dependencias es:

```
account_banking_pain_base
    └── account_banking_sepa_credit_transfer
    └── account_banking_sepa_direct_debit (en otro repo)
        └── irg_sale_order_extended
            └── isep_sale_subscription_custom
                └── isep_sale_subscription_extension
```
