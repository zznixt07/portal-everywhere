import os
import json
import random
import logging
import warnings
from datetime import datetime
from typing import Dict, List, Any, Union, Tuple
from pprint import pprint
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
from database import Database
from telegram import Telegram
from cookies_jar import CookiesJar
# import stackprinter
# stackprinter.set_excepthook()

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)
VERIFY_CERT = True


class Campus4_0:

    host = 'https://campus.softwarica.edu.np'
    api_url = 'https://api-campus.softwarica.edu.np'
    media_url = api_url + '/uploads/files'

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.sess.close()
        return

    def __init__(self, username: str, password: str):
        self.sess = requests.Session()
        self.sess.headers.update({
            'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                        + '(KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36'),
            'Referer': self.host + '/',
            })
        self._post('/verification/login', json={'username': username, 'password': password})
        """
        jar = CookiesJar('campus300.3_190378')
        cookie = jar.getCookiesFromJar('sid')
        if cookie:
            logger.debug('cookie found')
            self.sess.cookies.set(name='sid', value=cookie)
            return
        else:
            logger.debug('cookie not found. putting cookies to jar.')
            self._post(
                '/verification/login',
                json={'username': username, 'password': password})
            for cookie in self.sess.cookies:
                if cookie.name == 'sid':
                    jar.putCookiesToJar(cookie.value, cookie.expires)
                    break
        """

    def _get(self, endpoint: str, **kwargs):
        logger.debug('%s', self.api_url + endpoint)
        r = self.sess.get(self.api_url + endpoint, verify=VERIFY_CERT, **kwargs)
        r.raise_for_status()
        return r.json()

    def _post(self, endpoint: str, **kwargs):
        logger.debug('%s', self.api_url + endpoint)
        r = self.sess.post(self.api_url + endpoint, verify=VERIFY_CERT, **kwargs)
        r.raise_for_status()
        return r.json()
    
    def my_details(self):
        return self._get('/users/uid')['user']

    def enrolled_modules(self):
        return self._get('/users/my-learnings')['modules']

    def get_all_lessons(self, module_loc: str) -> List[Dict['id', Tuple['lesson_title', 'lesson_slug']]]:
        """get all lessons with week and slug"""
        lesson_ids = []
        lessons = self._get(f'/lessons/{module_loc}/weekly/public')['lessons']
        for lesson in lessons:
            week: int = lesson['week']
            for lsn in lesson['lessons']:
                lesson_ids.append({
                    lsn['_id']: (lsn['lessonTitle'], lsn['lessonSlug'], week)
                })

        return lesson_ids

    def get_lesson_content(self, lesson_slug: str) -> 'HTML':
        "get the html of the lesson"

        return self._get(f'/lessons/{lesson_slug}')['lesson']['lessonContents']

    def get_all_completed_lesson_ids(self) -> List['id']:
        'this gets all the completed lesson of *all* the modules'

        completed = self._get('/users/completed-lessons')
        return [lesson['lesson'] for lesson in completed['completedLessons']]
        
    def mark_lessons_as_complete(self, module_loc: str, lesson_id: str) -> None:
        
        curr_lesson = self._post('/tracking/lesson-status',
                            data={'lesson': lesson_id, 'moduleSlug': module_loc,})
        if curr_lesson['lessonStatus']:
            if curr_lesson['lessonStatus']['isCompleted']: return

        multiplier = 1000
        now_ts: int = int(float(datetime.now().timestamp() * multiplier))
        end_ts: int = now_ts + random.randint(9210, 24103) * multiplier
        print(now_ts, end_ts)
        # now_ts_sec: int = now_ts // multiplier
        # end_ts_sec: int = end_ts // multiplier
        # from datetime import timezone
        # frmt = '%I:%M %p, %b %d %Y'
        # utc_start = datetime.fromtimestamp(now_ts_sec, tz=timezone.utc).strftime(frmt)
        # utc_end = datetime.fromtimestamp(end_ts_sec, tz=timezone.utc).strftime(frmt)
        # local_start =  datetime.fromtimestamp(now_ts_sec).strftime(frmt)
        # local_end = datetime.fromtimestamp(end_ts_sec).strftime(frmt)
        # print(f'''
        # start time
        #     UTC   : {utc_start}
        #     local : {local_start}
        # end time
        #     UTC   : {utc_end}
        #     local : {local_end}
        # ''')
        start_lesson = self._post('/tracking/start',
                            data={
                                'lesson': lesson_id,
                                'moduleSlug': module_loc,
                                'startDate': now_ts,
                            })
        pprint(start_lesson)

        # end_ts = now_ts
        # end_lesson = self._post('/tracking/mark-as-complete',
        #                     data={
        #                         'endDate': end_ts,
        #                         'isCompleted': True,
        #                         'lesson': lesson_id,
        #                         'moduleSlug': module_loc,
        #                     })
        # pprint(end_lesson)

    def tests(self):
        multiplier = 1000
        lesson_id = '603b090707b8f52d153739dd'
        module_loc = 'developing-the-modern-web'
        now_ts: int = int(float(datetime.now().timestamp() * multiplier))
        # start_lesson = self._post('/tracking/start',
        #                     data={
        #                         'lesson': lesson_id,
        #                         'moduleSlug': module_loc,
        #                         'startDate': now_ts,
        #                     })
        # pprint(start_lesson)

        end_ts = now_ts + 5800 * multiplier
        end_ts = 1616496927 * 1000
        # print(now_ts, end_ts)
        end_lesson = self._post('/tracking/mark-as-complete',
                            data={
                                'endDate': end_ts,
                                'isCompleted': True,
                                'lesson': lesson_id,
                                'moduleSlug': module_loc,
                            })
        pprint(end_lesson)
        
    def get_assessment(self, lesson_name: str) -> dict:
        # https://api-campus.softwarica.edu.np/assessments/core-java-3
        assessment = self._get('/assessments/' + lesson_name)
        try:
            return assessment['assessment']
        except KeyError:
            return {}

    def get_all_notices(self, mark_new_as_read: bool = True) -> list:
        notice_lst = []
        
        resp = self._get(f'/notices/all-notices/1')
        unread_count = resp['unreadCount']
        if unread_count <= 0:
            return []

        notices = resp['notices']

        for notice in notices[:unread_count]:
            _id = notice['_id']
            if mark_new_as_read:
                self._post(f'/notices/{_id}/mark-as-read')
            dt = notice['createdAt']
            content = notice['noticeContent']
            title = notice['noticeTitle']
            by = ' '.join(notice['postedBy'].values())
            # read_by = notice['readBy']
            
            # if Common then we want it. if batch then filter section.
            # if notice['batch']: # if empty then its Common.
            #     if STD_BATCH not in notice['batch']: continue
            attachment = notice.get('filename', '')
            if attachment:
                attachment = self.media_url + '/' + quote(attachment)
            notice_lst.append({
                    'id': _id,
                    'title': title,
                    'content': content,
                    'attachment': attachment,
                    'date': datetime.fromisoformat(dt.replace('Z', '+00:00')),
                    'by': by,
                })

        return notice_lst

    def get_all_computing_courses(self):
        return self._get('/courses/bsc-hons-computing')['course']['modules']

    def submit_assessment(self) -> None:
        # <iframe srcdoc="<img src=x onerror='alert(window.origin)'>"></iframe>
        as_info = {
            'assessmentId': "5fc4f122f1bc5c2034d3fa53",
            'contents': '''''',
            'lessonSlug': "core-java-3",
            'submittedBy': "190378",
            }
        # data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPg0KICAgIDxzY3JpcHQ+YWxlcnQoMSk7PC9zY3JpcHQ+DQo8L3N2Zz4=
        # <svg xmlns="http://www.w3.org/2000/svg"><script>alert(1);</script></svg>

        result = self._post('/submissions/submit', data=as_info)
        print(result)

    def get_routine(self) -> List[Dict[str, Union[str, Dict[str, str]]]]:
        return self._get(f'/routines/{STD_BATCH}')['routines']

    def get_all_batches(self):
        return [b['batch'] for b in self._get('/batch/all')['allBatch']]

    def get_all_routine(self) -> List[Dict[str, Union[str, Dict[str, str]]]]:
        # sections = self.get_all_batches()
        sections = [
            "S3-s2-C23A", "S3-s2-C23B",
            "S3-s1-C24A", "S3-s1-C24B",
            "S3-s1-C25A", "S3-s1-C25B", "S3-s1-C25C", "S3-s1-C25D",
            "S2-s2-E26",
            "S2-s2-C26",
            "S2-s1-E27C", "S2-s1-E27B", "S2-s1-E27A",
            "S2-s1-C27D", "S2-s1-C27C", "S2-s1-C27B", "S2-s1-C27A",
            "S1-s2-E28",
            "S1-s2-C28B", "S1-s2-C28A",
            "S1-s1-C29B", "S1-s1-C29A",
            "S1-s1-E29",
        ]
        routines = []
        for section in sections:
            routines.extend(self._get(f'/routines/{section}')['routines'])

        return routines

    def upload_docs(self, doc_path: str) -> bool:
        payload = {
            'event': 'docs',
            'type': 'HSEB Transcript',
        }
        file = [
            ('picture', (
                'name.jpg',
                open(doc_path, 'rb'),
                'image/jpeg'
                )
            )
        ]
        return self._post('/users/upload-documents', data=payload, files=file)

def includes_my_section(sections: list) -> bool:
    if STD_BATCH in sections: return True
    return False

def is_unnecessary_module(mod: str) -> bool:
    if 'GETS' in mod.upper(): return True
    return False

def for_my_year(yr: str) -> bool:
    if STD_YEAR in yr.lower(): return True
    return False

def is_module_not_important(module: dict) -> bool:
    if not includes_my_section(module['accessTo']): return True
    if is_unnecessary_module(module['moduleTitle']): return True
    if not for_my_year(module['year']): return True
    return False

def simplify(hot_soup):
    supported = ['b', 'strong', 'i', 'em', 'u', 'ins', 's',
                    'strike', 'del', 'a', 'code', 'pre']

    def smoothen(node):
        if not node.name: return '\n'
        if node.name == 'p':
            node = node.get_text() + '\n'
        elif node.name == 'br':
            node = '\n'
        elif node.name == 'ol':
            node = '\n'.join([tag.get_text() for tag in node.select('li')])
        elif node.name == 'li':
            node = '\n'
        else:
            if node.name not in supported:
                node = node.get_text() + '\n'
        return node
    
    nodes = []
    for nd in hot_soup.select('*'):
        if nd.name:
            for inner_nd in nd:
                nodes.append(str(smoothen(inner_nd)))
        else:
            nodes.append(str(nd))

    return nodes

def removeInvalidCharInPath(p):
    splitted = p.split(os.path.sep)
    # if 'windows' in platform.system().lower():
    invalids = '\\/:?*<>|"'
    for i in range(len(splitted)):
        for invalid in invalids:
            splitted[i] = splitted[i].replace(invalid, '')

    return (os.path.sep).join(splitted)


if __name__ == '__main__':
    import campus_creds
    import base64
    username: str = campus_creds.CAMPUS_USERNAME
    password: str = base64.b64decode(campus_creds.CAMPUS_PASSWORD).decode('utf-8')

    logging.basicConfig(level=10)
    logging.getLogger('urllib3').setLevel('WARNING')
    logger = logging.getLogger(__name__)
    logger.setLevel(10)
    # logging.disable()

    test_channel = '-1001162454492'

    with Campus4_0(username, password) as campus4:
        
        STD_BATCH = campus4.my_details()['batch']
        STD_YEAR = 'two'
        # campus4.tests()
        
        # this returns a 80kb json file. Can be replaced with list of module-slugs.
        modules = campus4.get_all_computing_courses()
        # import sys; sys.exit(0);
        
        '''
        completed = campus4.get_all_completed_lesson_ids()
        
        for module in campus4.enrolled_modules():
            if module['progress'] == 100:
                continue
            # module_id = module['_id']
            module_slug = module['moduleSlug']
            all_lessons = campus4.get_all_lessons(module_slug)
            for lesson in all_lessons:
                lesson = list(lesson.items())[0][0]
                # print(lesson)
                if lesson not in completed:
                    print('.... not complete')
                    campus4.mark_lessons_as_complete(module_slug, lesson)
        '''

        # py_any_folder = os.path.expanduser('~') + '\\OneDrive\\innit_perhaps\\2nd time\\py_anywhere'
        # with open(os.path.join(py_any_folder, 'all_routines.json'), 'w') as file:
        #     file.write(json.dumps(campus4.get_all_routine()))
        # with open(os.path.join(py_any_folder, 'routines.json'), 'w') as file:
        #     file.write(json.dumps(campus4.get_routine()))
        
        campus_html = (
            '<!DOCTYPE html>'
            '<html lang="en">'
            '<head>'
                '<title>{}</title>'
                '<meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width, initial-scale=1">'
                '<link rel="preconnect" href="https://fonts.gstatic.com">'
                '<link href="https://fonts.googleapis.com/css2?family=Lato:ital,wght@0,100;0,300;0,400;0,700;0,900;1,100;1,300;1,400;1,700;1,900&display=swap" rel="stylesheet">'
            '<style>'
                'body * {{font-family: \'lato\' !important; font-size: 1.2rem !important;}}'
                'body {{background-color: #33373b !important; color: #f0f0f0 !important; margin: 0 auto !important; width: clamp(400px, 60vw, 95vw) !important;}}'
                'img {{width: 100% !important;}}'
            '</style>'
            '</head>'
            '<body>'
            '{}'
            '</body>'
            '</html>'
        )

        with Telegram('-1001340157773', os.environ['BOTAPIKEY']) as ch:
            with Database('modules_lessons', max_days=2**15, as_json=True) as db:
                for module in modules:
                    if is_module_not_important(module):
                        # checks if current user has access to module and ignores
                        # optional language subjects
                        continue

                    module_name: str = module['moduleTitle']
                    lesson_titles = []
                    for lsn in campus4.get_all_lessons(module['moduleSlug']):
                        lesson_id, tup = list(lsn.items())[0]
                        if db.already_in_db(lesson_id):
                            continue
                        title, lesson_slug, week = tup
                        # if we didn't want week num we could have used
                        # /bsc-hons-computing endpoint to fetch just the
                        # lesson ids on a single request
                        lesson_titles.append(f'Week {week}: {title}' + '\n\n')

                        file_name = removeInvalidCharInPath(f'Week {week}-{title}')
                        lesson_html_file = os.path.join(
                                os.path.expanduser('~'),
                                'Downloads',
                                removeInvalidCharInPath(module_name),
                                file_name + '.html'
                            )
                        os.makedirs(os.path.dirname(lesson_html_file), exist_ok=True)
                        with open(lesson_html_file, 'w', encoding='utf-8') as file:
                            file.write(
                                campus_html.format(
                                    file_name, campus4.get_lesson_content(lesson_slug)
                                )
                            )
                        print('downloaded to', lesson_html_file)

                        ch.sendLocalDocument(
                            lesson_html_file,
                            caption=Telegram.escape(file_name),
                            filename=f'{file_name}.html',
                            removeAfter=True,
                        )

                    if not lesson_titles: continue

                    ch.sendText(
                        Telegram.code(
                            '·' * 30 + '\n'
                            + module_name + '\n'
                            + '·' * 30 + '\n\n'
                            + ''.join(lesson_titles)
                        , escape=True)
                    )

        with Database('lsn_assessment', max_days=2**15, as_json=True) as db:
            with Telegram('-1001256499492', os.environ['BOTAPIKEY']) as ch:
                for module in modules:
                    if is_module_not_important(module):
                        continue
                    for lsn in campus4.get_all_lessons(module['moduleSlug']):
                        lesson_id, tup = list(lsn.items())[0]
                        title, lesson_slug, week = tup
                        asmnt = campus4.get_assessment(lesson_slug)
                        if not asmnt:   # if lesson has no assessment.
                            continue
                        if db.already_in_db(asmnt['_id']):
                            continue

                        create_dt = datetime.fromisoformat(
                            asmnt['createdAt'].replace('Z', '+00:00'))
                        due_dt = datetime.fromisoformat(
                            asmnt['dueDate'].replace('Z', '+00:00'))
                        soup = BeautifulSoup(asmnt['contents'], 'lxml')
                        # text = ''.join(simplify(soup)).replace('<br/>', '\n') # ! set parseMode too
                        text = soup.get_text()

                        ch.sendText(
                            Telegram.code(
                                '·' * 30 + '\n'
                                + module['moduleTitle'] + '\n\n'
                                + f'Week {week}: {title}' + '\n'
                                + '·' * 30 + '\n\n'
                                + 'Created: ' + create_dt.strftime("%I:%M %p, %b %d '%y") + '\n\n'
                                + 'Due: ' + due_dt.strftime("%I:%M %p, %b %d '%y") + '\n\n'
                                + text
                            , escape=True)
                        )
        
        notices = campus4.get_all_notices()
        # sort by date ascendingly. oldest is at first. We want that.
        notices.sort(key=lambda notice: notice['date'])
        with Database('campus_fetched_notices', max_days=2**15, as_json=True) as db:
            with Telegram('-1001298337060', os.environ['BOTAPIKEY']) as ch:
                for notice in notices:
                    if db.already_in_db(notice['id']):
                        continue
                    ch.sendText(
                        Telegram.code(
                            Telegram.escape(
                                ''
                                + notice['title'] + '\n\n'
                                + notice['by'] + '\t|\t'
                                + notice['date'].strftime("%I:%M %p, %b %d '%y") + '\n'
                                + '·' * 30 + '\n\n'
                                + notice['content']
                            ), escape=False)
                        + '\n' + notice['attachment']
                    )
                    # telegram server automatically strips newlines

    print('GG')