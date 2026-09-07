# Review de código — irg-practice-agreement-specific

Alcance revisado: `addons-extra/extrairg/irg_practice_agreement_specific/` completo
(modelos, wizard, controlador, vistas, QWeb, report, seguridad, datos de correo,
tests). No se revisan `plan.md`, `execution.md`, `verification.json`, evidencias ni
documentación. No se ha editado ni ejecutado código.

Ronda 1: `REVIEW FAIL` (1 BLOQUEANTE, 6 MENOR, 6 NIT).
Ronda 2 (esta): `REVIEW OK`. El bloqueante y una menor están cerrados y verificados.

## Comprobación de módulos prohibidos

- `irg_practice_agreement_sign`: sin cambios (`git status` limpio para esa ruta).
- `irg_practice_agreement_types`: sin cambios. El módulo es untracked completo, así que
  se verifica por mtime: todos sus ficheros siguen en 2026-09-04 15:48–16:08, frente a
  los del módulo nuevo, del 2026-09-07 10:06–10:31.
- `isep_practices_2`: sin cambios.

## Estado del hallazgo bloqueante de la ronda 1

**B1 — `especifico_nacional` seleccionable en backend generando un Convenio Marco
etiquetado como «Específico Nacional» — CERRADO.**

Verificado sobre el código actual:

- `models/practice_agreement.py:8`: `ESPECIFICO_TYPES = ('especifico_internacional',)`.
- `models/practice_agreement.py:14-20`: `selection_add` y `ondelete` contienen
  únicamente `especifico_internacional`. El valor ya no existe en la selección, así que
  no es alcanzable desde el formulario que publica `irg_practice_agreement_types`.
- `models/practice_agreement.py:181-187`: `_especifico_pdf_filename()` ya no bifurca por
  tipo; devuelve siempre `Convenio_Especifico_Internacional_...`. Desaparece la rama que
  podía nombrar «Nacional» un documento con clausulado marco.
- `report/practice_agreement_report_templates.xml:62`: `print_report_name` ya no tiene
  rama `Especifico_Nacional`; las tres ramas restantes (`Especifico_Internacional`,
  `Marco_Internacional`, `Marco_Nacional`) mantienen la guarda defensiva
  `'agreement_type' in object._fields`.
- `views/practice_agreement_views.xml:10,34`: los `attrs` pasan de
  `not in ['especifico_internacional', 'especifico_nacional']` a
  `!= 'especifico_internacional'`.
- `tests/test_practice_agreement_specific.py:119`: nueva aserción negativa
  `assertNotIn("especifico_nacional", keys)`, que fija la regresión.

Con ello desaparece la divergencia que motivaba el bloqueo: `_is_especifico()`,
las condiciones `t-if` del report, las del portal y los `attrs` del formulario evalúan
ahora exactamente el mismo predicado (`agreement_type == 'especifico_internacional'`).
Un `grep` sobre el módulo confirma que la única mención restante a `especifico_nacional`
es la aserción negativa del test.

**M2 — botón «Crear Convenio» sin restricción de grupo — CERRADO.**
`views/practice_request_views.xml:13` añade
`groups="irg_practice_agreement_sign.group_practice_agreement_user"`, que es
exactamente el grupo con ACL sobre el wizard y sobre `practice.agreement`. Se elimina el
`AccessError` al pulsar.

Ninguna de las dos correcciones toca el flujo de firma, el controlador ni el documento
QWeb, así que las comprobaciones de la ronda 1 sobre esas áreas siguen siendo válidas.

## Comprobaciones que pasan

- **MRO de `action_complete_signature`**: correcto. La clase del módulo nuevo queda
  primera en el MRO (`specific` → `types` → `sign`). Para los específicos no llama a
  `super()`, por lo que **no** se ejecuta el renombrado a `Convenio_Marco_*` de
  `irg_practice_agreement_types`, y la firma del centro sola no pone
  `state = 'completed'` (solo `_finalize_especifico_pdf`, que exige ambas firmas, lo
  hace). Para los marco delega en `super()` y el flujo previo queda intacto.
- **xpath sin selector `string`**: ninguno de los 8 xpath del módulo usa `@string`. Se
  usan `hasclass()`, `@name` y `contains(., ...)`.
- **QWeb sin `hasattr`**: confirmado, no aparece en ningún XML del módulo.
- **`print_report_name` defensivo**: `'agreement_type' in object._fields` en todas las
  ramas, conforme a `.agents/knowledge/.../irg_report_print_name_foreign_xmlid.md`.
- **Rutas públicas tokenizadas**: tokens `uuid4`, búsqueda por igualdad exacta sobre
  campo indexado, `sudo()` acotado al recordset del token, `csrf=True` con `csrf_token`
  en el formulario, POST-redirect-GET, idempotencia por `state == 'completed'` /
  `signature_student`, e IP normalizada desde `X-Forwarded-For`. Las URLs de alumno y
  centro son distintas y `student_access_token` es `copy=False`. El POST del alumno solo
  escribe firma, nombre e IP; no permite escribir campos arbitrarios.
- **Colisión de herencias QWeb con `irg_practice_agreement_types`**: no la hay. `types`
  ataca `//h4[contains(., 'CLÁUSULAS')]/parent::div` (div interno) y `specific` ataca
  `//div[hasclass('page')]` (contenedor). Lo mismo en el portal (`h6` vs `h5`).
- **Snapshots del wizard**: los nombres de campo coinciden con
  `isep_practices_2.practice.request` (`name` es realmente «Student Name»,
  `op_student_id`, `course_id.course_id`, `total_hours`, `*_available_*_time`,
  `tutor_id`, `practice_center_id`).
- **Documento QWeb**: genérico, sin INMIRA ni «Área de Psicología»; QUINTA con RC de iRG
  limitada a España y seguros a cargo del alumno fuera de España; Anexo I; tabla de tres
  columnas de firma (alumno / iRG precargada / centro); `student_proposed_activities`
  envuelto en `t-if`.
- Higiene: `__init__.py` correctos, `__pycache__` cubierto por `.gitignore`, ACL del
  wizard declarados para los dos grupos de convenios.

## Hallazgos abiertos

### BLOQUEANTE

Ninguno.

### MENOR

**M1 — `print_report_name` puede revertirse a la expresión de `types`.**
`report/practice_agreement_report_templates.xml`, línea 62. Ambos módulos sobrescriben
el mismo `ir.actions.report` ajeno; gana el último cargado. En instalación y en `-u all`
gana `specific` (orden de dependencias), pero un `-u irg_practice_agreement_types`
aislado devuelve la expresión antigua y los específicos volverían a imprimirse como
`Convenio_Marco_Nacional_...`. Sugerencia: documentarlo en el README del módulo y, si se
quiere robustez, mover la expresión final a un único punto (por ejemplo, un método
`_get_report_base_filename` en el modelo invocado desde `print_report_name`) para que la
cadena XML deje de ser el estado compartido.

**M3 — Nombre de fichero incoherente entre el PDF archivado y la impresión bajo demanda.**
`models/practice_agreement.py:181-187` genera
`Convenio_Especifico_Internacional_<alumno>_<centro>_<id>.pdf`, mientras
`print_report_name` genera `Convenio_Especifico_Internacional_<centro>_<referencia>`.
Unificar el criterio para que el adjunto y la descarga desde backend coincidan.

**M4 — `_store_center_signature_and_maybe_finalize` no protege la firma ya estampada.**
`models/practice_agreement.py:129-146`. Solo corta si `state == 'completed'`. El
controlador sí redirige cuando ya existe `signature_center`, pero una segunda llamada
directa al método (script, acción de servidor, otro controlador futuro) sobrescribiría
la firma y la traza de auditoría del centro mientras se espera al alumno. Añadir la
misma guarda `if self.signature_center: return True` que ya existe de facto en el
controlador. Equivalente en `action_complete_student_signature`.

**M5 — La firma del centro no mueve el estado y el `sent` se escribe sin verificar el envío.**
`models/practice_agreement.py:95-122` y `129-146`. `action_send_by_email` marca
`state = 'sent'` aunque `env.ref` no encuentre las plantillas (ambos `if template:` son
silenciosos), y tras firmar el centro el convenio sigue en `sent` sin ninguna señal en
backend de «media firma». Sugerencia: registrar un `message_post` o log cuando falte una
plantilla, y dejar traza en el chatter al recibir cada firma parcial.

**M6 — `_snapshot_vals` usa `getattr` sobre el recordset para los tramos horarios.**
`wizard/practice_agreement_specific_create_wizard.py:54-55`. Funciona, pero el criterio
del proyecto para sondear campos es `'campo' in record._fields`. Además solo se conserva
el horario del primer día con inicio y fin, y un día con solo uno de los dos valores se
lista en `practice_days` sin horario asociado. Si es intencionado, conviene un
comentario; si no, recoger el rango por día.

### NIT

- `wizard/practice_agreement_specific_create_wizard.py`: el parámetro `request` de
  `_snapshot_vals` y de `action_create_agreement` colisiona por nombre con
  `odoo.http.request`. Renombrar a `practice_request` mejora la lectura.
- `_float_to_hour` devuelve `'00:00'` para cero pero `'8:00'` para las ocho; usar
  `'%02d:%02d'` de forma uniforme.
- `views/portal_agreement_templates.xml`: el `position="after"` sobre el `h5` inserta el
  bloque específico entre el `h5` del marco y su `div`, así que en el DOM del marco
  quedan dos nodos ocultos intercalados. Es inocuo, pero anclar en el `div` daría un
  árbol más limpio.
- `models/practice_request.py`: `agreement_ids` se declara y no se expone en ninguna
  vista; añadir un `notebook`/botón inteligente en el formulario de la solicitud daría
  valor inmediato al campo.
- `data/mail_template_data.xml` no usa `noupdate="1"`, de modo que cualquier ajuste
  manual de las plantillas se perderá en el próximo `-u`. Consistente con el módulo base,
  pero conviene decidirlo explícitamente.
- El wizard no impide crear varios convenios específicos para la misma solicitud.
- Si en el futuro se recupera `especifico_nacional`, hay que reintroducirlo a la vez en
  la selección, en el report, en el portal y en los `attrs`; el estado actual es
  coherente precisamente porque el valor no existe en ninguna de las cuatro capas.

## Veredicto

REVIEW OK
