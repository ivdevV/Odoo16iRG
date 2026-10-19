# IRG Admission Unimarconi Mail — Design

## Objective

Desde la ficha de una admisión de máster oficial, el personal abre el
compositor de correo con una plantilla de iRG. El botón del mensaje lleva a
la aplicación de oficialidad, donde el alumno descarga, completa y sube el
formulario de matrícula de Unimarconi.

## Scope

Entra en este corte:

- módulo nuevo `irg_admission_unimarconi_mail` en `addons-extra/extrairg`;
- herencia de `op.admission`: botón en la cabecera y método que abre el
  compositor;
- plantilla `mail.template` con el texto y el aspecto aprobados;
- logo de iRG de la plantilla de seguimiento, dentro del módulo;
- pruebas del prefijo de lote, del correo vacío y del contexto del compositor.

Queda fuera:

- cambios en `irg_student_oficialidad_documents` y
  `irg_student_oficialidad_webhook`;
- adjuntar o rellenar el PDF italiano;
- recibir el formulario cumplimentado (ya entra por la aplicación como
  documento `matricula-unimarconi`);
- portal, envío automático y un grupo de seguridad nuevo;
- distinguir en el correo alumno nacional e internacional.

## Relationship with oficialidad

La aplicación `https://oficialidad.institutoraimongaja.com` ya pide la
matrícula cumplimentada y la envía a Odoo con la clave
`matricula-unimarconi`. Ese documento aparece en **Detalle Oficialidad** y
cuenta en el resumen `X/4`, para nacional e internacional.

Este módulo solo invita al alumno a entrar en esa aplicación. No crea
documentos ni llama al webhook.

## Module

- Nombre técnico: `irg_admission_unimarconi_mail`
- Versión: `16.0.1.0.0`
- Dependencias: `openeducat_admission`, `mail`
- Sin modelos nuevos. Sin `ir.model.access.csv`.

Archivos:

- `models/op_admission.py`: campo calculado de visibilidad y acción del botón
- `views/op_admission_views.xml`: botón en el `header` del formulario
- `data/mail_template_data.xml`: plantilla, con `noupdate="1"`
- `static/src/img/logo-irg.jpg`: logo de la plantilla de seguimiento
- `tests/test_unimarconi_mail.py`

## Button

Etiqueta: **Enviar matrícula Unimarconi**.

Visible en todos los estados de `op.admission` cuando el código del lote, sin
espacios al inicio y en mayúsculas, empieza por `MO`.

| Código | Botón |
| --- | --- |
| `MOPCONL2606`, `MOPCIN2701` | visible |
| `MONLHC…`, `MONLPRS…`, `MONLONL…` | visible |
| `mo…` (minúsculas) | visible |
| `MP…`, `MB…`, `MIAMONL…` | oculto |
| sin lote o código vacío | oculto |

El campo calculado que usa la vista no se almacena. El método del botón
repite la misma regla en el servidor.

## Send flow

1. La persona pulsa el botón en una sola admisión.
2. Si el lote no empieza por `MO`, el método se detiene. El aviso dice que
   el envío solo corresponde a lotes cuyo código empieza por `MO`.
3. Si `email` está vacío, el método se detiene y pide que se indique el
   correo de la admisión. No abre el compositor.
4. Si la plantilla no está instalada, el método se detiene con un error.
5. Se abre `mail.compose.message` en diálogo, modo `comment`, con la
   plantilla, el modelo `op.admission` y el id de esa admisión.
6. El remitente por defecto es
   `Instituto Raimon Gaja <academica@institutoraimongaja.com>`.
   El destinatario es el `email` de la admisión.
7. La persona puede editar el mensaje y enviarlo. Puede repetir el envío.
8. El envío queda en el chatter de la admisión. No hay modelo de historial
   aparte.

No se usa `sudo()` para leer la admisión ni para enviar.

## Mail template

Asunto: `¡Tu formulario de matrícula en Unimarconi!`

Saludo: `¡Hola, {nombre}!`. `{nombre}` es `first_name`. Si está vacío, se usa
`name`.

`{curso}` es `course_id.name`. Si el curso no tiene nombre, la primera frase
pasa a ser «Para tu máster te facilitamos…».

Cuerpo:

> Para tu {curso} te facilitamos el formulario de inscripción de la
> Università degli Studi Guglielmo Marconi.
>
> ¡Estamos aquí para acompañarte!
>
> Entra en la aplicación de oficialidad, descarga el formulario, complétalo y
> fírmalo. Está en italiano. Al subirlo queda en tu expediente como la
> matrícula Unimarconi cumplimentada, junto con el resto de la documentación.

El botón del correo dice **Acceso a oficialidad** y abre
`https://oficialidad.institutoraimongaja.com`. Debajo va la misma dirección
en texto, por si el botón no responde.

Cierre:

- Departamento Académico: `academica@institutoraimongaja.com`
- WhatsApp Departamento Académico: `+34 623 55 17 40`
- `© Instituto Raimon Gaja | Formación de calidad para profesionales de la salud`

Aspecto, tomado de la plantilla de seguimiento:

- fondo blanco y logo de iRG arriba a la izquierda;
- la frase de acompañamiento en `#0191c0`, centrada y en negrita;
- botón con fondo `#4db4e7` y letra blanca;
- pie en gris, centrado.

## Testing

Pruebas de módulo Odoo:

- `MO`, `mo` y `MONL` muestran el botón; `MP`, `MB`, `MIA` y el lote vacío
  no;
- sin correo, la acción no abre el compositor;
- con lote que no empieza por `MO`, la acción no abre el compositor;
- con correo y lote `MO`, la acción devuelve el compositor de esa admisión y
  esa plantilla;
- el cuerpo renderizado contiene la URL de oficialidad y el nombre del curso.

El diff toca una vista XML de formulario. En la validación de la misión el
check `e2e_testsprite` es obligatorio. `projectPath` es el directorio del
módulo.

## Mission classification

- Clase: `full`. Es una función nueva de producto.
- Tier: `complex`. El módulo supera los cinco archivos, con vista, plantilla
  y pruebas.
- Jev intake, al empezar la petición: `status: skipped`,
  `skipped_reason: http_error`. `effective_class_binding` es falso. La clase
  la fija esta política.
- Security Advisor: no. No hay autenticación nueva, secreto, migración,
  concurrencia, despliegue ni borrado histórico.

## Acceptance criteria

1. En una admisión con lote `MO`, el botón se ve en borrador y en el resto
   de estados.
2. En una admisión con lote `MP` o `MB`, el botón no se ve y la acción no
   abre el compositor.
3. Sin correo, el compositor no se abre y se pide el correo.
4. Con correo, el compositor sale con el asunto, el saludo, el nombre del
   curso, el remitente académico y el botón hacia
   `https://oficialidad.institutoraimongaja.com`.
5. Tras enviar, el mensaje queda en el chatter y se puede enviar otra vez.
6. Los módulos de documentos y webhook de oficialidad no cambian.
7. Las pruebas del módulo pasan, y el E2E de la vista pasa en la validación.
