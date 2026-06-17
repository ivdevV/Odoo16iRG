# Mision: diplomados-enlarge-page-composition

## Alcance

- Ampliar visualmente la composicion del anverso del diploma de `irg_generacion_diplomados`.
- Reducir la sensacion de margen interno: logo, textos, titulo y firmas deben ocupar mas superficie util de la hoja.
- Mantener fondo full-page y reverso en dos columnas.
- Mantener cambios limitados al reporte QWeb y artefactos de mision salvo que el analisis demuestre necesidad puntual.

## Fuera de alcance

- Cambios en modelos, wizard, datos, permisos o `AGENTS.md`.
- Commit o push a `Dev_iRG` sin OK explicito posterior del usuario.

## Clasificacion de complejidad

- Tier: `standard`.
- Justificacion: cambio visual localizado en reporte QWeb con validacion Odoo local; no toca seguridad, datos, migraciones ni concurrencia.

## Delegacion

- Analisis: subagente explorador para revisar el QWeb actual y proponer medidas.
- Implementacion: subagente codificador `general`.
- Validacion: subagente tester `general` usando `docker-compose.local.yml`.

## Plan

1. Revisar el QWeb actual y el feedback visual del usuario.
2. Aumentar tamanos y redistribuir verticalmente el anverso para llenar mas hoja.
3. Evitar cortes por bordes y solapes con firmas/arcos.
4. Validar XML, whitespace y carga del modulo con `docker-compose.local.yml`.
5. Registrar evidencia en `verification.json`.
