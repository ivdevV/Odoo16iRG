# Mision: refine-irg-diplomados-pdf-position

## Alcance

- Reajustar el reporte PDF de `irg_generacion_diplomados` usando como referencia el PDF generado por el usuario.
- Bajar el contenido principal para que no quede pegado arriba.
- Evitar solapes entre logo, textos superiores y encabezados del reverso.
- Mantener el diploma en dos paginas A4 landscape con fondo a pagina completa.

## Fuera de alcance

- Cambios de modelos, wizard, permisos o datos.
- Cambios en `AGENTS.md`.
- Commit o push remoto.

## Clasificacion de complejidad

- Tier: `standard`.
- Justificacion: cambio visual localizado en un reporte QWeb ya existente, pero afecta renderizado PDF y requiere ajustar posiciones con evidencia del PDF generado.

## Plan

1. Inspeccionar el PDF generado y la plantilla QWeb actual.
2. Eliminar o recolocar el texto duplicado que se pisa con el logo.
3. Bajar el bloque de contenido del anverso y el reverso.
4. Ajustar tamanos/posiciones de logo, titulo, firmas y secciones para ocupar mejor la hoja.
5. Validar XML y registrar evidencia.
