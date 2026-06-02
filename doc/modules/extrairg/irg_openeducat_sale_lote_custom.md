# irg_openeducat_sale_lote_custom

**Categoria:** Sales / OpenEduCat
**Version:** Odoo 16
**Autor:** Instituto Raimon Gaja

---

## Que hace este modulo

Extiende la generacion de lotes (`op.batch`) desde pedidos de venta academicos para construir codigos de lote a partir de la categoria del producto, el codigo del curso, la modalidad y la fecha efectiva de admision.

El metodo principal es `sale.order.get_lot_id(course_id)`.

---

## Formato de codigo de lote

El codigo se genera con esta estructura:

```text
<categoria><codigo_curso><modalidad><anio><mes>
```

Ejemplo: `DINEHC2606`.

| Segmento | Ejemplo | Origen |
| --- | --- | --- |
| Categoria | `DI` | `product.category.code` del producto o curso |
| Curso | `NE` | `op.course.code` |
| Modalidad | `HC` | Atributo `Modalidad` o regla de diplomado |
| Anio | `26` | Fecha efectiva de admision |
| Mes | `06` | Fecha efectiva de admision |

---

## Reglas relevantes

- Los productos bonificados online pueden cambiar el prefijo de categoria a `MB` si la modalidad es `ONL` y el precio es cero.
- Las modalidades `HC` y `PRS` desplazan la fecha al mes siguiente si la fecha seleccionada esta en el mes actual y el dia actual es mayor que 7.
- Los lotes `HC` creados entre julio, agosto o el 1 de septiembre se redirigen al 1 de septiembre.
- Los diplomados se identifican por categoria con codigo que empieza por `DI`, codigo `D` o nombre de categoria que contiene `DIPLOMADO`.
- Los diplomados fuerzan categoria `DI` y modalidad `HC` para evitar codigos genericos como `DINEGE2606`.

---

## Changelog

### 2026-06-02

- Se fuerza la modalidad `HC` en la generacion real de lotes cuando la linea o curso corresponde a un diplomado.
- Caso corregido: `DINEGE2606` ahora se genera como `DINEHC2606`.
- Validacion realizada con Odoo local en `docker-compose.local.yml` mediante una comprobacion funcional aislada con rollback.
