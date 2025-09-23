odoo.define('isep_ecommerce_fix.signature_check', function (require) {
    'use strict';

    const rpc = require('web.rpc');
    const checkoutForm = require('payment.checkout_form');

    const SignatureCheckMixin = {
        start: function () {
            this.$signatureCheckbox = this.$('#checkbox_signed');
            this.$orderIdInput = this.$('#order_id_holder');
            this.$submitButton = this.$('button[name="o_payment_submit_button"]');

            this._checkInitialSignature();

            return this._super(...arguments);
        },

        _checkInitialSignature: function () {
            if (!this.$signatureCheckbox.length) return;

            const orderId = this._getOrderId();
            if (!orderId) return;

            rpc.query({
                route: '/signature_status',
                params: { order_id: parseInt(orderId) },
            }).then(data => {
                if (data.signed) {
                    this.$signatureCheckbox.prop('checked', true);
                    $('#signature_warning').hide();
                    $('#sign_button').hide();
                } else {
                    this.$signatureCheckbox.prop('checked', false);
                    $('#signature_warning').hide();
                    $('#sign_button').hide();
                }
                this._updateSignatureDisabledReason();
            }).catch(() => {
                console.warn("No se pudo validar la firma inicialmente.");
                this._updateSignatureDisabledReason();
            });
        },

        _onClickSignatureCheckbox: function () {
            const orderId = this._getOrderId();
            if (!orderId) return;

            this.$signatureCheckbox.prop('disabled', true);

            rpc.query({
                route: '/signature_status',
                params: { order_id: parseInt(orderId) },
            }).then(data => {
                if (data.signed) {
                    this.$signatureCheckbox.prop('checked', true);
                    $('#signature_warning').hide();
                    $('#sign_button').hide();
                } else {
                    this.$signatureCheckbox.prop('checked', false);
                    $('#signature_warning')
                        .text("Debes firmar el documento antes de continuar.")
                        .show();
                    $('#sign_button').show();
                }

                this.$signatureCheckbox.prop('disabled', false);
                this._updateSignatureDisabledReason();
            }).catch(() => {
                this.$signatureCheckbox.prop('disabled', false);
                alert("Ocurrió un error al verificar la firma.");
            });
        },

        _getOrderId: function () {
            const val = this.$orderIdInput.val();
            return val ? parseInt(val) : null;
        },

        _updateSignatureDisabledReason: function () {
            const disabledReasons = this.$submitButton.data('disabled_reasons') || {};

            if (this.$signatureCheckbox.length > 0) {
                disabledReasons.signature = !this.$signatureCheckbox.prop('checked');
            }

            this.$submitButton.data('disabled_reasons', disabledReasons);

            const disabled = Object.values(disabledReasons).includes(true);
            this.$submitButton.prop('disabled', disabled);
        },
    };

    checkoutForm.include(Object.assign({}, SignatureCheckMixin, {
        events: Object.assign({}, checkoutForm.prototype.events, {
            'click #checkbox_signed': '_onClickSignatureCheckbox',
            'click #sign_button': '_onClickSignButton',
            'click #close_modal': '_onCloseModal',
            'click #sign_modal': '_onClickModalBackground',
            'click #fallback_link': '_onClickFallbackLink',
        }),

        _onClickSignButton: function () {
            const signLink = $('#sign_link_holder').val();
            if (signLink) {
                $('#sign_modal').show();
                $('#loading_spinner').show();
                $('#sign_iframe').hide();
                
                const iframe = $('#sign_iframe')[0];
                iframe.onload = function() {
                    $('#loading_spinner').hide();
                    $('#sign_iframe').show();
                };
                
                $('#sign_iframe').attr('src', signLink);
            }
        },

        _onCloseModal: function () {
            $('#sign_modal').hide();
            $('#sign_iframe').attr('src', '');
            $('#loading_spinner').show();
            $('#sign_iframe').hide();
        },

        _onClickModalBackground: function (e) {
            if (e.target.id === 'sign_modal') {
                this._onCloseModal();
            }
        },

        _onClickFallbackLink: function (e) {
            e.preventDefault();
            const signLink = $('#sign_link_holder').val();
            if (signLink) {
                window.open(signLink, '_blank');
            }
        },

        _isButtonReady: function () {
            const disabledReasons = this.$submitButton.data('disabled_reasons') || {};
            return !Object.values(disabledReasons).includes(true) && this._super(...arguments);
        },
    }));
});
