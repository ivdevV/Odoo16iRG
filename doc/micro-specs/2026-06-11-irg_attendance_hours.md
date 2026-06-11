# IRG Attendance Hours

## 1. Titulo corto

Total de horas semanales y mensuales en asistencias.

## 2. Resumen objetivo

Crear un modulo extra para calcular y mostrar el total de horas semanales y mensuales trabajadas de un empleado en cada registro de asistencia del modelo `hr.attendance`.

## 3. Motivo / justificacion

El equipo de gestion humana y control de tiempos necesita ver de forma directa en la vista de lista y de formulario de asistencias el total de horas acumuladas de manera semanal y mensual. Esto facilita el monitoreo de jornada laboral sin tener que ir a reportes agrupados o tablas dinamicas externas.

## 4. Alcance exacto

- Crear el modulo `irg_attendance_hours` en `addons-extra/extrairg/`.
- Extender el modelo `hr.attendance` con dos campos calculados de tipo Float: `irg_weekly_hours_total` y `irg_monthly_hours_total`.
- Heredar la vista de arbol/lista `hr_attendance.view_attendance_tree` para mostrar los campos despues de `worked_hours` usando el widget `float_time`.
- Heredar el formulario `hr_attendance.view_attendance_form` para mostrar los campos despues de `worked_hours` con el widget `float_time`.
- Mantener los campos como dinámicos (`store=False`) para garantizar la sincronizacion exacta en tiempo real cuando se anaden, modifican o eliminan registros de asistencia de la misma semana o mes.
- Optimizar la consulta a base de datos usando almacenamiento en cache local durante la ejecucion del computo en lote para evitar el problema de consultas N+1.

## 5. Diseno tecnico

- **Modulo:** `irg_attendance_hours`
- **Modelo heredado:** `hr.attendance` (`_inherit = 'hr.attendance'`)
- **Campos agregados:**
  - `irg_weekly_hours_total` (Float, compute `_compute_irg_weekly_hours_total`, readonly, string="Horas Semanales", widget="float_time")
  - `irg_monthly_hours_total` (Float, compute `_compute_irg_monthly_hours_total`, readonly, string="Horas Mensuales", widget="float_time")
- **Logica de calculo:**
  - **Semanas:** Rango de fecha de lunes a domingo de la semana correspondiente a la fecha de `check_in`. Suma de todas las `worked_hours` del mismo `employee_id` en dicho rango.
  - **Meses:** Rango del dia 1 al ultimo dia del mes correspondiente a la fecha de `check_in`. Suma de todas las `worked_hours` del mismo `employee_id` en dicho rango.
  - **Cache:** Utilizar un diccionario cache por ejecucion para almacenar los totales por empleado y semana/mes, evitando busquedas repetidas si `self` contiene varios registros del mismo empleado en el mismo periodo.
- **Vistas heredadas:**
  - `hr_attendance.view_attendance_tree`
  - `hr_attendance.view_attendance_form`
- **XPath:**
  - XPath `//field[@name='worked_hours']` con posicion `after`.

## 6. Dependencias

- `hr_attendance`

## 7. Backwards-compatibility / migracion

Los campos agregados no son almacenados (`store=False`), por lo que no modifican el esquema fisico de la base de datos de manera persistente (excepto el registro del campo en `ir.model.fields`). No requiere scripts de migracion de datos.

## 8. Casos de prueba / criterios de aceptacion

- El modulo se instala y desinstala limpiamente.
- Al acceder a la vista de asistencias, se muestran los campos `Horas Semanales` y `Horas Mensuales`.
- Si un empleado tiene multiples asistencias en la misma semana (ej. Lunes 8h, Martes 8h), en ambas lineas de asistencia se mostrara `16:00` en la columna `Horas Semanales`.
- Si las asistencias estan en meses distintos, las sumas mensuales se separan correctamente.
- El rendimiento al cargar la lista de asistencias no se degrada perceptiblemente.

## 9. Rollback plan

Desinstalar el modulo `irg_attendance_hours` desde el panel de Aplicaciones o por terminal y reiniciar el servidor. Odoo eliminara los campos dinamicos agregados y las modificaciones en las vistas de forma automatica.

## 10. Estimacion y responsable

Estimacion: 1 hora.
Responsable: Agente principal (Plan) / Subagente Codificador (Implementacion).
