from .common_imports import Http404, HttpResponse, redirect, messages, get_user_model
from .sessions import validate_otp_token
from django_ratelimit.decorators import ratelimit
from datetime import timedelta


class DoctorOrSuperuserRequiredMixin:
    """Mixin to check if the user is logged in and is either a doctor or a superuser."""
    
    def dispatch(self, request, *args, **kwargs):
        """
        Override the dispatch method to check if the user is authenticated and is a doctor or superuser.
        If not, raise a 404 error.
        """
        if not (request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser)):
            raise Http404("صفحه مورد نظر یافت نشد")
        
        return super().dispatch(request, *args, **kwargs)


class RedirectIfAuthenticatedMixin:
    """Mixin to redirect the user if they are already authenticated."""
    
    def dispatch(self, request, *args, **kwargs):
        """
        Override the dispatch method to check if the user is authenticated.
        If authenticated, redirect to the home page with an error message.
        """
        if request.user.is_authenticated:
            messages.error(request, "شما در حال حاضر وارد شده‌اید")
            return redirect('home:home')
        return super().dispatch(request, *args, **kwargs)


class RateLimitMixin:
    """Mixin to apply rate limiting to views."""
    
    rate_limit = '20/m'  # Default rate limit
    method_limit = ['POST']  # Limit only POST method
    key_limit = 'ip'  # Use IP address for rate limiting
    error_message = "حداکثر تعداد درخواست‌ها در دقیقه رسیده است. لطفاً کمی صبر کنید"  # Error message for rate limit exceeded

    def dispatch(self, request, *args, **kwargs):
        """
        Override the dispatch method to apply rate limiting before executing the main method.
        If the rate limit is exceeded, return a 429 response with an error message.
        """
        decorator = ratelimit(key=self.key_limit, rate=self.rate_limit, method=self.method_limit, block=False)
        
        # Check rate limit before executing the main method
        wrapped_dispatch = decorator(lambda req, *a, **kw: None)  # Empty function just to test the limit
        wrapped_dispatch(request, *args, **kwargs)  # Execute and store the rate limit result
        
        if getattr(request, 'limited', False):
            return HttpResponse(self.error_message, status=429)
        
        # If no rate limit, execute the main method
        return decorator(super().dispatch)(request, *args, **kwargs)
    

User = get_user_model()

class SessionValidatorMixin:
    """Mixin to validate session and expiration."""
    
    SESSION_EXPIRY = timedelta(minutes=5)  # Session expiry time

    def dispatch(self, request, *args, **kwargs):
        """
        Override the dispatch method to validate the session and OTP token.
        If the user is authenticated, redirect to the home page with an error message.
        If the OTP token is invalid, flush the session and redirect to the login page with an error message.
        """
        if request.user.is_authenticated:
            messages.error(request, "شما در حال حاضر وارد شده‌اید")
            return redirect('home:home')

        # Validate OTP token and get the user
        user, error = validate_otp_token(request)
        if error:
            request.session.flush()  # Flush the session in case of error
            messages.error(request, error)  # Display appropriate error message
            return redirect('accounts:doctor_login')

        # If everything is correct, set the user
        self.user = user
        return super().dispatch(request, *args, **kwargs)