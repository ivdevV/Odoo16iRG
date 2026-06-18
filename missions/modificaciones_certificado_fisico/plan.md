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
- Margen superior incrementado a 109.5 Pt (aproximadamente 50 píxeles de desplazamiento) en certificados físicos.
- Letra de cuerpo/cabecera ajustada a 8.5 Pt y letra de la tabla reducida a 7.5 Pt.
- Ausencia completa de firmas manuscritas y sellos institucionales en la parte inferior.
- Reemplazo de "Raimon Gaja Jaumeandreu" por "Raimon Gaja" y frase de cierre corregida a "Para que así conste, firmo la presente en Barcelona, a fecha...".
- Cargo de Raimon Gaja cambiado a "Director General iRG" con espaciado vertical de firma de 48 Pt.
- Tests unitarios modificados y nuevos agregados pasando correctamente.
