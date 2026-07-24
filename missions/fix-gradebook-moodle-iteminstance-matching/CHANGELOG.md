# Changelog — Moodle `iteminstance`

## 2026-07-24

- Añadido el addon puente `irg_gradebook_moodle_iteminstance`.
- Admitida la resolución de actividades por `id`, `cmid` o `iteminstance`.
- Diferenciados los diagnósticos de actividad ausente y resolución ambigua.
- Conservados los controles de tipo y reutilización del grade item.
- Integrado `iteminstance` con el fallback entre múltiples HomeClass.
- Los mapeos CSV existentes funcionan sin reimportación.
- Añadidas pruebas de esquema, resolución, colisiones, compatibilidad y
  fallback; regresión conjunta validada con 94 métodos.
