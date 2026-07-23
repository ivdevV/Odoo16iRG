# Plan de misión — irg-gradebook-moodle-mapping-admin

## Fuente y clasificación

- Especificación aprobada: `docs/superpowers/specs/2026-07-22-irg-gradebook-moodle-mapping-admin-design.md`.
- Política aplicable: `AGENTS.md` del repositorio.
- Misión: `full`; tier: `complex`.
- Justificación: afecta administración de datos y cruza addon, modelos, importador CSV, wizard, herramientas de shell, vistas, ACL y pruebas; supera cinco archivos.
- Runtime de validación: `docker-compose.local.yml`; servicio esperado: `odoo_local`; base: `test_irg_db`.

## Objetivo

Administrar e importar desde Odoo o `odoo shell` el mapeo curso Odoo → varios cursos Moodle → asignaturas Odoo → varios Activity IDs usando los dos CSV consolidados.

La solución representa explícitamente las relaciones jerárquicas, muestra el contexto Odoo/Moodle, y comparte la lógica de importación entre un wizard y el shell. Es conservadora e idempotente: actualiza o añade datos válidos sin borrar, desactivar ni vaciar históricos.

## Alcance y límites

- Crear el addon puente `irg_gradebook_moodle_mapping_admin` en `addons-extra/extrairg/`, dependiente de `irg_gradebook_moodle_routing`, mediante herencia; preservar `irg_gradebook_moodle_wizard` e `irg_gradebook_moodle_routing` sin modificaciones directas.
- Procesar exclusivamente `mapeo cursos.csv` y `Mapeo asignaturas.csv`, separados por `;`, en UTF-8 con BOM o MacRoman.
- Separar análisis sin escrituras y aplicación transaccional con revalidación server-side.
- Conservar en `ImportPlan` el nombre de curso Odoo y el nombre/código de
  asignatura Odoo procedentes del CSV para compararlos justo antes de cada
  escritura; cualquier cambio concurrente bloquea toda la aplicación.
- Omitir como `conflicting_subject_parent` las filas que intenten reutilizar la
  misma clave asignatura/curso Moodle con padres Odoo distintos.
- Validar el `ImportPlan` completo antes de la primera escritura: tipos, claves
  únicas, padres coherentes, actividades no vacías e IDs únicos.
- No crear cursos o asignaturas Odoo ausentes, consultar Moodle, borrar históricos, cambiar el cálculo de notas ni aceptar rutas indicadas desde la web.
- El diseño y este plan no autorizan commit, push, PR, despliegue ni importación real.

## Estructura prevista

```text
addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/
├── __init__.py
├── __manifest__.py
├── models/{__init__.py,moodle_mapping_admin.py}
├── services/{__init__.py,mapping_import.py}
├── wizard/{__init__.py,mapping_import_wizard.py}
├── tools/{__init__.py,import_mapping.py}
├── security/ir.model.access.csv
├── views/{moodle_mapping_admin_views.xml,mapping_import_wizard_views.xml}
├── tests/{__init__.py,common.py,test_mapping_admin_models.py,
│          test_mapping_import_analysis.py,test_mapping_import_apply.py,
│          test_mapping_import_wizard.py}
└── README.md

missions/irg-gradebook-moodle-mapping-admin/
├── plan.md
├── execution.md
├── verification.json
├── CHANGELOG.md
└── artifacts/{security-advisor.txt,red-tests.txt,green-tests.txt,
               review.txt,validation-tests.txt,real-csv-smoke.txt,scope-review.txt}
```

## Criterios de aceptación

1. Parseo UTF-8 BOM y MacRoman con `;`.
2. Encabezados legados y canónicos del CSV de cursos, incluido conflicto entre alias.
3. Un curso Odoo con varios Moodle Course IDs HomeClass/Online.
4. Una asignatura con varios Activity IDs.
5. Omisión de cualquier fila sin actividades sin crear un mapa vacío.
6. Deduplicación estable de IDs y alineación de nombres.
7. Rechazo por curso/asignatura inexistente, pertenencia incorrecta, nombres o código incoherentes y pareja de curso ausente.
8. Unión estable de filas repetidas para la misma asignatura y curso Moodle.
9. Idempotencia y conservación de líneas, tipos, históricos y metadatos no vacíos.
10. Ausencia de escrituras persistentes durante el análisis.
11. Atomicidad de la aplicación ante un fallo ORM.
12. Equivalencia entre la entrada binaria del wizard y las rutas del shell.
13. Restricción real del wizard a administradores, incluida llamada directa a métodos server-side por un usuario interno sin privilegios.
14. Vistas instalables con todas las columnas de curso, asignatura y actividad.
15. Regresión del routing `HC`/`ONL`, selección por año y aislamiento por mapa padre.

## Propiedad de fases y gates

| Fase | Propietario independiente | Gate |
| --- | --- | --- |
| Plan | Orquestador | Este plan antecede cualquier cambio funcional. |
| Security Advisor | Asesor independiente | Informe terminado en `artifacts/security-advisor.txt` cuya última línea sea `[YES] Reason: ...`; un `[NO]` enmienda el plan y bloquea Task 2. |
| Implementación/TDD | Codificador | RED antes de producción; GREEN y refactor conservando GREEN. |
| Review de código | Revisor distinto del codificador | Sin observaciones bloqueantes. |
| Validación | Validador distinto del codificador | `verification.json` en estado `passed`, con evidencias. |
| Documentación | Documentador | Uso, límites, changelog y conocimiento reutilizable consistentes. |
| Publicación | Responsable de entrega | Solo la acción y alcance expresamente autorizados por el usuario. |

## Gate de seguridad previo a producción

Task 2 queda bloqueada hasta que un Security Advisor independiente revise y deje el dictamen `[YES]` requerido. El wizard limitará el base64 codificado a `4 * ceil(10 MiB / 3)` antes de decodificar, repetirá el límite de 10 MiB sobre los bytes y aplicará el control previo en `create`/`write`, incluso por RPC. El adaptador shell solo aceptará rutas absolutas y leerá como máximo 10 MiB + 1 byte. La revisión también debe cubrir: contenido CSV y mensajes sin registrar filas completas ni datos personales; inexistencia de rutas web; `base.group_system` en ACL, interfaz y todos los métodos públicos server-side; singleton y estado `validated` al confirmar; llamadas RPC directas de usuarios internos no privilegiados; ausencia de `sudo()`; ausencia de `commit()`, `unlink()` y reemplazo completo de One2many; reanálisis y revalidación en servidor al confirmar; y rollback íntegro ante error ORM.

Las pruebas de seguridad del upload cubrirán exactamente 10 MiB, un byte decodificado por encima, base64 inválido, longitud codificada excesiva con el decodificador parcheado y escritura RPC directa excesiva.

## Baseline registrado el 2026-07-22

| Comando | Resultado |
| --- | --- |
| `git status --short` | `?? docs/superpowers/plans/2026-07-22-irg-gradebook-moodle-mapping-admin.md` y `?? docs/superpowers/specs/2026-07-22-irg-gradebook-moodle-mapping-admin-design.md`; son cambios no relacionados preexistentes y se dejan intactos. |
| `git rev-parse HEAD` | `c2495c7a67ee4e87b701d72edcee383f90a76ffe` |
| `docker compose -f /Users/ivrogo/Workspace/Proyectos iRG/Odoo16iRG/docker-compose.local.yml config --services` | `pgodoo_local`, `redisodoo_local`, `odoo_local`. El compose base vive fuera del worktree; `.superpowers/sdd/docker-compose.worktree.yml` está verificado y reemplaza el montaje `/mnt/extra-addons` por este worktree. |
| `docker compose -f /Users/ivrogo/Workspace/Proyectos iRG/Odoo16iRG/docker-compose.local.yml run --rm odoo_local odoo ... -u irg_gradebook_moodle_routing --test-tags /irg_gradebook_moodle_routing ...` | Baseline de regresión completado: 20 métodos, 22 pruebas, 0 fallos y 0 errores. Para validaciones que ejecuten código de este worktree se dispone del overlay verificado descrito en la fila anterior. |
