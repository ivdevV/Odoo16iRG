# Misión: Ajuste de posición Y del título del Diploma de Graduación

## Alcance
Bajar las coordenadas verticales (Y) de los títulos "Diploma de Graduación" (castellano) y "Diploma de Graduació" (catalán) en el reporte PDF del diploma de graduación (`irg_diploma_graduacion_student`).

## Clasificación de Complejidad
- **Tier:** `trivial`
- **Justificación:** Se trata de un ajuste puramente visual que modifica únicamente las coordenadas Y de dos líneas de texto en un único archivo (`diploma_pdf_report.py`). No introduce lógica nueva, no toca la base de datos, no afecta a la seguridad ni a la concurrencia.

## Modelos Asignados
- **Orquestador (Plan):** Gemini 3.5 Flash (actual)
- **Codificador (Implementación):** Gemini 3.5 Flash (gama mini/light/standard por ser trivial)
- **Testeador (Validación):** Gemini 3.5 Flash (intermedio)
- **Documentador (Documentación):** Gemini 3.5 Flash (ligero)

## Detalles del Cambio
- Archivo afectado: `addons-extra/extrairg/irg_diploma_graduacion_student/reports/diploma_pdf_report.py`
- Coordenadas actuales:
  - Español: `660`
  - Catalán: `632`
- Propuesta de nuevas coordenadas (reducción de 40 puntos para bajarlos):
  - Español: `620` (anteriormente 660)
  - Catalán: `592` (anteriormente 632)

## Plan de Validación
- Ejecutar los tests de Odoo para el módulo: `docker-compose -f docker-compose.local.yml run --rm web odoo -c /etc/odoo/odoo.conf -d odoo16irg_local --test-tags /irg_diploma_graduacion_student --stop-after-init` (o comando equivalente que se use en el entorno).
- Verificar que el reporte se genere correctamente sin errores de compilación o ejecución en ReportLab.
- Producir el archivo `verification.json` correspondiente.
