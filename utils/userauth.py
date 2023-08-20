from django.http import HttpResponseForbidden
from functools import wraps

from .time import cst_now
from user.models import Subscription, SubscriptionStatus, Usage, User


def check_usage_limit(view_func):
    "Decorator for view functions that require user login and usage limit"
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden('Not logged in')
        
        if is_usage_limit_reached(request.user):
            return HttpResponseForbidden('Max usage time was reached')
        
        return view_func(request, *args, **kwargs)

    return wrapper

def require_login(view_func):
    "Decorator for view functions that require user login"
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden('Not logged in')
        return view_func(request, *args, **kwargs)

    return wrapper

def is_usage_limit_reached(user: User):
    subscription = Subscription.get_unique(user)

    today = cst_now().date()
    usage = Usage.get_unique(user, today)

    return Usage.get_remaining_time_seconds(usage, subscription) <= 0
