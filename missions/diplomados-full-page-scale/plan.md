# Mision: diplomados-full-page-scale

## Alcance

- Resolver que el diploma de `irg_generacion_diplomados` se renderiza visualmente demasiado pequeno dentro de la hoja.
- Aumentar ligeramente el tamano del texto principal del nombre del diplomado.
- Revisar el paperformat y la plantilla QWeb para evitar escalado/margenes no deseados de wkhtmltopdf/Odoo.
- Mantener los cambios limitados al reporte y artefactos de mision.

## Fuera de alcance

- Cambios en modelos, wizard, datos, permisos o `AGENTS.md`.
- Commit o push a `Dev_iRG` sin OK explicito posterior del usuario.

## Clasificacion de complejidad

- Tier: `standard`.
- Justificacion: afecta dos archivos como maximo (`reports/diplomado_report.xml` y `reports/diplomado_templates.xml`) y requiere razonar sobre renderizado Odoo/wkhtmltopdf, pero no toca seguridad, datos, migraciones ni concurrencia.

## Delegacion

- Analisis: subagente explorador para revisar paperformat, QWeb y patrones del repo.
- Implementacion: subagente codificador (`general`) con alcance limitado al reporte.
- Validacion: subagente tester (`general`) usando `docker-compose.local.yml`.

## Plan

1. Revisar paperformat y plantilla actual para localizar la fuente del escalado.
2. Ajustar paperformat/CSS para que el lienzo coincida con A4 landscape sin shrink visual.
3. Usar una tecnica mas robusta para fondo full-page, preferentemente CSS background en el contenedor de pagina.
4. Aumentar ligeramente el texto del nombre del diplomado.
5. Validar XML y carga del modulo en Docker Compose local.
