# Changelog — excluir encuestas sin calificación

## 16.0.1.0.1

- Corregida la sincronización para que una respuesta `survey` con `no_scoring` no se convierta en un examen de libreta con nota cero.
- Protegidos los flujos automático, heredado (`send_result`) y de regularización pendiente.
- Conservadas las asignaciones con `no_scoring` y las encuestas puntuables.
- Añadidas regresiones Odoo para las tres categorías.
- Commit y push autorizados únicamente a desarrollo (`origin/Dev_iRG`); Producción se actualiza manualmente y no se toca en esta misión.
