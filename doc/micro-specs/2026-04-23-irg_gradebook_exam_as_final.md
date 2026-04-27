# Micro-spec: irg_gradebook_exam_as_final

## 1. Título corto
Nota del examen como nota final de asignatura

## 2. Resumen objetivo
Sobrescribir el cálculo de `final_subject_note` en `app.gradebook.subject` para que la nota
final de una asignatura sea únicamente la nota del examen registrado (o el promedio aritmético
si se registran varios exámenes como fallback), ignorando las demás categorías de evaluación
(asignaciones, interacciones, foro) en el cómputo final visible al estudiante.

## 3. Motivo / justificación
El método base `compute_final_subject_note` en `isep_gradebook` ya calcula el promedio de
exámenes con comentario que indica que esa era la intención original. Sin embargo, la semántica
debe quedar explícita y aislada en un módulo dedicado para facilitar su mantenimiento y
eventual ajuste sin tocar el módulo base.

No se toca `isep_gradebook` porque es un módulo UISEP compartido.

## 4. Alcance exacto
- **Modelo:** `app.gradebook.subject` — método `compute_final_subject_note`
- **Sin cambios en vistas**, sin nuevos modelos, sin cambios en templates portal
- El campo `final_subject_note` ya existe en el modelo base; solo se redefine su lógica de cómputo

## 5. Diseño técnico
```python
# models/app_gradebook_subject.py
class AppGradebookSubject(models.Model):
    _inherit = 'app.gradebook.subject'

    @api.depends(
        'gradebook_result_ids.scoring_total',
        'gradebook_result_ids.survey_type',
        'gradebook_id.round_subject_final',
        'gradebook_student_id.gradebook_id.round_subject_final',
    )
    def compute_final_subject_note(self):
        """
        La nota final de la asignatura es la nota del examen.
        Si hay un único examen, se toma su nota directamente.
        Si hay varios (fallback), se calcula el promedio aritmético.
        Si no hay exámenes, la nota final es 0.
        El redondeo respeta la configuración round_subject_final de la plantilla.
        """
        for rec in self:
            exam_results = rec.gradebook_result_ids.filtered(
                lambda r: r.survey_type == 'exam'
            )
            if exam_results:
                final_note = sum(exam_results.mapped('scoring_total')) / len(exam_results)
            else:
                final_note = 0.0
            gradebook_id = rec.gradebook_id or rec.gradebook_student_id.gradebook_id
            if gradebook_id and gradebook_id.round_subject_final:
                final_note = rec.round_custom(final_note)
            rec.final_subject_note = final_note
```

Mejoras respecto al método base:
- `@api.depends` ampliado con `survey_type` y los campos de redondeo para invalidación correcta
- Uso de `rec.round_custom()` en lugar de `self.round_custom()` para consistencia con el registro
- Docstring explícito

## 6. Dependencias (`depends` en `__manifest__`)
```python
'depends': ['isep_gradebook'],
```

## 7. Backwards-compatibility / migración
No aplica. El campo `final_subject_note` es `store=True` en el modelo base.
Al instalar el módulo, Odoo recomputará automáticamente el campo para todos los registros.

## 8. Casos de prueba / criterios de aceptación
- Una asignatura con 1 examen (nota: 7.5) → `final_subject_note = 7.5`
- Una asignatura con 2 exámenes (notas: 6.0 y 8.0) → `final_subject_note = 7.0`
- Una asignatura sin exámenes → `final_subject_note = 0.0`
- Con `round_subject_final = True` y nota 7.3 → `final_subject_note = 7`
- Con `round_subject_final = True` y nota 7.5 → `final_subject_note = 8` (round_custom)
- Las categorías assignment/interaction/foro NO afectan `final_subject_note`

## 9. Rollback plan
```bash
# Desinstalar el módulo (Odoo revertirá al método heredado del módulo base)
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf -d <dbname> \
    -u isep_gradebook --stop-after-init --db_host=pgodoo_latest
# Luego desinstalar desde la UI: Ajustes → Módulos técnicos → irg_gradebook_exam_as_final
```

## 10. Estimación y responsable
- Estimación: < 1 hora
- Responsable: IRG Dev
