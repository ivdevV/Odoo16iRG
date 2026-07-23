# Changelog — irg-gradebook-moodle-mapping-admin

## 2026-07-22

### Añadido

- Addon de administración para la jerarquía curso Odoo → curso Moodle →
  asignatura Odoo → Activity IDs Moodle, con navegación y contexto visibles.
- Importación conjunta de los dos CSV consolidados: `mapeo cursos.csv` y
  `Mapeo asignaturas.csv`.
- Wizard administrativo y adaptador de `odoo shell` sobre el mismo servicio
  de análisis y aplicación.
- Previsualización de solo lectura de creaciones y actualizaciones antes de
  confirmar, con reanálisis de los bytes persistidos al confirmar.

### Comportamiento de importación

- Validación de cabeceras, codificación, tamaño, IDs, referencias Odoo,
  coherencia curso/asignatura y pareja curso Odoo/Moodle.
- Parser CSV estricto: un fichero estructuralmente malformado bloquea el
  análisis completo; las incidencias de filas válidas se resumen como
  omisiones o advertencias.
- Omite asignaturas sin Activity IDs, conserva la primera aparición de IDs
  duplicados y une de forma estable filas compatibles.
- *Upsert* conservador e idempotente: crea o actualiza metadatos no vacíos y
  actividades nuevas, sin borrar, desactivar ni vaciar datos históricos.

### Seguridad y validación

- Acceso al wizard limitado a administradores de sistema tanto en interfaz
  como en métodos de servidor; sin `sudo()`.
- Preflight completo antes de escribir, revalidación de referencias al aplicar
  y transacción sin `commit` ni borrado implícito.
- Review independiente y validación independiente aprobadas, incluyendo 61
  pruebas Odoo sin fallos ni errores, comprobaciones estáticas y smoke
  reversible de UI/ACL/preview. El smoke con CSV reales no aplicó datos porque
  la base de pruebas no contenía el maestro de origen.
