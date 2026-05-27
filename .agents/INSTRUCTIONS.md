# OpenCode Instructions — Odoo 16 IRG Workspace

Estas instrucciones adaptan `.github/copilot-instructions.md` al sistema de OpenCode. Tienen prioridad como contexto de proyecto cuando se trabaje en este workspace.

## Contexto Del Proyecto

Este repositorio es un despliegue de Odoo 16 para una institucion educativa IRG/ISEP. La pila corre en Docker con servicios habituales como `odoo_latest`, `pgodoo_latest`, `nginx` y `redisodoo`. Todo el codigo custom vive bajo `addons-extra/`.

## Reglas No Negociables

1. Nunca modificar modulos nativos de Odoo ni modulos existentes de terceros. Las extensiones deben hacerse en modulos extra usando `_inherit`, `_inherits`, `inherit_id` y `xpath`.
2. Los modulos nuevos propios van en `addons-extra/extrairg/` con prefijo tecnico `irg_`.
3. La version objetivo es Odoo 16. Usar API, patrones y manifest compatibles con Odoo 16.
4. Antes de crear un modulo nuevo, escribir una micro-spec en `doc/micro-specs/` siguiendo `SPECIFICATIONS.md`.
5. Al terminar una tarea, emitir un changelog claro y conciso.

## Uso En OpenCode

OpenCode no usa los agentes de GitHub Copilot de forma nativa. Para replicar el comportamiento:

1. Cargar la skill de proyecto cuando aplique: `Especialista en Desarrollo Odoo 16`.
2. Leer `.agents/knowledge/` antes de disenar cambios de negocio o arquitectura.
3. Leer `.agents/workflows/` antes de crear, actualizar o documentar modulos.
4. Usar los perfiles de `.agents/agents/` como prompts operativos para subagentes OpenCode mediante `task` cuando la tarea sea compleja.
5. Usar `glob`, `grep` y `read` para exploracion; usar `apply_patch` para ediciones manuales.

## Modulos Odoo

Cada modulo `irg_*` debe incluir como minimo:

- `__manifest__.py` con `version: '16.0.x.x.x'`, `depends` explicito, `installable: True` y `license`.
- `__init__.py`.
- `models/` para logica Python cuando aplique.
- `views/` con XML heredado mediante `inherit_id` y `xpath`.
- `security/ir.model.access.csv` cuando se creen modelos nuevos.
- `tests/` para logica critica.

## Estandares Python

- Usar `_inherit` y llamar a `super()` al sobrescribir comportamiento existente.
- Justificar cada `sudo()` con un comentario breve.
- Envolver textos visibles al usuario con `_()`.
- Evitar SQL crudo salvo justificacion clara.
- Validar JSON en `fields.Text` mediante `create`, `write` o `@api.constrains`.
- No exponer endpoints sin CSRF, autenticacion y comprobaciones de permisos.

## Estandares XML, QWeb Y Assets

- No usar namespaces no soportados por el parser XML de Odoo, como `x-on:click` o `x-bind:class`.
- Usar XPath estables: `//field[@name='...']`, `//button[@name='...']`, `//div[@id='...']` o `hasclass()`.
- Evitar XPaths posicionales.
- Sanear cualquier contenido renderizado con `t-raw`.
- Registrar librerias externas en el bundle adecuado, normalmente `web.assets_frontend`.
- Proteger librerias de CDN con comprobaciones defensivas como `if (window.LibName) { ... }`.

## Areas Arquitectonicas Clave

- Suscripciones y pagos: `isep_sale_subscription_extension`, `isep_sale_order_cron_payment`, `isep_payment_cron`, `isep_website_sale_custom`, `irg_sale_subscription_esp`.
- Foro y karma: `website_forum` y modulos `irg_forum_*`.
- E-learning y educacion: OpenEduCat y modulos bajo `addons-extra/addons_uisep/`, mas overrides `irg_academic_adaptations`, `irg_campus_course_forum`, `irg_op_*`, `irg_quiz_auto_scoring`, `irg_survey_*`, `irg_timetable_*`.

## Docker Y Verificacion

```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf <args> --db_host=pgodoo_latest
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf -d <dbname> -i irg_module_name --stop-after-init --db_host=pgodoo_latest
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf -d <dbname> -u irg_module_name --stop-after-init --db_host=pgodoo_latest
```

El `odoo.conf` puede apuntar a `nat16_pgodoo_latest`; para pruebas locales usar `--db_host=pgodoo_latest`.

## Checklist Pre-Entrega

- El modulo esta en `addons-extra/extrairg/` y usa prefijo `irg_` si es nuevo.
- El manifest tiene version Odoo 16, dependencias explicitas e `installable: True`.
- `data` carga seguridad antes de vistas cuando aplica.
- No se modificaron archivos nativos ni modulos existentes fuera del alcance permitido.
- Existe `ir.model.access.csv` si se crearon modelos nuevos.
- XML valido, sin namespaces no soportados y con XPaths estables.
- Pruebas anadidas para logica critica cuando procede.
- Textos traducibles con `_()`.
- No hay endpoints inseguros ni `sudo()` injustificados.
- Se incluye changelog final.

## Flujo De Validación y Seguridad Pre-Documentación

Antes de documentar o dar por finalizado un módulo:
1. Validar en un Odoo local usando `docker-compose.local.yml` y correr los tests automatizados correspondientes.
2. **Obligatorio:** Invocar al agente **Security Advisor** para realizar una revisión de seguridad del código implementado, comandos shell o cambios propuestos. Se debe obtener su veredicto formal `[YES]` antes de continuar a la fase de documentación.

## Flujo De Documentacion De Modulos

Cuando se cree o actualice un modulo `irg_*`, generar o actualizar `doc/modules/extrairg/irg_<module_name>.md` junto al codigo. En OpenCode, usar el perfil `.agents/agents/odoo16_module_documenter.md` como prompt para un subagente `general` o ejecutar el flujo manualmente.

