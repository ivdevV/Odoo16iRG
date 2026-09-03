# irg_practice_request_online_types

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Depende de:** `openeducat_core`, `isep_practices_2`, `irg_practice_center_type_modalities`, `irg_practice_preferred_quarter`

---

## Qué hace

En la solicitud de prácticas del campus, un alumno de **máster online** solo puede elegir:

- Convalidación por experiencia (`validation`)
- Convalidación por TFM (`tfm_validation`)
- Prácticas asíncronas (`homeclass_asincronas`)

Secretaría en backend no está limitada.

## Detección (lote)

Se usa `op.student.course.batch_id.code`:

| Código | ¿Online? |
| --- | --- |
| Vacío | No |
| `MONLHC…` / `MONLPRS…` | No (Neurologopedia HomeClass / Presencial) |
| `MONLONL…` | Sí |
| Otro código con `ONL` | Sí |

No usar `'ONL' in code and 'MONL' not in code`: eso excluye la variante online real `MONLONL`.

## Autorización

El combo se recorta en QWeb. El POST y el `create`/`write` de `practice.request` con usuario portal rechazan un tipo no permitido. El campus crea con `sudo()` pero conserva el uid portal.

## Instalación

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local \
    odoo -c /etc/odoo/odoo.conf -d <db> \
    -i irg_practice_request_online_types \
    --stop-after-init
```

## Pruebas

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local \
    odoo -c /etc/odoo/odoo.conf -d <db_test> \
    -u irg_practice_request_online_types \
    --test-enable --test-tags /irg_practice_request_online_types \
    --stop-after-init --workers=0 --http-port=18069 --log-level=test
```

## Limitaciones

- Si no existe un registro `practice.center.type` con `homeclass_asincronas`, esa opción no aparece.
- El JS legacy que oculta la opción id 2 por nombre de curso se deja intacto.
