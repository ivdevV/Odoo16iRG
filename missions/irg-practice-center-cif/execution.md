# Ejecución: CIF en centros de prácticas

## Decisiones

- El CIF vive en `practice.center.cif`, un valor por centro.
- `resolve_center_cif` decide el valor: CIF del centro si tiene texto; si no, el VAT del contacto.
- No se editan `isep_practices_2` ni `irg_practice_agreement_sign`.

## TDD

`docker info` no conecta: el daemon de Docker no está en marcha (`DOCKER_DOWN`, comprobado también fuera del sandbox). No se puede ejecutar `odoo --test-enable` ni TestSprite contra `docker-compose.local.yml`.

Alternativa registrada antes de implementar el modelo: prueba unitaria de `resolve_center_cif` con `python3 -m unittest`, más `py_compile` y comprobación de que el XML de la vista está bien formado. Las `TransactionCase` quedan en el módulo para cuando el runtime arranque.

## Comandos

```text
python3 addons-extra/extrairg/irg_practice_center_cif/tests/test_resolve_center_cif.py
```

RED inicial: `FileNotFoundError` de `cif.py`, 4 errors. Tras implementar `resolve_center_cif`: `Ran 4 tests` / `OK`.

`python3 -m py_compile` de los Python del modulo: sin errores.
`xml.etree.ElementTree.parse` de `views/practice_center_views.xml`: `xml_ok`.

## Review

Primera review: bloqueante. Escribir el CIF en `res.partner.vat` sin pais puede lanzar `ValidationError` de `base_vat` y revertir Generate Center. Correccion: un solo `write` de `vat` y, si aplica, `country_id`, con contexto `no_vat_validation`. Segunda review: aprobado, sin bloqueantes nuevos.

## Validacion

Unidad, sintaxis y XML: pass, repetidos por el validador. Pruebas Odoo y `e2e_testsprite`: skipped. `docker compose -f docker-compose.local.yml ps` no conecta al socket de OrbStack. El E2E sigue siendo obligatorio por el XML de vistas, asi que la mision no queda cerrada.
