# irg_student_scholarship_webhook

## 1. Titulo corto

Webhook externo para documentacion de becas.

## 2. Resumen objetivo

Crear un endpoint seguro para que una aplicacion externa pueda enviar por email la documentacion de solicitudes de beca y registrarla automaticamente en Odoo.

## 3. Motivo / justificacion

El modulo `irg_student_scholarship_documents` ya centraliza la informacion de becas en `res.partner` y `op.student`. Esta integracion se implementa como modulo extra independiente para no modificar modulos nativos ni alterar el modulo funcional existente, reutilizando sus modelos y vistas por dependencia.

## 4. Alcance exacto

- Controlador nuevo para webhook JSON HTTP.
- Servicio tecnico para validar token, payload, alumno/contacto y archivo.
- Modelo destino reutilizado: `irg.scholarship.document`.
- Identificacion del alumno/contacto por email.
- Formato de archivo: contenido base64 en JSON.
- Assets, vistas backend y modelos persistentes nuevos: no aplica.

## 5. Diseno tecnico

- Modulo tecnico: `irg_student_scholarship_webhook`.
- Ruta: `POST /irg/scholarship/webhook/document`.
- Tipo de ruta: `type='http'`, `auth='none'`, `csrf=False` para integracion servidor-servidor.
- Autenticacion: cabecera `Authorization: Bearer <token>` validada contra `ir.config_parameter` con clave `irg_student_scholarship_webhook.token`.
- Payload esperado:
  - `email`: obligatorio.
  - `filename`: obligatorio.
  - `document_content_base64`: obligatorio.
  - `document_name`: opcional; si falta se usa `filename`.
  - `scholarship_type_name`: opcional; nombre del tipo de beca en `op.scholarship.type`.
  - `scholarship_type_key`: opcional; clave normalizada del nombre del tipo de beca en `op.scholarship.type`.
  - `note`: opcional.
- Resolucion de persona:
  - Buscar primero `op.student` por `partner_id.email`.
  - Si no hay alumno, buscar `res.partner` por email.
  - Si hay mas de una coincidencia en el nivel usado, devolver error de ambiguedad.
- Validacion de archivo:
  - Extensiones permitidas: PDF, JPG, JPEG, PNG, DOC y DOCX.
  - Tamano maximo: 10 MB tras decodificar base64.
  - Rechazo de base64 invalido, archivo vacio, filename vacio o extension no permitida.
- Escritura:
  - Si llega tipo de beca, resolverlo contra `op.scholarship.type` activo y asignarlo a `res.partner.irg_scholarship_type_id`.
  - Crear o actualizar `irg.scholarship.document` por `partner_id`, `filename` y `name` para evitar duplicados accidentales.
  - Usar `sudo()` solo tras validar token y payload, porque la aplicacion externa no dispone de usuario Odoo.

## 6. Dependencias

`base`, `openeducat_core`, `openeducat_scholarship_enterprise`, `irg_student_scholarship_documents`.

## 7. Backwards-compatibility / migracion

No modifica tablas nativas ni cambia vistas existentes. El modulo depende de los modelos ya creados por `irg_student_scholarship_documents`; si se desinstala, el webhook deja de estar disponible sin borrar la documentacion de becas ya registrada por el modulo base.

## 8. Casos de prueba / criterios de aceptacion

- El webhook rechaza peticiones sin token.
- El webhook rechaza token invalido.
- El webhook rechaza payload JSON invalido o campos obligatorios ausentes.
- El webhook rechaza emails inexistentes o ambiguos.
- El webhook asigna un tipo de beca OpenEduCat cuando recibe `scholarship_type_name` o `scholarship_type_key` valido.
- El webhook rechaza tipos de beca inexistentes o ambiguos.
- El webhook rechaza base64 invalido, archivos vacios, extensiones no permitidas y archivos de mas de 10 MB.
- Con token valido, email existente y archivo valido, se crea un documento de beca asociado al contacto correcto.
- Si se repite la misma combinacion `partner_id`, `filename` y `document_name`, se actualiza el documento existente en lugar de duplicarlo.

## 9. Rollback plan

```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf -d <dbname> \
    -u base --stop-after-init --db_host=pgodoo_latest
```

Si se requiere retirar la integracion, desinstalar `irg_student_scholarship_webhook` desde Apps o desde shell Odoo. El modulo no elimina documentos de beca existentes porque pertenecen al modulo base `irg_student_scholarship_documents`.

## 10. Estimacion y responsable

- Estimacion: 0,5 jornada tecnica para implementacion, pruebas y documentacion.
- Responsable: IRG / GitHub Copilot como asistente de implementacion.
