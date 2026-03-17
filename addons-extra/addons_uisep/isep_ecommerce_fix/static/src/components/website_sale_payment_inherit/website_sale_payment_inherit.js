odoo.define('isep_ecommerce_fix.signature_check', function (require) {
    'use strict';

    const rpc = require('web.rpc');
    const checkoutForm = require('payment.checkout_form');

    const SignatureCheckMixin = {
        start: function () {
            this.$signButton = this.$('#sign_button');
            this.$orderIdInput = this.$('#order_id_holder');
            this.$signatureSigned = this.$('#signature_signed');
            this.$submitButton = this.$('button[name="o_payment_submit_button"]');

            this._checkInitialSignature();

            return this._super(...arguments);
        },

        _checkInitialSignature: function () {
            if (!this.$signButton.length) return;

            const orderId = this._getOrderId();
            if (!orderId) return;

            rpc.query({
                route: '/signature_status',
                params: { order_id: parseInt(orderId) },
            }).then(data => {
                this._setSignLink(data.sign_link || '');
                if (data.signed) {
                    this._markAsSigned();
                } else {
                    this._markAsUnsigned();
                }
                this._updateSignatureDisabledReason();
            }).catch(() => {
                console.warn("No se pudo validar la firma inicialmente.");
                this._updateSignatureDisabledReason();
            });
        },

        _markAsSigned: function () {
            this.$signatureSigned.val('1');
            $('#sign_button').hide();
            $('#sign_success_badge').show();
            $('#signature_warning').hide();
        },

        _markAsUnsigned: function () {
            this.$signatureSigned.val('0');
            $('#sign_button').show();
            $('#sign_success_badge').hide();
        },

        _setSignLink: function (signLink) {
            $('#sign_link_holder').val(signLink || '');
        },

        _openSignModal: function (signLink) {
            if (!signLink) {
                alert("No se pudo preparar el documento de matrícula para firma.");
                return;
            }

            $('#sign_modal').show();
            $('#loading_spinner').show();
            $('#sign_iframe').hide();

            const iframe = $('#sign_iframe')[0];
            iframe.onload = function() {
                $('#loading_spinner').hide();
                $('#sign_iframe').show();
            };

            $('#sign_iframe').attr('src', signLink);
        },

        _getOrderId: function () {
            const val = this.$orderIdInput.val();
            return val ? parseInt(val) : null;
        },

        _updateSignatureDisabledReason: function () {
            const disabledReasons = this.$submitButton.data('disabled_reasons') || {};

            if (this.$signButton.length > 0) {
                disabledReasons.signature = this.$signatureSigned.val() !== '1';
            }

            this.$submitButton.data('disabled_reasons', disabledReasons);

            const disabled = Object.values(disabledReasons).includes(true);
            this.$submitButton.prop('disabled', disabled);
        },
    };

    checkoutForm.include(Object.assign({}, SignatureCheckMixin, {
        events: Object.assign({}, checkoutForm.prototype.events, {
            'click #sign_button': '_onClickSignButton',
            'click #close_modal': '_onCloseModal',
            'click #sign_modal': '_onClickModalBackground',
            'click #fallback_link': '_onClickFallbackLink',
        }),

        _onClickSignButton: function () {
            const signLink = $('#sign_link_holder').val();
            if (signLink) {
                this._openSignModal(signLink);
                return;
            }

            const orderId = this._getOrderId();
            if (!orderId) {
                alert("No se pudo localizar el pedido para preparar la firma.");
                return;
            }

            $('#sign_button').prop('disabled', true).html('<i class="fa fa-spinner fa-spin mr-1"/> Preparando documento...');

            rpc.query({
                route: '/signature_prepare',
                params: { order_id: parseInt(orderId) },
            }).then(data => {
                $('#sign_button').prop('disabled', false).html('<i class="fa fa-pencil-square-o mr-1"/> Realizar firma de matrícula');
                this._setSignLink(data.sign_link || '');
                if (data.sign_link) {
                    this._openSignModal(data.sign_link);
                    return;
                }
                alert("No se pudo generar el documento de matrícula para firma.");
            }).catch(() => {
                $('#sign_button').prop('disabled', false).html('<i class="fa fa-pencil-square-o mr-1"/> Realizar firma de matrícula');
                alert("Ocurrió un error al preparar el documento de matrícula.");
            });
        },

        _onCloseModal: function () {
            $('#sign_modal').hide();
            $('#sign_iframe').attr('src', '');
            $('#loading_spinner').show();
            $('#sign_iframe').hide();

            // After closing the modal, check if the document was signed
            var self = this;
            var orderId = this._getOrderId();
            if (orderId) {
                rpc.query({
                    route: '/signature_status',
                    params: { order_id: parseInt(orderId) },
                }).then(function (data) {
                    if (data.signed) {
                        self._markAsSigned();
                    }
                    self._updateSignatureDisabledReason();
                });
            }
        },

        _onClickModalBackground: function (e) {
            if (e.target.id === 'sign_modal') {
                this._onCloseModal();
            }
        },

        _onClickFallbackLink: function (e) {
            e.preventDefault();
            var signLink = $('#sign_link_holder').val();
            if (signLink) {
                window.open(signLink, '_blank');
            }
        },

        _isButtonReady: function () {
            var disabledReasons = this.$submitButton.data('disabled_reasons') || {};
            return !Object.values(disabledReasons).includes(true) && this._super(...arguments);
        },
    }));
});
