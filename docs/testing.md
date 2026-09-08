# Testing

```bash
python src/manage.py test                                        # everything, ~500 tests in ~7s
python src/manage.py test apps.contact                           # one app
python src/manage.py test apps.contact.tests.test_form.ContactFormTests
```

The label is `apps.contact`, not `contact`: it is a Python path, and the apps
moved into a package. (The *app label* is still plain `contact` — that is what
migrations and `AUTH_USER_MODEL` use, and it did not change.)

Run from the repository root or from inside `src`; both work. Discovery starts
at `src/` either way, set by the runner — Django's default of "the working
directory" would find nothing from the root and report `Ran 0 tests` as a
success.

No `--settings` flag: `DJANGO_ENV` defaults to `develop`, and test-time
configuration comes from the runner instead of a settings module.

## The runner

`utils/test_runner.py`, named by `TEST_RUNNER` in `base.py`. It overrides four
things, each load-bearing:

| Override | Without it |
|---|---|
| rate limiting off | a test calling one view ten times gets a 429 |
| MD5 password hashing | PBKDF2 at 600k iterations dominates the runtime — 25s against 6s |
| local-memory cache | tests need a live Redis |
| Celery inline | tests need a live broker and worker |

Media goes to a temp directory that is deleted afterwards.

This used to be a `settings/test.py`. It was never a place to deploy, and
sitting beside the three real environments it read like a fourth.

## Layout

Every app has a `tests/` package; files are named for what they cover.

```
src/apps/contact/tests/test_form.py            the public form
src/apps/contact/tests/test_messages_view.py   the staff inbox
src/utils/tests/test_sessions.py          the signed OTP token
src/apps/core/tests/test_cache_invalidation.py what busts which cache group
src/apps/core/tests/test_hygiene.py            repo-wide checks
```

## What is worth testing here

Bias toward **what breaks silently**. A crash gets reported; a stale page, an
unsent alert, or a permission that stopped being checked does not.

The tests that have caught real bugs in this project:

- **cache invalidation** — found two models that changed a page without
  busting it
- **the OTP flow** — found that adding a second auth backend made `login()`
  raise, so every completed login was a 500
- **`[hidden]` enforcement** — found that dropping Bootstrap broke the
  "you've seen everything" notes
- **external assets** — stops a CDN link creeping back in

## Writing them

**Assert the invariant, not today's value.** A test that asserts
`debug_toolbar` is absent breaks when run under develop settings; one that
asserts *presence follows `DEBUG`* is right in every environment.

**Mock where the name is looked up, not where it is defined.**
`patch('notifications.views.sms_view.send_bulk_sms_task.delay')`, not
`patch('notifications.tasks...')`. Get this wrong and the test still passes —
it just stops intercepting anything. Two rounds of moving files into packages
broke exactly this, silently.

**A test that cannot fail is worse than no test**, because the suite reports it
as green. When you write one for a security control, break the control on
purpose once and confirm it goes red. The session-token tests were checked
this way: disabling the signature check turns five of them red.

**Empty scaffolding beats `pass` stubs.** Where a file exists with no tests
yet, it holds a checklist in its docstring rather than passing placeholders.

## Coverage

```bash
pip install coverage
coverage run --source=. --omit="*/venv/*,*/migrations/*,*/tests/*" manage.py test
coverage report --skip-empty --sort=cover
```

Around 85%. The number is less useful than *where* the gaps are — the sorted
report puts the weakest files first.
