# Micro-spec: irg_diplomado_fixed_batch_period

## Contexto

El asistente de confirmacion manual estaba previsualizando Diplomados como modalidad `HC` y aplicando reglas mensuales/de verano propias de masteres HomeClass. El negocio define que los Diplomados no son masteres: para cada anio deben usar un unico lote fijo del 28 de junio al 30 de septiembre.

## Alcance

- Crear un modulo nuevo por herencia en `addons-extra/extrairg/`.
- Detectar Diplomados por codigo de categoria `DI`/`D`, nombre de categoria con `DIPLOMADO`, o nombre de producto con `DIPLOMADO`.
- Mostrar la modalidad del wizard como `Diplomado` para evitar confundirla con masteres HC.
- Generar/previsualizar un unico codigo anual `DI<codigo_curso>HC<yy>09`.
- Crear el lote real con `start_date = 28/06/<anio>`, `end_date = 30/09/<anio>` y `date_start_class = 28/06/<anio>`.
- Delegar cualquier linea no Diplomado en la logica actual, sin alterar masteres HC ni ONL.

## Fuera de alcance

- Cambiar la nomenclatura historica del codigo de lote que incluye `HC`.
- Modificar directamente `irg_sale_manual_confirmation_wizard` o `irg_openeducat_sale_lote_custom`.
- Cambiar plantillas de bienvenida o reglas de portal.

## Validacion esperada

- Prueba de wizard: Diplomado con fecha 28/06/2026 muestra modalidad `Diplomado` y lote `DINEHC2609`.
- Prueba de lote real: el lote `DINEHC2609` se crea con fechas 28/06/2026 a 30/09/2026.
- Prueba de no regresion: un producto Master no se marca como `Diplomado` ni usa codigo `DI...`.
