/** @odoo-module **/

/**
 * irg_html_embed_slide — embed_widget.js
 *
 * Widget para la vista normal del reproductor (no pantalla completa).
 * Selecciona todos los div.irg_html_embed_wrapper y los convierte en
 * un iframe con srcdoc, sandbox seguro y auto-redimensionado dinámico.
 */

import publicWidget from 'web.public.widget';

const IFRAME_SANDBOX = [
    'allow-scripts',
    'allow-same-origin',
    'allow-forms',
    'allow-popups',
    'allow-modals',
    'allow-downloads',
    'allow-popups-to-escape-sandbox',
    'allow-top-navigation-by-user-activation',
].join(' ');

/**
 * Genera el srcdoc completo del iframe envolviendo el HTML del usuario
 * con un script interno de auto-altura y reenvío de descargas al padre.
 */
function buildSrcdoc(html) {
    return `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<style>html,body{margin:0;padding:0} body{overflow:hidden}</style>
<script>
(function(){
  var scheduled = false;
  function postHeight(){
    scheduled = false;
    var h = Math.max(
      document.documentElement.scrollHeight || 0,
      document.body.scrollHeight || 0,
      document.documentElement.offsetHeight || 0,
      document.body.offsetHeight || 0,
      document.documentElement.clientHeight || 0
    );
    window.parent.postMessage({ __irg_embed__: true, height: h }, '*');
  }
  function schedule(){ if (!scheduled){ scheduled = true; requestAnimationFrame(postHeight); } }

  window.addEventListener('load', schedule);
  window.addEventListener('resize', schedule);
  document.addEventListener('DOMContentLoaded', schedule);
  new MutationObserver(schedule).observe(document.documentElement, {
    childList: true, subtree: true, attributes: true, characterData: true
  });
  if ('ResizeObserver' in window){ new ResizeObserver(schedule).observe(document.documentElement); }
  setTimeout(schedule, 50); setTimeout(schedule, 250); setTimeout(schedule, 1000);

  // Interceptar clics en enlaces de descarga y reenviarlos al padre
  document.addEventListener('click', function(e){
    var a = e.target.closest && e.target.closest('a[href]');
    if (!a) return;
    var href = a.getAttribute('href') || '';
    var isDownload = a.hasAttribute('download')
      || /\\/web\\/content\\//.test(href)
      || a.getAttribute('data-download') === '1';
    if (isDownload){
      e.preventDefault();
      var u = new URL(href, window.location.href).toString();
      window.parent.postMessage({ __irg_embed_download__: u }, '*');
    }
  }, true);

  window.addEventListener('message', function(ev){
    if (ev && ev.data && ev.data.__irg_embed_getHeight__) schedule();
  });
})();
<\/script>
</head>
<body>${html}</body>
</html>`;
}

publicWidget.registry.IrgHtmlEmbedWidget = publicWidget.Widget.extend({
    selector: '.irg_html_embed_wrapper',

    start: function () {
        const html = this.el.dataset.embed;
        if (!html) return;

        const iframe = document.createElement('iframe');
        iframe.title = 'Contenido embebido';
        iframe.setAttribute('width', '100%');
        iframe.setAttribute('scrolling', 'no');
        iframe.setAttribute('allow', 'microphone; camera');
        iframe.setAttribute('sandbox', IFRAME_SANDBOX);
        iframe.style.cssText = 'border:none;width:100%;display:block;overflow:hidden;';
        iframe.setAttribute('srcdoc', buildSrcdoc(html));

        const requestMeasure = () => {
            try { iframe.contentWindow && iframe.contentWindow.postMessage({ __irg_embed_getHeight__: true }, '*'); } catch(_){}
        };
        iframe.addEventListener('load', requestMeasure);

        const onMessage = (event) => {
            if (event.source !== iframe.contentWindow) return;
            const data = event.data || {};
            if (data.__irg_embed__ && typeof data.height === 'number' && data.height > 0) {
                iframe.style.height = data.height + 'px';
            }
            if (data.__irg_embed_download__) {
                this._triggerDownload(data.__irg_embed_download__);
            }
        };
        window.addEventListener('message', onMessage);

        const onResize = () => requestMeasure();
        window.addEventListener('resize', onResize);

        this.el.appendChild(iframe);

        this.on('destroy', this, () => {
            window.removeEventListener('message', onMessage);
            window.removeEventListener('resize', onResize);
        });
    },

    _triggerDownload(url) {
        try {
            const u = new URL(url, window.location.href);
            const allowed = new Set([window.location.hostname, 'app.universidadisep.com']);
            if (!allowed.has(u.hostname)) return;
            const a = document.createElement('a');
            a.href = u.toString(); a.target = '_blank'; a.rel = 'noopener';
            document.body.appendChild(a); a.click(); a.remove();
        } catch(_){}
    },
});
