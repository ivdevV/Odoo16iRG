# Plan de misión: oficialidad-webhook

## Objetivo y alcance

Crear el módulo nuevo `addons-extra/addons_uisep/irg_admission_oficialidad_webhook`
para enviar a n8n, desde un wizard abierto en `op.admission.register`, las admisiones
seleccionadas y la serialización completa de sus registros `op.admission`,
`op.student` y `res.partner`. El envío usa `urllib`, parámetros de sistema y Bearer
token; solo una respuesta HTTP 2xx marca `oficialidad_sent_date`.

La especificación aprobada por el usuario es `/Users/ivrogo/Downloads/00-spec.md` y
el plan detallado de referencia es `/Users/ivrogo/Downloads/01-plan.md`. Esta misión
adopta ambos documentos y resuelve la implementación como un módulo nuevo, sin
modificar módulos Odoo existentes.

## Contexto recuperado

- `.agents/workflows/odoo16_codebase_knowledge.md` obliga a consultar la knowledge
  base del proyecto.
- `.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`
  confirma los patrones `_inherit`, `xpath`, prefijo `irg_`, traducciones y revisión
  explícita de ACL/sudo.
- La ubicación `addons-extra/addons_uisep/` prevalece sobre la recomendación genérica
  `addons-extra/extrairg/` porque la especificación del usuario la fija expresamente
  y el módulo extiende OpenEducat siguiendo el patrón de `isep_admission_csv_export`.
- El servicio de referencia es
  `addons-extra/extrairg/irg_mail_n8n_webhook/models/irg_mail_n8n_service.py`.

## Clasificación y routing

- Tier: `complex`.
- Justificación objetiva: se crean más de cinco archivos, se integran modelos,
  vistas, wizard, ACL, parámetros, transporte HTTP y tests Odoo; además se maneja un
  token de autenticación y configuración de despliegue.
- Orquestador/Plan: agente principal, máxima capacidad disponible.
- Implementación: subagente codificador especializado en Odoo 16, tier `complex`,
  aplicando TDD.
- Seguridad: Security Advisor de alta capacidad, obligatorio por token/configuración.
- Validación: subagente testeador independiente, tier `standard`, con escalado a
  `complex` si `verification.json` falla.
- Documentación: subagente documentador ligero tras validación `passed`.
- Limitación: la API de subagentes de esta sesión no permite seleccionar un modelo
  por nombre; se usarán los roles anteriores con el modelo equivalente asignado por
  la plataforma.

## Fases

1. Preparación: trabajar en el worktree aislado sobre la rama
   `feat/oficialidad-webhook`, creada desde `origin/Dev_iRG` actualizado.
2. Implementación TDD: escribir primero la suite Odoo que cubre precarga, payload,
   serialización robusta, marcado 2xx, no-2xx, configuración ausente y selección
   vacía; confirmar RED cuando el runtime local lo permita; implementar el módulo
   mínimo hasta GREEN.
3. Revisión de seguridad: comprobar que el token no se registra ni se incluye en el
   payload, que no se añaden secretos reales, que `sudo()` se limita a lectura de
   configuración, que los errores truncan cuerpos remotos y que no se envían blobs.
4. Validación independiente: ejecutar criterios estáticos, instalación/actualización
   y tests contra `docker-compose.local.yml` y `test_irg_db`; guardar evidencia en
   `artifacts/` y emitir `verification.json`.
5. Documentación: actualizar README/changelog del módulo, `execution.log`,
   `diff.patch` y knowledge base con decisiones y gotchas reutilizables.

## Archivos previstos

- Módulo nuevo bajo
  `addons-extra/addons_uisep/irg_admission_oficialidad_webhook/` con manifest,
  inicializadores, modelos, wizard, vistas, datos, seguridad, tests y README.
- Artefactos en `missions/oficialidad-webhook/`.
- Entrada de knowledge base en
  `.agents/knowledge/odoo_development_modding/artifacts/`.

## Contrato de cierre

La misión solo se cerrará si `missions/oficialidad-webhook/verification.json` tiene
`status: passed` y todos los checks aplicables pasan. No se hará push ni se integrará
en `Dev_iRG` sin un OK explícito nuevo del usuario.
