"""
Things whose job is to stop an attack.

Grouped because they are read together: when someone asks "how does login
resist guessing" or "can a blog post run script", the answer is in this
package and nowhere else.

* `login_throttle` + `auth_backends` — refuse repeated failed logins
* `sessions` — the signed token that carries a half-finished login
* `sanitize` — strip anything executable from rich text before it is stored
* `math_captcha` — the self-hosted challenge on public forms
"""
