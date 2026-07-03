# Misión: fix_welcome_mail_selector_homeclass

## Alcance
Corregir la detección de lotes de modalidad **Online** en el selector automático de plantillas de bienvenida, en el wizard de confirmación manual, en el resolvedor de plantillas de diplomados, y en el autocompletado del lote, evitando que lotes de modalidad **HomeClass** con códigos que contienen "ONL" (como `MONLHC2609`) sean clasificados falsamente como Online.

## Clasificación de Complejidad
* **Tier:** `standard`
* **Justificación:** Afecta a 4-5 archivos distribuidos en varios submódulos, requiere lógica acotada de matching con contexto claro, sin decisiones de arquitectura ni riesgo de seguridad.
* **Modelo Elegido:** Gemini 3.5 Flash (o el modelo standard actual).

## Descomposición de la Tarea
1. Modificar la detección en `irg_elearning_correo_bienvenida_selector/models/op_admission.py`. (Completado)
2. Modificar la detección en `irg_openeducat_sale_lote_custom/models/op_batch.py`. (Completado)
3. Modificar la detección en `irg_sale_manual_confirmation_wizard/models/op_admission.py`. (Completado)
4. Modificar la detección en `irg_welcome_diplomado_template_selector/models/op_admission.py`. (Pendiente)
5. Añadir test en `irg_elearning_correo_bienvenida_selector/tests/test_welcome_mail.py` para asegurar que el código `MONLHC2609` (lote HomeClass) no sea tratado como Online. (Completado)
6. Validar el correcto funcionamiento corriendo los tests locales de todos los módulos.
7. Escribir documentación/changelog y actualizar la base de conocimientos si procede.
