# Forum Post Batch Visibility Controls

## Alcance

Implementar control granular por publicacion de foro para que desde la interfaz de Odoo se puedan configurar:

- Lotes que pueden visualizar una publicacion.
- Lotes que no pueden visualizar una publicacion.

La restriccion debe afectar a lectura de publicaciones, notificaciones flotantes y correos de foro.

## Complejidad

Tier: `standard`.

Justificacion: afecta 3 modulos custom acotados (`irg_forum_batch_visibility`, `irg_forum_notice_popup`, `irg_forum_email_notify`) y modifica logica de visibilidad, pero no toca autenticacion, secretos, migraciones de datos ni borrado historico. No requiere decisiones de arquitectura amplia.

## Knowledge Base Consultada

- `.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`: confirma convenciones del proyecto, uso de `addons-extra/extrairg/`, no modificar core, usar herencia y revisar correos.
- `.agents/workflows/odoo16_codebase_knowledge.md`: confirma consulta de reglas para tareas Odoo/email.

## Plan de Implementacion

1. Extender `forum.post` en `irg_forum_batch_visibility` con un campo Many2many de lotes excluidos.
2. Anadir helpers reutilizables en `forum.post` para comprobar si un usuario puede ver una publicacion concreta.
3. Actualizar la `ir.rule` de `forum.post` para aplicar exclusion negativa ademas de la lista positiva existente.
4. Exponer los dos campos desde la interfaz backend de Odoo para publicaciones.
5. Ajustar `irg_forum_notice_popup` para que sus busquedas con `sudo()` descarten publicaciones no visibles para el usuario.
6. Ajustar `irg_forum_email_notify` para filtrar destinatarios por visibilidad de la publicacion antes de crear `mail.mail`.
7. Validar sintaxis XML/Python y generar evidencia.
8. Documentar cambios y persistir aprendizaje reusable.

## Criterios de Aceptacion

- Una publicacion con `visibility_batch_ids` solo aparece para usuarios de esos lotes.
- Una publicacion con lotes excluidos no aparece para usuarios de esos lotes aunque tambien esten en permitidos.
- Publicaciones sin campos configurados heredan la visibilidad actual del foro.
- El popup no muestra publicaciones excluidas.
- Los correos no se crean para destinatarios excluidos de la publicacion.

## Modelos Elegidos

- Plan: orquestador con modelo de razonamiento alto.
- Implementacion: tier `standard`, modelo de codigo intermedio/fuerte.
- Validacion: tier `standard`, comandos locales disponibles y evidencia en `verification.json`.
- Documentacion: tier ligero/intermedio.
