# Mision: fix-irg-generacion-diplomados-layout

## Alcance

- Revisar el modulo `irg_generacion_diplomados`.
- Corregir el reporte PDF de diplomados para que la plantilla ocupe la pagina completa.
- Mantener el nombre del diplomado con la capitalizacion original de la plantilla/dato, sin forzar mayusculas.
- Recuadrar el reverso para evitar solapes entre listado de modulos y encabezados.

## Fuera de alcance

- Cambios funcionales en el wizard, modelos o seguridad.
- Modificacion de modulos nativos de Odoo.
- Cambios en datos historicos o migraciones.

## Contexto recuperado

- `.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`: los modulos custom viven en `addons-extra/extrairg/` y no se deben modificar modulos nativos; se deben usar cambios acotados y probar logica critica.
- `.agents/workflows/odoo16_codebase_knowledge.md`: confirma el uso de la knowledge base del proyecto como referencia para tareas Odoo.

## Clasificacion de complejidad

- Tier: `standard`.
- Justificacion: cambio localizado en 1 reporte XML y posiblemente pruebas, pero afecta renderizado PDF QWeb/wkhtmltopdf y comportamiento visual de dos paginas; no toca autenticacion, concurrencia, migraciones, secretos ni borrado de datos.

## Modelo por fase

- Plan: orquestador con modelo de razonamiento alto.
- Implementacion: tier `standard`, cambios minimos en QWeb/CSS.
- Validacion: inspeccion estatica XML, diff, y pruebas disponibles si el entorno Odoo lo permite.
- Documentacion: ligera, registrar changelog y aprendizajes reutilizables.

## Plan de implementacion

1. Inspeccionar plantilla QWeb, accion de reporte y recursos `static`.
2. Ajustar layout full-bleed evitando margenes del layout web y usando contenedores con dimensiones A4 landscape reales.
3. Eliminar `text-transform: uppercase` del nombre del diplomado.
4. Rehacer el reverso con una zona de contenido centrada que distribuya secciones sin solapes.
5. Validar XML/diff y registrar evidencia en `verification.json`.
