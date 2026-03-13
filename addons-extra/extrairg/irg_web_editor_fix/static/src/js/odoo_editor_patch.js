odoo.define('irg_web_editor_fix.odoo_editor_patch', function (require) {
    "use strict";

    var OdooEditor = require('web_editor.odoo_editor').OdooEditor;

    // Patch _applyRawCommand to handle TypeError
    var originalApplyRawCommand = OdooEditor.prototype._applyRawCommand;

    OdooEditor.prototype._applyRawCommand = function (command, value) {
        try {
            return originalApplyRawCommand.call(this, command, value);
        } catch (e) {
            if (e.message && e.message.indexOf('is not a function') !== -1) {
                console.warn('[IRG Web Editor Fix] TypeError handled in _applyRawCommand');
                return;
            }
            throw e;
        }
    };

    return OdooEditor;
});
