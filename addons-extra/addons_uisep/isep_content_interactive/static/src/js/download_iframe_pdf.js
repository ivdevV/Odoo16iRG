/** @odoo-module **/

import publicWidget from 'web.public.widget';
import { loadJS } from '@web/core/assets';

// Función para convertir imágenes externas a base64
async function convertImagesToBase64(doc) {
    console.log('=== CONVIRTIENDO IMÁGENES A BASE64 (iframe) ===');
    
    const images = doc.querySelectorAll('img');
    const promises = [];
    let convertedCount = 0;
    let errorCount = 0;
    
    for (const img of images) {
        const src = img.getAttribute('src') || '';
        
        // Solo procesar imágenes externas
        const isExternal = src.startsWith('http') && !src.includes(window.location.hostname);
        const isBackblaze = src.includes('backblazeb2.com') || src.includes('b2.s3');
        
        if (isExternal || isBackblaze) {
            console.log('Procesando imagen:', src.substring(0, 80) + '...');
            
            const promise = new Promise((resolve) => {
                const tempImg = new Image();
                tempImg.crossOrigin = 'anonymous';
                
                tempImg.onload = () => {
                    try {
                        const canvas = document.createElement('canvas');
                        canvas.width = tempImg.naturalWidth || tempImg.width || 200;
                        canvas.height = tempImg.naturalHeight || tempImg.height || 200;
                        const ctx = canvas.getContext('2d');
                        ctx.drawImage(tempImg, 0, 0);
                        img.src = canvas.toDataURL('image/png');
                        convertedCount++;
                        console.log('Imagen convertida:', src.substring(0, 50));
                    } catch (e) {
                        console.warn('Error en canvas:', src.substring(0, 50));
                        errorCount++;
                    }
                    resolve();
                };
                
                tempImg.onerror = () => {
                    console.warn('No se pudo cargar imagen:', src.substring(0, 50));
                    // Crear placeholder
                    img.style.backgroundColor = '#f0f0f0';
                    img.style.minWidth = '100px';
                    img.style.minHeight = '50px';
                    img.alt = 'Imagen no disponible';
                    errorCount++;
                    resolve();
                };
                
                // Agregar timestamp para evitar cache
                const separator = src.includes('?') ? '&' : '?';
                tempImg.src = src + separator + '_nocache=' + Date.now();
            });
            
            promises.push(promise);
        }
    }
    
    // Esperar con timeout
    await Promise.race([
        Promise.all(promises),
        new Promise(resolve => setTimeout(resolve, 15000))
    ]);
    
    console.log(`Conversión: ${convertedCount} éxitos, ${errorCount} errores`);
}

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

        btn.addEventListener('click', async function (e) {
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
            text.textContent = 'Preparando imágenes...';

            // Convertir imágenes externas a base64 primero
            await convertImagesToBase64(iframeDocument);
            
            text.textContent = 'Generando PDF...';

            const rawSlideName = btn.dataset.slideName || 'contenido_descargado';
            const safeSlideName = rawSlideName.replace(/[\\/:*?"<>|]/g, '').replace(/\s+/g, '_');

            html2pdf()
                .set({
                    margin: 0.5,
                    filename: `${safeSlideName}.pdf`,
                    image: { type: 'jpeg', quality: 0.98 },
                    html2canvas: { 
                        scale: 2,
                        useCORS: true,
                        allowTaint: true,
                        logging: true,
                        imageTimeout: 20000
                    },
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
