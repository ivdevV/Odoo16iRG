# Misión: fix_welcome_mail_selector_homeclass

## Alcance
Corregir la detección de lotes de modalidad **Online** en el selector automático de plantillas de bienvenida y en el wizard de confirmación manual, evitando que lotes de modalidad **HomeClass** con códigos que contienen "ONL" (como `MONLHC2609`) sean clasificados falsamente como Online.

## Clasificación de Complejidad
* **Tier:** `standard`
* **Justificación:** Afecta a 2-3 archivos (`irg_elearning_correo_bienvenida_selector` y `irg_sale_manual_confirmation_wizard`), requiere lógica acotada de matching con contexto claro, sin decisiones de arquitectura ni riesgo de seguridad.
* **Modelo Elegido:** Gemini 3.5 Flash (o el modelo standard actual).

## Descomposición de la Tarea
1. Modificar la detección en `irg_elearning_correo_bienvenida_selector/models/op_admission.py`.
2. Modificar la detección en `irg_sale_manual_confirmation_wizard/models/op_admission.py`.
3. Añadir test en `irg_elearning_correo_bienvenida_selector/tests/test_welcome_mail.py` para asegurar que el código `MONLHC2609` (lote HomeClass) no sea tratado como Online.
4. Validar el correcto funcionamiento corriendo los tests locales en `docker-compose.local.yml`.
5. Escribir documentación/changelog y actualizar la base de conocimientos si procede.
