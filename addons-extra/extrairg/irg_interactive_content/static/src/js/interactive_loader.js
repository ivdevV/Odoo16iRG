/** @odoo-module **/

(function () {
    function appendScript(src, onLoad) {
        if (document.querySelector('script[data-irg-src="' + src + '"]')) {
            if (onLoad) {
                onLoad();
            }
            return;
        }
        var script = document.createElement('script');
        script.src = src;
        script.defer = true;
        script.setAttribute('data-irg-src', src);
        if (onLoad) {
            script.addEventListener('load', onLoad);
        }
        document.head.appendChild(script);
    }

    function initMermaid() {
        if (window.mermaid) {
            window.mermaid.initialize({
                startOnLoad: true,
                securityLevel: 'loose',
            });
            if (window.mermaid.run) {
                window.mermaid.run();
            }
        }
    }

    function bootInteractiveLibraries() {
        appendScript('https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js');
        appendScript('https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js', initMermaid);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bootInteractiveLibraries);
    } else {
        bootInteractiveLibraries();
    }
})();
