# IRG Business API

Fachada de comandos académicos cerrados para Odoo 16. Lisa (u otro cliente RPC) no usa el ORM genérico: solo crea registros de `irg.api.operation` con un código allowlist, un payload JSON y una clave de idempotencia.

Entrega actual: fases 0–6. Lecturas académicas, borradores eLearning, clonación HomeClass→Online (bootstrap oficial), aperturas/acceso, matrícula oficial, mapas Moodle explícitos, encuestas en borrador y adjuntos privados.

## Instalación

```bash
odoo -c /etc/odoo/odoo.conf -d <dbname> -i irg_business_api --stop-after-init
```

Dependencias declaradas: `irg_course_convocatorias_v2`, `irg_online_subject_opening`, `openeducat_admission`. Gradebook y Moodle se leen solo si el modelo está instalado.

Asigna el grupo **IRG Business API / Business API User** al usuario técnico. Los administradores (`base.group_system`) también pueden operar.

## Uso

### Lectura

`create` de `irg.api.operation` ejecuta la consulta y deja el resultado en `result_snapshot` con `state=verified`.

Campos de cliente:

| Campo | Notas |
| --- | --- |
| `operation_code` | Código allowlist |
| `environment` | `test` o `beta`. `production` se rechaza |
| `request_payload` | JSON texto, máximo 64 KiB |
| `idempotency_key` | Única por usuario + código |

Campos de servidor (`state`, snapshots, `requested_by`, hashes, timestamps) se ignoran si el cliente los envía.

### Escritura

1. `create` valida el payload y deja `state=preview` con `before_snapshot` y `proposed_after`.
2. Aprobar: `action_approve()` en el registro, o un segundo `create` con `irg_approve_operation` y `{"operation_id": <id>}`.
3. Rechazar: `action_reject()` o `irg_reject_operation`.

`write()` y `unlink()` siempre fallan, incluso con `sudo` o con contexto RPC extra. El ACL tiene `perm_write` para que exista el modelo; el método bloquea cualquier mutación directa.

Los borradores de slide se crean como artículo (`slide_category=article`) no publicado. Publicar y despublicar son operaciones distintas.

**Clonación Online:** no crear el canal a mano. `irg_preview_online_clone` / `irg_apply_online_clone` con el `channel_id` del curso **HomeClass**. Al aprobar se llama a `action_copy_homeclass_to_online` (copia slides, secciones, quizzes y adjuntos). Si el Online ya tiene contenido, se rechaza. No copia matrículas de alumnos.

**Baja:** `irg_apply_withdrawal` está rechazada a propósito (`action_down` cancela facturas). Hay que usar la UI oficial.

Contrato detallado: [doc/api-contract.md](doc/api-contract.md).

## Pruebas

```bash
odoo -c /etc/odoo/odoo.conf -d <db_test> \
  -u irg_business_api --test-enable --test-tags /irg_business_api \
  --without-demo=all --stop-after-init --log-level=test
```

## Limitaciones

- Sin controladores HTTP en esta entrega.
- Página máxima 100; HTML de slide máximo 32k caracteres (`html_sanitize`).
- No se pueden borrar operaciones históricas; desinstalar el módulo no deshace escrituras aplicadas.
- E2E TestSprite de las vistas quedó fuera de esta corrida (herramienta ausente en el runtime de Cursor).
