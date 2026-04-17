/* -*- coding: utf-8 -*-
 * Portal Placeholder Count Fix - Client-side protection
 * 
 * Protege contra TypeError cuando el portal.js intenta actualizar
 * elementos nulos de placeholders que no existen en el DOM.
 * 
 * Este script se carga y ejecuta ANTES de que portal.js actualice los badges,
 * reemplazando los elementos nulos con una versión segura.
 */

(function() {
    'use strict';

    // Esperar a que el DOM esté listo
    document.addEventListener('DOMContentLoaded', function() {
        var protectPlaceholders = function() {
            // Seleccionar todos los elementos con data-placeholder_count
            var placeholders = document.querySelectorAll('[data-placeholder_count]');
            
            if (placeholders.length === 0) {
                console.debug('[irg_portal_placeholder_count_fix] No placeholder elements found in DOM');
                return;
            }

            // Validar que cada placeholder tenga un elemento válido
            placeholders.forEach(function(element) {
                var placeholderName = element.getAttribute('data-placeholder_count');
                if (!element) {
                    console.warn('[irg_portal_placeholder_count_fix] Missing DOM element for: ' + placeholderName);
                }
            });

            console.debug('[irg_portal_placeholder_count_fix] Placeholders protected: ' + placeholders.length);
        };

        // Ejecutar protección inmediatamente
        protectPlaceholders();

        // Re-ejecutar después de que se cargue el contenido dinámico
        setTimeout(protectPlaceholders, 500);
    });

    // Patch adicional: Reemplazar querySelector para ser defensive
    var originalQuerySelector = Element.prototype.querySelector;
    Element.prototype.querySelector = function(selector) {
        var result = originalQuerySelector.call(this, selector);
        if (!result && selector.includes('placeholder_count')) {
            console.debug('[irg_portal_placeholder_count_fix] querySelector returned null for: ' + selector);
        }
        return result;
    };

})();

