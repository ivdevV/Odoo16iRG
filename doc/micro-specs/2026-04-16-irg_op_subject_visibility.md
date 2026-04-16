# Micro-spec: irg_op_subject_visibility

## 1. Título corto
Visibilidad de asignaturas por lote en el portal eLearning

## 2. Resumen objetivo
Permite indicar, en cada registro `op.subject`, si la asignatura es visible para todos los
lotes del curso o solo para un subconjunto de lotes específicos. La restricción se aplica
en el portal web de eLearning (slides/canales) cuando un estudiante intenta acceder al
canal vinculado a la asignatura.

## 3. Motivo / justificación
La institución necesita controlar qué lotes pueden ver ciertos contenidos eLearning por
asignatura (p.ej. asignaturas de edición nueva que aún no deben estar visibles para lotes
antiguos). No se puede tocar el código nativo porque rompería la actualización del core.
Se utiliza la herencia de Odoo para añadir la lógica de visibilidad de forma no
destructiva.

## 4. Alcance exacto
- **Modelo**: `op.subject` (campos nuevos, sin tabla nueva)
- **Vista**: Formulario de `op.subject` — nuevo grupo "Visibilidad en Portal eLearning"
- **Controlador**: Extensión de `CustomWebsiteSlides.channel()` ya definida en
  `isep_elearning_custom`
- **Template QWeb**: Nueva página de aviso cuando un lote no tiene acceso
- **Sin nuevos modelos** → no se necesita `ir.model.access.csv`

## 5. Diseño técnico
### Campos nuevos en `op.subject`
| Campo | Tipo | Default | Descripción |
|---|---|---|---|
| `visible_all_course_batches` | Boolean | `True` | Visible para todos los lotes del curso |
| `batch_visibility_ids` | Many2many(`op.batch`) | vacío | Lotes con acceso explícito |
| `effective_batch_ids` | Many2many computed | — | Resolución efectiva según los dos anteriores |

### Método helper
`is_visible_for_batch(batch)` en `op.subject` — devuelve `True/False` según la config.

### Vista
Heredar de `irg_op_subject_multi_course.view_op_subject_form_multi_course`.
XPath: `//div[@class='oe_chatter']` position="before".

### Controlador
Heredar de `CustomWebsiteSlides` (de `isep_elearning_custom`).
Lógica adicional en `channel()`: si el canal tiene `op.subject` vinculado y el lote activo
del estudiante no está en `effective_batch_ids` → redirigir a
`/warning/subject-visibility/<channel_id>`.

### Template
`irg_op_subject_visibility.template_subject_not_visible` — página de aviso de acceso
restringido para un canal concreto.

## 6. Dependencias
```python
'depends': [
    'openeducat_core',
    'irg_op_subject_multi_course',
    'isep_elearning_custom',
]
```

## 7. Backwards-compatibility / migración
- El campo `visible_all_course_batches` tiene `default=True`, por lo que todas las
  asignaturas existentes seguirán siendo visibles sin cambios.
- No se modifica ningún dato existente.

## 8. Casos de prueba / criterios de aceptación
1. **Sin cambios (default)**: Asignatura con `visible_all_course_batches=True` →
   cualquier alumno matriculado en cualquier lote del curso puede acceder al canal.
2. **Restricción activa**: Asignatura con `visible_all_course_batches=False` y
   `batch_visibility_ids=[Lote A]` → alumno de Lote A accede; alumno de Lote B ve aviso.
3. **Campo efectivo**: `effective_batch_ids` muestra todos los lotes del curso cuando
   `visible_all_course_batches=True`; muestra solo los seleccionados cuando `False`.
4. **Usuario interno**: No afectado por la restricción (la redirección solo aplica a
   usuarios de portal/público).
5. **Asignatura sin canal**: Si `slide_channel_id` es vacío, la restricción no se evalúa.
6. **Asignatura sin cursos**: `effective_batch_ids` vacío cuando `visible_all=True` y
   `course_ids` vacío (nadie puede acceder) — comportamiento esperado.

## 9. Rollback plan
```bash
# Desinstalar módulo
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> --uninstall irg_op_subject_visibility \
    --stop-after-init --db_host=pgodoo_latest

# Los campos añadidos a op.subject se eliminan al desinstalar (son columnas extra).
# No hay modelos nuevos ni datos persistentes que requieran limpieza manual.
```

## 10. Estimación y responsable
- Responsable: iRG Developer
- Fecha: 2026-04-16
