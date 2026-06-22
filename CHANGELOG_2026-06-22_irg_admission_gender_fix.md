# Changelog: Corrección de Mapeo de Género en Admisiones (`irg_admission_gender_fix`)

**Fecha:** 2026-06-22  
**Autor:** Antigravity / Google DeepMind  
**Misión:** `fix_admission_gender_mapping`

## Descripción del Problema
Se identificó que el género se asignaba incorrectamente como "Otro" (`'o'`) al crear admisiones de forma nativa o por el wizard. Esto ocurría porque la información de género no se propagaba adecuadamente desde el contacto (`res.partner`). Adicionalmente, el contacto no cuenta con un campo de género visible por defecto, lo que requería lógica inteligente para adivinar el género a partir del título o el nombre del alumno.

Durante la validación de la suite, se detectó un conflicto de selección en el campo `res.partner.gender` provocado por valores incompatibles de `odoo_moodle_connector` y `isep_openeducat_sale`. Esto causaba una caída con `ValueError` debido a un valor por defecto no válido (`'male'`).

## Cambios Introducidos

### Módulo `irg_admission_gender_fix` (Nuevo Componente)
- **Manifest (`__manifest__.py`):** Configurado con dependencias explícitas (`openeducat_admission`, `openeducat_core`, `isep_openeducat_sale`, `isep_admission_from_student_field`, `odoo_moodle_connector`) para evitar conflictos de registry.
- **Modelo `res.partner` (`models/res_partner.py`):**
  - Heredado para unificar los valores de selección de los conectores de Moodle y OpenEduCat.
  - Se removió el valor por defecto (`default=False`), previniendo caídas de validación.
- **Modelo `op.admission` (`models/op_admission.py`):**
  - Sobrescribe `create` y `write` para mapear géneros `'male'`/`'female'` a `'m'`/`'f'`.
  - Propaga el género del contacto si se omite en la creación o si es `'o'`.
  - Implementa adivinación inteligente usando títulos de cortesía y terminaciones del nombre (heurística morfológica).
  - Asegura un fallback a `'o'` si no se determina el género, evitando violar la restricción `NOT NULL` en base de datos.
- **Modelo `op.student` (`models/op_student.py`):**
  - Sobrescribe `create` y `write` implementando las mismas validaciones y flujos que la admisión.

## Pruebas Realizadas
Se diseñó e implementó una suite de tests unitarios completa (`tests/test_gender_mapping.py`):
1. `test_01_create_admission_explicit_gender`: Mapeo explícito de `'male'`/`'female'` -> `'m'`/`'f'`.
2. `test_02_create_admission_from_partner_gender`: Propagación del género desde el contacto.
3. `test_03_write_admission_gender`: Comportamiento de escritura directa y cambio de partner.
4. `test_04_student_gender_mapping`: Propagación y mapeo para estudiantes.
5. `test_05_intelligent_gender_guessing`: Adivinación de género mediante el nombre (ej. Laura -> `'f'`, Juan -> `'m'`), títulos (ej. Sra. -> `'f'`) y sufijos morfológicos (ej. Carla -> `'f'`, Roberto -> `'m'`).

Todos los tests pasaron satisfactoriamente en el entorno local Docker:
`0 failed, 0 error(s) of 5 tests when loading database 'test_irg_db'`
