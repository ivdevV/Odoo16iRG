# irg_student_scholarship_documents

**Categoria:** extrairg  
**Version:** 16.0.1.1.0  
**Licencia:** LGPL-3  
**Instalable:** Si  
**Autor:** IRG  
**Depende de:** `base`, `contacts`, `portal`, `website`, `openeducat_core`, `openeducat_scholarship_enterprise`, `openeducat_web`, `isep_website_custom`

---

## Que hace este modulo

Centraliza la documentacion de solicitudes de beca en contactos y alumnos de OpenEduCat. Reutiliza el catalogo oficial de tipos de beca de OpenEduCat (`op.scholarship.type`), el mismo que se administra desde el menu **Becas > Tipos de becas** y que incluye el campo **Monto** (`amount`).

El modulo anade una pestana **Beca** en `res.partner` y `op.student`, permite adjuntar documentos con archivo binario, y ofrece una pagina de portal para que el alumno suba documentacion.

## Funcionalidades principales

- Usa `op.scholarship.type` como fuente de verdad para los tipos de beca.
- Anade `irg_scholarship_type_id` en `res.partner`, apuntando a `op.scholarship.type`.
- Anade `irg_scholarship_document_ids` en `res.partner` para listar documentos de beca.
- Crea el modelo `irg.scholarship.document` para guardar documentos, archivos, estado y observaciones.
- Muestra la misma informacion en `op.student` gracias a la delegacion de OpenEduCat por `partner_id`.
- Anade portal `/my/scholarship-documents` con subida de archivos.
- Valida extensiones permitidas y tamano maximo de 10 MB.
- Protege portal para que cada usuario vea solo sus documentos.

## Modelos

| Modelo | Tipo | Uso |
| --- | --- | --- |
| `op.scholarship.type` | OpenEduCat | Catalogo oficial de tipos de beca con nombre y monto. |
| `res.partner` | Heredado | Campos `irg_scholarship_type_id` y `irg_scholarship_document_ids`. |
| `op.student` | Delegado | Muestra los campos del partner asociado. |
| `irg.scholarship.document` | Nuevo | Documentos aportados por alumno/contacto. |

### Campos en `res.partner`

- `irg_scholarship_type_id`: `Many2one` a `op.scholarship.type`.
- `irg_scholarship_document_ids`: `One2many` a `irg.scholarship.document`.

### Modelo `irg.scholarship.document`

- `name`: nombre del documento.
- `partner_id`: contacto/alumno asociado.
- `scholarship_type_id`: related almacenado desde `partner_id.irg_scholarship_type_id`.
- `file`: archivo binario con `attachment=True`.
- `filename`: nombre de archivo.
- `note`: observaciones.
- `state`: `submitted`, `accepted` u `observed`.

## Vistas y UI

### Backend

- Formulario de contacto: pestana **Beca** con tipo de beca y documentos.
- Formulario de alumno: pestana **Beca** con la misma informacion del partner.
- Menu **Contactos > Documentos de beca** para revisar documentos.
- Los tipos se gestionan en el menu OpenEduCat **Becas > Tipos de becas**.

### Portal

- URL: `/my/scholarship-documents`.
- Muestra el tipo de beca asignado al alumno.
- Lista documentos ya aportados.
- Permite subir nuevos documentos con nombre, archivo y observaciones.
- Extensiones permitidas: `.pdf`, `.jpg`, `.jpeg`, `.png`, `.doc`, `.docx`.
- Tamano maximo: 10 MB.

## Seguridad

- Usuarios internos (`base.group_user`) tienen CRUD sobre `irg.scholarship.document`.
- Usuarios portal (`base.group_portal`) solo tienen lectura.
- Record rule portal: cada portal solo ve documentos donde `partner_id = user.partner_id.id`.
- La creacion desde portal usa `sudo()` despues de resolver el partner desde el usuario autenticado y validar archivo.
- La seguridad de `op.scholarship.type` la proporciona `openeducat_scholarship_enterprise`.

## Tests

Tests en [tests/test_scholarship_documents.py](../../../addons-extra/extrairg/irg_student_scholarship_documents/tests/test_scholarship_documents.py):

- Asociacion de documentos y tipo OpenEduCat al partner.
- Restriccion portal para ver solo documentos propios.

## Migraciones

### Version 16.0.1.1.0

**Pre-migracion:** Mapeo de tipos de beca heredados desde `irg_scholarship_type` a `op.scholarship.type`.

En versiones anteriores se usaba una tabla custom `irg_scholarship_type`. La migración realiza:

1. **Detección inteligente de nombres traducidos:** Antes de realizar el mapeo, verifica si las columnas `name` en ambas tablas son de tipo `jsonb` (campos traducibles multi-idioma).

2. **Extracción de valores traducidos:** Si detecta `jsonb`, extrae el nombre con la siguiente prioridad:
   - Español (`es_ES`)
   - Inglés (`en_US`)
   - Cualquier otro idioma disponible

3. **Mapeo normalizado:** Compara nombres con `lower(trim())` para hacer coincidir tipos de beca independientemente de mayúsculas/espacios y traducción.

4. **Limpieza de huérfanos:** Anula referencias de `res.partner.irg_scholarship_type_id` que apuntan a tipos que no existen en la tabla OpenEduCat.

**Implementación técnica:** La función auxiliar `_name_text_expression()` genera dinámicamente la expresión SQL apropiada según el tipo de columna (texto plano o `jsonb`), garantizando compatibilidad con entornos multilenguaje.

**Contexto:** Este hotfix fue necesario porque algunos despliegues tenían campos traducibles en `irg_scholarship_type.name`, y el mapeo simple por texto fallaba al no considerar la estructura `jsonb`.

## Instalacion / Actualizacion

```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_student_scholarship_documents \
    --stop-after-init --db_host=pgodoo_latest
```

## Rollback

Desinstalar `irg_student_scholarship_documents` desde Apps o shell Odoo. Los tipos de beca OpenEduCat (`op.scholarship.type`) no se eliminan porque pertenecen a `openeducat_scholarship_enterprise`; si se requiere conservar documentos, exportarlos antes de desinstalar.

**Nota sobre migracion:** La pre-migración de la versión 16.0.1.1.0 es irreversible. Una vez ejecutada, los registros de `res.partner.irg_scholarship_type_id` apuntan definitivamente a `op.scholarship.type` y la tabla antigua `irg_scholarship_type` (si existía) deja de usarse. Si se requiere revertir a una versión anterior del módulo que dependía de la tabla custom, se debe restaurar un backup de base de datos previo a la migración.
