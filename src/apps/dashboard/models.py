from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from utils.data.validators import validate_length


User = get_user_model()

class Doctor(models.Model):
    """
    A doctor's public profile — and the page most of this site's real traffic
    is looking for.

    Visitors search the doctors by name far more than they search "dentist in
    Mashhad". Until this model grew the fields below there was no page on the
    site carrying a full name at all (every template said only "دکتر بابایی و
    بهمدی"), so a search for a full name found the aggregator directories
    instead of the practice's own site.

    The CV-shaped fields are not decoration either. Dentistry is a YMYL topic,
    where Google weighs demonstrated expertise and credentials — so the degree,
    the council registration number and the education history are ranking
    input, not just page furniture.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        help_text="The user associated with this doctor."
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        blank=True,
        # Persian names slugify to Persian text; the ASCII-only default
        # validator would reject every real profile on this site.
        allow_unicode=True,
        verbose_name="نشانی صفحه",
        help_text="خالی بگذارید تا از نام و نام خانوادگی ساخته شود",
    )
    description = models.TextField(
        default="توضیحات پزشک هنوز ثبت نشده است",
        validators=[validate_length],
        verbose_name="معرفی",
    )
    headline = models.CharField(
        max_length=180,
        blank=True,
        default='',
        verbose_name="عنوان کوتاه",
        help_text="یک خط زیر نام، مثلاً: دندانپزشک، متخصص ایمپلنت و زیبایی",
    )
    specialty = models.CharField(
        max_length=120,
        blank=True,
        default='',
        verbose_name="تخصص",
        help_text="مثلاً: ایمپلنت و جراحی دهان و دندان",
    )
    degree = models.CharField(
        max_length=120,
        blank=True,
        default='',
        verbose_name="مدرک تحصیلی",
        help_text="مثلاً: دکترای حرفه‌ای دندانپزشکی",
    )
    # Shown on the page and emitted in the Physician JSON-LD. A verifiable
    # registration number is the strongest trust signal a medical page has.
    license_number = models.CharField(
        max_length=30,
        blank=True,
        default='',
        verbose_name="شماره نظام پزشکی",
    )
    experience_years = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="سال‌های تجربه",
    )
    education = models.TextField(
        blank=True,
        default='',
        verbose_name="تحصیلات",
        help_text="هر مورد در یک خط، مثلاً: دکترای دندانپزشکی — دانشگاه علوم پزشکی مشهد، ۱۳۹۲",
    )
    experience = models.TextField(
        blank=True,
        default='',
        verbose_name="سوابق کاری",
        help_text="هر مورد در یک خط",
    )
    certifications = models.TextField(
        blank=True,
        default='',
        verbose_name="دوره‌ها و گواهی‌نامه‌ها",
        help_text="هر مورد در یک خط",
    )
    memberships = models.TextField(
        blank=True,
        default='',
        verbose_name="عضویت‌ها",
        help_text="هر مورد در یک خط، مثلاً: عضو انجمن دندانپزشکی ایران",
    )
    services = models.ManyToManyField(
        'service.Service',
        blank=True,
        related_name='doctors',
        verbose_name="خدمات تخصصی",
    )
    branches = models.ManyToManyField(
        'about.Branch',
        blank=True,
        related_name='doctors',
        verbose_name="مطب‌های محل کار",
    )
    is_published = models.BooleanField(
        default=True,
        verbose_name="نمایش صفحه عمومی",
        help_text="اگر خاموش باشد صفحه‌ی رزومه ۴۰۴ می‌دهد و از sitemap حذف می‌شود",
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="ترتیب نمایش",
    )
    meta_description = models.CharField(
        max_length=300,
        blank=True,
        default='',
        verbose_name="توضیح متا",
        help_text="خالی بگذارید تا از عنوان کوتاه و تخصص ساخته شود",
    )
    twitter = models.URLField(max_length=200, blank=True, default='')
    instagram = models.URLField(max_length=200, blank=True, default='')
    telegram = models.URLField(max_length=200, blank=True, default='')
    linkedin = models.URLField(max_length=200, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-updated_at']
        verbose_name = "پزشک"
        verbose_name_plural = "پزشکان"

    def save(self, *args, **kwargs):
        """
        Override the save method to perform full_clean before saving.
        """
        if not self.slug:
            self.slug = self._build_slug()

        self.full_clean()
        super().save(*args, **kwargs)

    def _build_slug(self):
        """
        Slug from the doctor's own name, with a numeric suffix on collision.

        `allow_unicode` keeps the Persian, which is what visitors actually
        type and what a search engine matches the query against.
        """
        base = slugify(self.full_name, allow_unicode=True) or f'doctor-{self.user_id}'
        slug, n = base, 2
        while Doctor.objects.exclude(pk=self.pk).filter(slug=slug).exists():
            slug = f'{base}-{n}'
            n += 1
        return slug

    def __str__(self):
        if self.user:
            full_name = self.user.get_full_name.strip()
            return full_name if full_name else "نام پزشک مشخص نیست"
        return "بدون نام"

    def get_absolute_url(self):
        return reverse('doctors:doctor_detail', kwargs={'slug': self.slug})

    @property
    def full_name(self):
        """Bare name, no honorific — callers add "دکتر" where it reads right."""
        if not self.user:
            return ''
        return self.user.get_full_name.strip() or self.user.username

    @property
    def display_name(self):
        """The form used in headings, titles and structured data."""
        name = self.full_name
        return f"دکتر {name}" if name else "پزشک"

    @property
    def seo_description(self):
        """
        Falls back through the fields most likely to be filled, so a profile
        never ships with an empty meta description — an empty one lets Google
        invent its own snippet from whatever text it finds first.
        """
        if self.meta_description:
            return self.meta_description
        parts = [self.display_name]
        if self.headline:
            parts.append(self.headline)
        elif self.specialty:
            parts.append(self.specialty)
        parts.append('نوبت‌دهی آنلاین، رزومه، سوابق و خدمات تخصصی.')
        return ' — '.join(parts)

    @property
    def education_list(self):
        return [line.strip() for line in self.education.splitlines() if line.strip()]

    @property
    def experience_list(self):
        return [line.strip() for line in self.experience.splitlines() if line.strip()]

    @property
    def certification_list(self):
        return [line.strip() for line in self.certifications.splitlines() if line.strip()]

    @property
    def membership_list(self):
        return [line.strip() for line in self.memberships.splitlines() if line.strip()]

    @property
    def social_links(self):
        """(url, icon class, label) for every social field that is set."""
        pairs = (
            (self.instagram, 'fab fa-instagram', 'اینستاگرام'),
            (self.telegram, 'fab fa-telegram-plane', 'تلگرام'),
            (self.twitter, 'fab fa-x-twitter', 'ایکس'),
            (self.linkedin, 'fab fa-linkedin-in', 'لینکدین'),
        )
        return [(url, icon, label) for url, icon, label in pairs if url]
