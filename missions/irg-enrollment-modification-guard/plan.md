# Plan de implementación: irg_enrollment_modification_guard

Fecha: 2026-09-07
Estado: implementación realizada; cierre solicitado por usuario con Review y Validación pendientes.
Base inspeccionada: 928c2974ba94acfa4bb6e8730c14426f9071fc6e (Dev_iRG).

## Objetivo y arquitectura

Impedir que una aprobación de modificación de matrícula sobrescriba datos
que cambiaron desde la solicitud. Crear exclusivamente el addon
`addons-extra/extrairg/irg_enrollment_modification_guard`, versión 16.0.1.0.0,
con dependencia `irg_enrollment_modification`, mediante herencia de
`irg.enrollment.change`. No modificar addons existentes.

El modelo conservará una instantánea inmutable de los valores relevantes,
comprobará su vigencia antes de cada visto y protegerá la comprobación y la
escritura dentro de la misma transacción. Mantendrá el flujo académico →
financiero del módulo base, incluidos Word, PDF, denegación y reintento de PDF.

## Decisiones confirmadas por el usuario

- Comprobar solo los campos afectados y sus relaciones necesarias.
- Bloquear a todos, incluidos administradores, sin botón de forzar.
- Si existe conflicto, exigir una nueva solicitud y conservar la anterior.
- Académico aplica primero sus cambios. Finanzas comprueba pedido, pago y
  continuidad de los cambios académicos antes de aplicar el pago.
- Un bloqueo financiero no revierte los cambios académicos ya aplicados.
- Aplicar protección a pendientes anteriores a la instalación usando sus
  datos guardados. Si no bastan para verificar, bloquear y pedir nueva solicitud.

## Clasificación, capacidad y propietarios

Misión full, tier complex: seguridad, concurrencia y escritura coordinada en
matrícula/pedido/líneas. Requiere máxima capacidad de razonamiento disponible;
no se presupone selección de modelo hasta que el runtime la permita.

Orden obligatorio: Plan (orquestador) → Implementación/TDD (codificador) →
Review funcional (revisor distinto) → Validación (validador distinto del
codificador) → Documentación (documentador) → Publicación autorizada.
Antes de implementar, Security Advisor debe revisar este plan y emitir
`[YES] Reason: ...`; un NO obliga a enmendarlo y repetir esa revisión.
No ejecutar código de producción durante la preparación del plan.

## Fuentes consultadas

- `AGENTS.md`: ciclo, seguridad, validación local y autorizaciones separadas.
- `.agents/skills/odoo16_developer/SKILL.md`: herencia en módulo nuevo.
- `.agents/workflows/odoo16_codebase_knowledge.md`.
- `.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`.
- `.agents/knowledge/odoo_development_modding/artifacts/irg_enrollment_modification.md`.
- Addon base: `models/enrollment_change.py`, wizard, ACL, vistas y pruebas.

## Contrato de comparación

La identidad alumno–matrícula siempre debe ser coherente. No usar write_date:
una edición de teléfono, chatter u otro campo ajeno no invalida la solicitud.

| Cambio solicitado | Antes de Académico | Antes de Finanzas, si hay pago |
| --- | --- | --- |
| Curso o lote | Curso y lote originales; compatibilidad curso–lote destino | Valores finales aprobados; relaciones coherentes |
| Año académico | Año original e identidad de matrícula | Año aprobado |
| Modalidad | Pedido, destinatario, conjunto de líneas y modalidad de cada línea | Mismas líneas con modalidad aprobada |
| Forma de pago | Pedido, destinatario y pago original | Mismo pedido y pago original |

En Finanzas, además del pago, revisar todos los campos académicos que fueron
aplicados por esa solicitud. Un campo no solicitado conserva como expectativa
su origen solamente si forma parte de una relación necesaria (p. ej., curso
al cambiar lote). Rechazar destinos inexistentes o incoherentes antes de sudo.

Validar pedido del alumno mediante el contrato disponible: student_id de
sale.order, cuando existe, referencia res.partner; si student_id está informado debe coincidir con el partner del alumno;
solo sin student_id usar partner_id, sin confundir partner e id de op.student.
Conservar ese vínculo en la instantánea. Respetar acceso y compañía antes de
lecturas elevadas; no ampliar los permisos del módulo base.

## Instantánea y solicitudes anteriores

Añadir campos técnicos sin vistas nuevas:
- `irg_guard_snapshot`: fields.Json, copy=False, contenido versionado por fase.
- `irg_guard_blocked`: fields.Boolean, copy=False.
- `irg_guard_conflict_detail`: fields.Text, copy=False.

Para solicitudes nuevas, capturar en servidor los valores reales al crear y
normalizar los origin_* que se reflejan en Word. El cliente no puede aportar
la instantánea, marcas de bloqueo o aprobadores. Validar flags y destinos en
el modelo persistente; el wizard por sí solo no es suficiente.

Distinguir valor vacío conocido de dato histórico no documentado. En nuevas
instantáneas, false es un valor válido cuando el campo de origen es opcional.
En registros antiguos, un origen vacío sin prueba de captura es ambiguo y
bloquea únicamente si ese dato es necesario para la comprobación solicitada.

No rellenar instantáneas históricas con los valores actuales como si fueran
los originales. Reconstruir solo desde origin_*, dest_*, flags y vistos
persistidos. Las solicitudes antiguas de modalidad carecen de instantánea
por línea: bloquear si no puede acreditarse el conjunto y sus valores de
origen. No ejecutar migraciones masivas ni reescribir solicitudes cerradas.

## Bloqueo, experiencia de usuario y conservación

Al detectar conflicto, persistir la marca, registrar en chatter una nota
concisa con campo, esperado y actual, y devolver una notificación estándar
`ir.actions.client` / `display_notification` indicando que debe crearse una
nueva solicitud. No lanzar UserError después de escribir la marca: desharía
la evidencia por rollback de la transacción RPC.

Ejemplo: «No se puede aprobar: el lote era A y ahora es C. Cree una nueva
solicitud con los datos actuales. Esta solicitud se conserva como historial».

La marca es permanente: volver a poner A no rehabilita una solicitud ya
bloqueada. Mantener state y los vistos existentes; permitir la denegación
con los permisos originales para retirar la pendiente del circuito. No
repetir notas en cada intento. No generar documentos ni ejecutar los métodos
mutantes del padre cuando hay conflicto. No crear nueva solicitud
silenciosamente ni copiarla con sus datos originales.

## Integridad y concurrencia

Proteger create/write frente a modificación directa de identidad, flags,
orígenes, destinos, instantánea, estado y aprobadores. Las transiciones
legítimas del padre deben pasar por métodos privados del addon. No usar un
booleano de contexto aportable por RPC como autorización interna. El diseño
concreto de autorización interna debe revisarlo Security Advisor; una opción
es un token Python de identidad por proceso, inaccesible desde JSON/RPC.
Los permisos de grupo siguen comprobándose en cada acción pública.

Antes de comprobar y llamar al padre: comprobar ACL/reglas, bloquear filas
con SQL parametrizado y orden estable (solicitud, matrícula, pedido, líneas),
y refrescar caché ORM de campos relevantes. Incluir protección del conjunto
de líneas, no solo de las filas existentes. No hacer commit manual. Usar
savepoint para el bloque transaccional; un conflicto comercial se persiste
tras salir de ese bloque sin escrituras parciales.

Bajo el aislamiento PostgreSQL efectivo de Odoo, probar y respetar los
reintentos por serialización: no capturar SerializationFailure como si fuese
un conflicto comercial. Probar dos conexiones reales. Si solo se bloquea la
solicitud, una edición simultánea de matrícula todavía podría perderse.

## Archivos funcionales previstos

Bajo `addons-extra/extrairg/irg_enrollment_modification_guard/`:
- `__manifest__.py`, `__init__.py`.
- `models/__init__.py`, `models/enrollment_change.py`: captura, guardas,
  protección de escritura y coordinación de las acciones heredadas.
- `tests/__init__.py`, `tests/test_enrollment_guard.py`: negocio, roles,
  API directa, anteriores a instalación y documentos.
- `tests/test_enrollment_guard_concurrency.py`: transacciones independientes.

No se crean modelos nuevos ni ACL que amplíen acceso. No se modifican vistas,
QWeb, assets, controladores HTTP ni plantillas de documentos.

## Secuencia de implementación y aceptación

### 1. Preparación y Security Advisor

- [ ] Reconfirmar HEAD, cambios ajenos y runtime; conservarlos intactos.
- [ ] Crear worktree aislado desde la base acordada con rama codex/.
- [ ] Copiar los artefactos de misión al worktree y actualizar base efectiva.
- [ ] Registrar revisión de seguridad y YES antes del primer cambio funcional.
- [ ] Preparar base local desechable `odoo16irg_guard_test` y overlay del compose
      que monte exclusivamente el código aislado; registrar el servicio original.

### 2. TDD: instantánea, coherencia y protección de escritura

- [ ] Escribir y ejecutar RED para orígenes capturados por servidor, rechazo de
      matrícula ajena/pedido ajeno/destinos incoherentes y escritura directa de
      state, aprobadores, destinos o snapshot por académico, finanzas y admin.
- [ ] Implementar herencia mínima con captura versionada e inmutabilidad.
- [ ] Ejecutar GREEN y registrar salida breve; sin ampliar ACL.

### 3. TDD: aprobación académica y financiera

- [ ] RED: solicitud lote A→B, matrícula editada a C, aprobación bloqueada sin
      sobrescribir C ni generar PDF; bloqueo persiste incluso si vuelve a A.
- [ ] RED: sin cambios externos aplica B; cambiar teléfono no bloquea.
- [ ] RED: año, curso/lote y modalidad en varias líneas detectan conflictos;
      añadir/quitar una línea invalida una solicitud de modalidad.
- [ ] RED: académico aplica lote B; cambio posterior a C bloquea Finanzas,
      mantiene C y pago original; sin conflicto Finanzas aplica pago destino.
- [ ] RED: error persistido por notificación, sin duplicar chatter; admin no
      fuerza; denegación funciona; reintento de PDF no reaplica matrícula/pago.
- [ ] Implementar comparación antes de super y verificar GREEN.

Ejemplo del núcleo de aceptación usando fixtures course/batch del addon base:

```python
change = self.make_batch_request(origin=self.batch_a, target=self.batch_b)
change.student_course_id.write({'batch_id': self.batch_c.id})
action = change.with_user(self.academic).action_approve_academic()
self.assertEqual(action['tag'], 'display_notification')
self.assertTrue(change.irg_guard_blocked)
self.assertEqual(change.student_course_id.batch_id, self.batch_c)
self.assertEqual(change.state, 'submitted')
self.assertFalse(change.final_attachment_id)
```

`make_batch_request` es fixture a crear en test_enrollment_guard.py: crea un
wizard real con alumno/matrícula/lote origen y change_batch=True, ejecuta
`action_create_request` y devuelve `irg.enrollment.change` del res_id.

### 4. TDD: pendientes anteriores y concurrencia

- [ ] Crear fixtures mediante el addon base antes de instalar el guard, tanto
      submitted como academic_approved. No simular legado con una API pública
      que deje escribir la instantánea protegida.
- [ ] RED: origen verificable continúa; dato necesario ausente bloquea; vacío
      explícito en nueva instantánea no se interpreta como dato perdido.
- [ ] RED: antigua modalidad sin evidencia por línea bloquea; done/refused
      permanecen intactas; no hay migración automática de datos originales.
- [ ] RED con dos conexiones: doble aprobación, edición de matrícula mientras
      se aprueba y cambio simultáneo de líneas/pago. Exigir ausencia de datos
      sobrescritos y de duplicados de visto/documento tras reintentos.
- [ ] Implementar bloqueos/caché/reintentos compatibles con Odoo y GREEN.

### 5. Review y validación independiente

- [ ] Review única sobre la versión funcional final: requisitos, seguridad,
      transacciones, herencia y alcance. Corregir bloqueantes y repetir gates.
- [ ] Validador ejecuta sintaxis/manifest, tests del addon base y guard,
      instalación, actualización y pruebas de concurrencia en compose local.
- [ ] Usar `docker compose -f docker-compose.local.yml -f <overlay-verificado>`;
      resolver nombre de servicio/config desde el runtime antes de ejecutar y
      registrar el comando exacto, sin exponer secretos en los artefactos.
- [ ] Invocación Odoo en ese servicio: `odoo -d odoo16irg_guard_test
      -i irg_enrollment_modification_guard --test-enable
      --test-tags /irg_enrollment_modification,/irg_enrollment_modification_guard
      --stop-after-init --http-port=8079`; añadir configuración local comprobada.
- [ ] Probar actualización con `-u irg_enrollment_modification_guard`.
- [ ] `e2e_testsprite`: skipped justificado por diff exclusivamente de modelos
      y pruebas, sin disparadores web de AGENTS.md. Si se incorpora cualquiera
      de esos disparadores, enmendar plan y ejecutar e2e-tester después de los
      demás checks, solo módulo nuevo/8069/base desechable.
- [ ] Emitir verification.json con comandos exactos, entorno, base, evidencias,
      pass/fail/skipped y motivos. Solo passed permite cerrar implementación.
- [ ] Limpiar fixtures/base/usuarios y restaurar montaje y servicio original;
      verificar y registrar restauración antes de terminar.

### 6. Documentación y entrega

- [ ] Tras gates satisfactorios, crear README del addon, CHANGELOG de misión,
      `doc/modules/extrairg/irg_enrollment_modification_guard.md` y knowledge
      reutilizable sobre snapshot, legado y concurrencia.
- [ ] Comprobar enlaces, alcance, contradicciones y estado Git final acotado.
- [ ] Entregar archivos y pruebas. Commit, push y PR necesitan autorización
      explícita independiente; ninguna está concedida por este plan.

## Riesgos y límites explícitos

- La modalidad del padre escribe todas las líneas: el guard verifica ese
  conjunto; no redefine qué líneas debe cambiar el negocio.
- Un conflicto bloqueado no revierte cambios anteriores ni cierra por sí mismo
  la solicitud. La denegación existente permite archivarla operativamente.
- La protección alcanza operaciones Odoo; no pretende impedir modificaciones
  SQL de un administrador de base de datos o desinstalar el addon.
- No promete detectar un cambio y reversión ocurrido íntegramente antes de la
  comprobación; se compara la situación vigente. Tras detectar y registrar un
  conflicto, la solicitud queda bloqueada permanentemente.
- Pruebas y revisión pendientes: este documento no afirma implementación ni
  validación ejecutadas.

## Enmienda técnica de seguridad — 2026-09-07

Aprobación de negocio confirmada por el usuario. Para cubrir altas, movimientos
y borrados simultáneos de líneas bajo REPEATABLE READ, añadir
`models/sale_order_line.py` al addon: create/write/unlink adquirirán un fence
de versión de fila en los pedidos afectados antes de mutar las líneas, con
orden estable de IDs. La aprobación participará del mismo fence. SQL
parametrizado, sin commit manual; propagar conflictos de serialización para
el reintento completo de Odoo. Los scopes privados con token de identidad
solo autorizan escrituras internas concretas; un token no omite las guardas
de las acciones públicas. Estas piezas se incluyen en RED/GREEN concurrente.

Otros requisitos del Security Advisor: normalizar/eliminar defaults de contexto
para campos protegidos antes de create; token singleton comprobado mediante
`is`, jamás booleano o string serializable; denegación y reintento de PDF
participan de la misma serialización. El vínculo student_id explícito del
pedido prevalece sobre partner_id (un pagador no acredita al alumno).

## Ajuste de compatibilidad financiera — 2026-09-07

Primer GREEN detectó que el grupo financiero del módulo base carece de read
ACL académicas. Security Advisor permite una lectura privada elevada solo
para comparar registros académicos vinculados, manteniendo reglas de registro
y compañías del usuario original; no elevar acción completa ni ampliar ACL.
Comprobar grupo, ACL/reglas solicitud, alumno y pedido antes de esa lectura.
Los conflictos financieros muestran mensaje genérico sin revelar datos
académicos no autorizados. Pruebas de usuario financiero real, regla denegada
y compañía ajena obligatorias. Evidencia: artifacts/security-finance.txt.
