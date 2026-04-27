# payment_flywire

**Categoría:** addons_uisep
**Versión:** 1.0
**Licencia:** No especificada
**Instalable:** Sí
**Autor:** ISEP
**Depende de:** `payment`, `website`

---

## ¿Qué hace este módulo?

Implementa el proveedor de pagos Flywire para Odoo. Flywire es una plataforma especializada en pagos internacionales de alto valor (matrícula, tasas académicas), especialmente útil para alumnos internacionales que pagan en moneda extranjera. Integra Flywire como opción de pago en el checkout del ecommerce.

## Funcionalidades principales

- Proveedor de pago Flywire en el checkout.
- Gestión de la sesión de pago con Flywire.
- Webhook para confirmación de pagos.
- Soporte para múltiples monedas.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `payment.provider` | Herencia | Configuración Flywire (API key, URL) |
| `payment.transaction` | Herencia | Estado de transacciones Flywire |

## Controladores / Endpoints

| Ruta | Método | Descripción |
|------|--------|-------------|
| `/payment/flywire/webhook` | POST | Webhook de confirmación de pago |
| `/payment/flywire/return` | GET | Retorno tras el pago en Flywire |

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i payment_flywire \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u payment_flywire \
    --stop-after-init --db_host=pgodoo_latest
```
