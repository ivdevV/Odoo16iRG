# Spec — irg-business-api-gradebook-certificate

Copia de trabajo de la misión. Diseño canónico:
`docs/superpowers/specs/2026-09-07-irg-generate-gradebook-certificate-design.md`

## Problema

`irg_business_api` no genera certificados de notas. El agente IA no puede obtener el PDF sin la UI ni sin ORM genérico.

## Solución

Comando de escritura `irg_generate_gradebook_certificate`:

1. `create` → preview con validación de libreta, tipo, firma y envío.
2. `irg_approve_operation` → `irg.certificate.wizard.action_generate()`.
3. `result_snapshot` incluye `file_b64` + `checksum` para que el agente pase el PDF.
4. Adjunto `public=False`. Sin mail, sin factura portal, sin publicación.

## Criterios de aceptación

1. Payload explícito: `gradebook_student_id`, `document_type` (`gradebook_partial`|`gradebook`), `certificate_type` (`digital`|`physical`|`custom`|`physical_apostilled`), `signer` (`dpto_academico`|`raimon`). `idempotency_key` en el registro de operación.
2. Parcial admite libreta abierta. Final exige `done`. Firma obligatoria y válida. Físico exige `shipping_type`.
3. Misma `idempotency_key` + mismo payload no duplica solicitudes.
4. El PDF se crea con el wizard oficial.
5. El resultado verificado trae `certificate_request_id`, `attachment_id`, `state`, `name`, `checksum`, `file_b64`. El checksum coincide con el PDF decodificado.
6. `public` es falso. No se envían plantillas de certificado ni se publica el adjunto.
7. Tests del módulo en verde. E2E TestSprite skipped: el diff no toca vistas, QWeb, assets, portal ni controladores HTTP.

## Fuera de alcance

- Diplomas y otros documentos.
- HTTP nuevo.
- Credenciales de Google Chat.
- Descarga genérica de adjuntos ajenos a este flujo.
