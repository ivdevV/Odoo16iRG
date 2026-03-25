# Guía de Uso: Sistema de Importación de Calendarios Académicos iRG

**Módulos Odoo:** `irg_timetable_csv_import` + `irg_timetable_csv_upload_portal` | **Versión:** 16.0.1.0.0 | **Estado:** Activo

---

## 📋 Tabla de Contenidos

1. [Descarga de Calendarios desde Google Drive](#descarga-de-calendarios)
2. [Consolidación de Calendarios (Python)](#consolidación-de-calendarios)
3. [Instalación de Módulos en Odoo](#instalación-del-módulo)
4. [Configuración en Odoo](#configuración-en-odoo)
5. [Importación del CSV (Opción A: Portal Web)](#importación-portal-web)
6. [Importación del CSV (Opción B: Manual/Terminal)](#importación-del-csv)
7. [Monitoreo y Resolución de Errores](#monitoreo)
8. [FAQ](#faq)

---

## 1. Descarga de Calendarios desde Google Drive {#descarga-de-calendarios}

### Paso 1.1: Acceder a Google Drive

Ingresa a **Google Drive > Carpeta "Calendarios 365-2026-2027"**

```
https://drive.google.com/drive/folders/[ID_CARPETA]
```

### Paso 1.2: Descargar cada Sheet

Dentro de la carpeta hay **múltiples Google Sheets**, uno por cada **Máster/Programa**. Por ejemplo:

- `Calendario NC 365`
- `Calendario ND 365`
- `Calendario NL 365`
- etc.

**Para cada uno:**

1. Abre el sheet en Google Sheets
2. Haz clic en **Archivo > Descargar > Microsoft Excel (.xlsx)**
3. Guarda el archivo en una **carpeta local**, por ejemplo: `C:\Calendarios\` o `/home/user/calendarios/`

✅ **Resultado esperado:** Una carpeta con varios archivos `.xlsx` (uno por máster)

```
Calendarios/
├── Calendario NC 365.xlsx
├── Calendario ND 365.xlsx
├── Calendario NL 365.xlsx
├── Calendario ... .xlsx
└── ...
```

> **Nota:** Google Sheets puede descargarse con nombres largos — esto es normal.

---

## 2. Consolidación de Calendarios {#consolidación-de-calendarios}

### Paso 2.1: Crear el Script Python

En la **misma carpeta** donde descargaste los Excel (ej: `C:\Calendarios\`), crea un archivo llamado:

**`consolidar_calendarios.py`**

Copia el siguiente código:

```python
import os
import pandas as pd
import glob

ruta_carpeta = '.' 
archivos_excel = glob.glob(os.path.join(ruta_carpeta, '*.xlsx'))

lista_dataframes = []

print("Iniciando consolidación avanzada de calendarios iRG...\n")

for archivo in archivos_excel:
    if os.path.basename(archivo).startswith('~$'):
        continue
        
    nombre_master = os.path.basename(archivo).replace('.xlsx', '').strip()
    
    try:
        tabs = pd.read_excel(archivo, sheet_name=None, engine='openpyxl', header=None)
        
        for nombre_pestaña, df_tab in tabs.items():
            header_idx = -1
            for i, row in df_tab.iterrows():
                valores_fila = [str(val).lower().strip() for val in row.values]
                if 'fecha' in valores_fila or 'nombre asignatura' in valores_fila or 'asignatura' in valores_fila:
                    header_idx = i
                    break
            
            if header_idx == -1:
                print(f"ℹ️ Omitiendo pestaña oculta/vacía '{nombre_pestaña}' en '{nombre_master}'.")
                continue
                
            df_tab.columns = df_tab.iloc[header_idx].astype(str).str.strip()
            df_tab = df_tab.iloc[header_idx + 1:].copy()
            
            columnas_a_mantener = {}
            for col in df_tab.columns:
                # HOTFIX: Forzar conversión a string antes de pasar a minúsculas
                # Esto evita el error de "float object has no attribute lower"
                col_lower = str(col).lower() 
                if 'fecha' in col_lower: 
                    columnas_a_mantener[col] = 'Fecha'
                elif 'asignatura' in col_lower: 
                    columnas_a_mantener[col] = 'Nombre Asignatura'
                elif 'docente' in col_lower or 'profesor' in col_lower: 
                    columnas_a_mantener[col] = 'Docente'
            
            if columnas_a_mantener:
                df_tab = df_tab[list(columnas_a_mantener.keys())].rename(columns=columnas_a_mantener)
                df_tab.dropna(how='all', inplace=True)
                df_tab = df_tab[~df_tab['Fecha'].astype(str).str.contains('fuerza mayor', case=False, na=False)]
                
                df_tab.insert(0, 'Pestaña Origen', nombre_pestaña)
                df_tab.insert(0, 'Máster/Programa', nombre_master)
                
                lista_dataframes.append(df_tab)
                
        print(f"✅ Procesado con éxito: {nombre_master}")
        
    except Exception as e:
        print(f"❌ Error procesando {nombre_master}: {str(e)}")

if lista_dataframes:
    df_global = pd.concat(lista_dataframes, ignore_index=True)
    archivo_salida = 'Calendario_Global_iRG.csv'
    df_global.to_csv(archivo_salida, index=False, sep=';', encoding='utf-8-sig', decimal=',')
    
    print(f"\n🚀 ¡Proceso completado al 100%! Archivo generado: {archivo_salida}")
    print(f"Total de registros consolidados: {len(df_global)}")
else:
    print("\n⚠️ No se procesaron datos.")
```

### Paso 2.2: Ejecutar el Script

Abre una **terminal (PowerShell, CMD o Bash)** en la carpeta de Calendarios:

```bash
# En Windows (PowerShell o CMD)
cd C:\Calendarios\
python consolidar_calendarios.py

# En macOS/Linux
cd /home/user/calendarios/
python3 consolidar_calendarios.py
```

### Paso 2.3: Verificar el Resultado

Si todo funciona, verás algo como:

```
Iniciando consolidación avanzada de calendarios iRG...

✅ Procesado con éxito: Calendario NC 365
✅ Procesado con éxito: Calendario ND 365
✅ Procesado con éxito: Calendario NL 365
...

🚀 ¡Proceso completado al 100%! Archivo generado: Calendario_Global_iRG.csv
Total de registros consolidados: 1487
```

✅ **Se ha creado:** `Calendario_Global_iRG.csv` en la misma carpeta

---

## 3. Instalación de Módulos en Odoo {#instalación-del-módulo}

### Paso 3.1: Instalar `irg_timetable_csv_import`

Este es el módulo base que procesa los CSVs. Debe estar instalado:

```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
  -d odoo16_production \
  -i irg_timetable_csv_import \
  --stop-after-init \
  --db_host=pgodoo_latest \
  --log-level=info
```

### Paso 3.2: Instalar `irg_timetable_csv_upload_portal` (Recomendado)

Este módulo agrega la interfaz web para que gestores suban CSVs sin acceder a la terminal:

```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
  -d odoo16_production \
  -i irg_timetable_csv_upload_portal \
  --stop-after-init \
  --db_host=pgodoo_latest \
  --log-level=info
```

### Paso 3.3: Verificar la Instalación

Entra al panel de Odoo y ve a **Aplicaciones > Módulos instalados** → busca ambos módulos

Deben aparecer como **Instalados** ✅

---

## 4. Configuración en Odoo {#configuración-en-odoo}

### Paso 4.1: Configurar el Directorio de Vigilancia (`watch_dir`)

1. En Odoo, ve a **Ajustes > Técnicos > Parámetros del sistema**
2. **Busca o crea:** `irg_timetable_csv_import.watch_dir`
3. **Establece el valor:** La ruta del directorio donde colocarás los CSV

   **Ejemplo Windows:**
   ```
   C:\Calendarios\
   ```
   
   **Ejemplo Linux/Docker:**
   ```
   /mnt/calendarios/
   ```

4. Guarda.

> **Nota:** El directorio debe existir previamente. Si es dentro de Docker, copia o monta el directorio en el contenedor.

### Paso 4.2: Crear Mapeos de Programas (Program Maps)

El módulo necesita saber **qué Máster/Programa CSV** corresponde a **qué Curso** en Odoo.

1. Ve a **Horarios > Configuración > Mapeos iRG**
2. Para **cada programa**, crea un registro:

| Campo | Valor | Ejemplo |
|-------|-------|---------|
| **CSV Label** | Nombre exacto del programa en el CSV | `Calendario NC 365` |
| **Curso** | El curso en Odoo (Many2one) | `NC (16.0.1.0)` |
| **Lote (opcional)** | Si quieres un lote específico | `Lote 2026-1` |
| **Activo** | Sí | ✓ |

**Ejemplo de configuración para los 26 programas:**

```
CSV Label                    | Curso  | Lote (opcional)
──────────────────────────────────────────────────────
Calendario NC 365           | NC     | —
Calendario ND 365           | ND     | —
Calendario NL 365           | NL     | —
Calendario MPC 365          | MPC    | —
Calendario MSC 365          | MSC    | —
Calendario MPI 365          | MPI    | —
Calendario MNC 365          | MNC    | —
Calendario MND 365          | MND    | —
Calendario MTG 365          | MTG    | —
Calendario MTF 365          | MTF    | —
Calendario MDA 365          | MDA    | —
Calendario MNL 365          | MNL    | —
Calendario MTA 365          | MTA    | —
Calendario MIP 365          | MIP    | —
Calendario MIA 365          | MIA    | —
Calendario MEN 365          | MEN    | —
Calendario MRN 365          | MRN    | —
Calendario DC 365           | DC     | —
Calendario LD 365           | LD     | —
Calendario CS 365           | CS     | —
Calendario LG 365           | LG     | —
Calendario IA 365           | IA     | —
Calendario TG 365           | TG     | —
Calendario HD 365           | HD     | —
(y más según se agreguen)    |        |
```

> **💡 Consejo:** Copia/pega los nombres exactos desde el CSV generado para evitar errores de coincidencia.

---

## 5. Importación del CSV (Opción A: Portal Web) {#importación-portal-web}

### 🎯 Recomendado para Gestores

Si instalaste `irg_timetable_csv_upload_portal`, es la forma más segura y cómoda.

### Paso 5.1: Acceder al Portal Web

1. Entra a Odoo como **gestor o administrador**
2. Ve a la página **Mi Campus** (`/campus`)
3. Verás una nueva tarjeta: **"Actualizar Calendarios"** (con icono de nube ☁️)
4. Haz clic en ella

### Paso 5.2: Subir el CSV

1. En la página de upload, selecciona el archivo `Calendario_Global_iRG.csv`
2. Verifica que cumple los requisitos:
   - Extensión: `.csv`
   - Encoding: **UTF-8**
   - Columnas requeridas: `Máster/Programa`, `Fecha`, `Nombre Asignatura`, `Docente`
3. Haz clic en **"Subir y Procesar"**

### Paso 5.3: Confirmación

- Si todo es correcto, verás: **"✓ Excelente! El archivo se subió correctamente."**
- El sistema copiará el archivo a `watch_dir` automáticamente
- El cron procesará el CSV en la próxima ejecución (cada 6 horas)

### Historial

En la misma página ves el **Historial de Uploads** (últimos 5 intentos) con estado:
- 🟡 **Pendiente** — recientemente subido
- 🔄 **Procesando** — en la cola del cron
- ✅ **Completado** — importación exitosa
- ❌ **Error** — revisa el mensaje de error

---

## 6. Importación del CSV (Opción B: Manual/Terminal) {#importación-del-csv}

### Paso 6.1: Copiar el CSV al Directorio de Vigilancia

1. Copia el archivo generado `Calendario_Global_iRG.csv` 
2. Colócalo en el directorio configurado en **Paso 4.1**

   **Windows:** `C:\Calendarios\Calendario_Global_iRG.csv`
   
   **Docker:** Copia al contenedor o monta el volumen

### Paso 6.2: Disparar la Importación (Automática o Manual)

#### **Opción A: Cron Automático (Recomendado)**

El módulo tiene un **cron que se ejecuta cada 6 horas** automáticamente. Solo necesitas esperar.

#### **Opción B: Importación Manual (Para Testing)**

1. En Odoo, ve a **Horarios > Importación CSV > Logs de importación**
2. Alterna: ejecuta el cron manualmente desde **Ajustes > Técnicos > Acciones Programadas**
   - Busca `irg_timetable_csv_import: Procesar directorio de CSV`
   - Abre el registro y haz clic en el botón **Ejecutar Ahora** (si existe)

---

## 7. Monitoreo y Resolución de Errores {#monitoreo}

### Paso 7.1: Revisar Logs de Importación

1. Ve a **Horarios > Importación CSV > Logs de importación**
2. Verás una tabla con cada importación realizada:

| Archivo | Fecha | Estado | Sesiones Creadas | Actualizadas | Errores |
|---------|-------|--------|------------------|--------------|---------|
| `Calendario_Global_iRG.csv` | 2026-03-25 16:30 | ✅ OK | 1487 | 0 | — |

### Paso 7.2: Interpretar Estados

| Estado | Significado | Acción |
|--------|-------------|--------|
| **OK** ✅ | Sin errores; todas las sesiones se crearon/actualizaron | Nada — todo bien |
| **Advertencias** ⚠️ | Se importó parcialmente; algunos datos ignorados o vinculados aproximadamente | Revisa el detalle de errores |
| **Error** ❌ | No se importó nada (problemas graves) | Revisa los logs; consulta [FAQ](#faq) |

### Paso 7.3: Leer Detalles de Errores

Haz clic en un log para ver la **sección "Detalle de errores / advertencias"**:

**Ejemplos comunes:**

```
Sin mapeo configurado para "Calendario XX 365" — 150 fila(s) omitida(s). 
Añade el mapeo en Horarios > Configuración > Mapeos CSV.
```
→ **Solución:** Crea el mapeo faltante (Paso 4.2)

```
Asignatura no encontrada: "Fundamentos de Python" [Calendario NC 365 2026-03-20]
```
→ **Solución:** Verifica que la asignatura exista en el curso NC; añádela si falta

```
Docente no encontrado: "Dr. Juan Pérez" [Calendario NC 365 2026-03-20]
```
→ **Solución:** Crea el docente en **Contactos > Docentes** o verifica el nombre exacto

---

## 8. FAQ {#faq}

### P1. ¿Qué pasa si el CSV tiene fechas en formato incorrecto?

**R:** El script lo detecta automáticamente y salta las filas mal formadas. Verifica que tus Excel uses formato `DD/MM/YYYY` en la columna Fecha.

### P2. ¿Qué significa "Pestaña Origen" en el CSV consolidado?

**R:** Es el nombre de la hoja/pestaña del Excel original de cada máster. Se usa solo para auditoría; el sistema la ignora en la importación.

### P3. ¿Se crean las sesiones automáticamente o hay que aprobarlas manualmente?

**R:** Se crean **automáticamente** con estado **"Confirmado"**. Los alumnos las ven de inmediato en el calendario.

### P4. ¿Qué ocurre con la habilitación de contenido de asignaturas?

**R:** 
- El CSV genera **sesiones de clase** (op.session)
- El módulo **actualiza automáticamente** `op.subject.to.batch` (fecha_habilitación_contenido)
- **Regla:** El contenido se habilita **72 horas antes** de la primera sesión
- Esto lo controla automáticamente el cron existente `cron_auto_enroll_student()` — no requiere configuración manual

### P5. ¿Cómo vuelvo a importar si cambio el CSV?

**R:** Solo copia/sube el nuevo CSV — el sistema:
- **Crea** sesiones nuevas
- **Actualiza** sesiones existentes (si fecha/docente cambió)
- **No borra** nada (es seguro)  

### P6. ¿Qué usuario necesita para el portal web?

**R:** Solo **gestores de sitio web** (`website.group_website_publisher`) o **administradores Odoo** (`base.group_erp_manager`). Usuarios normales no ven la tarjeta ni pueden acceder a `/campus/csv-upload`.

### P7. ¿Qué pasó con el método manual de upload (terminal)?

**R:** Sigue funcionando. Puedes:
1. **Opción A (recomendada):** Usar el portal web (más seguro)
2. **10. ¿Qué pasa si un docente o asignatura no existe?

**R:** Se registra un **error** en el log y esa fila se salta. Crea el docente/asignatura en Odoo y re-ejecuta la importación.

### P11. ¿Necesito instalar Python localmente?

**R:** **Sí.** Para el script `consolidar_calendarios.py` necesitas:
- Python 3.8+
- `pandas` (instalable con `pip install pandas openpyxl`)

**Pero NOT para usar el portal web** — ese funciona 100% en Odoo sin requisitos locales.los últimos 5 uploads con estado
2. **Backend Odoo:** En **Horarios > Uploads Web** ves el historial completo (solo admins)

### P9. ¿Dónde veo los logs de error del servidor?

**R:** Dentro del contenedor Docker:
```bash
docker logs odoo_latest | tail -50
```
O revisa el archivo de log de Odoo (configurado en `odoo.conf`).

### P7. ¿Qué pasa si un docente o asignatura no existe?

**R:** Se registra un **error** en el log y esa fila se salta. Crea el docente/asignatura en Odoo y re-ejecuta la importación.

### P8. ¿Necesito instalar Python localmente?

**R:** Sí. Requiere:
- Python 3.8+
- `pandas` (instalable con `pip install pandas openpyxl`)

---

### Flujo Completo (con Portal Web — Recomendado)

```
1. Descarga sheets desde Google Drive (.xlsx)
   ↓
2. Ejecuta consolidar_calendarios.py (local — una sola vez)
   ↓
3. Genera Calendario_Global_iRG.csv
   ↓
4. Instala ambos módulos en Odoo:
   - irg_timetable_csv_import
   - irg_timetable_csv_upload_portal  ← NUEVO
   ↓
5. Configura watch_dir + Mapeos CSV en Odoo
   ↓
6. Entra a /campus > Tarjeta "Actualizar Calendarios"
   ↓
7. Sube Calendario_Global_iRG.csv vía portal web (seguro, sin terminal)
   ↓
8. Cron (cada 6h) procesa el CSV automáticamente
   ↓
9. Revisa estado en /campus/csv-upload > Historial
   ↓
10. ✅ Sesiones creadas + contenido habilitado automáticamente
```

### Flujo Alternativo (sin Portal Web — Manual)

```
1-3. [igual]
4. Instala solo: irg_timetable_csv_import
5. [igual]
6-7. Copia CSV manualmente a watch_dir (terminal/SSH)
8-10. [igual]
   ↓
10. ✅ Sesiones creadas + contenido habilitado automáticamente
```

---

## 📞 Soporte

Si encuentras un error:

1. **Revisa la sección 6 (Monitoreo)**
2. **Consulta la sección 7 (FAQ)**
3. **Si persiste:** contacta al equipo de desarrollo y proporciona:
   - Archivo CSV problemático
   - Log de error completo (desde Odoo o docker logs)
   - Versión del módulo (`irg_timetable_csv_import`)

---

**Última actualización:** Marzo 2026 | **Versión:** 1.0
