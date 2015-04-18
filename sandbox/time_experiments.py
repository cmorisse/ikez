# coding: utf-8
__author__ = 'cmorisse'

ch1 = '2015-04-02 09:08:57.068172653 +0200'
ch2 = '2015-04-04 07:08:57.068172653 +0000'
import datetime
import dateutil.parser
from dateutil.tz import tzlocal
from dateutil.relativedelta import relativedelta

ts1 = dateutil.parser.parse(ch1)
print ts1

print dateutil.parser.parse(ch2)
now = datetime.datetime.now(tz=tzlocal())
print now

print relativedelta(now, ts1).hours >= 1

diff = now - ts1
print diff


