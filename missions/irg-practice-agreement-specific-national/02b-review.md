# Review de código — irg-practice-agreement-specific-national

Revisor independiente. No se ha editado código de producción ni ejecutado tests.

Alcance revisado: `git diff 1770cff4` sobre
`addons-extra/extrairg/irg_practice_agreement_specific/` (7 ficheros modificados)
más el untracked `views/agreement_document_especifico_nacional.xml`. Se han leído
además, como contexto de contrato, los ficheros no modificados del módulo
(`controllers/portal_agreement.py`, `data/mail_template_data.xml`,
`security/ir.model.access.csv`, `wizard/..._views.xml`,
`views/practice_request_views.xml`) y los módulos vecinos
`irg_practice_agreement_types` e `irg_practice_agreement_sign`.

No se revisan `00-spec.md`, `01-plan.md`, `execution.md`, `verification.json`,
evidencias, changelog, `README.md` ni knowledge; el plan y la spec se usan
únicamente como contrato funcional.

Veredicto: **REVIEW OK** — 0 BLOQUEANTE, 1 IMPORTANTE, 5 MENOR, 6 NIT.

## Comprobación de módulos prohibidos

`git status --porcelain` limitado a `addons-extra/` devuelve exclusivamente los
8 caminos de `irg_practice_agreement_specific`. En concreto:

- `irg_practice_agreement_sign`: sin cambios. Está trackeado (27 ficheros en
  `git ls-files`) y `git status` para esa ruta está vacío.
- `irg_practice_agreement_types`: sin cambios. También trackeado (17 ficheros) y
  `git status` vacío para esa ruta. A diferencia de la misión anterior ya no hace
  falta comprobar por mtime.
- `isep_practices_2` y el resto de `addons-extra/`: sin cambios.

La excepción autorizada queda por tanto contenida dentro del módulo previsto.

## Comprobaciones del contrato funcional que pasan

- **`ESPECIFICO_TYPES` cubre ambos tipos.** `models/practice_agreement.py:8`:
  `('especifico_internacional', 'especifico_nacional')`. `_is_especifico()`
  (`:72-74`) evalúa `in ESPECIFICO_TYPES`, así que la doble firma, el token del
  estudiante en `create()`, `action_ensure_student_token()`,
  `action_send_by_email()`, `action_complete_signature()` y
  `action_complete_student_signature()` cubren nacional sin más cambios.
- **`selection_add` y `ondelete` coherentes.** `:15-22` añaden el valor y su
  `set default`; al desinstalar el módulo los nacionales caen al `marco_nacional`
  que `irg_practice_agreement_types` declara como default.
- **Wizard con las dos opciones.**
  `wizard/practice_agreement_specific_create_wizard.py:39-46` lista ambos valores
  con `required=True` y `default='especifico_internacional'`, y la vista
  `wizard/practice_agreement_specific_create_wizard_views.xml:10` ya renderizaba
  el campo con `widget="radio"`, de modo que el radio muestra las dos opciones sin
  tocar la vista.
- **Report: el `div.page` marco se oculta para ambos específicos.**
  `report/practice_agreement_report_templates.xml:6` pasa a
  `doc.agreement_type not in ('especifico_internacional', 'especifico_nacional')`,
  y `:9` / `:15` insertan dos `div.page` hermanos con `t-call` a la plantilla
  internacional y a la nacional respectivamente. No hay solape: los dos `t-if`
  son mutuamente excluyentes.
- **Predicados alineados Python/QWeb** conforme a
  `irg_selection_qweb_predicate_alignment.md`. Un `grep` de `especifico_nacional`
  sobre `addons-extra/` devuelve las cuatro capas coherentes: modelo
  (`ESPECIFICO_TYPES`), report (`:6`, `:15`), portal (`:7`, `:12`, `:15`, `:18`,
  `:28`, `:118`) y `attrs` del formulario
  (`views/practice_agreement_views.xml:10,34`, ambos con
  `('agreement_type', 'not in', [...])`). El controlador no necesitó cambios
  porque ya usaba `_is_especifico()` en las cinco rutas.
- **Sin `hasattr` en QWeb** (`irg_qweb_hasattr_unsafe.md`): `grep -rn hasattr`
  sobre el módulo no devuelve nada.
- **`print_report_name` defensivo** (`irg_report_print_name_foreign_xmlid.md`):
  `report/practice_agreement_report_templates.xml:72` tiene las cuatro ramas
  esperadas y repite la guarda `'agreement_type' in object._fields` en cada
  condición, con `Marco_Nacional` como caída final.
- **Plantilla nacional genérica y sin PII.** `grep -rn -E
  "Encuentro|Miroslava|CURP|Paterna|INMIRA"` sobre el módulo solo encuentra las
  aserciones negativas del test; el documento usa exclusivamente campos
  (`student_name`, `student_vat`, `center_official_name`, `tutor_name`, …) con
  placeholders `'_____'` de reserva.
- **QUINTA nacional correcta.**
  `views/agreement_document_especifico_nacional.xml:90-93`: responsabilidad
  civil, accidentes personales y asistencia sanitaria «corren a cargo de iRG»,
  sin la cláusula de «fuera de España». Un `grep` de «fuera de España» sobre
  `addons-extra/` solo la encuentra en la plantilla internacional del módulo y en
  `irg_practice_agreement_types/views/agreement_clauses_internacional.xml`, ambas
  bajo `t-if` de otro tipo, así que no puede contaminar el render nacional.
- **Ley 26/2015 presente y acotada.** Aparece una sola vez, en
  `agreement_document_especifico_nacional.xml:134`. No existe en ninguna otra
  plantilla, lo que hace fiable la aserción negativa del test internacional.
- **Refactor del bloque de firmas sin regresión.** El bloque inline del
  internacional se extrae a `agreement_especifico_signatures`
  (`report/practice_agreement_report_templates.xml:24-68`) y se invoca con
  `t-call` desde los dos `div.page`. El contenido es idéntico al anterior
  (alumno / iRG con `firma_raimon.png` de respaldo / centro, más el pie de
  auditoría bajo `doc.state == 'completed'`). `doc` e `image_data_uri` siguen
  disponibles porque el `t-call` se resuelve dentro del contexto del report.
- **Nombre del PDF sin regresión para internacional.**
  `models/practice_agreement.py:183-194`: `'Convenio_Especifico_%s_%s_%s_%s.pdf'`
  con `slug='Internacional'` reproduce exactamente la cadena previa
  `Convenio_Especifico_Internacional_<alumno>_<centro>_<id>.pdf`. Los adjuntos ya
  existentes no cambian de patrón.
- **MRO intacto.** `specific` sigue delante de `types`; para los específicos
  `action_complete_signature` no llama a `super()`, así que el renombrado a
  `Convenio_Marco_*` de `irg_practice_agreement_types:32-54` no se ejecuta sobre
  un nacional. La firma del centro sola no pone `state = 'completed'`.
- **`write()` de `irg_practice_agreement_types` no interfiere.** Bloquea solo
  `vals` que contengan `agreement_type` sobre estados `sent/completed/cancelled`;
  `_finalize_especifico_pdf()` escribe `state` y `pdf_attachment_id`, nunca el
  tipo.
- **xpath sin selector `string`.** Los 9 xpath del módulo usan `hasclass()`,
  `@name`, `contains(., …)` o `//header`. Ninguno usa `@string`.
- **Sin secretos.** El diff no introduce credenciales, tokens fijos ni URLs con
  autenticación. Los tokens siguen siendo `uuid4` por registro y el email se
  resuelve por campo, no hardcodeado.
- **Cobertura de tests suficiente para el alcance.**
  `tests/test_practice_agreement_specific.py` añade `test_wizard_creates_nacional`
  (`:240`), `test_html_nacional_has_irg_insurance_not_abroad` (`:247`),
  `test_html_internacional_keeps_abroad_insurance` (`:261`, guarda de
  contaminación cruzada en los dos sentidos) y
  `test_nacional_both_signatures_complete` (`:267`), que verifica que la firma del
  centro sola no completa, que ambas sí, y que el adjunto contiene
  `Especifico_Nacional` y no `Marco`. `:119` fija la presencia del valor en la
  selección y `test_marco_still_completes_with_center_only` (`:284`) protege la
  no regresión del marco.

## Hallazgos abiertos

### BLOQUEANTE

Ninguno.

### IMPORTANTE

**I1 — Las dos plantillas específicas duplican el clausulado compartido y pueden
divergir en silencio.**
`views/agreement_document_especifico_nacional.xml` frente a
`views/agreement_document_especifico_internacional.xml`. Las cláusulas TERCERA
(`:62-74` nacional / `:62-74` internacional), CUARTA en su parte común, SEXTA y
casi toda la sección de Normativa son texto legal idéntico copiado. La misión ya
demostró que sabe factorizar (`agreement_especifico_signatures`), pero no lo hizo
con el clausulado: a partir de ahora cualquier corrección de la normativa hay que
aplicarla dos veces y ningún test detecta la divergencia, porque las aserciones de
cada test miran solo su propio documento. Sugerencia: extraer los bloques
realmente comunes (TERCERA, la parte fija de CUARTA, SEXTA y los párrafos de
Normativa compartidos) a plantillas `t-call` reutilizables y dejar en cada
documento solo lo que de verdad diverge (encabezado, PRIMERA, QUINTA, SÉPTIMA y
los párrafos de normativa propios). No es bloqueante porque hoy el contenido es
correcto en ambos ficheros y los criterios de aceptación se cumplen; es deuda de
mantenimiento con impacto en un documento legal.

### MENOR

**M1 — Encabezado del documento nacional gramaticalmente incompleto.**
`views/agreement_document_especifico_nacional.xml:5-9`. El `h3` termina en
«… PARA LA REALIZACIÓN DE PRÁCTICAS DE FORMACIÓN y <centro>», sin nombrar a la
primera parte, de modo que el PDF imprime literalmente «…DE FORMACIÓN y Centro
Colaborador Test S.L.». Falta el «ENTRE INSTITUTO RAIMON GAJA (iRG)» antes de la
«y». El defecto viene heredado de la plantilla internacional, pero aquí es un
fichero nuevo y es texto de portada de un convenio firmado. Corrección: insertar
la parte iRG en el encabezado (y valorar arreglar también la internacional en una
misión aparte, para no ampliar el alcance de esta).

**M2 — La Normativa nacional conserva párrafos de contexto internacional.**
`views/agreement_document_especifico_nacional.xml:128-129`: «Las prácticas no
incluyen alojamiento, transporte hasta la ciudad donde se realicen las prácticas,
**visados** o cualquier otra prestación no descrita». En un convenio nacional la
mención a visados es incoherente con la propia razón de ser de la variante.
Corrección: eliminar «visados» del listado nacional, o confirmar con el usuario
que el texto del ejemplo debe reproducirse tal cual.

**M3 — Nombre del adjunto y `print_report_name` siguen usando criterios
distintos (arrastre de la misión anterior, ahora duplicado).**
`models/practice_agreement.py:183-194` produce
`Convenio_Especifico_Nacional_<alumno>_<centro>_<id>.pdf`, mientras
`report/practice_agreement_report_templates.xml:72` produce
`Convenio_Especifico_Nacional_<centro>_<referencia>`. El PDF archivado y la
descarga bajo demanda desde backend siguen sin coincidir, y ahora la
incoherencia existe en dos variantes en lugar de una. Unificar el criterio en un
único método del modelo invocado también desde `print_report_name`.

**M4 — `print_report_name` de `irg_practice_agreement_specific` puede revertirse
a la expresión de `types` (arrastre agravado).**
`report/practice_agreement_report_templates.xml:71-73`. Los dos módulos
sobrescriben el mismo `ir.actions.report` ajeno y gana el último cargado. En
instalación y en `-u all` gana `specific`, pero un
`-u irg_practice_agreement_types` aislado devuelve la expresión de dos ramas y un
específico nacional se imprimiría como `Convenio_Marco_Nacional_…`. Con la
variante nacional el escenario es más probable, porque hay más razones para tocar
el módulo de tipos. Misma sugerencia que M3: un único punto de verdad en el
modelo.

**M5 — El tipo «Convenio Específico Nacional» vuelve a ser alcanzable desde el
formulario de `irg_practice_agreement_types` sin pasar por el wizard.**
`models/practice_agreement.py:15-18` reintroduce el valor en la selección, y
`irg_practice_agreement_types/views/practice_agreement_views.xml:10,23,34`
muestra `agreement_type` en formulario, lista y agrupación. Un usuario del
backend puede crear un convenio nacional a mano sin solicitud, sin alumno y sin
email de estudiante; el documento se renderiza con placeholders y el convenio
queda atascado a la espera de una firma de alumno que nadie puede solicitar
(`action_send_by_email` exige `student_email`). No es bloqueante porque el
comportamiento es idéntico al de `especifico_internacional`, ya aceptado, y
porque a diferencia de la ronda 1 de la misión anterior el documento generado ya
es el correcto (las cuatro capas están alineadas), no un marco mal etiquetado.
Sugerencia: una `@api.constrains` o un `default_get`/dominio que exija
`practice_request_id` cuando `agreement_type in ESPECIFICO_TYPES`, o marcar el
valor como no seleccionable manualmente.

### NIT

- `models/practice_agreement.py:185-189`: el `slug` se calcula con
  `'Nacional' if … == 'especifico_nacional' else 'Internacional'`. Hoy es seguro
  porque el método solo se invoca desde `_finalize_especifico_pdf()`, pero el
  `else` implícito etiquetaría «Internacional» cualquier tipo futuro. Un `dict`
  explícito por tipo sería más fiel al criterio de predicado explícito del
  proyecto.
- `report/practice_agreement_report_templates.xml:72`: la expresión repite tres
  veces `'agreement_type' in object._fields` en una sola línea muy larga. Se
  puede evaluar la guarda una vez (`object._fields.get('agreement_type') and …`)
  o delegar en un método del modelo, ganando legibilidad sin perder la defensa.
- `views/portal_agreement_templates.xml:118-123`: la página del alumno usa
  `t-if especifico_nacional` / `t-else` internacional, mientras el resto del
  módulo usa predicados explícitos con `in (...)`. Hoy es inalcanzable para un
  marco (solo los específicos tienen `student_access_token`), pero el `t-else`
  como cajón de sastre rompe el patrón que la propia knowledge de alineación de
  predicados pide mantener.
- `views/agreement_document_especifico_nacional.xml:110`: el bloque se titula
  «Normativa», mientras el internacional usa «Anexo I – Normativa»
  (`agreement_document_especifico_internacional.xml:111`). Conviene unificar la
  nomenclatura entre documentos de la misma familia.
- `tests/test_practice_agreement_specific.py:114`: el test se sigue llamando
  `test_agreement_type_includes_especifico_internacional` cuando ahora también
  afirma la presencia de `especifico_nacional`. Renombrarlo a
  `..._includes_especificos`.
- `tests/test_practice_agreement_specific.py`: no hay ninguna aserción sobre la
  selección ni el default del propio wizard, al estilo de
  `irg_practice_agreement_types/tests/test_practice_agreement_types.py:112-116`.
  El comportamiento queda cubierto de forma indirecta por
  `test_wizard_creates_nacional`, pero un test del campo fijaría el radio de dos
  opciones que pide el plan.

## Nota fuera del alcance de esta review

`addons-extra/extrairg/irg_practice_agreement_specific/README.md:19` afirma «El
específico nacional no está en esta entrega», lo que queda desmentido por este
cambio. Es documentación, así que no cuenta como hallazgo de código y no afecta al
veredicto, pero conviene que el documentador lo corrija junto con la línea 4.

## Recordatorio de gates posteriores

El diff toca `views/`, `report/` y plantillas de portal, así que el disparo por
scope de la capa E2E (`e2e_testsprite`) declarado en `01-plan.md` es obligatorio y
no puede registrarse como `skipped`. Esta review no lo sustituye ni ejecuta
ninguna prueba.

## Veredicto

REVIEW OK
