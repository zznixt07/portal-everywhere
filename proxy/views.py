import logging
import json
from urllib.parse import urlparse
# from django.views.decorator.http import require_http_methods
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from requests import Session, Request
from requests.exceptions import RequestException 

logger = logging.getLogger(__name__)
FORMAT = '[%(module)s] :: %(levelname)s :: %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)


# whether the state is preserverd or not depends on the call to `Request` or `Session`
# specifically Request.prepare() doesnt apply state while Session.prepare_request() does
SESS = Session()

@csrf_exempt
def proxier(request, url):
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url

    # convert to url for appending instead of passing as params cuz <select>
    # html element can send multiple values with same key. This repetition of keys
    # would not be possible using dict.
    if request.GET:
        params = request.GET.urlencode()
        url += '?' + params
    
    headers = {**request.headers}
    # rewrite host header by parsing the target hostname
    headers['Host'] = urlparse(url).netloc
    http_method = request.method
    # django seems to put Content-Length & Content-Type header for GET requests.
    if http_method == 'GET':
        del headers['Content-Length']
    
    req = Request(http_method, url, headers=headers)
    # no session here. each request is new and fresh.
    prepped = req.prepare()
    # if has a body put it in body
    if http_method != 'GET':
        prepped.body = request.body
    try:
        # maybe stream, verify can be passed in header explicitly by the client.
        resp = SESS.send(prepped, stream=True, verify=True, timeout=5, allow_redirects=False)
    except RequestException as ex:
        return JsonResponse({'exception': str(ex)})

    this_response = HttpResponse()
    for chunk in resp.iter_content(chunk_size=1024*8):
        this_response.write(chunk)

    this_response.status_code = resp.status_code

    hop_by_hop_headers = [
        'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',
        'te', 'trailers', 'transfer-encoding', 'upgrade',
    ]
    for header, value in resp.headers.items():
        if header.lower() in hop_by_hop_headers: continue
        this_response[header] = value
    
    return this_response