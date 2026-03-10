# CHANGELOG - iRG Quiz Auto-Scoring

## Versión 16.0.1.0 - Marzo 9, 2026

### ✨ Nuevas Funcionalidades

#### 1. Auto-distribución de puntajes
- **Acción principal:** `Survey.action_auto_score_quiz()`
- Distribuye automáticamente 100 puntos entre preguntas sin puntaje
- Solo actúa en surveys de tipo `quiz`, `exam`, `cert`
- Valida que haya preguntas sin puntaje (previene acciones innecesarias)

#### 2. Interfaz de Usuario
- Botón "🎯 Auto-calcular Puntajes" en formulario de surveys
- Visible solo si survey_type es quiz/exam/cert
- Notificación clara con resumen de cambios realizados

#### 3. Auditoría y Logs
- Registro en chatter de cada survey
- Información capturada:
  - Fecha y hora de ejecución
  - Usuario que ejecutó
  - Puntaje asignado por pregunta
  - Número de preguntas configuradas

---

### 📁 Estructura de Módulo

```
irg_quiz_auto_scoring/
├── __init__.py
├── __manifest__.py
├── README.md
├── models/
│   ├── __init__.py
│   └── quiz.py              # Herencia survey.survey + acción principal
├── views/
│   └── survey_view.xml      # Vista heredada con botón
├── security/
│   └── ir.model.access.csv
└── i18n/
    └── es.po                # Traducciones español
```

---

### 🔧 Detalles Técnicos

#### Modelos Heredados
- **`survey.survey`** (módulo estándar)
  - Nuevo método: `action_auto_score_quiz()`
  - Métodos auxiliares para logging
  
#### Vistas
- **`survey_view.xml`**: Herencia de vista de formulario
  - Botón con estado condicional basado en `survey_type`
  - Acción `action_auto_score_quiz`
  - Clase Bootstrap: `btn-success`

#### Seguridad
- ACL mínimo: permisos de ERP Manager
- Modelo: `survey.model_survey_survey`

---

### ✅ Validaciones Implementadas

1. **Tipo de survey**
   - Solo `quiz`, `exam`, `cert`
   - Rechaza `assessment`, `feedback`

2. **Existencia de preguntas**
   - Valida que haya al menos una pregunta
   - Ignora líneas con `display_type` (separadores)

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
- `survey` (módulo estándar de Odoo 16)

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

- ✅ No modifica modelos base de survey
- ✅ No afecta surveys existentes (es opt-in)
- ✅ Reversible mediante desinstalación del módulo
- ✅ No requiere migración de datos

---

### 📝 Notas Importantes

1. **Primer uso:** El botón solo actúa en surveys de tipo quiz/exam/cert
2. **Auditoría:** Todos los cambios quedan registrados en el chatter
3. **Distribución:** Se asigna 100 puntos entre preguntas sin puntaje actual

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
