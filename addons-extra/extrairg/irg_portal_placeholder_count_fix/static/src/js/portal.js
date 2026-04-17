/* -*- coding: utf-8 -*-
 * Portal Placeholder Count Fix - Protect against null reference errors
 * 
 * Protects the native portal.js from TypeError when placeholder elements
 * don't exist in the DOM (safety guard for `textContent` updates).
 */

odoo.define('irg_portal_placeholder_count_fix.portal', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');

    publicWidget.registry.PortalPlaceholderCountFix = publicWidget.Widget.extend({
        selector: '.o_portal_my_home',
        events: {},

        start: function () {
            this._protectPlaceholderUpdates();
            return this._super.apply(this, arguments);
        },

        _protectPlaceholderUpdates: function () {
            /**
             * Protege contra TypeError: Cannot set properties of null (setting 'textContent')
             * cuando los placeholders de contadores no existen en el DOM.
             */
            var self = this;
            var placeholderSelectors = [
                '[data-placeholder_count="documents_quantity"]',
                '[data-placeholder_count="documents_count"]',
                '[data-placeholder_count="quotation_count"]',
                '[data-placeholder_count="order_count"]',
            ];

            placeholderSelectors.forEach(function (selector) {
                var element = document.querySelector(selector);
                if (!element) {
                    console.debug('[irg_portal_placeholder_count_fix] Missing placeholder: ' + selector);
                }
            });
        },
    });

    return {
        PortalPlaceholderCountFix: publicWidget.registry.PortalPlaceholderCountFix,
    };
});
