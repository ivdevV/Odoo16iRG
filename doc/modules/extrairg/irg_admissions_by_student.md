# irg_admissions_by_student

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** No especificada
**Instalable:** Sí
**Autor:** ISEP
**Depende de:** `sale`, `isep_openeducat_sale`, `irg_sale_order_extended`

---

## ¿Qué hace este módulo?

Sobrescribe la lógica de creación de admisiones para que use el campo `student_id` del pedido de venta cuando está disponible, en lugar de usar siempre el `partner_id` (cliente). Esto es importante cuando el pagador y el alumno son personas distintas (por ejemplo, un padre que paga para su hijo).

También añade la columna "Alumno" en la vista de líneas de pedido de venta.

## Funcionalidades principales

- Override de la creación de admisiones: prioriza `student_id` sobre `partner_id`.
- Columna "Alumno" (`student_id`) en la vista de líneas del pedido de venta.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `sale.order` | Herencia | Lógica de creación de admisión por alumno |

## Vistas y UI

- `views/sale_order_line_views.xml` — columna "Alumno" en líneas del pedido.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_admissions_by_student \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_admissions_by_student \
    --stop-after-init --db_host=pgodoo_latest
```
