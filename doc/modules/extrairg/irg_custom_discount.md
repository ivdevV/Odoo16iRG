# irg_custom_discount

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `sale`, `website_sale`

---

## ¿Qué hace este módulo?

Permite crear programas de descuento con fórmulas Python personalizadas para el ecommerce. A diferencia de los descuentos porcentuales fijos, este módulo permite definir lógicas complejas usando variables del pedido.

Variables disponibles en la fórmula:
- `amount_untaxed` — total sin impuestos
- `amount_total` — total con impuestos
- `qty_total` — cantidad total de productos
- `line_count` — número de líneas del pedido

Ejemplos: `amount_untaxed * 0.10` (10%), `min(amount_untaxed * 0.15, 500)` (15% con tope de 500€).

## Funcionalidades principales

- Modelo de programa de descuento con fórmula Python.
- Modelo de tabla de descuentos para configuración tabular.
- Modelo de excepción de descuento.
- Feedback en el carrito de la tienda online.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `irg.discount.program` (nuevo) | Nuevo | Código, fórmula, activo |
| `irg.discount.table` (nuevo) | Nuevo | Tramos y montos de descuento |
| `irg.discount.exception` (nuevo) | Nuevo | Productos/clientes excluidos |

## Vistas y UI

- `views/irg_discount_program_views.xml`, `views/irg_discount_table_views.xml`, `views/irg_discount_exception_views.xml` — backend.
- `views/website_cart_feedback.xml` — feedback de descuento en el carrito.

## Notas técnicas

- La evaluación de fórmulas se hace con `eval()` en un sandbox controlado.
- Requiere `security/ir.model.access.csv`.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_custom_discount \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_custom_discount \
    --stop-after-init --db_host=pgodoo_latest
```
