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
            link.href = 'https://cdn.jsdelivr.net/npm/@n8n/chat/dist/style.css';
            document.head.appendChild(link);
        }

        // Cargar el bundle ES del chat de n8n dinámicamente
        const customWelcome = '¡Hola! Soy tu tutor virtual, pregúntame cualquier cosa 🤖';
        import('https://cdn.jsdelivr.net/npm/@n8n/chat/dist/chat.bundle.es.js')
            .then(function (module) {
                module.createChat({
                    webhookUrl: webhookUrl,
                    showWelcomeScreen: true,
                    defaultLanguage: 'es',
                    initialMessages: [customWelcome],
                    i18n: {
                        es: {
                            title: title,
                            subtitle: customWelcome,
                            getStarted: 'Iniciar chat',
                            inputPlaceholder: 'Escribe tu consulta...'
                        },
                        en: {
                            title: title,
                            subtitle: 'Hi! I am your virtual tutor, ask me anything 🤖',
                            getStarted: 'Start chat',
                            inputPlaceholder: 'Type your question...'
                        }
                    },
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
