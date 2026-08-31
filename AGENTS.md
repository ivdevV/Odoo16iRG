# AGENTS.md — Odoo16iRG

Este archivo es la política canónica para cualquier agente que trabaje en Odoo16iRG. Las instrucciones directas del usuario prevalecen cuando amplían o restringen el alcance, pero no eliminan los controles de seguridad, la evidencia ni la autorización de publicación.

## Alcance y proporcionalidad

Las consultas, diagnósticos y revisiones de solo lectura no crean misión (`none`). Una petición muy simple (`simple`) tampoco crea misión ni exige el ciclo completo: se implementa directamente, sin subagentes, TDD, Review independiente, `verification.json` ni artefactos de misión. Para clasificarla como `simple` debe ser una edición puntual, mecánica o documental de un único archivo, sin lógica de producto, cambio de runtime, dependencias, datos, seguridad, permisos, despliegue ni riesgo de regresión. Su comprobación mínima obligatoria consiste en revisar el diff y su alcance, ejecutar el check de sintaxis o formato que aplique y confirmar el estado Git. La autorización de commit, push o PR sigue siendo independiente y explícita. Los cambios triviales que excedan esos límites, como documentación repartida o configuración no sensible, usan misión ligera (`light`). Features, bugfixes, cambios de comportamiento del producto, seguridad, datos o trabajo cross-module usan misión completa (`full`). La clasificación mide solo el cambio funcional: los archivos y artefactos de la propia misión no cuentan para determinar el nivel. La petición del usuario puede orientar la clasificación, pero nunca rebaja a `simple` un cambio que incumpla cualquiera de sus límites objetivos.

## Ciclo de vida obligatorio

El flujo canónico exacto es: `Plan → Implementación/TDD → Review de código → Validación → Documentación → Publicación autorizada`.

Después de Documentación y antes de Publicación autorizada se hace únicamente una comprobación final acotada del estado Git y de la coherencia de los artefactos. Esta comprobación no es una nueva Review, no repite la validación ni revisa la calidad editorial de la documentación. Solo se reabren Review y Validación si durante Documentación se modificó código, pruebas, seguridad, datos, configuración funcional o comportamiento de runtime.

Las fases tienen propietarios distintos y gates explícitos:

1. **Plan — orquestador.** Define alcance, criterios de aceptación, riesgos, tier, capacidad requerida, roles, pruebas y artefactos. Consulta la knowledge base antes de descomponer el trabajo y crea `plan.md` antes de cualquier cambio funcional. Si el usuario pidió implementar, el trabajo continúa después del plan salvo que haya una decisión material abierta, un riesgo sensible sin aprobar o una petición de «solo plan».
2. **Implementación/TDD — codificador.** El codificador es propietario de TDD: escribe y ejecuta RED antes de modificar código de producción; después implementa el cambio mínimo, ejecuta GREEN y refactoriza manteniendo GREEN. Cuando TDD no sea viable, registra en `execution.md` la causa objetiva y la alternativa de verificación antes de implementar.
3. **Review de código — revisor.** Una persona o agente distinto del codificador revisa exclusivamente los cambios de código y los elementos funcionales asociados, como pruebas, seguridad, datos y configuración de runtime. Comprueba requisitos, calidad, antipatrones y alcance, y no aprueba con observaciones bloqueantes abiertas. No revisa `plan.md`, `execution.md`, `verification.json`, evidencias, changelog, documentación ni knowledge, salvo cuando alguno de esos archivos contenga código ejecutable o cambie el comportamiento del producto. La Review se ejecuta una sola vez por versión funcional del código y solo se repite cuando el código o el comportamiento cambian.
4. **Validación — validador.** El validador es independiente del codificador, repite los checks sin confiar en resultados previos y no edita ni corrige código de producción. Emite `verification.json` y evidencia objetiva; si detecta un fallo, lo devuelve a Implementación.
5. **Documentación — documentador.** Solo empieza tras Review de código y Validación satisfactorias. Actualiza uso, configuración, pruebas, limitaciones y changelog, y persiste únicamente conocimiento reutilizable. El propio documentador comprueba alcance, enlaces, formato y ausencia de contradicciones; esta fase no requiere revisor independiente ni una nueva ronda de Review o Validación.
6. **Publicación autorizada — responsable de entrega.** Solo realiza la acción concreta que el usuario haya autorizado y después de los gates aplicables. Nunca infiere permiso para commit, push o PR a partir de otra acción.

Si falla un gate de código o de validación funcional, se reabre la fase de Implementación para corregir y repetir Review de código y Validación. Los defectos exclusivos de documentación o de artefactos se corrigen dentro de Documentación y solo requieren la comprobación final acotada; no reabren Implementación, Review ni Validación. La corrección y el escalado de capacidad son decisiones separadas, y corregir no implica escalar automáticamente. El fallo se registra con su evidencia. Si la capacidad fue insuficiente, se escala `trivial → standard → complex`; en `complex` se corrige y revalida sin afirmar un escalado adicional inexistente.

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

## Capa E2E

La cobertura extremo a extremo exigida en el contrato de verificación se
implementa con TestSprite MCP y se registra como el check `e2e_testsprite`. El rol
que la ejecuta es `e2e-tester` y su definición está en `.claude/agents/e2e-tester.md`.
`odoo --test-enable` no ejerce la capa web renderizada, de modo que ningún check
de módulo satisface por sí solo esta exigencia cuando el cambio alcanza la
superficie web.

La capa se dispara **por scope del diff**. Es obligatoria cuando el diff toca
vistas o QWeb (`.xml` bajo `views/`, `templates/` o `report/`), assets estáticos
(`static/`), portal, `website`, controladores HTTP o plantillas de diploma y
certificado. En cualquier otro caso el check se registra `skipped` con la
justificación del scope, conforme al contrato de verificación. El orquestador
declara el disparo en `plan.md` y el validador no puede rebajarlo por su cuenta.

La capa corre **después** del resto de checks de validación y solo cuando ninguno
ha fallado, para no gastar ejecución en cloud sobre código que aún no compila ni
pasa sus pruebas de módulo. Su veredicto es un gate: `E2E FAIL` obliga a
`status: failed` y reabre Implementación con la misma mecánica que cualquier otro
fallo de validación; sin `E2E PASS` o un `skipped` justificado no hay Publicación
autorizada. El límite de reintentos del ciclo es el general de la misión, y un
segundo `E2E FAIL` consecutivo sobre la misma causa se escala al usuario en vez de
reintentar una tercera vez.

Los límites de ejecución son estrictos porque TestSprite sube el código indicado a
su nube y tunela el puerto local. `projectPath` apunta **siempre** al directorio
del módulo de la misión, nunca a la raíz del repositorio ni a `etc/`, `docker/` o
`docker-compose*.yml`, que contienen credenciales. La ejecución va contra el
runtime local de `docker-compose.local.yml` en el puerto `8069` y contra una base
de datos desechable; queda **prohibido** apuntar TestSprite a beta o a producción,
y las credenciales de `needLogin` son de un usuario de la base local desechable y
nunca de una cuenta real. Al terminar se aplica la misma limpieza de fixtures,
usuarios y datos temporales que el resto de validaciones dependientes de runtime.

## Seguridad

El Security Advisor revisa obligatoriamente cambios de autenticación, concurrencia, migraciones, secretos o despliegue y borrado histórico antes de implementar. Examina alcance, integridad, pérdida de datos, comandos, contratos funcionales, APIs y sintaxis; su última línea debe ser `[YES] Reason: ...` o `[NO] Reason: ...`. Un `[NO]` bloquea Implementación: el orquestador enmienda el plan y solicita una revisión nueva hasta obtener `[YES]`.

Las restricciones, permisos o controles de UI nunca sustituyen los controles del servidor para acciones protegidas; toda acción protegida exige autorización server-side o un control equivalente en el servidor. Se aplican mínimo privilegio, reglas de acceso, validación de entradas y protección de datos en la capa que ejecuta la operación.

## Knowledge base

La ruta canónica de conocimiento reutilizable es `.agents/knowledge/odoo_development_modding/artifacts/`. Durante Plan se consultan y citan las entradas relevantes. Al documentar se guardan solo decisiones de arquitectura con su motivo, patrones probados, gotchas y convenciones implícitas útiles; no se crean entradas vacías, resúmenes duplicados ni copias de evidencia específica de una misión. Si una entrada resulta incorrecta, se corrige.

## Commit, push y PR

Commit, push y PR son acciones y autorizaciones separadas: autorizar commit no autoriza push ni PR; autorizar push tampoco autoriza PR. La autorización debe identificar la acción y su alcance; completar los tests, crear un commit local o recibir una autorización anterior no amplía el permiso.

Cada autorización de push es de un solo uso y queda ligada al remoto, rama y alcance concretos indicados. Después de usarla, o ante cualquier cambio material posterior, se requiere una autorización nueva o un OK nuevo. En particular, queda prohibido hacer push a `Dev_iRG` sin autorización explícita nueva del usuario en ese momento; no se hace push ni se abre PR por iniciativa del agente.
