import os
import logging
from pprint import pformat
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse
from django.conf import settings
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


def split_set_cookies_header(set_cookie_csv):
    import re
    # assuming that at least one cookie is present in the input parameter.
    splitted = re.split(r',\s(\w+=)', set_cookie_csv)

    first_cookie = splitted[0]
    rest_of_cookies = splitted[1:]
    all_cookies = [first_cookie]

    for i in range(0, len(rest_of_cookies), 2):
        all_cookies.append(''.join(rest_of_cookies[i : i + 2]))

    return all_cookies


def ktm_time(*args):
    return (
        datetime.fromtimestamp(datetime.now().timestamp(), tz=timezone.utc)
        + timedelta(hours=5, minutes=45)
    ).timetuple()

logging.Formatter.converter = ktm_time
logger = logging.getLogger(__name__)
logger.setLevel(10)

# whether the state is preserved or not depends on the call to `Request` or `Session`
# specifically Request.prepare() doesnt apply state while Session.prepare_request() does
SESS = Session()
# !warning: when testing locally with http instead of httpd,
# cookies that have secure flag will correctly not be sent.
# this will create the subtlest of bug and the biggest of headache.
if settings.DEBUG:
    logger.info('Using Local proxy @ 8000')
    SESS.proxies.update({
        'http': '127.0.0.1:8000',
        'https': '127.0.0.1:8000'
    })

SUPPORTED_SCHEMES = ['https://', 'http://'] # order

@csrf_exempt
@gzip_page
def proxier(request, url):
    original_url = url
    # original_url_with_qparams = request.get_full_path()
    # view_url = request.build_absolute_uri()[:-(len(original_url_with_qparams) - len(view_path))]
    view_path = '/' + '/'.join(request.resolver_match.route.split('/')[:-1]) # /proxy
    logger.debug('\n%sREQUEST RECEIVED%s', '-' * 30, '-' * 30)
    for scheme in SUPPORTED_SCHEMES:
        if url.startswith(scheme): break
    else:
        # Default to https
        url = SUPPORTED_SCHEMES[0] + url

    url_scheme, fallback_host, _ , _, _, _ = urlparse(url)
    # convert to url for appending instead of passing as params cuz <select>
    # html element can send multiple values with same key. This repetition of keys
    # would not be possible using dict.
    if request.GET:
        params = request.GET.urlencode()
        url += '?' + params
    
    final_response = HttpResponse()
    headers = {**request.headers}
    # remove heroku headers that leak ip.
    if 'X-Forwarded-For' in headers: # for local-dev.
        del headers['X-Forwarded-For']

    logger.debug('URL: %s', url)
    logger.debug('RAW HEADERS SENT BY CLIENT TO PROXY======:\n%s', pformat(headers))

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
        # the request header. So, remove it. The Host header is always sent
        # on HTTP/1.1
        del headers['Host']

    extra_headers = headers.pop('X-Cust-Extra-Headers', {})
    if extra_headers:
        # this is our custom header to bypass header name normalization by django eg: ("_"->"-")
        # see: https://stackoverflow.com/a/31282738/12091475
        # our delimiter is comma. but this could break if header value has comma in itself. (base64?)
        for hdr in extra_headers.split(','):
            splitted = hdr.split(':', 1)
            if len(splitted) == 2:
                hdr_key, hdr_val = splitted
                headers[hdr_key] = hdr_val


    http_method = request.method
    origin = headers.setdefault('Origin', '*')
    access_control_req_header = headers.setdefault('Access-Control-Request-Headers', '*')
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
    if settings.DEBUG:
        verify_ssl = False

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
        logger.debug('%sCOMPELTE%s\n', '+' * 30, '+' * 30)
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
        # dont follow redirects. will not cause problems.
        resp = SESS.send(
            prepped,
            stream=stream,
            verify=verify_ssl,
            timeout=15,
            allow_redirects=False
        )
        logger.debug('REQUEST HEADERS BY PROXY TO TRUE SERVER=======:\n%s', pformat(dict(resp.request.headers)))
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

        # ufff: requests merges all Set-Cookie headers in such a way that
        # seperating individual headers is a little pain. instead ignore it here
        # and parse from resp.cookies.
        if header.lower() == 'set-cookie': # Set-Cookie2 is deprecated and not used.
            continue

        # if relative location, gotta make it relative from /proxy (current view)
        # instead of the root url (/). here's the logic for location header
        # . if /url, then redirects to origin/url
        # . if url, then redirects to path/url
        # . If abs url, then redirects to abs url
        # convert all 3 above to /(current_view)/url
        if header.lower() == 'location':
            logger.info('Location Header found. Rewriting it.')
            if value.startswith('/'):
                logger.info('Location Header is relative. Making it absolute')
                value = url_scheme + '://' + fallback_host + value
            logger.info('Prefixing it with proxy endpoint: `%s`', view_path)
            value = view_path + '/' + value

        final_response[header] = value
        # i dont wanna iterate again
        headers_csv += header + ', '
    # add one last header so that we dont have to strip anything.
    headers_csv += 'Content-Encoding' # this header wont be duplicated cuz its in ignore list
    final_response['Access-Control-Expose-Headers'] = headers_csv
    final_response['Cross-Origin-Resource-Policy'] = 'cross-origin'

    # To send multiple cookies, use multiple "Set-Cookie" headers but keys in dict 
    # must be unique. Hence, use set_cookie instead of directly setting header.
    for cookie in resp.cookies:
        # for rewriting cookie path
        # use the orignal url instead of scheme prefixed cuz that is what the client
        # knows
        _scheme = urlparse(original_url)[0]
        # _path = urlparse(view_url)[2]
        _path = view_path + '/'
        _origin = f'{_scheme}://{fallback_host}' if _scheme else fallback_host
        expiry = datetime.fromtimestamp(cookie.expires, tz=timezone.utc) if cookie.expires else None
        # python seems to add double quotes on cookies containing slash(/). even stripping that.
        # django will re-add it. hence handle it client side.
        final_response.set_cookie(
            cookie.name,
            value=cookie.value or '',
            expires=expiry,
            # If domain was specified, then it would be set on the real server.
            # Unfortunately, browser dont accept cookies set from other domains
            # and using same requests.Session with multiple domain could increase
            # cookie collision and overwrite. path could solve all these problems.
            domain=cookie.domain if cookie.domain_specified else None,
            # we can use path to seperate cookies so that cookie with same name
            # from different origins can coexist on our origin.
            path=_path + _origin + cookie.path,
            secure=cookie.secure, # Note: During dev, secure cookie wont be set on http
            httponly=cookie._rest.get('HttpOnly') or False,
            samesite=cookie._rest.get('SameSite') or None
        )

    logger.debug('HEADERS(cookies not shown) TO SEND THE CLIENT=======:\n%s', pformat(dict(final_response.headers)))
    logger.debug('COOKIES TO SEND THE CLIENT=======:\n%s', pformat(dict(final_response.cookies)))
    logger.debug('%sCOMPELTE%s\n', '+' * 30, '+' * 30)
    return final_response

def index(request):
    return render(request, 'proxy/index.html')