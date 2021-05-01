import os
import logging
import time
import requests
from requests_toolbelt import MultipartEncoder

logger = logging.getLogger(__name__)


class Telegram:
    '''
    usage::
        with Telegram('-1001234567890', botKey) as myChannel:
            myChannel.sendPicture('https://google.com/favico.png', caption='nice')
            myChannel.sendText('hello. beep boop!!')
    '''
    
    UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
            + '(KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36')

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.s.close()
        return

    def __init__(self, channelId, botApiKey, sendWithoutSound=False, parseMode='MarkdownV2'):
        self.channelId = channelId
        self.apiUrl = 'https://api.telegram.org/bot' + botApiKey
        self.s = requests.Session()
        self.s.headers.update({'User-Agent': Telegram.UA})
        self.options = {
            'chat_id': self.channelId,
            'parse_mode': parseMode,
            'disable_notification': sendWithoutSound
        }

    def _post(self, url, chatInfo, fileObj):
        r = self.s.post(url, params=chatInfo, data=fileObj, timeout=245,
                        headers={'Content-Type': fileObj.content_type})
        # logger.debug('%s', r.text)
        if r.json()['ok']:
            logger.debug('sent successfully')
            return True
        return False

    def _send(self, url, chatInfo):
        '''sends the actual request'''
        r = self.s.get(url, params=chatInfo, timeout=200)
        resp = self.botResponse(r.json())
        if resp['response'] == 'retry':
            return self._send(url, chatInfo)
        if resp['status'] != 200:
            print(f'failed to send cuz {resp["response"]} {chatInfo}')
            # logger.debug(f'failed to send cuz {resp["response"]} {chatInfo}')
            httpUrl = self.containedHttpUrl(chatInfo)
            # if this was called from sendText() dont send anything
            if not httpUrl: return False
            # we will fallback to text. since caption key is present in medias
            # this is valid solution cuz caption has all necessary things (except url)
            logger.debug('trying to send as text instead')
            self.sendText(chatInfo['caption'] + '\n\n' + self.escape(httpUrl))
        else:
            logger.debug('sent successfully')
            return True

    def sendText(self, textToSend):
        # text > 4096 cannot be sent as one. so split it.
        lenLim = 4096
        for i in range(0, len(textToSend), lenLim):
            chatInfo = {**{'text': textToSend[i:i+lenLim]}, **self.options}
            url = self.apiUrl + '/sendMessage'
            return self._send(url, chatInfo)

    def sendPicture(self, url, caption=None):
        chatInfo = {**{'photo': url, 'caption': caption}, **self.options}
        url = self.apiUrl + '/sendPhoto'
        return self._send(url, chatInfo)

    def sendVideo(self, url, caption=None):
        chatInfo = {**{'video': url, 'caption': caption}, **self.options}
        url = self.apiUrl + '/sendVideo'
        return self._send(url, chatInfo)

    def sendLocalPicture(self, imgPath, caption=None, removeAfter=False):
        # From docs:
        # "Requests supports streaming uploads, which allow you to send large
        # streams or files without reading them into memory"
        with open(imgPath, 'rb') as file:
            files = {'photo': file}
            chatInfo = {**{'caption': caption}, **self.options}
            r = self.s.post(self.apiUrl + '/sendPhoto',
                            data=chatInfo,
                            files=files,
                            timeout=245)
        if r.json()['ok']:
            logger.debug('sent successfully')
        if removeAfter:
            os.remove(imgPath)
        return None

    def sendLocalVideo(self, vidPath, caption=None, filename=None, removeAfter=False):
        # https://stackoverflow.com/a/20830717/12091475
        # if both data and files param are given, requests cant stream-upload it.
        self._streamUpload('/sendVideo', vidPath, caption, filename, 'video')
        if removeAfter: os.remove(vidPath)
        return None

    def sendLocalDocument(self, docPath, caption=None, filename=None, removeAfter=False):
        self._streamUpload('/sendDocument', docPath, caption, filename, 'document')
        if removeAfter: os.remove(docPath)
        return None

    def _streamUpload(self, endpoint, filePath, caption, filename=None, type=None):
        if filename is None:
            filename = caption
        with open(filePath, 'rb') as fileObj:
            files = MultipartEncoder({
                    type: (filename, fileObj, 'multipart/form-data') # see _post
                })
            chatInfo = {**{'caption': caption}, **self.options}
            self._post(self.apiUrl + endpoint, chatInfo, files)
        return None

    @staticmethod
    def botResponse(resp):
        if resp['ok']:
            logger.debug('done')
            return {'response': True, 'status': 200}
        else:
            if resp['error_code'] == 429:
                tMinus = resp['parameters']['retry_after']
                logger.debug('sleeping for %s', tMinus)
                time.sleep(tMinus)
                return {'response': 'retry', 'status': 0}
        
        return {'response': resp['description'], 'status': resp['error_code']}

    @staticmethod
    def containedHttpUrl(dictionary):
        '''figure out whether dict has http url by looking at specific keys'''
        for k in ['video', 'photo']:
            if k in dictionary.keys():
                return dictionary[k]
        return False

    @staticmethod
    def escape(text, toEscape: str = None):
        """
        Call when sending non-formatted text to telegram chat. You can call this
        manually(recommended) or set escape=True while calling other style methods.
        """
        if not toEscape:
            toEscape = '_*[]()~`>#+-=|{}.!'
        for character in toEscape:
            text = text.replace(character, '\\' + character)

        return text

    @staticmethod
    def bold(string: str, escape: bool = False):
        return Telegram._replacer(string, '*', escape)

    @staticmethod
    def italic(string: str, escape: bool = False):
        return Telegram._replacer(string, '_', escape)

    @staticmethod
    def underline(string: str, escape: bool = False):
        return Telegram._replacer(string, '__', escape)
    
    @staticmethod
    def code(string: str, escape: bool = False):
        return Telegram._replacer(string, '`', escape)
    
    @staticmethod
    def _replacer(text: str, surrounds: str, escape: bool):
        if not text:        # if text is empty, dont include formatting char
            return text     # else Telegram cannot parse it properly
        if escape:
            return surrounds + Telegram.escape(text) + surrounds
        else:
            return surrounds + text + surrounds


    """============ Markdown v1 ================
    @staticmethod
    def bold(string, escape: bool = True):
        if escape: return '*' + Telegram._replacer(string, '*') + '*'
        else: return '*' + string + '*'

    @staticmethod
    def italic(string, escape: bool = True):
        if escape: return '_' + Telegram._replacer(string, '_') + '_'
        else: return '_' + string + '_'

    @staticmethod
    def code(string, escape: bool = True):
        if escape: return '`' + Telegram._replacer(string, '`') + '`'
        else: return '`' + string + '`'

    @staticmethod
    def escape(string):
        '''Call when sending non-formatted text to telegram chat
        Note: First escape then apply desired formatting and (set escape=False)
        '''
        return Telegram._replacer(string, '')

    @staticmethod
    def _replacer(text, surrounds):
        return text.replace('_', rf'{surrounds}\_{surrounds}') \
                .replace('*', rf'{surrounds}\*{surrounds}') \
                .replace('`', rf'{surrounds}\`{surrounds}') \
                .replace('[', rf'\[') # mentioning url or user is not supported
    """

if __name__ == '__main__':
    logging.basicConfig(level=10)
    logger = logging.getLogger(__name__)

    api_key = os.environ['BOTAPIKEY']
    with Telegram('-1001162454492', api_key) as ch:
        # ch.sendVideo('https://i.redd.it/7tiam6ru5pz51.gif',caption='')
        ch.sendPicture('https://i.redd.it/7tiam6ru5pz51.gif' ,caption='')
    print('Done')