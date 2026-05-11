# irg_student_scholarship_documents

## 1. Titulo corto

Documentacion de becas para alumnos y contactos.

## 2. Resumen objetivo

Crear una funcionalidad para registrar el tipo de beca seleccionado por un alumno y gestionar multiples documentos asociados a esa beca. La informacion se mostrara en el contacto, en el perfil backend del alumno y en una pagina del portal del alumno.

## 3. Motivo / justificacion

La gestion de becas requiere centralizar la documentacion aportada por cada alumno sin modificar modulos nativos ni OpenEduCat. Se implementa como modulo extra `irg_*` usando herencia sobre `res.partner` y vistas heredadas, ya que `op.student` delega en `res.partner` mediante `_inherits` y permite mostrar los mismos datos sin duplicarlos.

## 4. Alcance exacto

- Modelos nuevos: `irg.scholarship.type` y `irg.scholarship.document`.
- Modelo heredado: `res.partner`.
- Vistas backend: formulario de contactos, formulario de alumnos, vistas/listados de tipos de beca y documentos.
- Portal: pagina `/my/scholarship-documents` y ruta POST de subida de documentos.
- Seguridad: ACLs y record rules para usuarios internos y portal.
- Assets/reports: no aplica.

## 5. Diseno tecnico

- `res.partner` recibe `irg_scholarship_type_id` y `irg_scholarship_document_ids`.
- `op.student` no duplica campos: los campos de `res.partner` se usan desde el alumno por delegacion de OpenEduCat.
- `irg.scholarship.type` almacena tipos configurables de beca con nombre, descripcion, secuencia y activo.
- `irg.scholarship.document` almacena multiples documentos por contacto con binario `attachment=True`, nombre de archivo y estado simple.
- Vista contacto: `inherit_id="base.view_partner_form"`, `xpath` sobre `//notebook`.
- Vista alumno: `inherit_id="openeducat_core.view_op_student_form"`, `xpath` sobre `//notebook`.
- Portal: controller `auth='user'`, `website=True`, `csrf=True` en POST; valida que el usuario corresponde al alumno/contacto antes de guardar.
- Menu portal: registro `openeducat.portal.menu` hacia `/my/scholarship-documents`.

## 6. Dependencias

`base`, `contacts`, `portal`, `website`, `openeducat_core`, `openeducat_web`, `isep_website_custom`.

## 7. Backwards-compatibility / migracion

No modifica tablas nativas ni cambia comportamientos existentes. Anade campos y modelos nuevos. Los contactos existentes quedan sin tipo de beca y sin documentos hasta que se informen manualmente o desde el portal.

## 8. Casos de prueba / criterios de aceptacion

- Un usuario interno puede crear tipos de beca configurables.
- Un contacto puede tener un tipo de beca y multiples documentos asociados.
- El formulario de alumno muestra la misma informacion de beca que el contacto enlazado.
- Un alumno portal puede ver su beca y subir documentos permitidos.
- Un usuario portal no puede ver documentos de otro contacto.
- El POST de subida rechaza archivos vacios, demasiado grandes o con extension no permitida.

## 9. Rollback plan

```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf -d <dbname> \
    -u base --stop-after-init --db_host=pgodoo_latest
```

Si se requiere retirar la funcionalidad, desinstalar `irg_student_scholarship_documents` desde Apps o desde shell Odoo. Los adjuntos/documentos creados por el modulo deben exportarse antes si se necesitan conservar.

## 10. Estimacion y responsable

- Estimacion: 1 jornada tecnica para implementacion y validacion local.
- Responsable: IRG / GitHub Copilot como asistente de implementacion.
