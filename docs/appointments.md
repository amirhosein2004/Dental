# Booking

Patients book without an account. There is no patient login, no password, no
"my appointments" page — a name, a national code and a phone number, and the
clinic calls back. That constraint shapes everything below: the system cannot
identify who is asking, so it never lets the browser decide anything that
matters.

## The week is the whole design

A doctor does not publish dates. They publish a **weekly template**:

```
AvailabilitySlot   doctor · branch · weekday (0 = Saturday) · time · is_active
Appointment        slot · week_start · patient details · status
```

`AvailabilitySlot` is "Dr Babaei, Mashhad, Saturday, 20:00". It has no date and
never expires. `Appointment` is one patient's claim on one slot **for one
week**, stamped with `week_start` — the Saturday that opens that week.

That stamp is the entire expiry mechanism. When the week turns over, the new
`current_week_start()` no longer matches last week's bookings, so every slot is
free again. Nothing generates future rows and nothing cleans up past ones:
there is no cron job here to forget to install, and no window in which the
board shows a slot that a cleanup job has not reached yet.

The alternative — materialising dates months ahead — needs a job to top the
calendar up, a job to expire it, and an answer for what happens when either
misses a run. The clinic's schedule is genuinely the same every week, so the
data says so.

`weeks.py` owns every conversion. **Saturday is 0**, following the Iranian
week; Python's `date.weekday()` starts on Monday, so `to_py_weekday` /
`from_py_weekday` sit between them. Do the arithmetic there, never at a call
site — an off-by-one in this file is a booking on the wrong day.

## Who may take a slot

Two guards, and the second is the one that actually holds.

```python
# advisory
if slot.has_passed(week) or slot.booking_for(week): ...refuse

# authoritative
UniqueConstraint(fields=['slot', 'week_start'],
                 condition=Q(status='booked'))
```

Two visitors submitting the same slot in the same second both pass the read.
The database is the arbiter: the loser gets `IntegrityError`, which the view
turns into "someone just took this one" and a redirect back to the board. A
"check, then write" that trusts the check is the classic double-booking bug,
and here it means two patients in the chair at once.

The constraint is **partial** — `condition=Q(status='booked')` — which is why
cancelling is a status change rather than a delete: the slot reopens
immediately, and the record of who had held it survives for the front desk.

Two more things the browser is never allowed to say:

* **the slot and the week** come from the view, not the form. `AppointmentForm`
  carries only patient fields, so a tampered POST cannot book an inactive slot
  or reserve a week in the future.
* **`Appointment.clean()` refuses any week but the current one**, so a stale
  tab left open over the weekend fails loudly instead of booking the past.

`has_passed` compares against local time, not the date alone. Without it,
Saturday 09:00 was still bookable on Saturday afternoon.

## The board

`/appointments/` renders the live week **grouped by practice**, not as one flat
list. The clinic has two locations in different cities, and "Sunday 18:00 —
Dr X" does not say which — a patient in Quchan booked Mashhad and found out on
arrival. Grouping answers that before the click.

Booked and expired slots stay on the board, greyed rather than hidden: a week
with three openings and nothing else looks like a clinic that barely operates,
and a visitor cannot tell "nothing left" from "nothing offered".

Slots whose `branch` is null — rows from before the field existed — collect
under a final unnamed group rather than being dropped. Dropping them would take
a real, bookable opening off the board.

## The clinic side

| Route | Who | Does |
|---|---|---|
| `appointments:manage` | doctor / superuser | add and list recurring slots |
| `appointments:delete_slot` | owner / superuser | remove one |
| `appointments:list` | doctor / superuser | this week's bookings |
| `appointments:cancel` | owner / superuser | free a slot, keep the record |

A doctor sees only their own template and their own bookings; a superuser sees
everyone's. That is `user_owns` again — the same rule as the rest of the staff
side — and a slot belonging to someone else answers **404**, not 403.

On the staff form the `doctor` field is fixed to the signed-in doctor and
rendered hidden, so a crafted POST cannot put a slot in a colleague's schedule.
The branch list narrows to the practices that doctor works at, unless none are
recorded — narrowing to an empty list would leave them unable to add anything.

`branch` is required on the form while the column stays nullable. Nullable is
for the old rows; required is because a patient has to be told which city they
are booking.

## What a booking sets off

An SMS alert to the clinic's configured numbers, queued through Celery as
`NotificationLog.Kind.APPOINTMENT`:

```
نوبت جدید
<name> — <phone>
<weekday> <jalali date> ساعت <time>
پزشک: … / مطب: …
```

Queued, and a queueing failure is logged and swallowed — the booking is already
committed, and a broker hiccup must not look to the patient like a failed
submit. No web push on this path; contact messages get both. See
[notifications.md](notifications.md).

## Limits and validation

* **6 bookings per minute per IP** (`rate_limit = '6/m'`). The form collects a
  national code and a phone number; an unthrottled endpoint is a comfortable
  way to fill the whole week with fictitious patients.
* **National code is checksum-validated**, repdigits included — they pass the
  checksum by coincidence.
* **Phone is 11 digits starting with 0.** A patient reporting the form "rejects
  them" is usually a `+98` prefix.

There is no captcha here, unlike the contact form. The rate limit plus a
one-slot-per-week constraint bounds the damage a script can do to the schedule;
a captcha on the way to booking a dentist costs more bookings than it saves.

## Dates on screen

Stored Gregorian, displayed Jalali — `Appointment.jalali_date` via `jdatetime`.
Never format a date for a patient-facing screen straight from the ORM value.
