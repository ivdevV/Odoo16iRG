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
