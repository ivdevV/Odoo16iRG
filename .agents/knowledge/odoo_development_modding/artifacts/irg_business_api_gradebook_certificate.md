# Fachada API: certificado PDF (`file_b64`)

## Contexto

Un agente no puede usar `execute_kw` ni `/web/content` de sesión. El comando `irg_generate_gradebook_certificate` genera el PDF oficial y deja el binario en `result_snapshot` para que el agente lo reenvíe por su canal.

`document_type` admite los tipos de `irg.certificate.request`: `gradebook`, `gradebook_partial`, `diploma`, `attendance`, `enrollment`. El código de operación no se duplicó para no romper a Lisa.

## Split de generación

El wizard backend (`irg.certificate.wizard`) solo selecciona notas. Notas van por `action_generate()`. Diploma, matrícula y asistencia crean `irg.certificate.request` (`origin=backend`, `state=done`) y llaman `_generate_and_attach_pdf()`.

Diploma usa ReportLab (`_generate_diploma_pdf_content`), no LibreOffice. Un test que solo parchee `_convert_to_pdf` no cubre diploma.

## Gotcha: no usar la clave `datas`

`sanitize_mapping` recorta claves que contienen `datas`, `raw` o `bin_size`. El PDF debe ir como `file_b64`. El checksum es SHA-256 de los bytes decodificados.

## Gotcha: leer el adjunto con `bin_size=False`

`ir.attachment.datas` en contexto `bin_size` no es el fichero. El apply hace `browse(...).with_context(bin_size=False)` antes de decodificar.

## Gotcha: firmante explícito

El wizard backend tiene `default='raimon'`. La fachada exige `signer` en el payload (`dpto_academico` o `raimon`) y lo copia a los vals, para que el default no se active en silencio.

## Reglas de libreta

Igual que el portal: `gradebook` y `diploma` exigen `state == done`. Parcial, asistencia y matrícula se permiten con libreta abierta. Asistencia exige `session_id` si `irg_certificate_attendance` está instalado (validación HC/HomeClass del modelo oficial vía `new()` en preview).

## Fuera de este comando

Diplomados (`irg.diplomado.wizard` / `irg.diplomado.registry`) y actas TFM/TFG son productos distintos.

El `irg.diploma.registry` que crea `_generate_diploma_pdf_content` puede quedar sin `attachment_id`; el portal de diplomas no servirá ese PDF. El agente sí tiene `file_b64` en el snapshot.

## Retención

`irg.api.operation.unlink()` está denegado. Cada approve deja una copia base64 del PDF en `result_snapshot`, además del `ir.attachment` privado. Es auditoría deliberada para el agente, no un envío al alumno. La record rule limita la lectura al `requested_by` y a `base.group_system`. No hay cron de purga.

## Flujo oficial

Apply recupera el PDF parseando `/web/content/<id>` de la acción de descarga, no buscando el último registro.
