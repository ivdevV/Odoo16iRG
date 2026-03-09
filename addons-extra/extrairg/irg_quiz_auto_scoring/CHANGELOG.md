# CHANGELOG - iRG Quiz Auto-Scoring

## Versión 16.0.1.0 - Marzo 9, 2026

### ✨ Nuevas Funcionalidades

#### 1. Auto-distribución de puntajes
- **Acción principal:** `OpQuiz.action_auto_score_quiz()`
- Distribuye automáticamente 100 puntos entre preguntas sin puntaje
- Solo actúa en cuestionarios en estado "Draft" o "In-Progress"
- Valida que todas las preguntas estén sin puntaje (previene sobre-scoring)

#### 2. Recálculo automático de resultados de estudiantes
- Procesa todos los intentos (resultados) existentes de un cuestionario
- Para cada respuesta:
  - **Correcta:** Asigna el puntaje completo de la pregunta
  - **Incorrecta:** Asigna 0 puntos
- Recalcula automáticamente:
  - Puntaje total del intento
  - Porcentaje obtenido

#### 3. Sincronización con boletín de calificaciones
- Integración automática con `openeducat_grading` (si está instalado)
- Actualiza líneas de gradebook con nuevos puntajes
- Preserva integridad referencial

#### 4. Interfaz de Usuario
- Botón "🎯 Auto-calcular Puntajes" en formulario de cuestionarios
- Visible solo en estados "Draft" e "In-Progress"
- Notificación clara con resumen de cambios realizados

#### 5. Auditoría y Logs
- Registro en chatter de cada cuestionario
- Información capturada:
  - Fecha y hora de ejecución
  - Usuario que ejecutó
  - Puntaje asignado por pregunta
  - Número de intentos procesados

---

### 📁 Estructura de Módulo

```
irg_quiz_auto_scoring/
├── __init__.py
├── __manifest__.py
├── README.md
├── models/
│   ├── __init__.py
│   ├── quiz.py              # Herencia OpQuiz + acción principal
│   └── quiz_result.py       # Herencia OpQuizResult + recálculo
├── views/
│   └── quiz_view.xml        # Vista heredada con botón
├── security/
│   └── ir.model.access.csv
└── tests/
    ├── __init__.py
    └── test_quiz_auto_scoring.py
```

---

### 🔧 Detalles Técnicos

#### Modelos Heredados
- **`op.quiz`** (openeducat_quiz)
  - Nuevo método: `action_auto_score_quiz()`
  - Métodos auxiliares para procesamiento y sincronización
  
- **`op.quiz.result`** (openeducat_quiz)
  - Nuevo método: `recalculate_score()`
  - Nuevo campo: `obtain_mark` (puntaje obtenido)

#### Vistas
- **`quiz_view.xml`**: Herencia de vista de formulario
  - Botón con estado condicional
  - Acción `action_auto_score_quiz`
  - Clase Bootstrap: `btn-success`

#### Seguridad
- ACL mínimo: permisos de ERP Manager
- No requiere modelos nuevos con ACL compleja

---

### ✅ Validaciones Implementadas

1. **Estado del cuestionario**
   - Solo "Draft" o "In-Progress"
   - Rechaza "Done", "Cancel"

2. **Existencia de preguntas**
   - Valida que haya al menos una pregunta
   - Ignora líneas con `display_type` (separadores)

3. **Puntajes previos**
   - Rechaza si alguna pregunta ya tiene puntaje > 0
   - Previene sobre-escritura accidental

4. **Disponibilidad de módulos**
   - Detección automática de `openeducat_grading`
   - Sincronización opcional (no falla sin él)

---

### 🧪 Cobertura de Tests

Tests implementados en `test_quiz_auto_scoring.py`:

| Test ID | Descripción | Estado |
|---------|-------------|--------|
| TC1 | Distribución equitativa de puntajes | ✅ PASS |
| TC2 | Rechazo de cuestionarios con marks | ✅ PASS |
| TC3 | Validación de estados válidos | ✅ PASS |
| TC4 | Validación de cuestionario vacío | ✅ PASS |
| TC5 | Cálculo con respuestas correctas | ✅ PASS |
| TC6 | Cálculo con respuestas incorrectas | ✅ PASS |
| TC7 | Cálculo con respuestas mixtas | ✅ PASS |

---

### 📋 Dependencias

**Requeridos:**
- `openeducat_quiz` (v16.0.x)

**Opcionales:**
- `openeducat_grading` (para sincronización de boletín)

---

### 🚀 Instalación y Uso

```bash
# Instalar módulo
odoo -u irg_quiz_auto_scoring -d <db> --stop-after-init

# Verificar instalación
# - Menú: Educación > Cuestionarios > Cuestionarios
# - Abrir cuestionario en estado "Draft"
# - Botón "🎯 Auto-calcular Puntajes" debe estar visible
```

---

### 🔄 Backwards Compatibility

- ✅ No modifica modelos base de openeducat_quiz
- ✅ No afecta cuestionarios existentes (es opt-in)
- ✅ Reversible mediante desinstalación del módulo
- ✅ No requiere migración de datos

---

### 📝 Notas Importantes

1. **Primer uso:** El botón solo actúa en estado "Draft"
2. **Datos históricos:** No afecta intentos ya enviados antes de la ejecución
3. **Sincronización:** Solo funciona si `openeducat_grading` está instalado
4. **Auditoría:** Todos los cambios quedan registrados en el chatter

---

### 🐛 Problemas Conocidos

Ninguno identificado en la versión inicial.

---

### 📞 Soporte

Contactar a: equipo de desarrollo iRG

---

**Versión:** 16.0.1.0  
**Fecha:** Marzo 9, 2026  
**Autor:** iRG Inc
