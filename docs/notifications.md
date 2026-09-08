# Notifications

Two channels, for two different jobs.

| | Cost | Reaches | Needs |
|---|---|---|---|
| **Web push** | free | staff devices that opted in | nothing on iOS but an installed PWA |
| **SMS** | per message | any phone | a Kavenegar account and credit |

What triggers what:

| Event | SMS to `STAFF_ALERT_NUMBERS` | Push to subscribed staff devices |
|---|---|---|
| contact message | yes | yes |
| new booking | yes | no |
| staff bulk campaign | yes, to the pasted list | — |

The two alert paths are queued separately, so one broker hiccup cannot swallow
both, and a queueing failure is logged and swallowed either way: the message or
the booking is already saved, and a failed alert must not look to the visitor
like a failed submit.

The alert task is **retried** (3 attempts, backoff); the bulk task is never
retried, for the reason under [Spend guards](#spend-guards). The push task gets
two attempts — a push costs nothing and its `tag` makes a repeat replace the
banner already in the tray rather than adding a second one.

Every send writes a `NotificationLog` row, tagged with its kind
(`CONTACT_MESSAGE`, `APPOINTMENT`, `BULK`), before the provider is called.

With no `STAFF_ALERT_NUMBERS` configured, `notify_staff` no-ops — and still
writes the log row, so a silent clinic is visible rather than invisible.

## Web push

Staff turn it on themselves from `/contact/messages/`. The browser hands back
an endpoint and two keys; those become a `PushSubscription` row.

**One row per browser, not per person.** A doctor with a phone and a laptop
has two rows and both ring.

**Three layers decide who receives one:**

1. the button only exists on a staff page
2. the subscribe endpoint is staff-gated — a direct call gets 404
3. **the send path re-checks** `is_active` and `is_doctor or is_superuser`

The third exists because the first two are decisions made *once*, and the row
outlives them. Without it, a doctor who left the clinic would keep receiving
patients' names on their phone forever.

Patients never receive anything, and there is no setting that would let them.

### iPhone

Safari exposes the Push API **only** to a site added to the Home Screen and
launched from there. In a normal tab `PushManager` does not exist.

This is why the site is an installable PWA at all: `/manifest.webmanifest`
with `display: standalone`, plus the Apple meta tags for older iOS. Both are
needed — having only one is the usual reason an installed icon still opens in
a browser view.

The panel detects an iPhone in a plain tab and shows the Share → Add to Home
Screen instructions rather than "your browser is not supported", which would
be both wrong and a dead end.

Deleting the Home Screen icon drops the subscription. The server notices: a
410 from the push service deletes the row rather than retrying forever.

### Keys

```bash
python src/manage.py generate_vapid_keys
```

Set once per environment. Rotating them silently unsubscribes every device.
Stage must have its own pair, or a test fires notifications at phones that
subscribed on the live site.

## SMS

`SMS_BACKEND=console` logs instead of sending, and is the default everywhere
except production. Stage forces it regardless of what its env file says.

**Kavenegar**, 200 recipients per API call, batched automatically.

### Spend guards

- **500 recipients maximum** per bulk send.
- **The bulk task is never retried.** `send_sms` handles provider failure
  itself, so the only way the task raises is after some batches already went
  out — a retry would re-send them, billed again.
- Every send is written to `NotificationLog` before the provider is called, so
  a crash mid-send still leaves a trace.

### Persian text

70 characters per SMS part, 67 when concatenated — UCS-2, not GSM-7. A long
Persian message costs several messages per recipient. The compose box shows
the count.

### Rules worth knowing

Advertising SMS in Iran is regulated. Unlicensed medical claims get the panel
and the number blocked. Opt-out text is mandatory; recipients who opt out have
the cost refunded.

Advertising and service lines are separate; converting a line from advertising
to service is only possible for a registered legal entity.
