# Execution log — irg-tfm-outline-survey

- 2026-09-09: misión clasificada `full`, tier `complex`, por integración
  cross-module con Encuestas, portal, seguridad, concurrencia, versionado e
  historial inmutable.
- 2026-09-09: trabajo aislado en `codex/tfm-outline-survey`, base
  `b38baaf04359b4a0c9db3c765a1a986afc406940` (`origin/Dev_iRG`).
- 2026-09-09: usuario aprobó el diseño funcional y su revisión de tres pasos con
  varias preguntas por pantalla, siguiendo el patrón de solicitud de Prácticas.
- 2026-09-09: consultadas las entradas knowledge sobre Encuestas, XPaths QWeb y
  progreso académico; inspeccionados el formulario portal de Prácticas, el addon
  TFM actual y la API oficial de Survey en Odoo 16.
- 2026-09-09: creados especificación y plan antes de cualquier modificación
  funcional. Pendiente Security Advisor; TDD no puede empezar hasta `[YES]`.
- 2026-09-09: Security Advisor ronda 1 emitió `[NO]`: `survey.user_input` abría
  rutas públicas por token; la plantilla viva podía destruir/reinterpretar
  borradores; faltaban claves estables de paso, grupo de revisor, control de
  guardados obsoletos y orden común de locks. Diseño y plan enmendados para usar
  Survey solo como plantilla, congelar el cuestionario en modelos privados,
  incorporar revisión optimista, grupo Revisor TFM y locks centralizados.
- 2026-09-09: pendiente segunda ronda de Security Advisor; no se ha iniciado TDD
  ni modificado código funcional.
- 2026-09-09: Security Advisor ronda 2 emitió `[NO]` con la arquitectura principal
  ya validada, pero pidió retirar una referencia residual a `survey.user_input`,
  garantizar chatter sin notificaciones y fijar límites numéricos. Se enmendaron
  diseño y plan: Survey queda solo como plantilla; el registro será un
  `mail.message` interno creado directamente; límites de 500/20.000 caracteres,
  100 opciones, 50 selecciones, 100 preguntas y 100.000 caracteres totales.
- 2026-09-09: pendiente tercera ronda de Security Advisor; TDD continúa bloqueado.
- 2026-09-09: Security Advisor ronda 3 emitió `[YES]`; autorizó TDD con Survey
  solo como plantilla, borradores congelados, grupo Revisor TFM, revisión
  optimista, locks comunes, límites objetivos y auditoría no notificable.
- 2026-09-09: TDD RED escrito antes de producción: nueve pruebas Odoo y trece
  contratos estáticos. El validador terminó con exit 1 en la primera ausencia
  esperada (`survey` todavía no figuraba como dependencia). Evidencia:
  `artifacts/tdd-red.txt`. No se usó Docker.
- Restricción vigente: no ejecutar ni abrir Docker en este ordenador. Las pruebas
  Odoo/PostgreSQL/HTTP y TestSprite se registrarán `skipped` con justificación;
  nunca se usarán beta o producción como sustituto.
- Publicación: no existe autorización actual para commit, push ni PR.
- 2026-09-10: implementación completada con Survey únicamente como plantilla,
  snapshots privados versionados, formulario Portal de tres bloques, datos
  precargados editables, vista read-only del revisor y bloqueo del upload legacy.
- 2026-09-10: se añadieron límites de respuesta/plantilla, revisión optimista,
  locks compatibles con entregas, protección de rutas nativas Survey y chatter
  directo no notificable.
- 2026-09-10: la primera Review independiente emitió FAIL por acceso nativo de
  Survey, metadatos ocultos, títulos fijos y un test incompleto. Se corrigieron
  los cuatro puntos y se añadieron pruebas HTTP y de concurrencia.
- 2026-09-10: la segunda Review pidió ampliar cobertura HTTP y sanear errores de
  plantilla. Se completó inicio→guardado→revisión→envío→versión→lectura→cierre
  por convocatoria y se añadió `IrgTfmTemplateError` con log interno y aviso
  genérico.
- 2026-09-10: Review final independiente `PASS`, sin hallazgos bloqueantes.
- 2026-09-10: Validación independiente `PASS`: 16 contratos estáticos,
  compilación Python, XML/manifest/ACL, `git diff --check` y escaneos de
  seguridad. Odoo runtime, HTTP ejecutado y TestSprite quedaron `skipped` por la
  prohibición explícita de Docker y la prohibición de usar beta/producción.
- 2026-09-10: documentación completada en el README del addon, changelog de la
  misión y knowledge reutilizable sobre Survey como plantilla privada.
- 2026-09-10: durante la prueba manual en beta, Odoo 16 rechazó la plantilla
  `tfm_outline_form` porque tres directivas `t-field` estaban aplicadas a nodos
  virtuales `<t>`. Se reprodujo el defecto con un nuevo contrato estático en RED
  y se corrigió usando nodos HTML reales (`strong`, `span` y `div`).
- 2026-09-10: Review independiente de la corrección QWeb `PASS`, sin hallazgos
  bloqueantes. Validación independiente `PASS`: 17 contratos, XML válido,
  compilación Python, ausencia global de `<t t-field>` y `git diff --check`.
  La compilación QWeb dentro de Odoo y E2E continúan omitidos por la prohibición
  explícita de Docker.
- 2026-09-10: la prueba manual posterior mostró un borrador sin convocatoria en
  modo lectura. Las capturas descartaron estado y convocatoria; se trazó la
  condición hasta la clave QWeb genérica `editable` y se confirmó en el código
  oficial de Website 16 que Odoo aporta esa misma variable para el editor web.
- 2026-09-10: TDD RED añadió el contrato
  `portal_avoids_reserved_website_editable_context`; falló antes del cambio. La
  clave se renombró de forma mínima a `tfm_outline_editable` en controlador y
  plantilla. GREEN: 18 contratos. Review independiente `PASS`; validación
  independiente `PASS` en contratos, Python, XML, nombres y diff. Docker no se
  utilizó.
- 2026-09-10: una prueba manual limpia en beta descartó pestañas antiguas y
  reprodujo un conflicto optimista permanente al guardar el primer bloque. El
  código oficial de QWeb 16 confirmó que un atributo dinámico con valor entero
  `0` se omite, por lo que el campo oculto `revision` llegaba vacío en el primer
  guardado.
- 2026-09-10: TDD RED añadió el contrato `rendered_zero_revision` y una HttpCase
  que extrae la revisión del HTML; el contrato falló antes del cambio. Los dos
  formularios serializan ahora la revisión mediante `t-attf-value`, conservando
  explícitamente `value="0"`. GREEN: 19 contratos.
- 2026-09-10: Review independiente del hotfix `PASS`, sin hallazgos bloqueantes.
  Validación independiente `PASS`: 19 contratos, compilación Python, los 11 XML,
  `git diff --check` y alcance. QWeb/HttpCase/E2E en runtime permanecen omitidos
  por la prohibición explícita de Docker.
