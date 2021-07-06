import os
import logging
from pprint import pformat
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse
from django.shortcuts import render
from django.utils.cache import patch_vary_headers
# from django.views.decorator.http import require_http_methods
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.gzip import gzip_page
# from django.middleware.gzip import GZipMiddleware

from requests import Session, Request
from requests.exceptions import RequestException

if not os.environ.get('ENABLE_LOGGING') == 'TRUE':
    logging.disable()

def ktm_time(*args):
    return (
        datetime.fromtimestamp(datetime.now().timestamp(), tz=timezone.utc)
        + timedelta(hours=5, minutes=45)
    ).timetuple()

logging.Formatter.converter = ktm_time
logger = logging.getLogger(__name__)
logger.setLevel(10)

# whether the state is preserverd or not depends on the call to `Request` or `Session`
# specifically Request.prepare() doesnt apply state while Session.prepare_request() does
SESS = Session()

@csrf_exempt
@gzip_page
def proxier(request, url):
    logger.debug('_' * 10 + 'REQUEST RECEIVED' + '_' * 10)
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url

    # convert to url for appending instead of passing as params cuz <select>
    # html element can send multiple values with same key. This repetition of keys
    # would not be possible using dict.
    if request.GET:
        params = request.GET.urlencode()
        url += '?' + params
    
    final_response = HttpResponse()
    headers = {**request.headers}
    logger.debug('URL: %s', url)
    logger.debug('RAW HEADERS SENT BY CLIENT TO PROXY:\n%s', pformat(headers))

    # Remember all HTTP/1.1 request require Host Header. HTTP/2 uses
    # :authority: pseudo header. I think py-lib requests abstracts all this.
    if 'Forwarded' in headers:
        # client wants host header to be included too.
        import re
        host_obj = re.search(r'host=([\w\.\-]*);?', headers['Forwarded'])
        if host_obj:
            host = host_obj.group(1)
            if host:
                headers['Host'] = host_obj.group(1)
        
        # if not headers['Host']:
        #     headers['Host'] = urlparse(url).netloc
    else:
        # the host header is `portal-everywhere.herokuapp.com` cuz we cloned
        # the request header. So, remove it. Still, the Host header is always sent
        # on HTTP/1.1 req
        del headers['Host']

    http_method = request.method
    origin = headers.setdefault('Origin', '')
    access_control_req_header = headers.setdefault('Access-Control-Request-Headers', '')
    # access_control_req_method = headers.setdefault('Access-Control-Request-Methods', http_method)

    if http_method == 'GET':
        # django seems to put Content-Length & Content-Type header for GET requests.
        # but in prod its prob being served by gunicorn. so catch exception.
        try:
            del headers['Content-Length']
        except KeyError:
            pass
    # headers seem to be PascalCased
    verify_ssl = headers.pop('X-Requests-Verify', 'true') == 'true'
    stream = headers.pop('X-Requests-Stream', 'true') == 'true'

    # TODO: all headers should be sent only on OPTIONS request. Other methods can work fine wihtout all.
    # everything must be explicit to allow credentials to be sent from client browser.
    # but if the origin is null then ACAO will be * which wont allow credentials.
    cors_resp_headers = {
        'Access-Control-Allow-Origin': '*' if origin == 'null' else origin,
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Allow-Methods': 'HEAD, OPTIONS, GET, POST, PUT, PATCH, DELETE',
        # 'Access-Control-Allow-Methods': access_control_req_method,
        'Access-Control-Allow-Headers': access_control_req_header,
        'Access-Control-Expose-Headers': '', # if its not Preflight, this will be populated.
    }
    patch_vary_headers(final_response, ['Origin']) # cuz ACAO is dynamic
    for name, value in cors_resp_headers.items():
        final_response[name] = value

    if http_method == 'OPTIONS':
        return final_response

    req = Request(http_method, url, headers=headers)
    # no session here. each request is new and fresh.
    prepped = req.prepare()
    # if has a body, put it in body
    if http_method != 'GET':
        # setting body, should also set Content-Length. But we are lucky here.
        # cuz we are just copying the exact body from django request. So content-length
        # will be same.
        prepped.body = request.body
    try:
        # TODO: prepend host to location header ?
        # dont follow redirects.
        resp = SESS.send(prepped, stream=stream, verify=verify_ssl, timeout=15, allow_redirects=False)
        logger.debug('HEADERS REQUESTED BY PROXY ON BEHALF:\n%s', pformat(dict(resp.request.headers)))
    except RequestException as ex:
        return JsonResponse({'exception': str(ex)})

    for chunk in resp.iter_content(chunk_size=1024*8):
        final_response.write(chunk)

    final_response.status_code = resp.status_code

    # dont use content-encoding and content-length because the response is already
    # decoded by requests. django automatically sets the Content-Length.
    hop_by_hop_headers = [
        'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',
        'te', 'trailers', 'transfer-encoding', 'upgrade',
    ]
    ignore_headers = ['content-encoding', 'content-length'] + hop_by_hop_headers
    headers_csv = '' # doesnt include hop_by_hop_headers
    for header, value in resp.headers.items():
        if header.lower() in ignore_headers:
            continue
        final_response[header] = value
        # i dont wanna iterate again
        headers_csv += header + ', '
    # add one last header so that we dont have to strip anything.
    headers_csv += 'Content-Encoding' # this header wont be duplicated cuz its in ignore list
    final_response['Access-Control-Expose-Headers'] = headers_csv

    logger.debug('HEADERS TO SEND THE CLIENT:\n%s', final_response.items())
    return final_response

def index(request):
    return render(request, 'proxy/index.html')