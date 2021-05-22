import logging
from pprint import pformat
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse
from django.shortcuts import render
# from django.views.decorator.http import require_http_methods
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.gzip import gzip_page
# from django.middleware.gzip import GZipMiddleware

from requests import Session, Request
from requests.exceptions import RequestException

def ktm_time(*args):
    return (
        datetime.fromtimestamp(datetime.now().timestamp(), tz=timezone.utc)
        + timedelta(hours=5, minutes=45)
    ).timetuple()

logging.Formatter.converter = ktm_time
# FORMAT = '%(asctime)15s :: [%(module)s] :: %(levelname)s :: %(message)s'
# logging.basicConfig(level=logging.DEBUG, format=FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(10)

# whether the state is preserverd or not depends on the call to `Request` or `Session`
# specifically Request.prepare() doesnt apply state while Session.prepare_request() does
SESS = Session()

@csrf_exempt
@gzip_page
def proxier(request, url):
    print('_' * 10 + 'REQUEST RECEIVED' + '_' * 10)
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url

    # convert to url for appending instead of passing as params cuz <select>
    # html element can send multiple values with same key. This repetition of keys
    # would not be possible using dict.
    if request.GET:
        params = request.GET.urlencode()
        url += '?' + params
    
    headers = {**request.headers}
    logger.debug('URL: %s', url)
    logger.debug('RAW HEADERS:\n%s', pformat(headers))

    # rewrite host header by parsing the target hostname
    headers['Host'] = urlparse(url).netloc
    http_method = request.method
    # django seems to put Content-Length & Content-Type header for GET requests.
    if http_method == 'GET':
        # but in prod its prob being served by gunicorn. so catch excepetion.
        try: del headers['Content-Length']
        except KeyError: pass
    # headers seem to be PascalCased
    verify_ssl = headers.pop('X-Requests-Verify', 'true') == 'true'
    stream = headers.pop('X-Requests-Stream', 'true') == 'true'
    
    req = Request(http_method, url, headers=headers)
    # no session here. each request is new and fresh.
    prepped = req.prepare()
    # if has a body put it in body
    if http_method != 'GET':
        prepped.body = request.body
    try:
        # TODO: prepend host to location header ?
        # dont follow redirects.
        resp = SESS.send(prepped, stream=stream, verify=verify_ssl, timeout=30, allow_redirects=False)
        logger.debug('HEADERS REQUESTED BY PROXY ON BEHALF:\n%s', pformat(resp.request.headers))
    except RequestException as ex:
        return JsonResponse({'exception': str(ex)})

    this_response = HttpResponse()
    for chunk in resp.iter_content(chunk_size=1024*8):
        this_response.write(chunk)

    this_response.status_code = resp.status_code

    # dont use content-encoding and content-length because the response is already
    # decoded by requests. django automatically sets the Content-Length.
    ignore_headers = ['content-encoding', 'content-length']
    hop_by_hop_headers = [
        'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',
        'te', 'trailers', 'transfer-encoding', 'upgrade',
    ]
    for header, value in resp.headers.items():
        if header.lower() in hop_by_hop_headers + ignore_headers:
            continue
        this_response[header] = value
    
    # logger.debug('HEADERS TO SEND:\n%s', this_response.items())
    return this_response

def index(request):
    return render(request, 'proxy/index.html')