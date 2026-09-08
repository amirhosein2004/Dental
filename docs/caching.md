# Caching

Public pages are cached for a day. That is only safe because every write that
could change a page bumps that page's cache group — and when it does not, the
failure is silent: the site serves yesterday's content with nothing in the
logs to say why.

## How it works

Each cached page belongs to a **group**. A group has a version integer in
Redis, and that version is part of every key derived from it. Bumping the
version orphans every entry in the group at once; the orphans expire on their
own TTL.

Version bumping rather than pattern deletion because Django's Redis backend
cannot delete by pattern.

```python
# reading                                   # invalidating
key = get_cache_key(                        invalidate_group('gallery')
    request, cache_view='galleryview',
    group='gallery', public=True,
    vary_on=('category',),
)
```

## `vary_on` is a security control, not tidiness

The key includes only the query parameters named in `vary_on`. Everything else
in the query string is ignored.

This used to append `request.GET.urlencode()` wholesale, so `/blog/?x=1`,
`?x=2`, … each minted a distinct entry held for a day. A few minutes of
requesting a public page with a counter in the query string would fill Redis
with entries nobody will ever read, and the eviction that follows takes the
real cache with it.

Unknown parameters change nothing about the response — django-filter ignores
them — so they must not change the key either.

## What is cached

| Page | Group | TTL | Level |
|---|---|---|---|
| home | `home` | 24h | data |
| about | `about` | 24h | data |
| service list, service detail | `service` | 24h | data |
| doctor roster, doctor CV page | `doctors` | 24h | data |
| blog list | `blog` | 24h | **whole response** |
| gallery list | `gallery` | 24h | **whole response** |
| pricing | `pricing` | 1h | **whole response** |

Three caches sit outside the group scheme, because they are read on *every*
page rather than by one view. They have their own keys and their own
`invalidate_…()` function, and the signals call both:

| | Key | TTL | Cleared by |
|---|---|---|---|
| clinic info + branches (footer) | `about_info_v2` | 6h | `About`, `Branch` writes |
| doctor roster (footer) | `clinic_doctors_v1` | 6h | `Doctor` writes |
| services in the site-wide JSON-LD | `ld_services_v1` | 6h | `Service` writes |

Bumping a view group alone would not touch these: a deleted service would keep
appearing in the structured data of every page, and a renamed practice in the
footer of every cached one, until the entry expired on its own.

**The "Level" column is the difference that matters.** A *data* cache holds
the querysets and the template is rendered per request, so the page always
carries the right navigation for whoever asked. A *whole response* cache holds
the rendered `HttpResponse`.

**So the response-level pages skip the cache for anyone signed in** —
`if request.user.is_authenticated: return render_page()`, before the key is
even built. The stored copy was rendered for an anonymous visitor and its HTML
carries no management controls; serving it to a doctor would hide their own
dashboard link and their edit buttons. Two tests pin this in both directions.

`public=True` says the same thing from the other side: the key drops its
per-user segment, so there is one entry for the whole world rather than one
per visitor. It is only correct *because* of the bypass above.

## What invalidates what

The map is `apps/core/signals.py`, wired to `post_save` and `post_delete`:

| Model | Bumps |
|---|---|
| `Service` | home, about, service, doctors *(+ the JSON-LD cache)* |
| `ServiceFAQ` | service |
| `BlogPost` | home, blog |
| `Gallery` | home, gallery |
| `Image` | home, gallery |
| `PricingItem`, `PricingCategory` | pricing |
| `Doctor` | home, about, gallery, doctors |
| `CustomUser` | home, about, gallery, doctors |
| `Category` | blog, gallery |
| `Branch` | home, about, contact, service, doctors |

`About` and `Branch` are also wired in `apps/about/signals.py`, which is where
the footer's own cache is cleared. `About` bumps home, about and contact;
`Branch` appears in both files because it feeds the view groups *and* the
footer.

Why some of the less obvious edges exist:

- **`Service` → `doctors`.** A CV page lists the treatments that doctor
  performs, by title, so renaming a service changes those pages too.
- **`Branch` → `service`, `doctors`.** Address and phone differ per practice
  and are rendered on the CV pages and inside the `LocalBusiness` JSON-LD the
  service pages carry.

Two of those were found missing by tests and added:

- **`Image` → `home`.** The home page renders up to three images per gallery
  tile, so adding one to an existing gallery changes it. `Image` used to bump
  only `gallery`.
- **`CustomUser` → home, about.** A doctor's name and photo live on the user
  row, not on `Doctor`. Editing a profile through the dashboard writes here.

`apps/core/tests/test_cache_invalidation.py` warms each page, writes something that
should change it, and asks again. Add a test there whenever a model starts
appearing on a cached page.

## Redis holds four things

Cache, rate-limit counters, the login throttle, and the Celery queue.

Configured `allkeys-lru` with no persistence. A full instance evicts cold
cache entries rather than refusing writes — which would take the site down,
since the response cache sits on the request path. Losing it all on restart
costs a cold cache and nothing else.

## Gotchas

**LocMemCache is per-process.** In develop without containers, `cache.clear()`
from a shell does *not* clear the running server's cache. Restart it.

**Static files are not in this cache.** They are content-hashed by
`ManifestStaticFilesStorage` in production, so a changed file has a
changed URL and there is nothing to invalidate. In develop they are served
straight from the source tree, which is why a hard refresh is sometimes needed
after pulling.
