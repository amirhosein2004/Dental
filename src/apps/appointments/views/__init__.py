"""
Views for the appointments app.

`booking_view` is what a patient uses — the weekly board and the booking form,
both public and both rate-limited. `manage_view` is the clinic side: editing
the recurring slot template, and cancelling this week's bookings. `common`
holds the week/slot queries both need.
"""
