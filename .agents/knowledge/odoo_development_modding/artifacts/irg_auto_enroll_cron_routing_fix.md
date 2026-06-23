# Gotcha de Sincronización en Cron de Admisiones (Auto Enroll)

## Contexto
En Odoo 16, la inscripción automatizada a las asignaturas de e-learning se realiza mediante el cron `Auto Enroll Students` (`cron_auto_enroll_student` en `op.admission`).

## El Problema
Al segmentar admisiones para procesarlas con lógicas distintas (como el calendario individual online vs. el rango de fechas estándar por lote), se introdujo una inconsistencia entre la consulta de base de datos (SQL) en el cron y el filtro en memoria (Python) del botón manual:

* **Filtro Manual:** Utiliza `record._irg_has_online_subject_opening_context()`. Si el lote tiene fechas configuradas, devuelve `False` y delega a la lógica clásica de lote.
* **Filtro del Cron:** Clasificaba rígidamente por código de lote usando SQL (`batch_id.code ilike '%ONL%'`). Cualquier lote online con fechas entraba en la sección online, pero luego no generaba aperturas individuales ni se procesaba como lote estándar.

Esto provocaba que los estudiantes de lotes online con fechas planificadas quedaran flotando sin recibir inscripciones automáticas diariamente, aunque sí funcionara si un administrador hacía clic en el botón de forma manual.

## Solución y Aprendizaje
1. **Consistencia de Segmentación:** Al implementar flujos paralelos de procesamiento (como individual vs. lote), las consultas SQL en los crons deben segmentar utilizando criterios equivalentes a las funciones de comprobación lógica en Python, o bien realizar la segmentación en memoria utilizando `filtered()` sobre el conjunto de registros si el volumen de datos lo permite.
2. **Refactorización del Cron:** Se reemplazó la doble consulta SQL rígida por una consulta unificada de admisiones finalizadas, seguida de un filtrado en memoria usando el helper `_irg_has_online_subject_opening_context()`:

```python
    def cron_auto_enroll_student(self):
        admissions = self.search([('state', '=', 'done'), ('batch_id', '!=', False)])
        online_admissions = admissions.filtered(lambda r: r._irg_has_online_subject_opening_context())
        other_admissions = admissions - online_admissions
        ...
```
