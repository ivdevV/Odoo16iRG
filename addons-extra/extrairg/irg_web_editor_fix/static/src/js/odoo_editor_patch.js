odoo.define('irg_web_editor_fix.odoo_editor_patch', function (require) {
    "use strict";

    // Extender el OdooEditor para parchear _applyRawCommand
    var OdooEditor = require('web_editor.odoo_editor').OdooEditor;

    if (OdooEditor && OdooEditor.prototype) {
        // Guardar la función original
        var originalApplyRawCommand = OdooEditor.prototype._applyRawCommand;

        // Reemplazar con nuestra versión parcheada
        OdooEditor.prototype._applyRawCommand = function (command, value) {
            try {
                // Llamada original con validación extra
                return originalApplyRawCommand.call(this, command, value);
            } catch (error) {
                // Manejar específicamente el error de anchorNode
                if (error.message && error.message.includes('is not a function')) {
                    console.warn('IRG Web Editor Fix: Se ha prevenido un error en _applyRawCommand', error);
                    // Permitir que el flujo continúe sin interrumpir la edición
                    return;
                }
                // Re-lanzar otros errores
                throw error;
            }
        };

        // También parchear _protect para capturar errores antes de que lleguen a _applyRawCommand
        var originalProtect = OdooEditor.prototype._protect;

        OdooEditor.prototype._protect = function (fn) {
            return originalProtect.call(this, function () {
                try {
                    return fn.apply(this, arguments);
                } catch (error) {
                    if (error.message && error.message.includes('is not a function')) {
                        console.warn('IRG Web Editor Fix: Se ha prevenido un error en _protect', error);
                        return;
                    }
                    throw error;
                }
            });
        };

        console.info('IRG Web Editor Fix: Parches aplicados correctamente');
    }

    return OdooEditor;
});
