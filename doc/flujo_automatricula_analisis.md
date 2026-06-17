# INFORME EXHAUSTIVO: FLUJO DE AUTOMATRÍCULA EN ODOO 16 (PROYECTO ISEP/IRG)

## RESUMEN EJECUTIVO

El flujo de **automatrícula** se dispara automáticamente cuando una **orden de venta (sale.order)** es confirmada manualmente o por pago online. El proceso involucra múltiples módulos que trabajan coordinadamente para:

1. Crear registros de admisión (op.admission)
2. Enrollar estudiantes (op.student)
3. Crear usuarios del portal (res.users)
4. Inscribir en canales de e-learning (slide.channel.partner)
5. Enviar correos de bienvenida
6. Generar facturas automáticas

---

## 1. PUNTO DE ENTRADA — AUTOCONFIRMACIÓN DE PRESUPUESTO

### 1.1 Hook Principal: `_action_confirm()`

**Ubicación**: Dos implementaciones principales:

#### A. IMPLEMENTACIÓN PRIMARIA (Más Completa)
- **Archivo**: `/addons_uisep/isep_sale_order_admissions/models/sale_order.py` (líneas 29-69)
- **Modelo**: `SaleOrderAdmission` (_inherit 'sale.order')
- **Método**: `_action_confirm()`

**Lógica**:
```
1. Llama a super()._action_confirm() para confirmar primero la SO en Odoo
2. Valida si no hay 'period', calcula _compute_period()
3. Filtra líneas de venta que sean:
   - is_academic_program = True
   - recurring_invoice = True
4. Maneja DOS CASOS:

   CASO 1 (Una línea académica):
   - Crea/obtiene admission con _create_or_get_admission()
   - Asigna admission_id a sale.order
   - Procesa automáticamente con _process_auto_admission()

   CASO 2 (Múltiples líneas académicas):
   - Itera cada línea
   - Usa One2many (sale.order.admission.line)
   - Crea una fila de rastreo por línea
   - Procesa cada admisión
```

#### B. IMPLEMENTACIÓN SECUNDARIA (Más Simple)
- **Archivo**: `/addons_uisep/isep_openeducat_sale/models/sale_order.py` (líneas 95-108)
- **Modelo**: `SaleOrder` (_inherit 'sale.order')
- **Método**: `_action_confirm()`

**Lógica Simplificada**:
```
1. Valida language del curso
2. Llama get_academic_product_template_id()
3. Obtiene register_id con get_register_id()
4. Crea/obtiene admisión con get_admision_id()
5. Si mx/br_state_admission_done: ejecuta transiciones de estado
6. Si mx/br_auto_email_welcome: envía correo
```

### 1.2 Métodos Críticos de Creación

#### `_create_or_get_admission()` (isep_sale_order_admissions)
**Ubicación**: Líneas 72-130

**Proceso**:
1. **Búsqueda de Curso**: por `product_template_id` en `op.course`. Si no existe → fila error en `sale.order.admission.line`.
2. **Período**: `_compute_period()` si no existe. Valida (01, 02, 03).
3. **Registro de Admisión** (`op.admission.register`):
   - Busca existente: state IN ('confirm','application','admission'), periodo, product_template
   - Si state='confirm' → `start_application()` → 'application'
   - Si NO existe → crea con `course_id`, `product_template_id`, `period`, `start_date`=hoy, `end_date` calculado por periodo (meses 1-4=ene, 5-7=may, 8-12=ago)
4. **Creación de Admisión** (`op.admission`):
   - Valida que no exista
   - Parsea nombre en first/last
   - Campos: `sale_id`, `partner_id`, `email`, `mobile`, `phone`, `gender`, `batch_id` (vía `get_lot_id()`), `fees_term_id` (primer término), `application_date`, `admission_date`, `state`='draft'

#### `_process_auto_admission()` (isep_sale_order_admissions)
**Ubicación**: Líneas 133-168

```
IF auto.admission.required.{mx|br}_active = TRUE:

  IF {mx|br}_state_admission_done = TRUE:
    1. admission.submit_form()           → state = 'submit'
    2. admission.confirm_in_progress()   → state = 'confirm'
    3. admission.admission_confirm()     → state = 'admission'
    4. admission.enroll_student()        → state = 'done'
                                         (+ crea op.student, res.users)

  IF {mx|br}_auto_email_welcome = TRUE:
    admission.send_mail_view()           → envía email_op_admission_confirm

ELSE IF error:
  - Crea fila error en sale.order.admission.line
  - order.error_admission = True
  - Registra excepción en error_admission_msn
```

### 1.3 Triggers Automáticos vs Manuales

**AUTOMÁTICOS (Solo en _action_confirm automático)**:
- Creación de `op.admission` desde pago online
- Transiciones de estado automáticas (submit → confirm → admission → done)
- Creación de `op.student` + `res.users`
- Inscripción en canales de e-learning (después de done)
- Envío de email de bienvenida

**SOLO MANUALES (Si se confirma sin automatrícula)**:
- No se crea admisión automáticamente
- No se crea estudiante
- No se crea usuario
- No se inscribe en e-learning
- No se envía email de bienvenida
- **Solución**: `action_get_admision_id_manual()` o `action_get_register_id()`

---

## 2. PROCESO DE ADMISIÓN

### 2.1 Modelos Involucrados

| Modelo | Archivo | Descripción |
|--------|---------|-------------|
| **op.admission** | `community-16/openeducat_admission/models/admission.py` | Registro de admisión |
| **op.admission.register** | Community OpenEduCat | Convocatoria de admisión |
| **op.course** | Community OpenEduCat | Programa académico |
| **op.batch** | Community OpenEduCat | Lote/grupo |
| **op.student** | Community OpenEduCat | Registro estudiante |
| **op.fees.terms** | Community OpenEduCat | Términos cuotas |
| **res.partner** | Odoo core | Contacto |

### 2.2 Estados y Transiciones (`op.admission`)

```
draft
  → submit_form()         → submit
  → confirm_in_progress() → confirm
  → admission_confirm()   → admission
  → enroll_student()      → done  (Estado final activo)

OTROS: pending, reject, cancel, down
```
Archivo: `community-16/openeducat_admission/models/admission.py` líneas 223-231

### 2.3 Creación de `op.batch` (Lote)

**Método**: `get_lot_id(course_id)`

> **⚠️ IMPORTANTE**: Este método existe en DOS módulos. El módulo `irg_openeducat_sale_lote_custom` **sobreescribe completamente** la implementación de `isep_openeducat_sale`. En producción se ejecuta SOLO la versión IRG custom.

#### Versión ORIGINAL (isep_openeducat_sale — NO activa si irg_openeducat_sale_lote_custom está instalado)

```
code = {categ_code}{course_code}GE{month}{year}{lang_letter}
Ejemplo: MX123GE0125E (mes 01, año 25, español)
```

#### Versión ACTIVA (irg_openeducat_sale_lote_custom/models/sale_order.py — L11-144)

```
code = {categ_code}{course_code}{modalidad_prefix}{year}{month}
Ejemplo: MX123ONL2501  (Online, año 25, mes 01)
         MX123HC2501   (HomeClass, año 25, mes 01)
         MX123PRS2501  (Presencial, año 25, mes 01)
         MX123GE2501   (sin modalidad detectada)

DIFERENCIAS clave respecto a versión original:
  1. prefix_02 NO es 'GE' fijo — se lee del atributo de producto 'Modalidad':
       'Online'     → 'ONL'
       'HomeClass'  → 'HC'
       'Presencial' → 'PRS'
       otro/ninguno → 'GE' (fallback)
  2. Orden año/mes INVERTIDO: {year}{month} no {month}{year}
  3. SIN sufijo de idioma (prefix_06 eliminado)

LÓGICA DE FECHA (admission_date):
  - Si modalidad IN ['HC', 'PRS']:
      - Si hoy.day > 7 Y admission_date está en el mes actual → date += 1 mes
      - batch start_date = date.replace(day=1)   (primer día del mes)
  - Si modalidad = 'ONL' o 'GE':
      - Sin desplazamiento de fecha
      - batch start_date = date (tal cual)

DETECCIÓN DE categ_code (profix_01) — por prioridad:
  1. product.categ_id.code de la línea de venta que coincide con el curso
  2. course_id.product_template_id.categ_id.code
  3. course_id.product_template_ids[0].categ_id.code

Si no existe batch → crea con:
  - tutor_id, professor_id, coordinator, teams_domain, teams_link,
    teams_msg, modality_id  (desde auto.admission.required según lang)
  - start_date = batch_start_date (según lógica arriba)
  - end_date   = start_date + 1 año
```

#### Módulos Extensión de `op.batch` (campos adicionales al modelo base)

> El modelo base `op.batch` (community-16/openeducat_core) solo tiene campos esenciales (name, code, course_id, start_date, end_date, etc.). Los siguientes módulos lo extienden:

| Módulo | Archivo | Campos / Comportamiento añadidos |
|--------|---------|----------------------------------|
| **isep_openeducat_sale** | `addons_uisep/isep_openeducat_sale/models/op_batch.py` | `tutor_id` (Many2one res.users), `professor_id` (Many2one res.users), `teams_domain`, `teams_link`, `teams_msg`. **Crítico**: son los que se asignan desde `get_lot_id()` tomando valores de `auto.admission.required`. |
| **isep_elearning_custom** | `addons_uisep/isep_elearning_custom/models/op_batch.py` | `subject_to_batch_ids` (One2many → `op.subject.to.batch`). **Crítico para e-learning**: al crear/editar batch con `course_id`, auto-crea un registro `op.subject.to.batch` por cada asignatura del curso. Es la tabla que itera `cron_auto_enroll_student()`. |
| **isep_data_master_make** | `addons_uisep/isep_data_master_make/models/op_batch.py` | `date_start_class` (Date) — fecha real de inicio de clases (distinta de `start_date`). |
| **isep_control_escolar** | `addons_uisep/isep_control_escolar/models/op_batch.py` | `company_type`, `scholar_year`, `cct`, `educational_mod`, `shift_type` — campos institucionales MX (SEP). |
| **irg_batch_subject_schedule_manual** | `extrairg/irg_batch_subject_schedule_manual/models/op_batch.py` | `irg_course_subject_ids` (related readonly a `course_id.subject_ids`). Modifica `write()` para saltar validación de asignaturas al cambiar `course_id`. |
| **isep_program_sepyc** | `addons_uisep/isep_program_sepyc/models/op_batch.py` | Onchange `sepyc_program` que propaga flag a todos los estudiantes del lote. |

#### Modelo `op.subject.to.batch` (isep_elearning_custom)

**Archivo**: `addons_uisep/isep_elearning_custom/models/op_batch.py`

```
Campos:
  subject_id  → Many2one op.subject
  batch_id    → Many2one op.batch
  code        → Char (código asignatura)
  date_from   → Date (inicio ventana de acceso e-learning)
  date_to     → Date (fin ventana de acceso e-learning)

Validaciones onchange:
  - date_from >= batch_id.start_date
  - date_to   <= batch_id.end_date

Creación automática:
  - Al crear op.batch con course_id → se crean registros por cada subject en course.subject_ids
  - Al cambiar course_id en batch existente → se eliminan los anteriores y se recrean
```

**Rol en el flujo**: `cron_auto_enroll_student()` itera `batch_id.subject_to_batch_ids` y usa `date_from`/`date_to` de cada registro para determinar si crear `slide.channel.partner` activo o inactivo. Sin estos registros, el cron NO inscribe al estudiante en ningún canal e-learning.

### 2.4 Creación de `op.student` y Vinculación

**Método**: `enroll_student()` (community-16/openeducat_admission, líneas 286-371)

1. **Validación cupo**: si `register_id.max_count`, cuenta admisiones 'done'; si llega → Error
2. **Crear/Actualizar op.student**:
   - Si NO existe → `get_student_vals()` (líneas 233-284)
   - **Crea res.users**:
     ```
     name, login=email, image_1920, is_student=True,
     company_id, groups_id=[base.group_portal], partner_id auto
     ```
   - **Actualiza partner**: phone, mobile, email, dirección, país, estado, imagen, zip
   - **Crea op.student**: user_id, partner_id, course_detail_ids (course_id, batch_id, academic_years_id, academic_term_id, fees_term_id, fees_start_date, product_id), first_name, last_name, birth_date, gender
   - Si EXISTE student_id → añade nuevo course_detail (multi-curso)
3. **Crear cuotas (`op.fees.detail`)**:
   - Si `fees_term_id.fees_terms` ∈ ['fixed_days','fixed_date']
   - Por cada línea: amount=(value*fees)/100, date=due_date o fees_start_date+due_days, state=draft, discount
4. **Crear registro asignaturas (`op.subject.registration`)**: student, batch, course, min/max_unit_load, state=draft → llama `get_subjects()`

### 2.5 Automatizaciones en `op.admission`

Ubicación: `addons_uisep/isep_elearning_custom/models/op_admission.py`

- **`submit_form()`** (L219): busca user por email, vincula o crea partner. State → 'submit'.
- **`cron_auto_enroll_student()`** (L412): cron diario, admisiones 'done', por cada subject_batch en batch_id.subject_to_batch_ids valida fechas y crea/actualiza `slide.channel.partner`. Pasado date_to → desactiva.

---

## 3. CORREO DE BIENVENIDA Y COMUNICACIONES

### 3.1 Mail Template Principal

**Ubicación**: `/addons_uisep/isep_elearning_custom/data/op_admission_welcome.xml`
**XML ID**: `isep_elearning_custom.email_op_admission_confirm`

```xml
<record id="email_op_admission_confirm" model="mail.template">
  <field name="name">Confirmación de admisión Elearning</field>
  <field name="subject">¡Bienvenido! {{ object.name or '' }}</field>
  <field name="email_from">{{ user.email or '' }}</field>
  <field name="email_to">{{ object.email }}</field>
  <field name="model_id" ref="openeducat_admission.model_op_admission"/>
  <field name="auto_delete" eval="True"/>
  <field name="body_html">...</field>
</record>
```

Variables: `object.partner_id.name`, `object.application_number`, `object.new_password_user`.

### 3.2 Métodos de Envío

**`send_mail()`** (isep_elearning_custom, L297-311):
```python
IF NOT email_send_ok:
  IF NOT tutor_id: RAISE
  IF NOT batch_id.start_date: RAISE
  IF NOT batch_id: RAISE
  template_id = 'isep_elearning_custom.email_op_admission_confirm'
  self.message_post_with_template(template_id, force_send=True)
  self.email_send_ok = True
```

Alternativos:
- `send_mail_view()` (L281): wrapper, llama `send_mail(True)`
- `ad_auto_email_welcome()` (isep_openeducat_sale): con manejo de excepción

### 3.3 Correo de Retiro

Modelo: `admission.downconsult`. Trigger: `action_down()` (L113):
```
1. action_down() → state='down'
2. Crea admission.downconsult
3. Cancela facturas pendientes
4. Envía survey feedback
```

---

## 4. CREACIÓN DE USUARIO PORTAL Y ACCESO E-LEARNING

### 4.1 Creación de `res.users`

Ubicación: `community-16/openeducat_admission/models/admission.py` L233-244

```python
{
  'name': student.name,
  'login': student.email,              # EMAIL = LOGIN
  'image_1920': student.image,
  'is_student': True,
  'company_id': student.company_id,
  'groups_id': [(6, 0, [group_portal_id])],
  'partner_id': <auto>,
}
```
Grupo: `base.group_portal` (acceso portal/e-learning, sin backend).

### 4.2 Actualización de `res.partner`
Sincroniza: phone, mobile, email, street, street2, city, zip, country_id, state_id, image_1920.

### 4.3 Inscripción en `slide.channel`

#### A. Manual: `enroll_elearning_wizard()` (L314-362)
Abre wizard con asignaturas del curso, permite seleccionar, crea `slide.channel.partner`.

#### B. Automática (Cron): `cron_auto_enroll_student()` (L412-465)
Diario, admisiones 'done', por cada subject_batch:
- Validación fechas: `date_from ≤ TODAY ≤ date_to` → active=True; `TODAY > date_to` → active=False
- Crea/actualiza `slide.channel.partner`:
```python
{
  'active', 'channel_id': subject.slide_channel_id,
  'partner_id', 'course_id', 'batch_id',
  'op_subject_id', 'register_id', 'admission_id',
  'date_from', 'date_to',
}
```

### 4.4 Permisos

- Inicial: `base.group_portal` (portal + website, sin backend)
- Adicionales: configurables en `auto.admission.required`

---

## 5. OTROS EFECTOS DEL FLUJO AUTOMÁTICO

### 5.1 Cronograma de Suscripción (Subscription Schedule)

**Módulos**: `isep_sale_subscription_extension` y `isep_sale_subscription_custom`
(estructuralmente idénticos; `_extension` es la versión más reciente)

**Trigger**: `action_confirm()` en ambos módulos:
```python
def action_confirm(self):
    res = super().action_confirm()
    if self.recurrence_id and not self.subscription_schedule:
        self.create_subscription_schedule()
    return res
```
Se ejecuta **después** de los módulos de admisión (por orden de herencia).

**`create_subscription_schedule()`** — crea registros `sale.subscription.schedule`:

```
Validaciones previas:
  - recurrence_id requerido
  - start_date requerido
  - end_date requerido
  - amount_recurring_taxinc > 0

Lógica:
  1. Borra cronogramas existentes de la orden
  2. Itera term_number veces (cuotas):
     - Calcula payment_date = start_date + (recurrence * i)
     - Si hay payment_term_id → usa _compute_terms() para importes
     - Si no → divide amount_total / term_number equitativamente
     - Crea sale.subscription.schedule con:
         order_id, term_number, term_label ('01 de 12'),
         date_due, date_schedule, amount_recurring_taxinc, currency_id

Campos de control en sale.order usados:
  recurrence_id (Many2one sale.subscription.plan)
  term_number   (Int — nº cuotas)
  start_date, end_date
  payment_term_id
  subscription_schedule (One2many → sale.subscription.schedule)
```

**Relación con facturación**: el cron `cron_recurring_create_invoice_update()` de `isep_sale_order_cron_payment` usa `next_invoice_date` y `subscription_schedule` para determinar qué facturas generar y cuándo.

### 5.2 Facturación Automática `addons_uisep/isep_sale_order_cron_payment/data/cron_sale_order_link_payment.xml`
```xml
<record model="ir.cron" id="account_analytic_cron_for_invoice_payment">
  <field name="name">Venta de suscripción: generar facturas y pagos recurrentes</field>
  <field name="model_id" ref="sale.model_sale_order"/>
  <field name="code">model.cron_recurring_create_invoice_update()</field>
  <field name="interval_number">1</field>
  <field name="interval_type">days</field>
</record>
```

**Método**: `cron_recurring_create_invoice_update()` (`isep_sale_order_cron_payment/models/sale_order.py` L44-229)

Lógica:
1. Busca SO con state IN ['sale','done'], is_subscription=True, subscription_management!='upsell', next_invoice_date ≤ hoy+num_day
2. Por SO: calcula invoiceable_lines, si payment_token → cancela drafts, crea invoice con `_create_invoices()`, llama `_handle_automatic_invoices()`, payment automático, actualiza next_invoice_date
3. Excepciones → payment_exception=True, email a admin

**Campos control en sale.order**:
```
invoice_schedule_done, is_invoice_cron, payment_exception,
next_invoice_date, payment_token_id
```

### 5.2 Asientos Contables

`_create_invoices()` heredado. Campos automáticos:
```
move_type='out_invoice', partner_id, invoice_date,
invoice_line_ids, order_subscription_id, journal_id
```

**Cancelación retiro**: `_cancel_unpaid_invoices_by_order()` (L127). Al `action_down()`:
```python
invoices = search([
  ('order_subscription_id','=',order_id),
  ('state','=','posted'),
  ('payment_state','=','not_paid')
])
FOR each: button_draft() → button_cancel()
```

### 5.3 Wizards y Pop-ups

**`op.admission.elearning.wizard`** (isep_elearning_custom L54-86): abre wizard, carga cursos/asignaturas, usuario selecciona, actualiza `slide.channel.partner`.

**Validaciones `send_mail()`**: tutor_id, batch_id.start_date, batch_id requeridos.

### 5.4 Logs y Chatter

Logger isep_sale_order_admissions:
```python
_logger.info("Caso 1: flujo original para orden %s" % order.name)
_logger.info("Caso 2: múltiples admisiones para orden %s" % order.name)
```

Chatter en `op.admission`: mensajes de retiro, errores de facturación.

Campos en SO: `error_admission` (Boolean), `error_admission_msn` (Html).

### 5.5 Fields Adicionales en `sale.order`

```
admission_multi_ids (One2many)
admission_register_id (Many2one op.admission.register)
admission_id (Many2one op.admission)
admission_date, period, error_admission, error_admission_msn
product_template_id, course_id, gender
website_send_mail, is_from_website_origin
```

---

## 6. DIFERENCIAS CRÍTICAS: AUTOMÁTICO vs MANUAL

### 6.1 Tabla Comparativa

| Acción | Automático | Manual | Replicación |
|--------|-----------|--------|-------------|
| 1. Crear admisión | ✅ `_action_confirm()` | ❌ | `action_get_register_id()` + `action_get_admision_id()` |
| 2. Estado submit | ✅ `submit_form()` | ❌ | Ejecutar `submit_form()` |
| 3. Estado confirm | ✅ `confirm_in_progress()` | ❌ | Ejecutar `confirm_in_progress()` |
| 4. Estado admission | ✅ `admission_confirm()` | ❌ | Ejecutar `admission_confirm()` |
| 5. Crear op.student | ✅ `enroll_student()` | ❌ | Ejecutar `enroll_student()` |
| 6. Crear res.users | ✅ `get_student_vals()` | ❌ | Interno en `enroll_student()` |
| 7. Inscribir e-learning | ✅ cron diario | ⚠️ parcial | Manual o esperar cron |
| 8. Email bienvenida | ✅ `send_mail_view()` | ❌ | Ejecutar `send_mail_view()` |
| 9. Crear cuotas | ✅ `enroll_student()` | ❌ | Crear `op.fees.detail` |
| 10. Facturas recurrentes | ✅ cron | ⚠️ manual | `_create_invoices()` |

### 6.2 Pasos Para Replicar Manualmente

```python
# EN SALE.ORDER:
register = order.get_register_id(order.period, order.product_template_id)
admission = order.get_admision_id(register)

admission.submit_form()               # → 'submit'
admission.confirm_in_progress()       # → 'confirm'
admission.admission_confirm()         # → 'admission'
admission.enroll_student()            # → 'done' (+student+users)

admission.send_mail(force_send=True)

# Inscripción e-learning (esperar cron o):
admission.auto_enroll_student()

# Facturas (esperar cron o):
order.with_context(recurring_automatic=False)._create_invoices()
```

### 6.3 Puntos de Fallo

1. "El aplicante necesita un Tutor asignado" → set tutor_id en batch
2. "Necesita establecer fecha de inicio de Clases" → set batch_id.start_date
3. "Necesita asignar un grupo" → set batch_id
4. "Please fill in the mobile number" → validación enroll_student()
5. "No se encontró Curso..." → validar product_template_id → op.course

---

## 7. MÓDULOS Y DEPENDENCIAS

### 7.1 Árbol

```
isep_sale_order_admissions
├── isep_openeducat_sale
│   ├── openeducat_core
│   ├── openeducat_admission
│   ├── openeducat_admission_enterprise
│   ├── website_slides
│   ├── isep_elearning_custom
│   └── isep_student_migration
├── isep_elearning_custom
├── isep_ecommerce_fix
└── isep_subject_precedence

isep_sale_order_cron_payment (SEPARADO)
├── sale, account, payment
```

### 7.2 Archivos Críticos

| Funcionalidad | Archivo | Líneas |
|---------------|---------|--------|
| Confirmación SO | `isep_sale_order_admissions/models/sale_order.py` | 29-69 |
| Crear Admission | `isep_sale_order_admissions/models/sale_order.py` | 72-130 |
| Procesamiento Auto | `isep_sale_order_admissions/models/sale_order.py` | 133-168 |
| Alt. Simple | `isep_openeducat_sale/models/sale_order.py` | 95-108 |
| Configuración | `isep_openeducat_sale/models/auto_admission_required.py` | 1-41 |
| Estados Admission | `community-16/openeducat_admission/models/admission.py` | 223-231 |
| Crear Student | `community-16/openeducat_admission/models/admission.py` | 233-284 |
| Enroll Student | `community-16/openeducat_admission/models/admission.py` | 286-371 |
| Custom Admission | `isep_elearning_custom/models/op_admission.py` | 169-214 |
| Submit Form | `isep_elearning_custom/models/op_admission.py` | 219-279 |
| Send Mail | `isep_elearning_custom/models/op_admission.py` | 297-311 |
| Auto Enroll | `isep_elearning_custom/models/op_admission.py` | 412-465 |
| Mail Template | `isep_elearning_custom/data/op_admission_welcome.xml` | 1-1300+ |
| Facturación Cron | `isep_sale_order_cron_payment/data/cron_sale_order_link_payment.xml` | 6-26 |
| Batch Code ACTIVO (IRG) | `addons_uisep/irg_openeducat_sale_lote_custom/models/sale_order.py` | 11-144 |
| Subscription Schedule | `addons_uisep/isep_sale_subscription_extension/models/sale_order.py` | 327-501 |

---

## 8. CONFIGURACIÓN

### 8.1 `auto.admission.required` (Singleton)

`isep_openeducat_sale/models/auto_admission_required.py`

#### México (mx_*)
- `mx_active`, `mx_auto_email_welcome`, `mx_state_admission_done`
- `mx_tutor_id`, `mx_professor_id`, `mx_coordinator`
- `mx_teams_domain`, `mx_teams_link`, `mx_teams_msg`
- `mx_modality_id`

#### Brasil (br_*)
Mismo esquema.

### 8.2 `op.fees.terms`

```
op.fees.terms
  ├── name, fees_terms: 'fixed_days'|'fixed_date'
  └── line_ids (op.fees.terms.line)
      ├── due_days, due_date (opcional), value (% del total)
```

---

## 9. RESUMEN: PUNTOS DE EXTENSIBILIDAD

### 9.1 Extender Sin Riesgo

1. Validaciones: heredar `_action_confirm()` antes de super
2. Campos: agregar en sale.order, op.admission, op.student
3. Mail templates: crear en `isep_elearning_custom/data/`
4. Automatizaciones: nuevas ir.cron / server actions
5. Post-enroll: heredar `auto_enroll_student()`

### 9.2 NO Modificar

- `community-16/openeducat_admission/models/admission.py` (base)
- Métodos core: `enroll_student()`, `get_student_vals()`
- `models/auto_admission_required.py` (singleton)

---

**FIN DEL INFORME**
