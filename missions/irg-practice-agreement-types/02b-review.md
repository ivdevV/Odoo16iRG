# Review de código — irg_practice_agreement_types

Alcance revisado: código funcional del módulo nuevo `addons-extra/extrairg/irg_practice_agreement_types`
(modelos, wizard, vistas, QWeb, seguridad y tests) y lectura de
`addons-extra/extrairg/irg_practice_agreement_sign` solo como referencia de lo heredado.
No se revisan `01-plan.md`, `execution.md`, `verification.json`, changelog ni knowledge.

## Verificación de criterios

| # | Criterio | Estado | Evidencia |
| --- | --- | --- | --- |
| 1 | Botón "Crear Convenio" abre wizard con radio Nacional/Internacional | OK | `views/practice_center_views.xml` reetiqueta el botón heredado a `action_open_create_agreement_wizard`; `wizard/practice_agreement_create_wizard_views.xml` usa `widget="radio"` |
| 2 | `agreement_type` persistido y legacy sigue nacional | OK | `models/practice_agreement.py` (Selection `store`, `index`, `tracking`, `default='marco_nacional'`); `action_create_agreement` de `practice.center` no se modifica y hereda el default |
| 3 | PDF nacional sin LATAM/4.3; internacional con 4.3 y sin INMIRA | OK | `report/practice_agreement_report_templates.xml` conmuta el `div` de CLÁUSULAS por `t-if`; `INMIRA` no aparece en ninguna plantilla del árbol |
| 4 | Sin `hasattr` en QWeb | OK | `rg hasattr` sobre el módulo: sin coincidencias |
| 5 | ACL del wizard | OK | `security/ir.model.access.csv` cubre el modelo transitorio para `group_practice_agreement_user` y `group_practice_agreement_manager`, ambos existentes en el módulo base |
| 6 | No editar módulos existentes | OK a nivel de ficheros | `git status` solo muestra el directorio nuevo como untracked; el módulo `irg_practice_agreement_sign` no tiene modificaciones (ver MENOR-1 sobre sobrescritura de un registro ajeno) |

Los xpath de herencia resuelven de forma unívoca contra el módulo base
(`//h4[contains(., 'CLÁUSULAS')]/parent::div`, `//h6[...]`, `//div[hasclass('oe_title')]`,
`//field[@name='name']`, `//filter[@name='group_by_state']`), y `doc` / `agreement` están en
contexto en cada plantilla donde se usan. La plantilla internacional es texto estático, por lo que
el `t-call` no necesita contexto adicional. El override de `action_complete_signature` se ejecuta
siempre en `sudo()` desde el controlador portal, así que el renombrado de adjuntos no puede
provocar `AccessError`.

## Hallazgos

### BLOQUEANTE

Ninguno.

### MENOR

**MENOR-1 — Sobrescritura de `ir.actions.report` propiedad del módulo base.**
`report/practice_agreement_report_templates.xml` reescribe
`irg_practice_agreement_sign.action_report_practice_agreement.print_report_name`. El `xml_id`
sigue perteneciendo al módulo base, con dos consecuencias reales: (a) al actualizar solo
`irg_practice_agreement_sign` el valor vuelve al original y el nombre del PDF internacional se
degrada en silencio; (b) al desinstalar `irg_practice_agreement_types` el override **no** se
revierte y la expresión queda referenciando `object.agreement_type`, campo ya eliminado, con lo
que imprimir cualquier convenio lanzaría `AttributeError`.
Corrección: hacer la expresión defensiva, por ejemplo evaluando
`object.agreement_type if 'agreement_type' in object._fields else False`, o mover la lógica de
nombre a un método Python del modelo y dejar el registro del módulo base intacto.

**MENOR-2 — `agreement_type` sin control server-side de integridad tras la firma.**
`views/practice_agreement_views.xml` solo protege el campo con
`attrs="{'readonly': [('state', 'in', ['sent','completed','cancelled'])]}"`. Un `write` por RPC
puede cambiar el tipo de un convenio ya firmado: el PDF archivado conservaría las cláusulas
nacionales mientras el portal (que renderiza en vivo desde el registro, también en estado
`completed`) mostraría las internacionales. Es divergencia documental sobre un documento con
valor legal.
Corrección: añadir un `write` override o `@api.constrains` en
`models/practice_agreement.py` que impida modificar `agreement_type` cuando
`state == 'completed'`. Se reconoce que el módulo base expone los mismos campos con la misma
laxitud, pero `agreement_type` es el que conmuta el cuerpo de cláusulas.

**MENOR-3 — Renombrado de adjuntos por reconstrucción de cadena.**
`models/practice_agreement.py` recompone `old_name` replicando el formato exacto del `filename`
del módulo base para localizar el adjunto del centro. Si el base cambia ese formato, el
renombrado pasa a ser un no-op silencioso. Además el `search(..., limit=1)` renombraría solo uno
si hubiera varios adjuntos coincidentes.
Corrección: comentar la dependencia explícita del formato del base, o buscar el adjunto del
centro por `res_model`/`res_id` y sufijo (`name like '%_' || id || '.pdf'`) en lugar del nombre
completo.

**MENOR-4 — Estilo de la plantilla internacional en el portal.**
`views/agreement_clauses_internacional.xml` usa estilos inline pensados para PDF (`font-size:
11.5pt`, márgenes en px) y se reutiliza tal cual en el portal, que es Bootstrap
(`text-justify`, `mb-3`, `font-weight-bold`). El convenio internacional se verá tipográficamente
distinto al nacional en la página que firma el centro.
Corrección: separar la variante portal o migrar el fragmento a clases Bootstrap equivalentes.

**MENOR-5 — Duplicación del cuerpo de cláusulas.**
Las cláusulas 1-3 y 5-9 de la plantilla internacional replican el texto del módulo base con
variaciones menores de redacción. Editar el nacional no propagará al internacional.
Corrección aceptable: dejarlo documentado como decisión (los textos divergen de forma
intencionada) o extraer las cláusulas comunes a un fragmento compartido.

**MENOR-6 — Aserción débil en el test de la ruta legacy.**
`tests/test_practice_agreement_types.py:75` usa
`assertNotEqual(agreement.agreement_type, "marco_internacional")`, que también pasaría si el
campo quedase en `False`. Debería ser `assertEqual(..., "marco_nacional")` para cubrir de verdad
el criterio 2.

### NIT

- `wizard/practice_agreement_create_wizard_views.xml:23` define
  `action_practice_agreement_create_wizard`, que nunca se usa: el botón del centro devuelve el
  diccionario de acción directamente desde `models/practice_center.py`. Código muerto.
- `views/agreement_clauses_internacional.xml` es un fragmento de report/portal, no una vista;
  encajaría mejor en `report/` por coherencia con el módulo base.
- `views/portal_agreement_templates.xml:10` hace `t-set doc = agreement` pero la plantilla
  llamada no usa `doc`. Se puede eliminar.
- `wizard/practice_agreement_create_wizard_views.xml:9` deja `practice_center_id` con
  `invisible="1"`; mostrarlo en solo lectura daría contexto al usuario sobre qué centro va a
  recibir el convenio.

## Notas de seguridad

- Sin secretos ni credenciales en el módulo. No se toca ninguna zona sensible de `PROJECT.md`
  (`etc/`, `docker*`, pagos, integraciones, migraciones).
- El wizard no usa `sudo()`; la creación de `practice.agreement` pasa por la ACL del módulo base.
  El modelo transitorio queda además restringido a su creador por el propio Odoo.
- Sin inputs de usuario sin validar, sin f-strings en SQL, sin dependencias nuevas.
- `__pycache__/` presente en el directorio del módulo, pero cubierto por `.gitignore:23`.

## Veredicto ronda 1

Tests GREEN confirmados en `artifacts/green-tests.txt`: `0 failed, 0 error(s) of 6 tests`.
No hay hallazgos BLOQUEANTES; los seis criterios de la misión se cumplen. MENOR-1 y MENOR-2
deberían atenderse antes de considerar el módulo estable en producción, pero no impiden avanzar
a Validación.

REVIEW OK

---

# Ronda 2 — re-revisión del delta funcional

Alcance de esta ronda: exclusivamente los dos cambios posteriores a la ronda 1
(`models/practice_agreement.py` y `report/practice_agreement_report_templates.xml`) más el test
nuevo. No se revisan `01-plan.md`, `execution.md` ni changelog. Se releyó
`irg_practice_agreement_sign/models/practice_agreement.py`,
`.../views/practice_agreement_views.xml` y `.../report/practice_agreement_report.xml` como
referencia del comportamiento heredado.

GREEN de esta ronda: `artifacts/green-tests.txt` → `0 failed, 0 error(s) of 7 tests`
(los 7 métodos del fichero de tests están en el log, incluido
`test_cannot_change_type_after_sent`).

## Estado de los hallazgos previos

**MENOR-2 — RESUELTO.** `models/practice_agreement.py:21-30` añade el `write()` override que
faltaba. Verificaciones hechas:

- Es batch-safe: usa `self.filtered(...)` en vez de `ensure_one()` y devuelve `super().write(vals)`.
- No rompe ningún flujo heredado: ni `action_send_by_email` (`state: 'sent'`) ni
  `action_complete_signature` (`state: 'completed'` + campos de firma) del módulo base escriben
  `agreement_type`, así que la guarda nunca se dispara en el camino normal de firma.
- El bloqueo es más amplio que lo recomendado (`sent`/`completed`/`cancelled` en vez de solo
  `completed`) y esa ampliación es correcta: el portal renderiza el convenio en vivo desde el
  registro, así que cambiar el tipo con el enlace ya enviado alteraría las cláusulas bajo los pies
  del firmante.
- `UserError` y `_()` importados correctamente; el mensaje se traduce.

**MENOR-1 — PARCIALMENTE RESUELTO.** La expresión defensiva de
`report/practice_agreement_report_templates.xml:17` cierra el escenario grave: al desinstalar
`irg_practice_agreement_types`, el `ir.model.data` del `xml_id` sigue perteneciendo al módulo base
(escribir un `xml_id` ajeno no transfiere la propiedad del registro), el valor sobrescrito
permanece y ahora evalúa a `'Nacional'` en lugar de reventar con `AttributeError`. El comentario
que documenta el porqué es adecuado.
Sigue abierto el sub-caso (a): `report/practice_agreement_report.xml:3` del módulo base **no**
está dentro de un bloque `noupdate="1"`, por lo que un `-u irg_practice_agreement_sign` en
solitario revierte el `print_report_name` al original y el PDF internacional vuelve a nombrarse
como nacional, en silencio. Se mantiene como MENOR.

**MENOR-3, MENOR-4, MENOR-5, MENOR-6 y los NIT** de la ronda 1 siguen abiertos sin cambios; no
formaban parte de este delta.

## Hallazgos nuevos de la ronda 2

### BLOQUEANTE

Ninguno.

### MENOR

**MENOR-7 — La guarda rechaza también los `write` que no cambian el valor.**
`models/practice_agreement.py:22` comprueba solo `'agreement_type' in vals`, no si el valor difiere
del actual. Cualquier `write` que reenvíe el valor vigente (multi-edición, código genérico que
recompone un `vals` completo, integraciones) fallará con un error que al usuario le resultará
incomprensible porque no ha cambiado nada. El formulario protege el campo con `attrs` y el árbol
heredado no es editable, así que hoy no se dispara desde la UI, pero la superficie RPC sí.
Corrección: filtrar por diferencia real, p. ej.
`lambda rec: rec.state in (...) and rec.agreement_type != vals['agreement_type']`.

**MENOR-8 — Sin vía de recuperación para un convenio con el tipo equivocado.**
El módulo base no expone ninguna acción de «volver a borrador» ni de cancelar
(`views/practice_agreement_views.xml:10-12`: solo `action_send_by_email` y `action_view_pdf`, y el
`statusbar` no es `clickable`). Con la guarda nueva, un convenio enviado con el tipo equivocado
queda congelado de forma definitiva: no se puede corregir ni pasar a `cancelled`, y su enlace de
portal sigue siendo firmable. La carencia es del módulo base, pero el bloqueo nuevo la vuelve
visible. No hay pérdida de datos y el rodeo (crear un convenio nuevo) existe, por eso no bloquea.
Corrección sugerida: documentar la limitación, o añadir un botón de reset a borrador restringido a
`group_practice_agreement_manager`.

**MENOR-9 — El mensaje de error no cubre el caso `cancelled`.**
`models/practice_agreement.py:27-28` dice «ya enviado o firmado», pero la guarda también salta con
`state == 'cancelled'`. Conviene ajustar el texto para no confundir al usuario.

**MENOR-10 — Cobertura del delta incompleta.**
`tests/test_practice_agreement_types.py:118-127` se llama `test_cannot_change_type_after_sent` pero
solo ejercita `state == 'completed'`; las ramas `sent` y `cancelled` —justamente la ampliación
respecto a lo recomendado en la ronda 1— no están cubiertas. Y la expresión defensiva de
`print_report_name` **no la ejerce ningún test**: el helper `_render_agreement_html` usa
`_render_qweb_html`, que no evalúa `print_report_name`. La expresión es sintácticamente válida y
`_fields` supera el filtro de `safe_eval` de Odoo (no contiene dunder ni está en
`_UNSAFE_ATTRIBUTES`), pero conviene que la Validación confirme al menos una impresión real del PDF
para que el fallback no quede solo razonado sobre el papel.
Corrección: añadir una aserción sobre `safe_eval(report.print_report_name, {'object': agreement})`
y extender el test de la guarda a `sent`.

### NIT

- La guarda se aplica también en `sudo()` y en contexto de instalación/migración. Es lo habitual en
  Odoo y no hace falta cambiarlo, pero si en el futuro hay un script de migración de datos habrá
  que preverle una salida por contexto.

## Notas de seguridad de esta ronda

El delta no introduce credenciales, `sudo()` nuevo, entradas sin validar ni dependencias, y no toca
zonas sensibles (`etc/`, `docker*`, pagos, integraciones, migraciones). La guarda de `write` es un
control **server-side**, no una restricción de UI, que es exactamente lo que pedía MENOR-2: refuerza
la integridad del documento con valor legal en la capa que ejecuta la operación. La expresión de
`print_report_name` se evalúa con el `safe_eval` de Odoo y no amplía la superficie de evaluación.

## Veredicto ronda 2

Los dos cambios hacen lo que dicen hacer y ninguno rompe el comportamiento heredado. No hay
hallazgos BLOQUEANTES. Los hallazgos nuevos (MENOR-7 a MENOR-10) son de robustez y cobertura, no de
corrección funcional, y los abiertos de la ronda 1 no han empeorado.

REVIEW OK

[YES] Reason: El `write()` override es un control server-side correcto y batch-safe que no
interfiere con `action_send_by_email` ni `action_complete_signature`, la expresión defensiva de
`print_report_name` elimina el `AttributeError` tras desinstalar el módulo, el GREEN cubre 7 tests
sin fallos ni errores, y los hallazgos restantes (no-op writes rechazados, ausencia de vía de
recuperación, mensaje impreciso y cobertura pendiente del fallback de impresión) son MENORES que no
bloquean la Validación.
