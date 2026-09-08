"""
Populate the database with realistic Persian demo content so the design can be
reviewed against real data instead of empty states.

Usage:
    python manage.py seed_demo            # wipe demo content + reseed
    python manage.py seed_demo --keep     # only fill gaps, keep existing rows

Never touches auth credentials: usernames, emails, and passwords are left
alone. Doctor *profiles* (display name, bio, socials, avatar) are refreshed
because those are what the public pages actually render.
"""
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from apps.about.models import About, Branch
from apps.blog.models import BlogPost
from apps.contact.models import ContactMessage
from apps.core.models import Category
from apps.dashboard.models import Doctor
from apps.gallery.models import Gallery, Image
from apps.pricing.models import PricingCategory, PricingItem
from apps.service.models import Service, ServiceFAQ
from apps.users.models import CustomUser

from ._demo_images import make_image


# --------------------------------------------------------------------------
# Content
# --------------------------------------------------------------------------

CATEGORIES = [
    'ایمپلنت',
    'ارتودنسی',
    'زیبایی و لمینت',
    'ترمیمی و عصب‌کشی',
    'دندانپزشکی کودکان',
    'جراحی لثه',
]


# Two practices. Separate rows rather than separate *pages*: a page per city
# describing the same treatments is a doorway page, but the addresses, phone
# numbers and hours genuinely differ and are rendered in the footer of every
# page, on the contact page and inside the LocalBusiness JSON-LD.
BRANCHES = [
    {
        'city': 'مشهد',
        'address': 'مشهد، بلوار وکیل‌آباد، نبش وکیل‌آباد ۲۲، ساختمان پزشکان آرمان، طبقه سوم',
        'postal_code': '9187654321',
        'phone': '05138000000',
        'extra_phones': '05138000001',
        'hours': 'شنبه تا چهارشنبه: ۹ تا ۱۳ و ۱۶ تا ۲۰\nپنجشنبه: ۹ تا ۱۳\nجمعه: تعطیل',
        # Vakil-Abad, Mashhad. Demo coordinates — close enough that the
        # map frames the right neighbourhood, which is what makes the two
        # maps on the contact page reviewable at all.
        'latitude': '36.316500',
        'longitude': '59.526600',
        'map_link': 'https://www.google.com/maps/search/?api=1&query=36.3165,59.5266',
        'order': 1,
    },
    {
        'city': 'قوچان',
        'address': 'قوچان، خیابان گوهرشاد، بین ناصرخسرو و داوودی، ساختمان پزشکان مهر، طبقه دوم',
        'postal_code': '9471234567',
        'phone': '05147247247',
        'extra_phones': '',
        'hours': 'شنبه تا چهارشنبه: ۱۶ تا ۲۰\nپنجشنبه و جمعه: تعطیل',
        # Gowharshad street, Quchan.
        'latitude': '37.106800',
        'longitude': '58.512500',
        'map_link': 'https://www.google.com/maps/search/?api=1&query=37.1068,58.5125',
        'order': 2,
    },
]


DOCTORS = [
    {
        'first_name': 'سعیده',
        'last_name': 'بابایی',
        'description': (
            'متخصص ایمپلنت و جراحی دهان، فک و صورت با بیش از ۱۲ سال سابقه بالینی. '
            'فارغ‌التحصیل دانشگاه علوم پزشکی مشهد و عضو انجمن ایمپلنتولوژی ایران. '
            'تمرکز اصلی من روی جراحی‌های بدون درد، بازسازی استخوان و ایمپلنت‌های '
            'فوری است؛ درمانی که هم از نظر عملکرد و هم زیبایی، نتیجه‌ای طبیعی داشته باشد.'
        ),
        'headline': 'دندانپزشک، متخصص ایمپلنت و جراحی دهان و فک',
        'specialty': 'ایمپلنت و جراحی دهان، فک و صورت',
        'degree': 'دکترای تخصصی جراحی دهان، فک و صورت',
        'license_number': '۱۲۸۴۵۶',
        'experience_years': 12,
        'education': (
            'دکترای دندانپزشکی — دانشگاه علوم پزشکی مشهد، ۱۳۹۱\n'
            'تخصص جراحی دهان، فک و صورت — دانشگاه علوم پزشکی مشهد، ۱۳۹۵\n'
            'فلوشیپ ایمپلنتولوژی پیشرفته — ۱۳۹۷'
        ),
        'experience': (
            'جراح ایمپلنت، مطب دندانپزشکی دکتر بابایی و بهمدی — ۱۳۹۵ تا امروز\n'
            'دستیار جراحی، بیمارستان قائم مشهد — ۱۳۹۲ تا ۱۳۹۵'
        ),
        'certifications': (
            'دوره پیشرفته پیوند استخوان و سینوس لیفت\n'
            'دوره ایمپلنت فوری (Immediate Loading)\n'
            'دوره جراحی بدون درد با آرام‌بخشی'
        ),
        'memberships': (
            'عضو انجمن ایمپلنتولوژی ایران\n'
            'عضو جامعه دندانپزشکی ایران'
        ),
        'branches': ['مشهد', 'قوچان'],
        'instagram': 'https://instagram.com/dr.saeedebabaee',
        'telegram': 'https://t.me/sbdental',
        'linkedin': '',
        'twitter': '',
    },
    {
        'first_name': 'سجاد',
        'last_name': 'بهمدی',
        'description': (
            'متخصص ارتودنسی و ناهنجاری‌های فک و صورت، دارای بورد تخصصی از دانشگاه '
            'علوم پزشکی تهران. در درمان‌های ارتودنسی نامرئی (اینویزیلاین) و ارتودنسی '
            'کودکان فعالیت می‌کنم و باور دارم هر لبخند، طرح درمان مخصوص خودش را '
            'می‌خواهد. تا امروز بیش از ۹۰۰ بیمار دوره درمان خود را نزد من کامل کرده‌اند.'
        ),
        'headline': 'دندانپزشک، متخصص ارتودنسی',
        'specialty': 'ارتودنسی و ناهنجاری‌های فک و صورت',
        'degree': 'دکترای تخصصی ارتودنسی',
        'license_number': '۱۳۵۹۰۲',
        'experience_years': 10,
        'education': (
            'دکترای دندانپزشکی — دانشگاه علوم پزشکی تهران، ۱۳۹۲\n'
            'تخصص ارتودنسی — دانشگاه علوم پزشکی تهران، ۱۳۹۶\n'
            'بورد تخصصی ارتودنسی — ۱۳۹۶'
        ),
        'experience': (
            'ارتودنتیست، مطب دندانپزشکی دکتر بابایی و بهمدی — ۱۳۹۶ تا امروز\n'
            'بیش از ۹۰۰ دوره درمان ارتودنسی تکمیل‌شده'
        ),
        'certifications': (
            'دوره ارتودنسی نامرئی (Invisalign)\n'
            'دوره ارتودنسی پیشگیرانه کودکان'
        ),
        'memberships': 'عضو انجمن ارتودنتیست‌های ایران',
        'branches': ['مشهد'],
        'instagram': 'https://instagram.com/dr.behmadi',
        'telegram': '',
        'linkedin': 'https://www.linkedin.com/in/dr-behmadi',
        'twitter': '',
    },
    {
        'first_name': 'نگار',
        'last_name': 'رضایی',
        'description': (
            'دندانپزشک ترمیمی و زیبایی، با تمرکز ویژه روی لمینت سرامیکی، کامپوزیت '
            'ونیر و طراحی لبخند دیجیتال. همچنین درمان کودکان را با رویکرد بدون '
            'ترس و بازی‌محور انجام می‌دهم تا اولین تجربه دندانپزشکی برای کودک، '
            'خاطره خوبی باقی بماند.'
        ),
        'headline': 'دندانپزشک ترمیمی و زیبایی',
        'specialty': 'ترمیمی، زیبایی و دندانپزشکی کودکان',
        'degree': 'دکترای حرفه‌ای دندانپزشکی',
        'license_number': '۱۴۲۷۸۳',
        'experience_years': 7,
        'education': 'دکترای دندانپزشکی — دانشگاه علوم پزشکی مشهد، ۱۳۹۵',
        'experience': 'دندانپزشک ترمیمی و زیبایی، مطب دکتر بابایی و بهمدی — ۱۳۹۶ تا امروز',
        'certifications': (
            'دوره طراحی لبخند دیجیتال (DSD)\n'
            'دوره لمینت سرامیکی و ونیر کامپوزیت'
        ),
        'memberships': '',
        'branches': ['قوچان'],
        'instagram': 'https://instagram.com/dr.negar.rezaei',
        'telegram': 'https://t.me/negar_dental',
        'linkedin': '',
        'twitter': '',
    },
]


# Questions patients actually ask, attached to the treatment they are about.
# There is no site-wide FAQ page on purpose: a generic one would compete with
# these very service pages for the same queries, and answers no single search
# intent well enough to rank on its own.
#
# Keyed by the leading words of the service title, so a re-seed that reworded
# a title does not silently drop the FAQs.
SERVICE_FAQS = {
    'ایمپلنت': [
        ('کاشت ایمپلنت چقدر طول می‌کشد؟',
         'جراحی هر ایمپلنت حدود ۳۰ تا ۶۰ دقیقه است. جوش خوردن ایمپلنت با استخوان '
         'بسته به وضعیت استخوان بین سه تا شش ماه طول می‌کشد و پس از آن روکش نصب می‌شود.'),
        ('ایمپلنت درد دارد؟',
         'جراحی با بی‌حسی موضعی انجام می‌شود و در حین کار دردی احساس نمی‌کنید. '
         'ناراحتی چند روز اول با مسکن معمولی کنترل می‌شود.'),
        ('عمر ایمپلنت چقدر است؟',
         'با رعایت بهداشت و مراجعه منظم، ایمپلنت می‌تواند بیش از بیست سال دوام بیاورد.'),
    ],
    'ارتودنسی': [
        ('ارتودنسی چند وقت طول می‌کشد؟',
         'به‌طور متوسط بین ۱۲ تا ۲۴ ماه، بسته به میزان نامرتبی دندان‌ها و سن بیمار.'),
        ('ارتودنسی برای بزرگسالان هم نتیجه می‌دهد؟',
         'بله. حرکت دادن دندان در هر سنی ممکن است؛ در بزرگسالان معمولاً کمی بیشتر طول می‌کشد.'),
        ('ارتودنسی نامرئی چه تفاوتی دارد؟',
         'به‌جای سیم و براکت از پلاک‌های شفاف متحرک استفاده می‌شود که در گفت‌وگو دیده نمی‌شوند '
         'و برای غذا خوردن و مسواک زدن برداشته می‌شوند.'),
    ],
    'لمینت': [
        ('لمینت به تراش دندان نیاز دارد؟',
         'لمینت سرامیکی تراش بسیار کمی می‌خواهد؛ در برخی موارد بدون تراش هم انجام می‌شود.'),
        ('لمینت چند سال دوام دارد؟',
         'لمینت سرامیکی با مراقبت درست معمولاً ۱۰ تا ۱۵ سال دوام می‌آورد.'),
    ],
}


SERVICES = [
    (
        'ایمپلنت دندان',
        'جایگزینی دندان از دست‌رفته با پایه تیتانیومی که مستقیم در استخوان فک قرار '
        'می‌گیرد. نتیجه، دندانی است که در جویدن و ظاهر تفاوتی با دندان طبیعی ندارد. '
        'از برندهای استرومن سوئیس و دنتیوم کره استفاده می‌کنیم و کل مراحل با اسکن '
        'سه‌بعدی و طراحی دیجیتال انجام می‌شود.',
    ),
    (
        'ارتودنسی ثابت و نامرئی',
        'مرتب‌سازی دندان‌ها و اصلاح فاصله، شلوغی و ناهماهنگی فک. علاوه بر براکت‌های '
        'فلزی و سرامیکی، درمان با آلاینرهای شفاف هم انجام می‌شود؛ گزینه‌ای که در '
        'طول درمان تقریباً دیده نمی‌شود و برای بزرگسالان شاغل بسیار مناسب است.',
    ),
    (
        'لمینت و کامپوزیت ونیر',
        'اصلاح رنگ، فرم و اندازه دندان‌های جلو با روکش‌های بسیار نازک سرامیکی یا '
        'کامپوزیت. قبل از شروع، طرح لبخند شما به‌صورت دیجیتال شبیه‌سازی می‌شود تا '
        'نتیجه نهایی را پیش از تراش دندان ببینید و تأیید کنید.',
    ),
    (
        'عصب‌کشی و درمان ریشه',
        'نجات دندان‌هایی که عفونت به عصب آن‌ها رسیده است، بدون نیاز به کشیدن دندان. '
        'با میکروسکوپ دندانپزشکی و روتاری، کانال‌ها کاملاً تمیز و پر می‌شوند. اغلب '
        'درمان در یک جلسه و کاملاً بی‌حس انجام می‌شود.',
    ),
    (
        'جرم‌گیری و بلیچینگ',
        'پاک‌سازی حرفه‌ای جرم و پلاک بالای لثه و زیر لثه، همراه با پالیش نهایی. در '
        'صورت تمایل، سفید کردن دندان با ژل بلیچینگ و لایت مخصوص انجام می‌شود که '
        'معمولاً چند درجه روشن‌تر شدن رنگ دندان را در یک جلسه به همراه دارد.',
    ),
    (
        'دندانپزشکی کودکان',
        'درمان و پیشگیری مخصوص کودکان: فلوراید تراپی، فیشورسیلانت، ترمیم دندان شیری '
        'و فضانگهدار. محیط مطب و روند کار طوری طراحی شده که کودک اضطراب نگیرد و '
        'مراجعه بعدی برایش سخت نباشد.',
    ),
]

BLOG_POSTS = [
    {
        'title': 'ایمپلنت دندان چیست و چه کسانی کاندید آن هستند؟',
        'categories': ['ایمپلنت', 'جراحی لثه'],
        'content': """
<h2>ایمپلنت دقیقاً چیست؟</h2>
<p>ایمپلنت دندانی یک پایه کوچک از جنس تیتانیوم است که به‌جای ریشه دندان از
دست‌رفته، داخل استخوان فک قرار می‌گیرد. بعد از اینکه این پایه با استخوان جوش
خورد، روکش دندان روی آن بسته می‌شود. نتیجه، دندانی است که هم در جویدن و هم در
ظاهر، تفاوت محسوسی با دندان طبیعی ندارد.</p>

<h2>چه کسانی کاندید مناسبی هستند؟</h2>
<ul>
    <li>افرادی که یک یا چند دندان دائمی خود را از دست داده‌اند</li>
    <li>کسانی که از پروتز متحرک راضی نیستند و دنبال راه‌حل ثابت‌اند</li>
    <li>بیمارانی که حجم استخوان فک کافی دارند یا امکان پیوند استخوان برایشان وجود دارد</li>
    <li>افرادی که بهداشت دهان مناسبی رعایت می‌کنند</li>
</ul>

<h2>مراحل درمان</h2>
<p>در جلسه اول، عکس‌برداری سه‌بعدی (CBCT) گرفته می‌شود تا حجم و کیفیت استخوان
بررسی شود. سپس در یک جلسه کوتاه و با بی‌حسی موضعی، پایه ایمپلنت قرار می‌گیرد.
دوره جوش‌خوردگی معمولاً بین سه تا شش ماه طول می‌کشد و در پایان، روکش نهایی
ساخته و نصب می‌شود.</p>

<h2>مراقبت بعد از ایمپلنت</h2>
<p>ایمپلنت پوسیدگی نمی‌گیرد، اما لثه اطراف آن می‌تواند دچار التهاب شود. مسواک
دو بار در روز، استفاده از نخ دندان یا برس بین‌دندانی و مراجعه هر شش ماه برای
معاینه، عمر ایمپلنت را به بیش از بیست سال می‌رساند.</p>

<p>اگر مطمئن نیستید ایمپلنت برای شما مناسب است یا نه، یک جلسه مشاوره رایگان
رزرو کنید تا با بررسی شرایط دهان شما، گزینه‌های موجود را با هم مرور کنیم.</p>
""",
    },
    {
        'title': 'ارتودنسی نامرئی یا براکت فلزی؟ راهنمای انتخاب',
        'categories': ['ارتودنسی'],
        'content': """
<h2>تفاوت اصلی در کجاست؟</h2>
<p>در ارتودنسی ثابت، براکت‌ها روی دندان چسبانده می‌شوند و سیم آن‌ها را به‌مرور
جابه‌جا می‌کند. در ارتودنسی نامرئی، مجموعه‌ای از آلاینرهای شفاف در اختیار شما
قرار می‌گیرد که هر یکی دو هفته یک‌بار عوض می‌شود و دندان‌ها را قدم‌به‌قدم به
موقعیت هدف می‌رساند.</p>

<h2>ارتودنسی ثابت؛ نقاط قوت</h2>
<ul>
    <li>در موارد پیچیده و ناهنجاری‌های شدید فک، نتیجه دقیق‌تری می‌دهد</li>
    <li>هزینه معمولاً کمتر از آلاینر است</li>
    <li>نیازی به همکاری روزانه بیمار ندارد چون قابل درآوردن نیست</li>
</ul>

<h2>ارتودنسی نامرئی؛ نقاط قوت</h2>
<ul>
    <li>در طول روز تقریباً دیده نمی‌شود</li>
    <li>هنگام غذا خوردن و مسواک زدن درمی‌آید، پس بهداشت دهان راحت‌تر است</li>
    <li>زخم شدن گونه و لب که در براکت فلزی شایع است، رخ نمی‌دهد</li>
</ul>

<h2>پس کدام را انتخاب کنم؟</h2>
<p>اگر ناهنجاری شما خفیف تا متوسط است و می‌توانید متعهد شوید که آلاینر را
روزی ۲۰ تا ۲۲ ساعت در دهان نگه دارید، ارتودنسی نامرئی گزینه بسیار خوبی است.
در موارد شدیدتر یا وقتی جراحی فک هم لازم است، براکت ثابت همچنان استاندارد
طلایی محسوب می‌شود.</p>

<p>در جلسه معاینه، اسکن دیجیتال از دهان شما گرفته می‌شود و نتیجه تقریبی هر دو
روش را قبل از تصمیم‌گیری می‌بینید.</p>
""",
    },
    {
        'title': 'لمینت سرامیکی یا کامپوزیت ونیر؟ مقایسه صادقانه',
        'categories': ['زیبایی و لمینت'],
        'content': """
<h2>هر کدام چه هستند؟</h2>
<p>لمینت سرامیکی، پوسته‌ای بسیار نازک از جنس پرسلن است که در لابراتوار ساخته
و روی سطح جلویی دندان چسبانده می‌شود. کامپوزیت ونیر اما همان جلسه و مستقیماً
روی دندان توسط دندانپزشک شکل داده می‌شود.</p>

<h2>ماندگاری</h2>
<p>لمینت سرامیکی با رعایت نکات مراقبتی معمولاً ده تا پانزده سال دوام می‌آورد.
کامپوزیت ونیر بین چهار تا هفت سال ماندگاری دارد و در برابر لکه چای و قهوه
حساس‌تر است، اما ترمیم و اصلاح آن بسیار ساده‌تر و کم‌هزینه‌تر است.</p>

<h2>میزان تراش دندان</h2>
<p>در لمینت، معمولاً بین نیم تا هفت دهم میلی‌متر از سطح دندان تراشیده می‌شود.
در روش‌های بدون تراش (نو-پرپ) این مقدار به نزدیک صفر می‌رسد، اما همه بیماران
کاندید آن نیستند. کامپوزیت ونیر در بیشتر موارد تراش بسیار کمی لازم دارد.</p>

<h2>هزینه</h2>
<p>کامپوزیت ونیر به‌طور میانگین یک‌سوم تا نصف قیمت لمینت سرامیکی تمام می‌شود.
اگر بودجه محدود است یا می‌خواهید ابتدا نتیجه را تجربه کنید، شروع با کامپوزیت
انتخاب منطقی‌ای است.</p>

<h2>جمع‌بندی</h2>
<p>برای تغییر بلندمدت، طبیعی‌ترین حالت شفافیت و بالاترین مقاومت در برابر لکه،
لمینت سرامیکی برتری دارد. برای اصلاح سریع، اقتصادی و قابل‌برگشت، کامپوزیت
ونیر گزینه بهتری است.</p>
""",
    },
    {
        'title': 'اولین مراجعه کودک به دندانپزشک؛ چطور آماده‌اش کنیم؟',
        'categories': ['دندانپزشکی کودکان'],
        'content': """
<h2>بهترین سن برای اولین ویزیت</h2>
<p>توصیه انجمن دندانپزشکی کودکان این است که اولین مراجعه، حداکثر تا شش ماه
بعد از رویش اولین دندان شیری و در هر صورت پیش از یک‌سالگی انجام شود. این
مراجعه بیشتر جنبه آموزشی و آشناسازی دارد تا درمانی.</p>

<h2>چند نکته که کار را آسان می‌کند</h2>
<ul>
    <li>وقت ملاقات را برای ساعتی بگیرید که کودک سرحال و استراحت‌کرده است</li>
    <li>از کلماتی مثل «درد»، «آمپول» یا «نترس» استفاده نکنید؛ ذهن کودک روی همان‌ها قفل می‌شود</li>
    <li>قبلش در خانه بازی «دندانپزشکی» کنید و دندان‌های عروسک را بشمارید</li>
    <li>خودتان آرام باشید؛ کودکان اضطراب والدین را خیلی سریع منتقل می‌گیرند</li>
</ul>

<h2>در مطب چه اتفاقی می‌افتد؟</h2>
<p>ابتدا کودک با اتاق و صندلی آشنا می‌شود، ابزارها را می‌بیند و لمس می‌کند.
سپس یک معاینه کوتاه انجام می‌شود و در صورت نیاز فلوراید تراپی یا فیشورسیلانت
پیشنهاد می‌گردد. معمولاً کل جلسه کمتر از بیست دقیقه طول می‌کشد.</p>

<h2>بعد از ویزیت</h2>
<p>مراجعه‌های منظم هر شش ماه، مسواک دو بار در روز با خمیر دندان حاوی فلوراید
مناسب سن، و محدود کردن نوشیدنی‌های شیرین بین وعده‌ها، بیشترین تأثیر را در
سلامت دندان کودک دارند.</p>
""",
    },
    {
        'title': 'خونریزی لثه را جدی بگیرید؛ نشانه‌ها و درمان',
        'categories': ['جراحی لثه', 'ترمیمی و عصب‌کشی'],
        'content': """
<h2>خونریزی لثه طبیعی نیست</h2>
<p>خیلی‌ها فکر می‌کنند خونریزی هنگام مسواک زدن عادی است. در واقع این معمولاً
اولین نشانه التهاب لثه (ژنژیویت) است؛ مرحله‌ای که هنوز کاملاً قابل برگشت
است، اما اگر رها شود می‌تواند به پریودنتیت و تحلیل استخوان منجر شود.</p>

<h2>نشانه‌های هشدار</h2>
<ul>
    <li>خونریزی هنگام مسواک یا نخ دندان</li>
    <li>قرمزی، ورم یا حساسیت لثه</li>
    <li>بوی بد دهان که با مسواک برطرف نمی‌شود</li>
    <li>عقب‌نشینی لثه و بلندتر به‌نظر رسیدن دندان‌ها</li>
    <li>لق شدن دندان‌ها در مراحل پیشرفته</li>
</ul>

<h2>چه چیزی باعثش می‌شود؟</h2>
<p>عامل اصلی، تجمع پلاک میکروبی و تبدیل آن به جرم است. اما سیگار، دیابت
کنترل‌نشده، تغییرات هورمونی در بارداری و برخی داروها هم می‌توانند شدت آن را
بیشتر کنند.</p>

<h2>درمان چیست؟</h2>
<p>در مراحل اولیه، یک جلسه جرم‌گیری حرفه‌ای همراه با آموزش تکنیک صحیح مسواک و
نخ دندان معمولاً کافی است. در موارد پیشرفته‌تر جرم‌گیری عمقی زیر لثه
(SRP) و گاهی جراحی فلپ لازم می‌شود.</p>

<p>اگر بیش از یک هفته است لثه‌تان خونریزی می‌کند، منتظر بهتر شدن خودبه‌خودی
نمانید و یک معاینه رزرو کنید.</p>
""",
    },
    {
        'title': 'پوسیدگی دندان چطور شکل می‌گیرد و چطور جلویش را بگیریم؟',
        'categories': ['ترمیمی و عصب‌کشی'],
        'content': """
<h2>پوسیدگی یک‌شبه ایجاد نمی‌شود</h2>
<p>باکتری‌های دهان قند باقی‌مانده روی دندان را مصرف و اسید تولید می‌کنند. این
اسید مینای دندان را کم‌کم حل می‌کند. تا وقتی این تخریب در حد مینا باشد بدون
درد است — به همین دلیل بیشتر پوسیدگی‌ها در معاینه کشف می‌شوند، نه با درد.</p>

<h2>مراحل پیشرفت</h2>
<ul>
    <li>لکه سفید مات روی مینا؛ در این مرحله با فلوراید قابل برگشت است</li>
    <li>حفره سطحی در مینا؛ نیاز به ترمیم ساده</li>
    <li>رسیدن به عاج؛ حساسیت به سرد و شیرین شروع می‌شود</li>
    <li>رسیدن به عصب؛ درد شبانه و نیاز به عصب‌کشی</li>
</ul>

<h2>مؤثرترین کارهای پیشگیرانه</h2>
<p>مسواک دو بار در روز با خمیردندان فلورایده، نخ دندان شبانه، و مهم‌تر از همه
کاهش <em>تعداد</em> وعده‌های شیرین (نه فقط مقدارش). هر بار مصرف قند، حدود بیست
دقیقه محیط دهان را اسیدی می‌کند؛ پس نوشیدن آرام یک نوشابه در طول دو ساعت از
خوردن یک‌بارهٔ آن بدتر است.</p>

<h2>چه زمانی مراجعه کنیم؟</h2>
<p>هر شش ماه یک معاینه، حتی بدون درد. پوسیدگی‌ای که در مرحله لکه سفید پیدا شود
با یک جلسه فلوراید متوقف می‌شود؛ همان پوسیدگی دو سال بعد می‌تواند به روکش
برسد.</p>
""",
    },
    {
        'title': 'جرم‌گیری هر چند وقت یک بار لازم است؟',
        'categories': ['جراحی لثه'],
        'content': """
<h2>پاسخ کوتاه: معمولاً هر شش ماه</h2>
<p>برای بیشتر افراد، جرم‌گیری حرفه‌ای دو بار در سال کافی است. اما این یک عدد
ثابت برای همه نیست و به سرعت رسوب جرم در دهان شما بستگی دارد.</p>

<h2>چه کسانی به فاصله کوتاه‌تری نیاز دارند؟</h2>
<ul>
    <li>سیگاری‌ها و مصرف‌کنندگان قلیان — رسوب سریع‌تر و تیره‌تر</li>
    <li>افراد با سابقه پریودنتیت — هر سه تا چهار ماه</li>
    <li>بیماران دیابتی</li>
    <li>کسانی که ارتودنسی ثابت دارند</li>
    <li>افرادی که بزاق غلیظ یا خشکی دهان دارند</li>
</ul>

<h2>آیا جرم‌گیری به دندان آسیب می‌زند؟</h2>
<p>نه. دستگاه اولتراسونیک جرم را می‌شکند، نه مینا را. حساسیت چند روزه بعد از
جرم‌گیری طبیعی است و علتش این است که سطح ریشه‌ای که زیر جرم پنهان بوده تازه در
معرض قرار گرفته؛ این حس معمولاً در یک هفته از بین می‌رود.</p>

<h2>بعد از جرم‌گیری</h2>
<p>۲۴ ساعت اول از خوردنی‌های خیلی سرد و رنگ‌دار (چای پررنگ، قهوه، سس) پرهیز
کنید. اگر لثه‌تان قبل از جرم‌گیری التهاب داشت، چند روز خونریزی خفیف هنگام
مسواک ممکن است ادامه داشته باشد.</p>
""",
    },
    {
        'title': 'بلیچینگ خانگی یا مطبی؟ تفاوت‌ها را بدانید',
        'categories': ['زیبایی و لمینت'],
        'content': """
<h2>تفاوت اصلی: غلظت و زمان</h2>
<p>در بلیچینگ مطبی، ژل با غلظت بالا زیر نظر دندانپزشک و با محافظت لثه استفاده
می‌شود و نتیجه در یک تا دو جلسه دیده می‌شود. در روش خانگی، ژل با غلظت پایین‌تر
داخل قالب اختصاصی ریخته و هر شب برای دو تا سه هفته استفاده می‌شود.</p>

<h2>مطبی؛ برای چه کسی؟</h2>
<ul>
    <li>وقتی مناسبتی نزدیک است و زمان کم دارید</li>
    <li>وقتی حوصله یا نظم استفاده شبانه ندارید</li>
    <li>وقتی لثه حساس دارید و به محافظت حین کار نیاز است</li>
</ul>

<h2>خانگی؛ برای چه کسی؟</h2>
<ul>
    <li>وقتی بودجه محدودتر است</li>
    <li>وقتی می‌خواهید نتیجه تدریجی و کنترل‌شده باشد</li>
    <li>برای نگه‌داشتن نتیجه پس از بلیچینگ مطبی</li>
</ul>

<h2>چقدر دوام دارد؟</h2>
<p>معمولاً یک تا سه سال، و کاملاً به عادت‌ها وابسته است. چای، قهوه، سیگار و
سس‌های رنگی نتیجه را سریع‌تر برمی‌گردانند. بهترین کار، ترکیب هر دو روش است:
یک جلسه مطبی برای رسیدن به رنگ هدف، بعد قالب خانگی برای نگه‌داری هر چند ماه.</p>

<h2>یک نکته مهم</h2>
<p>بلیچینگ روی روکش، لمینت و کامپوزیت اثر ندارد. اگر دندان‌های جلوی شما ترمیم
رنگی دارند، ابتدا بلیچینگ و بعد تعویض ترمیم‌ها انجام می‌شود — نه برعکس.</p>
""",
    },
    {
        'title': 'دندان عقل را چه زمانی باید کشید؟',
        'categories': ['جراحی لثه'],
        'content': """
<h2>هر دندان عقلی نباید کشیده شود</h2>
<p>اگر دندان عقل کامل رویش پیدا کرده، در قوس فک جا شده، قابل مسواک زدن است و
با دندان مقابل درست تماس دارد، دلیلی برای کشیدن آن وجود ندارد.</p>

<h2>موارد نیازمند جراحی</h2>
<ul>
    <li>نهفته بودن و فشار روی ریشه دندان کنار</li>
    <li>پوسیدگی دندان عقل یا دندان مجاور به‌دلیل عدم دسترسی مسواک</li>
    <li>عفونت‌های مکرر لثه اطراف (پری‌کورونیت)</li>
    <li>ایجاد کیست یا تحلیل استخوان اطراف</li>
    <li>پیش از شروع ارتودنسی، وقتی فضا برای مرتب‌سازی لازم است</li>
</ul>

<h2>جراحی چطور انجام می‌شود؟</h2>
<p>ابتدا با عکس سه‌بعدی موقعیت دقیق ریشه و فاصله‌اش از عصب فک بررسی می‌شود.
جراحی با بی‌حسی موضعی و معمولاً در ۲۰ تا ۴۵ دقیقه انجام می‌گیرد. در موارد
اضطراب زیاد، بی‌حسی همراه با آرام‌بخشی هم ممکن است.</p>

<h2>دوره بهبودی</h2>
<p>ورم در دو روز اول به اوج می‌رسد و بعد کم می‌شود. کمپرس سرد روز اول، غذای
نرم و خنک، پرهیز از سیگار و مکیدن با نی (که لخته را جدا می‌کند) مهم‌ترین
نکات‌اند. بخیه‌ها معمولاً بعد از یک هفته کشیده می‌شوند.</p>
""",
    },
    {
        'title': 'بوی بد دهان؛ شش علت شایع و راه‌حلشان',
        'categories': ['جراحی لثه', 'ترمیمی و عصب‌کشی'],
        'content': """
<h2>در بیشتر موارد، علت در دهان است</h2>
<p>حدود ۸۵ درصد موارد بوی بد دهان منشأ دهانی دارد، نه معده. یعنی با رسیدگی
درست دندانپزشکی قابل حل است.</p>

<h2>شش علت رایج</h2>
<ul>
    <li><strong>پلاک روی زبان:</strong> پشت زبان بیشترین باکتری بودار را نگه
    می‌دارد؛ اسکراپر زبان تأثیر فوری دارد</li>
    <li><strong>بیماری لثه:</strong> جیب‌های عمیق لثه محل تجمع باکتری بی‌هوازی‌اند</li>
    <li><strong>پوسیدگی و ترمیم‌های شکسته:</strong> محل گیر کردن غذا</li>
    <li><strong>خشکی دهان:</strong> بزاق شوینده طبیعی دهان است؛ برخی داروها و
    تنفس دهانی آن را کم می‌کنند</li>
    <li><strong>سینوزیت و ترشحات پشت حلق</strong></li>
    <li><strong>رفلاکس معده</strong> — علت واقعی معده‌ای، اما شایع‌تر از آنچه
    فکر می‌شود نیست</li>
</ul>

<h2>چه کاری کنیم؟</h2>
<p>اول یک معاینه دندانپزشکی و جرم‌گیری. سپس تمیز کردن روزانه زبان، نخ دندان
شبانه و نوشیدن آب کافی. دهان‌شویه فقط بو را چند ساعت می‌پوشاند و علت را از بین
نمی‌برد — اگر بو با دهان‌شویه برمی‌گردد، مشکلی درمان‌نشده وجود دارد.</p>

<h2>چه زمانی نگران باشیم؟</h2>
<p>اگر بعد از جرم‌گیری و رعایت کامل بهداشت، بو بعد از دو هفته ادامه داشت،
بررسی گوش و حلق و بینی و گوارش منطقی است.</p>
""",
    },
    {
        'title': 'مسواک برقی بهتر است یا معمولی؟',
        'categories': ['ترمیمی و عصب‌کشی', 'دندانپزشکی کودکان'],
        'content': """
<h2>تکنیک مهم‌تر از ابزار است</h2>
<p>یک مسواک معمولی که درست و دو دقیقه استفاده شود، از یک مسواک برقی گران که
شلخته استفاده شود بهتر عمل می‌کند. با این حال، مطالعات نشان می‌دهند مسواک برقی
چرخشی-نوسانی به‌طور میانگین پلاک بیشتری برمی‌دارد.</p>

<h2>مسواک برقی برای چه کسانی واقعاً تفاوت می‌سازد؟</h2>
<ul>
    <li>افرادی که ارتودنسی ثابت دارند</li>
    <li>کسانی که مهارت دستی محدود دارند (سالمندان، بیماران آرتریت)</li>
    <li>کودکانی که مسواک زدن را جدی نمی‌گیرند — تایمر و بازی‌سازی کمک می‌کند</li>
    <li>افرادی که فشار زیاد وارد می‌کنند؛ سنسور فشار جلوی سایش لثه را می‌گیرد</li>
</ul>

<h2>اگر مسواک معمولی استفاده می‌کنید</h2>
<ul>
    <li>برس نرم انتخاب کنید، نه متوسط یا زبر</li>
    <li>مسواک را ۴۵ درجه روی مرز لثه بگذارید و حرکت چرخشی کوچک بدهید</li>
    <li>هرگز اره‌ای و افقی نکشید؛ این کار باعث فرسایش طوقه دندان می‌شود</li>
    <li>هر سه ماه یا وقتی پرزها باز شد عوضش کنید</li>
</ul>

<h2>چیزی که هیچ مسواکی جایش را نمی‌گیرد</h2>
<p>نخ دندان. مسواک — برقی یا معمولی — به سطوح بین دندانی نمی‌رسد و بیشتر
پوسیدگی‌های بزرگسالان دقیقاً همان‌جا شروع می‌شوند.</p>
""",
    },
    {
        'title': 'بعد از ایمپلنت چه بخوریم و از چه پرهیز کنیم؟',
        'categories': ['ایمپلنت'],
        'content': """
<h2>۴۸ ساعت اول مهم‌ترین بازه است</h2>
<p>در دو روز اول، هدف محافظت از لخته و کاهش ورم است. غذای نرم و خنک بخورید و
از جویدن در سمت جراحی‌شده پرهیز کنید.</p>

<h2>مناسب برای روزهای اول</h2>
<ul>
    <li>سوپ و آش خنک یا هم‌دمای اتاق</li>
    <li>ماست، پنیر نرم، تخم‌مرغ آب‌پز</li>
    <li>پوره سیب‌زمینی، موز، آووکادو</li>
    <li>اسموتی — با قاشق، نه با نی</li>
</ul>

<h2>مواردی که باید پرهیز کرد</h2>
<ul>
    <li><strong>نی:</strong> مکش می‌تواند لخته را جدا کند</li>
    <li><strong>سیگار:</strong> مهم‌ترین عامل شکست ایمپلنت؛ حداقل دو هفته</li>
    <li>غذاهای داغ در ۲۴ ساعت اول</li>
    <li>دانه‌های ریز مثل کنجد و برنج که لای زخم گیر می‌کنند</li>
    <li>آجیل، نان سنگک و هر چیز سخت تا اجازه دندانپزشک</li>
    <li>الکل و دهان‌شویه‌های الکل‌دار</li>
</ul>

<h2>بهداشت در دوره بهبودی</h2>
<p>از روز دوم شست‌وشوی ملایم با آب نمک گرم (نیم قاشق چای‌خوری در یک لیوان)
چند بار در روز. مسواک زدن سایر دندان‌ها را ادامه دهید و فقط ناحیه جراحی را
تا اجازه دندانپزشک دست نزنید.</p>

<h2>چه زمانی تماس بگیریم؟</h2>
<p>درد شدیدی که با مسکن کم نمی‌شود، ورمی که بعد از روز سوم بیشتر می‌شود، تب،
یا خونریزی‌ای که با فشار گاز بند نمی‌آید — هر کدام یعنی همان روز تماس بگیرید.</p>
""",
    },
]

PRICING = [
    ('ایمپلنت', 1, [
        ('ایمپلنت استرومن سوئیس (هر واحد)', 32_000_000),
        ('ایمپلنت دنتیوم کره‌ای (هر واحد)', 18_500_000),
        ('ایمپلنت اسنوکن کره‌ای (هر واحد)', 15_000_000),
        ('پیوند استخوان (هر ناحیه)', 6_500_000),
        ('روکش زیرکونیا روی ایمپلنت', 4_800_000),
    ]),
    ('ارتودنسی', 2, [
        ('ارتودنسی ثابت فلزی — دو فک', 48_000_000),
        ('ارتودنسی ثابت سرامیکی — دو فک', 62_000_000),
        ('ارتودنسی نامرئی (آلاینر)', 95_000_000),
        ('پلاک متحرک ارتودنسی (هر فک)', 7_500_000),
        ('ریتینر ثابت بعد از درمان', 3_200_000),
    ]),
    ('زیبایی و لمینت', 3, [
        ('لمینت سرامیکی (هر واحد)', 9_500_000),
        ('کامپوزیت ونیر (هر واحد)', 3_800_000),
        ('بلیچینگ مطبی دو فک', 4_200_000),
        ('بلیچینگ خانگی با قالب اختصاصی', 2_600_000),
        ('طراحی لبخند دیجیتال (DSD)', 3_000_000),
    ]),
    ('ترمیمی و عصب‌کشی', 4, [
        ('عصب‌کشی تک‌کاناله', 3_400_000),
        ('عصب‌کشی دوکاناله', 4_600_000),
        ('عصب‌کشی سه‌کاناله', 6_200_000),
        ('ترمیم کامپوزیت یک سطحی', 1_100_000),
        ('ترمیم کامپوزیت دو سطحی', 1_650_000),
        ('روکش PFM', 3_900_000),
    ]),
    ('جراحی و لثه', 5, [
        ('کشیدن دندان ساده', 1_200_000),
        ('جراحی دندان عقل نهفته', 5_500_000),
        ('جرم‌گیری کامل دو فک', 1_400_000),
        ('جرم‌گیری عمقی زیر لثه (هر کوادرانت)', 2_300_000),
        ('فرنکتومی با لیزر', 3_100_000),
    ]),
    ('کودکان', 6, [
        ('معاینه و مشاوره کودک', 450_000),
        ('فلوراید تراپی دو فک', 900_000),
        ('فیشورسیلانت (هر دندان)', 700_000),
        ('ترمیم دندان شیری', 1_300_000),
        ('فضانگهدار ثابت', 2_800_000),
    ]),
]

# (category, doctor index, image count). Enough entries to span several
# "load more" pages (page size is 4) with varied image counts.
GALLERIES = [
    ('ایمپلنت', 0, 5),
    ('ارتودنسی', 1, 4),
    ('زیبایی و لمینت', 2, 6),
    ('ترمیمی و عصب‌کشی', 0, 3),
    ('دندانپزشکی کودکان', 2, 4),
    ('ایمپلنت', 1, 2),
    ('جراحی لثه', 0, 4),
    ('زیبایی و لمینت', 0, 5),
    ('ارتودنسی', 2, 3),
    ('ترمیمی و عصب‌کشی', 1, 2),
    ('دندانپزشکی کودکان', 0, 6),
    ('جراحی لثه', 2, 3),
    ('ایمپلنت', 2, 4),
    ('زیبایی و لمینت', 1, 3),
]

CONTACT_MESSAGES = [
    ('مریم احمدی', '09121234567', True,
     'سلام، برای ایمپلنت دو تا دندان آسیاب پایین می‌خواستم مشاوره بگیرم. '
     'لطفاً بفرمایید هزینه تقریبی چقدر می‌شود و چند جلسه طول می‌کشد؟'),
    ('رضا موسوی', '09359876543', True,
     'وقت بخیر. دخترم ۹ سالشه و دندون‌هاش نامرتب دراومده. برای ارتودنسی کودکان '
     'نوبت مشاوره می‌خواستم. ترجیحاً بعدازظهرهای پنجشنبه.'),
    ('سارا کریمی', '09151112233', False,
     'سلام، من چند وقته لثه‌ام موقع مسواک زدن خونریزی می‌کنه. برای معاینه و '
     'جرم‌گیری می‌خوام نوبت بگیرم. لطفاً اولین وقت خالی رو بهم اطلاع بدید.'),
    ('امیرحسین نوری', '09024445566', False,
     'سلام و خسته نباشید. می‌خواستم بدونم برای لمینت شش تا دندون جلو، امکان '
     'پرداخت اقساطی هم دارید یا نه؟ ممنون میشم راهنمایی کنید.'),
    ('فاطمه صادقی', '05147247247', True,
     'دندون عقلم درد گرفته و صورتم ورم کرده. امکانش هست امروز یا فردا نوبت '
     'اورژانسی بدید؟ خیلی ممنون میشم.'),
    ('حسین رحیمی', '09187778899', False,
     'سلام. یک روکش قدیمی دارم که لق شده. برای تعویضش باید چیکار کنم و '
     'هزینه‌اش چقدره؟ اگر ممکنه تماس بگیرید.'),
    ('زهرا تهرانی', '09336667788', False,
     'سلام، برای بلیچینگ دندان می‌خواستم بدونم چند جلسه لازمه و بعدش '
     'چقدر ماندگاری داره؟ رنگ دندونام تیره شده.'),
]


class Command(BaseCommand):
    help = 'Seed the database with realistic Persian demo content.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep',
            action='store_true',
            help='Do not delete existing content; only create what is missing.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        keep = options['keep']

        if not keep:
            self.stdout.write('Wiping existing demo content…')
            Image.objects.all().delete()
            Gallery.objects.all().delete()
            BlogPost.objects.all().delete()
            Service.objects.all().delete()
            PricingItem.objects.all().delete()
            PricingCategory.objects.all().delete()
            ContactMessage.objects.all().delete()
            Category.objects.all().delete()

        # A full run also replaces existing artwork (the dev DB is full of
        # leftover screenshots); `--keep` leaves any existing image alone.
        self.refresh_images = not keep

        categories = self._seed_categories()
        # Branches first: the doctor profiles link to them.
        branches = self._seed_branches()
        doctors = self._seed_doctors(branches)
        self._seed_about()
        self._seed_services()
        self._seed_blog(categories, doctors)
        self._seed_galleries(categories, doctors)
        self._seed_pricing()
        self._seed_contact()

        self.stdout.write(self.style.SUCCESS('\nDone. Row counts:'))
        for model in (Category, Doctor, About, Branch, Service,
                      ServiceFAQ, BlogPost, Gallery, Image, PricingCategory,
                      PricingItem, ContactMessage):
            self.stdout.write(f'  {model.__name__:18} {model.objects.count()}')

    # ---------------------------------------------------------------- helpers

    @staticmethod
    def _img(seed, name, motif='tooth', width=1200, height=800):
        return ContentFile(make_image(seed, width, height, motif), name=name)

    def _log(self, label, obj):
        self.stdout.write(f'  + {label}: {obj}')

    # ------------------------------------------------------------------ seeds

    def _seed_categories(self):
        out = {}
        for name in CATEGORIES:
            cat, created = Category.objects.get_or_create(name=name)
            out[name] = cat
            if created:
                self._log('category', name)
        return out

    def _seed_branches(self):
        """
        The two practices, keyed by city so a re-run updates rather than
        duplicates. Never wiped by the `--keep`-less path: the footer of every
        page reads these, so an empty table is a visibly broken site.
        """
        branches = {}
        for spec in BRANCHES:
            # Fetched-then-filled rather than `get_or_create(city=…)`: that
            # form inserts the row before the rest of the spec is applied, and
            # `Branch.save` runs `full_clean`, so it fails on a blank address.
            branch = Branch.objects.filter(city=spec['city']).first() or Branch()
            for field, value in spec.items():
                setattr(branch, field, value)
            branch.save()
            branches[spec['city']] = branch
            self._log('branch', branch.display_title)
        return branches

    def _seed_doctors(self, branches):
        """
        Refresh doctor *profiles* only. Usernames/emails/passwords untouched so
        existing logins keep working.
        """
        users = list(
            CustomUser.objects.filter(is_doctor=True).order_by('pk')
        )
        if not users:
            self.stdout.write(self.style.WARNING(
                '  ! No users with is_doctor=True — skipping doctor profiles.'
            ))
            return []

        doctors = []
        for idx, user in enumerate(users[:len(DOCTORS)]):
            spec = DOCTORS[idx]
            user.first_name = spec['first_name']
            user.last_name = spec['last_name']
            if self.refresh_images or not user.image:
                user.image.save(
                    f'doctor-{idx + 1}.jpg',
                    self._img(idx * 3 + 1, f'doctor-{idx + 1}.jpg',
                              motif='avatar', width=600, height=600),
                    save=False,
                )
            user.save()

            doctor, _ = Doctor.objects.get_or_create(user=user)
            doctor.description = spec['description']
            doctor.headline = spec['headline']
            doctor.specialty = spec['specialty']
            doctor.degree = spec['degree']
            doctor.license_number = spec['license_number']
            doctor.experience_years = spec['experience_years']
            doctor.education = spec['education']
            doctor.experience = spec['experience']
            doctor.certifications = spec['certifications']
            doctor.memberships = spec['memberships']
            doctor.order = idx + 1
            doctor.instagram = spec['instagram']
            doctor.telegram = spec['telegram']
            doctor.linkedin = spec['linkedin']
            doctor.twitter = spec['twitter']
            # The slug is left alone once set: changing it breaks a URL a
            # search engine already holds.
            doctor.save()
            doctor.branches.set(
                [branches[city] for city in spec['branches'] if city in branches]
            )
            doctors.append(doctor)
            self._log('doctor', f"{spec['first_name']} {spec['last_name']}")
        return doctors

    def _seed_about(self):
        about = About.objects.first() or About()
        about.name = 'مطب دندانپزشکی دکتر بابایی و بهمدی'
        about.email = 'info@sbdental.ir'
        about.description = (
            'مطب تخصصی دندانپزشکی دکتر بابایی و بهمدی از سال ۱۳۹۲ در قوچان فعالیت '
            'می‌کند. تیم ما متشکل از متخصصان ایمپلنت، ارتودنسی و زیبایی است و با '
            'تجهیزات دیجیتال روز شامل رادیوگرافی سه‌بعدی، اسکنر داخل‌دهانی و لیزر، '
            'درمانی دقیق و کم‌تهاجم ارائه می‌دهد. هدف ما این است که هر بیمار با '
            'اطلاعات کامل و بدون اضطراب، بهترین تصمیم را برای سلامت دهانش بگیرد.'
        )
        if self.refresh_images or not about.image:
            about.image.save(
                'about-clinic.jpg',
                self._img(4, 'about-clinic.jpg', motif='tooth', width=1400, height=900),
                save=False,
            )
        about.save()
        self._log('about', about.name)

    def _seed_services(self):
        for idx, (title, description) in enumerate(SERVICES):
            svc = Service.objects.filter(title=title).first()
            if svc is None:
                svc = Service(title=title, description=description, order=idx + 1)
                svc.image = self._img(idx + 11, f'service-{idx + 1}.jpg', motif='tooth')
                svc.save()
                self._log('service', title)
            self._seed_service_faqs(svc)

    def _seed_service_faqs(self, service):
        """
        Attach the FAQ block whose key appears in this service's title.

        Matched on a keyword rather than the full title so a reworded title
        ("ایمپلنت دندان" to "کاشت ایمپلنت") keeps its questions instead of
        silently losing them.
        """
        for keyword, pairs in SERVICE_FAQS.items():
            if keyword not in service.title:
                continue
            for order, (question, answer) in enumerate(pairs, start=1):
                ServiceFAQ.objects.get_or_create(
                    service=service,
                    question=question,
                    defaults={'answer': answer, 'order': order},
                )
            self._log('faq', f'{service.title} ({len(pairs)})')
            break

    def _seed_blog(self, categories, doctors):
        if not doctors:
            self.stdout.write(self.style.WARNING('  ! No doctors — skipping blog posts.'))
            return
        for idx, spec in enumerate(BLOG_POSTS):
            if BlogPost.objects.filter(title=spec['title']).exists():
                continue
            post = BlogPost(
                title=spec['title'],
                slug=slugify(spec['title'], allow_unicode=True),
                content=spec['content'].strip(),
                writer=doctors[idx % len(doctors)],
            )
            post.image = self._img(idx + 21, f'blog-{idx + 1}.jpg',
                                   motif='tooth', width=1400, height=900)
            post.save()
            post.categories.set([
                categories[name] for name in spec['categories'] if name in categories
            ])
            self._log('blog', spec['title'])

    def _seed_galleries(self, categories, doctors):
        if not doctors:
            self.stdout.write(self.style.WARNING('  ! No doctors — skipping galleries.'))
            return

        # Gallery has no natural key to dedupe on, so treat GALLERIES as an
        # ordered list and only create the entries not yet present. Without
        # this, `--keep` would clone every gallery on each run.
        existing = Gallery.objects.count()
        if existing >= len(GALLERIES):
            self.stdout.write(f'  = galleries already seeded ({existing})')
            return

        for idx, (cat_name, doctor_idx, image_count) in enumerate(GALLERIES):
            if idx < existing:
                continue
            gallery = Gallery.objects.create(
                category=categories.get(cat_name),
                doctor=doctors[doctor_idx % len(doctors)],
            )
            for n in range(image_count):
                img = Image(gallery=gallery)
                img.image = self._img(
                    idx * 10 + n + 31,
                    f'gallery-{gallery.pk}-{n + 1}.jpg',
                    motif='sparkle', width=1000, height=1000,
                )
                img.save()
            self._log('gallery', f'{cat_name} ({image_count} تصویر)')

    def _seed_pricing(self):
        for name, order, items in PRICING:
            cat, _ = PricingCategory.objects.get_or_create(
                name=name, defaults={'order': order}
            )
            for title, price in items:
                PricingItem.objects.get_or_create(
                    title=title, defaults={'price': price, 'category': cat}
                )
            self._log('pricing', f'{name} ({len(items)} آیتم)')

    def _seed_contact(self):
        for name, phone, is_read, message in CONTACT_MESSAGES:
            if ContactMessage.objects.filter(name=name, phone=phone).exists():
                continue
            ContactMessage.objects.create(
                name=name, phone=phone, message=message, is_read=is_read
            )
            self._log('message', name)
