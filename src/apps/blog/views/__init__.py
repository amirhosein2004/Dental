"""
Views for the blog app.

`public_view` is the cached list, its "load more" endpoint and the article
page. `manage_view` is authoring, behind the ownership rule that a doctor may
edit only their own posts. `common` holds the queryset and paging helpers both
need, so neither has to import the other.
"""
