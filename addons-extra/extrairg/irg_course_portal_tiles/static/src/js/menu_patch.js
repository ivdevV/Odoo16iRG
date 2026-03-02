document.addEventListener('DOMContentLoaded', function () {
    try {
        // Change Blog link to external articles page
        var anchors = document.querySelectorAll('a.nav-link, nav a');
        anchors.forEach(function(a){
            var text = (a.textContent || '').trim();
            if(text === 'Blog' || (a.getAttribute('href') && a.getAttribute('href').indexOf('/blog') !== -1)){
                a.setAttribute('href', 'https://institutoraimongaja.com/articulos/');
                // open external in same tab; no-op otherwise
            }
            if(text === 'Atención al cliente' || text === 'Atención al Cliente'){
                a.textContent = 'Atención al Alumno';
            }
        });

        // Also replace in possible dropdowns or menu spans
        var nodes = document.querySelectorAll('li a, li span');
        nodes.forEach(function(n){
            var t = (n.textContent || '').trim();
            if(t === 'Atención al cliente' || t === 'Atención al Cliente'){
                n.textContent = 'Atención al Alumno';
            }
            if(t === 'Blog'){
                // if element is not an anchor, try to find child anchor
                var a = n.querySelector && n.querySelector('a');
                if(a) a.setAttribute('href', 'https://institutoraimongaja.com/articulos/');
            }
        });

        // Replace in Aplicaciones tile cards (hover_effect spans inside portal tiles)
        var tileLabels = document.querySelectorAll('.hover_effect span, .card_new span, .card-ext span');
        tileLabels.forEach(function(s){
            var t = (s.textContent || '').trim();
            if(t === 'Atención al cliente' || t === 'Atención al Cliente'){
                s.textContent = 'Atención al Alumno';
            }
        });
    } catch (err) {
        console && console.warn && console.warn('menu_patch error', err);
    }
});
