# flake8: noqa
from datetime import timedelta
from statistics import mean

SCALES = [
    ('minutes', timedelta(minutes=1)),
    ('hours', timedelta(hours=1)),
    ('days', timedelta(days=1)),
    ('weeks', timedelta(days=7)),
    ('months', timedelta(days=
    # you, a fool: a month is 30 days
    # me, wise:
        mean((31,
            mean((29 if year % 400 == 0
                        or (year % 100 != 0 and year % 4 == 0)
                    else 28
                    for year in range(400)))
            ,31,30,31,30,31,31,30,31,30,31))
        )),
    ('years', timedelta(days=
    # you, a fool: ok. a year is 365.25 days. happy?
    # me, wise: absolutely not
        mean((366 if year % 400 == 0
                or (year % 100 != 0 and year % 4 == 0)
            else 365
            for year in range(400)))
        )),
]

