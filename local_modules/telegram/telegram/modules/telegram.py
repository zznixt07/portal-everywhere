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
    apiEndpoint = 'https://api.telegram.org/bot'
    UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
            + '(KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36')

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.s.close()
        return

    def __init__(self, channelId, botApiKey, sendWithoutSound=False, parseMode='MarkdownV2'):
        self.apiUrl = self.apiEndpoint + botApiKey
        self.s = requests.Session()
        self.s.headers.update({'User-Agent': Telegram.UA})

        # map class argument to telegram's POST form keys
        self.telegramArg = {
            'parseMode': 'parse_mode',
            'sendWithoutSound': 'disable_notification'
        }
        self.options = {
            'chat_id': channelId,
            'parse_mode': parseMode,
            'disable_notification': sendWithoutSound
        }

        # tuple values is taken from telegram bots API docs.
        self.endpointMethods = {
            'sendLocalPicture': ('/sendPhoto', 'photo'),
            'sendLocalVideo': ('/sendVideo', 'video'),
            'sendLocalDocument': ('/sendDocument', 'document'),
        }

    def setOptions(self, opts: dict):
        for key in opts:
            self.options[self.telegramArg[key]] = opts[key]

    def __getattr__(self, method):

        def arg_collector(filepath, caption=None, filename=None, removeAfter=False, **opts):
            endpoint, fieldName = self.endpointMethods.get(method)
            if not endpoint:
                raise AttributeError
            self.setOptions(opts)
            resp = self._streamUpload(endpoint, fieldName, filepath, caption, filename, **opts)
            if not resp:
                return False
                # eventho if remove=True, dont remove if unsuccessful.
            if removeAfter:
                os.remove(filepath)
            return True

        return arg_collector

    def _post(self, endpoint, chatInfo, fileObj):
        'perform POST for image, video, and general files.'

        chatInfo = {**self.options, **chatInfo}
        r = self.s.post(self.apiUrl + endpoint, params=chatInfo, data=fileObj,
                        timeout=245, headers={'Content-Type': fileObj.content_type})
        # logger.debug('%s', r.text)
        if not r.json()['ok']:
            logger.debug('%s', chatInfo)
            logger.debug('%s', r.json())
            return False
        logger.debug('sent successfully')
        return True

    def _send(self, endpoint, chatInfo):
        'perform GET for text'

        chatInfo = {**self.options, **chatInfo}
        r = self.s.get(self.apiUrl + endpoint, params=chatInfo, timeout=200)
        resp = self.botResponse(r.json())
        if resp['response'] == 'retry':
            return self._send(endpoint, chatInfo)
        if resp['status'] != 200:
            logger.debug('%s', chatInfo)
            logger.debug('%s', r.json())
            return False
        
        logger.debug('sent successfully')
        return True

    def sendText(self, textToSend, **opts):
        responses = []
        self.setOptions(opts)
        # text > 4096 cannot be sent as one. so split it.
        lenLim = 4096
        for i in range(0, len(textToSend), lenLim):
            chatInfo = {'text': textToSend[i:i+lenLim]}
            url = '/sendMessage'
            responses.append(self._send(url, chatInfo))

        return all(responses)

    def sendPicture(self, url, caption=None, **opts):
        self.setOptions(opts)
        chatInfo = {'photo': url, 'caption': caption}
        url = '/sendPhoto'
        return self._send(url, chatInfo)

    def sendVideo(self, url, caption=None, **opts):
        self.setOptions(opts)
        chatInfo = {'video': url, 'caption': caption}    
        url = '/sendVideo'
        return self._send(url, chatInfo)

    def _streamUpload(self, endpoint, fieldName, filePath, caption, filename=None, **opts):
        # if both data and files param are given, requests cant stream-upload it.
        # https://stackoverflow.com/a/20830717/12091475
        with open(filePath, 'rb') as fileObj:
            files = MultipartEncoder({
                fieldName: (filename or caption or '', fileObj, 'multipart/form-data') # see _post
            })
            self.setOptions(opts)
            chatInfo = {'caption': caption}
            return self._post(endpoint, chatInfo, files)

    @staticmethod
    def botResponse(resp):
        if resp['ok']:
            logger.debug('done')
            return {'response': True, 'status': 200}
        if resp['error_code'] == 429:
            tMinus = resp['parameters']['retry_after']
            logger.debug('sleeping for %s', tMinus)
            time.sleep(tMinus)
            return {'response': 'retry', 'status': 0}
    
        return {'response': resp['description'], 'status': resp['error_code']}

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
    def captionedUrl(url='', caption='', escape: bool = False):
        if escape:
            # AFAIK no need to escape url
            return f'[{Telegram.escape(caption)}]({url})'
        return f'[{caption}]({url})'
    
    @staticmethod
    def _replacer(text: str, surrounds: str, escape: bool):
        if not text:        # if text is empty, dont include formatting char
            return text     # cuz Telegram wont parse.
        if escape:
            return surrounds + Telegram.escape(text) + surrounds
        
        return surrounds + text + surrounds


    """============ Markdown v1 ================

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
    with Telegram('-1001162454492', api_key, sendWithoutSound=False) as ch:
        # ch.sendVideo('https://i.redd.it/7tiam6ru5pz51.gif',caption='')
        # ch.sendPicture('https://i.redd.it/7tiam6ru5pz51.gif' ,caption='')
        # ch.sendLocalVideo(
            # r"C:\Users\zznixt\Downloads\Telegram Desktop\IMG_4898.MP4",
            # caption='geggedity',
            # filename='family_guy_funny_moments #18',
        # )
        # ch.sendText('[hello](https://cdn.hipwallpaper.com/i/5/73/1uVwnA.jpg)')
        ch.sendText(
            Telegram.bold('Shrinkflation: Costco Paper Towels, Now with 20 Fewer Sheets per Roll\n', escape=True)
            + Telegram.captionedUrl(
                caption=Telegram.escape("▲ 145 | 18:00 May 03 '21 | 7 comments\n" + '·' * 118 + "\n\n"),
                url=Telegram.escape('https://news.ycombinator.com/item?id=27019345'),
            )
            + Telegram.captionedUrl(
                caption=Telegram.bold('forums.redflagdeals.com', escape=True),
                url=Telegram.escape('https://forums.redflagdeals.com/costco-paper-towels-now-20-fewer-sheets-per-roll-2461125/'),
            )
        )

    print('====Done====')