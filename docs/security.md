# Security

Every control here exists because of a specific way the site could be hurt.
Where one looks over-careful, the reason is named.

## Authentication

**Two steps.** Password, then a six-digit code by email. Neither half alone
gets in. The gate between them is an HMAC-signed session token whose payload
includes the user id — so keeping a valid signature and pointing it at another
account fails.

**Both windows are two minutes**, and deliberately equal. If the session token
outlived the code, a visitor would pass the first gate holding a code the next
screen then rejects.

**Login throttle** (`utils/security/login_throttle.py`) — counters in Redis:

| Counter | Limit | Catches |
|---|---|---|
| (IP, username) | 5 | guessing one account's password |
| IP | 20 | spraying one password across many usernames |

Locked for 15 minutes. **Keyed on the pair, never on the username alone** —
that is the shape most lockout bugs take: anyone who knows a staff username
could lock them out of their own account from anywhere, and the protection
becomes the attack.

Enforced by `LoginThrottleBackend`, first in `AUTHENTICATION_BACKENDS`. It
never authenticates anyone; it only refuses. Every login path goes through
`authenticate()`, so no future view can forget it.

This replaced django-axes, which had been installed but was **not enforcing
anything** — its backend was missing from `AUTHENTICATION_BACKENDS`, so it
recorded failures and refused nothing. Django's own `axes.W003` check was
reporting it.

## Authorisation

Two roles, one ownership function, and staff routes that answer **404 rather
than 403**. A 403 confirms the route exists and that the object id is real.

**Permission is re-checked at use, not only at grant.** Web push subscriptions
are the example: a doctor who leaves has `is_doctor` cleared and is locked out
the same minute, but their subscription row outlives that. Without a check at
send time their phone would keep receiving patients' names indefinitely.

## Input

**Blog HTML is sanitised on the way in**, in `BlogPost.save()`, using `nh3`
with an allow-list. Bodies are rendered with `|safe`, so anything that
survives executes in every visitor's browser. CKEditor's `disallow` list is
editor configuration — anyone posting straight to the endpoint skips it.

**Images are opened, not trusted by extension.** A text file named `.jpg` is
rejected because `validate_image` calls `Image.verify()`.

**Uploads are capped at 30 files per POST** and 60MB at nginx. Django limits
the size of one file but never how many arrive together.

**National codes are checksum-validated**, including rejecting repdigits,
which pass the checksum by coincidence.

**Public forms carry a math captcha and a honeypot.** The captcha is
self-hosted — no reCAPTCHA, which is unreliable from Iran and sends visitor
data to a third party. Challenges are single-use, capped at 8 live per
session, and the refresh endpoint is rate-limited: it is public, needs no
login, and every call writes to the session store.

## Transport and headers

`production.py` sets HSTS (1 year, preload), secure cookies, `SameSite=Strict`
sessions, `X-Frame-Options: DENY`, and `SECURE_SSL_REDIRECT`.

**`SECURE_PROXY_SSL_HEADER` is required alongside it.** TLS terminates at
nginx, which talks plain HTTP to gunicorn; without this setting Django never
sees a request as secure and redirects an already-HTTPS request back to HTTPS,
forever. nginx sets `X-Forwarded-Proto` on every proxied request, overwriting
whatever the client sent, so it cannot be forged.

**`ALLOWED_HOSTS` is never `*`.** The Host header is what Django echoes into
the absolute URLs it builds — the password-reset link among them.

## Rate limits

| Endpoint | Limit |
|---|---|
| contact form | 20/min |
| login | 5/min |
| OTP verify | 5/2min |
| booking | 6/min |
| bulk SMS | 5/min |
| captcha refresh | 30/min |

Keyed on the forwarded IP, since REMOTE_ADDR behind nginx is the proxy.

## Spend controls

Bulk SMS costs real money per recipient and cannot be undone:

- **500 recipients maximum** per send. A paste ten times larger than intended
  — a whole exported column instead of one cell — is refused at the form.
- **The task is not retried.** `send_sms` handles provider failure itself, so
  the only way the task raises is *after* some batches went out; a retry would
  re-send them, billed again, to patients who already got the message.

## What is deliberately not done

**No CSP header on pages.** The site loads no third-party scripts, so the main
benefit would be inline-script protection — and the theme initialiser in
`base.html` is inline by necessity (it must run before first paint to avoid a
flash). Worth revisiting with a nonce.

`/media/` is the exception and does carry one:
`default-src 'none'; … sandbox`, set by nginx. Uploads are attacker-supplied
bytes served from our own origin, and a file a browser decides to render as a
document would otherwise run script as this site.

**The admin URL is in neither `robots.txt` nor the sitemap** — not even as a
`Disallow`, and not as a comment. Naming it to forbid it publishes it to
whoever reads the first file an attacker fetches. Staff *routes* are a
different case: `/dashboard/`, `/auth/`, `/notifications/` and the rest are
listed, because they are guessable anyway and crawling them only burns crawl
budget on redirects to a login form. `Disallow` saves crawl budget; the
`noindex` meta tag on every private template is what controls indexing.

**No 2FA beyond the emailed code.** The code is the second factor.

## Checking

```bash
python src/manage.py check --deploy --settings=config.settings.production
```

With a production-shaped environment this reports no issues. Run it before
every deploy — it catches a `DEBUG=True` or a weak `SECRET_KEY` that reached
the server.
