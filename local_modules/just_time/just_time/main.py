from __future__ import annotations
from typing import Dict, Union
from datetime import time, timedelta, timezone, tzinfo


class JustTime:

    def __init__(self,
        hour: int = 0, minute: int = 0, second: int = 0, microsecond: int = 0,
        tzinfo: tzinfo = timezone.utc):
        '''JustTime allows representing time greater than 24hrs.
        If time is greater than 24hrs then only the hour will increase past its
        normal limit of <=23. Minute, second, and microsecond remain under their
        limit.
        Supports addition and substraction with other JustTime, time and timedelta object.

        You can also convert seconds to HH:MM:SS format by specifying just the
        :param:seconds
        '''

        self._total_microseconds: int = (hour * 3600 + minute * 60 + second) * (10 ** 6) + microsecond
        self._total_seconds: int = self._total_microseconds * (10 ** -6)
        rem = self._total_microseconds % (3600 * 10 ** 6)
        hh = self._total_microseconds // (3600 * 10 ** 6)
        mm = rem // (60 * 10 ** 6)
        ss = rem % (60 * 10 ** 6) // (10 ** 6)
        self._hour: int = hh
        self._minute: int = mm
        self._second: int = ss
        self._microsecond: int = self._total_microseconds % (10 ** 6)

    @property
    def hour(self) -> int:
        "[-inf, +inf]"
        return self._hour

    @property
    def minute(self) -> int:
        "[-inf, +59]"
        return self._minute
    
    @property
    def second(self) -> int:
        "[-inf, +59]"
        return self._second
    
    @property
    def microsecond(self):
        "[-inf, +1_000_000]"
        return self._microsecond
    
    def __str__(self) -> str:
        # 02, max width=2. precede with 0s if width < 2
        return f'{self.hour:02}:{self.minute:02}:{self.second:02}:{self.microsecond:06}'

    def __repr__(self) -> str:
        return f'JustTime({self.hour}, {self.minute}, {self.second}, {self.microsecond})'

    def __lt__(self, other) -> bool:
        if isinstance(other, (JustTime, time)):
            other = JustTime(other.hour, other.minute, other.second, other.microsecond)
        return self.total_seconds() < other.total_seconds()

    def __gt__(self, other) -> bool:
        if isinstance(other, (JustTime, time)):
            other = JustTime(other.hour, other.minute, other.second, other.microsecond)
        return self.total_seconds() > other.total_seconds()

    def __eq__(self, other) -> bool:
        if isinstance(other, (JustTime, time)):
            other = JustTime(other.hour, other.minute, other.second, other.microsecond)
        return self.total_seconds() == other.total_seconds()

    def __le__(self, other) -> bool:
        return self.__lt__(other) or self.__eq__(other)

    def __ge__(self, other) -> bool:
        return self.__gt__(other) or self.__eq__(other)      
               
    def __add__(self, other) -> JustTime:
        "TODO support tzinfo"
        other_obj: Union[time, JustTime]
        if isinstance(other, (time, JustTime)):
            other_obj = other
        elif isinstance(other, timedelta):
            other_obj = JustTime(second=int(other.total_seconds()))
        else:
            return NotImplemented

        return JustTime(
            hour=self.hour+other_obj.hour,
            minute=self.minute+other_obj.minute,
            second=self.second+other_obj.second,
            microsecond=self.microsecond+other_obj.microsecond,
        )

    def __sub__(self, other) -> Union[timedelta, JustTime]:
        # t-t -> delta
        # t-delta -> t
        "TODO support tzinfo"
        other_obj: Union[time, JustTime]
        if isinstance(other, (time, JustTime)):
            # return timedelta(seconds=self.total_seconds()-int(other.total_seconds()))
            return timedelta(
                hours=self.hour-other.hour,
                minutes=self.minute-other.minute,
                seconds=self.second-other.second,
                microseconds=self.microsecond-other.microsecond,
            )
        elif isinstance(other, timedelta):
            # return JustTime(second=self.total_seconds()-int(other.total_seconds()))
            other_obj = JustTime(second=int(other.total_seconds()))
            return JustTime(
                hour=self.hour-other_obj.hour,
                minute=self.minute-other_obj.minute,
                second=self.second-other_obj.second,
                microsecond=self.microsecond-other_obj.microsecond,
            )
        else:
            return NotImplemented

    def strftime(self, str_f: str) -> str:
        frmt_info: Dict[str, str] = {
            'H': f'{self.hour:02}',
            'I': f'{self.hour % 12:02}' if self.hour > 12 else f'{self.hour:02}',
            'p': 'AM' if self.hour < 12 else 'PM',
            'M': f'{self.minute:02}',
            'S': f'{self.second:02}',
            'f': f'{self.microsecond:06}'
        }
        # translation: Dict[int, int] = str.maketrans(frmt_info)
        for character in frmt_info:
            # str_f = str_f.replace('%' + character, translation[ord(character)])
            str_f = str_f.replace('%' + character, frmt_info[character])
        
        return str_f

    def total_seconds(self) -> float:
        return self._total_seconds

    def total_microseconds(self) -> int:
        return self._total_microseconds

    def lies_between(self, starting, ending) -> bool:
        if self.total_microseconds() in range(
                starting.total_microseconds(), ending.total_microseconds()
            ):
            return True
        else:
            return False


if __name__ == '__main__':

    t1 = JustTime(1, 0, 0, 66_000_000)
    t2 = JustTime(23, 59, 59)
    print(t1.strftime('%I:%M %p'))
    print(t2.strftime('%I:%M %p'))
    print(t2)
    # print(t1.hour)
    # print(t1.minute)
    # print(t1.second)
    # print(t1.total_seconds())

    # print(t1 + t2)
    # print(t1 - t2)
    # print(t2 - t1)
    # d1 = timedelta(hours=3, minutes=5)
    # print(t1 + d1)
    # print(t1 - d1)
    t3 = JustTime(0,0,2,4_000_100)
    t4 = JustTime(0,0,2,1_001_300)
    # print(t3._total_microseconds)
    print(t3 + t4)
    print(t3 - t4)
    print(t4 - t3)
    print(t4 <= t3)
    # print(t3.total_seconds())
    # print(t3.hour)
    # print(t1.sec_to_HH_MM_SS(86399))
    mine_st = JustTime(9, 0)
    mine_end = JustTime(11, 0)

    # other_st = JustTime(8, 30)
    other_st = JustTime(9, 30)
    # other_end = JustTime(10, 30)
    other_end = JustTime(11, 30)

    # other_st = JustTime(8, 0)
    # other_end = JustTime(8, 40)

    gaps = []
    # st_diff = (other_st - mine_st).total_seconds()
    # end_diff = (mine_end - other_end).total_seconds()
    # if st_diff > 0:
    #     gaps.append((mine_st, other_st))
    # if end_diff > 0:
    #     gaps.append((other_end, mine_end))
    # st_diff = other_st.total_microseconds() - mine_st.total_microseconds()
    # end_diff = mine_end.total_microseconds() - other_end.total_microseconds()

    # first check if starting time lies in range
    if other_st.lies_between(mine_st, mine_end):
        st_diff = range(mine_st.total_microseconds(), other_st.total_microseconds())
        end_diff = range(other_end.total_microseconds(), mine_end.total_microseconds())
        if st_diff:
            gaps.append(st_diff)
        if end_diff:
            if end_diff[-1] - end_diff[0] > mine_st.total_microseconds() - mine_end.total_microseconds():
                gaps.append(range(mine_st.total_microseconds(), mine_end.total_microseconds()))
            else:
                gaps.append(end_diff)

    from pprint import pprint
    # print(gaps)
    # pprint([(JustTime(microsecond=n[0]), JustTime(microsecond=n[-1])) for n in gaps])
    # if other_st.total_microseconds() != mine_st.total_microseconds():


    from typing import List, Tuple

    def bits_to_time_ranges(time_begin: JustTime, bits: str) -> List[Tuple(JustTime, JustTime)]:

        def helper(secs: int): return time_begin + timedelta(seconds=secs)

        time_ranges: List[Tuple(JustTime, JustTime)] = []
        offset: int = 0
        bit_set: bool = False

        for i in range(len(bits)):
            if bits[i] == '1':
                if not bit_set:
                    bit_set = True
                    offset = i
            else:
                if bit_set:
                    bit_set = False
                    time_ranges.append((helper(offset), helper(i)))
        else:
            if bit_set:
                time_ranges.append((helper(offset), helper(i)))

        return time_ranges

    def bitwise_and(p1: str, p2: str) -> str:
        shortest_len: int = len(p1) if len(p1) < len(p2) else len(p2)
        return ''.join([str(int(p1[i]) & int(p2[i])) for i in range(shortest_len)])

    lst = [
        (JustTime(9, 15), JustTime(9, 25)),
        (other_st, other_end),
    ]
    gaps = []
    for other_st, other_end in lst:
        if (not other_st.lies_between(mine_st, mine_end)
            and not other_end.lies_between(mine_st, mine_end)
            ):
            # both ends lie outside the range. No collision.
            continue

        dark_matter_length = 0
        # at most, 1 end is outside the range.
        if (other_st - mine_st).total_seconds() > 0:
            left_diff = int(float((other_st - mine_st).total_seconds()))
        else:
            left_diff = 0
            dark_matter_length = int(float((other_end - mine_st).total_seconds()))

        if (mine_end - other_end).total_seconds() > 0:
            right_diff = int(float((mine_end - other_end).total_seconds()))
        else:
            right_diff = 0
            dark_matter_length = int(float((mine_end - other_st).total_seconds()))

        # print(f'{left_diff=} {right_diff=}')
        if dark_matter_length <= 0:
            dark_matter_length = int(float((other_end - other_st).total_seconds()))
        dark_matter = (
            left_diff * '1'
            # + int(float((other_end - other_st).total_seconds())) * '0'
            + dark_matter_length * '0'
            + right_diff * '1'
        )

        # print(dark_matter,'dark_matter')
        normal_matter = int(float((mine_end - mine_st).total_seconds())) * '1'
        bits: str = bitwise_and(normal_matter, dark_matter)
        # print(bits)
        
        gaps.extend(bits_to_time_ranges(mine_st, bits))

    print(gaps)
    duplicates_removed = []
