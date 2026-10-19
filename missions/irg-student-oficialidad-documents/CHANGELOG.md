# Changelog — irg-student-oficialidad-documents

## 16.0.1.0.0 — 2026-10-15

### Anadido

- Modulo `irg_student_oficialidad_documents`: catalogo de 7 tipos de documento de oficialidad (nacional, internacional y `matricula-unimarconi` para ambos) y modelo `irg.oficialidad.document` con `UNIQUE(partner_id, document_type_id)`.
- Resumen por alumno (`X/4`), checklist Recibido/Pendiente y aviso informativo si el VAT no encaja con `student_type`, en **Detalle Oficialidad** de `op.student`. Se conserva `annex_9`.
- Lista de documentos descargables en la ficha del alumno; adjuntos privados; ACL solo para usuarios internos.
- Modulo `irg_student_oficialidad_webhook`: `POST /irg/oficialidad/webhook/document` con Bearer token (`irg_student_oficialidad_webhook.token`, vacio por defecto y `noupdate`).
- El `student_type` lo envia la app y se confia en el; el VAT solo avisa, nunca bloquea.
- Reenvio del mismo tipo para el mismo contacto actualiza el documento (idempotente).

### Seguridad (Security Advisor `[YES]`, C1–C10)

- `compare_digest` sobre bytes UTF-8; token vacio = no configurado (fail closed).
- Validacion: token → JSON → campos/`student_type` → archivo → tipo de documento → email → escritura.
- Email sin comodines; saneado de `filename` y textos; sin PII ni token en logs; 500 generico con rollback.
- Riesgos residuales aceptados: token unico compartido, `student_type` confiado desde la app, sobrescritura sin historial.

### Verificacion

- 91 tests Odoo (25 documentos + 66 webhook), 0 fallos; sintaxis Python/XML correcta.
- E2E TestSprite de la vista **Detalle Oficialidad**: 8 escenarios en verde (BD desechable, entorno restaurado).
- Evidencia en `verification.json` y `artifacts/`.

### Documentacion

- `doc/modules/extrairg/irg_student_oficialidad_webhook.md`
- `addons-extra/extrairg/irg_student_oficialidad_documents/README.md`

### Limitaciones conocidas

- Sin limite de peticiones ni de tamano en Odoo: configurar el proxy (`client_max_body_size` ~14m, `limit_req`) y comprobar `dbfilter`.
- Validacion de archivos solo por extension (sin magic bytes) y sin auditoria de cambios de `student_type`.
- Un reenvio no reinicia el `state` del documento.
- Fuera de alcance: portal, n8n saliente y la aplicacion Next.js.
