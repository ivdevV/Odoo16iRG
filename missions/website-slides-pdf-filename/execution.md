# Execution — website-slides-pdf-filename

## Clasificación

- Misión `full`, tier `standard`.
- Base: `c93611b84afa5b9d144abbab1f2d07b4e177d727` (`origin/Dev_iRG`).
- Rama: `cursor/slides-pdf-download-name-e49d`.

## Entorno observado antes de implementar

- `node --version` → `v22.23.4`.
- `docker-compose.local.yml` no está en el workspace.
- `docker` no está instalado (`NO_DOCKER`).
- MCP `odoo-prod` en error de descubrimiento. No se consultó PROD.
- MCP TestSprite está registrado. Sin runtime local no se puede tunelar el puerto 8069.

## TDD

QUnit/hoot de Odoo 16 no es viable aquí: no hay runtime Odoo ni Docker. La alternativa, decidida antes de tocar `download.js`, es un test Node (`node:test`) que carga el script en `vm` y ejercita `ensurePdfName`. El ciclo RED → cambio mínimo → GREEN sí se aplica sobre esa función.

## Knowledge

Citada en `plan.md`. No cambia la decisión de añadir `.pdf` en vez de sustituir la extensión de ofimática.

## Seguridad

Subagente `bc-5bfe84f7-02c5-5217-904f-7eaa22f03213`, antes de editar `download.js`.

[YES] Reason: El nombre solo alimenta el atributo download y el filename de html2pdf; el saneado elimina separadores e inyección de ruta, no hay sumidero de comandos ni de servidor, y el acceso al PDF sigue en el controlador existente.

## RED

Comando: `node --test addons-extra/addons_uisep/website_slides_customizations/static/tests/ensure_pdf_name.test.js`

Resultado: 9 tests, 0 pass, 9 fail, exit 1. `ensurePdfName` no existía y los call sites seguían pasando el título crudo.

Evidencia: `artifacts/red-tests.txt`.

## GREEN

Misma función y los dos call sites en `download.js`. Sin refactor: la función ya es el cambio mínimo.

Comandos:

- `node --check` de `download.js` y del test: exit 0.
- `node --test .../ensure_pdf_name.test.js`: 9 pass, 0 fail, exit 0.

Evidencia: `artifacts/green-tests.txt`.

## Review

Subagente `bc-8d930ffd-e718-526e-9015-e0d82089811a`. Informe: `02-review.md`.

REVIEW PASS. Sin observaciones bloqueantes. No se reabrió Implementación.

## Validación

Subagente `bc-7ef35cc1-3894-5751-982c-46c2f81617e6`. Repitió los checks y escribió `verification.json`. No tocó `download.js`.

| Check | Resultado |
| --- | --- |
| unit_node_test | pass (9/9) |
| syntax_download_js | pass |
| syntax_unit_test | pass |
| scope_diff | pass |
| manifest_version | pass (`0.1`, fuera del diff) |
| runtime_odoo | skipped: sin docker, sin compose local, sin listener en 8069 |

## E2E

Subagente `bc-bc398422-6037-5dc0-9d77-09fd7a742585`. No invocó TestSprite.

`e2e_testsprite`: skipped. Causa: no hay runtime local. El diff sí toca `static/`, así que la capa estaba disparada. Evidencia: `artifacts/e2e-testsprite.txt`.

`verification.json` queda `status: pending`. La E2E no está validada y no es un fallo de producto. Escalados: 0. No hay un segundo E2E FAIL.

## Documentación

Después de Review y Validación, sin tocar `download.js` ni el test:

- `missions/website-slides-pdf-filename/CHANGELOG.md`
- `addons-extra/addons_uisep/website_slides_customizations/README.md`
- `.agents/knowledge/odoo_development_modding/artifacts/website_slides_pdf_download_filename.md`
- Ajuste de redacción en `artifacts/e2e-testsprite.txt`: el skip es de runtime, no de scope.

No se reabre Review ni Validación: no cambia código, pruebas, seguridad, datos ni runtime.

## Publicación

Autorizada por el encargo: commit y push solo a `cursor/slides-pdf-download-name-e49d`.

No autorizada: PR, push a `Dev_iRG`, merge, despliegue.
