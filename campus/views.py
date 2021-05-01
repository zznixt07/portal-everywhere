import base64
import logging
import time
# from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse
from .campus_api import campus_4, campus_creds


username: str = campus_creds.CAMPUS_USERNAME
password: str = base64.b64decode(campus_creds.CAMPUS_PASSWORD).decode('utf-8')

logging.basicConfig(level=10)
logging.getLogger('urllib3').setLevel('WARNING')
logger = logging.getLogger(__name__)
logger.setLevel(10)
# logging.disable()

test_channel = '-1001162454492'
SESSION_TIMEOUT = 30 * 60
CAMPUS4 = campus_4.Campus4_0(username, password)
LOGIN_TS = time.time()
STD_YEAR = 'two'
STD_BATCH = CAMPUS4.my_details()['batch']
MODULES = CAMPUS4.get_all_computing_courses()

def refresh_stale_sess():
    global CAMPUS4
    if (time.time() - LOGIN_TS) > SESSION_TIMEOUT:
        CAMPUS4 = campus_4.Campus4_0(username, password)
        return True
    return False

def recent_notices(request):
    refresh_stale_sess()
    # sort by date ascendingly. oldest is at first. We want that.
    notices = sorted(CAMPUS4.get_all_notices(), key=lambda notice: notice['date'])
    return JsonResponse(notices, safe=False)

def lessons_in_module(request, module_slug):
    return JsonResponse(CAMPUS4.get_all_lessons(module_slug), safe=False)

def assessment_in_lesson(request, lesson_slug):
    return JsonResponse(CAMPUS4.get_assessment(lesson_slug), safe=False)

def own_routine(request):
    return JsonResponse(CAMPUS4.get_routine(), safe=False)
