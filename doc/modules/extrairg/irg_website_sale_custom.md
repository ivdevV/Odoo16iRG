# irg_website_sale_custom

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `base`, `website_sale`, `website_sale_subscription`, `product`, `sale`

---

## ¿Qué hace este módulo?

Proporciona personalizaciones del ecommerce de IRG para el proceso de checkout: campos de dirección personalizados, información extra en el formulario de compra, y hooks de automatización post-pago. También gestiona el campo de recurrencia temporal de ventas.

## Funcionalidades principales

- Templates de checkout con campos personalizados de dirección.
- Campos de información extra en el formulario de compra (`template_extra_info.xml`).
- Gestión de recurrencia temporal de ventas (`sale_temporal_recurrence_views.xml`).
- Vistas de atributo de valor de plantilla de producto personalizadas.
- Acciones automáticas y plantillas de email para el proceso post-pago.
- Toast de confirmación de dirección (JS).

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `sale.temporal.recurrence` | Herencia | Vistas de recurrencia |
| `product.template.attribute.value` | Herencia | Vistas de atributo |
| `crm.team` | Herencia | Vistas de equipo de ventas |

## Vistas y UI

- `views/template.xml`, `views/template_extra_info.xml` — checkout.
- `views/sale_temporal_recurrence_views.xml` — recurrencia.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_website_sale_custom \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_website_sale_custom \
    --stop-after-init --db_host=pgodoo_latest
```
