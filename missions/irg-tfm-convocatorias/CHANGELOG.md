# Changelog — irg_tfm_convocatorias

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
