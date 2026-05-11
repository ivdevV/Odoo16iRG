# irg_student_scholarship_documents

**Categoría:** extrairg  
**Versión:** 16.0.1.0.0  
**Licencia:** LGPL-3  
**Instalable:** Sí  
**Autor:** IRG  
**Depende de:** `base`, `contacts`, `portal`, `website`, `openeducat_core`, `openeducat_web`, `isep_website_custom`

---

## ¿Qué hace este módulo?

Permite a los alumnos subir documentación relacionada con solicitudes de becas desde su portal privado y al personal administrativo gestionar esa documentación desde el backend. El módulo introduce el concepto de "tipos de beca" (becas por mérito, becas económicas, ayudas, etc.) que se asignan a cada alumno o contacto y proporciona un sistema completo para adjuntar, revisar y aprobar los documentos requeridos.

Los alumnos acceden a `/my/scholarship-documents` desde su campus virtual, donde pueden ver el tipo de beca asignado, consultar el historial de documentos enviados (con fecha, estado y observaciones) y cargar nuevos archivos. Cada documento puede tener tres estados: Recibido (pendiente de revisión), Aceptado (aprobado por administración) u Observado (requiere corrección). El personal administrativo gestiona todo desde el módulo Contactos de Odoo, con acceso rápido a los documentos desde el perfil del alumno y filtros por tipo de beca o estado de documento.

## Funcionalidades principales

- **Tipos de beca configurables** — Catálogo de tipos de beca (ej: "Beca Excelencia", "Ayuda Económica") con descripción y ordenamiento por secuencia.
- **Asignación de beca a contacto/alumno** — Campo `irg_scholarship_type_id` en `res.partner` y `op.student` (vía related).
- **Subida de documentos desde el portal** — Página pública autenticada en `/my/scholarship-documents` con formulario de upload.
- **Validación de archivos** — Extensiones permitidas (PDF, JPG, JPEG, PNG, DOC, DOCX), límite de 10 MB, archivo obligatorio.
- **Gestión de estados de documento** — Flujo: Recibido → Aceptado/Observado, con botones de acción en el backend.
- **Visualización en pestaña de contacto/alumno** — Notebook tab "Beca" en formulario de contactos y alumnos con lista de documentos editable inline.
- **Reglas de seguridad portal** — Los usuarios portal solo ven y descargan sus propios documentos.
- **Menú dinámico en campus** — Entrada visible en el portal del alumno con icono personalizado.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `irg.scholarship.type` | Nuevo | `name` (traducible), `description` (traducible), `sequence`, `active` |
| `irg.scholarship.document` | Nuevo | `name`, `partner_id`, `scholarship_type_id` (related), `file`, `filename`, `note`, `state` (submitted/accepted/observed), `create_date` |
| `res.partner` | Herencia | `irg_scholarship_type_id`, `irg_scholarship_document_ids` (One2many) |
| `op.student` | Herencia indirecta | Mismos campos vía `partner_id` |

### Campos añadidos a `res.partner`

- **`irg_scholarship_type_id`** (`Many2one` → `irg.scholarship.type`) — Tipo de beca asignado al contacto.
- **`irg_scholarship_document_ids`** (`One2many` ← `irg.scholarship.document.partner_id`) — Lista de todos los documentos de beca del contacto.

### Campos añadidos a `op.student`

Los campos se acceden directamente desde `partner_id`. Las vistas en `op.student` heredan el formulario de OpenEduCat y añaden la misma pestaña "Beca" usando los campos relacionados.

### Campo `state` en `irg.scholarship.document`

- **`submitted`** (Recibido) — Estado inicial al subir el documento desde el portal o crear en backend.
- **`accepted`** (Aceptado) — Documento revisado y aprobado.
- **`observed`** (Observado) — Documento requiere correcciones o atención adicional.

## Vistas y UI

### Backend (Odoo)

**Menú: Contactos → Tipos de beca**
- Lista de tipos de beca con secuenciación drag & drop.
- Formulario simple con nombre, descripción (traducibles) y campo activo.

**Menú: Contactos → Documentos de beca**
- Lista de todos los documentos del sistema ordenados por fecha descendente.
- Filtros por contacto, tipo de beca, estado.
- Formulario con header statusbar (estado del documento) y botones de acción:
  - **Marcar recibido** — Volver al estado inicial.
  - **Aceptar** — Aprobar el documento.
  - **Observar** — Marcar para revisión o corrección.

**Formulario de contacto/alumno → Pestaña "Beca"**
- Campo de selección de tipo de beca.
- Lista editable inline de documentos con columnas: Fecha, Nombre, Filename, Archivo, Estado, Observaciones.
- Posibilidad de adjuntar documentos directamente desde el backend.

### Frontend (Portal del alumno)

**URL:** `/my/scholarship-documents`

La página se divide en dos columnas:

**Columna izquierda** — Documentos aportados (tabla responsive)
- Muestra: Nombre del documento, Fecha de subida, Estado (badge coloreado), Botón de descarga.
- Tooltip con observaciones si el documento tiene notas.
- Mensaje "No hay documentos cargados" si está vacía.

**Columna derecha** — Formulario de subida
- Campo de texto: Nombre del documento (opcional, por defecto usa el filename).
- Input de archivo: Acepta `.pdf,.jpg,.jpeg,.png,.doc,.docx`, obligatorio.
- Textarea: Observaciones opcionales del alumno.
- Botón "Subir" que envía POST a `/my/scholarship-documents/upload`.

**Header de página:**
- Título "Documentación de beca".
- Muestra el tipo de beca asignado al alumno (o "Sin tipo de beca asignado" si no tiene).
- Botón "Volver" que redirige a `/campus`.

**Mensajes de feedback:**
- **Éxito:** "Documento subido correctamente" (alerta verde).
- **Error:** Mensajes específicos según validación fallida (alerta roja).

**Integración en campus:**
- Entrada de menú "Documentación de beca" en el portal de OpenEduCat (icono académico azul, secuencia 45).
- Visible solo para alumnos, no para padres.

## Controladores / Endpoints

### GET `/my/scholarship-documents`

- **Autenticación:** Usuario autenticado (`auth='user'`)
- **CSRF:** Habilitado (página de formulario)
- **Descripción:** Renderiza la página de documentación de beca con lista de documentos y formulario de subida.
- **Lógica:**
  - Resuelve el partner del usuario actual (si es alumno portal, busca su `op.student` con `sudo()`).
  - Carga todos los documentos del partner con `sudo()` (necesario para que portal lea attachments).
  - Renderiza template `irg_student_scholarship_documents.portal_scholarship_documents`.

### POST `/my/scholarship-documents/upload`

- **Autenticación:** Usuario autenticado (`auth='user'`)
- **CSRF:** Habilitado (`csrf=True`)
- **Métodos:** Solo POST
- **Descripción:** Procesa el upload de un documento de beca.
- **Parámetros (multipart form-data):**
  - `scholarship_file` (file, requerido) — Archivo binario.
  - `document_name` (string, opcional) — Nombre descriptivo del documento.
  - `note` (string, opcional) — Observaciones del alumno.

- **Validaciones:**
  1. Archivo presente y con nombre válido.
  2. Extensión en lista permitida (`ALLOWED_EXTENSIONS`).
  3. Contenido no vacío.
  4. Tamaño ≤ 10 MB (`MAX_FILE_SIZE_BYTES`).

- **Respuesta exitosa:** Redirige a `/my/scholarship-documents?success=1`.
- **Errores posibles:**
  - "Selecciona un archivo." — No se subió archivo.
  - "El archivo no tiene nombre." — Filename vacío.
  - "Formato no permitido. Usa PDF, JPG, PNG, DOC o DOCX." — Extensión no válida.
  - "El archivo está vacío." — Contenido vacío tras leer.
  - "El archivo supera el límite de 10 MB." — Excede `MAX_FILE_SIZE_BYTES`.

## Seguridad / Record Rules

### Modelo `irg.scholarship.type`

**Acceso:**
- **Usuarios internos** (`base.group_user`): CRUD completo.
- **Usuarios portal** (`base.group_portal`): Solo lectura.

**Record rule portal:**
- `rule_irg_scholarship_type_portal_active` — Los usuarios portal solo ven tipos de beca activos (`[('active', '=', True)]`).

### Modelo `irg.scholarship.document`

**Acceso:**
- **Usuarios internos** (`base.group_user`): CRUD completo.
- **Usuarios portal** (`base.group_portal`): Solo lectura (la creación se hace con `sudo()` tras validación de identidad).

**Record rule portal:**
- `rule_irg_scholarship_document_portal_own` — Los usuarios portal solo ven sus propios documentos (`[('partner_id', '=', user.partner_id.id)]`).

### Uso de `sudo()` en controladores

El módulo usa `sudo()` en dos puntos del portal:

1. **Resolución de alumno:** Para que usuarios portal sin acceso directo a `op.student` puedan resolver su registro de alumno y obtener su `partner_id`.
2. **Lectura/creación de documentos:** Los usuarios portal no tienen permisos de escritura en `irg.scholarship.document` ni en `ir.attachment` (modelo subyacente de `fields.Binary`).

**Justificación:** Estos `sudo()` están protegidos porque:
- El partner siempre se deriva del usuario autenticado (`request.env.user`).
- Solo se leen/crean documentos asociados a ese partner.
- Todas las validaciones de archivo (tamaño, formato, contenido) se ejecutan antes del `sudo()`.
- Las record rules adicionales previenen accesos indebidos si se intenta forzar otro partner_id.

Este patrón es seguro y necesario para que los usuarios portal puedan interactuar con sus propios documentos sin exponer vulnerabilidades.

## Dependencias externas

- **`openeducat_core`** — Modelo `op.student` para resolución de alumno en portal.
- **`openeducat_web`** — Modelo `openeducat.portal.menu` para entrada dinámica en campus.
- **`isep_website_custom`** — Dependencia de infraestructura web del proyecto.

## Notas técnicas

### Extensiones permitidas

Definidas en constante `ALLOWED_EXTENSIONS`:

```python
{'.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx'}
```

Para cambiar las extensiones permitidas, modifica esta constante en [controllers/portal.py](../../../addons-extra/extrairg/irg_student_scholarship_documents/controllers/portal.py).

### Límite de tamaño de archivo

Definido en constante `MAX_FILE_SIZE_BYTES`:

```python
10 * 1024 * 1024  # 10 MB
```

Para aumentar el límite, modifica esta constante **y** ajusta el límite de Nginx (`client_max_body_size`) y PHP-FPM si corresponde.

### Almacenamiento de archivos

Los documentos se almacenan usando `fields.Binary(attachment=True)`, lo que significa que Odoo los guarda en el filestore (directorio de attachments) en lugar de la base de datos. Esto optimiza el rendimiento y el tamaño de backups.

### Acceso a descargas desde portal

La descarga de archivos usa la URL estándar de Odoo:

```
/web/content/irg.scholarship.document/{id}/file/{filename}?download=true
```

Esta ruta está protegida por las record rules de portal — solo se puede descargar si el documento pertenece al usuario autenticado.

## Tests

El módulo incluye suite de tests en [tests/test_scholarship_documents.py](../../../addons-extra/extrairg/irg_student_scholarship_documents/tests/test_scholarship_documents.py) con cobertura de:

- **`test_partner_stores_scholarship_documents`** — Verifica que los documentos se asocian correctamente al partner y el campo `scholarship_type_id` se resuelve vía related field.
- **`test_portal_user_only_sees_own_documents`** — Verifica que las record rules previenen que un usuario portal vea documentos de otros alumnos.

**Ejecutar tests:**

```bash
docker exec odoo_latest odoo \
  -c /etc/odoo/odoo.conf \
  -d <dbname> \
  --test-tags=irg_student_scholarship_documents \
  --stop-after-init \
  --db_host=pgodoo_latest
```

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_student_scholarship_documents \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_student_scholarship_documents \
    --stop-after-init --db_host=pgodoo_latest
```

## Rollback / Desinstalación

Para desinstalar el módulo de forma limpia:

1. **Desde la interfaz de Odoo:**
   - Activar modo desarrollador.
   - Ir a Aplicaciones → Buscar "IRG Student Scholarship Documents".
   - Desinstalar.

2. **Desde CLI:**

```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> \
    --uninstall irg_student_scholarship_documents \
    --stop-after-init \
    --db_host=pgodoo_latest
```

**Advertencia:** La desinstalación eliminará:
- Todos los registros de `irg.scholarship.type`.
- Todos los registros de `irg.scholarship.document` (incluyendo archivos adjuntos).
- Los campos añadidos a `res.partner` (`irg_scholarship_type_id`, `irg_scholarship_document_ids`).
- El menú del portal del alumno.

**Antes de desinstalar, considera:**
- Exportar los documentos de beca si necesitas conservar el historial.
- Verificar que ningún otro módulo depende de `irg_student_scholarship_documents`.
- Hacer backup de la base de datos.

**Dependientes conocidos:**
- `irg_student_scholarship_webhook` — Usa el modelo `irg.scholarship.document` para crear documentos vía API. Si este módulo está instalado, desinstálalo primero.
