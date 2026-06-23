(function () {
    'use strict';

    function initN8nChat() {
        // Evitar inicializar múltiples veces en la misma vista/página
        if (window.n8nChatInitialized) {
            return;
        }

        const configEl = document.getElementById('irg_n8n_chat_bubble_config');
        if (!configEl) {
            return;
        }

        const webhookUrl = configEl.getAttribute('data-webhook-url');
        if (!webhookUrl) {
            return;
        }

        const title = configEl.getAttribute('data-title') || 'Soporte Académico';
        const welcomeMsg = configEl.getAttribute('data-welcome-msg') || '¡Hola! ¿En qué te puedo ayudar hoy?';
        const studentName = configEl.getAttribute('data-student-name') || '';
        const studentEmail = configEl.getAttribute('data-student-email') || '';
        const courseName = configEl.getAttribute('data-course-name') || '';
        const subjectName = configEl.getAttribute('data-subject-name') || '';

        // Marcar como inicializado para prevenir colisiones o bucles de llamadas
        window.n8nChatInitialized = true;

        // Cargar el CSS del widget de chat de n8n si no existe
        if (!document.getElementById('n8n-chat-style')) {
            const link = document.createElement('link');
            link.id = 'n8n-chat-style';
            link.rel = 'stylesheet';
            link.href = 'https://cdn.jsdelivr.net/npm/@n8n/chat/code/dist/style.css';
            document.head.appendChild(link);
        }

        // Cargar el bundle ES del chat de n8n dinámicamente
        import('https://cdn.jsdelivr.net/npm/@n8n/chat/code/dist/chat.bundle.es.js')
            .then(function (module) {
                module.createChat({
                    webhookUrl: webhookUrl,
                    showWelcomeScreen: true,
                    chatInputPlaceholder: 'Escribe tu consulta...',
                    title: title,
                    subtitle: courseName + ' - ' + subjectName,
                    initialMessages: [welcomeMsg],
                    metadata: {
                        studentName: studentName,
                        studentEmail: studentEmail,
                        courseName: courseName,
                        subjectName: subjectName
                    }
                });
            })
            .catch(function (err) {
                console.error('Error al instanciar el chat de n8n:', err);
                window.n8nChatInitialized = false;
            });
    }

    // Registrar observadores o listeners de carga
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        initN8nChat();
    } else {
        document.addEventListener('DOMContentLoaded', initN8nChat);
    }
})();
