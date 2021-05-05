from functools import wraps
from django.core.exceptions import PermissionDenied

def has_correct_auth_header(function):
    
    @wraps(function)
    def check_header(request, *args, **kwargs):
        rand_key = '96a768f388be5aaa8416c361570d053611357724f1b9'
        if request.META.get('HTTP_AUTHORIZATION') == 'Basic: ' + rand_key:
            return function(request, *args, **kwargs)
        else:
            return PermissionDenied

    return check_header