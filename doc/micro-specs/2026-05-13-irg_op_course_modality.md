# Micro-Spec: IRG Course Modality (2026-05-13)

## 1. Título corto
Añadir modalidades multi-selección en `op.course`

## 2. Resumen objetivo
Crear un módulo nuevo `irg_op_course_modality` para permitir que un curso académico (`op.course`) pueda configurarse con una o varias modalidades entre Presencial, HomeClass y Online. El objetivo es introducir este dato maestro sin alterar la lógica activa de lotes, admisiones ni eLearning ya desplegada.

## 3. Motivo / justificación
- La modalidad del lote ya existe en algunos flujos, pero no resuelve el caso de negocio de modalidad propia del curso.
- Un mismo curso puede impartirse en más de una modalidad simultáneamente.
- No se debe tocar el core de OpenEduCat ni reutilizar de forma forzada `op.modality`, porque ese modelo hoy responde a otra necesidad funcional en `op.batch`.
- El futuro desbloqueo de secciones online en eLearning necesita una bandera estable en el curso para combinarla con la nomenclatura `ONL` excluyendo `MONL`.

## 4. Alcance exacto
- Nuevo modelo `irg.course.modality`.
- Herencia de `op.course` para añadir `irg_modality_ids`.
- Datos semilla para Presencial, HomeClass y Online.
- Vistas backend para ficha de curso y mantenimiento del catálogo.
- ACL del modelo nuevo.
- Tests de persistencia y catálogo.
- Sin cambios en `op.batch`, `op.admission`, controllers, cron, reports ni assets.

## 5. Diseño técnico
### Modelo `irg.course.modality`
- Campos: `name`, `code`, `sequence`, `active`, `course_ids`.
- Restricción SQL de unicidad sobre `code`.
- Orden por `sequence, name`.

### Modelo `op.course`
- `_inherit = 'op.course'`.
- Campo `irg_modality_ids` como Many2many contra `irg.course.modality` usando `op_course_irg_modality_rel`.

### Datos
- XML `noupdate=1` con tres registros base:
  - `presencial`
  - `homeclass`
  - `online`

### Vistas
- Herencia de `openeducat_core.view_op_course_form` para insertar modalidades tras `code`.
- Herencia de `openeducat_core.view_op_course_tree` para exponer modalidades en listado.
- Acción y menú de configuración para el catálogo bajo `openeducat_core.menu_op_school_config_general`.

### Integración futura
- El futuro módulo de eLearning deberá consultar `course_id.irg_modality_ids` para `code == 'online'`.
- La lógica ONL/MONL de batch seguirá resuelta fuera de este módulo.

## 6. Dependencias
- `openeducat_core`

## 7. Backwards-compatibility / migración
- Cambio completamente aditivo.
- No modifica campos existentes ni métodos de negocio del curso.
- No requiere migración de datos obligatoria; los cursos existentes pueden quedar sin modalidad hasta que negocio los configure.
- Compatible con los módulos actuales que heredan `op.course`, porque solo añade un campo nuevo y un catálogo auxiliar.

## 8. Casos de prueba / criterios de aceptación
1. Un curso puede guardarse sin modalidades.
2. Un curso puede guardar una sola modalidad.
3. Un curso puede guardar varias modalidades simultáneamente.
4. Las tres modalidades base existen tras instalar el módulo.
5. No pueden existir dos modalidades con el mismo `code`.
6. La instalación del módulo no rompe la apertura del formulario de `op.course`.
7. La lógica vigente de aperturas online por lote sigue dependiendo de `ONL` y `MONL` y no se modifica por este módulo.

## 9. Rollback plan
- Desinstalar `irg_op_course_modality` desde Odoo si se quiere retirar la funcionalidad.
- O revertir el commit del módulo y actualizar la base:

```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_op_course_modality \
    --stop-after-init --db_host=pgodoo_latest
```

## 10. Estimación y responsable
- Esfuerzo estimado: 3-4 horas
- Responsable: GitHub Copilot / desarrollo IRG
- Fecha: 2026-05-13