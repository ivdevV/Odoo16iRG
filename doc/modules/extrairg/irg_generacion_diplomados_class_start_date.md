# irg_generacion_diplomados_class_start_date

Addon de herencia que hace que los diplomas de diplomados impriman la fecha de
inicio de clases del lote (`op.batch.date_start_class`) en «celebrado del …».

Instalar de forma explicita (`auto_install` es falso). Dependencias: generacion
de diplomados, `isep_data_master_make`, verificacion web QR, portal dedicado y
portal campus.

Si se cambia la fecha de inicio de clases del lote, la siguiente descarga del
alumno (con `start_date` ya informado en el registro) regenera el PDF. Los
ficheros que el alumno ya tenga en su dispositivo no cambian.

Reimprimir en el historico siempre regenera.
