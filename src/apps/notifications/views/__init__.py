"""
Views for the notifications app, split by what they serve.

`sms_view` is the staff console — composing a batch, saved recipient groups,
the delivery log. `push_view` is the browser-notification plumbing: small JSON
handlers plus the two files (`/sw.js`, `/manifest.webmanifest`) that have to be
served from the site root.

They share an app because both are "tell the clinic something happened", but
they share nothing else — one spends money per message, the other is a
browser permission — so they do not belong in one file.

`__init__.py` is present on purpose. Without it Python treats the directory as
an implicit namespace package, which mostly works and then quietly does not:
test discovery skips it, and a same-named directory elsewhere on the path can
merge into it.
"""
