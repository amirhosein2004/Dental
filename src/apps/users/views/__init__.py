"""
Views for the users app.

Empty on purpose. The custom user model lives here, but every screen that
touches it belongs to another app: signing in is `accounts`, editing a profile
is `dashboard`. The package exists so that if a user-facing screen ever does
land here, it has somewhere to go that matches every other app.
"""
