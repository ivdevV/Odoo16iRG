# Mision: diplomados-back-page-columns

## Alcance

- Corregir el reverso del reporte `irg_generacion_diplomados` para que entren todas las asignaturas.
- Usar columnas y tipografia mas compacta en los listados.
- Reaprovechar mejor la altura de la hoja, evitando que el contenido quede concentrado arriba.
- Mantener el cambio limitado al QWeb del reporte y artefactos de mision.

## Fuera de alcance

- Cambios en modelos, wizard, permisos, datos o `AGENTS.md`.
- Commit o push a `Dev_iRG` sin OK explicito posterior del usuario.

## Contexto

- El PDF generado por el usuario muestra que el reverso corta asignaturas online y deja demasiado espacio en blanco inferior.
- La regla local exige validar con `docker-compose.local.yml` cuando aplique.

## Clasificacion de complejidad

- Tier: `standard`.
- Justificacion: cambio visual localizado en reporte QWeb con validacion local Odoo; no toca autenticacion, concurrencia, migraciones, secretos, despliegue ni borrado de datos.

## Delegacion

- Implementacion: subagente codificador (`general`) con instrucciones de Odoo 16/QWeb.
- Validacion: subagente tester (`general`) con instrucciones de usar `docker-compose.local.yml` y emitir evidencia.
- Documentacion: orquestador completa artefactos de mision y resumen.

## Plan

1. Revisar QWeb actual del reporte.
2. Cambiar el reverso a una composicion de dos columnas para los listados, con fuente y line-height mas compactos.
3. Ajustar logo/contenedor del reverso para ocupar mejor la pagina y no cortar online.
4. Validar XML, whitespace y carga del modulo en Docker Compose local.
5. Registrar evidencia en `verification.json`.
