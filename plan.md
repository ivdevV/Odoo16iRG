# Plan de Misión: Módulo de Convenios de Prácticas y Firma Digital (`irg_practice_agreement_sign`)

## Scope & Tier Classification
- **Tier:** `standard`
- **Justificación:** Módulo nuevo que interactúa con `isep_practices_2`, expone rutas web públicas mediante tokens de seguridad para la cumplimentación y captura de firma digital, e incluye la firma pre-autorizada del Sr. Raimon Gaja (`Firma Raimon.png`).
- **Roles:**
  - Orquestador: Definición de plan y criterios.
  - Codificador: Desarrollo del modelo `practice.agreement`, controlador web, reporte QWeb y vistas.
  - Revisor / Validador: Verificación de sintaxis, pruebas unitarias y generación de PDF.
  - Documentador: Registro en CHANGELOG.md y actualización de documentación.

## Criterios de Aceptación
1. Creación del módulo `irg_practice_agreement_sign` en `addons-extra/extrairg/`.
2. Extensión/Integración con el modelo `practice.center` de `isep_practices_2`.
3. Carga automática de la firma oficial de Raimon Gaja (`Firma Raimon.png`) en el lado izquierdo del PDF.
4. Generación de enlace público tokenizado `/convenio/firma/<token>`.
5. Formulario web responsive donde el centro completa datos y firma en el lado derecho.
6. Generación automática del convenio PDF firmado y guardado en los documentos del centro.

## Riesgos y Mitigaciones
- **Seguridad en enlaces públicos:** Usar tokens aleatorios criptográficos (UUID4/urlsafe).
- **Fidelidad del documento:** Maquetar la plantilla QWeb PDF respetando el diseño exacto de `Convenio Marco iRG - Modelo firma.docx` y `Convenio Marco iRG - Modelo firma.pdf`.

## Estado del Gate
- Plan refinado con la incorporación de la firma oficial `Firma Raimon.png`.
