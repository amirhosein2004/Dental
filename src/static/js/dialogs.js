/* Site-wide dialogs — replaces both window.confirm() and Bootstrap's modal.

   window.confirm() renders as an OS alert: wrong typography, wrong text
   direction, unrelated to the site. Bootstrap's modal meant shipping ~30KB of
   CSS and ~80KB of JS from a CDN for a handful of dialogs — and a CDN that is
   not reliably reachable from Iran.

   Two features, both delegated from `document` so markup injected later (AJAX
   "load more") works without re-binding.

   1. Confirm before a destructive submit — attributes go on the <form>:

          <form method="post" action="..."
                data-confirm
                data-confirm-title="حذف زمان"
                data-confirm-text="این زمان حذف شود؟"
                data-confirm-ok="حذف">

      Only `data-confirm` is required. Submitting is blocked until the user
      accepts, then the original form is submitted natively, so no view or
      request logic changes.

   2. Open an arbitrary <dialog> — for dialogs that hold a form or content:

          <button data-dialog-open="#catEdit-3">…</button>
          <dialog id="catEdit-3" class="cd-dialog"> … <button data-dialog-close> </dialog>

   Confirms fall back to window.confirm() where <dialog> is unsupported —
   better an ugly prompt than a destructive action with no confirmation. */
(function () {
    'use strict';

    var DEFAULTS = {
        title: 'تأیید عملیات',
        text: 'آیا از انجام این کار مطمئن هستید؟',
        ok: 'تأیید',
        cancel: 'انصراف',
    };

    var dialog = null;
    var pendingForm = null;

    function build() {
        var el = document.createElement('dialog');
        el.className = 'cd-dialog';
        el.innerHTML =
            '<div class="cd-dialog__body">' +
            '  <div class="cd-dialog__icon"><i class="fas fa-triangle-exclamation"></i></div>' +
            '  <h3 class="cd-dialog__title"></h3>' +
            '  <p class="cd-dialog__text"></p>' +
            '  <div class="cd-dialog__actions">' +
            '    <button type="button" class="ds-btn ds-btn--ghost" data-cd-cancel></button>' +
            '    <button type="button" class="ds-btn cd-dialog__ok" data-cd-ok></button>' +
            '  </div>' +
            '</div>';
        document.body.appendChild(el);

        el.querySelector('[data-cd-cancel]').addEventListener('click', function () {
            el.close();
        });
        el.querySelector('[data-cd-ok]').addEventListener('click', function () {
            var form = pendingForm;
            pendingForm = null;
            el.close();
            if (form) {
                // Mark as accepted so the submit handler lets it through.
                form.dataset.cdConfirmed = '1';
                // requestSubmit keeps native validation and the submitter's
                // name/value; form.submit() would skip both.
                if (form.requestSubmit) form.requestSubmit();
                else form.submit();
            }
        });
        // Clicking the backdrop cancels.
        el.addEventListener('click', function (event) {
            if (event.target === el) el.close();
        });
        el.addEventListener('close', function () { pendingForm = null; });

        return el;
    }

    function read(form, key) {
        return form.getAttribute('data-confirm-' + key) || DEFAULTS[key];
    }

    function onSubmit(event) {
        var form = event.target;
        if (!form.matches || !form.matches('[data-confirm]')) return;

        if (form.dataset.cdConfirmed === '1') {
            delete form.dataset.cdConfirmed;
            return; // already accepted — let it through
        }

        event.preventDefault();

        // Built on first use, so pages with no destructive form pay nothing
        // and forms injected later (AJAX "load more") are still covered.
        if (!dialog) dialog = build();

        if (typeof dialog.showModal !== 'function') {
            if (window.confirm(read(form, 'text'))) {
                form.dataset.cdConfirmed = '1';
                if (form.requestSubmit) form.requestSubmit();
                else form.submit();
            }
            return;
        }

        dialog.querySelector('.cd-dialog__title').textContent = read(form, 'title');
        dialog.querySelector('.cd-dialog__text').textContent = read(form, 'text');
        dialog.querySelector('[data-cd-ok]').textContent = read(form, 'ok');
        dialog.querySelector('[data-cd-cancel]').textContent = read(form, 'cancel');

        pendingForm = form;
        dialog.showModal();
    }

    /* ---- Generic <dialog> opener (replaces Bootstrap's modal) ---------- */

    function onClick(event) {
        var opener = event.target.closest('[data-dialog-open]');
        if (opener) {
            var target = document.querySelector(opener.getAttribute('data-dialog-open'));
            if (target && typeof target.showModal === 'function') {
                event.preventDefault();
                target.showModal();
            }
            return;
        }

        var closer = event.target.closest('[data-dialog-close]');
        if (closer) {
            var open = closer.closest('dialog');
            if (open) {
                event.preventDefault();
                open.close();
            }
        }
    }

    function onBackdropClick(event) {
        // A click that lands on the <dialog> itself (not its content) is the
        // backdrop; treat it as dismiss, matching the confirm dialog.
        if (event.target.tagName === 'DIALOG') event.target.close();
    }

    function init() {
        // Delegated + capture phase so forms added later (AJAX "load more")
        // are covered without re-binding.
        document.addEventListener('submit', onSubmit, true);
        document.addEventListener('click', onClick);
        document.addEventListener('click', onBackdropClick, true);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
