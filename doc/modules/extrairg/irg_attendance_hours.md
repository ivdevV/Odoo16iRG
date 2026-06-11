# irg_attendance_hours

## Proposito

El módulo `irg_attendance_hours` calcula y muestra en tiempo real el total de horas semanales y mensuales acumuladas trabajadas por cada empleado, directamente en cada uno de sus registros de asistencia (`hr.attendance`). Esto facilita al personal de Gestión Humana y Control de Tiempos el monitoreo visual del progreso de la jornada laboral sin necesidad de recurrir a reportes externos o tablas dinámicas complejas.

## Alcance funcional

- Añade dos campos dinámicos calculados no almacenados (`store=False`) en el modelo de asistencias para calcular en tiempo real las horas acumuladas de la semana y del mes correspondientes a la fecha de entrada (`check_in`).
- Muestra estos campos tanto en la vista de lista (árbol) como en la vista de formulario del modelo `hr.attendance`.
- Utiliza la conversión horaria basada en la zona horaria del usuario/contexto para delimitar de manera exacta las fechas locales de inicio y fin de los periodos semanales y mensuales.
- Implementa una optimización de rendimiento a través de almacenamiento en caché en memoria durante la ejecución por lotes (`batch processing`), resolviendo el problema de consultas redundantes (N+1 queries) mediante el uso estratégico de `read_group`.

## Diseno tecnico

### Modelo extendido

El módulo hereda del modelo estándar de Odoo:
- `hr.attendance` (definido en [hr_attendance.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_attendance_hours/models/hr_attendance.py))

### Campos agregados

- `irg_weekly_hours_total` (Float, compute `_compute_irg_weekly_hours_total`, readonly, string="Horas Semanales", widget="float_time"): Suma total de horas trabajadas por el empleado durante la semana (lunes a domingo) correspondiente a la fecha de entrada (`check_in`).
- `irg_monthly_hours_total` (Float, compute `_compute_irg_monthly_hours_total`, readonly, string="Horas Mensuales", widget="float_time"): Suma total de horas trabajadas por el empleado durante el mes (del día 1 al último día) correspondiente a la fecha de entrada (`check_in`).

### Logica de cache (Batch Performance Caching)

Para asegurar la eficiencia y la escalabilidad de la consulta de datos al cargar listados masivos de asistencias, se ha diseñado un mecanismo de caché por transacción:

1. **Filtrado inicial:** Se descartan los registros sin `check_in` o `employee_id` definidos (asignándoles `0.0`).
2. **Mapeo de periodos únicos:** Se calculan las fechas de inicio y fin del periodo (semana o mes) para cada registro utilizando la zona horaria local. Con esto se conforma un conjunto (`set`) de claves únicas compuestas por `(employee_id, start_date, end_date)`.
3. **Conversión a UTC:** Para cada periodo único, los límites locales de fecha y hora (de `00:00:00` a `23:59:59`) se convierten a UTC para coincidir con el almacenamiento de la base de datos de Odoo.
4. **Consulta agregada:** Se realiza una sola consulta `read_group` por cada periodo/empleado único utilizando `worked_hours:sum`, evitando lanzar una consulta SQL individual por cada registro visualizado.
5. **Asignación rápida:** Los resultados agregados se guardan temporalmente en los diccionarios `weekly_cache` y `monthly_cache` para asignarse instantáneamente a los respectivos registros del lote.

### Conversion de Zonas Horarias

Para que los límites del periodo de tiempo correspondan a la realidad horaria del empleado, el módulo evalúa la zona horaria activa a través del orden de prioridad estándar:
1. Zona horaria en el contexto (`tz` en `self.env.context`).
2. Zona horaria configurada en el perfil del usuario actual (`self.env.user.tz`).
3. Retorno por defecto a `UTC`.

El cálculo localiza la fecha de `check_in` a este huso horario y determina el inicio y fin de la semana/mes antes de realizar la conversión inversa a UTC para el filtrado en base de datos.

### Detalles de herencia de vistas

Las modificaciones visuales se definen en [hr_attendance_views.xml](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_attendance_hours/views/hr_attendance_views.xml) heredando dos vistas base de `hr_attendance`:

1. **Vista de Lista/Árbol:** `hr_attendance.view_attendance_tree`
   - **ID de la vista heredada:** `view_attendance_tree_inherit_irg`
   - **Posición:** Se añaden las columnas mediante XPath `//field[@name='worked_hours']` con posición `after`.
   - **Widget utilizado:** `float_time` para mostrar las horas en formato estándar de tiempo (por ejemplo, `40:00`).

2. **Vista de Formulario:** `hr_attendance.hr_attendance_view_form`
   - **ID de la vista heredada:** `hr_attendance_view_form_inherit_irg`
   - **Posición:** Se añaden los campos mediante XPath `//field[@name='check_out']` con posición `after`.
   - **Widget utilizado:** `float_time`.

## Instalacion y actualizacion

Los siguientes comandos deben ejecutarse desde la raíz del proyecto local utilizando la configuración de Docker Compose.

### Instalar el modulo en una base local

```bash
docker compose -f docker-compose.local.yml run --rm odoo_local odoo \
  -d <base_datos> \
  -i irg_attendance_hours \
  --stop-after-init
```

### Actualizar el modulo en una base local

```bash
docker compose -f docker-compose.local.yml run --rm odoo_local odoo \
  -d <base_datos> \
  -u irg_attendance_hours \
  --stop-after-init
```

### Ejecutar pruebas del modulo

```bash
docker compose -f docker-compose.local.yml run --rm odoo_local odoo \
  -d <base_datos> \
  -i irg_attendance_hours \
  --test-enable \
  --test-tags /irg_attendance_hours \
  --stop-after-init
```

*(Sustituir `<base_datos>` por el nombre de la base de datos local correspondiente)*

## Comportamiento de uso

- Al navegar a la lista de asistencias del personal en Odoo, el sistema computará dinámicamente el total de horas que acumula el empleado para la semana y el mes de cada registro, representándolo en las nuevas columnas `Horas Semanales` y `Horas Mensuales`.
- Dado que los campos son dinámicos, cualquier cambio (creación, edición de horas o eliminación de un registro de asistencia) impactará el total y se reflejará instantáneamente en la pantalla en la siguiente recarga de página.
- El formato de tiempo despliega las horas y minutos (ej. `38:30` para 38 horas y media) facilitando la lectura directa del tiempo acumulado.

## Cobertura de pruebas

La lógica y el aislamiento del cálculo se encuentran cubiertos bajo la suite de pruebas unitarias implementada en [test_attendance_hours.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_attendance_hours/tests/test_attendance_hours.py).

La suite hereda de `TransactionCase` y consta de 4 pruebas detalladas:
1. `test_01_weekly_and_monthly_calculation`: Verifica que las horas de múltiples asistencias creadas dentro del mismo periodo de semana y mes para un único empleado se sumen y acumulen correctamente.
2. `test_02_weekly_boundary_conditions`: Comprueba que las asistencias en semanas distintas del mismo mes segreguen correctamente el total de la semana, pero sumen y unifiquen el total acumulado en el campo mensual.
3. `test_03_monthly_boundary_conditions`: Valida el escenario de fin de mes, comprobando que las asistencias en días contiguos que caen en la misma semana de transición pero en meses distintos sumen de forma conjunta la semana, pero permanezcan separadas e independientes en el cálculo mensual.
4. `test_04_multiple_employees_isolation`: Asegura que los registros de diferentes empleados creados en los mismos periodos de tiempo se calculen de manera totalmente aislada, sin interferir en los totales del otro.

## Limitaciones

- **Campos no almacenados:** Los campos calculados no se guardan físicamente en la base de datos (`store=False`). Por lo tanto, no se pueden usar directamente para búsquedas complejas indexadas, agrupaciones de Odoo avanzadas del lado del cliente o filtros de búsqueda directa (búsqueda por base de datos), aunque se renderizan en tiempo real sin problemas en las vistas.
- **Requisito de check_in:** El cálculo depende estrictamente del campo `check_in`. Si un registro no cuenta con una fecha de entrada definida, los totales correspondientes se inicializarán automáticamente en `0.0`.
- **Efecto de zona horaria:** Al depender de la zona horaria del usuario que realiza la consulta, los límites semanales y mensuales de registros tomados muy cerca del cambio de día (medianoche) podrían categorizarse en semanas o meses distintos si son visualizados por usuarios con diferentes zonas horarias configuradas en su perfil.

## Changelog

### 2026-06-11

- **Versión inicial (16.0.1.0.0):**
  - Implementación del módulo `irg_attendance_hours`.
  - Adición de campos computados `irg_weekly_hours_total` e `irg_monthly_hours_total` en `hr.attendance`.
  - Incorporación de optimización en lote (`caching`) con `read_group` para prevenir consultas redundantes en vistas masivas de datos.
  - Soporte multi-zona horaria dinámica según el contexto del usuario (`pytz`).
  - Herencia de vistas en formularios y árboles para el módulo `hr_attendance` incorporando el widget `float_time`.
  - Cobertura de tests unitarios completa (4 casos de prueba) validando cálculos de acumulación, condiciones de borde semanales/mensuales e independencia de empleados.
