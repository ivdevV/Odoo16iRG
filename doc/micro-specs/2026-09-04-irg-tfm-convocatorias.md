# Micro-spec: activación y convocatorias del Trabajo Final de Máster

## Objetivo

Automatizar el expediente de TFM desde el 50 % de progreso, habilitar el envío previo del Esquema en MyCampus y, tras asignación manual de convocatoria, controlar dos entregas fechadas y el contenido eLearning visible.

## Alcance aprobado

- Addon nuevo `irg_tfm_convocatorias`; no se modifica código de addons existentes.
- Una ficha `tesis.model` por `op.student.course`, creada al alcanzar `completion_proc >= 50` cuando `activate_tesis=True` y el lote cumple: HC desde 2511, MONLHC desde 2601, ONL desde 2602; PRS excluido.
- La ficha y la tarjeta “Trabajo Final de Máster” aparecen al 50 %. Sin convocatoria solo se admiten versiones de Esquema con comentario opcional.
- La convocatoria es global, manual, editable por usuarios internos y contiene las ventanas de Entrega parcial y Entrega final, en días completos y zona Europe/Madrid.
- La asignación sin Esquema emite advertencia no bloqueante. Asignar cierra el Esquema; retirar reabre el Esquema y retira accesos posteriores.
- Cada máster configura un canal TFM. Categorías sin convocatoria son comunes; las etiquetadas son exclusivas. Las restricciones se aplican en QWeb y en servidor.
- Archivos portal: PDF/DOC/DOCX, máximo 20 MiB de bytes crudos, formato real validado e historial inmutable. El personal interno gestiona excepciones creando versiones nuevas con motivo y chatter.
- Se elimina el acceso legacy desde `/my`; no se envían correos automáticos.

## Contrato de seguridad

- La propiedad se prueba en servidor desde usuario a estudiante, matrícula, expediente y entrega; cualquier ambigüedad deniega.
- Toda mutación portal es POST con CSRF. No existen transiciones ni borrados por GET.
- Las operaciones internas protegidas comprueban `base.group_user` dentro del método de negocio antes de elevar privilegios; el portal carece de ACL directas de escritura.
- Los adjuntos son privados, pertenecen solo a una entrega y la descarga revalida propiedad.
- Las rutas legacy inseguras quedan neutralizadas por completo, incluido el contador de `/my`.
- Las carreras de activación, asignación y subida se serializan con constraints PostgreSQL, savepoints y bloqueo/relectura del expediente.
- Las membresías activas ajenas no se modifican ni se apropian; solo se reactiva una archivada creada por TFM para el mismo expediente. Solo puede archivarse una creada por TFM cuando ya no tiene referencias ni procedencia académica ajena.
- El control eLearning efectivo se aplica antes del controlador padre y no se basa únicamente en la membresía.

## Criterios de aceptación

Las matrices de elegibilidad, idempotencia, transición de convocatoria, ventanas de entrega, versionado, aislamiento portal, accesos eLearning directos y ausencia del flujo `/my` quedan cubiertas por pruebas automatizadas y E2E cuando el runtime esté disponible.
