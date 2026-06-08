# Referencia Técnica: irg_course_convocatorias_v2

Este documento provee la especificación técnica completa y de referencia para el módulo `irg_course_convocatorias_v2`.

---

## Ficha Técnica

| Propiedad | Valor |
| --- | --- |
| **Nombre Técnico** | `irg_course_convocatorias_v2` |
| **Categoría** | Website/eLearning |
| **Versión** | `16.0.1.0.0` |
| **Licencia** | LGPL-3 |
| **Instalable** | Sí |
| **Aplicación** | No |
| **Autor** | iRG |

### Dependencias

El módulo interactúa y depende de los siguientes componentes del sistema:
- `website_slides` (eLearning nativo de Odoo)
- `website_slides_survey` (Certificaciones/Encuestas de Odoo)
- `openeducat_core` (Estructura académica de OpenEduCat)
- `irg_op_course_modality`
- `isep_elearning_custom`
- `irg_elearning_editable_sections`
- `irg_op_subject_visibility`

---

## Descripción General

`irg_course_convocatorias_v2` gestiona la separación entre las modalidades de impartición **HomeClass** y **Online** dentro del módulo de eLearning (`slide.channel`). Permite estructurar contenidos específicos y controlar los accesos y visualizaciones en el portal según las inscripciones académicas de los estudiantes en OpenEduCat.

---

## Estructura de Datos (Extensiones de Modelos)

El módulo extiende el modelo base de canales de eLearning para almacenar relaciones y configuraciones específicas de las modalidades.

### `slide.channel`

#### Campos Relacionados y Computados
* **`irg_related_course_ids`** (`Many2many` a `op.course`): Almacena los cursos de OpenEduCat asociados al canal.
* **`irg_related_modality_ids`** (`Many2many` a `irg.course.modality`): Modalidades correspondientes a los cursos relacionados.
* **`irg_homeclass_batch_ids`** (`Many2many` a `op.batch`): Lotes/Convocatorias identificadas con modalidad HomeClass.
* **`irg_online_batch_ids`** (`Many2many` a `op.batch`): Lotes/Convocatorias identificadas con modalidad Online.
* **`irg_homeclass_section_ids`** (`Many2many` a `slide.slide`): Secciones y bloques asignados a HomeClass.
* **`irg_online_content_ids`** (`Many2many` a `slide.slide`): Diapositivas y contenidos pertenecientes al canal clonado online.
* **`irg_online_section_ids`** (`Many2many` a `slide.slide`): Categorías o secciones del canal online.
* **`irg_online_channel_id`** (`Many2one` a `slide.channel`): Enlace al canal de eLearning independiente que contiene la versión online.
* **`irg_homeclass_channel_id`** (`Many2one` a `slide.channel`): Enlace de retorno desde el clon online al canal original HomeClass.
* **`irg_is_online_clone`** (`Boolean`): Indica si el canal actual es un clon específico de modalidad online.
* **`irg_active_tab`** (`Selection`): Pestaña seleccionada en el flujo administrativo (`homeclass` o `online`).

#### Campos de Configuración del Canal Online (Delegados)
* **`irg_online_description_html`** (`Html`): Descripción específica para la versión online.
* **`irg_online_enroll`** (`Selection`): Modo de matrícula en el canal online.
* **`irg_online_visibility`** (`Selection`): Visibilidad del canal online.
* **`irg_online_promote_strategy`** (`Selection`): Estrategia de promoción online.
* **`irg_online_enroll_msg`** (`Html`): Mensaje al inscribirse en la versión online.

---

## API y Métodos Públicos

### Verificación y Detección de Modalidades

#### `_irg_get_related_courses()`
* **Descripción:** Retorna un recordset con todos los cursos (`op.course`) asociados al canal a través de las asignaturas, campos directos o lotes permitidos en sus diapositivas.
* **Seguridad:** Eleva privilegios con `.sudo()` para realizar las búsquedas sobre `op.course`.

#### `_irg_is_online_student_for_channel()`
* **Descripción:** Comprueba si el usuario logueado en la sesión actual (`self.env.user.partner_id`) es un estudiante activo registrado bajo la modalidad online para este canal.
* **Seguridad:** Invoca internamente a `_irg_is_partner_online_student_for_channel` enviando `self.sudo()`.

#### `_irg_is_partner_online_student_for_channel(partner)`
* **Descripción:** Evalúa si el `res.partner` suministrado tiene una admisión activa (`op.admission`) en un lote de OpenEduCat cuya fecha de finalización sea igual o posterior al día de hoy y corresponda a la modalidad online (detectada a través de tokens en su código o modalidad).
* **Seguridad:** Utiliza `sudo()` para consultar admisiones (`op.admission`) y lotes (`op.batch`).

---

## Control de Accesos y Seguridad (Resolución del Error 403)

### Descripción del Incidente (Error 403)
Los estudiantes y usuarios de portal no cuentan con permisos de lectura en Odoo sobre los datos del core académico de OpenEduCat:
- `op.course` (Cursos académicos)
- `op.batch` (Lotes / Convocatorias)
- `op.admission` (Admisiones e Inscripciones)

Cuando un usuario de portal intentaba acceder a la interfaz del curso en el sitio web/portal, la carga del canal llamaba a los métodos de verificación `_irg_get_related_courses()` y `_irg_is_online_student_for_channel()`. Esto generaba una excepción de seguridad `AccessError` (Error 403 Forbidden) debido a la falta de accesos de lectura en los modelos académicos mencionados, impidiendo al usuario ver el curso.

### Solución Aplicada
Se implementó una elevación de privilegios controlada utilizando `.sudo()` en los puntos de consulta específicos de estos modelos:
1. En `_irg_get_related_courses()`, la instancia del entorno y el modelo `op.course` se evalúan con `.sudo()`.
2. En `_irg_is_online_student_for_channel()`, se realiza la invocación usando `self.sudo()`.
3. En `_irg_is_partner_online_student_for_channel()`, el recordset y las consultas de búsqueda para `op.admission` y `op.batch` se instancian con `.sudo()`.

> [!NOTE]
> Esta elevación de privilegios es segura porque las consultas realizadas son estrictamente de solo lectura y se utilizan únicamente para evaluar reglas de negocio (saber si un estudiante está inscrito para mostrar el contenido que le corresponde). No exponen datos sensibles al frontend ni permiten la modificación de registros.

---

## Optimización de Copia de Canales (Preferencia de Rendimiento y Memoria)

### Descripción del Incidente (MemoryError / Timeout)
Al realizar el bootstrap de canales de gran tamaño con archivos adjuntos pesados (presentaciones PDF extensas, vídeos o imágenes en alta resolución), la serialización en base64 de Python consumía excesiva memoria virtual. Esto provocaba fallos de falta de memoria (`MemoryError`) en el worker de Odoo y tiempos de espera excedidos (`Timeout`) debido a la alta carga de E/S al leer y escribir archivos físicos de gran tamaño repetidamente.

### Solución de Rendimiento Aplicada
Se reestructuró el proceso de duplicación de diapositivas para realizarlo sin serializar base64 en Python:
1. **Exclusión técnica en la creación inicial:** Los campos binarios `'datas'`, `'document_binary_content'` e `'image_1920'` se eliminaron de la lista de clonación inicial en `_irg_bootstrap_slide_clone_fields()`.
2. **Duplicación nativa de adjuntos:** Tras la creación de la diapositiva, se realiza una búsqueda de sus correspondientes `ir.attachment` en la base de datos y se duplican usando `attachment.copy({'res_id': copy_id})`.
3. **Independencia funcional:** El filestore de Odoo trabaja con direccionamiento por hash. Al copiar los registros de `ir.attachment`, ambos adjuntos apuntan inicialmente al mismo archivo físico en disco (ahorrando espacio de disco), pero son registros totalmente independientes en la base de datos. Si el usuario sube un archivo nuevo al clon de Online, se crea un nuevo archivo en el filestore para el canal Online, dejando el canal HomeClass de origen 100% inalterado y seguro.

---

## Optimización de Edición de Secciones iRG por Lotes

### Descripción del Incidente (`MemoryError` en `onchange`)
Al editar el apartado **Secciones iRG** y limitar contenidos por lotes, Odoo puede ejecutar un `onchange` sobre relaciones `x2many` de `slide.slide`. Durante el cálculo interno del snapshot (`models.onchange -> Snapshot.diff`), Odoo lee los campos binarios relacionados de las diapositivas, como `image_binary_content` y `binary_content`.

En cursos con adjuntos grandes, esa lectura acaba consultando `ir.attachment.datas` y serializando el fichero completo en base64 (`base64.b64encode(attach.raw)`). Si el adjunto es demasiado grande para la memoria disponible del worker, el servidor falla con `MemoryError` antes de guardar la limitación por lotes.

### Solución Aplicada
Las vistas de `slide.channel` añaden ahora `bin_size: True` en los contextos de las relaciones editables de contenidos y secciones iRG:

- `slide_ids`
- `irg_native_section_ids`
- `irg_online_slide_ids`
- `irg_online_section_ids`

Con `bin_size: True`, Odoo no devuelve el contenido binario real durante la lectura generada por el `onchange`; devuelve una representación ligera/tamaño del binario. Esto evita que el snapshot cargue adjuntos pesados al modificar restricciones por lote.

Los defaults existentes de creación se conservan, incluyendo `default_channel_id`, `default_irg_content_modality`, `default_is_category` y `default_slide_category` cuando aplican.

### Compatibilidad con `op.batch` sin `modality_id`
Durante la validación se detectó que algunas bases de prueba tienen `op.batch` sin el campo opcional `modality_id`. La detección de tokens de modalidad ahora comprueba defensivamente si el campo existe antes de leerlo y continúa usando alternativas como `batch.code` cuando están disponibles.

Este comportamiento evita un `AttributeError` en instalaciones donde la modalidad directa del lote no está instalada, sin cambiar la lógica de clasificación cuando `modality_id` sí existe.

---

## Validación y Suite de Pruebas

La suite de pruebas del módulo valida el correcto comportamiento de la elevación de privilegios y el flujo de bootstrap.

### Pruebas Unitarias (`tests/test_bootstrap_online_v2.py`)
La clase de test `TestBootstrapOnlineFromHomeClassV2` contiene las siguientes verificaciones:

* **`test_portal_user_access_check`**:
  * **Objetivo:** Simular un usuario del grupo Portal (`base.group_portal`) y forzar la ejecución de `_irg_is_online_student_for_channel()`.
  * **Validación:** Verifica que el usuario portal no recibe ningún error 403 (`AccessError`) y que el método devuelve el valor booleano correcto.
* **`test_bootstrap_creates_independent_online_copies`**: Valida que el clon online no altere el canal HomeClass de origen.
* **`test_bootstrap_remaps_hierarchy_within_online`**: Asegura el correcto remapeo de categorías, prerrequisitos y secciones iRG clonadas.
* **`test_student_modality_detection`**: Evalúa la correcta identificación de estudiantes en lotes online u homeclass.
* **`test_slide_channel_partner_synchronization`**: Comprueba la sincronización de miembros entre canales.

### Resultados de Ejecución
```bash
odoo-bin -c odoo.conf -d test_irg_db -i irg_course_convocatorias_v2 --test-enable
```
* **Estado:** Exitoso.
* **Tests pasados:** 10/10.
* **Errores/Fallos:** 0.

### Validación de la corrección `bin_size` / secciones iRG

La regresión del `MemoryError` se cubre con tests estáticos que parsean la vista XML y verifican que los campos `x2many` de contenidos/secciones incluyen `bin_size: True` sin perder sus defaults de creación.

Comandos ejecutados en local:

```bash
python3 addons-extra/extrairg/irg_course_convocatorias_v2/tests/test_slide_channel_views_bin_size.py
python3 -m compileall -q \
  addons-extra/extrairg/irg_course_convocatorias_v2 \
  addons-extra/extrairg/irg_course_convocatorias \
  addons-extra/addons_uisep/irg_elearning_editable_sections
docker compose -f docker-compose.local.yml run --rm odoo_local \
  odoo -c /etc/odoo/odoo.conf \
  -d validation_bin_size_v2_20260605 \
  --stop-after-init \
  --init irg_course_convocatorias_v2 \
  --test-enable \
  --test-tags /irg_course_convocatorias_v2 \
  --log-level=test
```

Resultado Odoo local:

- `irg_course_convocatorias_v2`: 12 tests ejecutados, 0 fallos, 0 errores.
- La validación confirmó que el bloqueo previo por `op.batch.modality_id` ya no aparece.

### Changelog

- **2026-06-05:** se añade `bin_size: True` a los contextos de contenidos y secciones iRG para evitar que los `onchange` de limitación por lotes carguen adjuntos binarios grandes y provoquen `MemoryError`. Se añade test estático de regresión para la vista. Se refuerza `_irg_get_batch_modality_tokens()` para soportar bases donde `op.batch` no incluye `modality_id`.
