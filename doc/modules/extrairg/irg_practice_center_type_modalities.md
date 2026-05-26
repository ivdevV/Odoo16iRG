# irg_practice_center_type_modalities

## Resumen

`irg_practice_center_type_modalities` ajusta las modalidades disponibles en `Practice Center Types` para reflejar las denominaciones academicas requeridas por IRG.

El cambio se implementa por herencia sobre `practice.center.type`, sin modificar el modulo base `isep_practices_2`.

## Funcionalidad

El campo `type_of_practice` conserva sus claves tecnicas existentes cuando ya estaban en uso:

| Clave tecnica | Etiqueta visible |
| --- | --- |
| `on_site` | Presencial en España |
| `validation` | Convalidación por experiencia |
| `homeclass_sincronas` | HomeClass Sincronas |
| `homeclass_asincronas` | HomeClass Asincronas |

Tambien se añaden dos opciones nuevas:

| Clave tecnica | Etiqueta visible |
| --- | --- |
| `on_site_origin` | Presencial País de Origen |
| `tfm_validation` | Convalidación por TFM |

El modulo crea registros `practice.center.type` disponibles para las dos opciones nuevas, de forma que aparezcan como tipos configurables.

## Archivos

- `models/practice_center_type.py` — hereda `practice.center.type` y amplia `type_of_practice` con `selection_add`.
- `data/practice_center_type_data.xml` — crea los registros base para las nuevas opciones.
- `tests/test_practice_center_type_modalities.py` — valida etiquetas, registros XML y nombres mostrados.

## Instalacion

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local \
    odoo -c /etc/odoo/odoo.conf \
    -d test_irg_db \
    -i irg_practice_center_type_modalities \
    --stop-after-init
```

## Pruebas

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local \
    odoo -c /etc/odoo/odoo.conf \
    -d test_irg_db \
    -u irg_practice_center_type_modalities \
    --test-enable \
    --test-tags /irg_practice_center_type_modalities \
    --stop-after-init \
    --workers=0 \
    --http-port=18069
```

## Limitaciones

- No renombra datos historicos fuera de las claves de seleccion; los registros existentes con `on_site` o `validation` muestran la nueva etiqueta por el propio campo selection.
- No modifica las opciones `HomeClass Sincronas` y `HomeClass Asincronas`.

## Changelog

- 2026-05-26: Creado el modulo `irg_practice_center_type_modalities` con las modalidades nuevas y las etiquetas actualizadas.
