from django.db import models

from utils.data.validators import validate_phone, validate_image, validate_length


class About(models.Model):
    """
    Singleton — the brand, not a location.

    Address, phone and opening hours used to live here too, which meant the
    site could only ever describe one place. They now live on ``Branch``, one
    row per practice, and this model keeps only what is true of the practice
    as a whole: its name, its email, the blurb and the logo. The "درباره ما"
    page is about the people and the practice, not a second copy of the
    contact details already in the footer.
    """
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254)
    description = models.TextField(validators=[validate_length])
    image = models.ImageField(upload_to='about', validators=[validate_image])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "درباره ما"
        verbose_name_plural = "درباره ما"

    def save(self, *args, **kwargs):
        # Reuse the existing row's PK so callers can freely construct a new
        # instance without accidentally duplicating.
        existing_pk = self.__class__.objects.values_list('pk', flat=True).first()
        if existing_pk is not None and self.pk is None:
            self.pk = existing_pk

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @classmethod
    def get_solo(cls):
        return cls.objects.first()


class Branch(models.Model):
    """
    One physical practice. Two rows today — مشهد and قوچان.

    Deliberately has no URL of its own. Separate pages per city were
    considered and rejected: with two locations and one shared price list,
    per-city pages would have been the same copy with the city swapped, which
    Google treats as a doorway page and penalises. The data still has to exist
    separately — the two practices have different addresses, different phone
    numbers and possibly different hours — so it lives in a model that the
    footer, the contact page, the doctor profiles and the LocalBusiness
    JSON-LD all read from. Model, not page.

    ``About`` stays the singleton it was: it describes the practice as a brand
    (name, blurb, logo, email). Anything that differs *between* locations
    belongs here instead.
    """
    city = models.CharField(
        max_length=60,
        unique=True,
        verbose_name="شهر",
        help_text="مثلاً: مشهد",
    )
    title = models.CharField(
        max_length=120,
        blank=True,
        default='',
        verbose_name="عنوان نمایشی",
        help_text="خالی بگذارید تا «مطب دندانپزشکی <شهر>» ساخته شود",
    )
    address = models.CharField(max_length=500, verbose_name="آدرس")
    postal_code = models.CharField(
        max_length=10,
        blank=True,
        default='',
        verbose_name="کد پستی",
    )
    phone = models.CharField(
        max_length=11,
        validators=[validate_phone],
        verbose_name="تلفن",
    )
    extra_phones = models.TextField(
        blank=True,
        default='',
        verbose_name="شماره‌های دیگر",
        help_text="هر شماره در یک خط، یا با کاما جدا کنید",
    )
    hours = models.TextField(
        blank=True,
        default='',
        verbose_name="ساعات کاری این مطب",
        help_text="هر خط یک بازه — مثلاً «شنبه تا چهارشنبه: ۹ الی ۱۳ و ۱۶ الی ۲۰»",
    )
    map_embed_url = models.URLField(
        max_length=1000,
        blank=True,
        default='',
        verbose_name="لینک embed نقشه",
        help_text="آدرس src داخل تگ iframe نقشه گوگل یا نشان",
    )
    map_link = models.URLField(
        max_length=1000,
        blank=True,
        default='',
        verbose_name="لینک مسیریابی",
        help_text="لینکی که کاربر با زدنش در نقشه مسیر می‌گیرد",
    )
    # Only used to fill `geo` in the LocalBusiness JSON-LD. Blank is fine —
    # the schema block omits the property rather than emitting a null island
    # at 0,0.
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        verbose_name="عرض جغرافیایی",
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        verbose_name="طول جغرافیایی",
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="ترتیب نمایش",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'city']
        verbose_name = "مطب"
        verbose_name_plural = "مطب‌ها"

    def save(self, *args, **kwargs):
        from apps.notifications.phones import parse_numbers

        valid, _invalid = parse_numbers(self.extra_phones)
        self.extra_phones = '\n'.join(n for n in valid if n != self.phone)

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.display_title

    @property
    def display_title(self):
        return self.title or f"مطب دندانپزشکی {self.city}"

    @property
    def extra_phone_list(self):
        return [line for line in self.extra_phones.splitlines() if line]

    @property
    def phone_list(self):
        """Every number for this location, primary first."""
        return ([self.phone] if self.phone else []) + self.extra_phone_list

    @property
    def hours_list(self):
        """
        The opening hours of *this* practice, one entry per line.

        There is no site-wide hours row any more. Two practices in two cities
        do not keep the same hours, and a single shared block meant whichever
        city it did not describe was being told the wrong thing — worse than
        being told nothing. Every surface that shows hours (footer, contact
        page, doctor profile) reads them from the branch it is already naming.
        """
        return [line.strip() for line in self.hours.splitlines() if line.strip()]

    @classmethod
    def get_primary(cls):
        """
        The branch that stands in wherever the site needs exactly one — the
        `og:` tags, a single call button. First by display order, so staff
        choose it by reordering rather than by a separate flag.
        """
        return cls.objects.first()
