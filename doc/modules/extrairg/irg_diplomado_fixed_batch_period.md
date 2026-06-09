# irg_diplomado_fixed_batch_period

**Categoria:** Education  
**Version:** 16.0.1.3.0  
**Licencia:** LGPL-3  
**Instalable:** Si  
**Autor:** Instituto Raimon Gaja  
**Depende de:** `irg_sale_manual_confirmation_wizard`, `irg_openeducat_sale_lote_custom`

## Que hace este modulo

Este modulo corrige el tratamiento de Diplomados en el asistente de confirmacion manual y en la busqueda/creacion real de lotes. Los Diplomados dejan de usar las reglas mensuales de masteres HomeClass y pasan a un periodo fijo anual.

## Regla de negocio

Para cada curso de Diplomado y anio existe un unico lote:

- Inicio: `28/06/<anio>`
- Fin: `30/09/<anio>`
- Inicio de clases: `28/06/<anio>`
- Codigo: `DI<codigo_curso>HC<yy>06`

Ejemplo para el curso `NE` en 2026: `DINEHC2606`, del `28/06/2026` al `30/09/2026`.

## Deteccion de Diplomados

Una linea se considera Diplomado si cumple alguno de estos criterios:

- Categoria con codigo `DI` o que empieza por `DI`.
- Categoria con codigo `D`.
- Categoria cuyo nombre contiene `DIPLOMADO`.
- Producto cuyo nombre contiene `DIPLOMADO`.

### Exclusión de Líneas con Precio Negativo

Las líneas de presupuesto que tengan un precio unitario negativo (`price_unit < 0`) o subtotal negativo (`price_subtotal < 0`) (por ejemplo, líneas correspondientes a descuentos aplicados) son excluidas explícitamente y no se consideran líneas académicas. Esto evita que productos de descuento como "Dcto. Diplomado" o "Descuento Máster" sean clasificados erróneamente como programas académicos e intenten generar admisiones o lotes.

## Alcance tecnico

El modulo hereda:

- `sale.order`: intercepta `get_lot_id()` solo cuando la linea es Diplomado; si no lo es, delega en `super()`.
- **MRO (Method Resolution Order):** Se añade la dependencia de `irg_openeducat_sale_lote_custom` en el manifest (`depends`) para corregir el orden de resolución de métodos en Odoo. Esto garantiza que nuestra lógica personalizada `get_lot_id` para Diplomados se ejecute en primer lugar, sobrescribiendo la generación de lotes personalizada de los módulos base.
- `sale.order`: sobrescribe la restricción `_constraint_subscription_recurrence` para permitir confirmar y guardar presupuestos que contienen productos recurrentes sin un plan de recurrencia asignado, siempre y cuando todas las líneas recurrentes tengan un precio igual o inferior a cero (es decir, estén bonificadas).
- `sale.order`: devuelve modalidad interna `GE` para Diplomados, evitando que las reglas HC/PRS desplacen fechas de admision. La previsualizacion del wizard muestra `Diplomado` para el usuario.
- `sale.order` y `irg.manual.confirmation.wizard`: reimplementan la deteccion de linea academica con dominios `in` de lista para evitar errores de compatibilidad en Odoo 16.
- La categoria del curso solo participa en la deteccion si la linea pertenece realmente a ese curso, evitando contagios en presupuestos con lineas academicas distintas.
- `irg.manual.confirmation.wizard`: muestra `Diplomado` en la previsualizacion y calcula el codigo fijo anual.

## No afectacion a masteres

Las lineas que no cumplen la deteccion de Diplomado siguen por la logica existente de `irg_sale_manual_confirmation_wizard` e `irg_openeducat_sale_lote_custom`. Esto preserva las reglas actuales de masteres HC y ONL, incluidos desplazamientos mensuales, verano HC y online trimestral cuando aplique.

## Pruebas

Incluye pruebas en `addons-extra/extrairg/irg_diplomado_fixed_batch_period/tests/test_diplomado_fixed_batch_period.py`:

- Previsualizacion del wizard para Diplomado 2026.
- Creacion/busqueda de lote fijo con fechas exactas.
- No regresion basica para producto Master no Diplomado.
- Exclusión de líneas de descuento con precio unitario o subtotal negativo, validado en la prueba `test_discount_line_ignored_by_academic_lines`.

## Changelog

- 16.0.1.3.0: Exclusión de líneas con precio negativo para evitar tratar productos de descuento como líneas académicas en el wizard y en el modelo `sale.order`. Se añade la prueba unitaria `test_discount_line_ignored_by_academic_lines` para verificar este comportamiento.
- 16.0.1.2.0: Permitir la confirmación de presupuestos bonificados (precio 0 o menor) omitiendo la restricción de recurrencia en `sale_subscription`.
- 16.0.1.1.0: Corrección del sufijo del código de lote a `06` (antes `09`) para Diplomados. Adición de la dependencia `'irg_openeducat_sale_lote_custom'` en el manifest para corregir el orden de resolución de métodos (MRO) de Odoo, asegurando que `get_lot_id` personalizado prevalezca sobre los módulos base.
- 16.0.1.0.0: Modulo inicial. Anade regla de lote fijo anual para Diplomados y evita que se procesen como masteres HC/ONL.
