# Plan: Soporte para Modalidad Intensivo (IN), Código MOPCIN2701 y Campo 'Es Intensivo' en Sale Order

## Alcance y Clasificación
- **Nivel de Misión**: `standard` (Modificaciones en 2 módulos: `irg_openeducat_sale_lote_custom` e `irg_sale_manual_confirmation_wizard`).
- **Capacidad Requerida**: Standard (Generación de lotes Odoo ORM, detección de modalidad de producto, campos indicadores en presupuestos, lotes y admisiones, y vistas XML).

## Criterios de Aceptación
1. **Reconocimiento de Modalidad Intensivo (IN)**: El sistema debe mapear el atributo `Modalidad` cuando su valor sea `Intensivo`, `Curso Intensivo`, `Cursos Intensivos`, `IN` o código `IN` al prefijo de modalidad **`IN`**, así como cuando el campo `irg_is_intensive` esté activo en el presupuesto (`sale.order` / `sale.order.line`).
2. **Campo 'Es Intensivo' (`irg_is_intensive`) en Sale Order**: Añadir el campo booleano `irg_is_intensive` ("Es Intensivo") en `sale.order` y `sale.order.line`, con control de interfaz (toggle/checkbox) en el formulario del presupuesto para que los comerciales/enrollment lo puedan marcar explícitamente.
3. **Generación del Código de Lote**: Para un presupuesto de Máster Oficial con código de curso `PC` y fecha 01/01/2027, el código de lote debe ser `MOPCIN2701` (`MO` + `PC` + `IN` + `27` + `01`). Aplica de forma genérica a cualquier curso.
4. **Reglas de Fecha y Duración**: La modalidad `IN` debe fijar la fecha de inicio del lote el 1º del mes (`2027-01-01`), fecha de inicio de clases igual a la fecha de inicio del lote, y calcular la fecha fin a 16 o 24 meses (igual que `ONL`).
5. **Campo Indicador en Lotes y Admisiones**: Mantenimiento de `irg_is_intensive` en `op.batch` y `op.admission` (relacionado) con visibilidad y filtros en las vistas formulario, lista y búsqueda.
6. **Wizard Manual de Confirmación**: El wizard manual debe detectar la modalidad `IN` cuando la variante de producto es Intensivo o `irg_is_intensive` en la orden/línea está activo, previsualizar el código `MOPCIN2701` e indicar `IN (Intensivo)`, asignando correctamente el lote al confirmar.
7. **Pruebas Automatizadas (TDD)**: Escribir y ejecutar suites de pruebas unitarias que certifiquen el comportamiento GREEN.

## Matriz de Roles
- **Orquestador**: Planificación, control del ciclo de vida y gates.
- **Codificador**: Implementación TDD y salvaguardas en los módulos.
- **Revisor**: Revisión de código diff y ausencia de regresiones.
- **Validador**: Ejecución de suite de pruebas unitarias y emisión de `verification.json`.
- **Documentador**: Actualización de `execution.md` y `CHANGELOG`.
- **Responsable de Entrega**: Notificación final al usuario.

## Fases del Ciclo de Vida
1. **Plan**: `plan.md` e `implementation_plan.md` aprobados por el usuario.
2. **Implementación/TDD**:
   - Campos `irg_is_intensive` en `sale.order` y `sale.order.line`.
   - Vistas XML de `sale.order` actualizadas con la casilla "Es Intensivo".
   - Lógica `get_lot_id` y `_detect_line_modalidad` utilizando `irg_is_intensive`.
   - Pruebas unitarias actualizadas y validadas.
3. **Review de Código**: Inspección de diffs y verificación de alcance.
4. **Validación**: Ejecución de suite de pruebas unitarias y generación de `verification.json`.
5. **Documentación**: Actualizar `execution.md` y `CHANGELOG`.
6. **Publicación Autorizada**: Informar al usuario de la finalización.
