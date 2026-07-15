# Plan: campos de nacimiento y ciudadanía del estudiante

## Alcance

Crear un módulo Odoo 16 nuevo que añada estos datos compartidos al contacto (`res.partner`) y al perfil OpenEducat (`op.student`):

- Población de nacimiento.
- País de nacimiento.
- País de ciudadanía.

Los valores se almacenarán únicamente en `res.partner`. OpenEducat los expondrá mediante la delegación existente `_inherits = {"res.partner": "partner_id"}`, garantizando que ambas fichas leen y escriben el mismo dato. El campo existente `op.student.nationality` no se modifica.

## Complejidad

Tier `complex`: aunque la lógica es acotada, el módulo y sus evidencias afectan a más de cinco archivos (modelos, dos vistas, pruebas y documentación), señal objetiva del routing del proyecto. No hay cambios de autenticación, secretos, concurrencia ni migraciones destructivas.

## Fases

1. Plan: confirmar el patrón `_inherits`, nombres técnicos y puntos de inserción de las vistas.
2. Implementación: aplicar TDD; crear primero pruebas que fallen por la ausencia de los campos y después el módulo mínimo.
3. Validación: ejecutar pruebas Odoo en `docker-compose.local.yml`, validar XML/Python y generar `verification.json` con evidencia.
4. Documentación: documentar instalación, campos, vínculo de datos, pruebas y changelog.

## Diseño técnico

- Módulo nuevo: `irg_student_birth_citizenship`.
- Modelo propietario: `res.partner`.
- Campos:
  - `birth_place`: `fields.Char` — Población de nacimiento.
  - `birth_country_id`: `fields.Many2one('res.country')` — País de nacimiento.
  - `citizenship_country_id`: `fields.Many2one('res.country')` — País de ciudadanía.
- Vista de estudiante: campos junto a `birth_date` y `nationality` dentro de información personal.
- Vista de contacto: bloque de datos personales en la ficha estándar.
- Sin duplicación ni lógica de sincronización; el vínculo lo proporciona `_inherits`.

## Estrategia de pruebas

- Verificar definición, tipo y comodel de los tres campos.
- Crear un contacto y su estudiante; escribir desde el estudiante y comprobar el contacto.
- Escribir desde el contacto y comprobar el estudiante.
- Verificar que las vistas combinadas de contacto y estudiante contienen los tres campos.
- Confirmar que `op.student.nationality` permanece disponible e independiente.

## Ejecución

Por instrucción expresa del usuario, todas las fases se ejecutan en el agente principal y no se lanzan subagentes.
