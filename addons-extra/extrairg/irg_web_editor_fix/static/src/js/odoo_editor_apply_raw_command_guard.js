/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import * as OdooEditorModule from "@web_editor/js/editor/odoo-editor/src/OdooEditor";

const OdooEditorClass = OdooEditorModule.OdooEditor || OdooEditorModule.default;

if (OdooEditorClass && OdooEditorClass.prototype && OdooEditorClass.prototype._applyRawCommand) {
    patch(OdooEditorClass.prototype, "irg_web_editor_fix.apply_raw_command_guard", {
        _applyRawCommand(method, ...args) {
            const selection = this.document && this.document.getSelection ? this.document.getSelection() : null;
            const anchorNode = selection ? selection.anchorNode : null;

            if (anchorNode && typeof method === "string" && method) {
                const anchorMethod = anchorNode[method];
                if (typeof anchorMethod !== "function") {
                    const elementNode = anchorNode.nodeType === 3 ? anchorNode.parentNode : anchorNode;
                    const elementMethod = elementNode && elementNode[method];

                    if (typeof elementMethod === "function") {
                        return elementMethod.apply(elementNode, args);
                    }
                    return false;
                }
            }

            try {
                return this._super(method, ...args);
            } catch (error) {
                const message = (error && error.message) || "";
                if (message.includes("is not a function") && message.includes("anchorNode")) {
                    return false;
                }
                throw error;
            }
        },
    });
}
