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
                        or year % 100 != 0 and year % 4 == 0
                    else 28
                    for year in range(400)))
            ,31,30,31,30,31,31,30,31,30,31))
        )),
    ('years', timedelta(days=
    # you, a fool: ok. a year is 365.25 days. happy?
    # me, wise: absolutely not
        mean((366 if year % 400 == 0
                or year % 100 != 0 and year % 4 == 0
            else 365
            for year in range(400)))
        )),
]

def decompose_interval(attrname):
    scales = [scale[1] for scale in SCALES]
    scales.reverse()

    def decorator(cls):
        scl_name = '{}_scale'.format(attrname)
        sig_name = '{}_significand'.format(attrname)

        @property
        def scale(self):

            if getattr(self, attrname) == timedelta(0):
                return timedelta(minutes=1)

            for m in scales:
                if getattr(self, attrname) % m == timedelta(0):
                    return m

            return timedelta(minutes=1)

        @scale.setter
        def scale(self, value):
            if(type(value) != timedelta):
                value = timedelta(seconds=float(value))
            setattr(self, attrname, max(1, getattr(self, sig_name)) * value)

        @property
        def significand(self):
            return int(getattr(self, attrname) / getattr(self, scl_name))

        @significand.setter
        def significand(self, value):
            if type(value) == str and value.strip() == '':
                value = 0

            try:
                value = int(value)
                assert value >= 0
            except (ValueError, AssertionError) as e:
                raise ValueError("Incorrect time interval", e)
            setattr(self, attrname, value * getattr(self, scl_name))


        setattr(cls, scl_name, scale)
        setattr(cls, sig_name, significand)

        return cls

    return decorator
