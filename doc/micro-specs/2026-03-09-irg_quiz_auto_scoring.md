# Micro-spec: Auto-scoring de Cuestionarios (irg_quiz_auto_scoring)

## 1. Título
Auto-scoring inteligente para cuestionarios sin puntaje inicial y actualización de calificaciones

## 2. Resumen objetivo
Agregar un botón en el formulario de carga de cuestionarios (`op.quiz`) que:
- Distribuya automáticamente 100 puntos entre preguntas sin puntaje
- Calcule puntajes de respuestas basado en resultados correctos/incorrectos
- Sincronice calificaciones actualiza al boletín del estudiante

## 3. Motivo / Justificación
Los cuestionarios se crean frecuentemente sin puntajes en las preguntas. Esta funcionalidad evita trabajo manual repetitivo y garantiza coherencia en la evaluación automática de cuestionarios. Se crea como módulo extra para no modificar el core de `openeducat_quiz`.

## 4. Alcance exacto
**Modelos a heredar:**
- `op.quiz` (Quiz)
- `op.quiz.line` (Pregunta del cuestionario)
- `op.quiz.result` (Resultado/intento)

**Vistas:**
- Heredar vista de formulario de `op.quiz` para agregar botón "Auto-calcular Puntajes"

**No toca:**
- Modelos nativos de Odoo
- Cambios forzados en cuestionarios ya calificados

## 5. Diseño técnico

### 5.1 Botón en formulario
- Ubicación: Vista de formulario de `op.quiz`, botón inferior al lado del estado
- Acción: llamar a método `action_auto_score_quiz()`
- Visible solo si: `state in ['draft', 'open']`

### 5.2 Lógica principal (método `action_auto_score_quiz` en herencia de `op.quiz`)

**Paso 1: Validar condiciones**
```
IF líneas sin puntaje (mark = 0 o None):
    - Calcular puntaje por pregunta = 100 / count(line_ids sin display_type)
    - Asignar ese puntaje a cada pregunta
    - Registrar en log de cambios
ELSE:
    - Mostrar advertencia: "El cuestionario ya tiene puntajes asignados"
    - Retornar sin hacer cambios
```

**Paso 2: Procesar resultados existentes**
```
FOR EACH resultado (op.quiz.result) de este cuestionario:
    FOR EACH resultado_línea (op.quiz.result.line):
        IF respuesta_correcta (answer == given_answer):
            resultado_línea.score = correspondiente puntaje_pregunta
        ELSE:
            resultado_línea.score = 0
        resultado_línea.save()

    # Recalcular total del resultado
    resultado.total_score = SUM(resultado_línea.score)
    resultado.percentage = (total_score / total_marks) * 100
    resultado.save()
```

**Paso 3: Sincronizar con boletín (si existe integración con gradebook)**
```
IF módulo openeducat_grading está instalado:
    FOR EACH resultado:
        - Obtener estudiante y curso/asignatura del resultado
        - Actualizar línea correspondiente en gradebook
        - Registrar cambio
```

### 5.3 Modelos heredados

**irg.quiz.auto.score (modelo de auditoría, opcional)**
- `quiz_id` (Many2one → op.quiz)
- `datetime` (Datetime)
- `created_by` (Many2one → res.users)
- `affected_results_count` (Integer)
- `notes` (Text)

## 6. Dependencias (`depends` en `__manifest__`)
```python
'depends': [
    'openeducat_quiz',
    'openeducat_grading',  # opcional, si está instalado
]
```

## 7. Backwards-compatibility / Migración
- **Acción reversible:** El botón solo asigna puntajes a preguntas SIN puntaje actual
- **Seguridad:** Verificar que `state == 'draft'` antes de permitir cambios
- **No afecta quizzes publicados:** Solo actúa en draft/open

## 8. Casos de prueba / Criterios de aceptación

### TC1: Distribución de puntajes
```
CUANDO: Click en botón + cuestionario con 5 preguntas sin puntaje
ENTONCES: Cada pregunta recibe 20 puntos (100/5)
RESULTADO: ✓ PASS si mark de cada línea = 20.0
```

### TC2: Rechazo si ya tiene puntajes
```
CUANDO: Click en botón + cuestionario con preguntas que tienen puntaje > 0
ENTONCES: Mostrar mensaje "Ya tiene puntajes asignados"
RESULTADO: ✓ PASS si no hay cambios en marks
```

### TC3: Cálculo de puntajes en intentos
```
CUANDO: Existen 3 resultados (intentos) del quiz con preguntas respondidas correctas/incorrectas
ENTONCES: Cada score de resultado_línea = puntaje_pregunta si respuesta correcta, 0 si incorrecta
RESULTADO: ✓ PASS si total_score recalculado correctamente
```

### TC4: Actualización de boletín
```
CUANDO: Quiz usado en gradebook + se ejecuta auto-score
ENTONCES: Las calificaciones en gradebook se actualizan con nuevos puntajes
RESULTADO: ✓ PASS si gradebook_line.grade refleja nuevo cálculo
```

## 9. Rollback plan

**Desinstalación:**
```bash
odoo -u irg_quiz_auto_scoring -d <db> --stop-after-init
odoo -u openeducat_quiz -d <db> --stop-after-init
```

**Reversión manual de marks (SQL, si fue necesario):**
```sql
-- Verificar cambios antes de ejecutar
SELECT id, name, mark FROM op_quiz_line 
WHERE quiz_id = <quiz_id> AND mark IS NOT NULL;

-- Restaurar de backup de BD si es crítico
```

## 10. Estimación y responsable
- **Estimación:** 6-8 horas
- **Responsable:** Equipo de desarrollo iRG
- **Revisión:** Equipo de QA + Arquitecto de educación
- **Fecha propuesta:** Marzo 2026

---

## Notas adicionales
- Considerar agregar permisos `irg.quiz.auto.score.view`, `irg.quiz.auto.score.create`
- Registrar cada ejecución en modelo de auditoría para trazabilidad
- Mostrar modal de confirmación antes de procesar (número de afectados, cambios)
