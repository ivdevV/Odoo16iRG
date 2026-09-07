# Fachada API: certificado de notas con `file_b64`

## Contexto

Un agente no puede usar `execute_kw` ni `/web/content` de sesión. El comando `irg_generate_gradebook_certificate` genera el PDF por el wizard oficial y deja el binario en `result_snapshot` para que el agente lo reenvíe por su canal.

## Gotcha: no usar la clave `datas`

`sanitize_mapping` recorta claves que contienen `datas`, `raw` o `bin_size`. El PDF debe ir como `file_b64`. El checksum es SHA-256 de los bytes decodificados.

## Gotcha: leer el adjunto con `bin_size=False`

`ir.attachment.datas` en contexto `bin_size` no es el fichero. El apply hace `browse(...).with_context(bin_size=False)` antes de decodificar.

## Gotcha: firmante explícito

El wizard backend tiene `default='raimon'`. La fachada exige `signer` en el payload (`dpto_academico` o `raimon`) y lo copia a los vals, para que el default no se active en silencio.

## Retención

`irg.api.operation.unlink()` está denegado. Cada approve deja una copia base64 del PDF en `result_snapshot`, además del `ir.attachment` privado. Es auditoría deliberada para el agente, no un envío al alumno. La record rule limita la lectura al `requested_by` y a `base.group_system`. No hay cron de purga; una limpieza futura sería un comando admin aparte, no un `unlink` genérico.

## Flujo oficial

Apply crea `irg.certificate.wizard` y llama `action_generate()`. El certificado se resuelve parseando `/web/content/<id>` de la acción de descarga, no buscando el último registro.
