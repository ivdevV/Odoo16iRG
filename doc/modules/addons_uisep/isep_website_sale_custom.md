# isep_website_sale_custom

**Categoría:** addons_uisep
**Versión:** 16.1
**Licencia:** No especificada
**Instalable:** Sí
**Autor:** ISEP
**Depende de:** `isep_sale_subscription_custom`, `isep_record_request`, `isep_openeducat_sale`, `website_sale_subscription`, `website_sale`, `sign`, `product`, `sale`

---

## ¿Qué hace este módulo?

Es el punto de entrada del proceso de matrícula online. Personaliza el checkout del ecommerce de Odoo para incluir campos adicionales específicos del alumno (datos académicos, forma de pago, financiación), gestiona la recurrencia temporal y la integración con la firma electrónica del contrato de matrícula.

## Funcionalidades principales

- Checkout personalizado con campos adicionales del alumno.
- Selección de forma de pago y plan de financiación en el checkout.
- Generación y envío del documento de matrícula para firma electrónica.
- Gestión de recurrencia temporal en el proceso de compra.
- Controladores HTTP del checkout con validación de datos.
- Integración con `sign` para el contrato de matrícula.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `sale.order` | Herencia | Campos del alumno, plan de pago, firma |

## Controladores / Endpoints

| Ruta | Método | Descripción |
|------|--------|-------------|
| `/shop/checkout` | GET/POST | Checkout personalizado con campos del alumno |
| `/shop/payment` | GET/POST | Selección de forma de pago y financiación |

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i isep_website_sale_custom \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u isep_website_sale_custom \
    --stop-after-init --db_host=pgodoo_latest
```
