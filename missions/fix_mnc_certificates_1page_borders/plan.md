# Misión: Adaptación a 1 página y corrección de bordes de tabla para Certificados de Notas MNC

## Alcance
Modificar la generación de certificados de notas completos (`irg_gradebook_certificates`) y parciales (`irg_certificate_partial`) para que:
1. Las solicitudes con más de 15 asignaturas (como el Máster en Neuropsicología Clínica basada en la Evidencia - MNC, con 23 asignaturas) se generen en exactamente **1 sola página**.
2. Todas las filas de datos de la tabla tengan un borde inferior fino uniforme (`dee2e6`), y únicamente la última fila de datos conserve el borde inferior grueso (`000000`) antes del pie de Nota Media General.

## Routing de Capacidad
- Tier: `standard`
- Capacidad requerida: Trabajo en dos módulos (`irg_gradebook_certificates` y `irg_certificate_partial`), manipulación de XML de Word (`python-docx`), conversión LibreOffice PDF y tests.

## Criterios de Aceptación
1. Certificados de notas finales y parciales de MNC (23 asignaturas) caben en 1 página tanto para firmante `raimon` como `dpto_academico`.
2. La fila #12 (EN11) no muestra borde grueso negro intermedio.
3. Certificados con <= 15 asignaturas mantienen su comportamiento y maquetación estándar.
