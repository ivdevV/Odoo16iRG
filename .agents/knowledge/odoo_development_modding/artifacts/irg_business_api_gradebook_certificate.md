# Fachada API: certificado de notas PDF (`file_b64`)

## Contexto

Un agente no puede usar `execute_kw` ni `/web/content` de sesión. El comando `irg_generate_gradebook_certificate` genera el PDF de **notas** (completo o parcial) y deja el binario en `result_snapshot` para que el agente lo reenvíe por su canal.

`document_type` admite solo `gradebook` y `gradebook_partial`. Diploma, matrícula y asistencia son comandos propios (`irg_generate_diploma`, `irg_generate_enrollment_certificate`, `irg_generate_attendance_certificate`); si llegan como tipo de este comando, se rechazan con el nombre del comando nuevo. Ver `irg_business_api_academic_documents.md`.

## Split de generación

El wizard backend (`irg.certificate.wizard`) solo selecciona notas. Este comando llama a `action_generate()`. No crea `irg.certificate.request` para diploma/matrícula/asistencia.

## Gotcha: no usar la clave `datas`

`sanitize_mapping` recorta claves que contienen `datas`, `raw` o `bin_size`. El PDF debe ir como `file_b64`. El checksum es SHA-256 de los bytes decodificados.

## Gotcha: leer el adjunto con `bin_size=False`

`ir.attachment.datas` en contexto `bin_size` no es el fichero. El apply hace `browse(...).with_context(bin_size=False)` antes de decodificar.

## Gotcha: firmante explícito

El wizard backend tiene `default='raimon'`. La fachada exige `signer` en el payload (`dpto_academico` o `raimon`) y lo copia a los vals, para que el default no se active en silencio.

## Reglas de libreta

Igual que el portal para notas: `gradebook` exige `state == done`. `gradebook_partial` se permite con libreta abierta.

## Fuera de este comando

Diploma académico, certificado de matrícula y certificado de asistencia. Diplomados (`irg.diplomado.*`) y actas TFM/TFG.

## Retención

`irg.api.operation.unlink()` está denegado. Cada approve deja una copia base64 del PDF en `result_snapshot`, además del `ir.attachment` privado. Es auditoría deliberada para el agente, no un envío al alumno. La record rule limita la lectura al `requested_by` y a `base.group_system`. No hay cron de purga.

## Flujo oficial

Apply recupera el PDF parseando `/web/content/<id>` de la acción de descarga, no buscando el último registro.
