from django.http import JsonResponse
from .logic import api as tech 
from own_custom_app.decorators import has_correct_auth_header

@has_correct_auth_header
def xda(request):
    resp = tech.xdadev_feed()
    return JsonResponse(resp, safe=False)

@has_correct_auth_header
def torrentfreak(request):
    resp = tech.torrentfreak_feed()
    return JsonResponse(resp, safe=False)

