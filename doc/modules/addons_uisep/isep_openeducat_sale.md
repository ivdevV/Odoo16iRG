# isep_openeducat_sale

**Categoría:** addons_uisep
**Versión:** 16.0.1
**Licencia:** No especificada
**Instalable:** Sí
**Autor:** ISEP
**Depende de:** `openeducat_core`, `sale`, `openeducat_admission`, `openeducat_admission_enterprise`, `website_slides`, `isep_elearning_custom`, `isep_student_migration`

---

## ¿Qué hace este módulo?

Crea automáticamente admisiones académicas a partir de pedidos de venta confirmados. Es el módulo que conecta el proceso comercial (venta de un curso en la tienda o en el CRM) con el proceso académico (matrícula del alumno en OpenEduCat).

## Funcionalidades principales

- Override de `action_confirm` en `sale.order` para crear la admisión automáticamente.
- Mapeado de producto de venta → curso OpenEduCat.
- Creación de `op.admission` con datos del alumno extraídos del pedido.
- Creación o búsqueda del `op.student` correspondiente.
- Enrollado del alumno en el canal de eLearning del curso.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `sale.order` | Herencia | Lógica de auto-creación de admisión |
| `product.template` | Herencia | Vinculación con `op.course` |

## Vistas y UI

- `views/product_template_views.xml` — campo de curso en el formulario del producto.
- `views/sale_order_views.xml` — estado de la admisión en el pedido.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i isep_openeducat_sale \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u isep_openeducat_sale \
    --stop-after-init --db_host=pgodoo_latest
```
