# Diseño: mejora operativa de AGENTS.md

## Objetivo

Convertir `AGENTS.md` en una política ejecutable y coherente para Odoo16iRG, manteniendo sus garantías actuales y eliminando contradicciones, placeholders y costes de evidencia innecesarios.

## Alternativas consideradas

1. **Parche mínimo:** corregir TDD, JSON y placeholders. Menor diff, pero deja ambiguos review, escalado, Docker, worktrees y publicación.
2. **Reescritura focalizada en un solo archivo (seleccionada):** reorganizar `AGENTS.md` por alcance, ciclo de vida, roles, gates, misiones, validación, seguridad y publicación. Es suficientemente completa sin crear un manual distribuido.
3. **Dividir la política en varios documentos:** `AGENTS.md` como índice y manuales separados. Escala mejor a largo plazo, pero añade navegación y riesgo de reglas divergentes para el tamaño actual del proyecto.

## Diseño seleccionado

### Alcance y proporcionalidad

- Las consultas de solo lectura, diagnósticos y revisiones sin cambios no crean misión.
- Los cambios triviales de documentación o configuración usan una misión ligera.
- Features, bugfixes, cambios de comportamiento, seguridad, datos y trabajo cross-module usan misión completa.
- La complejidad se calcula sobre el cambio funcional; los propios artefactos de misión no inflan artificialmente el tier.

### Ciclo de vida

El flujo canónico será:

`Plan → Implementación/TDD → Review → Validación → Documentación → Publicación autorizada`

- TDD pertenece al codificador: RED antes de producción, GREEN y refactor.
- Review es una puerta explícita de requisitos, calidad, antipatrones y seguridad.
- El validador es independiente, no confía en resultados previos y no corrige código de producción.
- Cualquier gate fallido reabre implementación. El escalado de modelo y la corrección son conceptos separados: en tier máximo se corrige y revalida sin afirmar un escalado inexistente.

### Plan y autonomía

- `plan.md` siempre precede a cambios funcionales.
- Si el usuario pidió implementar, se continúa tras el plan salvo que exista una decisión material abierta, un riesgo sensible sin aprobar o una petición explícita de "solo plan".
- Security Advisor `[NO]` obliga a enmendar el plan y obtener un `[YES]` nuevo antes de implementar.

### Routing de capacidad

- Se mantienen los tiers `trivial`, `standard` y `complex` con señales objetivas.
- La política hablará de capacidad requerida, no de un modelo concreto que el runtime quizá no permita seleccionar.
- Solo se afirmará una selección de modelo cuando la herramienta realmente la soporte.

### Artefactos

- Misión ligera: `plan.md`, `execution.md` y `verification.json`.
- Misión completa: añade `artifacts/`, `CHANGELOG.md` y documentación/knowledge cuando corresponda.
- `diff.patch` pasa a ser opcional porque Git es la fuente canónica del diff.
- La evidencia versionada será concisa: salida final, RED relevante y diagnósticos que expliquen decisiones. Se evitarán logs repetitivos completos; los artefactos grandes deberán resumirse o comprimirse.
- Se usará `execution.md` y evidencias `.txt`/`.json` para no colisionar con el `*.log` de `.gitignore`.

### Verificación

- El ejemplo será JSON válido.
- Cada check tendrá `pass`, `fail` o `skipped`; todo skip requerirá justificación.
- `passed` exige cero fallos y que los skips sean explícitamente aceptables para el alcance.
- Se registrarán comando, resultado, evidencia, entorno, base/commit y tier efectivo cuando sea posible.
- Para Odoo se usará `docker-compose.local.yml`; en worktrees se montará el código aislado mediante overlay y se restaurará el servicio original al finalizar.
- Toda fixture o usuario temporal se limpiará o archivará y la restauración formará parte de la evidencia.

### Seguridad y publicación

- Se mantienen los disparadores de Security Advisor para autenticación, concurrencia, migraciones, secretos/despliegue y borrado histórico.
- Se añade que permisos de UI nunca sustituyen controles de servidor.
- Una autorización de push cubre una única publicación, al remoto/rama y alcance indicados. Cualquier cambio material posterior requiere un OK nuevo.
- Commit, push y PR se distinguen expresamente; autorizar uno no autoriza automáticamente los demás.

### Knowledge base

- La ubicación canónica será `.agents/knowledge/odoo_development_modding/artifacts/`.
- Solo se persistirán aprendizajes reutilizables; no se crearán entradas vacías o resúmenes duplicados.

## Archivos previstos

- Modificar `AGENTS.md`.
- Crear los artefactos de misión bajo `missions/improve-agents-md/`.
- No modificar módulos Odoo ni configuración de runtime.

## Criterios de aceptación

- No quedan placeholders editoriales.
- TDD, review y validación independiente tienen propietarios inequívocos.
- Todos los gates y bucles de corrección están definidos.
- El ejemplo de verificación parsea como JSON.
- Las reglas de evidencia son compatibles con `.gitignore`.
- Worktrees, compose, cleanup y publicación tienen contratos verificables.
- Las reglas conservan la prohibición de push a `Dev_iRG` sin autorización explícita nueva.
