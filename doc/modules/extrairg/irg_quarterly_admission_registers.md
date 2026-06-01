# IRG Quarterly Admission Registers (Registros de Admisión Trimestrales)

El módulo `irg_quarterly_admission_registers` proporciona una agrupación de registros de admisión (`op.admission.register`) basada en trimestres naturales del calendario para todos los programas académicos (tanto presenciales / HomeClass como Online), excluyendo específicamente a los Diplomados.

## Propósito y Objetivos

El objetivo principal de este módulo es agrupar los registros de admisión en cuatro trimestres naturales del año (Q1 a Q4) en lugar de una agrupación mensual u otros rangos específicos de fechas. Esto simplifica la gestión académica y administrativa de las matrículas y admisiones para programas que inician de forma continua o trimestral.

## Dependencias

El módulo interactúa directamente con el flujo de ventas y la creación de admisiones de OpenEduCat en ISEP. Sus dependencias declaradas en el manifiesto son:

*   `sale` (Módulo base de ventas de Odoo)
*   `isep_openeducat_sale` (Integración de ventas y OpenEduCat para ISEP)
*   `isep_sale_order_admissions` (Gestión de admisiones desde órdenes de venta)
*   `irg_sale_manual_confirmation_wizard` (Asistente de confirmación manual de ventas de iRG)

---

## Mecanismo de Funcionamiento

El módulo hereda los modelos `sale.order` y `op.admission.register` para modificar la lógica de cálculo del periodo, la resolución del registro y la alineación de fechas de los trimestres naturales. Las modificaciones clave son las siguientes:

### Modelo: `sale.order`

#### 1. Cálculo del Periodo (`_compute_period`)
Sobrescribe el método `_compute_period` en `sale.order`. Si la orden de venta contiene líneas con productos que son programas académicos (`is_academic_program = True`) y tiene una fecha de admisión asignada (`admission_date`), calcula el periodo en formato trimestral natural `YYYY-XX` (donde `XX` es el código del trimestre), **excluyendo a los Diplomados** (aquellos productos cuya categoría de producto tiene un código que comienza por `'DI'`, insensible a mayúsculas/minúsculas):
*   **Trimestre 1 (Enero - Marzo):** Código `'01'` (Resultado: `YYYY-01`)
*   **Trimestre 2 (Abril - Junio):** Código `'02'` (Resultado: `YYYY-02`)
*   **Trimestre 3 (Julio - Septiembre):** Código `'03'` (Resultado: `YYYY-03`)
*   **Trimestre 4 (Octubre - Diciembre):** Código `'04'` (Resultado: `YYYY-04`)

#### 2. Resolución de Registro de Admisión (`_find_or_create_register`)
Sobrescribe el método `_find_or_create_register` en `sale.order`.
*   Determina si la línea del pedido o el pedido en sí corresponden a un programa académico.
*   **Exclusión de Diplomados:** Si la categoría de producto de la línea o la del curso asociado tiene un código que comienza por `'DI'` (insensible a mayúsculas/minúsculas), el producto se excluye del flujo trimestral y se procesa bajo el flujo mensual/estándar.
*   Para los programas académicos no excluidos, determina la fecha base del periodo utilizando la fecha de inicio del enroller (`start_date_enroller`) de la línea (con fallbacks a `admission_date` o `Date.today()`).
*   Aplica la lógica de desplazamiento por modalidad (por ejemplo, para la modalidad HomeClass `HC` o Presencial `PRS`, si la fecha actual supera el día 7 del mes actual y coincide con el año y mes de la fecha base, desplaza la fecha un mes hacia adelante con `relativedelta(months=1)`). Además, si la modalidad es `HC` y la fecha cae en Julio o Agosto, o es el 1 de Septiembre, se establece fijamente en el 1 de Septiembre.
*   Calcula el trimestre correspondiente a la fecha resultante (mapeado de `01` a `04`) y reescribe el parámetro `period` con el formato `YYYY-XX`.
*   **Limpieza de contexto:** Limpia el flag de contexto `irg_get_lot_line_id` (estableciéndolo en `False` mediante `.with_context(irg_get_lot_line_id=False)`) al invocar al método `super()`. Esto evita que el módulo `irg_sale_manual_confirmation_wizard` interceda y sobrescriba el periodo calculado con su propia lógica mensual u otra parametrización.

#### 3. Fecha Límite de Registro (`gat_date_max_register`)
Sobrescribe `gat_date_max_register` en `sale.order` para que, si el pedido contiene algún programa académico que **no sea un Diplomado** (código de categoría que empieza con `'DI'`), la fecha máxima de registro coincida con el último día del trimestre natural correspondiente al periodo:
*   Periodo finalizado en `'01'` (Q1): Retorna el `31 de Marzo` del año del periodo.
*   Periodo finalizado en `'02'` (Q2): Retorna el `30 de Junio` del año del periodo.
*   Periodo finalizado en `'03'` (Q3): Retorna el `30 de Septiembre` del año del periodo.
*   Periodo finalizado en `'04'` (Q4): Retorna el `31 de Diciembre` del año del periodo.

### Modelo: `op.admission.register`

#### 1. Creación y Edición (`create` y `write`)
Sobrescribe los métodos `create` (decorado con `@api.model_create_multi`) y `write` para alinear las fechas de inicio (`start_date`) y fin (`end_date`) del registro de admisión con los límites naturales del trimestre correspondiente a su periodo.
*   Esta alineación sólo se ejecuta si el registro está asociado a un curso considerado programa académico y **se excluye si la categoría de producto del curso tiene un código que comienza por `'DI'** (insensible a mayúsculas/minúsculas).
*   Las fechas se alinean según los siguientes rangos fijos:
    *   **Trimestre `'01'` (Q1):** Del `1 de Enero` al `31 de Marzo`.
    *   **Trimestre `'02'` (Q2):** Del `1 de Abril` al `30 de Junio`.
    *   **Trimestre `'03'` (Q3):** Del `1 de Julio` al `30 de Septiembre`.
    *   **Trimestre `'04'` (Q4):** Del `1 de Octubre` al `31 de Diciembre`.

---

## Criterios de Uso

*   **Identificación Académica:** La lógica trimestral sólo se activa si la orden de venta tiene al menos un producto con la casilla `is_academic_program` marcada en su plantilla de producto (`product.template`).
*   **Regla de Exclusión de Diplomados:** Cualquier curso o producto perteneciente a una categoría cuyo código empiece por `'DI'` (por ejemplo, `'DI'`, `'DI_ONLINE'`, etc.) será completamente ignorado por las reglas trimestrales de este módulo, siguiendo el flujo de registro estándar mensual o por fechas.
*   **Asignación Automática:** Los estudiantes matriculados en programas académicos (que no sean diplomados) dentro del mismo trimestre natural y para la misma asignatura/curso serán agrupados automáticamente en el mismo registro de admisión trimestral.

## Limitaciones

1.  **Migración de Datos Existentes:** El módulo no altera ni migra los registros de admisión existentes de forma retroactiva. La agrupación trimestral natural aplica a los pedidos de venta confirmados a partir de su instalación.
2.  **Formato de Periodos Estricto:** La base de datos debe soportar la nomenclatura `YYYY-01` a `YYYY-04`. Cualquier módulo externo que dependa de un formato de periodo mensual (`YYYY-MM`) para la facturación o la matriculación podría requerir adaptaciones si se procesa junto con este módulo.
3.  **Dependencia del Contexto:** Al desactivar temporalmente `irg_get_lot_line_id` en el contexto durante la llamada al super método en `_find_or_create_register`, cualquier comportamiento personalizado aguas abajo que requiera conocer la línea de pedido mediante ese flag específico no estará disponible en ese segmento de ejecución.
