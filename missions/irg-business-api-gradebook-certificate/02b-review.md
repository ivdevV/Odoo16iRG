# Review de código — irg-business-api-gradebook-certificate

Revisor independiente (no es el codificador). Revisión de solo lectura: no se ha
editado código de producción ni se han ejecutado pruebas. La ejecución real de
tests corresponde al validador.

## Alcance revisado

Archivos funcionales de la misión:

- `addons-extra/extrairg/irg_business_api/models/api_constants.py`
- `addons-extra/extrairg/irg_business_api/models/api_operation.py`
- `addons-extra/extrairg/irg_business_api/models/gradebook_service.py`
- `addons-extra/extrairg/irg_business_api/tests/test_gradebook_certificate.py`
- `addons-extra/extrairg/irg_business_api/tests/__init__.py`
- `addons-extra/extrairg/irg_business_api/__manifest__.py`

Contexto leído sin revisar como entregable: `00-spec.md`, `01-plan.md`, el diseño
canónico `docs/superpowers/specs/2026-09-07-irg-generate-gradebook-certificate-design.md`,
`PROJECT.md` y la nota de knowledge `irg_business_api_command_facade.md`.

Referencias auxiliares consultadas para verificar contratos externos:
`irg_gradebook_certificates/wizard/certificate_wizard.py`,
`irg_gradebook_certificates/models/irg_certificate_request.py`,
`irg_business_api/models/api_serializer.py`,
`irg_business_api/models/survey_service.py`,
`irg_business_api/security/ir_rule.xml`,
`irg_business_api/security/ir.model.access.csv`,
`isep_gradebook/models/app_gradebook_student.py`.

Alcance del diff verificado con `git diff --stat`: 157 inserciones y 1 borrado
(el bump de versión). `gradebook_service.py` suma 136 líneas sin ninguna
eliminación, es decir, `get_gradebook_summary` y `get_student_grade_evidence`
quedan intactos, tal como exigía el plan. No hay cambios en
`irg_gradebook_certificates` ni en ningún módulo ajeno.

## Verificación de criterios

| # | Criterio | Resultado | Evidencia |
| --- | --- | --- | --- |
| 1 | `irg_generate_gradebook_certificate` es `kind=write` (preview → approve) | Cumple | `api_constants.py:152-163` declara `'kind': 'write'`; `api_operation.py:184-211` enruta `write` a `_irg_run_preview` y deja el apply para `_irg_apply_preview` vía `irg_approve_operation`. |
| 2 | Payload explícito y firmante obligatorio sin default silencioso | Cumple | `api_constants.py:154-162` fija el allowlist de claves (claves extra las rechaza `api_operation.py:137-139`). `gradebook_service.py:100-117` valida `document_type`, `certificate_type`, `signer` y `shipping_type`. El wizard tiene `default='raimon'`, pero el servicio siempre pasa `signer` explícito en `vals`, así que el default nunca se activa. |
| 3 | Parcial admite libreta abierta; final exige `done` | Cumple | `gradebook_service.py:118-122`. Confirmado contra la selección real de `app.gradebook.student.state` (`draft`/`in_progress`/`done`, default `in_progress`) en `isep_gradebook/models/app_gradebook_student.py:29-32`. |
| 4 | Apply usa el flujo oficial `action_generate` y no busca "el último certificado" | Cumple | `gradebook_service.py:183-185` llama `wizard.action_generate()`; `gradebook_service.py:137-150` resuelve el adjunto parseando `/web/content/(\d+)` del `ir.actions.act_url`, sin ningún `search` por recencia. |
| 5 | Resultado con ids, `state`, `name`, `checksum` sha256 y `file_b64` (no `datas`) | Cumple | `gradebook_service.py:195-205`. Verificado que ninguna clave del resultado colisiona con `SECRET_TOKENS` (`api_constants.py:9-13`), cuyo filtrado es por subcadena en `api_serializer.contains_secret_key`: `file_b64`, `checksum`, `attachment_id`, `attachment_name`, `mimetype` y `certificate_request_id` sobreviven a `sanitize_mapping`. El checksum se calcula sobre los bytes decodificados y `file_b64` reutiliza el mismo base64 del adjunto, así que son consistentes por construcción. |
| 6 | Adjunto `public=False`, sin plantillas de correo ni factura de portal | Cumple | `irg_certificate_request._generate_and_attach_pdf` crea el adjunto con `'public': False`; `gradebook_service.py:186-187` aborta si quedara público. `action_generate` no invoca `_send_digital_notification`, `_send_paid_notification`, `_send_team_notification` ni `_create_portal_invoice`. |
| 7 | Idempotencia por campo de `irg.api.operation`, no por clave JSON | Cumple | `idempotency_key` es campo del modelo (`api_operation.py:48`) con constraint SQL única y reutilización de la operación previa en `api_operation.py:142-153`. No aparece en el allowlist de claves del payload. |
| 8 | Dependencia blanda: `UserError` si los certificados no están instalados | Cumple | `gradebook_service.py:83-87` verifica `irg.certificate.wizard`, `irg.certificate.request` y `app.gradebook.student` en el registro. `__manifest__.py:13-17` no añade `irg_gradebook_certificates` a `depends`. La guarda es alcanzable tanto en preview como en apply, porque ambos pasan por `_gradebook`. |
| 9 | Gotchas de la fachada respetados | Cumple | Grep sobre el módulo: no hay `irg_api_internal` ni `self.env.sudo()` en código de producción (la única aparición de `irg_api_internal` está en `test_access_permissions.py`, que precisamente comprueba que el flag NO funciona). `gradebook_service.py` no llama a `sudo()`; usa el env ya elevado que le pasa `api_operation.py:186,390`. `bin_size=False` aplicado en el `browse` del adjunto (`gradebook_service.py:142`) antes de leer `datas`. |
| 10 | Tests de validación, PDF privado + checksum, no duplicar clave y ausencia de correo | Cumple | `test_gradebook_certificate.py`: `test_unknown_payload_key_rejected`, `test_missing_signer_rejected`, `test_invalid_signer_rejected`, `test_final_certificate_requires_done_gradebook`, `test_partial_allows_open_gradebook`, `test_physical_requires_shipping`, `test_approve_returns_private_pdf_and_checksum`, `test_same_idempotency_key_does_not_duplicate`, `test_approve_does_not_queue_certificate_mail`. `tests/__init__.py:8` importa el módulo, requisito de descubrimiento recogido en `PROJECT.md`. |

Comprobaciones adicionales de arquitectura y seguridad:

- **Exposición del PDF.** `result_snapshot` queda protegido por la regla
  `rule_irg_api_operation_own` (`ir_rule.xml`), que limita la lectura al
  `requested_by` y a `base.group_system`. Un miembro del grupo API no puede leer
  los snapshots de otro usuario, así que el `file_b64` no se filtra entre
  usuarios de la fachada.
- **Anti-forja.** El apply reconstruye el payload desde `proposed_after`, que es
  campo `readonly` escrito solo por el servidor; `write()` público está bloqueado
  con `AccessError`. No hay vía RPC para inyectar un `proposed` manipulado.
- **Optimistic lock.** `gradebook_service.py:181-182` compara el estado de
  negocio de la libreta entre preview y apply, además del `SELECT … FOR UPDATE`
  y el savepoint que ya aporta `_irg_apply_preview`. Coincide con el patrón
  documentado en la knowledge base.
- **Atomicidad.** Si la guarda de `public` o la de PDF vacío disparan, el
  `ROLLBACK TO SAVEPOINT irg_api_apply` deshace también la creación del
  `irg.certificate.request`, de modo que no quedan certificados huérfanos.
- **Doble aprobación.** `_irg_apply_preview` retorna pronto si el estado ya es
  `applied`/`verified`, así que aprobar dos veces no genera un segundo PDF.

## Hallazgos

### BLOQUEANTE

Ninguno.

### MENOR

1. **`result_snapshot` acumula PDFs sin vía de purga.**
   `gradebook_service.py:195-205` guarda el PDF completo en base64 dentro de
   `irg.api.operation.result_snapshot`, y `irg.api.operation.unlink()` lanza
   `AccessError` incondicionalmente (`api_operation.py:96-97`). Cada certificado
   generado por la API deja, por tanto, una copia binaria permanente y no
   borrable desde el ORM, duplicada respecto al `ir.attachment`. Con PDFs de
   certificado reales (cientos de KB a algún MB, según plantilla y número de
   asignaturas) la tabla crece sin techo y sin retención. El diseño acepta
   explícitamente que el snapshot sea grande, pero no contempla el ciclo de vida.
   Recomendación: documentar la retención en el contrato y prever una purga
   (por ejemplo un cron administrativo que vacíe `result_snapshot` de operaciones
   `verified` de este código pasados N días), o al menos dejar constancia del
   coste en la nota de knowledge de la fase de documentación.

2. **`'public': False` es un literal, no el estado leído del adjunto.**
   `gradebook_service.py:204`. La guarda de las líneas 186-187 hace que el valor
   sea correcto hoy, pero el snapshot deja de ser evidencia y pasa a ser una
   afirmación. El propio módulo ya tiene el patrón bueno en
   `survey_service.py:200` (`bool(attachment.public) if 'public' in attachment._fields else False`).
   Además, `test_approve_returns_private_pdf_and_checksum:149` afirma sobre ese
   literal, con lo que esa aserción concreta es vacua; la que sí vale es la de la
   línea 151 sobre el registro real. Recomendación: devolver el valor leído.

3. **Preview crea un `irg.certificate.wizard` que se descarta sin explicación.**
   `gradebook_service.py:154`. El `create` existe solo para disparar los
   `@api.constrains` del wizard, que además duplican las validaciones que
   `_validated_certificate_vals` acaba de hacer. Sin comentario, se lee como
   código muerto y un futuro lector lo borrará. Recomendación: o se elimina, o se
   añade una línea explicando que valida contra las constraints oficiales del
   wizard antes de comprometer el preview.

4. **Mensaje de error único para cuatro fallos distintos.**
   `_certificate_from_download_action` (`gradebook_service.py:137-150`) lanza
   `'Certificate PDF was not generated.'` cuando la URL no casa, cuando el
   adjunto no existe, cuando el `res_model` no es el esperado y cuando el
   certificado no existe; `apply` reutiliza el mismo texto para el PDF vacío
   (línea 190). En producción, con el `ir.actions.act_url` cambiado de formato o
   con un adjunto mal enlazado, el diagnóstico será imposible desde el log.
   Recomendación: diferenciar los mensajes o registrar el motivo con `_logger`.

5. **Valores de payload no textuales producen excepciones crudas en vez de `UserError`.**
   `gradebook_service.py:116` evalúa `custom_options not in CUSTOM_OPTIONS`
   contra un `set`: si el agente envía una lista o un dict, salta
   `TypeError: unhashable type` en lugar de un `UserError` legible. Lo mismo con
   `custom_description`, que se pasa tal cual al campo `Text` del wizard sin
   comprobar el tipo. El patrón `(payload.get(x) or '').strip()` del resto del
   archivo tiene la misma debilidad y es la norma preexistente del módulo, así
   que no es una regresión, pero `custom_options` es el único punto donde el
   fallo es una excepción de tipo y no un `AttributeError` evidente.
   Recomendación: normalizar con `str(...)` o rechazar los no-`str` con
   `UserError`.

6. **`certificate_count` se captura en `before` y nunca se usa.**
   `gradebook_service.py:156-162` cuenta los certificados existentes de la
   libreta, pero `apply` solo compara `gradebook_state` (línea 181). Como dato de
   auditoría en el snapshot es defendible; como guarda de concurrencia está a
   medias. Recomendación: o se usa para detectar generaciones concurrentes, o se
   documenta que es informativo.

7. **El mock de `_convert_to_pdf` deja ficheros temporales.**
   `test_gradebook_certificate.py:76-81` sustituye `_convert_to_pdf`, que es
   justamente el método que hace `os.unlink` del `.docx` y del `.pdf`
   intermedios. Con el mock, cada test que aprueba deja el `.docx` generado por
   `_fill_template` en el `tempfile` del contenedor. Son tres tests por ejecución;
   no rompe nada, pero `AGENTS.md` pide limpieza de datos temporales.
   Recomendación: envolver el mock en un `side_effect` que borre `docx_path`
   antes de devolver `PDF_BYTES`.

8. **Huecos de cobertura sobre reglas que el código sí implementa.**
   No hay test para: `certificate_type` inválido, el rechazo de `shipping_type`
   en certificados no físicos (`gradebook_service.py:113-114`, regla más estricta
   que la spec y no cubierta), `gradebook_student_id` inexistente, la guarda
   "the gradebook changed after preview" (línea 181-182) y la guarda de
   `public` (líneas 186-187). Los criterios de aceptación de la misión sí quedan
   cubiertos, por eso no es bloqueante, pero son reglas de servidor sin red.

### NIT

- `api_operation.py:296,328`: `GradebookService(env)` se instancia en línea
  dentro del literal del diccionario, mientras el resto de servicios usan
  variable local (`elearning`, `access`, `academic`, `moodle`, `survey`). Además
  la línea supera con holgura el ancho habitual del archivo. Coherencia
  puramente estética.
- `_irg_apply_preview` deja `target_model='app.gradebook.student'` y `target_id`
  apuntando a la libreta, no al `irg.certificate.request` creado. Es defendible
  (el objetivo del comando es la libreta) y el id del certificado viaja en el
  `result_snapshot`, pero la traza de auditoría no apunta al artefacto producido.
- `gradebook_service.py:186`: `if 'public' in attachment._fields` es defensivo
  innecesario, `public` siempre existe en `ir.attachment` en Odoo 16. Mismo
  patrón que ya usa `survey_service`, así que es consistente con la casa.
- `test_gradebook_certificate.py:40-45`: el fixture escribe `partner_id`,
  `course_id` y `batch_id` en `app.gradebook.student`, que son `related` a
  `admission_id` y por tanto escriben de vuelta en la admisión. Con estos datos
  son los mismos valores, así que es inocuo, pero basta con `admission_id`.

## Conclusión

El comando cumple los diez criterios funcionales y de seguridad exigidos. Respeta
los gotchas de la fachada (sin flag de contexto, sin `self.env.sudo()`, sin
dependencia dura, `bin_size=False`), usa el flujo oficial del wizard, resuelve el
adjunto por la URL de la acción en lugar de por recencia, mantiene el PDF privado
y no dispara correo ni factura. El diff está acotado al módulo de la misión y no
toca `irg_gradebook_certificates`.

Ningún hallazgo compromete la seguridad, la arquitectura ni el plan. Los ocho
puntos MENOR son mejoras de robustez, observabilidad y ciclo de vida del dato; el
primero (retención del `file_b64` en un modelo sin `unlink`) merece decisión
explícita del usuario durante la fase de documentación, pero no invalida la
implementación ni justifica reabrir Implementación.

VERDICT: APPROVE
