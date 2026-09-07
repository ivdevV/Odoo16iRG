# Review de código — irg-business-api-certificate-types

Revisor independiente (no es el codificador). Revisión de solo lectura: no se ha
editado código de producción ni se han ejecutado pruebas. La ejecución real de
tests corresponde al validador.

## Alcance revisado

Archivos funcionales de la misión:

- `addons-extra/extrairg/irg_business_api/models/gradebook_service.py`
- `addons-extra/extrairg/irg_business_api/models/api_constants.py`
- `addons-extra/extrairg/irg_business_api/tests/test_gradebook_certificate.py`
- `addons-extra/extrairg/irg_business_api/__manifest__.py`

Contexto leído sin revisar como entregable: `00-spec.md`, `01-plan.md`, la review
previa `missions/irg-business-api-gradebook-certificate/02b-review.md` y las notas
de knowledge `irg_business_api_gradebook_certificate.md` e
`irg_business_api_command_facade.md`.

Referencias auxiliares consultadas para verificar contratos externos:
`irg_gradebook_certificates/wizard/certificate_wizard.py`,
`irg_gradebook_certificates/models/irg_certificate_request.py`,
`irg_gradebook_certificates/__manifest__.py`,
`irg_certificate_attendance/models/irg_certificate_request.py`,
`irg_certificate_attendance/views/irg_certificate_request_views.xml`,
`irg_certificate_attendance/controllers/portal.py`,
`irg_campus_certificates_portal/controllers/portal.py`,
`irg_generacion_diplomas/wizard/diploma_wizard.py`,
`irg_generacion_diplomas/models/diploma_registry.py`,
`irg_business_api/models/api_operation.py`,
`irg_business_api/models/api_serializer.py`,
`irg_business_api/tests/common.py`.

Alcance del diff verificado con `git status --porcelain` y `git diff --stat`: los
únicos archivos de producción tocados son los cuatro declarados en el plan
(`gradebook_service.py` +52/−7, `api_constants.py` +2/−1, `__manifest__.py` +1/−1)
más el archivo de tests (+186/−0, sin ninguna línea eliminada: no se ha debilitado
ni borrado ninguna prueba anterior). **No hay cambios en `irg_gradebook_certificates`
ni en `irg_certificate_attendance`**, tal como exigía el plan. El otro archivo sucio
del árbol, `.gitignore`, ya estaba modificado antes de esta misión y sus seis líneas
(`.envrc`, `.superpowers/`) no guardan relación con el certificado.

## Verificación de criterios

| # | Criterio | Resultado | Evidencia |
| --- | --- | --- | --- |
| 1 | El código de operación `irg_generate_gradebook_certificate` se conserva (Lisa no se rompe) | Cumple | `api_constants.py:73` mantiene la clave y solo cambia la etiqueta de la Selection (`'Generate gradebook certificate PDF'` → `'Generate certificate PDF'`). Las etiquetas de Selection no se almacenan en base de datos, así que el cambio no requiere migración ni invalida operaciones históricas. |
| 2 | `document_type` admite gradebook, gradebook_partial, diploma, attendance y enrollment | Cumple | `gradebook_service.py:11-13`. El conjunto coincide exactamente con la Selection oficial de `irg.certificate.request.document_type` (`irg_gradebook_certificates/models/irg_certificate_request.py:135-147`), sin inventar valores ni omitir ninguno. El mensaje de error de `gradebook_service.py:105-109` enumera los cinco. |
| 3 | Notas (gradebook / gradebook_partial) siguen el wizard `action_generate()` | Cumple | `gradebook_service.py:174-178` enruta `WIZARD_DOCUMENT_TYPES` al `irg.certificate.wizard`. `WIZARD_DOCUMENT_TYPES` (`gradebook_service.py:14`) replica la Selection real del wizard, que solo acepta notas (`certificate_wizard.py:14-17`); pasar `diploma` al wizard habría reventado por valor de Selection inválido, y el split lo evita. |
| 4 | Diploma / enrollment / attendance crean `irg.certificate.request` con origin=backend, state=done y `_generate_and_attach_pdf()` | Cumple | `gradebook_service.py:179-184`. Es el mismo par de valores que usa el flujo oficial de backend (`certificate_wizard.py:123-124`), de modo que no se inventa un estado nuevo ni se dispara `_process_payment`, que es el único punto que envía correo (`irg_certificate_request.py:400-415`). |
| 5 | La descarga se resuelve por `/web/content/<id>` y no por recencia | Cumple | `_issue_certificate` devuelve `cert.action_download_pdf()` (`gradebook_service.py:184`), cuya URL es `/web/content/%d?download=true` (`irg_certificate_request.py:1630-1639`), y `_certificate_from_download_action` (`gradebook_service.py:158-171`) la parsea con `CONTENT_ID_RE`. Ninguna rama nueva introduce `search(..., order='id desc', limit=1)`. |
| 6 | `gradebook` y `diploma` exigen libreta `state == done`; parcial, asistencia y matrícula se permiten con libreta abierta | Cumple | `gradebook_service.py:15` (`FINAL_DOCUMENT_TYPES = {'gradebook', 'diploma'}`) y `gradebook_service.py:125-129`. Coincide literalmente con la regla del portal, `irg_campus_certificates_portal/controllers/portal.py:176` (`if document_type in ('gradebook', 'diploma') and gradebook.state != 'done'`). Importante: el modelo `irg.certificate.request` **no** tiene ninguna constraint propia para diploma y la del wizard solo cubre `gradebook` (`certificate_wizard.py:104-110`), así que el servicio es aquí el único gate y estaba obligado a replicarlo. Lo hace correctamente y en `_validated_certificate_vals`, es decir, tanto en preview como en apply. |
| 7 | `session_id` obligatorio en asistencia si el campo existe; `UserError` claro si el módulo no está | Cumple | `gradebook_service.py:143-153`. La guarda de dependencia blanda se hace por presencia del campo (`'session_id' not in self.env['irg.certificate.request']._fields`), no por `ir.module.module`, que es el patrón correcto y el mismo que ya usa el módulo. Además valida que la `op.session` exista, cosa que ni el portal ni el modelo oficial hacen. |
| 8 | `session_id` prohibido en el resto de tipos | Cumple | `gradebook_service.py:154-155`. Y `_issue_certificate` / preview filtran la clave antes de tocar el wizard (`gradebook_service.py:176,190`), que no tiene ese campo salvo con el módulo de asistencia instalado. |
| 9 | El preview de asistencia usa `new()` + `_validate_attendance_request()` (HC / HomeClass) | Cumple | `gradebook_service.py:192-194`. `new()` no persiste, de modo que el preview no deja registros huérfanos, y `_validate_attendance_request` funciona sobre el `NewId` porque lee `rec.session_id.id` y `rec.gradebook_student_id.id`, que ya son enteros reales (`irg_certificate_attendance/models/irg_certificate_request.py:21-44`). El `ValidationError` que lanza es subclase de `UserError` en Odoo 16, así que llega al cliente como error de negocio y no como traza. |
| 10 | Resultado igual que antes: `file_b64`, checksum SHA-256, `public=False`, sin mail, sin factura portal | Cumple | `gradebook_service.py:230-249` está intacto respecto a la versión anterior (el diff no toca ese bloque salvo la línea de `_issue_certificate`). El checksum se calcula sobre los bytes decodificados y `file_b64` reutiliza el mismo base64, así que son consistentes por construcción; `bin_size=False` sigue aplicado en el `browse` del adjunto (`gradebook_service.py:163`). Ninguna ruta nueva llama a `_create_portal_invoice` ni a `_send_*_notification`. |
| 11 | `session_id` añadido al allowlist de claves JSON | Cumple | `api_constants.py:162`. Sin esa entrada, `api_operation.py:137-139` habría rechazado el payload con `Unsupported payload keys`. Verificado además que `session_id` no contiene ninguno de los `SECRET_TOKENS` (`api_constants.py:9-13`), cuyo filtrado es por subcadena en `api_serializer.contains_secret_key`, de modo que sobrevive a `sanitize_mapping` tanto en `proposed_after` como en el rebuild del apply. |
| 12 | `file_b64` no puede llamarse `datas` | Cumple | `gradebook_service.py:247` conserva la clave `file_b64`. `'datas'` está en `SECRET_TOKENS` y el resultado se pasa por `ser.sanitize_mapping` en `api_operation.py:414`, así que renombrarla la habría borrado del snapshot. |
| 13 | Tests: diploma parchea `_generate_diploma_pdf_content`; asistencia parchea `_fill_template` + `_convert_to_pdf` | Cumple | `test_gradebook_certificate.py:138-153`. El parcheo es correcto para cada ruta: `_generate_and_attach_pdf` bifurca en `document_type == 'diploma'` (`irg_certificate_request.py:1594-1599`), y el módulo de asistencia solo trae plantillas Word de asistencia, no de notas, de ahí que haya que cortar antes con `_fill_template`. |
| 14 | Criterio 1 de la spec: enrollment en libreta abierta, preview + approve con PDF privado | Cumple | `test_enrollment_allows_open_gradebook` y `test_enrollment_approve_returns_private_pdf` (`test_gradebook_certificate.py:272-295`), con el helper `_assert_verified_private_pdf` (`155-169`) que comprueba estado `verified`, checksum, `public` en el registro real de `ir.attachment`, `origin='backend'` y ausencia de `invoice_id`. |
| 15 | Criterio 2 de la spec: diploma con libreta abierta falla, con libreta `done` genera PDF | Cumple | `test_diploma_requires_done_gradebook` y `test_diploma_approve_on_done_gradebook` (`test_gradebook_certificate.py:297-317`). El primero afirma sobre el texto del mensaje (`'finalizada'`), no solo sobre el tipo de excepción, lo cual distingue el fallo correcto de cualquier otro `UserError`. |
| 16 | Versión del manifiesto | Cumple | `__manifest__.py:4` → `16.0.1.3.0`. Bump menor coherente con una ampliación funcional retrocompatible. |
| 17 | Sin cambios fuera del módulo de la misión | Cumple | `git status --porcelain`: solo los cuatro archivos declarados. Ver «Alcance revisado». |

Comprobaciones adicionales de arquitectura y seguridad:

- **Anti-forja y optimistic lock.** El apply reconstruye el payload desde
  `proposed_after` (`gradebook_service.py:211-224`), que es campo `readonly`
  escrito solo por el servidor, y vuelve a pasar por
  `_validated_certificate_vals`. Es decir, la clave nueva `session_id` **no**
  entra por un atajo: se revalida (existencia de la sesión, tipo de documento
  correcto) exactamente igual que en el preview. La comparación de
  `gradebook_state` (`gradebook_service.py:226-227`) sigue vigente para todos los
  tipos nuevos, así que cerrar o reabrir una libreta entre preview y approve
  sigue abortando la operación.
- **Atomicidad.** Las tres rutas nuevas ocurren dentro del `SAVEPOINT
  irg_api_apply` de `api_operation.py:392-410`, de modo que un fallo de plantilla,
  de LibreOffice o de la guarda de `public` deshace también el
  `irg.certificate.request` recién creado. No quedan certificados huérfanos en
  estado `done` sin PDF.
- **Doble aprobación.** `_irg_apply_preview` retorna pronto si el estado ya es
  `applied`/`verified` (`api_operation.py:374-375`), así que aprobar dos veces no
  emite un segundo diploma ni un segundo número de registro.
- **Exposición del PDF.** Sin cambios: `result_snapshot` sigue protegido por
  `rule_irg_api_operation_own`, así que el `file_b64` de un diploma no se filtra
  entre usuarios de la fachada.
- **Sin regresión en las lecturas.** `get_gradebook_summary` y
  `get_student_grade_evidence` no aparecen en el diff.
- **Gotchas de la fachada.** Las ramas nuevas no introducen `self.env.sudo()`,
  ni flags de contexto tipo `irg_api_internal`, ni dependencia dura en el
  manifiesto. El `sudo()` que aparece en la generación (adjunto, registro de
  diploma) vive en `irg_gradebook_certificates`, fuera del alcance editable.

## Hallazgos

### BLOQUEANTE

Ninguno.

### MENOR

1. **La asistencia no comprueba que la sesión pertenezca al lote del alumno, y el
   único control existente es de UI.**
   `gradebook_service.py:148-153` valida que la `op.session` exista, y
   `_validate_attendance_request` valida que la *libreta* sea HomeClass o de lote
   HC, pero nadie comprueba que `session.batch_id == gradebook.batch_id`. En el
   backend esa restricción existe solo como dominio de vista
   (`irg_certificate_attendance/views/irg_certificate_request_views.xml:16`,
   `domain="[('batch_id', '=', batch_id)]"`), que es precisamente el tipo de
   control que `AGENTS.md` prohíbe tomar como sustituto de un control de
   servidor. El resultado es que se puede emitir un certificado oficial firmado
   que afirma que el alumno asistió a una clase concreta de otro grupo o de otro
   curso.
   No lo clasifico como BLOQUEANTE porque el agujero es preexistente y no lo
   abre esta misión: el POST del portal hace `int(session_id)` directo desde el
   formulario sin ninguna comprobación de lote
   (`irg_certificate_attendance/controllers/portal.py:155`), de modo que la
   superficie de riesgo ya existía y la ruta API es, de hecho, más estricta
   (exige el grupo de la fachada más una aprobación humana explícita). Aun así,
   la corrección natural cabe entera dentro del archivo que la misión sí posee.
   Recomendación: añadir en `_validated_certificate_vals` una comprobación
   `session.batch_id == gradebook.batch_id` (o, como mínimo, misma `course_id`)
   con su `UserError`, y decidir con el usuario si además se propone el arreglo
   en el modelo oficial como misión aparte.

2. **El preview de asistencia muestra la sesión como un entero desnudo, así que
   la aprobación humana no es informada.**
   `gradebook_service.py:203-209` vuelca en `proposed` el mismo `vals`, con
   `session_id: 42` y nada más. Quien aprueba la operación —el único gate humano
   del comando— no puede verificar de qué clase, asignatura ni fecha se trata sin
   consultar la base a mano. El propio portal sí resuelve esos datos para el
   alumno (`irg_certificate_attendance/controllers/portal.py:60-67` devuelve
   `class_title`, `subject_name` y `date`). Recomendación: enriquecer `proposed`
   con `session_name`, `session_subject` y `session_date`; es coste cero y
   convierte la aprobación en una decisión real. Nota: son claves de solo
   lectura para el humano, y el apply debe seguir reconstruyendo el payload solo
   desde las claves del allowlist, como ya hace.

3. **El diploma no tiene guarda de dependencia blanda, y su fallo aparece en el
   apply en vez del preview.**
   Para asistencia el código comprueba la disponibilidad del módulo en
   `_validated_certificate_vals` (`gradebook_service.py:144-145`), es decir,
   durante el preview y con un mensaje explícito. Para diploma no hay guarda
   equivalente, y sin embargo `_generate_diploma_pdf_content` depende de
   `report.irg_generacion_diplomas.diploma_pdf` y de `irg.diploma.registry`
   (`irg_certificate_request.py:1520-1521,1579`), módulo que **no** figura en los
   `depends` de `irg_gradebook_certificates`
   (`irg_gradebook_certificates/__manifest__.py:23-32`). Si `irg_generacion_diplomas`
   no está instalado, el `KeyError` del registro cae en el `except Exception`
   genérico de `_generate_and_attach_pdf` (`irg_certificate_request.py:1601-1609`)
   y Lisa recibe «No se pudo generar el PDF del certificado. Revise el log.»
   *después* de que un humano ya haya aprobado la operación. Recomendación:
   añadir en el preview, para `document_type == 'diploma'`, la comprobación
   `'irg.diploma.registry' in self.env` con un `UserError` del mismo estilo que
   el de asistencia.

4. **Efecto lateral del diploma no declarado en el preview: número de registro
   oficial y entrada verificable públicamente.**
   Aprobar un diploma por la API ejecuta `_generate_diploma_pdf_content`, que
   consume la secuencia `irg.diploma.registry`, llama a
   `op.sign_certificate.stamp_data` y crea un `irg.diploma.registry` con
   `state='valid'` y una `qr_url` de `institutoraimongaja.com/verificar`
   (`irg_certificate_request.py:1493-1589`). El `proposed` solo anuncia
   `will_call: irg.certificate.request._generate_and_attach_pdf`
   (`gradebook_service.py:208`), sin mencionar que se emite un identificador
   oficial verificable desde fuera. Además, aunque el `ROLLBACK TO SAVEPOINT`
   deshace el registro si algo falla después, la secuencia de Postgres no se
   revierte, de modo que un fallo deja un hueco en la numeración oficial.
   Recomendación: declarar el efecto en `will_call` o en `proposed`, y dejar
   constancia del hueco de secuencia en la nota de knowledge durante
   Documentación.

5. **El registro de diploma creado por esta vía queda sin `attachment_id`, y el
   portal lo listará como válido sin poder servirlo.**
   `irg_certificate_request._generate_diploma_pdf_content` crea el
   `irg.diploma.registry` sin `attachment_id` (`irg_certificate_request.py:1579-1587`),
   a diferencia del wizard oficial de diplomas, que sí lo enlaza
   (`irg_generacion_diplomas/wizard/diploma_wizard.py:118-127`). Como el portal
   del campus lista los diplomas `state='valid'` del alumno y su descarga
   redirige a `?error=no_pdf` cuando falta el adjunto
   (`irg_campus_certificates_portal/controllers/portal.py:54-57,236-237`), cada
   diploma emitido por la API dejará una entrada visible e indescargable para el
   alumno. Es un defecto preexistente de `irg_gradebook_certificates` —lo sufre
   igual el flujo de portal con pago— y la misión tiene prohibido tocar ese
   módulo, así que no procede corregirlo aquí. Pero sí procede documentarlo como
   limitación conocida del `document_type: diploma` y decidir si merece misión
   propia.

6. **La cobertura real de asistencia es prácticamente nula en el entorno de
   validación.**
   De los cuatro tests de asistencia, tres se saltan cuando
   `irg_certificate_attendance` no está instalado
   (`test_gradebook_certificate.py:329-330,354-355` y el gate `_attendance_available`
   de `64-68`), que es exactamente el caso de la DB donde se obtuvo el GREEN. El
   único que corre es `test_attendance_without_module_is_rejected`. Es decir: el
   `new()` + `_validate_attendance_request()` del preview, el viaje de
   `session_id` por preview → `proposed` → apply, la comprobación de existencia
   de `op.session` y el parcheo doble de `_fill_template`/`_convert_to_pdf` no
   están ejercidos por la evidencia GREEN, pese a ser el grueso del código nuevo.
   El criterio 3 de la spec ya se escribió condicionado («si el módulo está
   instalado»), así que no es un incumplimiento, pero el validador debe registrar
   el `skipped` con su justificación explícita en `verification.json` en lugar de
   dejar que los 70 tests en verde sugieran una cobertura que no existe.

7. **`_patch_pdf` ejecuta el `_fill_template` real también en la ruta de
   matrícula y deja el `.docx` temporal en el contenedor.**
   `test_gradebook_certificate.py:130-135` solo sustituye `_convert_to_pdf`, que
   es justamente el método que hace `os.unlink` de los intermedios
   (`irg_certificate_request.py:1484-1489`). Con `document_type: enrollment` la
   rama no-notas de `_fill_template` guarda el `.docx` y encima lo reescribe con
   `_ensure_bottom_right_arcs` (`irg_certificate_request.py:1166-1174`), así que
   cada test de matrícula deja un fichero suelto. Era ya un MENOR de la review
   anterior y ahora afecta a más pruebas; `AGENTS.md` pide limpieza de datos
   temporales. Recomendación: dar al mock un `side_effect` que borre `docx_path`
   antes de devolver `PDF_BYTES`. `_patch_attendance_pdf` no tiene el problema
   porque corta antes, en `_fill_template`.

8. **`'Certificate PDF was not generated.'` sigue cubriendo cinco fallos
   distintos, ahora sobre más rutas.**
   `_certificate_from_download_action` (`gradebook_service.py:158-171`) usa el
   mismo texto para URL que no casa, adjunto inexistente, `res_model` inesperado
   y certificado inexistente, y `gradebook_service.py:234` lo reutiliza para PDF
   vacío. Con tres generadores distintos detrás (wizard de notas, plantilla Word
   de matrícula/asistencia, ReportLab de diploma), diagnosticar desde el log pasa
   de difícil a imposible. Hallazgo heredado de la review anterior, no corregido,
   y con impacto mayor ahora. Recomendación: diferenciar los mensajes o registrar
   el motivo con `_logger`.

9. **Hallazgos heredados que siguen abiertos.** Se mantienen sin cambios y sin
   corrección: la retención indefinida del `file_b64` en `result_snapshot` de un
   modelo cuyo `unlink()` siempre lanza `AccessError`; el `'public': False`
   literal de `gradebook_service.py:248` en vez del valor leído del adjunto (que
   además hace vacua la aserción de `_assert_verified_private_pdf:167`, aunque la
   de la línea 168 sobre el registro real sí vale); y `certificate_count`
   (`gradebook_service.py:195-201`) capturado en `before` y nunca usado en el
   apply. No los repito en detalle porque no son de esta misión, pero el primero
   empeora: un diploma en ReportLab es sensiblemente más pesado que un
   certificado de notas.

### NIT

- El comando, el servicio y los métodos siguen llamándose `..._gradebook_certificate`
  y `GradebookService` aunque ahora emiten diplomas, matrículas y asistencias. La
  decisión de conservar el código de operación es correcta y está justificada
  (no romper a Lisa), y la etiqueta de la Selection ya se actualizó, pero el
  nombre interno ha quedado desalineado con el alcance. No merece renombrar nada
  ahora; sí merece una línea en la documentación.
- `gradebook_service.py:14` define `WIZARD_DOCUMENT_TYPES` como `set` de strings,
  y `irg_gradebook_certificates/wizard/certificate_wizard.py:14` define una
  constante homónima como lista de tuplas de Selection. Son cosas distintas con
  el mismo nombre en dos módulos relacionados; conviene al menos no importarlas
  cruzadas por error en el futuro.
- El filtro `{key: value for key, value in vals.items() if key != 'session_id'}`
  aparece duplicado en `gradebook_service.py:176` y `:190`, y en ambos casos es
  inalcanzable: `vals` solo contiene `session_id` cuando `document_type ==
  'attendance'`, y esa rama nunca entra en el camino del wizard. Es defensa
  muerta, correcta pero sin comentario que la explique.
- `gradebook_service.py:154`: `elif session_id:` ignora en silencio un
  `session_id` igual a `0`, `false` o `""` enviado con un tipo no-asistencia, en
  lugar de rechazarlo como clave indebida. Irrelevante en la práctica, pero es
  una asimetría con el rigor del resto de validaciones.
- `_validated_certificate_vals` resuelve la libreta (`gradebook_service.py:103`)
  antes de validar `document_type`, de modo que un `gradebook_student_id`
  inválido enmascara un `document_type` inválido. Afecta solo a la calidad del
  mensaje de error.
- `test_gradebook_certificate.py:78-91`: la admisión HC reutiliza
  `cls.partner.id`, con lo que el mismo partner acumula dos admisiones del mismo
  curso. Es inocuo para lo que se prueba y desaparece con el rollback de
  `TransactionCase`.
- `_patch_attendance_pdf` devuelve la ruta ficticia
  `'/tmp/irg-api-cert-stub.docx'`, que nunca se crea. Funciona porque
  `_convert_to_pdf` está parcheado y jamás la abre, pero acopla el test al orden
  interno de llamadas de `_generate_and_attach_pdf`.
- `target_model`/`target_id` de la operación siguen apuntando a la libreta y no
  al `irg.certificate.request` producido. Heredado y defendible.

## Conclusión

La ampliación cumple los diecisiete criterios funcionales y de seguridad
revisados. El split entre wizard y `irg.certificate.request` es la decisión
arquitectónica correcta y está bien motivado: el wizard oficial solo acepta notas
en su Selection, así que forzar diploma o matrícula por ahí habría reventado. La
regla de libreta `done` para `gradebook` y `diploma` reproduce literalmente la del
portal, y en el caso del diploma el servicio es el único gate existente, cosa que
el código ha detectado y cubierto. La guarda de dependencia blanda de asistencia
se hace por presencia de campo y no por módulo, que es el patrón correcto, y la
validación HC se delega en el modelo oficial mediante `new()`, sin persistir nada
en el preview. La clave `session_id` viaja por el allowlist y se revalida en el
apply, sin atajos. El resultado, el checksum, la privacidad del adjunto y la
ausencia de correo y de factura de portal quedan intactos, y el diff no toca
ninguno de los dos módulos vetados ni degrada ninguna prueba anterior.

Ningún hallazgo compromete la seguridad, la arquitectura ni el plan, por lo que no
procede reabrir Implementación. De los nueve puntos MENOR, tres merecen decisión
explícita del usuario antes de cerrar la misión: la falta de comprobación
servidor de que la sesión pertenece al lote del alumno (agujero preexistente que
esta misión podría cerrar barato desde el archivo que sí posee), la ausencia de
guarda de dependencia para el diploma —que convierte un módulo no instalado en un
fallo posterior a la aprobación humana— y el hecho de que el registro de diploma
generado por esta vía quede indescargable desde el portal del alumno. Los tres se
pueden abordar en Documentación como limitaciones declaradas o abrir como misión
aparte; ninguno invalida la implementación. Aparte de eso, el validador debe
recoger de forma explícita que los tests de asistencia quedaron `skipped` en la
base de datos usada para el GREEN.

VERDICT: APPROVE
