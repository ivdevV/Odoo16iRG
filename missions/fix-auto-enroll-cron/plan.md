# Misión `fix-auto-enroll-cron`

## Fuente y alcance vinculante

Esta misión ejecuta exclusivamente el plan
`/Users/ivrogo/.claude/plans/quiero-que-revises-el-moonlit-ripple.md`.
No se autoriza ninguna mejora, refactorización ni corrección fuera de sus tareas T0.1–T5.

Conocimiento recuperado y aplicado:

- `.agents/knowledge/odoo_development_modding/artifacts/irg_auto_enroll_cron_routing_fix.md`:
  el cron y el botón deben compartir el mismo criterio de segmentación.
- `.agents/workflows/odoo16_codebase_knowledge.md`: se respetan la estructura
  `addons-extra/extrairg/` y las reglas de conocimiento del proyecto.

La instrucción directa del plan de editar cuatro módulos existentes prevalece, para esta
misión concreta, sobre la regla general de crear siempre un módulo nuevo. El único módulo
nuevo será el micro-módulo expresamente pedido por T1.2.

## Clasificación de complejidad

Tier: `complex`.

Justificación objetiva: afecta a más de cinco archivos, cruza varios módulos, modifica la
ejecución programada y su aislamiento transaccional, introduce triggers de cron y requiere
razonar sobre MRO, precedencia, datos históricos y concurrencia potencial. Por tocar
programación/concurrencia del cron se activa una revisión Security Advisor antes de escribir
código de producción.

Modelos/roles:

- Plan/orquestación: modelo de razonamiento alto.
- Implementación: subagente codificador de tier `complex`, aplicando Odoo 16 y TDD.
- Validación: subagente testeador de tier `standard`, con escalado a `complex` si falla.
- Documentación: subagente ligero, solo después de `verification.json` en `passed`.
- Security Advisor: subagente de razonamiento alto antes de implementación.

## Ejecución estricta por fases

1. Fase 0: ejecutar T0.1–T0.4 únicamente con consultas de solo lectura en local y beta;
   guardar evidencia y tabla de hipótesis por entorno.
2. Gate H2: resuelto por el usuario el 2026-07-13. Las admisiones `manual` deben entrar
   en auto-enroll; T2.1 no debe excluirlas del domain.
3. Fase 1: implementar únicamente T1.1–T1.4 mediante TDD.
4. Fase 2: implementar únicamente T2.1–T2.4 mediante TDD.
5. Fase 3: ejecutar T3.1–T3.2 solo si H4 queda confirmada en Fase 0.
6. Fase 4 local: ejecutar T4.1–T4.2 en `docker-compose.local.yml` y producir evidencia.
7. Validación independiente: producir `verification.json`; solo `passed` permite avanzar.
8. Documentación: completar los artefactos de misión, changelog y conocimiento reutilizable.
9. Fase 4 beta y Fase 5 remota: no desplegar, hacer push ni abrir PR hasta recibir el OK
   explícito nuevo que exige `AGENTS.md`. El merge queda excluido en todo caso.

## Artefactos obligatorios

- `execution.log`: comandos, decisiones, resultados y escalados durante la ejecución.
- `artifacts/`: evidencia de diagnóstico y pruebas.
- `diff.patch`: diff completo de la misión.
- `verification.json`: contrato objetivo del validador.
- `spec.md`, `progress.md`, `review.md`, `validation.md`: cierre SDD solicitado por Fase 5.

## Criterios de parada

- H2 confirmada: checkpoint resuelto; incluir modalidad `manual` en auto-enroll.
- Bloqueo o ambigüedad del plan: no adivinar.
- Validación fallida: registrar y escalar `standard -> complex`; no documentar como cerrado.
- Ningún commit ni acción remota antes de `PASS global` y autorización explícita del usuario.

---

# Plan de implementación revisado

> **Para subagentes:** usar desarrollo dirigido por subagentes y TDD rojo→verde. Cada tarea
> se revisa contra este documento y `spec.md`. No hacer commits: `AGENTS.md` exige
> `verification.json: passed` y un OK explícito nuevo antes de cualquier commit/push.

**Objetivo:** hacer robusto el auto-enroll horario y bajo demanda, unificando cron y botón,
incluyendo modalidad manual, preservando históricos y evitando desmatriculaciones masivas,
duplicados concurrentes y triggers perdidos.

**Arquitectura:** `irg_online_subject_opening` seguirá siendo la implementación efectiva del
cron y delegará cada admisión en `auto_enroll_student()`. `irg_subject_fix` concentrará la
precedencia común y la reactivación idempotente. El nuevo micro-módulo
`irg_auto_enroll_cron_robust` observará cambios en `op.subject.to.batch` y usará el trigger
nativo de Odoo sin locks ni estado auxiliar. El mismo micro-módulo impondrá la unicidad
activa por alumno/canal/lote y envolverá el entrypoint completo de auto-enroll para aislar
únicamente colisiones concurrentes de ese índice.

**Stack:** Odoo 16, Python ORM, PostgreSQL row locks/savepoints, XML data y tests Odoo
`TransactionCase`/cursores de registro para concurrencia.

## Restricciones globales

- Procesar admisiones `state='done'` con `batch_id`, incluida `modality='manual'`.
- Intervalo por defecto: 1 hora; XML con `noupdate="1"`.
- Abort/rollback global solo si `archived / (activated + archived) > 0.30`.
- Savepoint individual por admisión; `except` fuera de ese savepoint.
- Fallback histórico siempre restringido por `partner_id + op_subject_id + batch_id`.
- Backfill solo como artefacto one-shot, no cargado ni ejecutado en `Base16`.
- Entorno de validación local obligatorio: `docker-compose.local.yml`.
- Ningún cambio fuera de T1.1–T4.2 y los cuatro requisitos S1–S4 de `spec.md`.

## Mapa de archivos

**Modificar**

- `addons-extra/addons_uisep/isep_elearning_custom/data/cron_batch_slide_channel.xml`:
  propiedad `noupdate` e intervalo horario.
- `addons-extra/extrairg/irg_online_subject_opening/models/op_admission.py`:
  cron efectivo, logging, savepoints, guardarraíl, lock compartido y delegación al botón.
- `addons-extra/extrairg/irg_online_subject_opening/tests/test_online_subject_opening.py`:
  pruebas end-to-end, equivalencia, aislamiento, guardarraíl, concurrencia y precedencia.
- `addons-extra/extrairg/irg_online_clone_access_fix/models/op_admission.py`:
  retirar únicamente el override muerto de cron.
- `addons-extra/extrairg/irg_subject_fix/models/op_admission.py`:
  helper de precedencia, búsqueda activa/archivada y comentario del cron muerto.
- `addons-extra/extrairg/irg_online_clone_access_fix/models/slide_channel_partner.py`:
  sincronización de clon aislada por lote y selección activa primero.
- `addons-extra/extrairg/irg_course_convocatorias_v2/models/slide_channel_partner.py`:
  creación/sincronización inicial del clon aislada por lote.
- `addons-extra/addons_uisep/isep_elearning_custom/models/op_admission.py`:
  comentario sobre el override muerto; no borrar lógica.

**Crear**

- `addons-extra/extrairg/irg_auto_enroll_cron_robust/__init__.py`.
- `addons-extra/extrairg/irg_auto_enroll_cron_robust/__manifest__.py`.
- `addons-extra/extrairg/irg_auto_enroll_cron_robust/models/__init__.py`.
- `addons-extra/extrairg/irg_auto_enroll_cron_robust/models/op_subject_to_batch.py`.
- `addons-extra/extrairg/irg_auto_enroll_cron_robust/models/op_admission.py`.
- `addons-extra/extrairg/irg_auto_enroll_cron_robust/models/slide_channel_partner.py`.
- `addons-extra/extrairg/irg_auto_enroll_cron_robust/hooks.py`.
- `addons-extra/extrairg/irg_auto_enroll_cron_robust/tests/__init__.py`.
- `addons-extra/extrairg/irg_auto_enroll_cron_robust/tests/test_auto_enroll_cron_robust.py`.
- `missions/fix-auto-enroll-cron/artifacts/backfill_memberships.sql`.
- `missions/fix-auto-enroll-cron/artifacts/membership-gaps-report.sql`.

### Tarea 1 — Configuración del cron T1.1

**Prueba primero**

Añadir en el nuevo test del micro-módulo:

```python
from lxml import etree
from odoo.modules.module import get_module_resource

def test_auto_enroll_cron_has_hourly_default(self):
    cron = self.env.ref('isep_elearning_custom.ir_cron_auto_enroll_students')
    self.assertEqual((cron.interval_number, cron.interval_type), (1, 'hours'))

def test_auto_enroll_cron_xml_is_noupdate(self):
    xml_path = get_module_resource(
        'isep_elearning_custom', 'data', 'cron_batch_slide_channel.xml'
    )
    root = etree.parse(xml_path).getroot()
    self.assertEqual(root.get('noupdate'), '1')
```

Ejecutar solo los tests y comprobar que fallan con `days`/`noupdate="0"`. El test de
intervalo se ejecutará en la base nueva de validación; en una base ya actualizada el XML
`noupdate="1"` no modifica retroactivamente el valor existente, por diseño de Odoo 16.

**Implementación mínima**

Cambiar el wrapper a `<odoo noupdate="1">`, conservar el mismo XML ID y cambiar solo:

```xml
<field name="interval_number">1</field>
<field name="interval_type">hours</field>
```

Ejecutar de nuevo el test hasta `PASS`.

### Tarea 2 — Trigger nativo T1.2 + S3

**Interfaces**

- Modelo heredado: `op.subject.to.batch`.
- Helper: `_irg_trigger_auto_enroll_cron()` sin argumentos ni retorno funcional.
- Campos observados: `{'date_from', 'date_to', 'subject_id'}`.

**Pruebas rojas**

Crear tests con nombres exactos:

- `test_create_schedules_one_pending_trigger`.
- `test_relevant_write_schedules_trigger`.
- `test_irrelevant_write_does_not_schedule_trigger`.
- `test_unlink_schedules_trigger`.
- `test_change_committed_during_running_cron_keeps_trigger_for_next_run`.

Los tests limpiarán únicamente triggers del cron creados dentro de su transacción y contarán:

```python
domain = [
    ('cron_id', '=', cron.id),
]
```

El test concurrente abrirá dos cursores mediante `registry(dbname).cursor()`: el primero
establecerá el snapshot equivalente a un cron en curso; el segundo confirmará un cambio y
su trigger. La limpieza ejecutada con el primer snapshot no debe ver ni borrar el trigger
nuevo. Los cursores se cerrarán y limpiarán en `finally`.

**Implementación mínima**

Manifest exacto:

```python
{
    'name': 'IRG Auto Enroll Cron Robust',
    'version': '16.0.1.0.0',
    'summary': 'Programa de forma robusta el auto-enroll al cambiar asignaturas de lote',
    'category': 'Education',
    'author': 'IRG',
    'license': 'LGPL-3',
    'depends': ['irg_online_clone_access_fix'],
    'data': [],
    'uninstall_hook': 'uninstall_hook',
    'installable': True,
    'application': False,
}
```

Helper obligatorio:

```python
def _irg_trigger_auto_enroll_cron(self):
    cron = self.env.ref('isep_elearning_custom.ir_cron_auto_enroll_students')
    cron._trigger()
```

`create`, `write` y `unlink` llamarán al helper después de `super()` solo cuando aplique.
`unlink` conservará el `env` y llamará al helper tras borrar; el helper no leerá campos de
las filas eliminadas. No añadir locks, deduplicación ni estado auxiliar para los triggers.
Ejecutar los cinco tests hasta `PASS`.

En `slide.channel.partner._auto_init()`, después de `super()`, comprobar que esta consulta no
devuelve filas:

```sql
SELECT partner_id, channel_id, batch_id
FROM slide_channel_partner
WHERE active IS TRUE AND batch_id IS NOT NULL
GROUP BY partner_id, channel_id, batch_id
HAVING count(*) > 1
LIMIT 1
```

Si devuelve una fila, lanzar `ValidationError` y no modificar datos. Si no devuelve nada,
crear mediante `tools.index_exists()` + SQL el índice:

```sql
CREATE UNIQUE INDEX irg_scp_active_partner_channel_batch_uniq
ON slide_channel_partner (partner_id, channel_id, batch_id)
WHERE active IS TRUE AND batch_id IS NOT NULL
```

`uninstall_hook` usará `tools.drop_index()` para retirar solo ese índice.

Añadir pruebas rojas/verdes:

- `test_same_partner_channel_batch_cannot_have_two_active_memberships`.
- `test_same_partner_channel_different_batch_is_allowed_by_index`.
- `test_homeclass_to_online_uses_clone_and_both_memberships_coexist`.
- `test_concurrent_auto_enroll_keeps_one_active_membership`.
- `test_clone_sync_does_not_reassign_membership_from_other_batch`.
- `test_active_membership_is_preferred_over_older_archived_membership`.

El override superior de `op.admission.auto_enroll_student()` iterará admisiones y envolverá
todo `super(OpAdmission, record).auto_enroll_student()` en un savepoint. Solo capturará
`IntegrityError` cuando `exc.diag.constraint_name` sea exactamente
`irg_scp_active_partner_channel_batch_uniq`; registrará la colisión concurrente y continuará.
Cualquier otra constraint se volverá a lanzar.

En las búsquedas de `slide.channel.partner` del botón, sincronización online y reconciliación
de clones, añadir `batch_id` y usar:

```python
ChannelPartner = self.env['slide.channel.partner'].sudo().with_context(active_test=False)
order='active DESC, create_date ASC'
```

La sincronización inicial de `irg_course_convocatorias_v2` copiará `batch_id` al clon y lo
usará en su domain cuando el origen lo tenga. Si el origen no tiene lote, conservará el
comportamiento `batch_id=False`. No modificar memberships de otros lotes.

### Tarea 3 — Precedencia histórica y botón idempotente T2.3, T3.1, S4

**Interfaces**

- `_irg_subject_precedence_is_satisfied(subject)` devuelve `bool`.
- `auto_enroll_student()` conserva su contrato actual.

**Pruebas rojas**

Añadir:

- `test_archived_membership_is_reactivated_without_duplicate`.
- `test_historical_completed_parent_same_batch_unlocks_child`.
- `test_historical_completed_parent_other_batch_does_not_unlock_child`.

La reactivación debe conservar el ID original y el count. El fallback del mismo lote usará
una membership padre `completed=True`, `active=False`, sin `admission_id`; el caso negativo
usará otro `batch_id`.

**Implementación mínima**

El helper de precedencia buscará primero una membership activa y completada con
`admission_id=self.id`; si no existe, buscará con `active_test=False` una completada con el
mismo alumno, padre y lote, sin filtrar `admission_id`.

La búsqueda del botón será exactamente una fila, incluyendo archivadas:

```python
channel_partner = self.env['slide.channel.partner'].sudo().with_context(
    active_test=False,
).search([
    ('partner_id', '=', record.partner_id.id),
    ('channel_id', '=', subject.slide_channel_id.id),
    ('batch_id', '=', record.batch_id.id),
    '|', ('active', '=', True), ('active', '=', False),
], order='active DESC, create_date ASC', limit=1)
```

Sustituir el check inline por el helper. En `irg_online_subject_opening`, retirar el helper
duplicado para usar el heredado. No añadir row locks. Ejecutar tests hasta `PASS`.

### Tarea 4 — Cron unificado, aislamiento, logging y guardarraíl T1.3, T1.4, T2.1, S1

**Interfaces**

- `_irg_auto_enroll_membership_snapshot(admissions)` devuelve `{membership_id: active}` y
  abarca pares exactos `(partner_id, batch_id)`.
- `_irg_auto_enroll_transition_counts(before, after)` devuelve
  `(activated_count, archived_count)`; nuevas filas activas cuentan como activadas.
- `_irg_mass_archive_ratio(initial_active_count, archived_count)` devuelve `float`.

**Pruebas rojas**

Añadir:

- `test_cron_processes_manual_modality`.
- `test_cron_and_button_produce_equivalent_memberships`.
- `test_cron_continues_after_one_admission_fails`.
- `test_mass_archive_ratio_zero_when_untouched`.
- `test_mass_archive_guard_allows_single_archive_in_larger_initial_scope`.
- `test_mass_archive_guard_allows_exactly_thirty_percent`.
- `test_mass_archive_guard_rolls_back_above_thirty_percent`.
- `test_date_change_past_archives_future_reactivates_and_two_runs_are_idempotent`.
- `test_cron_online_branch_end_to_end_without_batch_dates`.

Para el fallo aislado, parchear `auto_enroll_student` solo para una admisión y comprobar que
otra se procesa. Para rollback >30%, crear suficientes transiciones reales y comprobar tras
la excepción que cada `active` conserva su valor inicial.

**Implementación mínima**

Domain del cron:

```python
admissions = self.search([
    ('state', '=', 'done'),
    ('batch_id', '!=', False),
])
```

No habrá filtro `modality`. El cuerpo seguirá esta forma:

```python
_logger.info('Auto-enroll start: admissions=%s', len(admissions))
with self.env.cr.savepoint():
    before = self._irg_auto_enroll_membership_snapshot(admissions)
    processed = errors = 0
    for record in admissions:
        try:
            with self.env.cr.savepoint():
                record.auto_enroll_student()
            processed += 1
        except Exception:
            errors += 1
            _logger.exception('Auto-enroll failed for admission %s', record.id)
    after = self._irg_auto_enroll_membership_snapshot(admissions)
    activated, archived = self._irg_auto_enroll_transition_counts(before, after)
    initial_active = sum(1 for active in before.values() if active)
    ratio = self._irg_mass_archive_ratio(initial_active, archived)
    _logger.info(
        'Auto-enroll end: processed=%s activated=%s archived=%s errors=%s',
        processed, activated, archived, errors,
    )
    if ratio > 0.30:
        _logger.warning(
            'Auto-enroll mass archive blocked: activated=%s archived=%s initial_active=%s ratio=%.2f%%',
            activated, archived, initial_active, ratio * 100,
        )
        raise ValidationError('Auto-enroll mass archive guard exceeded 30%')
return True
```

La excepción del guardarraíl no se captura dentro del método; debe salir del savepoint
exterior y hacer rollback de todo el run. Los errores individuales sí se capturan fuera de
su savepoint. Ejecutar todos los tests hasta `PASS`.

**Ajuste aprobado tras validación T4.2 (2026-07-13)**

La validación manual demostró que el denominador anterior `activated + archived` convertía
un único archivado sin activaciones en un falso 100% y revertía el cambio de fechas requerido
por T4.2. El usuario aprobó calcular el 30% sobre todas las memberships activas del snapshot
inicial dentro de los pares alumno/lote objetivo. La reimplementación debe hacerse con TDD y
repetir íntegramente la validación automática y manual antes de cerrar la misión.

### Tarea 5 — Limpieza estricta de MRO T2.2, T2.4

**Pruebas/revisión roja**

- Confirmar por introspección que el cron efectivo es el de `irg_online_subject_opening`.
- Ejecutar los tests existentes de clones antes de modificar y conservar su salida.

**Implementación mínima**

- Borrar únicamente `cron_auto_enroll_student` de
  `irg_online_clone_access_fix/models/op_admission.py`.
- Añadir comentario sobre override muerto encima de los métodos de cron de
  `irg_subject_fix` e `isep_elearning_custom`; no borrarlos ni cambiar su cuerpo.
- Ejecutar tests de clones y online; deben seguir `PASS`.

### Tarea 6 — Informe y backfill one-shot T3.2

Crear `membership-gaps-report.sql` solo con `SELECT` que agrupe:

- totales sin `admission_id`/`op_subject_id`;
- candidatos únicos y ambiguos para admisión por `partner_id + batch_id`;
- candidatos únicos y ambiguos para asignatura por canal y lote/curso.

Crear `backfill_memberships.sql` con una transacción explícita. Los `UPDATE` solo afectarán
filas con exactamente un candidato obtenido por CTE `GROUP BY ... HAVING count(*) = 1`.
El script mostrará conteos antes/después y terminará en `ROLLBACK`; ops deberá sustituirlo
conscientemente por `COMMIT` tras revisar el informe. No referenciar estos archivos desde
ningún manifest/hook y no ejecutarlos contra `Base16`.

Validar sintaxis dentro de una transacción siempre revertida en una copia local.

### Tarea 7 — Validación local T4.1–T4.2

Usar exclusivamente `docker-compose.local.yml`. Preparar una base de validación aislada y
actualizar:

```text
isep_elearning_custom
irg_subject_fix
irg_online_subject_opening
irg_online_clone_access_fix
irg_auto_enroll_cron_robust
```

Ejecutar con `--test-enable --stop-after-init` y tags de los módulos tocados. Guardar salida
completa en `missions/fix-auto-enroll-cron/artifacts/test-output.log`.

Prueba T1.1 de upgrade:

1. Cambiar en la BD local el intervalo del cron a 2 horas.
2. Ejecutar `-u isep_elearning_custom`.
3. Consultar el registro y comprobar que sigue en 2 horas por `noupdate=1`.
4. Restaurarlo por ORM/SQL local a 1 hora para el resto de validación.

Prueba manual T4.2:

1. Cambiar `date_to` de una línea al pasado.
2. Comprobar que existe un único `ir.cron.trigger` pendiente.
3. Ejecutar “Run manually”.
4. Verificar archivado y logs con contadores.
5. Mover `date_to` al futuro, ejecutar otra vez y verificar reactivación sin duplicado.

Ejecutar lint/sintaxis Python/XML aplicable. El validador independiente emitirá
`verification.json`; cualquier check relevante fallido implica `status: failed`.

### Tarea 8 — Cierre local y gate remoto

Después de `verification.json: passed`, el documentador completará `validation.md`,
`review.md`, `diff.patch`, changelog y la entrada reutilizable de knowledge base. El
orquestador comprobará el diff contra este plan y que no haya extras.

No se hará commit, push, despliegue beta ni PR en esta ejecución sin un OK explícito nuevo.
T4.3 y la parte remota de T5 permanecen como gate posterior del usuario.
