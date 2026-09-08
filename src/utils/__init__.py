"""
Cross-app helpers, grouped by why you would open the file.

    security/   stops attacks — login throttling, signed tokens, HTML
                sanitising, the captcha
    http/       shapes a request or response — view mixins, response caching
    data/       checks or converts a value — field validators, social handles
    mail/       sends email — the helper, and the Celery task wrapping it

`__init__.py` is not ceremony here. Without it Python treats `utils` as an
implicit namespace package, and unittest's discovery walks past it — every
test under `utils/` was silently absent from `manage.py test` while still
passing when run explicitly as `manage.py test utils`.
"""
