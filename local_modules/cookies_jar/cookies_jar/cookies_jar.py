import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class CookiesJar:

    dbName = os.path.join(os.path.dirname(__file__), 'db', 'cookies_database')

    def __init__(self, cookieKey):
        'cookieKey maybe some sites name whose cookie we want to store.'
        self.cookieKey = cookieKey
        os.makedirs(os.path.dirname(self.dbName), exist_ok=True)

    def putCookiesToJar(self, cookieValue, expiry=None):
        '''puts the given cookie to json file.
        usage:
         
        for cookie in self.sess.cookies:
          if cookie.name == 'sessionid':
            CookiesJar('websitename_').putCookiesToJar(cookie.value, cookie.expires)
        '''
        if expiry is None: expiry = 2**31

        d = {self.cookieKey: [cookieValue, expiry]}

        with open(self.dbName + '.json', 'a+') as f:
            f.seek(0)
            contents = f.read()
            if contents:
                d = {**d, **json.loads(contents)}
            f.seek(0)
            f.truncate()
            f.write(json.dumps(d))

    def getCookiesFromJar(self, cookieName: str):
        '''
        param:
            cookieName

        usage:
                CookiesJar('websitename_').getCookiesFromJar('PHPSESSID'))
        '''

        with open(self.dbName + '.json', 'a+') as f:
            f.seek(0)
            read = f.read()
            if read == '':
                logger.debug('json file is empty')
                f.write('{}')
                return None

            fullDict = json.loads(read)
            cookies = fullDict.get(self.cookieKey, None)
            # pprint(cookies)
            if not cookies:
                logger.debug('did not find key cookies in json file')
                return None

            # should be done with using cookies under 1000 seconds
            if (cookies[1] - datetime.now().timestamp()) < 1000:
                logger.debug('cookies found but expired')
                # after poping should not continue to iterate
                del fullDict[self.cookieKey]
                f.seek(0)
                f.truncate()
                f.write(json.dumps(fullDict))
                return None
            else:
                return cookies[0]
        

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger('__name__')

    site = CookiesJar('mysitename_session')
    site.putCookiesToJar(
            'verylonggibbrishidtotracktheuser',
            datetime.now().timestamp() + 100000000)
    print(site.getCookiesFromJar('mysitename_session'))

