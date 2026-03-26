odoo.define('irg_website_sale_monthly_price.website_sale_monthly', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    require('website_sale.website_sale');

    publicWidget.registry.WebsiteSale.include({
        /**
         * @override
         */
        _onChangeCombination: function (ev, $parent, combination) {
            this._super.apply(this, arguments);
            
            console.log('IRG Monthly Price Debug: _onChangeCombination called', combination);
            
            var months = combination.months || 1;
            var selectedPrice = combination.price || 0;
            // Display directly as variant price divided by months (no frontend normalization)
            var displayPrice = (months > 1 ? (selectedPrice / months) : selectedPrice);
            var displayMonths = months;

            if (displayPrice && displayPrice > 0) {
                var formattedPrice = this._priceToStr(displayPrice);
                
                var $price = $parent.find('.oe_price .oe_currency_value');
                $price.text(formattedPrice);
                
                // Add or update installment suffix
                var $suffix = $parent.find('.oe_price .isep_month_suffix');
                var suffixText = displayMonths > 1 ? (' / ' + displayMonths + ' meses') : '';
                if (suffixText) {
                    if ($suffix.length === 0) {
                        $parent.find('.oe_price').append('<span class="text-muted isep_month_suffix" style="font-size: 0.8rem;"></span>');
                        $suffix = $parent.find('.oe_price .isep_month_suffix');
                    }
                    $suffix.text(suffixText);
                } else if ($suffix.length) {
                    $suffix.remove();
                }
            } else {
                $parent.find('.oe_price .isep_month_suffix').remove();
            }
        }
    });

    $(document).ready(function () {
        function preselectPlanAndModality() {
            if (window.location.pathname.indexOf('/shop/') === -1) {
                return;
            }

            var $variantsRoot = $('.js_add_cart_variants').first();
            if (!$variantsRoot.length) {
                return;
            }

            var $variantBlocks = $variantsRoot.find('.variant_attribute');
            if (!$variantBlocks.length) {
                return;
            }

            function blockByName(regex) {
                return $variantBlocks.filter(function () {
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

            var $plansBlock = blockByName(/plan/);
            var $modalityBlock = blockByName(/modalidad/);
            var $triggerInput = $();

            if ($plansBlock.length) {
                var $planInputs = $plansBlock.find('input[type="radio"], input.js_variant_change');
                var minMonthsAttr = parseInt($('#isep_monthly_price_active').attr('data-min-months') || '', 10);
                var bestMonths = -1;
                var $bestInput = $();

                $planInputs.each(function () {
                    var $input = $(this);
                    var labelText = inputLabelText($input).toLowerCase();
                    var monthsMatch = labelText.match(/(\d+)\s*mes/);
                    var months = monthsMatch ? parseInt(monthsMatch[1], 10) : (labelText.indexOf('contado') !== -1 ? 1 : 0);
                    if (minMonthsAttr > 1) {
                        if (months === minMonthsAttr) {
                            $bestInput = $input;
                            return false;
                        }
                    } else if (months > bestMonths) {
                        bestMonths = months;
                        $bestInput = $input;
                    }
                });

                if ($bestInput.length && !$bestInput.is(':checked')) {
                    $bestInput.prop('checked', true);
                    $triggerInput = $bestInput;
                }
            }

            if ($modalityBlock.length) {
                var $modalityInputs = $modalityBlock.find('input[type="radio"], input.js_variant_change');
                var $homeClass = $();
                $modalityInputs.each(function () {
                    var $input = $(this);
                    var labelText = inputLabelText($input).toLowerCase();
                    if (labelText.indexOf('homeclass') !== -1) {
                        $homeClass = $input;
                    }
                });

                if ($homeClass.length && !$homeClass.is(':checked')) {
                    $homeClass.prop('checked', true);
                    $triggerInput = $homeClass;
                }
            }

            if ($triggerInput.length) {
                $triggerInput.trigger('change');
            }
        }

        function hidePaymentWarning() {
            var warningPhrases = [
                "importe pagado es diferente",
                "amount paid is different"
            ];
            
            $(".alert").each(function() {
                var $alert = $(this);
                var html = $alert.html();
                var lowerHtml = html.toLowerCase();
                
                var found = false;
                warningPhrases.forEach(function(phrase) {
                    if (lowerHtml.indexOf(phrase) !== -1) {
                        found = true;
                    }
                });

                if (found) {
                    console.log('IRG Monthly Price: Found payment warning in alert.');
                    
                    if (lowerHtml.indexOf('success') !== -1 || lowerHtml.indexOf('éxito') !== -1 || lowerHtml.indexOf('exito') !== -1) {
                        var regexEs = /No podemos confirmar su pedido.*?información\./i;
                        var regexEn = /We cannot confirm your order.*?information\./i;
                        
                        var newHtml = html.replace(regexEs, '').replace(regexEn, '');
                        
                        newHtml = newHtml.replace(/<br\s*\/?>(\s*<br\s*\/?>)?/g, '<br>');
                        
                        $alert.html(newHtml);
                        console.log('IRG Monthly Price: Removed warning text from mixed alert.');
                    } else {
                        $alert.addClass('d-none');
                        $alert.hide();
                        console.log('IRG Monthly Price: Hidden full warning alert.');
                    }
                }
            });
        }

        hidePaymentWarning();
        preselectPlanAndModality();
        setTimeout(preselectPlanAndModality, 250);
        
        var observer = new MutationObserver(function(mutations) {
            hidePaymentWarning();
        });
        
        var target = document.querySelector('body');
        if (target) {
            observer.observe(target, { childList: true, subtree: true });
        }
    });
});
