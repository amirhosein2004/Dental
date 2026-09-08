"""
Views for the contact app.

`contact_view` is the public form — the only place on the site an anonymous
visitor can write to the database. `messages_view` is the staff inbox behind
it. They are kept apart because the public one carries the captcha, honeypot
and rate limit, and the staff one carries none of that and must not look like
it does.
"""
