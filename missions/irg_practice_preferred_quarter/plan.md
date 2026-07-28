# Mission Plan — IRG Practice Preferred Quarter

## Contexto y Alcance
Misión para incorporar la pregunta "Trimestre preferente para iniciar las prácticas" en el formulario portal de solicitud de prácticas antes de "Tipo de práctica", con guardado en `practice.request` y vista backend.

## Clasificación
- **Tier**: `standard`
- **Nivel de Misión**: `full`

## Fases
1. **Plan**: Definición de la estructura, micro-spec y estrategia TDD.
2. **Implementación/TDD**:
   - `models/practice_request.py`: `irg_preferred_quarter` Selection field.
   - `views/practice_request_portal_templates.xml`: XPath injection before `practice_center_type_id`.
   - `views/practice_request_views.xml`: Inyección backend.
   - `controllers/main.py`: Validación y guardado.
3. **Review de código**: Verificación estática y de cumplimiento de normas IRG.
4. **Validación**: Ejecución de tests automatizados y verificación de coherencia.
5. **Documentación**: Registro en changelog y documentación.
