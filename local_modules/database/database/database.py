import os
import json
import shelve
import logging
import platform
from typing import Union
from datetime import timedelta, datetime

logger = logging.getLogger(__name__)


class IterableDatabase(type):

    _dbs = set()

    def __iter__(cls):
        return cls

    def __next__(cls):
        try:
            return cls._dbs.pop()
        except KeyError:
            raise StopIteration

    def add_dbs(cls, db_name, as_json):
        if as_json: cls._dbs.add(db_name + '.json')
        else: cls._dbs.add(db_name)


class Database(metaclass=IterableDatabase):

    file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'db')

    @staticmethod
    def file_empty(path_to_file):
        # assuming parent directory already exists
        if not os.path.exists(path_to_file):
            # return FileNotFoundError
            with open(path_to_file, 'w') as f:
                pass
        with open(path_to_file) as f:
            return f.read(1) == ''

    @staticmethod
    def store_default_value(default_value, path_to_file):
        '''for txt file'''
        os.makedirs(os.path.dirname(path_to_file), exist_ok=True)
        with open(path_to_file, 'w') as f:
            f.write(str(default_value))
        return True    

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.shelf.close()    
        return

    def __init__(self, db_name: str = 'auto_created_db', max_days: int = 7, as_json: bool = False):
        self.max_days = max_days
        self.db_name = db_name
        self.as_json = as_json

        os.makedirs(self.file_path, exist_ok=True)
        if self.db_name not in self.__class__._dbs:
            self.__class__.add_dbs(self.db_name, as_json=self.as_json)

        if self.as_json:
            json_file_path = os.path.join(self.file_path, self.db_name + '.json')
            if not os.path.exists(json_file_path) or not os.stat(json_file_path).st_size:
                Database.store_default_value('{}', json_file_path)
            self.shelf = open(json_file_path, 'a+')
        else:
            self.shelf = shelve.open(os.path.join(self.file_path, self.db_name))

    def already_in_db(
            self,
            unq_id: Union[str, int],
            ts_or_date_obj: Union[int, datetime] = datetime.now().timestamp()):
        try:
            ts_or_date_obj = int(ts_or_date_obj)
        except TypeError:
            ts_or_date_obj = ts_or_date_obj.timestamp()
        str_unq_id = str(unq_id)
        # logger.debug('=' * 7, 'ALREADY SENT', '=' * 7)
        # .fromtimestamp() returns local time. if tz is given, 
        # timestamp is converted to tz’s time zone.
        # eg: datetime.fromtimestamp(timestamp, timezone.utc) -> current UTC time
        
        # if not ts_or_date_obj:
        #     if self.as_json:
        #         self.shelf.seek(0)  # always seek to 0, cuz .read() below seeks to eof
        #         d = json.loads(self.shelf.read()).setdefault('tbl', [])
        #     else:
        #         d = self.shelf.setdefault('tbl', [])
            
        #     if str_unq_id in d: return True
        #     d.append(str_unq_id)
        # else:
        if self.as_json:
            self.shelf.seek(0)  # always seek to 0, cuz below .read() seeks to eof
            bytes_present = self.shelf.read()
            d = json.loads(bytes_present).setdefault('tbl', {})
        else:
            d = self.shelf.setdefault('tbl', {})
        
        if str_unq_id in d.keys(): return True
        d.update(
        {
            str_unq_id: {
                'creation': ts_or_date_obj,
                'expiration': ts_or_date_obj
                            + timedelta(days=self.max_days).total_seconds()
            }
        })

        if self.as_json:
            self.shelf.seek(0)
            self.shelf.truncate()
            self.shelf.write(json.dumps({'tbl': d}))
        else:
            self.shelf['tbl'] = d

        return False


def check_db_once_every_day():
    '''Every day check all dbs for expired urls/ids. if so, delete.'''

    def isFileEmpty(p):
        if not os.path.exists(p):
            # return FileNotFoundError
            with open(p, 'w') as f:
                pass
        with open(p) as f:
            return f.read(1) == ''
    
    def storeDefaultValue(defaultValue, fullFilePath):
        '''for txt file'''
        os.makedirs(os.path.dirname(fullFilePath), exist_ok=True)
        with open(fullFilePath, 'w') as f:
            f.write(str(defaultValue))
        return True
    
    logger.debug('Is it time to check Database?')
    tomorrowFile = os.path.join(Database.file_path, 'tomorrows_time.txt')

    # os.path.exists() will return false if python has inadequate permission
    if not os.path.exists(tomorrowFile): storeDefaultValue(0, tomorrowFile)

    with open(tomorrowFile) as file: timeInFile = int(float(file.read().strip()))

    if datetime.now().timestamp() > timeInFile:
        logger.debug('It is Time to check Database')
        # time to check for expiration
        for db in Database:
            logger.debug(f'Checking: {db} ....')
            file_path = os.path.join(Database.file_path, db)
            if 'windows' in platform.system().lower():
                if (not os.path.exists(file_path)
                    and not os.path.exists(file_path + '.dat')):
                    continue
            if 'linux' in platform.system().lower():
                if not os.path.exists(file_path): continue
            try:
                if db.endswith('.json'):
                    f = open(file_path, 'r+')
                    try: d = json.loads(f.read())['tbl']
                    except KeyError: continue
                else:
                    f = shelve.open(file_path)
                    if 'tbl' not in f.keys(): continue
                    d = dict(f['tbl'])

                copyDict = {**d}
                for k, v in d.items():
                    if v['expiration'] < datetime.now().timestamp():
                        # remove url from dictionary
                        logger.debug("%s has expired. removing it", k)
                        copyDict.pop(k)

                if db.endswith('.json'):
                    f.seek(0)
                    f.truncate()
                    f.write(json.dumps({'tbl': copyDict}))
                else: f['tbl'] = copyDict
            finally:
                f.close()

        tomorrow = (datetime.now() + timedelta(days=1)).timestamp()
        storeDefaultValue(tomorrow, tomorrowFile)


if __name__ == '__main__':
    import time
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    with Database('test', as_json=True) as db:
        if db.already_in_db(104124, time.time()):
            print('already')
        if db.already_in_db('vbrrrrrrrrrrrrrrrr'):
            print('already')
        if db.already_in_db(104124, time.time()):
            print('already')
        if db.already_in_db(10, time.time()):
            print('already')
        if db.already_in_db(20, time.time()):
            print('already')
        if db.already_in_db(20, time.time()):
            print('already')
    print('-'*8)
    with Database('test', as_json=False) as db:
        if db.already_in_db(104124, time.time()):
            print('already')
        if db.already_in_db(104124, time.time()):
            print('already')
        if db.already_in_db(10, time.time()):
            print('already')
        if db.already_in_db(20, time.time()):
            print('already')
        if db.already_in_db(20, time.time()):
            print('already')

    check_db_once_every_day()

    print('gg')
