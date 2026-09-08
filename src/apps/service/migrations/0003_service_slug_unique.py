"""
Fill in the service slugs, then make them unique. See the dashboard migration
of the same shape for why this is two steps.
"""
from django.db import migrations, models
from django.utils.text import slugify


def fill_slugs(apps, schema_editor):
    Service = apps.get_model('service', 'Service')
    seen = set()

    for service in Service.objects.all():
        if service.slug:
            seen.add(service.slug)
            continue

        base = slugify(service.title, allow_unicode=True) or f'service-{service.pk}'

        slug, n = base, 2
        while slug in seen:
            slug = f'{base}-{n}'
            n += 1

        seen.add(slug)
        service.slug = slug
        service.save(update_fields=['slug'])


def noop(apps, schema_editor):
    """Reversing only drops the constraint; the values are harmless to keep."""


class Migration(migrations.Migration):

    dependencies = [
        ('service', '0002_alter_service_options_service_content_and_more'),
    ]

    operations = [
        migrations.RunPython(fill_slugs, noop),
        migrations.AlterField(
            model_name='service',
            name='slug',
            field=models.SlugField(allow_unicode=True, blank=True, help_text='خالی بگذارید تا از عنوان ساخته شود', max_length=200, unique=True, verbose_name='نشانی صفحه'),
        ),
    ]
