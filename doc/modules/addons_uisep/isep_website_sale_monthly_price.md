# isep_website_sale_monthly_price

**Categoría:** addons_uisep
**Versión:** 16.0.1.0.0
**Licencia:** No especificada
**Instalable:** Sí
**Autor:** ISEP
**Depende de:** `website_sale`, `product`, `isep_website_sale_custom`, `website_sale_subscription`

---

## ¿Qué hace este módulo?

Muestra el precio mensual de los cursos de financiación en la tienda online. En lugar de mostrar solo el precio total del curso, muestra de forma destacada el precio mensual de la cuota de financiación, facilitando la decisión de compra de los alumnos.

## Funcionalidades principales

- Campo de precio mensual en `product.template`.
- Plantilla de producto en la tienda con precio mensual destacado.
- Integración con el plan de financiación del ecommerce.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `product.template` | Herencia | Precio mensual, plan de cuotas |

## Vistas y UI

- Plantilla de producto en la tienda con precio mensual.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i isep_website_sale_monthly_price \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u isep_website_sale_monthly_price \
    --stop-after-init --db_host=pgodoo_latest
```
