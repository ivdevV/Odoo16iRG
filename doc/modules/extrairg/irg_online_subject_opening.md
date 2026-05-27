# irg_online_subject_opening

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `isep_elearning_custom`, `irg_subject_fix`, `isep_subject_precedence`, `website_slides`

---

## ¿Qué hace este módulo?

Calcula un calendario individual de apertura y cierre de asignaturas online para cada admisión. Está pensado para programas online cuyo lote contiene `ONL` en el código, excluyendo explícitamente los lotes `MONL`. En esos casos, cada alumno no ve todas las asignaturas del lote a la vez, sino solo las que corresponden a la ventana activa de su calendario personal.

El calendario se deriva de la fecha de admisión, el curso y el lote. La primera asignatura se abre el día de admisión, cada asignatura siguiente se desplaza 30 días y cada ventana dura 30 días naturales, con cierre 29 días después de la apertura. El orden de asignaturas se estabiliza por código, nombre e identificador para que la secuencia sea reproducible.

Además de mostrar la planificación en backend y filtrar el portal del alumno, el módulo sincroniza las inscripciones en `website_slides`: activa o crea la relación `slide.channel.partner` cuando una asignatura debe estar disponible y mantiene las fechas, el curso, el lote, la admisión y la asignatura en esa inscripción.

## Funcionalidades principales

- Crea el modelo `irg.online.subject.opening` para guardar aperturas por admisión y asignatura.
- Detecta admisiones online individuales a partir del código del lote: incluye códigos con `ONL` y excluye códigos con `MONL`.
- Genera, actualiza o elimina aperturas automáticamente al crear o modificar una admisión.
- Calcula ventanas de 30 días por asignatura desde `admission_date`.
- Usa las asignaturas programadas en `batch_id.subject_to_batch_ids`; si el lote no tiene líneas, usa las asignaturas del curso.
- Filtra en el portal del alumno las asignaturas visibles según la fecha actual.
- Sincroniza inscripciones en canales eLearning (`slide.channel.partner`) durante matrícula manual, auto-matrícula y cron.
- Respeta precedencias de asignaturas antes de activar una inscripción online.
- Mantiene el comportamiento original para admisiones que no pertenecen al flujo online individual.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `irg.online.subject.opening` | Nuevo | `admission_id`, `partner_id`, `student_id`, `course_id`, `batch_id`, `subject_id`, `subject_code`, `slide_channel_id`, `sequence`, `opening_date`, `closing_date`, `active` |
| `op.admission` | Herencia | `irg_online_subject_opening_ids`, `irg_is_online_subject_opening` y métodos de generación, visibilidad y sincronización online |

## Vistas y plantillas

- `views/op_admission_views.xml` hereda `openeducat_admission.view_op_admission_form`.
- Añade el campo `irg_is_online_subject_opening` después de `batch_id` para indicar si la admisión usa calendario online individual.
- Añade la pestaña **Aperturas Online** en la admisión, visible solo cuando aplica el calendario online individual.
- La pestaña muestra las aperturas en modo solo lectura, con secuencia, asignatura, código, canal eLearning, fecha de apertura y fecha de cierre.
- Define la vista árbol y búsqueda de `irg.online.subject.opening`, con filtros por activo y agrupaciones por curso, lote, asignatura y fecha de apertura.
- Añade la acción y menú **Aperturas Online** bajo el menú raíz de admisiones, limitado al grupo `openeducat_admission.group_op_admission_user`.
- `templates/portal_subject_opening.xml` hereda `irg_subject_fix.user_profile_content_details_irg_fix` y sustituye el cálculo de `subject_ids` en portal: para admisiones online individuales usa solo las asignaturas visibles en la fecha actual; para el resto mantiene las asignaturas válidas del lote.

## Reglas de negocio

- Una admisión solo puede tener una apertura por asignatura mediante la restricción SQL `unique(admission_id, subject_id)`.
- `opening_date` no puede ser posterior a `closing_date`.
- El curso y el lote de cada apertura deben coincidir con el curso y lote de la admisión.
- Una admisión se considera online individual si `batch_id.code` contiene `ONL` y no contiene `MONL`, sin distinguir mayúsculas/minúsculas.
- Para generar calendario se requiere lote online individual, `admission_date`, `course_id` y `batch_id`.
- Si la admisión deja de cumplir el contexto online individual, sus aperturas existentes se eliminan.
- Si cambian fecha de admisión, lote, curso o estado, el calendario se regenera.
- Las asignaturas se ordenan por código normalizado, nombre e identificador.
- La fecha de apertura de cada asignatura se calcula como `admission_date + 30 * indice` días.
- La fecha de cierre se calcula como `opening_date + 29` días.
- Una asignatura con precedencia solo puede activarse si existe una inscripción activa y completada para su asignatura padre en la misma admisión.

## Cron y comportamiento de matrícula

El módulo no declara un cron XML propio. En su lugar, hereda `cron_auto_enroll_student` de `op.admission` para separar dos flujos:

- Para admisiones `done` con lote online individual (`ONL` sin `MONL`), genera aperturas y sincroniza inscripciones eLearning según la ventana activa de cada asignatura.
- Para el resto de admisiones, conserva una lógica equivalente al flujo estándar por fechas de `op.subject.to.batch`: activa la inscripción si hoy está entre `date_from` y `date_to`, la desactiva cuando la fecha ya venció y omite admisiones manuales cuando el campo `modality` existe y vale `manual`.

En matrícula manual, `enroll_student` llama primero al comportamiento original, regenera aperturas y sincroniza canales. En auto-matrícula (`auto_enroll_student` y `auto_enroll_student_auto`), las admisiones online individuales no ejecutan el flujo estándar completo; sincronizan sus aperturas calculadas. Las admisiones no online se delegan al `super()` correspondiente.

En `auto_enroll_student_subject(subject_id)`, el módulo sincroniza solo las aperturas cuyas asignaturas dependen de la asignatura padre indicada. Esto permite abrir asignaturas hijas cuando se cumple la precedencia configurada por `isep_subject_precedence`.

La sincronización busca inscripciones `slide.channel.partner` activas o archivadas para el alumno, canal y lote. Si existe, actualiza fechas y contexto. Si no existe y la asignatura puede estar activa hoy, crea la inscripción con `channel_id`, `partner_id`, curso, registro, admisión, lote, fechas y asignatura.

## Tests

El módulo incluye pruebas transaccionales en `tests/test_online_subject_opening.py`, etiquetadas como `post_install` y `-at_install`.

Casos cubiertos:

- Un lote `ONL` genera aperturas ordenadas por código de asignatura.
- Las fechas de apertura y cierre se calculan en ventanas sucesivas de 30 días desde la fecha de admisión.
- Un lote `MONL` se excluye aunque contenga la cadena `ONL`.
- Un lote sin `ONL` no genera calendario individual.
- Al cambiar `admission_date`, las fechas de apertura se regeneran.
- La sincronización sin canales eLearning conserva el calendario y no crea inscripciones `slide.channel.partner`.

Para ejecutar las pruebas del módulo en una base local:

```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_online_subject_opening \
    --test-tags /irg_online_subject_opening \
    --stop-after-init --db_host=pgodoo_latest
```

## Seguridad

El módulo define `security/ir.model.access.csv` para el modelo `irg.online.subject.opening`:

- `base.group_user`: lectura solamente.
- `openeducat_admission.group_op_admission_user`: lectura, escritura, creación y borrado.

No define controladores HTTP propios.

## Dependencias externas

- `isep_elearning_custom`: aporta el contexto de asignaturas por lote y la integración académica de eLearning.
- `irg_subject_fix`: aporta la plantilla de portal heredada para ajustar la lista de asignaturas visibles.
- `isep_subject_precedence`: aporta la relación de precedencia entre asignaturas usada antes de activar inscripciones.
- `website_slides`: aporta los canales eLearning y el modelo `slide.channel.partner` que se sincroniza.

## Notas técnicas

- Usa `sudo()` al buscar, actualizar o crear `slide.channel.partner`, porque la sincronización se ejecuta desde flujos de matrícula y cron que deben gestionar inscripciones eLearning del alumno aunque el usuario actual no tenga permisos directos sobre todas las relaciones.
- No usa SQL directo, acciones de servidor propias ni assets JS/SCSS.
- La generación es idempotente: actualiza aperturas existentes, crea las faltantes y elimina aperturas obsoletas cuando cambia el conjunto de asignaturas.
- La visibilidad en portal se calcula con `fields.Date.context_today` cuando no se pasa una fecha explícita.
- El modelo `irg.online.subject.opening` se ordena por admisión, secuencia, código de asignatura e identificador.
- Las aperturas tienen `ondelete='cascade'` respecto a la admisión, por lo que se eliminan si se borra la admisión asociada.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_online_subject_opening \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_online_subject_opening \
    --stop-after-init --db_host=pgodoo_latest
```

## Operación

Para activar el flujo, el lote de la admisión debe tener un código que contenga `ONL` y no contenga `MONL`. La admisión debe tener fecha de admisión, curso y lote. Al guardar o matricular, Odoo generará la pestaña de aperturas online y el portal mostrará solo las asignaturas cuyo rango incluya la fecha actual.

Antes de operar en producción conviene verificar que cada asignatura tenga configurado su `slide_channel_id`; si falta el canal, la apertura se conserva pero no se crea inscripción eLearning para esa asignatura. También es importante revisar las precedencias entre asignaturas, porque una asignatura hija dentro de su ventana temporal no se activará hasta que la asignatura padre esté completada para la misma admisión.

## Changelog

### [16.0.1.1.0] - 2026-05-22
- Modificación del decorador `@api.depends` en `_compute_irg_is_online_subject_opening` en `op.admission` para depender de `'batch_id.code', 'batch_id.subject_to_batch_ids.date_from', 'batch_id.subject_to_batch_ids.date_to'` para asegurar el re-cálculo automático ante cambios en las fechas de asignaturas del lote.
- Añadido caso de prueba `test_get_subjects_visible_for_batch_online` para validar el nuevo flujo de visibilidad de asignaturas online.