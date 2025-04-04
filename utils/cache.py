def get_cache_key(request, cache_view=None):
    """ 
    Create a unique cache key for authenticated and anonymous users, including GET parameters.
    """
    if request.user.is_authenticated:
        base_key = f"cache_{cache_view}_user_{request.user.id}"
    else:
        base_key = f"cache_{cache_view}_anon"
    
    # اضافه کردن پارامترهای GET به کلید کش
    get_params = request.GET.urlencode()  # تبدیل پارامترهای GET به رشته (مثلاً category=tech&tag=python)
    if get_params:
        return f"{base_key}_{get_params}"
    return base_key
