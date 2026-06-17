# Misión: Modificaciones en Variante Física de Certificados de Notas

## Alcance y Descomposición
Modificación de las plantillas e inyección de datos para certificados de notas físicos y apostillados. Afecta a:
- `irg_gradebook_certificates` (Certificado completo)
- `irg_certificate_partial` (Certificado parcial)

## Clasificación de Complejidad y Justificación
- **Tier**: `standard`
- **Justificación**: Afecta a 2 archivos de lógica y 2 archivos de pruebas unitarias. No introduce riesgos de seguridad (auth, secretos, concurrencia, base de datos) ni cambios estructurales complejos, sino ajustes de diseño estético en generación de documentos Word.

## Asignación de Modelos
- **Plan**: Gemini 3.5 Flash (modelo actual de razonamiento).
- **Implementación**: Modelo codificador intermedio.
- **Validación**: Modelo testeador intermedio.
- **Documentación**: Modelo documentador ligero.

## Criterios de Aceptación (Verificación)
- Margen superior incrementado a 1.78 pulgadas (aproximadamente 128 Pt) en certificados físicos.
- Letra de cuerpo/cabecera sin reducir (10 Pt) y letra de la tabla reducida a 7.5 Pt.
- Ausencia completa de firmas manuscritas y sellos institucionales en la parte inferior.
- Tests unitarios modificados y nuevos agregados pasando correctamente.
