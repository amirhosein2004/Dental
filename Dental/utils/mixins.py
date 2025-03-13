from .common_imports import Http404, HttpResponse, redirect, messages, get_user_model
from .sessions import validate_otp_token
from django_ratelimit.decorators import ratelimit
from datetime import timedelta


class DoctorOrSuperuserRequiredMixin:
    """میکسین برای بررسی اینکه کاربر لاگین کرده و یا دکتر یا ادمین باشد"""
    
    def dispatch(self, request, *args, **kwargs):
        # بررسی اینکه کاربر لاگین کرده و دکتر یا ادمین باشد
        if not (request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser)):
            raise Http404("صفحه مورد نظر یافت نشد")
        
        return super().dispatch(request, *args, **kwargs)

class RedirectIfAuthenticatedMixin:
    '''میکسین برای اینکه اگر کاربر لاگین کرده باشد ریدارکت شود'''
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.error(request, "شما در حال حاضر وارد شده‌اید")
            return redirect('home:home')
        return super().dispatch(request, *args, **kwargs)

class RateLimitMixin:

    rate_limit = '20/m'  # مقدار پیش‌فرض
    method_limit = ['POST'] # محدود کردن فقط برای متد POST
    key_limit = 'ip'
    error_message = "حداکثر تعداد درخواست‌ها در دقیقه رسیده است. لطفاً کمی صبر کنید"

    def dispatch(self, request, *args, **kwargs):
        """بررسی محدودیت قبل از اجرای `super().dispatch`"""
        decorator = ratelimit(key=self.key_limit, rate=self.rate_limit, method=self.method_limit, block=False)
        
        # ⛔ بررسی محدودیت قبل از اجرای متد اصلی
        wrapped_dispatch = decorator(lambda req, *a, **kw: None)  # تابع خالی فقط برای تست محدودیت
        wrapped_dispatch(request, *args, **kwargs)  # اجرا و ذخیره نتیجه محدودیت
        
        if getattr(request, 'limited', False):

            return HttpResponse(self.error_message, status=429)
        
        # 🟢 اگر محدودیت نبود، حالا متد اصلی را اجرا کن
        return decorator(super().dispatch)(request, *args, **kwargs)
    

User = get_user_model()

class SessionValidatorMixin:
    """Mixin برای اعتبارسنجی سشن و انقضا"""
    SESSION_EXPIRY = timedelta(minutes=5)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.error(request, "شما در حال حاضر وارد شده‌اید")
            return redirect('home:home')

        # اعتبارسنجی توکن و گرفتن کاربر
        user, error = validate_otp_token(request)
        if error:
            request.session.flush()  # پاک کردن سشن در صورت خطا
            messages.error(request, error)  # نمایش پیام خطای مناسب
            return redirect('accounts:doctor_login')

        # اگه همه‌چیز درست بود، کاربر رو ست می‌کنیم
        self.user = user
        return super().dispatch(request, *args, **kwargs)