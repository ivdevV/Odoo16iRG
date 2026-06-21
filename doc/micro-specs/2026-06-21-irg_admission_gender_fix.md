# IRG Admission Gender Fix

## 1. Título corto
Corrección de mapeo de género de contacto a admisión y estudiante.

## 2. Resumen objetivo
Crear el módulo `irg_admission_gender_fix` que hereda `op.admission` y `op.student` para corregir de forma centralizada la conversión de las claves de género (`gender` / `gender_type`) del contacto (`res.partner`) hacia los valores esperados por OpenEduCat (`'m'`, `'f'`, `'o'`).

## 3. Motivo / justificación
La presencia del módulo de Moodle redefine la selección de `gender` en `res.partner` con los valores `('male', 'female', 'not-sure')` y valor por defecto `'male'`. Al crear admisiones desde pedidos de venta (manualmente o mediante el asistente de confirmación), se propaga este valor al campo `gender` de `op.admission`/`op.student` que requiere estrictamente `('m', 'f', 'o')`. Dado que `'male'` o `'female'` son valores no contemplados en la selección de la admisión, Odoo aplica el fallback de la admisión que es `'o'` (Otro). La conversión debe ser automática en base al contacto.

## 4. Alcance exacto
- Crear el módulo `irg_admission_gender_fix` en `addons-extra/extrairg/`.
- Interceptar `create` y `write` en `op.admission` y `op.student` para:
  - Mapear `'male'` / `'Male'` -> `'m'`.
  - Mapear `'female'` / `'Female'` -> `'f'`.
  - Mapear `'other'` / `'not-sure'` -> `'o'`.
  - Si el género provisto es `'o'` o es nulo/vacío, e existe un `partner_id` válido, recuperar el género del partner y mapearlo correspondientemente.
  - En `write`, no sobreescribir un `'o'` explícito con el género del partner si no se está cambiando de partner ni de género.
- Crear tests unitarios que verifiquen el mapeo de todas las variantes de género en la creación y edición.

## 5. Diseño técnico
- Módulo: `addons-extra/extrairg/irg_admission_gender_fix`.
- Dependencias: `openeducat_admission`, `openeducat_core`.
- Herencia de modelos:
  - `_inherit = 'op.admission'`
  - `_inherit = 'op.student'`
- Lógica de mapeo en `create` (multi) y `write`.

## 6. Dependencias
- `openeducat_admission`
- `openeducat_core`

## 7. Backwards-compatibility / migración
Ninguna migración requerida. Las admisiones y estudiantes existentes seguirán teniendo sus valores actuales. Las nuevas admisiones y estudiantes heredarán correctamente el género mapeado de su partner asociado.

## 8. Casos de prueba / criterios de aceptación
- Crear un registro de admisión pasando en valores `gender='male'` y comprobar que se guarda como `gender='m'`.
- Crear un registro de admisión pasando en valores `gender='female'` y comprobar que se guarda como `gender='f'`.
- Crear un registro de admisión asociando un partner con `gender='male'` y comprobar que se guarda como `gender='m'`.
- Crear un registro de estudiante asociando un partner con `gender='female'` y comprobar que se guarda como `gender='f'`.
- Modificar el partner de un registro y verificar que el género se actualiza.
