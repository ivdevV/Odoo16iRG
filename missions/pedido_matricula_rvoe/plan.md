# Plan: Pedido de Matrícula RVOE en sale.order (IRG)

## Alcance y Objetivos
El objetivo es revisar e implementar un segundo reporte de matrícula para el modelo `sale.order` en Odoo 16 para la entidad **IRG**, denominado **"Pedido de matrícula RVOE"**, el cual debe ser accesible desde el botón "Imprimir" del formulario de Pedido de Ventas.

Este reporte servirá como un duplicado idéntico del original de forma que pueda editarse desde el backend de Odoo de manera independiente (vía Vistas/Reportes QWeb en la interfaz de Odoo) sin interferir con el reporte predeterminado.

## Clasificación de Complejidad
* **Complejidad**: `standard`
* **Justificación**: Afecta a un máximo de 3 archivos (definición de la acción del reporte, plantilla del reporte QWeb duplicada e inclusión en el manifiesto del nuevo módulo `irg_pedido_matricula_rvoe`). No modifica bases de datos, lógica de concurrencia, ni elementos de seguridad crítica.
* **Modelo Propuesto para Implementación**: Modelo intermedio fuerte de código (standard).
* **Modelo para Validación**: Modelo intermedio por defecto.

## Descomposición de la Tarea
1. **Identificación de la Plantilla Base**:
   La plantilla base del pedido de matrícula de IRG está definida en `irg_sale_order_extended.registration_order_template`.
2. **Definición de la Acción de Reporte**:
   Crear un registro en `ir.actions.report` vinculando el nuevo reporte al modelo `sale.order` con `binding_model_id` apuntando a `sale.order` para que figure en el menú "Imprimir" como "Pedido de matrícula RVOE".
3. **Definición de la Plantilla QWeb**:
   Crear la plantilla del reporte PDF (usando QWeb) estructurada de manera idéntica a la matrícula base de IRG pero con su propio ID (`irg_pedido_matricula_rvoe.registration_order_rvoe_template`) para que sea editable de forma independiente.
4. **Registro en el Manifiesto**:
   Agregar el nuevo archivo XML en la lista `data` del manifiesto del nuevo módulo de extensión `irg_pedido_matricula_rvoe`.

## Plan de Verificación
* **Verificación Técnica**:
  * Comprobar mediante el entorno de desarrollo local (`docker-compose.local.yml`) que el reporte se renderiza correctamente en PDF.
  * Validar la existencia del botón "Pedido de matrícula RVOE" en la acción de "Imprimir" de un `sale.order`.
  * Generar un `verification.json` que demuestre que el reporte se compila y genera sin errores en el runtime local.
