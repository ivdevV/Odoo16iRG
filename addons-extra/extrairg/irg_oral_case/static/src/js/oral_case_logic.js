(function (root) {
    'use strict';

    var RETRYABLE = {
        n8n_unavailable: true,
        n8n_not_configured: true,
        n8n_rejected: true,
        server_error: true,
    };

    var ERRORS = {
        session_expired: 'Tu sesión ha caducado. Inicia sesión de nuevo; tus respuestas no se han enviado.',
        invalid_csrf: 'La página lleva mucho tiempo abierta. Recárgala y vuelve a empezar.',
        missing_consent: 'Falta tu consentimiento. Vuelve al principio y marca la casilla.',
        invalid_consent: 'Falta tu consentimiento. Vuelve al principio y marca la casilla.',
        missing_video: 'Una de tus respuestas está vacía. Grábala de nuevo.',
        empty_video: 'Una de tus respuestas está vacía. Grábala de nuevo.',
        video_too_large: 'Una respuesta es demasiado pesada para enviarla. Grábala de nuevo un poco más corta.',
        invalid_video_type: 'Tu navegador graba en un formato que no podemos recibir. Usa Chrome, Edge o Firefox.',
        duration_exceeded: 'Una respuesta supera el tiempo máximo. Grábala de nuevo.',
        invalid_duration: 'Una respuesta supera el tiempo máximo. Grábala de nuevo.',
        missing_self_assessment: 'No se han podido preparar tus respuestas para el envío. Recarga la página.',
        invalid_self_assessment: 'No se han podido preparar tus respuestas para el envío. Recarga la página.',
        not_oral_case: 'Esta actividad no está disponible ahora mismo. Avisa a tu profesorado.',
        missing_slide: 'Esta actividad no está disponible ahora mismo. Avisa a tu profesorado.',
        slide_not_found: 'Esta actividad no está disponible ahora mismo. Avisa a tu profesorado.',
        invalid_case_config: 'Esta actividad no está disponible ahora mismo. Avisa a tu profesorado.',
        slide_forbidden: 'No tienes acceso a esta actividad. Si crees que es un error, avisa a tu profesorado.',
        grade_already_confirmed: 'Tu profesorado ya confirmó la nota de esta actividad.',
        n8n_unavailable: 'No hemos podido enviar tus respuestas por un problema técnico. Tus grabaciones siguen en esta página: inténtalo de nuevo en unos minutos sin cerrarla.',
        n8n_not_configured: 'No hemos podido enviar tus respuestas por un problema técnico. Tus grabaciones siguen en esta página: inténtalo de nuevo en unos minutos sin cerrarla.',
        n8n_rejected: 'No hemos podido enviar tus respuestas por un problema técnico. Tus grabaciones siguen en esta página: inténtalo de nuevo en unos minutos sin cerrarla.',
        server_error: 'No hemos podido enviar tus respuestas por un problema técnico. Tus grabaciones siguen en esta página: inténtalo de nuevo en unos minutos sin cerrarla.',
        job_not_found: 'No encontramos tu envío. Si acabas de enviarlo, espera un momento y recarga.',
        clips_required: 'No se han podido preparar tus respuestas para el envío. Recarga la página.',
        clips_mismatch: 'No se han podido preparar tus respuestas para el envío. Recarga la página.',
        single_video_expected: 'No se han podido preparar tus respuestas para el envío. Recarga la página.',
    };

    function formatTime(seconds) {
        var value = Math.max(0, parseInt(seconds, 10) || 0);
        var minutes = Math.floor(value / 60);
        var rest = value % 60;
        return String(minutes) + ':' + (rest < 10 ? '0' : '') + String(rest);
    }

    function isSafeHttps(url) {
        if (!url || /[\s\\]/.test(url)) {
            return false;
        }
        try {
            var parsed = new URL(url);
            return parsed.protocol === 'https:' && !parsed.username && !parsed.password && !!parsed.hostname;
        } catch (error) {
            return false;
        }
    }

    function isVimeoHost(url) {
        if (!isSafeHttps(url)) {
            return false;
        }
        var host = new URL(url).hostname;
        return host === 'vimeo.com' || host === 'www.vimeo.com' || host === 'player.vimeo.com';
    }

    function vimeoSrc(url) {
        if (!isVimeoHost(url)) {
            return null;
        }
        var parsed = new URL(url);
        if (parsed.hostname === 'player.vimeo.com') {
            return parsed.toString();
        }
        var parts = parsed.pathname.split('/').filter(Boolean);
        var id = '';
        var hash = '';
        for (var i = 0; i < parts.length; i++) {
            if (/^[0-9]+$/.test(parts[i])) {
                id = parts[i];
                if (parts[i + 1] && /^[A-Za-z0-9]+$/.test(parts[i + 1])) {
                    hash = parts[i + 1];
                }
                break;
            }
        }
        if (!id) {
            return null;
        }
        var target = new URL('https://player.vimeo.com/video/' + id);
        parsed.searchParams.forEach(function (value, key) {
            target.searchParams.set(key, value);
        });
        if (hash && !target.searchParams.get('h')) {
            target.searchParams.set('h', hash);
        }
        return target.toString();
    }

    function chooseRecorderMime(isTypeSupported) {
        var options = ['video/webm;codecs=vp8,opus', 'video/webm', 'video/mp4'];
        if (typeof isTypeSupported !== 'function') {
            return '';
        }
        for (var i = 0; i < options.length; i++) {
            try {
                if (isTypeSupported(options[i])) {
                    return options[i];
                }
            } catch (error) {
                continue;
            }
        }
        return '';
    }

    function canonicalFromMime(mime) {
        var base = String(mime || '').split(';')[0].trim().toLowerCase();
        if (base === 'video/mp4') {
            return {mime: 'video/mp4', ext: 'mp4'};
        }
        if (base === 'video/webm') {
            return {mime: 'video/webm', ext: 'webm'};
        }
        return null;
    }

    function screenButtons(screen, options) {
        options = options || {};
        if (screen === 'recording') {
            return ['stop'];
        }
        if (screen === 'review') {
            var buttons = ['use'];
            if (options.allowRetry) {
                buttons.push('retry');
            }
            return buttons;
        }
        if (screen === 'prompt') {
            return ['record'];
        }
        if (screen === 'clip') {
            return options.skip ? ['skip'] : ['play'];
        }
        return [];
    }

    function retryRestartsClip() {
        return false;
    }

    function clipDurationLabel(seconds) {
        var value = Number(seconds);
        if (!isFinite(value) || value <= 0) {
            return null;
        }
        return 'El vídeo dura ' + formatTime(Math.round(value));
    }

    function responseLimitLabel(seconds) {
        return 'Tiempo máximo: ' + formatTime(seconds);
    }

    function countdownAnnouncement(left, flags) {
        flags = flags || {};
        var value = Math.max(0, parseInt(left, 10) || 0);
        if (!flags.started) {
            return {
                text: 'Grabando. Quedan ' + formatTime(value) + '.',
                announced15: false,
                started: true,
            };
        }
        if (value === 15 && !flags.announced15) {
            return {
                text: 'Quedan 15 segundos.',
                announced15: true,
                started: true,
            };
        }
        if (value <= 0) {
            return {
                text: 'Has llegado al tiempo máximo. Tu respuesta se ha guardado.',
                announced15: true,
                started: true,
            };
        }
        return null;
    }

    function shouldOfferSkip(flags) {
        return !!(flags && flags.failed);
    }

    function watchdogMs(durationSeconds, playbackStarted) {
        if (!playbackStarted) {
            return null;
        }
        var duration = Number(durationSeconds);
        if (isFinite(duration) && duration > 0) {
            return Math.round((duration + 15) * 1000);
        }
        return 90000;
    }

    function visibleStudentText(segment) {
        if (!segment) {
            return '';
        }
        if (segment.student_text && String(segment.student_text).trim()) {
            return String(segment.student_text);
        }
        return segment.prompt ? String(segment.prompt) : '';
    }

    function errorMessage(code) {
        return ERRORS[code] || 'No se ha podido enviar la intervención.';
    }

    function canRetrySubmit(code) {
        return !!RETRYABLE[code];
    }

    root.IrgOralCaseLogic = {
        formatTime: formatTime,
        isSafeHttps: isSafeHttps,
        isVimeoHost: isVimeoHost,
        vimeoSrc: vimeoSrc,
        chooseRecorderMime: chooseRecorderMime,
        canonicalFromMime: canonicalFromMime,
        screenButtons: screenButtons,
        retryRestartsClip: retryRestartsClip,
        clipDurationLabel: clipDurationLabel,
        responseLimitLabel: responseLimitLabel,
        countdownAnnouncement: countdownAnnouncement,
        shouldOfferSkip: shouldOfferSkip,
        watchdogMs: watchdogMs,
        visibleStudentText: visibleStudentText,
        errorMessage: errorMessage,
        canRetrySubmit: canRetrySubmit,
    };
}(typeof globalThis !== 'undefined' ? globalThis : this));
