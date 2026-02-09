(function () {
    "use strict";

    // Guardar y detener la propagación de unhandledrejection específico
    window.addEventListener('unhandledrejection', function (event) {
        try {
            var reason = event.reason || '';
            var msg = (reason && reason.message) ? reason.message : String(reason);
            if (msg.indexOf("Cannot set properties of null (setting 'textContent')") !== -1 || msg.indexOf("setting 'textContent'") !== -1) {
                console.warn('elearning_student_ui: suppressed known frontend error', msg);
                event.preventDefault();
            }
        } catch (e) {
            // ignore
        }
    });

    // Lista de etiquetas/textos a ocultar en la UI de alumno
    var labelsToRemove = [
        'Presupuestos',
        'Pedidos de venta',
        'Pedidos de compra',
        'Documentación',
        'Proyectos',
        'Tareas',
        'Partes de horas',
        'Tíquets',
        'Centro de práctica'
    ];

    function removeByText() {
        try {
            labelsToRemove.forEach(function (label) {
                // Buscar elementos cuyo texto coincida exactamente (trim)
                var elems = document.querySelectorAll('a, button, span, div');
                elems.forEach(function (el) {
                    if (!el || !el.textContent) { return; }
                    if (el.textContent.trim() === label) {
                        var node = el.closest('li, a, .o_portal_my_home, .o_stat_button, .o_kanban_record');
                        if (node) {
                            node.remove();
                        } else {
                            el.remove();
                        }
                    }
                });
            });
        } catch (e) {
            console.error('elearning_student_ui removeByText error', e);
        }
    }

    // Ejecutar al cargar DOM y tras cambios dinámicos (por ejemplo editor web o re-render)
    function safeRun() {
        if (document.readyState === 'complete' || document.readyState === 'interactive') {
            removeByText();
        } else {
            document.addEventListener('DOMContentLoaded', removeByText);
        }
    }

    // Observador para volver a limpiar cuando la página cambie dinámicamente
    function attachObserver() {
        try {
            var observer = new MutationObserver(function () {
                removeByText();
            });
            observer.observe(document.body, { childList: true, subtree: true });
        } catch (e) {
            // MutationObserver puede fallar en entornos muy antiguos; es seguro ignorar
        }
    }

    safeRun();
    attachObserver();

})();
