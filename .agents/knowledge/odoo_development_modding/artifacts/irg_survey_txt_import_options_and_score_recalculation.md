# gotcha: Interacción con irg_exam_score_100 en Pruebas Unitarias de Encuestas/Exámenes

## Descripción
Al escribir pruebas unitarias para creación o importación de preguntas/respuestas de exámenes (como en el wizard de importación TXT), existe una interferencia con el módulo `irg_exam_score_100`. 

Este módulo recalcula dinámicamente el campo `answer_score` de las respuestas en exámenes para que sumen `100.0` en total. Si una encuesta de tipo `exam` se crea en un entorno de test y tiene una sola pregunta con una opción correcta, la puntuación de esa opción se escala automáticamente a `100.0` en lugar de mantener el `1.0` original asignado en la creación.

## Impacto
Cualquier aserción de test que verifique el valor por defecto o asignado directamente de `answer_score` (por ejemplo, `self.assertEqual(ans.answer_score, 1.0)`) fallará con un error del tipo:
```
AssertionError: 100.0 != 1.0
```

## Solución / Recomendación
En las pruebas unitarias que involucren encuestas/exámenes y sus preguntas, en lugar de validar una puntuación exacta de `1.0`, debe validarse que sea mayor que `0.0` o bien adaptada a la escala reajustada:
```python
if 'answer_score' in ans._fields:
    self.assertTrue(ans.answer_score > 0.0)
```
Esto garantiza la compatibilidad de los tests independientemente de si el módulo `irg_exam_score_100` está instalado/cargado en la base de datos de pruebas.
