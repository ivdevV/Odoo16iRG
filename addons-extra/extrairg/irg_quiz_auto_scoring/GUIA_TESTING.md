# GUÍA PASO A PASO: Probar Auto-Scoring en Odoo 16

## 📋 Requisitos Previos

✅ Módulo `irg_quiz_auto_scoring` instalado  
✅ Acceso como usuario con permisos de ERP Manager  
✅ Módulo `survey` completamente instalado (estándar en Odoo 16)  
✅ Navegador con soporte para elementos interactivos

---

## 🎯 PRUEBA 1: Crear y Auto-Calificar un Cuestionario Básico

### Paso 1: Navegar al Módulo de Cuestionarios
1. Ir a **Educación** (Education)
2. Hacer clic en **Cuestionarios** (Quizzes)
3. Hacer clic en **Cuestionarios** nuevamente (lista principal)
4. Ver lista de cuestionarios existentes

**Pantalla esperada:**
- Vista de árbol/lista con cuestionarios
- Botón "Crear" en la esquina superior izquierda

---

### Paso 2: Crear un Nuevo Cuestionario
1. Hacer clic en el botón **"Crear"** (Create)
2. Se abrirá un formulario en blanco

**Campos a rellenar:**
| Campo | Valor | Notas |
|-------|-------|-------|
| Nombre | "Quiz Test - Auto-Scoring" | Identificador claro |
| Categoría | Seleccionar cualquiera | Ej: "General" |
| Asignado a | "Abierto para todos" | Acceso público |
| Estado | Automático: "Draft" | ⚠️ CRÍTICO: Debe estar en Draft |

**Pantalla esperada:**
- Formulario con campos vacíos
- Estado mostrado como "Draft" en la esquina superior derecha

---

### Paso 3: Agregar Preguntas SIN Puntaje

⚠️ **IMPORTANTE:** Las preguntas deben estar **SIN puntaje inicial** para que el botón funcione.

#### Para cada pregunta (créa 5 preguntas):

1. **Desplazarse hacia abajo** al apartado "Preguntas" (Questions)
2. Hacer clic en **"Agregar una línea"** (Add a line)
3. Rellenar los campos:

| Campo | Valor | Ejemplo |
|-------|-------|---------|
| Pregunta | Describir la pregunta | "¿Cuál es la capital del Perú?" |
| Tipo de pregunta | "Opcional" (Optional) | Tipo de respuesta |
| Respuesta correcta | Respuesta esperada | "Lima" |
| Puntaje | **DEJAR EN 0 o VACÍO** | ⚠️ CRÍTICO |

**Repetir 5 veces con preguntas diferentes:**
```
Pregunta 1: "¿Cuál es la capital del Perú?" → Respuesta: "Lima" → Puntaje: [VACÍO]
Pregunta 2: "¿Cuál es el río más largo de América?" → Respuesta: "Amazonas" → Puntaje: [VACÍO]
Pregunta 3: "¿Cuántos continentes hay?" → Respuesta: "7" → Puntaje: [VACÍO]
Pregunta 4: "¿Cuál es la moneda de Perú?" → Respuesta: "Sol" → Puntaje: [VACÍO]
Pregunta 5: "¿En qué año se fundó el Perú?" → Respuesta: "1821" → Puntaje: [VACÍO]
```

**Pantalla esperada:**
- Tabla con 5 líneas de preguntas
- Columna de Puntaje vacía o con 0

---

### Paso 4: Guardar el Cuestionario

1. Hacer clic en **"Guardar"** (Save) o presionar `Ctrl+S`
2. El cuestionario se salvará en estado "Draft"

**Pantalla esperada:**
- Mensaje de confirmación: "Cambios guardados"
- Estado sigue siendo "Draft"

---

### Paso 5: VISUALIZAR EL BOTÓN "Auto-calcular Puntajes"

1. **Desplazarse hacia arriba** hasta ver los botones de acción
2. **Buscar el botón verde** con ícono 🎯 y texto **"Auto-calcular Puntajes"**

**Pantalla esperada:**
- Botón visible en color verde (btn-success)
- Disponible/activo (no gris)
- Posicionado antes del botón "Abrir" (Open)

---

### Paso 6: PASAR EL RATÓN SOBRE EL BOTÓN PARA VER EL TOOLTIP

1. **Posicionar el cursor del ratón** sobre el botón "🎯 Auto-calcular Puntajes"
2. **ESPERAR 2-3 segundos** sin hacer clic
3. **Se abrirá una ventana emergente** con la explicación en 6 pasos

**Tooltip esperado:**
```
PASO A PASO de lo que hará este botón:

1️⃣ VALIDAR ESTADO: Verifica que el cuestionario esté en Draft o In-Progress

2️⃣ VERIFICAR PREGUNTAS: Confirma que existan preguntas en el cuestionario

3️⃣ DISTRIBUIR PUNTAJES: Si ninguna pregunta tiene puntaje:
   • Divide 100 entre la cantidad total de preguntas
   • Asigna ese resultado como puntaje a cada pregunta
   • Ejemplo: 100 ÷ 5 preguntas = 20 puntos c/u

4️⃣ PROCESAR INTENTOS: Para cada intento que hayan hecho estudiantes:
   • Si respuesta fue CORRECTA → asigna el puntaje de la pregunta
   • Si respuesta fue INCORRECTA → asigna 0 puntos
   • Recalcula el total y porcentaje del intento

5️⃣ SINCRONIZAR: Si el módulo 'Calificaciones' está activo:
   • Actualiza automáticamente el boletín de cada estudiante
   • Suma todos los puntajes para la calificación final

6️⃣ REGISTRAR: Guarda un registro de auditoría con:
   • Fecha y hora de ejecución
   • Usuario que ejecutó la acción
   • Número de preguntas y puntaje asignado
   • Cantidad de intentos procesados
```

---

### Paso 7: HACER CLIC EN EL BOTÓN PARA EJECUTAR

1. **Hacer clic** en el botón "🎯 Auto-calcular Puntajes"
2. **El sistema procesará** (puede tomar 1-5 segundos)
3. **Se abrirá una notificación verde** en la esquina inferior derecha

**Notificación esperada:**
```
✓ Auto-scoring de Cuestionario

✓ Auto-scoring completado exitosamente.
- 5 preguntas fueron configuradas con 20.00 puntos cada una
- 0 intentos de estudiantes fueron re-evaluados
- Puntaje total del cuestionario: 100.00 puntos
```

---

### Paso 8: VERIFICAR QUE LOS PUNTAJES SE ASIGNARON

1. **Desplazarse hacia abajo** al apartado de Preguntas
2. **Verificar la columna "Puntaje"** de todas las preguntas

**Resultado esperado:**
```
✓ ANTES:
  Pregunta 1 → Puntaje: [VACÍO]
  Pregunta 2 → Puntaje: [VACÍO]
  ...

✓ DESPUÉS:
  Pregunta 1 → Puntaje: 20.00
  Pregunta 2 → Puntaje: 20.00
  Pregunta 3 → Puntaje: 20.00
  Pregunta 4 → Puntaje: 20.00
  Pregunta 5 → Puntaje: 20.00
```

---

### Paso 9: VERIFICAR LA AUDITORÍA EN CHATTER

1. **Desplazarse hacia abajo** hasta el final del formulario
2. **Buscar la sección "Chatter"** (mensajes de discusión)
3. **Verificar que haya un mensaje nuevo** de auto-scoring

**Mensaje esperado en Chatter:**
```
[Auto-Scoring] Distribución de puntajes inicial: 20.00 puntos 
por pregunta (5 preguntas sin puntaje) | Usuario: [Tu nombre]
```

---

## 🎯 PRUEBA 2: Verificar Rechazo - Cuestionario con Puntajes Previos

### Objetivo
Verificar que el botón rechaza cuestionarios que **ya tienen puntajes asignados**.

### Pasos

1. **Crear un NUEVO cuestionario** con el mismo proceso anterior
   - Nombre: "Quiz Test - Con Puntajes"
   - Agregar 3 preguntas

2. **EN LUGAR DE DEJAR VACÍO EL PUNTAJE,** asignar valores:
   ```
   Pregunta 1 → Puntaje: 25.00
   Pregunta 2 → Puntaje: 25.00
   Pregunta 3 → Puntaje: 25.00
   ```

3. **Guardar el cuestionario**

4. **Hacer clic** en el botón "🎯 Auto-calcular Puntajes"

**Resultado esperado:**
```
✗ ADVERTENCIA (Notificación roja)

El cuestionario ya tiene puntajes asignados en todas sus preguntas. 
No se realizó ningún cambio.
```

**Pantalla esperada:**
- Notificación en color rojo/naranja
- Los puntajes NO cambian (siguen siendo 25.00)
- Chatter no registra cambios

---

## 🎯 PRUEBA 3: Verificar Rechazo - Estado Incorrecto

### Objetivo
Verificar que el botón solo funciona en estado "Draft" o "In-Progress".

### Pasos

1. **Abrir el primer cuestionario** (Quiz Test - Auto-Scoring)
   - Debe estar ya procesado con puntajes de 20.00

2. **Cambiar el estado a "Done":**
   - Hacer clic en el campo de "Estado" (State)
   - Seleccionar "Done"
   - Guardar

3. **Hacer clic** en el botón "🎯 Auto-calcular Puntajes"

**Resultado esperado:**
```
✗ ADVERTENCIA (Notificación roja)

Solo se pueden auto-calcular puntajes en cuestionarios 
en estado 'Draft' o 'In-Progress'.
```

**Botón esperado:**
- El botón debe estar **GRIS/DESHABILITADO** cuando el estado NO es Draft/Open

---

## 🎯 PRUEBA 4: Simular Intentos de Estudiantes (Opcional pero Recomendado)

### Objetivo
Verificar que los intentos se recalculan y se sincronizan con el boletín.

### Pasos Previos (Setup)

1. **Cambiar el estado del cuestionario a "Open":**
   - Hacer clic en "Abrir" (Open button)
   - Confirmar la acción

2. **Cambiar estado nuevamente a "Draft":**
   - Esto permite volver a ejecutar auto-scoring

### Crear un Resultado (Intento)

1. **Ir a:** Educación > Cuestionarios > Resultados (Results)
2. **Hacer clic en "Crear"**
3. **Rellenar:**
   - Quiz: El cuestionario creado anteriormente
   - Estudiante: Crear uno nuevo o seleccionar existente
   - Estado: "Done"

4. **Agregar respuestas del estudiante:**
   - En la sección "Líneas de Resultado"
   - Agregar líneas para cada pregunta
   - Marcar respuestas: algunas correctas, algunas incorrectas
   ```
   Pregunta 1 → Respuesta correcta: "Lima" ✓
   Pregunta 2 → Respuesta incorrecta: "Mississippí" ✗
   Pregunta 3 → Respuesta correcta: "7" ✓
   Pregunta 4 → Respuesta incorrecta: "Dólar" ✗
   Pregunta 5 → Respuesta correcta: "1821" ✓
   ```

5. **Guardar el resultado**

### Ejecutar Auto-Scoring

1. **Volver al cuestionario**
2. **Cambiar estado a "Draft"** (si no está ya)
3. **Hacer clic en** "🎯 Auto-calcular Puntajes"

**Notificación esperada:**
```
✓ Auto-scoring completado exitosamente.
- 5 preguntas fueron configuradas con 20.00 puntos cada una
- 1 intento de estudiante fue re-evaluado
- Puntaje total del cuestionario: 100.00 puntos
```

### Verificar Resultado Actualizado

1. **Ir a Educación > Cuestionarios > Resultados**
2. **Abrir el resultado creado**
3. **Verificar puntuajes:**
   ```
   ESPERADO:
   Pregunta 1: 20.00 puntos (correcto)
   Pregunta 2: 0 puntos (incorrecto)
   Pregunta 3: 20.00 puntos (correcto)
   Pregunta 4: 0 puntos (incorrecto)
   Pregunta 5: 20.00 puntos (correcto)
---

## ⚠️ CHECKLIST DE VERIFICACIÓN FINAL

Cuando termines todas las pruebas, verifica estos puntos:

### ✅ Prueba 1 - Auto-Scoring Básico
- [ ] Botón visible en survey de tipo quiz/exam/cert
- [ ] Tooltip muestra la descripción de acción
- [ ] Click en botón crea notificación verde
- [ ] Puntajes se asignan correctamente (100/5 = 20)
- [ ] Chatter registra la acción

### ✅ Prueba 2 - Rechazo con Puntajes
- [ ] Notificación de error al intentar auto-calcular
- [ ] Los puntajes NO cambian

### ✅ Prueba 3 - Validación de Tipo Survey
- [ ] Botón gris en surveys de tipo assessment/feedback
- [ ] Error al intentar ejecutar en tipo inválido

---

## 📊 EJEMPLO VISUAL DEL FLUJO

```
┌─────────────────────────────────────────┐
│  Crear Cuestionario                     │
│  Nombre: "Quiz Test - Auto-Scoring"     │
│  Estado: Draft                          │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Agregar 5 Preguntas SIN PUNTAJE        │
│  ✓ Pregunta 1 (puntaje vacío)           │
│  ✓ Pregunta 2 (puntaje vacío)           │
│  ✓ Pregunta 3 (puntaje vacío)           │
│  ✓ Pregunta 4 (puntaje vacío)           │
│  ✓ Pregunta 5 (puntaje vacío)           │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Guardar Cuestionario                   │
│  ✓ Cambios guardados                    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  🎯 Auto-calcular Puntajes              │
│  (Esperar tooltip + hacer clic)         │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Sistema Procesa:                       │
│  1 VALIDAR ESTADO                       │ ✓
│  2 VERIFICAR PREGUNTAS                  │ ✓
│  3 DISTRIBUIR PUNTAJES                  │ ✓ (20 c/u)
│  4 PROCESAR INTENTOS                    │ ✓ (0 intentos)
│  5 SINCRONIZAR GRADEBOOK                │ ✓ (si existe)
│  6 REGISTRAR AUDITORÍA                  │ ✓
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  ✓ NOTIFICACIÓN VERDE                   │
│                                         │
│  Auto-scoring completado exitosamente   │
│  - 5 preguntas → 20 puntos c/u          │
│  - 0 intentos re-evaluados              │
│  - Total: 100 puntos                    │
└─────────────────────────────────────────┘
```

---

## 🆘 TROUBLESHOOTING

### Problema: El botón no aparece

**Causas posibles:**
1. Módulo no instalado correctamente
2. No tiene permisos suficientes (necesita ERP Manager)
3. Caché de navegador - presione `Ctrl+Shift+R` para limpiar

**Solución:**
```bash
odoo -u irg_quiz_auto_scoring -d <db> --stop-after-init
```

### Problema: El botón está gris/deshabilitado

**Causas posibles:**
1. Estado del cuestionario NO es "Draft" o "Open" (states="draft,open")
2. El cuestionario ya está en estado "Done"

**Solución:**
- Cambiar survey_type a quiz/exam/cert

### Problema: Error al hacer clic

**Causas posibles:**
1. Las preguntas ya tienen puntajes
2. No hay preguntas en el survey
3. El módulo survey no está disponible

**Solución:**
- Verificar los logs de Odoo: `tail -f /var/log/odoo/odoo.log`

### Problema: Los puntajes no se asignaron

**Causas posibles:**
1. Las preguntas ya tenían puntajes
2. El módulo no heredó correctamente

**Solución:**
- Verificar que visible.mark está en 0 o NULL antes de ejecutar

---

## ✨ Conclusión

Con esta guía deberías poder:
✅ Instalar y activar el módulo  
✅ Crear cuestionarios sin puntaje  
✅ Ejecutar auto-scoring exitosamente  
✅ Verificar que los puntajes se asignaron  
✅ Ver la auditoría en chatter  
✅ Validar restricciones de estado  

**¡El módulo está completamente funcional!**
