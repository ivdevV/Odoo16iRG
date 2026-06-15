# AGENTS.md - [NOMBRE_DEL_PROYECTO]

## Regla obligatoria de desarrollo

Todo desarrollo en este proyecto debe seguir siempre el flujo:

1. Plan
2. Implementacion
3. Validacion
4. Documentacion

Cada fase se delegara o ejecutara con el rol indicado, y los subagentes solo se lanzaran cuando llegue su fase correspondiente:

- **Plan**: lo realiza el agente principal, actuando como orquestador del trabajo. Define el alcance, descompone la tarea, **clasifica su complejidad** (ver "Routing dinamico de modelos"), decide que subagentes y modelos se usaran en cada fase, y crea el directorio de mision (ver "Artefactos de mision").
- **Implementacion**: la realiza un subagente codificador. [Indicar aqui la skill o convencion de codigo del proyecto si aplica, p. ej. `documentation-writer`, lint/formatters, guia de estilo, etc.]
- **Validacion**: la realiza un subagente testeador. La regla de cierre es la **verificacion explicita con evidencia** (ver "Contrato de verificacion"): ninguna tarea se considera terminada sin un `verification.json` con estado `passed`. Cuando el cambio sea una feature, bugfix o cambio de comportamiento, debera aplicar TDD siempre que sea viable.
- **Documentacion**: la realiza un subagente documentador despues de que el validador haya pasado los testeos. Documentara todos los cambios, modulos/componentes nuevos, configuracion, pruebas realizadas, criterios de uso y limitaciones conocidas. Tambien debera incluir un changelog claro y conciso al cierre, y **persistir aprendizajes** en la knowledge base (ver "Knowledge base").

## Routing dinamico de modelos

El modelo no se asigna de forma fija por rol, sino **por tarea en tiempo de ejecucion**, segun una clasificacion de complejidad que produce el orquestador en la fase de Plan. El principio sigue siendo el coste: usar el modelo mas barato capaz de cumplir la fase con garantias, y escalar solo cuando la evidencia lo justifique.

### Clasificacion de complejidad (la realiza el orquestador antes de delegar)

Cada tarea se etiqueta en un tier usando senales **objetivas**, no juicio difuso:

| Tier | Senales | Modelo |
|------|---------|--------|
| `trivial` | 1 archivo afectado, sin logica nueva, sin riesgo: renombrados, formateo, boilerplate, edicion repetitiva, lookups, parsing simple, resumenes rutinarios | Modelo ligero/barato (gama `mini`/`nano` o equivalente Groq) |
| `standard` | 2-5 archivos, logica acotada con contexto claro, fixes localizados, sin decisiones de arquitectura ni riesgo de seguridad | Modelo intermedio fuerte de codigo |
| `complex` | >5 archivos o cross-module, requiere razonar sobre trade-offs, diseno de arquitectura, debugging no reproducible, o toca seguridad/concurrencia/datos | Modelo de razonamiento de gama alta |

Senales que **fuerzan** subir de tier independientemente del resto: cualquier cambio que toque autenticacion, concurrencia, migraciones de datos, secretos/configuracion de despliegue, o borrado de datos historicos. Estos van como minimo a `standard` y disparan al Security Advisor.

El orquestador deja registrada la clasificacion y su justificacion en `plan.md` (ver artefactos), para que la decision sea auditable.

### Escalado reactivo

El tier inicial es una apuesta optimista, no un compromiso. Si una tarea **falla la verificacion** (su `verification.json` sale `failed`), se re-encola automaticamente al siguiente tier superior, hasta un maximo de un escalado por nivel. La cadena es: `trivial -> standard -> complex`. Cada reintento se registra en `execution.log` con el motivo del fallo anterior.

Esto hace que en agregado se pague el modelo caro solo cuando hace falta de verdad, en lugar de asignarlo por defecto "por si acaso".

### Modelo por rol (punto de partida, modulado por el tier de la tarea)

- **Orquestador / Plan**: siempre el modelo de razonamiento mas capaz disponible. El planning no se abarata: un mal plan contamina todas las fases siguientes.
- **Codificador / Implementacion**: el modelo lo determina el tier de la tarea (tabla anterior), no el rol.
- **Testeador / Validacion**: modelo intermedio por defecto; escala al modelo del orquestador si aparecen fallos complejos o no reproducibles.
- **Documentador / Documentacion**: modelo ligero/barato, salvo documentacion critica o de arquitectura compleja.
- **Security Advisor**: modelo de razonamiento alto, unicamente cuando se revisen acciones con riesgo.

Si el modelo preferido no esta disponible, se usara el equivalente mas cercano en capacidad.

## Artefactos de mision

Cada tarea o conjunto coherente de cambios se ejecuta dentro de un directorio de mision versionado, que sirve como evidencia trazable del trabajo (no solo del resultado final). Estructura:

```
missions/<nombre-mision>/
  plan.md            # Plan antes de ejecutar: alcance, descomposicion,
                     #   clasificacion de complejidad + justificacion, modelos elegidos
  execution.log      # Que se hizo: comandos, decisiones, reintentos y escalados
  diff.patch         # Cambios concretos aplicados
  verification.json  # Resultado del validador (ver contrato abajo)
  artifacts/         # Outputs intermedios: capturas, logs de tests, datos de prueba
```

Reglas:

- `plan.md` se crea **antes** de tocar codigo. Es el "Plan Artifact": el usuario puede revisarlo y corregir el rumbo antes de gastar en ejecucion.
- `execution.log` se va escribiendo durante la implementacion, no al final. Debe registrar cada escalado de modelo con su motivo.
- El orquestador lee `verification.json` para decidir si la mision esta cerrada o si hay que re-encolar (escalado reactivo).
- Una mision sin `verification.json` con estado `passed` **no se considera completada**, aunque el codigo "parezca" funcionar.

## Contrato de verificacion

La validacion no es un juicio textual ("parece correcto" / "notificar al usuario"), sino la produccion de **evidencia objetiva**. El subagente testeador prueba su propio trabajo y emite un `verification.json` con esta forma minima:

```json
{
  "status": "passed",            // "passed" | "failed"
  "task": "<nombre-mision>",
  "checks": [
    { "name": "unit_tests",       "result": "pass", "detail": "42 passed, 0 failed" },
    { "name": "integration_tests","result": "pass", "detail": "..." },
    { "name": "lint",             "result": "pass", "detail": "..." },
    { "name": "build",            "result": "pass", "detail": "..." }
  ],
  "evidence": ["artifacts/test-output.log", "artifacts/screenshot.png"],
  "model_tier_used": "standard",
  "escalations": 0
}
```

La validacion debe incluir, como minimo:

- Testeos unitarios o pruebas automatizadas adecuadas al cambio.
- Testeos de integracion o de extremo a extremo cuando el cambio afecte a varios componentes.
- Linters/formatters y build cuando apliquen al stack.

`status` solo puede ser `passed` si **todos** los checks relevantes pasan. Cualquier check en `fail` -> `status: failed` -> dispara escalado reactivo o, si ya se agoto la cadena de tiers, se detiene y se reporta al usuario.

Una vez `passed`, se notificara al usuario para que revise el resultado. **No se subira nada al repositorio remoto hasta recibir su OK explicito.**

Para pruebas locales en este proyecto se debe usar siempre el entorno definido en `docker-compose.local.yml`. Las validaciones Odoo, pruebas de modulos, renderizados de reportes y comprobaciones que dependan del runtime local deben ejecutarse contra ese compose cuando aplique.

Queda prohibido subir cambios a la rama remota de desarrollo `Dev_iRG` sin autorizacion explicita del usuario en ese momento. Haber recibido una peticion previa de push o haber completado la validacion no autoriza pushes posteriores; cada subida a `Dev_iRG` requiere un OK explicito nuevo.

No se debe dar por terminado un cambio sin `verification.json` `passed` y sin documentar que se ha seguido este flujo, o explicar explicitamente por que una parte concreta no pudo ejecutarse.

## Knowledge base

El aprendizaje es un primitivo del flujo, no un efecto secundario. Al cerrar cada mision, el documentador persiste lo reutilizable para que las misiones futuras planifiquen mejor.

- **Que se guarda**: decisiones de arquitectura y su motivo, snippets/patrones que funcionaron, gotchas del proyecto (APIs inexistentes detectadas, sintaxis imposible, configuraciones fragiles), y convenciones implicitas que se descubrieron durante el trabajo.
- **Donde**: [adaptar al stack del proyecto. Recomendado: indice vectorial — p. ej. Postgres + pgvector — para recuperacion semantica; alternativa simple: `knowledge/*.md` indexado por tema.]
- **Cuando se recupera**: el orquestador consulta la knowledge base **en la fase de Plan**, antes de descomponer, para reutilizar decisiones previas y no repetir errores ya resueltos. Las entradas recuperadas relevantes se citan en `plan.md`.
- **Mantenimiento**: las entradas son editables y revisables; una entrada incorrecta detectada en una mision posterior se corrige, no se acumula ruido.

## Perfil de seguridad para revisiones sensibles

Cuando una fase proponga comandos, cambios de archivos o acciones con riesgo de seguridad, integridad o perdida de datos, se usara el siguiente perfil de revision:

- **Nombre**: Security Advisor.
- **Rol**: experto estricto en seguridad y revisor de codigo.
- **Criterio**: verificar la seguridad de cambios de archivos, comandos shell y ejecuciones de herramientas antes de aprobarlos.
- **Herramientas esperadas**: lectura de archivos, listado de directorios, busqueda de texto y busqueda web si hiciera falta contexto.
- **Estilo de decision**: respuesta final obligatoria con `[YES] Reason: ...` o `[NO] Reason: ...`, siendo el veredicto la ultima linea.
- **Reglas clave**: ignorar urgencias retoricas, comprobar alcance, proteger datos valiosos como logs o historicos, preservar contratos funcionales, detectar APIs inexistentes o sintaxis imposible, comprobar que la justificacion coincide con el cambio real y rechazar operaciones destructivas o degradaciones no justificadas.
- **Disparadores automaticos**: las senales que fuerzan subida de tier (auth, concurrencia, migraciones, secretos/despliegue, borrado de datos) invocan al Security Advisor obligatoriamente, sin esperar a que el orquestador lo decida.
