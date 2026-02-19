odoo.define('isep_website_sale_custom.address_toast', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');

    publicWidget.registry.IsepAddressToast = publicWidget.Widget.extend({
        selector: 'body',

        start: function () {
            this._super.apply(this, arguments);

            if (window.location.pathname.indexOf('/shop/address') === -1) {
                return;
            }

            var toastShown = false;
            var showToast = function () {
                if (toastShown) {
                    return;
                }
                toastShown = true;
                var $toast = $('<div class="alert alert-info position-fixed" style="z-index: 2000; right: 1rem; top: 1rem; min-width: 320px;">Aguarda un momento mientras cargamos los datos de matriculación. ¡Gracias!</div>');
                $('body').append($toast);
                setTimeout(function () {
                    $toast.fadeOut(300, function () { $(this).remove(); });
                }, 5000);
            };

            $(document).on('submit', 'form[action*="/shop/address"], form#checkout_form, form[name="checkout"]', function () {
                showToast();
            });

            $(document).on('click', [
                'form[action*="/shop/address"] button',
                'form[action*="/shop/address"] input[type="submit"]',
                'form#checkout_form button',
                '.o_wsale_checkout_next',
                '.a-submit',
                '.btn-primary'
            ].join(', '), function () {
                showToast();
            });
        },
    });
});
