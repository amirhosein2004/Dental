"""
Fill in the slugs, then make them unique.

Separate from the migration that added the column, because a unique index
cannot be built over a table where every row still holds the same empty
default.
"""
from django.db import migrations, models
from django.utils.text import slugify


def fill_slugs(apps, schema_editor):
    """
    One slug per doctor, from the doctor's own name.

    `allow_unicode` keeps the Persian: these URLs are meant to match what a
    patient types into a search box, and transliterating the names would
    defeat the reason the pages exist.
    """
    Doctor = apps.get_model('dashboard', 'Doctor')
    seen = set()

    for doctor in Doctor.objects.select_related('user').all():
        if doctor.slug:
            seen.add(doctor.slug)
            continue

        user = doctor.user
        name = f'{user.first_name} {user.last_name}'.strip() if user else ''
        base = slugify(name, allow_unicode=True) or f'doctor-{doctor.pk}'

        slug, n = base, 2
        while slug in seen:
            slug = f'{base}-{n}'
            n += 1

        seen.add(slug)
        doctor.slug = slug
        doctor.save(update_fields=['slug'])


def noop(apps, schema_editor):
    """Reversing only drops the constraint; the values are harmless to keep."""


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0003_alter_doctor_options_doctor_branches_and_more'),
    ]

    operations = [
        migrations.RunPython(fill_slugs, noop),
        migrations.AlterField(
            model_name='doctor',
            name='slug',
            field=models.SlugField(allow_unicode=True, blank=True, help_text='خالی بگذارید تا از نام و نام خانوادگی ساخته شود', max_length=200, unique=True, verbose_name='نشانی صفحه'),
        ),
    ]
