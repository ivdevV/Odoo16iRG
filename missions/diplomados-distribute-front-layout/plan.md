# Mision: diplomados-distribute-front-layout

## Alcance

- Corregir el anverso del diploma para que no se perciba como un bloque central comprimido.
- Distribuir vertical y horizontalmente la composicion para aprovechar mejor la hoja.
- Reducir firmas e imagenes de firma a un tamano razonable y evitar solapes.
- Mantener el reverso y la logica del modulo sin cambios.

## Fuera de alcance

- Cambios en modelos, wizard, datos, permisos, `AGENTS.md` o paperformat.
- Commit o push a `Dev_iRG` sin OK explicito posterior del usuario.

## Clasificacion de complejidad

- Tier: `standard`.
- Justificacion: cambio visual localizado en QWeb con validacion Odoo local; no toca seguridad, datos, migraciones ni concurrencia.

## Delegacion

- Analisis: subagente explorador para proponer medidas del anverso.
- Implementacion: subagente codificador `general`.
- Validacion: subagente tester `general` usando `docker-compose.local.yml`.

## Plan

1. Revisar el QWeb actual y el feedback visual.
2. Redistribuir el anverso: logo arriba, texto central mas extendido, firmas mas bajas/separadas y de menor tamano.
3. Mantener el reverso sin cambios.
4. Validar XML, whitespace y carga del modulo con `docker-compose.local.yml`.
5. Registrar evidencia en `verification.json`.
