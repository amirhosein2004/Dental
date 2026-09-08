"""
Server-side HTML sanitising for rich-text content.

Blog bodies are rendered with ``{{ blog.content|safe }}`` — they have to be,
or the editor's markup would show as escaped text. That makes the stored value
executable, so it must be cleaned on the way *in*.

The CKEditor config in settings lists ``script``/``iframe``/``style`` under
``htmlSupport.disallow``, but that is editor configuration: it shapes what the
editor will produce, not what the server will accept. Anyone who posts
straight to the create/update endpoint — or who gets hold of one doctor's
account — bypasses it entirely. This module is the check that actually runs.

Kept deliberately close to the editor's own toolbar: every tag the toolbar can
produce is allowed, nothing else is.
"""
import nh3

# Mirrors the toolbar in ``CKEDITOR_5_CONFIGS['extends']`` plus the tags its
# `htmlSupport.allow` list names. Anything absent is stripped, tag and all.
ALLOWED_TAGS = {
    'p', 'br', 'span', 'div',
    'b', 'strong', 'i', 'em', 'u', 's', 'strike', 'sub', 'sup', 'mark',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li',
    'blockquote', 'pre', 'code',
    'a', 'img', 'figure', 'figcaption',
    'table', 'thead', 'tbody', 'tfoot', 'tr', 'td', 'th', 'caption',
    'hr',
}

ALLOWED_ATTRIBUTES = {
    # `rel` is deliberately absent: it is set by `link_rel` below, and nh3
    # refuses to do both (an author-supplied rel could otherwise undo it).
    'a': {'href', 'title', 'target'},
    'img': {'src', 'alt', 'title', 'width', 'height'},
    'td': {'colspan', 'rowspan'},
    'th': {'colspan', 'rowspan', 'scope'},
    # CKEditor writes alignment and colour as inline styles. `style` is *not*
    # allowed: it carries `expression()`/`url(javascript:)` in older engines
    # and is the usual way to hide a click-jacking overlay. Alignment classes
    # survive instead.
    '*': {'class', 'dir'},
}

# Only these may appear in an href/src. `javascript:` and `data:` are the two
# that turn a link or an image into script execution.
ALLOWED_URL_SCHEMES = {'http', 'https', 'mailto', 'tel'}


def sanitize_html(value):
    """
    Return `value` with every tag, attribute and URL scheme outside the
    allow-lists removed. Empty input passes through unchanged.

    ``link_rel`` forces ``rel="noopener noreferrer"`` onto links so a post that
    opens in a new tab cannot reach back through ``window.opener``.
    """
    if not value:
        return value

    return nh3.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes={k: set(v) for k, v in ALLOWED_ATTRIBUTES.items()},
        url_schemes=ALLOWED_URL_SCHEMES,
        link_rel='noopener noreferrer',
    )
