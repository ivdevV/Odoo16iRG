# Plan: recálculo autoritativo de plantilla 50/50

## Objetivo

Garantizar que la selección explícita del template con
`final_calculation_mode = diploma_50_50` aplique inmediatamente la ponderación
del Diplomado en `app.gradebook.student`, sin depender de clasificaciones
secundarias del curso que puedan provocar un fallback silencioso a 9,78.

## Evidencia

- El addon `irg_diploma_gradebook_beta_course_detection` figura instalado.
- La plantilla seleccionada muestra `Diplomado: presencial 50% + resto 50%`.
- Aun así, la libreta conserva 9,78.
- El promedio base aparece antes de seleccionar template porque
  `total_final` se calcula directamente desde las notas obligatorias.
- Las plantillas estándar no modifican `final_subject_note`, cuyo código base
  usa únicamente exámenes.

## Alcance

1. Crear un addon nuevo bajo `addons-extra/extrairg/`, dependiente del último
   puente de compatibilidad.
2. Hacer autoritativo el modo `diploma_50_50`: no consultar
   `_is_diplomado_course()` cuando el usuario seleccionó explícitamente esta
   plantilla específica de Diplomados.
3. Calcular directamente el bloque presencial 50% y el promedio de los demás
   módulos obligatorios 50%, conservando la exclusión NLEX/EX.
4. Reaplicar el resultado al final de `_amount_prod_final` y
   `compute_avg_score` para protegerlo frente a la cadena MRO.
5. Asegurar invalidación y recálculo al cambiar `gradebook_id`.
6. Añadir pruebas de regresión que fuercen a falso los detectores heredados y
   verifiquen 9,78 -> 9,22 al seleccionar el template.

## Fuera de alcance

- Cambiar cómo las plantillas estándar ponderan asignaciones/exámenes dentro
  de cada asignatura.
- Migraciones o escrituras masivas de libretas históricas.
- Modificar addons existentes.
- Commit o push sin autorización explícita posterior.

## Complejidad y routing

- **Tier:** `complex`.
- **Justificación:** conflicto cross-module reiterado, más de cinco archivos,
  orden MRO de computes y diferencia de datos/runtime no reproducible
  directamente desde beta.
- **Implementación:** subagente codificador de alta capacidad.
- **Validación:** subagente independiente con tests Odoo en
  `docker-compose.local.yml` y `verification.json` obligatorio.
- **Documentación:** subagente posterior a validación `passed`.
- **Security Advisor:** no aplica; no hay auth, secretos, migraciones,
  concurrencia ni borrado de datos.

## Criterios de aceptación

- Seis módulos con 10 y presencial 8,44 producen 9,22.
- El resultado cambia de 9,78 a 9,22 al escribir `gradebook_id` especial.
- Funciona aunque `_is_diplomado_course()` heredado devuelva falso.
- Template estándar conserva media simple.
- NLEX/EX queda excluido.
- Todos los checks relevantes pasan y `verification.json.status = passed`.

## Conocimiento aplicado

- `irg_diploma_gradebook_template_nlex_compat.md`: un compute posterior debe
  reaplicar el valor especial tras `super()`.
- `irg_diploma_gradebook_beta_course_detection.md`: los guard clauses ocultos
  pueden producir resultados válidos pero funcionalmente incorrectos.
