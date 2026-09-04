# Review de código (re-review) — irg-diplomado-class-start-date

Revisor independiente (no codificador). Fase Review de AGENTS.md: se revisa
únicamente código y elementos funcionales asociados (pruebas, seguridad, datos,
runtime). No se revisan `plan.md`, `execution.md`, `verification.json` ni
documentación.

Segunda ronda, posterior al `REVIEW FAIL` anterior.

Alcance revisado:

- `addons-extra/extrairg/irg_generacion_diplomados_class_start_date/` (addon completo)
- Fixtures y aserciones de `irg_diplomado_portal_request/tests/test_portal.py` y
  `irg_campus_diplomados_portal/tests/test_portal.py` (compatibilidad)
- Controladores padre de ambos portales, `irg_generacion_diplomados_website_verify`,
  `irg_generacion_diplomados` (modelo y asistente)
- Spec `docs/superpowers/specs/2026-09-04-irg-diplomado-class-start-date-design.md`
- Condiciones vinculantes de `artifacts/security-advisor.txt`
- Evidencia `artifacts/green-tests.txt` y `artifacts/dependency-portal-tests.txt`

Base: worktree actual, addon sin commitear. Ningún módulo existente ha sido
modificado.

---

## Resumen

Los dos hallazgos bloqueantes están cerrados y los tres menores señalados
también. El addon sigue siendo *inherit-only*, no toca módulos existentes y
cumple las siete condiciones vinculantes del Security Advisor, ahora con
cobertura sobre la ruta que motivó la condición 6.

Queda una decisión de producto que hay que dejar por escrito: para resolver la
regresión de compatibilidad, el codificador ha estrechado la semántica de
«reimprimir siempre en cada descarga» a «reimprimir solo si falta el PDF o la
`start_date` almacenada está desfasada». Es más segura y cumple los criterios de
aceptación de la spec para los flujos reales, pero contradice literalmente la
Decisión 3 del diseño. No lo bloqueo, y explico por qué en MENOR-1.

---

## Verificación de los hallazgos anteriores

### BLOQUEANTE-1 — Cerrado

`_irg_should_refresh_on_download` (`models/diplomado_registry.py:41-53`) devuelve
`True` solo si no hay adjunto con bytes, o si `start_date` está informada **y**
difiere de la fecha viva del lote. He comprobado los fixtures de los dos módulos
dependientes en lugar de fiarme del razonamiento:

- `irg_diplomado_portal_request/tests/test_portal.py:235-250` crea el registro con
  `issue_date` y `attachment_id`, **sin** `start_date`. El helper devuelve `False`,
  no se llama al `action_reprint` mockeado y la respuesta sigue siendo
  `b'DIPLOMADO_PORTAL_PDF'`.
- `irg_campus_diplomados_portal/tests/test_portal.py:230-250, 287` crea
  `diplomado_ok` y `diplomado_fail` igualmente sin `start_date`, compartiendo
  `cls.test_attachment`. No hay reprint, no se sobrescribe el adjunto compartido y
  la respuesta sigue siendo `b'PDF_TEST_CONTENT'`.
- El otro caso, `test_portal.py:204-206`, sí espera regeneración: el registro se
  crea en la propia petición y no tiene adjunto, así que el helper devuelve `True`
  y el mock produce `b'DIPLOMADO_DIRECT_DOWNLOAD_PDF'`, igual que en la línea base.

`action_reprint` del personal (`models/diplomado_registry.py:85-104`) sigue
regenerando siempre, sin `super()` y sin retorno anticipado, como exige la
condición 4. Ningún módulo existente ha sido editado.

También he verificado la causa por la que esas dos suites no se pueden ejecutar
en esta base: `op.course.lang` es `required=True` en
`addons-extra/addons_uisep/isep_elearning_custom/models/op_course.py:25`, y los
fixtures de ambos módulos crean `op.course` sin `lang`
(`irg_diplomado_portal_request/tests/test_portal.py:72`,
`irg_campus_diplomados_portal/tests/test_portal.py:74`). El error de
`setUpClass` en `artifacts/dependency-portal-tests.txt` es previo e independiente
de esta misión; esas suites ya estaban en rojo antes del cambio. Ver MENOR-2 para
el tratamiento en Validación.

### BLOQUEANTE-2 — Cerrado

`tests/test_class_start_date.py:419-461` añade los tres casos HTTP contra
`/campus/certificates/download/diplomado/<id>`, que es la única ruta donde el
addon escribe su propia autorización:

1. Propietario elegible: `start_date` pasa a `2026-03-15`, `attachment_id` es el
   mismo registro y los bytes cambian.
2. Partner ajeno: 303 a `/campus/certificates`, `start_date` y bytes intactos.
3. Nota 7.0 (frontera de `> 7.0`): 303 con `error=grade_too_low`, sin mutación.

Lo importante es que los dos negativos sí protegen el orden: si el
`action_reprint()` de `controllers/portal.py:62-70` subiera por encima del gate de
`controllers/portal.py:53-61`, habría mutación y ambas aserciones se pondrían en
rojo. Eso era exactamente lo que faltaba. El log de `artifacts/green-tests.txt`
confirma los tres códigos de estado y las dos redirecciones reales.

### MENOR-1 anterior (orden render/escritura) — Cerrado

`action_reprint` resuelve la fecha, renderiza y solo después escribe `start_date`
y el adjunto (`models/diplomado_registry.py:87-99`).
`test_reprint_render_failure_keeps_start_date_and_pdf` lo fija. Como efecto
lateral positivo, el fallo de render ya no deja la fecha adelantada al PDF, y
además el registro se autocura: al no escribirse `start_date`, la descarga
siguiente vuelve a detectar el desfase y reintenta.

### MENOR-2 anterior (duplicación del gate campus) — Rebajado a NIT

`controllers/portal.py:50-52` deja constancia explícita de que la copia es
deliberada y debe seguir al padre. Era la corrección mínima que propuse. Sigue
siendo una copia que puede divergir, así que queda como NIT-1.

### MENOR-3 anterior (resolución de lote) — Cerrado con matiz

`_irg_wizard_batch` usa ahora `candidates.sorted('id', reverse=True)[:1]`
(`wizard/diplomado_wizard.py:17`), coherente con el `order='id desc'` del modelo
(`models/diplomado_registry.py:21`). Queda el matiz de MENOR-3 más abajo.

### NIT-1 anterior (fecha vacía en el asistente) — Cerrado

`wizard/diplomado_wizard.py:28-29` solo asigna si `new_date` es verdadero.

---

## Hallazgos de esta ronda

### MENOR-1 — La semántica implementada contradice la Decisión 3 de la spec

**Archivos:** `models/diplomado_registry.py:41-53`, `controllers/portal.py:31-32`
y `controllers/portal.py:63-64`.

La spec dice en la Decisión 3: «on every backend reprint and every portal
download, sync `registry.start_date` from the live batch and regenerate the PDF»,
y la tabla de componentes repite «always call `action_reprint` before sending the
file» para los dos controladores. El código regenera de forma condicional.

No lo bloqueo por tres razones concretas:

1. El criterio de aceptación sigue cumpliéndose. «Changing `date_start_class` on
   the batch and downloading again prints the new class start date» se satisface
   porque los diplomas reales llevan `start_date` informada (el asistente la
   rellena por onchange y el portal dedicado la escribe al crear el registro), de
   modo que el desfase se detecta y se regenera.
2. Reduce la superficie de mutación de un documento ya emitido, que era
   precisamente la preocupación que disparó la revisión de seguridad. Ninguna de
   las siete condiciones vinculantes del apartado 8 del Advisor exige el «always»;
   aparece en la descripción del alcance, no en el gate.
3. La alternativa era editar aserciones de dos módulos existentes, que es lo que
   el modding rule prohíbe y lo que yo mismo marqué como fuera de alcance sin
   aprobación del orquestador.

**Acción requerida, no bloqueante.** En Documentación hay que actualizar la
Decisión 3 y la tabla de componentes de la spec para que describan la regla real
(«regenerar si falta el PDF o si la `start_date` almacenada difiere de la fecha
viva del lote»), y el orquestador debe confirmar con el propietario que esa es la
semántica de producto deseada. Si el propietario exige el «always» literal, esto
pasa a ser rework de Implementación y arrastra la decisión sobre las aserciones de
los dos módulos dependientes.

### MENOR-2 — La compatibilidad con las suites dependientes está establecida por lectura, no por ejecución

**Archivo de evidencia:** `artifacts/dependency-portal-tests.txt`.

Las dos suites abortan en `setUpClass` por el `op.course.lang` requerido descrito
arriba, así que ninguna llega a las aserciones que este cambio tenía que
preservar. El razonamiento de compatibilidad es sólido y lo he verificado sobre
los fixtures, pero es estático.

**Corrección.** El validador debe registrar este check como `skipped` con la
justificación objetiva (fixture gap previo, ajeno al diff, con traza en el
artefacto) en lugar de darlo por `pass`, y dejar constancia de que
`test_download_refresh_only_when_stored_start_is_stale`
(`tests/test_class_start_date.py:160-183`) es la cobertura sustitutiva. Si es
barato, ejecutar esas dos suites en una base donde sus fixtures sí creen el curso
cerraría el hueco del todo. No reabre Implementación: es tratamiento de evidencia.

### MENOR-3 — Un registro con `start_date` vacía nunca se sincroniza en la descarga

**Archivo:** `models/diplomado_registry.py:41-53`.

`start_date` no es un campo obligatorio en `irg.diplomado.registry`
(`irg_generacion_diplomados/models/diplomado_registry.py:42-45`). Un registro con
la fecha vacía y un PDF ya guardado no se regenera nunca por descarga: imprimirá
la celebración en blanco de forma indefinida hasta que alguien pulse Reimprimir en
el backend. Es un caso estrecho —el asistente y el portal dedicado siempre
informan la fecha— pero es exactamente el caso que la regla nueva sacrifica para
mantener la compatibilidad, así que conviene que sea una decisión consciente y no
un efecto colateral.

**Corrección.** Elegir explícitamente entre las dos opciones y documentarla:
tratar «vacía + lote resoluble» también como desfase, asumiendo entonces el
conflicto con los fixtures de los dos módulos dependientes; o dejarlo como está y
anotar la limitación en la spec y en el changelog, indicando que esos registros se
corrigen con el botón Reimprimir. La segunda opción es coherente con MENOR-1.

### MENOR-4 — El asistente puede quedar con `start_date` posterior a `end_date`

**Archivos:** `wizard/diplomado_wizard.py:8-18` frente a
`irg_generacion_diplomados/wizard/diplomado_wizard.py:72-79`.

El asistente base toma `finished_courses[0]` (primer elemento, orden por defecto)
para fijar `course_id` y `end_date`; el override toma la matrícula finalizada
**más reciente** de ese mismo curso para la fecha de inicio. Para un alumno
rematriculado en el mismo curso con dos lotes finalizados, el diploma puede
mostrar el inicio del lote nuevo y el fin del lote viejo, incluso con inicio
posterior al fin.

La incoherencia es inherente a la Decisión 4 de la spec, que congela `end_date` y
solo resincroniza `start_date`, así que no es un defecto introducido por el
codificador. Aun así es visible en el documento impreso.

**Corrección.** Documentar la limitación con el caso concreto, o resolver el lote
una sola vez y usarlo para ambas fechas en la creación (nunca en la
resincronización, que la spec limita a `start_date`).

### NIT-1 — El gate del campus sigue siendo una copia del padre

`controllers/portal.py:53-61` duplica `irg_campus_diplomados_portal/controllers/portal.py:198-208`.
El comentario nuevo mitiga el riesgo, pero si el padre endurece su regla, el gate
que protege la **mutación** se quedará más laxo que el que protege la descarga.
Extraer un helper en el padre sigue siendo lo correcto cuando se pueda tocar ese
módulo.

### NIT-2 — Trato desigual del fallo de render entre las dos rutas

`controllers/portal.py:33-40` devuelve `?error=no_pdf` y no sirve el PDF anterior;
`controllers/portal.py:65-70` registra el error y deja que el padre sirva el PDF
anterior. Ambos comportamientos están sancionados por la spec (líneas 144-145) y
por el apartado 4 del Advisor, así que no es un hallazgo de cumplimiento; solo
conviene saber que en el portal dedicado un fallo de ReportLab deja al alumno sin
descargar un diploma que sí existe en base.

### NIT-3 — El docstring justifica la regla con los tests, no con el producto

`models/diplomado_registry.py:44-48` explica la decisión diciendo «That matches
historical portal tests». La regla es de producto; conviene redactarla como tal
(«un registro sin fecha almacenada no se resincroniza por descarga») y dejar la
compatibilidad con las suites para `execution.md`.

### NIT-4 — Higiene de fixtures en el `HttpCase` (sin cambios)

`tests/test_class_start_date.py:311` hace `cr.commit()` y `tearDownClass` solo
restaura el monkeypatch. La limpieza defensiva de arranque (líneas 210-232) hace
el test reejecutable y es la convención vigente en los dos portales, así que sigo
sin bloquearlo. Un `addClassCleanup` que borre y confirme sería lo correcto según
AGENTS.md.

---

## Condiciones del Security Advisor

| # | Condición | Estado |
| --- | --- | --- |
| 1 | Campus: partner + nota antes del reprint (segunda variante) | Cumple (`controllers/portal.py:46-70`), **ahora con tres tests** |
| 2 | Portal dedicado: reprint solo en `_send_diplomado_file`; rutas republicadas con `@http.route()` vacío | Cumple (`controllers/portal.py:14-20`, `30-41`) |
| 3 | Sin sudo nuevo en modelos, sin rutas públicas, sin ACL de portal, helpers `_irg_*` privados | Cumple |
| 4 | `action_reprint` usa `_get_diplomado_pdf_data()`, sin `super()`, fail-closed, solo adjunto propio | Cumple (`models/diplomado_registry.py:85-104`) |
| 5 | Sin hook en `op.batch`, sin reescritura masiva, sin `unlink`, sin tocar issue/end date ni payload de `/verificar` | Cumple |
| 6 | Tests negativos: partner ajeno y nota insuficiente no mutan `start_date` ni bytes | Cumple en las dos rutas (4 casos negativos) |
| 7 | `'app.gradebook.student' in self.env`, no `env.get` | Cumple (`models/diplomado_registry.py:26`) |

La reducción de la frecuencia de regeneración descrita en MENOR-1 no debilita
ninguna de estas condiciones: mutar menos un documento emitido va en la dirección
que pedía el Advisor, así que no considero que reabra su revisión.

---

## Lo que está bien y conviene no tocar

- Addon nuevo bajo `addons-extra/extrairg/`, `auto_install: False`, sin `data`,
  sin ACL, sin modelos ni rutas nuevas. Cero ediciones en módulos existentes.
- `depends` incluye `irg_generacion_diplomados_website_verify`, de modo que este
  `action_reprint` gana el MRO y puede usar `_get_diplomado_pdf_data()` sin
  `super()`, como exige la condición 4. El log de carga confirma que el módulo
  entra último (244/244).
- `_irg_attachment_belongs_to_registry` comprueba `res_model` y `res_id`, crea un
  adjunto nuevo cuando el existente es ajeno y nunca hace `unlink()`.
- Render antes de cualquier escritura, con test explícito del fallo de render.
- Resolución de lote acotada a `student_id` + `course_id`, con `id desc` coherente
  entre modelo y asistente, y sin cambiar `start_date` cuando no hay lote.
- SQL crudo solo en un test y parametrizado; nada en métodos de producción.

---

## Veredicto

No hay hallazgos bloqueantes abiertos. Los dos anteriores están cerrados y
verificados contra los fixtures reales de los módulos dependientes, y la única
autorización server-side que escribe el addon tiene ya test positivo y dos
negativos que fijan el orden del gate. Los cuatro hallazgos menores son de
documentación, tratamiento de evidencia y limitaciones a declarar; ninguno exige
cambiar código antes de validar. Pasa a Validación, con la advertencia de MENOR-2
sobre cómo debe registrarse el check de las suites dependientes y con MENOR-1
pendiente de confirmación del propietario en Documentación.

REVIEW PASS
