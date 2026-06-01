# IRG Forum Online Student Block

## 1. Titulo corto

Bloqueo de foros de campus para alumnos online.

## 2. Resumen objetivo

Crear un modulo extra que impida que alumnos online accedan a foros de campus/curso, publiquen temas o respuestas, y reciban notificaciones de esos foros.

## 3. Motivo / justificacion

La instancia ya restringe foros por lote y curso mediante modulos propios. La nueva restriccion debe implementarse por herencia en un modulo `irg_*` independiente para no modificar modulos nativos ni modulos custom existentes, manteniendo una separacion clara y reversible.

## 4. Alcance exacto

- Modelos heredados: `res.users`, `forum.forum`, `forum.post`.
- Seguridad: reglas `ir.rule` sobre `forum.forum` y `forum.post`.
- Notificaciones: filtro sobre destinatarios de email y seguidores.
- No se modifican vistas salvo que una validacion posterior detecte botones residuales.

## 5. Diseno tecnico

- Nuevo modulo: `addons-extra/extrairg/irg_forum_online_student_block`.
- `res.users` calcula los lotes y cursos online bloqueantes del usuario a partir de lotes cuyo codigo contiene `ONL` y no contiene `MONL`.
- La deteccion online inspecciona `forum_effective_batch_ids`, `op_batch_ids`, admisiones y cursos de estudiante.
- Se preserva HomeClass: codigos con modalidad `HC`, incluidos master HC como `MIAHC2606`, no cumplen la condicion online.
- Se preserva master online `MONL`: codigos como `MIAMONL2601` o `MBIAMONL2601` quedan excluidos por la regla `MONL`.
- `forum.forum._visibility_domain_for_user()` se extiende para excluir foros cuyo lote o curso intersecte con los lotes/cursos online bloqueantes del usuario. Esto evita romper alumnos mixtos que tambien tengan un master HC en otro curso.
- Reglas globales de lectura refuerzan el bloqueo ante acceso directo por URL con la misma granularidad por lote/curso.
- `forum.post.create()` bloquea la publicacion de temas y respuestas en foros de campus/curso.
- `_get_notification_recipients()` y `_notify_forum_followers_on_new_post()` excluyen partners de alumnos online cuando el foro es de campus/curso.

## 6. Dependencias

- `website_forum`
- `website`
- `openeducat_core`
- `irg_forum_batch_visibility`
- `irg_campus_course_forum`
- `irg_forum_email_notify`
- `irg_forum_followers_post_notify`

## 7. Backwards-compatibility / migracion

No se crean tablas nuevas ni se alteran columnas almacenadas. Los campos nuevos en `res.users` son computados no almacenados. La desinstalacion elimina las reglas y restaura el comportamiento anterior.

## 8. Casos de prueba / criterios de aceptacion

- Un alumno con lote `IAONL2601` no ve foros con lote/curso, no puede crear posts ni respuestas y no recibe notificaciones.
- Un alumno con lote `IAHC2606` conserva acceso y notificaciones si ya tenia permisos por las reglas existentes.
- Un alumno con master HC `MIAHC2606` conserva la logica actual.
- Un alumno mixto con un lote online en un curso y un master HC en otro no pierde el foro del master HC.
- Un alumno con `MIAMONL2601`, `MBIAMONL2601` o codigo generico con `MONL` no se considera bloqueado por esta regla.
- Un administrador de sistema conserva acceso.

## 9. Rollback plan

```bash
odoo -c /etc/odoo/odoo.conf -d <dbname> -u irg_forum_batch_visibility,irg_campus_course_forum,irg_forum_email_notify,irg_forum_followers_post_notify --stop-after-init
```

Si el modulo ya esta instalado y se quiere retirar completamente:

```bash
odoo -c /etc/odoo/odoo.conf -d <dbname> shell
# Desinstalar irg_forum_online_student_block desde Apps o mediante script controlado de ir.module.module.
```

## 10. Estimacion y responsable

- Estimacion: 0.5 jornada tecnica con validacion funcional en servidor real.
- Responsable: iRG / Copilot.