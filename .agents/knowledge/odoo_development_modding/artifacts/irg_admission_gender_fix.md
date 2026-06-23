# Conflicto de Selección de Género y Propagación a Admisiones/Estudiantes

## Contexto y Problema
En Odoo 16, cuando múltiples módulos heredan e instancian el mismo campo de selección (`Selection`) sobre un modelo (por ejemplo, `gender` en `res.partner`), Odoo unifica los campos en el registro global:
1. Si un módulo define `gender` con selección `[('male', 'Male'), ...]` y un default `'male'`, y otro posterior redefine `gender` con selección `[('m', 'Masculino'), ...]` sin usar `selection_add`, el listado de opciones finales se sobrescribe al segundo formato.
2. Sin embargo, el valor por defecto (`default='male'`) del primer módulo permanece en la definición.
3. Al crear un registro sin especificar este campo, Odoo intenta aplicar el default `'male'`. Puesto que `'male'` ya no es un valor válido en la lista de opciones actualizada `['m', 'f', 'o']`, la validación falla arrojando un error crítico: `ValueError: Wrong value for res.partner.gender: 'male'`.

## Solución Aplicada
1. **Unificación y Limpieza de Campo en Heredero:**
   En el nuevo módulo `irg_admission_gender_fix`, se heredó `res.partner` para redefinir el campo `gender` combinando de forma explícita todas las opciones de selección necesarias (de ambos formatos) y limpiando el valor por defecto:
   ```python
   gender = fields.Selection([
       ('m', 'Masculino'),
       ('f', 'Femenino'),
       ('o', 'Otro'),
       ('male', 'Male'),
       ('female', 'Female'),
       ('not-sure', 'Not Sure')
   ], string='Género', default=False)
   ```
   Esto permite que los tests y conectores que pasan `'male'` sigan funcionando mientras se evita que la creación automática asigne un default inválido.

2. **Lógica de Fallback para Campos Requeridos (`required=True`):**
   Los campos de género en `op.admission` y `op.student` son obligatorios a nivel de base de datos (`NOT NULL`). Al implementar flujos automáticos de mapeo desde el contacto, si la lógica de mapeo o adivinación inteligente retorna un valor no soportado (o un fallback a `'o'`), el código debe asignarlo explícitamente en el diccionario `vals` para evitar fallos por violación de restricciones `NotNullViolation` en SQL.
   ```python
   # Fallback obligatorio para campos con required=True en Odoo
   if not vals.get('gender'):
       vals['gender'] = 'o'
   ```

## Aprendizajes Clave
- **Herencia e Intersección de Selection:** Siempre inspeccionar si hay múltiples módulos redefiniendo el mismo campo de selección. Los defaults declarados en módulos base o paralelos pueden causar colisiones silenciosas si el listado de opciones de selección es reemplazado.
- **Normalización Multicapa:** Cuando se tiene una mezcla de valores (ej. `'male'` vs `'m'`), es mejor unificar la aceptación a nivel de campo en el modelo origen (`res.partner`) y normalizar al formato de destino (`'m'`, `'f'`) durante la propagación o procesamiento.
- **Adivinación Inteligente de Datos Faltantes:** Un enfoque heurístico en tres niveles (1. Campos del contacto -> 2. Título de cortesía -> 3. Diccionarios de nombres comunes y sufijos morfológicos `-a`/`-o`) ofrece una excelente precisión para campos obligatorios que no están expuestos en la interfaz de usuario del contacto.
