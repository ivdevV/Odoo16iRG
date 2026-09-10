# Plan de implementación — Esquema TFM como encuesta versionada

## Clasificación y alcance

- Nivel de misión: `full`.
- Tier funcional: `complex`.
- Motivo: añade modelos y datos, integra Encuestas con portal y `tesis.model`,
  introduce rutas autenticadas, versionado inmutable, concurrencia, permisos y
  compatibilidad con datos históricos; afecta más de cinco archivos y superficies
  web/backend.
- Addon objetivo: `addons-extra/extrairg/irg_tfm_convocatorias`.
- Rama aislada: `codex/tfm-outline-survey`.
- Base: `b38baaf04359b4a0c9db3c765a1a986afc406940`
  (`origin/Dev_iRG`).
- Especificación aprobada:
  `docs/superpowers/specs/2026-09-09-tfm-outline-survey-design.md`.
- Fuera de alcance: Entrega parcial, Entrega final, fechas de convocatoria,
  activación al 50 % y reglas eLearning, salvo la integración mínima necesaria
  para conservar su comportamiento.
- Publicación: implementar no autoriza commit, push ni PR. Cada acción requiere
  autorización nueva, independiente y explícita.

## Conocimiento consultado

- `.agents/knowledge/odoo_development_modding/artifacts/irg_survey_txt_import_options_and_score_recalculation.md`:
  las pruebas de encuesta no deben depender de puntuaciones exactas cuando
  conviven extensiones de exámenes. Esta encuesta será no evaluable.
- `.agents/knowledge/odoo_development_modding/artifacts/odoo_qweb_xpath_parent_shape.md`:
  cualquier herencia QWeb se contrastará con la estructura real del padre y el
  control visual no sustituirá autorización server-side.
- `.agents/knowledge/odoo_development_modding/artifacts/irg_course_completion_progress.md`:
  se preservan `completion_porc` y los disparadores de activación existentes; no
  se amplía esa lógica.
- Formulario portal de referencia:
  `irg_practice_request_student_profile/views/practice_request_portal_templates.xml`.
  Se replica el patrón de pasos con varias preguntas, adaptándolo para guardar
  borradores persistentes.
- API oficial Odoo 16 consultada en `addons/survey`: se reutilizarán únicamente
  `survey.survey`, `survey.question` y `survey.question.answer` como plantilla
  editable. No se crearán `survey.user_input` ni `survey.user_input.line`.

## Criterios de aceptación

1. Se instala/actualiza una única encuesta global **Esquema preliminar y
   orientador del TFM**, editable desde Encuestas y cargada como `noupdate`.
2. La plantilla inicial contiene tres secciones y las diez preguntas aprobadas,
   con tipos, ayudas, opciones y obligatoriedad correctos.
3. Nombre, correo y máster provienen de la matrícula exacta del expediente, pero
   el alumno puede editarlos antes de enviar.
4. El portal muestra tres pasos con varias preguntas por paso, no una pregunta
   por página.
5. **Siguiente** y **Guardar borrador** persisten respuestas y paso actual; al
   regresar se reanuda el único borrador del expediente.
6. El borrador congela texto, ayuda, tipo, opciones, orden y paso al iniciarse;
   editar la plantilla solo afecta a borradores nuevos.
7. **Revisar y enviar Esquema** valida todas las obligatorias, crea una versión
   correlativa y vuelve inmutable la copia congelada y sus respuestas.
8. Antes de convocatoria se permiten varias versiones completadas. Después de
   asignarla no se puede iniciar, guardar ni finalizar; retirarla reabre el
   borrador o permite crear otro.
9. El alumno ve sus versiones y respuestas; el revisor TFM las abre desde
   `tesis.model`. Las respuestas parciales del borrador no se exponen al revisor.
10. Los Esquemas históricos en archivo siguen visibles en lectura y cuentan para
   la advertencia no bloqueante de convocatoria. Las entregas parcial/final no
   cambian.
11. Toda ruta comprueba en servidor usuario, matrícula, expediente, cuestionario,
    sección y estado; peticiones cruzadas devuelven recurso no encontrado.
12. Una revisión correlativa evita que una pestaña obsoleta sobrescriba un
    guardado más reciente.
13. Las versiones terminadas y snapshots no admiten edición, borrado ni copia.
14. No se crean `survey.user_input`, tokens, correos, invitaciones ni enlaces
    anónimos.

## Riesgos y controles previos

- Autorización/IDOR: resolver siempre mediante
  `res.users → op.student → op.student.course → tesis.model`; nunca aceptar un
  `user_input_id` aislado como prueba de propiedad.
- Carrera con convocatoria: centralizar el orden de bloqueo compatible con el
  addon actual —convocatoria vigente cuando exista, curso y expediente— y releer
  matrícula, convocatoria y borrador antes de guardar o finalizar.
- Dos pestañas: enviar `revision` como campo oculto, compararla y aumentarla bajo
  lock; una revisión antigua falla sin sobrescribir.
- Versiones duplicadas: constraint SQL y asignación correlativa bajo lock; una
  colisión se reintenta una sola vez mediante savepoint.
- Plantilla editada durante un borrador: al crear el borrador se congelan texto,
  ayuda, tipo, obligatoriedad, orden, paso y opciones en modelos TFM propios. La
  finalización valida esa copia; el borrador y la versión nunca dependen de la
  plantilla viva.
- Rutas nativas de Encuestas: no crear `survey.user_input`; usar Survey solo como
  plantilla editable elimina el canal alternativo por token público.
- Configuración inválida: las secciones llevan claves estables `proposal`,
  `approach`, `results`; se exige exactamente una de cada una y un único campo de
  cada origen automático. Tipos no soportados se rechazan de forma segura.
- Elevación con `sudo()`: limitarla a búsquedas/creación imprescindibles después
  del gate de propiedad; no devolver recordsets ajenos a QWeb.
- Compatibilidad: no migrar ni modificar `irg.tfm.entrega(stage='outline')`.
- Acceso del revisor: crear grupo **Revisor TFM**; solo él puede leer versiones
  terminadas/respuestas y la vista oculta borradores. Gestionar Encuestas no
  concede acceso implícito a respuestas TFM.
- Límites/salida: máximo 500 caracteres para `char_box`, 20.000 para `text_box`,
  100 opciones configuradas y 50 seleccionadas por pregunta, 100 preguntas por
  plantilla y 100.000 caracteres textuales por Esquema. Se exige pertenencia
  exacta de opciones y `t-esc` para cualquier texto del alumno.
- Chatter sin correo: crear una fila `mail.message` interna y no notificable de
  forma directa, sin `message_post`, con solo versión/fecha y sin respuestas.
  Probar que finalizar no crea `mail.notification`, destinatarios ni `mail.mail`.
- Security Advisor: la primera ronda emitió `[NO]`. Este plan incorpora sus seis
  bloqueantes y controles adicionales; TDD sigue bloqueado hasta obtener `[YES]`.

## Archivos previstos

- Modificar:
  - `__manifest__.py`
  - `models/__init__.py`
  - `models/tesis_model.py`
  - `controllers/portal.py`
  - `views/tfm_portal_templates.xml`
  - `views/tesis_model_views.xml`
  - `security/ir.model.access.csv`
  - `tests/__init__.py`
- Crear:
  - `data/tfm_outline_survey.xml`
  - `models/irg_tfm_esquema.py`
  - `models/survey_question.py`
  - `models/res_config_settings.py`
  - `security/irg_tfm_security.xml`
  - `views/survey_tfm_views.xml`
  - `views/res_config_settings_views.xml`
  - `tests/test_tfm_outline_survey.py`
- Documentación posterior a gates:
  - guía del addon y changelog de misión;
  - knowledge solo si aparece un patrón reutilizable no documentado.

## Plan TDD y de implementación

### Tarea 1 — Contrato de plantilla y configuración

1. Añadir tests RED que exijan dependencia `survey`, encuesta `noupdate`, tres
   secciones con claves técnicas, diez preguntas, opciones y tres orígenes de
   prerrelleno únicos.
2. Ejecutar el validador estático/AST/XML disponible y conservar la evidencia RED.
3. Implementar datos, extensión de `survey.question`, configuración global y
   validación del contrato mínimo de plantilla.
4. Ejecutar GREEN y refactorizar manteniendo GREEN.

### Tarea 2 — Borrador, respuestas y snapshot inmutable

1. Añadir tests RED de creación/reanudación del borrador, congelación de plantilla,
   prerrelleno editable, guardado por paso, versión correlativa, inmutabilidad,
   unicidad, revisión obsoleta y concurrencia.
2. Implementar `irg.tfm.esquema`, `irg.tfm.esquema.pregunta` y
   `irg.tfm.esquema.opcion`, helpers privados de guardado/finalización y
   constraints. Survey se usa solo como plantilla; no se crea `survey.user_input`.
3. Integrar `tesis.model`: relaciones, conteo de Esquema válido, registro interno
   no notificable al enviar una versión y advertencia compatible con archivos
   históricos.
4. Ejecutar GREEN y refactorizar manteniendo GREEN.

### Tarea 3 — Portal de tres pasos y aislamiento

1. Añadir tests RED HTTP/contratos de rutas para iniciar, mostrar, guardar,
   avanzar, retroceder, revisar, enviar y consultar versiones.
2. Cubrir propiedad exacta, CSRF, revisión obsoleta, secciones/preguntas/opciones
   manipuladas, convocatoria concurrente, alumno ajeno, límites de tamaño,
   escape de salida y formulario configurado incorrectamente.
3. Implementar controladores POST autenticados y QWeb de tres pasos con múltiples
   preguntas, indicadores, errores de campo, resumen y navegación segura.
4. Sustituir solo la subida nueva del Esquema; conservar el bloque separado de
   archivos históricos y los formularios de Entrega parcial/final.
5. Ejecutar GREEN y refactorizar manteniendo GREEN.

### Tarea 4 — Vista del revisor y seguridad declarativa

1. Añadir tests RED de ACL/vistas: grupo Revisor TFM, lectura solo de versiones
   terminadas, sin create/write/unlink/copy directos, pestaña Esquemas y ausencia
   de respuestas de borrador.
2. Implementar grupo, reglas/ACL mínimas, vistas read-only y botón
   **Ver respuestas**.
3. Exponer claves de paso, marca de prerrelleno y configuración global solo a los
   grupos internos adecuados.
4. Ejecutar GREEN y comprobar XML/manifest/imports.

### Tarea 5 — Regresión integral

1. Ejecutar pruebas estáticas, `compileall`, parseo XML, `git diff --check` y los
   tests puros disponibles sin Docker.
2. Verificar que no cambian ventanas/archivos de parcial/final, activación,
   eLearning, rutas legacy neutralizadas ni historial de archivos outline.
3. Ejecutar búsqueda de secretos, rutas públicas, `survey.user_input`, `t-raw`,
   correos/notificaciones generados y uso inseguro de `sudo()`.

## Gates independientes

### Review de código

Un revisor distinto del codificador inspeccionará el diff funcional y pruebas:
requisitos, APIs Odoo 16, seguridad, concurrencia, inmutabilidad, compatibilidad,
QWeb y alcance. Cualquier hallazgo bloqueante reabre Implementación/TDD.

### Validación

Un validador distinto del codificador repetirá desde cero los checks disponibles
y emitirá `verification.json` con comandos, resultados y evidencia. No editará
código de producción.

- `python_compile`: obligatorio.
- `xml_manifest_acl_contracts`: obligatorio.
- `static_tdd_contracts`: obligatorio.
- `git_diff_check`: obligatorio.
- `odoo_module_tests`: `skipped` justificado; el usuario prohibió Docker en este
  equipo y no existe otro runtime Odoo/PostgreSQL autorizado.
- `integration_http`: `skipped` por la misma limitación.
- `e2e_testsprite`: activado por controladores/QWeb, pero `skipped` justificado;
  la política exige runtime local Docker y prohíbe beta/producción. No se abrirá
  Docker ni se tunelará beta.

El estado podrá ser `passed` solo si no hay fallos y todos los skips contienen la
justificación anterior sin afirmar cobertura runtime inexistente.

## Documentación y entrega

Después de Review y Validación satisfactorias:

1. Actualizar guía de configuración: instalar/actualizar, localizar la encuesta,
   editar secciones/preguntas, probar como alumno y consultar como revisor.
2. Añadir changelog con compatibilidad y pasos de despliegue.
3. Persistir knowledge únicamente si surge un patrón reutilizable nuevo.
4. Realizar comprobación final acotada de Git y coherencia de artefactos.
5. Detenerse sin commit, push ni PR. Solicitar autorización específica si el
   usuario quiere cualquiera de esas acciones.
