/** @odoo-module **/

const FORUM_POST_PUBLISHED_KEY = 'irg_forum_post_published';
const SUCCESS_MESSAGE = '¡Post Publicado!';

function markPendingToastOnSubmit(event) {
    const form = event.target;
    if (!(form instanceof HTMLFormElement)) {
        return;
    }
    const action = form.getAttribute('action') || '';
    const method = (form.getAttribute('method') || 'get').toLowerCase();
    if (method === 'post' && action.includes('/forum/') && action.includes('/new')) {
        sessionStorage.setItem(FORUM_POST_PUBLISHED_KEY, String(Date.now()));
    }
}

function showPublishToastIfNeeded() {
    const marker = sessionStorage.getItem(FORUM_POST_PUBLISHED_KEY);
    if (!marker) {
        return;
    }
    sessionStorage.removeItem(FORUM_POST_PUBLISHED_KEY);

    const markerTime = Number(marker);
    if (!Number.isFinite(markerTime) || (Date.now() - markerTime) > 60000) {
        return;
    }

    const toast = document.createElement('div');
    toast.textContent = SUCCESS_MESSAGE;
    toast.className = 'alert alert-success shadow';
    toast.style.position = 'fixed';
    toast.style.top = '24px';
    toast.style.right = '24px';
    toast.style.zIndex = '1080';
    toast.style.margin = '0';
    toast.style.transition = 'opacity .3s ease';

    document.body.appendChild(toast);

    window.setTimeout(() => {
        toast.style.opacity = '0';
    }, 4700);

    window.setTimeout(() => {
        toast.remove();
    }, 5000);
}

document.addEventListener('submit', markPendingToastOnSubmit, true);
document.addEventListener('DOMContentLoaded', showPublishToastIfNeeded);
