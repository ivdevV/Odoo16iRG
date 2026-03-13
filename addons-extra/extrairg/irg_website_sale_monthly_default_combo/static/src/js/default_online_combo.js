odoo.define('irg_website_sale_monthly_default_combo.default_online_combo', function (require) {
    'use strict';

    function blockByName($root, regex) {
        return $root.find('.variant_attribute').filter(function () {
            var txt = ($(this).text() || '').toLowerCase();
            return regex.test(txt);
        }).first();
    }

    function inputLabelText($input) {
        var inputId = $input.attr('id');
        if (inputId) {
            var $forLabel = $('label[for="' + inputId + '"]');
            if ($forLabel.length) {
                return ($forLabel.text() || '').trim();
            }
        }
        var $closestLabel = $input.closest('label');
        if ($closestLabel.length) {
            return ($closestLabel.text() || '').trim();
        }
        return ($input.parent().text() || '').trim();
    }

    function preselectOnlineAndMaxPlan() {
        if (window.location.pathname.indexOf('/shop/') === -1) {
            return;
        }

        var $variantsRoot = $('.js_add_cart_variants').first();
        if (!$variantsRoot.length) {
            return;
        }

        var $triggerInput = $();

        // 1) Select max months in Planes
        var $plansBlock = blockByName($variantsRoot, /plan/);
        if ($plansBlock.length) {
            var $planInputs = $plansBlock.find('input[type="radio"], input.js_variant_change');
            var bestMonths = -1;
            var $bestInput = $();

            $planInputs.each(function () {
                var $input = $(this);
                var labelText = inputLabelText($input).toLowerCase();
                var monthsMatch = labelText.match(/(\d+)\s*mes/);
                var months = monthsMatch ? parseInt(monthsMatch[1], 10) : (labelText.indexOf('contado') !== -1 ? 1 : 0);
                if (months > bestMonths) {
                    bestMonths = months;
                    $bestInput = $input;
                }
            });

            if ($bestInput.length && !$bestInput.is(':checked')) {
                $bestInput.prop('checked', true);
                $triggerInput = $bestInput;
            }
        }

        // 2) Select Online modality (non-convenio preferred)
        var $modalityBlock = blockByName($variantsRoot, /modalidad/);
        if ($modalityBlock.length) {
            var $modalityInputs = $modalityBlock.find('input[type="radio"], input.js_variant_change');
            var $online = $();

            $modalityInputs.each(function () {
                var $input = $(this);
                var labelText = inputLabelText($input).toLowerCase();
                if (labelText.indexOf('online') !== -1 && labelText.indexOf('convenio') === -1) {
                    $online = $input;
                }
            });

            if ($online.length && !$online.is(':checked')) {
                $online.prop('checked', true);
                $triggerInput = $online;
            }
        }

        if ($triggerInput.length) {
            $triggerInput.trigger('change');
        }
    }

    $(document).ready(function () {
        preselectOnlineAndMaxPlan();
        setTimeout(preselectOnlineAndMaxPlan, 250);
    });
});
