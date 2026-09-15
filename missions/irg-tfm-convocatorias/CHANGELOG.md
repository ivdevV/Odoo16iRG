# Changelog — irg_tfm_convocatorias

## 16.0.1.0.4 — 2026-09-09

### Corregido

- **Secciones Online** permite asignar **Convocatorias TFM** a categorías del
  clon desde el canal base, sin habilitar la creación, el borrado ni la edición
  de otros datos del contenido.
- El canal Online puede recuperarse cuando un clon antiguo conserva únicamente
  el enlace inverso hacia su HomeClass, siempre que exista un solo candidato
  exacto.
- La selección del canal falla cerrada ante relaciones ambiguas, inconsistentes
  o autorreferenciadas y no recorre familias transitivas.
- Los usuarios externos no pueden modificar las convocatorias de una categoría
  mediante llamadas directas al servidor.
- Se añadió cobertura específica del lote real `MOPCONL2606` para verificar que
  el alumno es dirigido al canal Online y recibe la membresía correcta.

### Validación

- Security Advisor aprobó la resolución exacta y los controles server-side.
- Review independiente aprobada tras corregir el caso de autorenlace.
- Validación independiente `passed`: 13 grupos, 77 pruebas estructurales, 39
  contratos, compilación, XML/XPath y alcance Git sin fallos.
- Odoo/PostgreSQL/TestSprite no se ejecutaron porque el usuario prohibió usar
  Docker en este equipo; no se afirma un resultado de runtime o E2E.

## 16.0.1.0.3 — 2026-09-08

### Corregido

- La matrícula TFM decide el canal efectivo: los lotes Online elegibles abren el
  clon Online y los lotes HomeClass/Neurologopedia abren el canal base, sin usar
  admisiones ajenas como señal de modalidad.
- Las rutas de canal y material fallan cerradas ante expediente ambiguo, lote
  PRS/desconocido, clon ausente o relaciones base/Online inconsistentes.
- Se conserva la redirección Online existente para cursos no TFM y, en TFM, se
  mantienen las restricciones de fecha, lote, prácticas, morosidad y requisitos.
- Las membresías creadas por TFM ya no disparan la réplica automática V2 y se
  reconcilian al sustituir, desvincular, reparar o borrar un canal de la familia.
- Los clones heredan la convocatoria únicamente desde una categoría HomeClass
  válida; una referencia de origen inválida no se interpreta como contenido común.
- La pestaña backend **Entregas TFM** muestra etapa, versión, archivo, comentario,
  convocatoria, autor y fecha en lugar de mostrar solamente el ID.
- En expedientes del flujo nuevo se ocultan la fase y los documentos legacy.
- La categoría creada desde **Secciones iRG** conserva `Es una categoría`, por lo
  que permite guardar **Convocatorias TFM** sin el error de validación observado.
- El portal muestra fechas `dd/mm/aaaa` y renombra el acceso eLearning a
  **Guía y recursos para el TFM**.

### Validación

- Security Advisor aprobado después de enmendar aislamiento y lifecycle.
- Review independiente aprobada sin hallazgos Critical, Important ni Minor.
- Validación independiente `passed`: 13 grupos, 70 pruebas estructurales, 35
  contratos, XML/manifiesto, compilación y alcance Git sin fallos.
- Odoo/PostgreSQL/TestSprite no se ejecutaron por la prohibición expresa de usar
  Docker en este equipo; no se afirma un resultado de runtime o E2E.

## 16.0.1.0.2 — 2026-09-07

### Corregido

- Corregido el XPath QWeb del listado eLearning: `website_slides.course_slides_list_slide` usa un elemento raíz `li`, no un `div`.
- La condición de convocatoria se aplica ahora al contenedor completo del material, ocultando también iconos, badges y controles.
- Añadido un contrato de regresión contra la estructura relevante del padre oficial de Odoo 16.

### Validación

- Review independiente aprobada sin observaciones Critical, Important ni Minor.
- Validador independiente aprobado: siete XML válidos, XPath con una coincidencia exacta y 20 contratos estáticos.
- La instalación real en Odoo queda pendiente de repetirse en beta; no se utilizó Docker en este equipo.

## 16.0.1.0.1 — 2026-09-07

### Corregido

- Sustituida la referencia inexistente `completion_proc` por el campo real calculado `op.student.course.completion_porc`.
- Declaradas las dependencias directas `isep_student_filter` e `isep_gradebook`, de modo que el campo y la libreta estén disponibles antes del hook de instalación.
- Adaptado el cron para evaluar en Python un progreso que no está almacenado ni admite dominios SQL.
- Añadida la reevaluación inmediata tras crear, modificar o eliminar calificaciones, con recálculo persistido de la nota final, invalidación de caché y bloqueo ordenado por matrícula.
- Corregidos los fixtures de prueba para no escribir un campo calculado y añadida cobertura del proveedor real y del cruce del 50 % desde una nota de examen.

### Validación

- Review independiente aprobada sin hallazgos Critical ni Important.
- Validador estático independiente aprobado: 13 grupos, 18 archivos Python, 55 pruebas estructuradas y 19 contratos.
- Odoo/PostgreSQL/TestSprite no se ejecutaron por la prohibición expresa de usar Docker en este equipo; no se afirma validación de runtime.

## 16.0.1.0.0 — 2026-09-07

### Añadido

- Activación automática e irreversible de un expediente `tesis.model` al alcanzar el 50 % en cursos y lotes elegibles.
- Cortes diferenciados para HomeClass (`HC2511`), Neurologopedia (`MONLHC2601`) y Online (`ONL2602`), con exclusión presencial `PRS`.
- Activación inmediata y cron horario acotado, idempotente y protegido contra concurrencia.
- Catálogo global `irg.tfm.convocatoria` con código único, estado y ventanas para Entrega parcial y Entrega final.
- Flujo MyCampus **Trabajo Final de Máster** con Esquema previo, Entrega parcial, Entrega final e historial versionado.
- Integración por curso con un canal TFM y categorías eLearning comunes o exclusivas por convocatoria.
- Membresías eLearning con procedencia por expediente para preservar accesos creados por otros procesos.
- Excepciones internas versionadas, con motivo obligatorio y trazabilidad en chatter.

### Cambiado

- El nuevo flujo reemplaza las secciones heredadas 1–5 por Esquema, Entrega parcial y Entrega final.
- La asignación de convocatoria cierra el Esquema y habilita fechas/contenido; retirarla revierte esos accesos sin borrar el historial.
- La visibilidad eLearning combina convocatoria con los filtros existentes de lote y prácticas.
- La creación automática suprime de forma contextual el correo heredado de `isep_tesis_model`; el nuevo flujo no añade correos automáticos.
- La entrada heredada **Revisión de tesis** se elimina de `/my`; el acceso del alumno queda integrado en cada curso de MyCampus.

### Seguridad

- Ownership portal fail-closed desde usuario hasta matrícula, expediente, entrega y adjunto.
- Mutaciones por `POST` con CSRF y autorización interna comprobada antes de cualquier elevación de privilegios.
- Validación server-side de tamaño, extensión, MIME y formato real PDF/DOC/DOCX, con límites contra archivos ZIP/DOCX hostiles.
- Adjuntos privados ligados a una única entrega, descarga reautorizada e historial completamente inmutable.
- Serialización de asignaciones y subidas con orden global de locks, relectura de configuración y constraints PostgreSQL.
- Denegación de contenidos eLearning exclusivos antes de ejecutar el controlador padre, incluida la navegación por URL directa.
- Neutralización completa de las rutas legacy de consulta, mutación, descarga y borrado.

### Validación

- Review independiente final aprobada sin hallazgos abiertos.
- Validador estático reproducible aprobado para Python, XML, ACL, manifest, imports, tests, helpers y contratos funcionales/de seguridad.
- Tests Odoo, integración PostgreSQL y TestSprite no ejecutados en esta máquina por la prohibición expresa de usar Docker y la ausencia de TestSprite MCP; no se afirma resultado de runtime ni E2E.
