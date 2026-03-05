/** @odoo-module **/

import ajax from 'web.ajax';

const POPUP_POLL_INTERVAL_MS = 10000;
const POPUP_INITIAL_DELAY_MS = 1200;

let popupPollTimer = null;
let isCheckingPopup = false;

function getCourseIdFromPath() {
    const match = window.location.pathname.match(/\/campus\/course\/(\d+)/);
    return match ? parseInt(match[1], 10) : null;
}

function getFirstCourseIdFromPage() {
    const links = document.querySelectorAll('a[href*="/campus/course/"]');
    for (const link of links) {
        const href = (link.getAttribute('href') || '').trim();
        const match = href.match(/\/campus\/course\/(\d+)/);
        if (match) {
            return parseInt(match[1], 10);
        }
    }
    return null;
}

async function markSeen(courseId, noticeId) {
    if (!courseId || !noticeId) {
        return;
    }
    await ajax.jsonRpc('/campus/forum_notice_popup_seen', 'call', {
        course_id: courseId,
        notice_id: noticeId,
    });
}

function shouldRunPopupCheck() {
    const path = window.location.pathname || '';
    return !path.startsWith('/web');
}

async function fetchNoticePayload() {
    let result = await ajax.jsonRpc('/campus/forum_notice_popup', 'call', {});

    const fallbackCourseId = getCourseIdFromPath() || getFirstCourseIdFromPage();
    if ((!result || !result.notice) && fallbackCourseId) {
        result = await ajax.jsonRpc(`/campus/course/${fallbackCourseId}/forum_notice_popup`, 'call', {});
    }

    const notice = result && result.notice;
    if (!notice || !notice.id) {
        return null;
    }

    const noticeCourseId = notice.course_id || fallbackCourseId;
    return {
        notice,
        courseId: noticeCourseId,
    };
}

function closePopup(wrapper, courseId, noticeId) {
    markSeen(courseId, noticeId).catch(() => {});
    wrapper.remove();
}

function renderPopup(courseId, notice) {
    if (!notice || !notice.id) {
        return;
    }

    const wrapper = document.createElement('div');
    wrapper.className = 'irg-forum-popup-wrap';
    wrapper.innerHTML = `
        <div class="irg-forum-popup-backdrop"></div>
        <div class="irg-forum-popup-card" role="dialog" aria-modal="true" aria-label="Aviso del foro">
            <button type="button" class="irg-forum-popup-close" aria-label="Cerrar">×</button>
            <div class="irg-forum-popup-badge">Aviso del foro</div>
            <h4 class="irg-forum-popup-title">${notice.title || 'Nuevo aviso'}</h4>
            ${notice.forum_name ? `<div class="irg-forum-popup-meta">Foro: ${notice.forum_name}</div>` : ''}
            ${notice.preview ? `<div class="irg-forum-popup-preview">${notice.preview}</div>` : ''}
            <div class="irg-forum-popup-actions">
                <button type="button" class="btn btn-secondary irg-forum-popup-dismiss">Cerrar</button>
                ${notice.url ? `<a class="btn btn-primary irg-forum-popup-open" href="${notice.url}">Ver aviso</a>` : ''}
            </div>
        </div>
    `;

    document.body.appendChild(wrapper);

    const closeBtn = wrapper.querySelector('.irg-forum-popup-close');
    const dismissBtn = wrapper.querySelector('.irg-forum-popup-dismiss');
    const backdrop = wrapper.querySelector('.irg-forum-popup-backdrop');
    const openBtn = wrapper.querySelector('.irg-forum-popup-open');

    [closeBtn, dismissBtn, backdrop].forEach((node) => {
        if (node) {
            node.addEventListener('click', () => closePopup(wrapper, courseId, notice.id));
        }
    });

    if (openBtn) {
        openBtn.addEventListener('click', () => {
            markSeen(courseId, notice.id).catch(() => {});
        });
    }
}

async function initForumNoticePopup() {
    if (!shouldRunPopupCheck()) {
        return;
    }

    if (document.querySelector('.irg-forum-popup-wrap')) {
        return;
    }

    if (isCheckingPopup) {
        return;
    }

    isCheckingPopup = true;

    try {
        const payload = await fetchNoticePayload();
        if (!payload) {
            return;
        }
        renderPopup(payload.courseId, payload.notice);
    } catch (error) {
        console.warn('[irg_forum_notice_popup] Failed to load popup notice', error);
    } finally {
        isCheckingPopup = false;
    }
}

function startForumNoticePolling() {
    if (!shouldRunPopupCheck() || popupPollTimer) {
        return;
    }

    window.setTimeout(() => {
        initForumNoticePopup();
    }, POPUP_INITIAL_DELAY_MS);

    popupPollTimer = window.setInterval(() => {
        initForumNoticePopup();
    }, POPUP_POLL_INTERVAL_MS);
}

function attachVisibilityRefresh() {
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
            initForumNoticePopup();
        }
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        startForumNoticePolling();
        attachVisibilityRefresh();
    });
} else {
    startForumNoticePolling();
    attachVisibilityRefresh();
}
