# Review de código — irg-practice-agreement-specific-homeclass

Revisor independiente. No se ha editado código de producción ni ejecutado tests.

Alcance revisado: `git diff HEAD` sobre
`addons-extra/extrairg/irg_practice_agreement_specific/` (7 ficheros
modificados) más el untracked
`views/agreement_document_especifico_homeclass_sincronas.xml`. Working tree
sin commit; base `583891193`. Se han leído además, como contexto de contrato,
los ficheros no modificados del módulo (`controllers/portal_agreement.py`,
`data/mail_template_data.xml`, `security/ir.model.access.csv`,
`wizard/..._views.xml`, `views/practice_request_views.xml`) y los módulos
vecinos `irg_practice_agreement_types` e `irg_practice_agreement_sign`.

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
  `git status` vacío para esa ruta.
- `isep_practices_2` y el resto de `addons-extra/`: sin cambios.

La excepción autorizada queda contenida dentro del módulo previsto
(`16.0.1.2.0`). El `__manifest__.py` declara la plantilla nueva en `data`
antes del report y del portal que la invocan.

## Comprobaciones del contrato funcional que pasan

- **`ESPECIFICO_TYPES` cubre los tres tipos.** `models/practice_agreement.py:8-12`:
  `especifico_internacional`, `especifico_nacional`,
  `especifico_homeclass_sincronas`. `_is_especifico()` (`:78-80`) evalúa
  `in ESPECIFICO_TYPES`, así que la doble firma, el token del estudiante en
  `create()`, `action_ensure_student_token()`, `action_send_by_email()`,
  `action_complete_signature()` y `action_complete_student_signature()` cubren
  HomeClass sin más cambios. El controlador no se tocó porque ya enruta por
  `_is_especifico()` en las cinco rutas.
- **`selection_add` y `ondelete` coherentes.** `:19-28` añaden el valor y su
  `set default`; al desinstalar el módulo los HomeClass caen al
  `marco_nacional` que `irg_practice_agreement_types` declara como default.
- **Wizard con las tres opciones.**
  `wizard/practice_agreement_specific_create_wizard.py:39-46` lista los tres
  valores con `required=True` y `default='especifico_internacional'`. La vista
  `wizard/practice_agreement_specific_create_wizard_views.xml:10` ya renderiza
  el campo con `widget="radio"`, de modo que el radio muestra las tres opciones
  sin tocar la vista.
- **Report: el `div.page` marco se oculta para los tres específicos.**
  `report/practice_agreement_report_templates.xml:6` pasa a
  `doc.agreement_type not in ('especifico_internacional', 'especifico_nacional', 'especifico_homeclass_sincronas')`,
  y `:21-26` insertan un `div.page` hermano con `t-call` a
  `agreement_document_especifico_homeclass_sincronas` más
  `agreement_especifico_signatures`. Los tres `t-if` de página son mutuamente
  excluyentes; no hay solape con el marco.
- **Predicados alineados Python/QWeb** conforme a
  `irg_selection_qweb_predicate_alignment.md`. Un `grep` de
  `especifico_homeclass_sincronas` sobre el módulo lo encuentra el mismo día en
  modelo (`ESPECIFICO_TYPES` + `selection_add`), report (`:6`, `:21`), portal
  centro (`:7`, `:12`, `:15`, `:18`, `:34`) y alumno (`:127`), y `attrs` del
  formulario (`views/practice_agreement_views.xml:10,34`). No queda ningún
  predicado de dos valores (`internacional`, `nacional`) sin el tercero.
- **Sin `hasattr` en QWeb** (`irg_qweb_hasattr_unsafe.md`): `grep -n hasattr`
  sobre el módulo no devuelve nada.
- **`print_report_name` defensivo** (`irg_report_print_name_foreign_xmlid.md`):
  `report/practice_agreement_report_templates.xml:78` tiene las cinco salidas
  (3 específicos + 2 marcos). Las cuatro condiciones que leen
  `object.agreement_type` repiten `'agreement_type' in object._fields`;
  `Marco_Nacional` sigue siendo la caída final, que no accede al campo. El
  slug de descarga bajo demanda es `Especifico_Homeclass_Sincronas`.
- **Filename `Homeclass_Sincronas`.**
  `models/practice_agreement.py:191-194`: rama explícita para
  `especifico_homeclass_sincronas` →
  `Convenio_Especifico_Homeclass_Sincronas_<alumno>_<centro>_<id>.pdf`. El test
  de doble firma afirma ese token y niega `Marco`.
- **Plantilla HomeClass según decisiones de producto.**
  `views/agreement_document_especifico_homeclass_sincronas.xml`:
  - PRIMERA (`:35-36`): modalidad sincrónica online en tiempo real por
    plataformas digitales; no hay `doc.street` / `doc.city` / `doc.zip`.
  - SEGUNDA (`:46`): supervisión virtual por encuentros sincrónicos.
  - TERCERA (`:51-60`): puntualidad en sesiones sincrónicas, plataforma, no
    grabar, confidencialidad digital.
  - CUARTA (`:74-76`): difusión del centro, talleres a usuarios y guías
    psicoeducativas genéricas. Actividades propuestas solo con
    `t-if="doc.student_proposed_activities"` (`:77`).
  - Sin QUINTA: CUARTA → SEXTA (`:82`) → SÉPTIMA (`:87`).
  - SÉPTIMA (`:88-98`): prácticas no remuneradas; el centro puede cobrar a
    pacientes (gratuita / bonificada / estándar); esos importes no son
    remuneración del alumno.
  - Normativa (`:130`, `:139`): ley 26/2015 y Zoom.
- **Genérico y sin PII del ejemplo.** `grep` de `FUPPEMM|Luz Mary|INMIRA|Área
  de Psicología` sobre el módulo solo encuentra las aserciones negativas del
  test. El documento usa campos (`student_name`, `student_vat`,
  `center_official_name`, `tutor_name`, …) con placeholders de reserva. El
  test HTML niega también `Carrer Provença` (calle del fixture) y
  `fuera de España`.
- **HTML internacional no se contamina.**
  `test_html_internacional_keeps_abroad_insurance` (`:262`) sigue exigiendo
  `fuera de España` y la ausencia de `26/2015` en el internacional. El QUINTA
  «a cargo de iRG» permanece solo en nacional (`agreement_document_especifico_nacional.xml:90-92`)
  e internacional (con «fuera de España»).
- **MRO intacto.** `specific` sigue delante de `types`; para los específicos
  `action_complete_signature` no llama a `super()`, así que el renombrado a
  `Convenio_Marco_*` de `irg_practice_agreement_types:32-54` no se ejecuta
  sobre un HomeClass. La firma del centro sola no pone `state = 'completed'`.
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
  `tests/test_practice_agreement_specific.py` añade
  `test_wizard_creates_homeclass` (`:285`),
  `test_html_homeclass_sync_online_no_quinta` (`:296`: sincrónica, tiempo
  real, plataformas digitales, no grabar, cobrar a los pacientes, 26/2015,
  guías psicoeducativas, niega QUINTA iRG / fuera de España / PII / dirección
  del fixture) y `test_homeclass_both_signatures_complete` (`:319`: el centro
  solo no completa; ambas sí; adjunto `Homeclass_Sincronas`, no `Marco`).
  `:120` fija el valor en la selección.
  `test_marco_still_completes_with_center_only` (`:338`) y el HTML
  internacional con «fuera de España» protegen la no regresión.

## Hallazgos abiertos

### BLOQUEANTE

Ninguno.

### IMPORTANTE

**I1 — Las tres plantillas específicas duplican el clausulado compartido y
pueden divergir en silencio.**
`views/agreement_document_especifico_homeclass_sincronas.xml` frente a
nacional e internacional. SEXTA, el encabezado, el preámbulo y casi toda la
Normativa (inasistencia, visados, prácticas presenciales, abandono del
centro, Zoom) son texto legal copiado. La misión ya factorizó las firmas
(`agreement_especifico_signatures`) y las cláusulas propias de HomeClass
(PRIMERA, TERCERA online, CUARTA de difusión, SÉPTIMA económica, ausencia de
QUINTA) sí divergen, pero la Normativa se copió entera del nacional. A partir
de ahora cualquier corrección normativa hay que aplicarla tres veces y ningún
test detecta la divergencia. Sugerencia: extraer los párrafos realmente
comunes a `t-call` y dejar en cada documento solo lo que diverge. No es
bloqueante porque hoy el contenido cumple los criterios de aceptación; es
deuda de mantenimiento con impacto en un documento legal, agravada al pasar
de dos variantes a tres.

### MENOR

**M1 — Encabezado del documento HomeClass gramaticalmente incompleto.**
`views/agreement_document_especifico_homeclass_sincronas.xml:5-9`. El `h3`
termina en «… PARA LA REALIZACIÓN DE PRÁCTICAS DE FORMACIÓN y <centro>», sin
nombrar a la primera parte, de modo que el PDF imprime literalmente «…DE
FORMACIÓN y Centro Colaborador Test S.L.». Falta el «ENTRE INSTITUTO RAIMON
GAJA (iRG)» antes de la «y». El defecto viene heredado de nacional e
internacional, pero aquí es un fichero nuevo y es texto de portada de un
convenio firmado. Corrección: insertar la parte iRG en el encabezado (y
valorar arreglar las otras dos en una misión aparte).

**M2 — La Normativa HomeClass conserva párrafos de contexto presencial e
internacional.**
`agreement_document_especifico_homeclass_sincronas.xml:115-116` («no se
garantiza la práctica presencial»), `:124` (alojamiento, transporte hasta la
ciudad, **visados**) y `:133` («el estudiante de prácticas presenciales se
acogerá a los horarios»). Chocan con la PRIMERA de este mismo documento
(sincrónica online, sin dirección física), que es la razón de ser de la
variante. Corrección: recortar o reescribir esos tres párrafos para la
modalidad online, o confirmar con el usuario que el anexo del ejemplo debe
reproducirse tal cual.

**M3 — Nombre del adjunto y `print_report_name` siguen usando criterios
distintos (arrastre, ahora en tres variantes).**
`models/practice_agreement.py:189-201` produce
`Convenio_Especifico_Homeclass_Sincronas_<alumno>_<centro>_<id>.pdf`, mientras
`report/practice_agreement_report_templates.xml:78` produce
`Convenio_Especifico_Homeclass_Sincronas_<centro>_<referencia>`. El PDF
archivado y la descarga bajo demanda desde backend siguen sin coincidir. Unificar
el criterio en un único método del modelo invocado también desde
`print_report_name`.

**M4 — `print_report_name` de `irg_practice_agreement_specific` puede
revertirse a la expresión de `types` (arrastre agravado).**
`report/practice_agreement_report_templates.xml:77-78`. Los dos módulos
sobrescriben el mismo `ir.actions.report` ajeno y gana el último cargado. En
instalación y en `-u all` gana `specific`, pero un
`-u irg_practice_agreement_types` aislado devuelve la expresión de dos ramas
y un HomeClass se imprimiría como `Convenio_Marco_Nacional_…`. Con tres
específicos el escenario es más probable. Misma sugerencia que M3: un único
punto de verdad en el modelo.

**M5 — El tipo «Convenio Específico HomeClass Síncronas» vuelve a ser
alcanzable desde el formulario de `irg_practice_agreement_types` sin pasar
por el wizard.**
`models/practice_agreement.py:22` reintroduce el valor en la selección, y
`irg_practice_agreement_types/views/practice_agreement_views.xml:10,23,34`
muestra `agreement_type` en formulario, lista y agrupación. Un usuario del
backend puede crear un HomeClass a mano sin solicitud, sin alumno y sin email
de estudiante; el documento se renderiza con placeholders y el convenio queda
atascado a la espera de una firma de alumno que nadie puede solicitar
(`action_send_by_email` exige `student_email`). No es bloqueante porque el
comportamiento es idéntico al de los otros dos específicos, ya aceptado, y
porque las cuatro capas están alineadas (el documento generado es el
HomeClass, no un marco mal etiquetado). Sugerencia: una `@api.constrains` o
un dominio que exija `practice_request_id` cuando
`agreement_type in ESPECIFICO_TYPES`.

### NIT

- `models/practice_agreement.py:191-196`: el `slug` usa `if nacional / elif
  homeclass / else Internacional`. Hoy es seguro porque el método solo se
  invoca desde `_finalize_especifico_pdf()`, pero el `else` implícito
  etiquetaría «Internacional» cualquier tipo futuro. Un `dict` explícito por
  tipo sería más fiel al criterio de predicado explícito del proyecto.
- `report/practice_agreement_report_templates.xml:78`: la expresión repite
  cuatro veces `'agreement_type' in object._fields` en una sola línea. Se
  puede evaluar la guarda una vez o delegar en un método del modelo. La quinta
  salida (`Marco_Nacional`) no lee el campo; el patrón es el mismo que ya se
  aceptó en la variante nacional.
- `views/portal_agreement_templates.xml:124-132`: la página del alumno ahora
  distingue nacional y HomeClass con `t-if` / `t-elif`, pero el internacional
  sigue en `t-else`. Hoy es inalcanzable para un marco (solo los específicos
  tienen `student_access_token`), pero el `t-else` como cajón de sastre rompe
  el patrón de predicados explícitos.
- `tests/test_practice_agreement_specific.py:114`: el test se sigue llamando
  `test_agreement_type_includes_especifico_internacional` cuando ahora afirma
  los tres específicos. Renombrarlo a `..._includes_especificos`.
- `tests/test_practice_agreement_specific.py`: no hay aserción sobre la
  selección ni el default del wizard (tres valores, radio). El comportamiento
  queda cubierto de forma indirecta por `test_wizard_creates_homeclass`.
- El HTML HomeClass sí cita Zoom (`:139`) y las tres tarifas de SÉPTIMA, pero
  el test no las fija; solo exige `26/2015` y `cobrar a los pacientes`. Un
  `assertIn("Zoom")` y `assertNotIn("QUINTA")` anclarían las decisiones de
  producto con el mismo rigor que el resto del criterio HTML.

## Nota fuera del alcance de esta review

`addons-extra/extrairg/irg_practice_agreement_specific/README.md:3-5` y `:21-22`
siguen describiendo un radio de dos opciones (Internacional o Nacional) y no
mencionan HomeClass. Es documentación, así que no cuenta como hallazgo de
código y no afecta al veredicto, pero conviene que el documentador lo corrija
junto con la versión del manifiesto.

`.gitignore` aparece modificado en el working tree; no forma parte de esta
misión y no se ha revisado.

## Recordatorio de gates posteriores

El diff toca `views/`, `report/` y plantillas de portal, así que el disparo por
scope de la capa E2E (`e2e_testsprite`) declarado en `01-plan.md` es obligatorio
y no puede registrarse como `skipped`. Esta review no lo sustituye ni ejecuta
ninguna prueba.

## Veredicto

REVIEW OK
