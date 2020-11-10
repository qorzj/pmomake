from datetime import datetime as Datetime
from unittest import TestCase
from pmo.datetime_util import IDatetime


class DatetimeUtilTest(TestCase):
    def test_day_to_next(self):
        datetime = Datetime(2020, 11, 1, 15, 30, 0)
        datetime = IDatetime.day_to_next(datetime)
        self.assertEqual(str(datetime), '2020-11-02 11:30:00')

    def test_add(self):
        datetime = Datetime(2020, 11, 2, 11, 30, 0)
        datetime = IDatetime.add(datetime, minutes=90)
        self.assertEqual(str(datetime), '2020-11-02 13:00:00')
        datetime = IDatetime.add(datetime, minutes=90)
        self.assertEqual(str(datetime), '2020-11-03 10:30:00')
