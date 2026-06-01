# irg_forum_online_student_block

**Categoría:** extrairg  
**Versión:** 16.0.1.0.0  
**Licencia:** LGPL-3  
**Instalable:** Sí  
**Autor:** IRG  
**Depende de:** `website_forum`, `website`, `openeducat_core`, `irg_forum_batch_visibility`, `irg_campus_course_forum`, `irg_forum_email_notify`, `irg_forum_followers_post_notify`

---

## Propósito

El módulo bloquea el acceso de alumnos online a foros de campus o curso en Odoo 16. Su objetivo es impedir que estos usuarios vean foros restringidos por su lote o curso online, publiquen temas o respuestas en ellos, y reciban notificaciones asociadas a esos foros.

La restricción se implementa como módulo independiente mediante herencia, sin modificar `website_forum` ni los módulos IRG existentes de visibilidad y notificación. Esto permite activar o retirar el comportamiento de forma reversible.

## Criterio de Bloqueo Online

Un usuario se considera bloqueado para un foro concreto si está relacionado con al menos un lote (`op.batch`) cuyo código, en mayúsculas, contiene `ONL` y no contiene `MONL`, y ese lote o su curso intersecta con la configuración de visibilidad del foro.

Casos importantes:

- `IAONL2601` queda bloqueado.
- `IAHC2606` no queda bloqueado porque es HomeClass (`HC`).
- `MIAHC2606` no queda bloqueado; los máster HomeClass también conservan acceso.
- `MIAMONL2601` y `MBIAMONL2601` no quedan bloqueados; el máster online `MONL` está excluido explícitamente por este módulo.

## Dependencias

- `website_forum` y `website`: base funcional de foros y portal web.
- `openeducat_core`: modelos académicos `op.student`, `op.batch`, `op.admission` y `op.student.course`.
- `irg_forum_batch_visibility`: visibilidad de foros por lote.
- `irg_campus_course_forum`: visibilidad de foros por curso/campus.
- `irg_forum_email_notify`: notificaciones generales de foro.
- `irg_forum_followers_post_notify`: notificaciones a seguidores de publicaciones.

## Comportamiento

- Los alumnos bloqueados no ven foros cuyo lote o curso intersecte con sus lotes/cursos online bloqueantes.
- Si un alumno es mixto y tiene un máster HomeClass en otro curso, conserva acceso a los foros de ese máster HC si las reglas base ya se lo permitían.
- El acceso directo por URL a foros o publicaciones de campus/curso queda reforzado con reglas globales de lectura.
- La creación de temas y respuestas en foros de campus/curso queda bloqueada con un `UserError` traducible.
- Los alumnos online bloqueados se eliminan de los destinatarios de notificaciones por email cuando el foro está asociado a lotes o cursos.
- Los usuarios públicos y administradores de sistema no se bloquean por esta lógica.

## Modelos y Métodos

| Modelo | Tipo | Campos / métodos principales |
|--------|------|------------------------------|
| `res.users` | Herencia | `irg_forum_online_blocked`, `irg_forum_online_blocked_batch_ids`, `irg_forum_online_blocked_course_ids`, `_compute_irg_forum_online_block`, `_irg_forum_online_candidate_batches`, `_irg_forum_is_blocked_online_batch` |
| `forum.forum` | Herencia | `_irg_is_campus_course_forum`, `_visibility_domain_for_user`, `_irg_user_blocks_campus_forums`, `_irg_user_is_blocked_from_forum`, `_irg_filter_online_blocked_partners`, `_get_notification_recipients` |
| `forum.post` | Herencia | `create`, `_irg_forum_from_create_vals`, `_notify_forum_followers_on_new_post` |

`res.users` calcula el bloqueo a partir de lotes efectivos del foro, lotes directos del usuario, admisiones y cursos activos del alumno. La lectura de datos académicos se realiza con `sudo()` para que usuarios portal puedan ser evaluados correctamente en decisiones de acceso.

`forum.forum` amplía el dominio de visibilidad existente y filtra destinatarios de notificaciones. `forum.post` intercepta la creación de publicaciones y respuestas para impedir escritura en foros restringidos cuando el usuario cumple el criterio online.

## Seguridad

El archivo `security/forum_online_student_rules.xml` añade dos reglas globales de lectura:

- `forum_forum_online_student_global_rule`: impide leer foros cuyo lote o curso coincida con los lotes/cursos online bloqueantes del usuario.
- `forum_post_online_student_global_rule`: impide leer publicaciones cuyo foro coincida con los lotes/cursos online bloqueantes del usuario.

Las reglas no conceden permisos de escritura, creación ni borrado. Los administradores de sistema (`base.group_system`) quedan excluidos para conservar capacidad de soporte y gestión.

## Vistas y UI

No añade vistas ni campos visibles en la interfaz. El bloqueo actúa en dominios, reglas de seguridad, creación de publicaciones y destinatarios de notificación.

## Tests

El módulo incluye tests post-instalación en `tests/test_online_student_block.py`:

- Verifica que un alumno `ONL` solo ve foros globales.
- Verifica que un alumno `ONL` no puede publicar temas ni respuestas en foros de campus.
- Verifica que un alumno `ONL` se elimina de destinatarios de notificación.
- Verifica que `HC`, máster `HC` y `MONL` no se bloquean.
- Verifica que un alumno mixto con lote online y máster HC en otro curso conserva el foro del máster HC.
- Verifica que un usuario administrador no queda bloqueado por la regla.

Comando de referencia para ejecutar el módulo con tests en el servidor Odoo preparado:

```bash
odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_forum_online_student_block \
    --test-enable --stop-after-init
```

## Instalación / Actualización

```bash
# Instalar
odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_forum_online_student_block \
    --stop-after-init

# Actualizar
odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_forum_online_student_block \
    --stop-after-init
```

## Rollback

El módulo no crea tablas nuevas ni campos almacenados. Para retirar el comportamiento, desinstalar `irg_forum_online_student_block` desde Apps o mediante un script controlado de `ir.module.module`.

Tras retirarlo, actualizar los módulos de visibilidad y notificación relacionados para restaurar su comportamiento base:

```bash
odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_forum_batch_visibility,irg_campus_course_forum,irg_forum_email_notify,irg_forum_followers_post_notify \
    --stop-after-init
```

## Limitaciones

- La detección depende del código del lote. Si los códigos académicos no siguen la convención `ONL` / `MONL`, la clasificación puede no coincidir con la modalidad real.
- El módulo no migra seguidores existentes ni modifica suscripciones; filtra destinatarios en tiempo de notificación.
- No oculta botones mediante vistas. La protección principal está en dominio, reglas de lectura y bloqueo de `forum.post.create()`.
- El módulo no bloquea `MONL`; los máster online quedan explícitamente fuera de esta regla por requisito de negocio.
- En foros configurados solo por curso, si el curso coincide con un lote online bloqueante del alumno, el foro queda bloqueado aunque el alumno tenga otro lote no online del mismo curso. Esta decisión evita que un foro común de curso se mezcle con usuarios online.

## Changelog

- 2026-06-01 - Documentación inicial del módulo `irg_forum_online_student_block`.
- 2026-06-01 - Se documenta el criterio de negocio: bloquear códigos con `ONL`, excluir `MONL`, y preservar HomeClass `HC` incluido máster `MIAHC2606`.
- 2026-06-01 - Se documenta bloqueo granular por intersección de lote/curso para preservar máster HC no relacionado en alumnos mixtos.