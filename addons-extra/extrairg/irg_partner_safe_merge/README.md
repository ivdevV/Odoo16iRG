# IRG Partner Safe Merge

`irg_partner_safe_merge` consolida de forma controlada dos contactos personales duplicados. Conserva el contacto maestro, traslada únicamente las relaciones autorizadas y archiva el contacto de origen con una auditoría inmutable.

## Instalación

1. Asegúrese de que `addons-extra/extrairg` esté incluido en la ruta de addons de Odoo.
2. Actualice la lista de aplicaciones y busque **IRG Partner Safe Merge**.
3. Instale el módulo. La instalación no fusiona ni modifica contactos, y no programa tareas automáticas.

## Uso

Solo un administrador del sistema puede ejecutar el proceso.

1. En **Contactos**, desde la vista de lista, seleccione exactamente dos contactos.
2. Elija **Acción → Safe merge**.
3. Revise la recomendación del maestro. Se priorizan suscripciones activas o confirmadas, ventas confirmadas, historial de pagos, usuario o estudiante enlazado, completitud y antigüedad. Es una recomendación: puede usar **Swap master and source** antes del preview final.
4. Genere el preview. Revise el inventario de relaciones y resuelva cada conflicto escalar no vacío eligiendo conservar el valor del maestro o usar el del origen. Cuando cambie una decisión, genere de nuevo el preview final.
5. Marque **I confirm this safe merge** y confirme. El sistema vuelve a validar y bloquea los registros; si algo cambió desde el preview, exige generar uno nuevo.

## Límites y bloqueos

El proceso exige dos contactos distintos, activos y personales, sin relación padre/hijo, con compañías compatibles y una coincidencia de email normalizado, teléfono o documento. No permite reutilizar un contacto ya fusionado.

Se bloquea si hay referencias no autorizadas, bancos, pagos o contabilidad en el origen; dos usuarios o estudiantes, incoherencia entre ellos; o colisiones de negocio, membresías o relaciones no aprobadas. Los leads no se fusionan: cada lead conserva su ID y únicamente se reasigna su contacto cuando está permitido.

Solo se pueden decidir los campos de identidad y contacto admitidos por el módulo. Los demás valores se conservan en el origen archivado y quedan descritos en la auditoría.

## Seguridad, auditoría y recuperación

La autorización se comprueba en el servidor al abrir, previsualizar y confirmar; la interfaz no es el único control. La confirmación es atómica: un error revierte todos los cambios. El origen queda archivado y marcado con su maestro; no puede reactivarse ni eliminarse. La auditoría registra actor, fecha, decisión, hash de preview, inventario, acciones y snapshots antes/después, y solo los administradores pueden leerla en **Contactos → Configuración → Safe merge audits**.

No hay detección, fusión ni reversión automática. Para una fusión en producción, compruebe una copia de seguridad recuperable y obtenga autorización explícita para ese par de contactos antes de confirmar. Una corrección posterior requiere un proceso manual y auditado; no se debe intentar reactivar ni borrar el origen fusionado.
