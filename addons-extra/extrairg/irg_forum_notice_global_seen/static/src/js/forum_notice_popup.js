/** @odoo-module **/

import ajax from 'web.ajax';

const POPUP_POLL_INTERVAL_MS = 3000;
const POPUP_INITIAL_DELAY_MS = 1200;

let popupPollTimer = null;
let isCheckingPopup = false;
const suppressedNoticeIds = new Set();
const markSeenRequests = new Map();

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

function markSeen(noticeId, courseId = null) {
    if (!noticeId) {
        return Promise.reject(new Error('Missing forum notice id'));
    }
    if (!markSeenRequests.has(noticeId)) {
        const request = ajax.jsonRpc(
            '/campus/forum_notice_popup_seen',
            'call',
            {notice_id: noticeId, course_id: courseId}
        ).then((result) => {
            if (!result || !result.ok) {
                throw new Error('Forum notice was not persisted as seen');
            }
            return result;
        }).finally(() => markSeenRequests.delete(noticeId));
        markSeenRequests.set(noticeId, request);
    }
    return markSeenRequests.get(noticeId);
}

function shouldRunPopupCheck() {
    const path = window.location.pathname || '';
    return !path.startsWith('/web');
}

async function fetchNoticePayload() {
    let result = await ajax.jsonRpc('/campus/forum_notice_popup', 'call', {});
    const fallbackCourseId = getCourseIdFromPath() || getFirstCourseIdFromPage();
    if ((!result || !result.notice) && fallbackCourseId) {
        result = await ajax.jsonRpc(
            `/campus/course/${fallbackCourseId}/forum_notice_popup`,
            'call',
            {}
        );
    }

    const notice = result && result.notice;
    if (!notice || !notice.id || suppressedNoticeIds.has(notice.id)) {
        return null;
    }
    return {
        notice,
        courseId: notice.course_id || fallbackCourseId,
    };
}

async function dismissPopup(wrapper, courseId, noticeId) {
    suppressedNoticeIds.add(noticeId);
    try {
        await markSeen(noticeId, courseId);
    } catch (error) {
        console.warn('[irg_forum_notice_global_seen] Failed to mark notice', error);
    } finally {
        wrapper.remove();
    }
}

function getSafeNoticeUrl(value) {
    if (typeof value !== 'string' || !value.trim()) {
        return null;
    }
    try {
        const url = new URL(value, window.location.origin);
        if (
            !['http:', 'https:'].includes(url.protocol) ||
            url.origin !== window.location.origin
        ) {
            return null;
        }
        return url.href;
    } catch (error) {
        return null;
    }
}

function renderPopup(courseId, notice) {
    if (!notice || !notice.id || suppressedNoticeIds.has(notice.id)) {
        return;
    }

    const wrapper = document.createElement('div');
    wrapper.className = 'irg-forum-popup-wrap';
    wrapper.dataset.noticeId = String(notice.id);
    wrapper.innerHTML = `
        <div class="irg-forum-popup-backdrop"></div>
        <div class="irg-forum-popup-card" role="dialog" aria-modal="true" aria-label="Aviso del foro">
            <button type="button" class="irg-forum-popup-close" aria-label="Cerrar">×</button>
            <div class="irg-forum-popup-badge">Aviso del foro</div>
            <h4 class="irg-forum-popup-title"></h4>
            <div class="irg-forum-popup-meta" hidden></div>
            <div class="irg-forum-popup-preview" hidden></div>
            <div class="irg-forum-popup-actions">
                <button type="button" class="btn btn-secondary irg-forum-popup-dismiss">Cerrar</button>
            </div>
        </div>
    `;
    document.body.appendChild(wrapper);

    const titleNode = wrapper.querySelector('.irg-forum-popup-title');
    const metaNode = wrapper.querySelector('.irg-forum-popup-meta');
    const previewNode = wrapper.querySelector('.irg-forum-popup-preview');
    const actionsNode = wrapper.querySelector('.irg-forum-popup-actions');
    const closeBtn = wrapper.querySelector('.irg-forum-popup-close');
    const dismissBtn = wrapper.querySelector('.irg-forum-popup-dismiss');
    const backdrop = wrapper.querySelector('.irg-forum-popup-backdrop');

    titleNode.textContent = notice.title || 'Nuevo aviso';
    if (notice.forum_name) {
        metaNode.hidden = false;
        metaNode.textContent = `Foro: ${notice.forum_name}`;
    }
    if (notice.preview) {
        previewNode.hidden = false;
        previewNode.textContent = notice.preview;
    }

    const safeUrl = getSafeNoticeUrl(notice.url);
    let openBtn = null;
    if (safeUrl) {
        openBtn = document.createElement('a');
        openBtn.className = 'btn btn-primary irg-forum-popup-open';
        openBtn.textContent = 'Ver aviso';
        openBtn.href = safeUrl;
        actionsNode.appendChild(openBtn);
    }

    [closeBtn, dismissBtn, backdrop].forEach((node) => {
        if (node) {
            node.addEventListener('click', () => {
                dismissPopup(wrapper, courseId, notice.id);
            });
        }
    });

    if (openBtn) {
        openBtn.addEventListener('click', async (event) => {
            event.preventDefault();
            suppressedNoticeIds.add(notice.id);
            try {
                await markSeen(notice.id, courseId);
            } catch (error) {
                console.warn(
                    '[irg_forum_notice_global_seen] Failed to mark notice',
                    error
                );
            } finally {
                window.location.assign(openBtn.href);
            }
        });
    }
}

async function initForumNoticePopup() {
    if (
        !shouldRunPopupCheck() ||
        document.querySelector('.irg-forum-popup-wrap') ||
        isCheckingPopup
    ) {
        return;
    }
    isCheckingPopup = true;
    try {
        const payload = await fetchNoticePayload();
        if (payload) {
            renderPopup(payload.courseId, payload.notice);
        }
    } catch (error) {
        console.warn(
            '[irg_forum_notice_global_seen] Failed to load popup notice',
            error
        );
    } finally {
        isCheckingPopup = false;
    }
}

function startForumNoticePolling() {
    if (!shouldRunPopupCheck() || popupPollTimer) {
        return;
    }
    window.setTimeout(initForumNoticePopup, POPUP_INITIAL_DELAY_MS);
    popupPollTimer = window.setInterval(
        initForumNoticePopup,
        POPUP_POLL_INTERVAL_MS
    );
}

function attachVisibilityRefresh() {
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
            initForumNoticePopup();
        }
    });
}

function start() {
    startForumNoticePolling();
    attachVisibilityRefresh();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
} else {
    start();
}
