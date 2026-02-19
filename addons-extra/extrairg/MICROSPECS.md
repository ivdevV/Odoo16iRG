Microspecs — Spec-Driven Development (light)

Objetivo
- Definir un proceso ligero para elaborar planes de desarrollo (microspecs) para módulos Odoo.

Regla de ubicación
- Todos los nuevos módulos Odoo se crearán en `addons-extra/extrairg`.

Proceso (light)
1. Propósito breve: 1-2 frases que expliquen el objetivo del módulo.
2. Alcance mínimo (MVP): lista corta de funcionalidades imprescindibles.
3. Entregables:
   - Archivos: `__manifest__.py`, `__init__.py`, `models/`, `views/`.
   - Opcional pero recomendado: `security/ir.model.access.csv`, `README.md`, `tests/`, `data/`.
4. Dependencias: enumerar módulos Odoo que debe declarar `depends` en el manifest.
5. Interfaces: vistas, reportes, controladores web públicos, assets.
6. Criterios de aceptación (QA): casos de uso mínimos y pasos de verificación.
7. Tareas de implementación: dividir en subtareas técnicas (modelos, vistas, seguridad, tests).
8. Lanzamiento: pasos para instalar/actualizar el módulo en el entorno (reinicio, actualizar módulo).

Hardening mínimo obligatorio (anti-rotura)
1. Validación XML/QWeb:
   - Evitar atributos con namespace no declarado en XML (ej.: `x-on:click`, `x-bind:class`) porque rompen el parser de Odoo.
   - En vistas Odoo usar atributos XML-safe (ej.: `x-data`, `x-model`, `x-show`) o mover lógica compleja a JS propio en `static/src/js`.
   - No mezclar sintaxis JS/templating que genere XML inválido dentro de atributos.
2. XPaths robustos:
   - Heredar vistas con `inherit_id` y `xpath` estables (anclas semánticas, no frágiles).
   - Si se reemplaza un bloque crítico (pdf viewer, player, etc.), definir fallback explícito.
3. Payloads dinámicos:
   - Si se guarda JSON en `fields.Text`, validar estructura en backend (create/write o constrains).
   - Sanitizar HTML antes de `t-raw`.
4. Assets frontend:
   - Registrar librerías en `web.assets_frontend`.
   - Si se usa CDN, dejar inicialización defensiva (`if (window.lib) ...`).
5. Instalación segura:
   - Probar instalación limpia (`-i`) y actualización (`-u`) del módulo en entorno de pruebas.
   - Criterio de salida: sin `RPC_ERROR` ni `XMLSyntaxError`.

Puerta de revisión técnica (obligatoria antes de merge)
1. Revisión estática:
   - Verificar sintaxis de XML/Python y orden de carga en `data` del manifest.
2. Revisión funcional mínima:
   - Caso normal + caso borde principal (p.ej. JSON vacío o inválido).
3. Revisión de integración:
   - Confirmar que el override de template no rompe el render por defecto.
4. Evidencia:
   - Adjuntar en la PR: captura/log corto de instalación/upgrade y checklist marcada.

Notas prácticas
- Nombre del módulo: usar prefijo `irg_` para módulos locales.
- Estructura: colocar Python en `models/` y JS/CSS en `static/`.
- Manifest: incluir `data` y `demo` necesarios; mantener `installable: True`.
- Seguridad: siempre añadir `ir.model.access.csv` si se crean modelos nuevos.

Uso
- Crear este archivo al empezar un nuevo módulo y enlazarlo desde la issue/ticket correspondiente.
- Enlazar también `MICROREVIEW_CHECKLIST.md` en cada PR para estandarizar revisiones.
