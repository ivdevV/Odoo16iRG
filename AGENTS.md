# AGENTS.md — Odoo16iRG

Este archivo es la política canónica para cualquier agente que trabaje en Odoo16iRG. Las instrucciones directas del usuario prevalecen cuando amplían o restringen el alcance, pero no eliminan los controles de seguridad, la evidencia ni la autorización de publicación.

## Alcance y proporcionalidad

Las consultas, diagnósticos y revisiones de solo lectura no crean misión (`none`). Los cambios triviales de documentación o configuración no sensible usan misión ligera (`light`). Features, bugfixes, cambios de comportamiento, seguridad, datos o trabajo cross-module usan misión completa (`full`). La clasificación mide solo el cambio funcional: los archivos y artefactos de la propia misión no cuentan para determinar el nivel.

## Ciclo de vida obligatorio

El flujo canónico exacto es: `Plan → Implementación/TDD → Review → Validación → Documentación → Publicación autorizada`.

Después de Documentación y antes de Publicación autorizada se ejecuta una revalidación final sobre el árbol final; se actualizan `verification.json` y la evidencia para que cubran exactamente el estado entregado.

Las fases tienen propietarios distintos y gates explícitos:

1. **Plan — orquestador.** Define alcance, criterios de aceptación, riesgos, tier, capacidad requerida, roles, pruebas y artefactos. Consulta la knowledge base antes de descomponer el trabajo y crea `plan.md` antes de cualquier cambio funcional. Si el usuario pidió implementar, el trabajo continúa después del plan salvo que haya una decisión material abierta, un riesgo sensible sin aprobar o una petición de «solo plan».
2. **Implementación/TDD — codificador.** El codificador es propietario de TDD: escribe y ejecuta RED antes de modificar código de producción; después implementa el cambio mínimo, ejecuta GREEN y refactoriza manteniendo GREEN. Cuando TDD no sea viable, registra en `execution.md` la causa objetiva y la alternativa de verificación antes de implementar.
3. **Review — revisor.** Una persona o agente distinto del codificador comprueba requisitos, calidad, antipatrones, alcance y seguridad. No aprueba con observaciones bloqueantes abiertas.
4. **Validación — validador.** El validador es independiente del codificador, repite los checks sin confiar en resultados previos y no edita ni corrige código de producción. Emite `verification.json` y evidencia objetiva; si detecta un fallo, lo devuelve a Implementación.
5. **Documentación — documentador.** Solo empieza tras Review y Validación satisfactorios. Actualiza uso, configuración, pruebas, limitaciones y changelog, y persiste únicamente conocimiento reutilizable.
6. **Publicación autorizada — responsable de entrega.** Solo realiza la acción concreta que el usuario haya autorizado y después de los gates aplicables. Nunca infiere permiso para commit, push o PR a partir de otra acción.

Si cualquier gate falla, reabre la fase de Implementación para corregir y repetir Review y Validación; la corrección y el escalado de capacidad son decisiones separadas, y corregir no implica escalar automáticamente. El fallo se registra con su evidencia. Si la capacidad fue insuficiente, se escala `trivial → standard → complex`; en `complex` se corrige y revalida sin afirmar un escalado adicional inexistente.

## Routing de capacidad

El orquestador clasifica con señales objetivas y justifica el tier en `plan.md`:

| Tier | Señales funcionales | Capacidad requerida |
| --- | --- | --- |
| `trivial` | Un archivo, sin lógica nueva ni riesgo; edición mecánica o documental | Capacidad ligera con seguimiento preciso de instrucciones |
| `standard` | Dos a cinco archivos, lógica acotada, fix localizado y contexto claro | Capacidad sólida de implementación y pruebas |
| `complex` | Más de cinco archivos, cross-module, arquitectura, debugging no reproducible, seguridad, concurrencia o datos | Máxima capacidad de razonamiento disponible |

Autenticación, concurrencia, migraciones de datos, secretos o configuración de despliegue y borrado de datos históricos fuerzan como mínimo `standard` y activan al Security Advisor. La política expresa capacidad requerida: solo se registra una selección de modelo cuando el runtime permite seleccionarlo realmente; en otro caso se documenta la capacidad usada sin inventar control sobre el modelo.

## Artefactos de misión

Toda misión usa `execution.md` y evidencia concisa compatible con `.gitignore`; `diff.patch` es opcional porque Git conserva el diff canónico. Una misión ligera contiene `plan.md`, `execution.md` y `verification.json`. Una misión completa añade `artifacts/`, `CHANGELOG.md` y documentación o knowledge cuando correspondan. La evidencia versionada guarda la salida final, el RED relevante y diagnósticos necesarios; no duplica logs completos repetitivos. Los outputs grandes se resumen o comprimen y se prefieren extensiones versionables como `.txt` y `.json`.

`execution.md` se actualiza durante el trabajo con comandos, decisiones, reintentos, escalados y sus motivos. `plan.md` siempre precede a cambios funcionales. `verification.json` es el gate de cierre: sin estado `passed` no se considera terminada la misión.

## Contrato de verificación

Cada check registra nombre, comando, resultado y detalle. El resultado solo admite `pass`, `fail` o `skipped`; todo `skipped` requiere una justificación no vacía y aceptable para el alcance. `status` solo puede ser `passed` cuando no existe ningún fallo y todos los skips están justificados; cualquier `fail` obliga a `status: failed` y reabre Implementación.

Este es un ejemplo válido de `verification.json`:

```json
{
  "status": "passed",
  "task": "example-mission",
  "checks": [
    {
      "name": "unit_tests",
      "command": "python3 -m unittest discover",
      "result": "pass",
      "detail": "42 passed, 0 failed",
      "evidence": "artifacts/unit-tests.txt"
    },
    {
      "name": "integration_tests",
      "command": "not run",
      "result": "skipped",
      "detail": "No aplica: cambio exclusivamente documental",
      "evidence": "artifacts/scope-review.txt"
    }
  ],
  "environment": {
    "runtime": "docker-compose.local.yml",
    "database": "odoo16irg_test",
    "base_commit": "0123456789abcdef"
  },
  "model_tier_used": "standard",
  "escalations": 0,
  "evidence": [
    "artifacts/unit-tests.txt",
    "artifacts/scope-review.txt"
  ]
}
```

La validación incluye pruebas unitarias o automatizadas apropiadas, integración o extremo a extremo cuando cruza componentes, y lint, formato y build cuando apliquen. Cada entrada conserva el comando ejecutado, resultado, evidencia, entorno, base o commit y tier efectivo cuando puedan obtenerse.

## Runtime local, worktrees y limpieza

Las validaciones Odoo, pruebas de módulos, renderizados y checks dependientes del runtime usan siempre `docker-compose.local.yml`. Si se trabaja en un worktree y el compose monta el checkout principal, en el worktree se aplica un overlay que monta el código aislado. Al finalizar se ejecuta cleanup o limpieza de fixtures, usuarios y datos temporales, se restaura el servicio original y se registra evidencia tanto de la limpieza como de la restauración. Ninguna prueba debe dejar el entorno compartido apuntando al worktree.

## Seguridad

El Security Advisor revisa obligatoriamente cambios de autenticación, concurrencia, migraciones, secretos o despliegue y borrado histórico antes de implementar. Examina alcance, integridad, pérdida de datos, comandos, contratos funcionales, APIs y sintaxis; su última línea debe ser `[YES] Reason: ...` o `[NO] Reason: ...`. Un `[NO]` bloquea Implementación: el orquestador enmienda el plan y solicita una revisión nueva hasta obtener `[YES]`.

Las restricciones, permisos o controles de UI nunca sustituyen los controles del servidor para acciones protegidas; toda acción protegida exige autorización server-side o un control equivalente en el servidor. Se aplican mínimo privilegio, reglas de acceso, validación de entradas y protección de datos en la capa que ejecuta la operación.

## Knowledge base

La ruta canónica de conocimiento reutilizable es `.agents/knowledge/odoo_development_modding/artifacts/`. Durante Plan se consultan y citan las entradas relevantes. Al documentar se guardan solo decisiones de arquitectura con su motivo, patrones probados, gotchas y convenciones implícitas útiles; no se crean entradas vacías, resúmenes duplicados ni copias de evidencia específica de una misión. Si una entrada resulta incorrecta, se corrige.

## Commit, push y PR

Commit, push y PR son acciones y autorizaciones separadas: autorizar commit no autoriza push ni PR; autorizar push tampoco autoriza PR. La autorización debe identificar la acción y su alcance; completar los tests, crear un commit local o recibir una autorización anterior no amplía el permiso.

Cada autorización de push es de un solo uso y queda ligada al remoto, rama y alcance concretos indicados. Después de usarla, o ante cualquier cambio material posterior, se requiere una autorización nueva o un OK nuevo. En particular, queda prohibido hacer push a `Dev_iRG` sin autorización explícita nueva del usuario en ese momento; no se hace push ni se abre PR por iniciativa del agente.
