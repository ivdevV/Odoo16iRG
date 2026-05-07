(function () {
    'use strict';

    function getClosestButton(target) {
        if (target && target.closest) {
            return target.closest('#custom_download_button');
        }
        if (target && target.parentElement) {
            return target.parentElement.closest('#custom_download_button');
        }
        return null;
    }

    function getDownloadButton(event) {
        if (event && event.target) {
            const button = getClosestButton(event.target);
            if (button) {
                return button;
            }
        }
        return document.getElementById('custom_download_button');
    }

    function restoreDownloadButton() {
        const spinner = document.getElementById('custom_loading_spinner');
        const text = document.getElementById('custom_download_text');
        const icon = document.getElementById('custom_download_icon');
        if (spinner) {
            spinner.style.display = 'none';
        }
        if (text) {
            text.textContent = 'Descargar';
        }
        if (icon) {
            icon.style.display = 'inline-block';
        }
    }

    function cleanClone(element) {
        if (!element || !element.cloneNode) {
            return null;
        }
        const clone = element.cloneNode(true);
        clone.querySelectorAll('script').forEach((node) => node.remove());
        return clone;
    }

    function buildDownloadItem() {
        const fullScreenContent = document.querySelector('.o_wslides_fs_content');
        if (fullScreenContent) {
            return cleanClone(fullScreenContent);
        }

        const content = document.querySelector('.o_wslides_lesson_content');
        const container = document.createElement('div');
        let appended = false;

        if (content) {
            const header = content.querySelector('.oe_structure');
            if (header) {
                const headerClone = cleanClone(header);
                if (headerClone && headerClone.hasChildNodes()) {
                    for (const node of Array.from(headerClone.childNodes)) {
                        container.appendChild(node.cloneNode(true));
                    }
                    appended = true;
                }
            }
        }

        const slidesNode = document.querySelector('.o_wslides_lesson_content_type > div > div > div');
        if (slidesNode) {
            const slidesClone = cleanClone(slidesNode);
            if (slidesClone && slidesClone.hasChildNodes()) {
                for (const node of Array.from(slidesClone.childNodes)) {
                    container.appendChild(node.cloneNode(true));
                }
                appended = true;
            }
        }

        if (!appended && content) {
            const contentClone = cleanClone(content);
            if (contentClone) {
                container.appendChild(contentClone);
                appended = true;
            }
        }

        if (!appended) {
            const fallback = document.querySelector('.o_wslides_lesson_content_type');
            if (fallback) {
                const fallbackClone = cleanClone(fallback);
                if (fallbackClone) {
                    container.appendChild(fallbackClone);
                    appended = true;
                }
            }
        }

        return appended ? container : null;
    }

    function safeDownload(event) {
        const button = getDownloadButton(event);
        const name = (button && button.dataset && button.dataset.slideName) ? button.dataset.slideName : 'slide';
        const category = (button && button.dataset && button.dataset.slideType) ? button.dataset.slideType : '';
        const url = new URL(window.location.href);

        if (category === 'document') {
            const path = url.pathname.replace(/\/+$/, '');
            url.pathname = path + '/pdf_content';
            return downloadPDF(url.href, name);
        }

        const spinner = document.getElementById('custom_loading_spinner');
        const text = document.getElementById('custom_download_text');
        const icon = document.getElementById('custom_download_icon');
        if (spinner) {
            spinner.style.display = 'inline-block';
        }
        if (text) {
            text.textContent = 'Descargando...';
        }
        if (icon) {
            icon.style.display = 'none';
        }

        const item = buildDownloadItem();
        if (!item) {
            console.error('IRG: no slide content found for PDF download');
            restoreDownloadButton();
            return;
        }

        if (!window.html2pdf) {
            console.error('IRG: html2pdf library is missing');
            restoreDownloadButton();
            return;
        }

        const opt = {
            pagebreak: { mode: 'avoid-all' },
            margin: [12, 12, 12, 12],
            filename: name,
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 1 },
            jsPDF: {
                unit: 'mm',
                format: 'letter',
                orientation: 'portrait',
                width: 200.9,
                windowWidth: 720,
                autoPaging: 'text',
                margin: [72, 72, 72, 72],
            },
        };

        try {
            window.html2pdf().set(opt).from(item).save().then(() => {
                restoreDownloadButton();
            }).catch((err) => {
                console.error('IRG: html2pdf save failed', err);
                restoreDownloadButton();
            });
        } catch (err) {
            console.error('IRG: error while generating PDF', err);
            restoreDownloadButton();
        }
    }

    function downloadPDF(url, filename) {
        fetch(url).then((response) => response.blob()).then((blob) => {
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }).catch((error) => {
            console.error('IRG: downloadPDF error', error);
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        document.body.addEventListener('click', function (event) {
            const button = getClosestButton(event.target);
            if (!button) {
                return;
            }
            event.preventDefault();
            event.stopImmediatePropagation();
            safeDownload(event);
        }, true);
    });

    window.download_as_pdf = safeDownload;
})();
