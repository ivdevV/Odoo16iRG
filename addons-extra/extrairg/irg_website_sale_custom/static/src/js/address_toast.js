odoo.define('irg_website_sale_custom.address_toast', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');

    publicWidget.registry.IsepAddressToast = publicWidget.Widget.extend({
        selector: 'body',

        start: function () {
            this._super.apply(this, arguments);

            var toastStorageKey = 'irg_checkout_address_toast';
            var path = window.location.pathname || '';
            var isShopAddress = path.indexOf('/shop/address') === 0;
            var isShopFlow = path.indexOf('/shop/') === 0;

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

            if (isShopFlow && window.sessionStorage && sessionStorage.getItem(toastStorageKey) === '1') {
                sessionStorage.removeItem(toastStorageKey);
                showToast();
            }

            if (!isShopAddress) {
                return;
            }

            var markAndShowToast = function () {
                if (window.sessionStorage) {
                    sessionStorage.setItem(toastStorageKey, '1');
                }
                showToast();
            };

            $(document).on('submit', 'form[action*="/shop/address"], form#checkout_form, form[name="checkout"]', function () {
                markAndShowToast();
            });

            $(document).on('click', [
                'form[action*="/shop/address"] button',
                'form[action*="/shop/address"] input[type="submit"]',
                'form#checkout_form button',
                '.o_wsale_checkout_next',
                '.a-submit',
                '.btn-primary'
            ].join(', '), function () {
                markAndShowToast();
            });
        },
    });
});
