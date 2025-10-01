/** @odoo-module **/

import publicWidget from 'web.public.widget';
import { loadJS } from '@web/core/assets';

publicWidget.registry.IframeDownloadButton = publicWidget.Widget.extend({
    selector: '#custom_download_button_iframe',
    start: async function () {
        const btn = this.el;
        const spinner = document.getElementById('custom_loading_spinner_iframe');
        const icon = document.getElementById('custom_download_icon_iframe');
        const text = document.getElementById('custom_download_text_iframe');

        if (!window.html2pdf) {
            await loadJS('https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js');
        }

        btn.addEventListener('click', function (e) {
            e.preventDefault();

            const iframe = document.getElementById('slide_dynamic_iframe');
            if (!iframe) {
                alert('No se encontró el iframe.');
                return;
            }

            const iframeDocument = iframe.contentDocument || iframe.contentWindow.document;
            if (!iframeDocument) {
                alert('No se pudo acceder al contenido del iframe.');
                return;
            }

            const element = iframeDocument.body;
            spinner.style.display = 'inline-block';
            icon.style.display = 'none';
            text.textContent = 'Generando PDF...';

            // const slideName = btn.dataset.slideName || 'contenido_iframe';
            const rawSlideName = btn.dataset.slideName || 'contenido_descargado';
            const safeSlideName = rawSlideName.replace(/[\\/:*?"<>|]/g, '').replace(/\s+/g, '_');

            html2pdf()
                .set({
                    margin: 0.5,
                    // filename: `${slideName}.pdf`,
                    filename: `${safeSlideName}.pdf`,
                    image: { type: 'jpeg', quality: 0.98 },
                    html2canvas: { scale: 2 },
                    jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
                })
                .from(element)
                .save()
                .finally(() => {
                    spinner.style.display = 'none';
                    icon.style.display = 'inline-block';
                    text.textContent = 'Descargar';
                });
        });
    }
});
