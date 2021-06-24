from datetime import datetime as Datetime
from datetime import date as Date
from datetime import timedelta as Timedelta
import re
from typing import Protocol, Dict


class IDatetime(Protocol):
    hours_of_day: int = 4  # 一天工作日包含多少工作小时
    predict_minutes: int = 0  # 预警时间
    holiday_exclude_days = ''  # 节假日排除的日期
    holiday_include_days = ''  # 节假日包含的日期

    @classmethod
    def load_options(cls, options: Dict):
        if 'day' in options:
            day_hours_opt = options['day']
            assert day_hours_opt.endswith('h')
            cls.hours_of_day = int(day_hours_opt.rstrip('h'))
        if 'predict' in options:
            predict_opt = options['predict']
            cls.predict_minutes = cls.minute_of_str(predict_opt)
        if 'exclude' in options:
            cls.holiday_exclude_days = options['exclude']
        if 'include' in options:
            cls.holiday_include_days = options['include']

    @classmethod
    def is_holiday(cls, date: Date):
        is_weekend = 5 <= date.weekday() <= 6
        date_str = str(date)
        return (is_weekend and date_str not in cls.holiday_exclude_days) or date_str in cls.holiday_include_days

    @classmethod
    def noon(cls, datetime: Datetime) -> Datetime:
        return datetime.replace(hour=12, minute=0, second=0, microsecond=0)

    @classmethod
    def day_begin(cls, datetime: Datetime) -> Datetime:
        return cls.noon(datetime) - Timedelta(minutes=cls.hours_of_day * 60 / 2)

    @classmethod
    def day_end(cls, datetime: Datetime) -> Datetime:
        return cls.noon(datetime) + Timedelta(minutes=cls.hours_of_day * 60 / 2)

    @classmethod
    def day_to_next(cls, datetime: Datetime) -> Datetime:
        if datetime < cls.day_begin(datetime):
            return cls.day_begin(datetime)  # 基本不会使用，无效过多处理
        if datetime <= cls.day_end(datetime):
            return datetime
        left_minute = (datetime - cls.day_end(datetime)).seconds // 60
        tomorrow_begin = cls.day_begin(datetime) + Timedelta(days=1)
        return cls.add(tomorrow_begin, minutes=left_minute)

    @classmethod
    def skip_holiday(cls, datetime: Datetime, *, days: int) -> Datetime:
        date = datetime.date()
        if cls.is_holiday(date):
            return cls.skip_holiday(datetime + Timedelta(days=1), days=days)
        elif days <= 0:
            return datetime
        else:
            return cls.skip_holiday(datetime + Timedelta(days=1), days=days - 1)

    @classmethod
    def add(cls, datetime: Datetime, *, minutes: int) -> Datetime:
        if datetime < cls.day_begin(datetime):
            datetime = cls.day_begin(datetime)
        elif datetime > cls.day_end(datetime):
            datetime = cls.day_end(datetime)
        day_num, left_minute = minutes // (cls.hours_of_day * 60), minutes % (cls.hours_of_day * 60)
        next_day = cls.skip_holiday(datetime, days=day_num)
        return cls.day_to_next(next_day + Timedelta(minutes=left_minute))

    @classmethod
    def noon_of_str(cls, date_str: str) -> Datetime:
        day = Date.fromisoformat(date_str)
        return Datetime(day.year, day.month, day.day, 12, 0, 0)

    @classmethod
    def minute_of_str(cls, time_str: str) -> int:
        if re.match(r'^\d+d$', time_str):
            return int(time_str[:-1]) * cls.hours_of_day * 60
        if re.match(r'^\d+\.5d$', time_str):
            return int(time_str[:-3]) * cls.hours_of_day * 60 + 30
        if re.match(r'^\d+h$', time_str):
            return int(time_str[:-1]) * 60
        return 0
