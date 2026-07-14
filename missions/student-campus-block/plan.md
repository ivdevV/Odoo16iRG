# Mission Plan: student-campus-block

## Fuente y objetivo

- Especificacion aprobada: `/Users/ivrogo/Downloads/plan.md` (2026-07-14).
- Objetivo: crear el modulo aislado `irg_student_campus_block` para bloquear o reactivar el acceso del usuario portal vinculado a `op.student` desde su formulario.
- Base: rama `feat/student-campus-block`, creada desde el ultimo `origin/Dev_iRG` disponible (`65ec4a043`).

## Knowledge recuperada

- `.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`: modulo nuevo bajo `addons-extra/extrairg/`, prefijo `irg_`, herencia `_inherit`, XPath preciso, cadenas traducibles y `sudo()` justificado.
- `.agents/workflows/odoo16_codebase_knowledge.md`: seguir las reglas de conocimiento del proyecto.
- Memoria de 2026-07-13: no contiene observaciones generadas adicionales; la fuente recuperable es el propio plan entregado por el usuario.

## Alcance y decisiones cerradas

1. Crear un modulo nuevo sin modificar OpenEduCat ni otros modulos existentes.
2. Extender `op.student` con el booleano computado no almacenado `irg_campus_blocked = bool(user_id) and not user_id.active`.
3. Sustituir el toggle ambiguo de la especificacion por dos acciones publicas explicitas e idempotentes: bloquear y desbloquear. Esta enmienda de seguridad evita que una vista obsoleta invierta accidentalmente el estado decidido por otro operador.
4. Ambas acciones comprobaran en servidor `group_op_back_office_admin` antes de elevar permisos, rechazaran usuarios internos/publicos/no portal, y solo actuaran sobre el `user_id` actualmente vinculado, recuperado con `active_test=False` y `.exists()`.
5. `sudo()` se limitara a la escritura de `res.users`; `message_post()` se ejecutara con el operador real.
6. Registrar en chatter operador real, usuario objetivo, accion y resultado solo cuando haya cambio efectivo.
7. Heredar `openeducat_core.view_op_student_form`, insertar dos botones mutuamente excluyentes y un ribbon rojo.
8. Restringir los botones a `openeducat_core.group_op_back_office_admin`. Se descarta faculty por minimo privilegio: archivar usuarios es una accion de autenticacion de alto impacto y el boton existente de creacion de usuario ya aplica ese mismo grupo.
9. Las confirmaciones indicaran que el bloqueo corta todo acceso autenticado a Odoo (no solo eLearning), que se hace efectivo en la siguiente peticion y que no afecta a Moodle.
10. Moodle queda fuera de alcance (fase 2), segun la especificacion.
11. Cubrir mediante tests bloqueo, desbloqueo, idempotencia/estado obsoleto, ausencia de usuario, chatter, RPC como faculty, objetivo interno/no portal y el riesgo de re-matricula. Para re-matricula se verificaran y documentaran dos escenarios: usuario bloqueado aun vinculado (debe seguir inactivo) y usuario archivado desvinculado (riesgo de colision preexistente, fuera de este modulo si se reproduce).

## Complejidad y routing

- Tier: `complex`.
- Justificacion objetiva: se crean mas de cinco archivos y el cambio afecta autenticacion (`res.users.active`), lo que fuerza revision del Security Advisor. Tambien existe un cruce entre modulos con re-matricula.
- Orquestador/Plan: agente principal, modelo de razonamiento alto.
- Implementacion: subagente codificador, tier complex, aplicando TDD RED-GREEN-REFACTOR.
- Seguridad: Security Advisor de razonamiento alto antes de aceptar la implementacion.
- Validacion: subagente testeador independiente; escalado solo si hay fallos complejos.
- Revision de antipatrones/calidad: subagente independiente despues de implementar.
- Documentacion: subagente ligero despues de `verification.json: passed`.

## Fases y criterios

### 1. Plan

- Confirmar patrones reales de `op.student`, grupos, chatter, compose y flujo de re-matricula.
- Crear los artefactos de mision antes del codigo.
- Obtener veredicto del Security Advisor sobre permisos, `sudo()`, alcance y riesgos de reactivacion.
- No abrir Implementacion hasta obtener veredicto `[YES]` sobre esta enmienda.

### 2. Implementacion (TDD)

- Crear primero tests descubribles, incluidos negativos de seguridad, y ejecutar RED contra `docker-compose.local.yml`.
- Implementar el minimo modulo compatible con Odoo 16.
- Ejecutar GREEN y refactorizar solo con pruebas verdes.
- Mantener `execution.log` durante el trabajo.

### 3. Revision y validacion

- Revisar diff, APIs, traducciones, XPath, permisos y antipatrones.
- Instalar/actualizar en `test_irg_db` mediante el compose local.
- Ejecutar tests con `--test-enable --stop-after-init` y guardar salida completa.
- Validar carga de vista y comprobar que el usuario archivado no autentica en la siguiente peticion; no se afirmara que la sesion Redis se elimina fisicamente.
- Generar `verification.json`; todos los checks relevantes deben pasar.

### 4. Documentacion

- Crear changelog, informe de implementacion/uso/limitaciones y entrada reutilizable en `.agents/knowledge/`.
- Generar `diff.patch` final y completar `execution.log`.

## Restricciones de entrega

- No hacer push, PR ni modificar `Dev_iRG` remoto sin un OK explicito nuevo del usuario.
- No tocar los cambios locales preexistentes del checkout principal.
- No considerar la mision terminada sin `verification.json` con `status: passed`.
