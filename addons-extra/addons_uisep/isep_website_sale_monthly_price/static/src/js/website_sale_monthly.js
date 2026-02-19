odoo.define('isep_website_sale_monthly_price.website_sale_monthly', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    require('website_sale.website_sale');

    publicWidget.registry.WebsiteSale.include({
        /**
         * @override
         */
        _onChangeCombination: function (ev, $parent, combination) {
            this._super.apply(this, arguments);
            
            console.log('ISEP Monthly Price Debug: _onChangeCombination called', combination);
            
            var minInstallmentPrice = combination.min_installment_price;
            var minInstallmentMonths = combination.min_installment_months || 1;

            if (minInstallmentPrice && minInstallmentPrice > 0) {
                var formattedPrice = this._priceToStr(minInstallmentPrice);
                
                var $price = $parent.find('.oe_price .oe_currency_value');
                $price.text(formattedPrice);
                
                // Add or update installment suffix
                var $suffix = $parent.find('.oe_price .isep_month_suffix');
                var suffixText = minInstallmentMonths > 1 ? (' / ' + minInstallmentMonths + ' meses') : '';
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
                    console.log('ISEP Monthly Price: Found payment warning in alert.');
                    
                    // If the alert contains "success" or "éxito", we assume it's a mixed message
                    // and we only want to remove the warning part.
                    if (lowerHtml.indexOf('success') !== -1 || lowerHtml.indexOf('éxito') !== -1 || lowerHtml.indexOf('exito') !== -1) {
                        // Try to remove the warning text specifically. 
                        // Since we don't know the exact full string including HTML tags, 
                        // we can try to hide the specific text node or replace the content.
                        
                        // A safer approach for mixed content: 
                        // 1. Get the text. 
                        // 2. If it contains the warning, replace the warning text with empty string.
                        // 3. Update HTML.
                        
                        // Regex to match the warning sentence roughly
                        // Spanish: "No podemos confirmar su pedido ya que el importe pagado es diferente al total de la cesta. Póngase en contacto con nosotros para obtener más información."
                        var regexEs = /No podemos confirmar su pedido.*?información\./i;
                        var regexEn = /We cannot confirm your order.*?information\./i;
                        
                        var newHtml = html.replace(regexEs, '').replace(regexEn, '');
                        
                        // Also clean up any leftover <br> or empty lines if possible
                        newHtml = newHtml.replace(/<br\s*\/?>\s*<br\s*\/?>/g, '<br>');
                        
                        $alert.html(newHtml);
                        console.log('ISEP Monthly Price: Removed warning text from mixed alert.');
                    } else {
                        // If it doesn't look like a success message, hide the whole alert
                        $alert.addClass('d-none');
                        $alert.hide();
                        console.log('ISEP Monthly Price: Hidden full warning alert.');
                    }
                }
            });
        }

        hidePaymentWarning();
        
        // Observer for dynamic changes
        var observer = new MutationObserver(function(mutations) {
            hidePaymentWarning();
        });
        
        var target = document.querySelector('body');
        if (target) {
            observer.observe(target, { childList: true, subtree: true });
        }
    });
});
