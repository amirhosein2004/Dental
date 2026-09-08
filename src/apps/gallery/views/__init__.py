"""
Gallery views, split by who they serve.

`public_view` is what a visitor sees — the masonry list and its "load more"
endpoint, both cached. `manage_view` is the staff side: creating a gallery,
adding and removing images, deleting the whole thing. `common` holds the two
things both need, so neither imports the other.
"""
