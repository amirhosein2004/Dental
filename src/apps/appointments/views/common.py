"""Week and slot queries shared by the public board and the staff screens."""
from ..models import Appointment, AvailabilitySlot
from ..weeks import WEEKDAYS, slot_date


def _booked_slot_ids(week_start):
    return set(
        Appointment.objects
        .filter(week_start=week_start, status=Appointment.Status.BOOKED)
        .values_list('slot_id', flat=True)
    )


def _week_board(week_start):
    """
    Public schedule: active slots grouped by weekday, each tagged with whether
    it is still bookable this week.

    Booked and expired slots are shown rather than hidden so a visitor sees the
    real shape of the week instead of an inexplicably sparse list.
    """
    slots = (
        AvailabilitySlot.objects
        .filter(is_active=True)
        .select_related('doctor__user', 'branch')
    )
    taken = _booked_slot_ids(week_start)

    board = []
    for weekday, label in WEEKDAYS:
        entries = []
        for slot in slots:
            if slot.weekday != weekday:
                continue
            passed = slot.has_passed(week_start)
            entries.append({
                'slot': slot,
                'is_taken': slot.pk in taken,
                'has_passed': passed,
                'is_open': slot.pk not in taken and not passed,
            })
        if entries:
            board.append({
                'weekday': weekday,
                'label': label,
                'date': slot_date(week_start, weekday),
                'entries': entries,
            })
    return board


def _branch_boards(week_start):
    """
    The public schedule split by practice.

    A flat week was ambiguous the moment the clinic had two locations: "Sunday
    18:00 — Dr X" does not say which city, and a patient in Quchan had no way
    to tell a Mashhad slot from a local one until they arrived. Grouping by
    branch answers that before the patient clicks rather than after.

    Slots with no branch (rows created before the field existed) are collected
    under a final ``None`` group rather than dropped — hiding them would take
    a real, bookable opening off the board.
    """
    slots = (
        AvailabilitySlot.objects
        .filter(is_active=True)
        .select_related('doctor__user', 'branch')
    )
    taken = _booked_slot_ids(week_start)

    # Preserve Branch.Meta.ordering (primary first, then `order`, then city),
    # which a `set` of branches would not.
    groups, seen = [], {}
    for slot in slots.order_by('branch__order', 'branch__city'):
        key = slot.branch_id
        if key not in seen:
            seen[key] = {'branch': slot.branch, 'days': {}}
            groups.append(seen[key])

    for group in groups:
        for weekday, label in WEEKDAYS:
            entries = []
            for slot in slots:
                if slot.weekday != weekday or slot.branch_id != (
                    group['branch'].pk if group['branch'] else None
                ):
                    continue
                passed = slot.has_passed(week_start)
                entries.append({
                    'slot': slot,
                    'is_taken': slot.pk in taken,
                    'has_passed': passed,
                    'is_open': slot.pk not in taken and not passed,
                })
            if entries:
                group['days'][weekday] = {
                    'weekday': weekday,
                    'label': label,
                    'date': slot_date(week_start, weekday),
                    'entries': entries,
                }

    # `days` is built as a dict to keep the lookup above cheap; templates want
    # a list, and one that is still in weekday order.
    return [
        {
            'branch': g['branch'],
            'board': [g['days'][wd] for wd, _ in WEEKDAYS if wd in g['days']],
            'open_count': sum(
                1
                for day in g['days'].values()
                for entry in day['entries']
                if entry['is_open']
            ),
        }
        for g in groups
        if g['days']
    ]
