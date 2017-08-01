from datetime import timedelta

SCALES = [
    ('seconds', timedelta(seconds=1)),
    ('minutes', timedelta(minutes=1)),
    ('hours', timedelta(hours=1)),
    ('days', timedelta(days=1)),
    ('months', timedelta(days=30)),
    ('years', timedelta(days=365)),
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
                return timedelta(seconds=1)

            for m in scales:
                if getattr(self, attrname) % m == timedelta(0):
                    return m

            return timedelta(seconds=1)

        @scale.setter
        def scale(self, value):
            if(type(value) != timedelta):
                value = timedelta(seconds=float(value))
            setattr(self, attrname, getattr(self, sig_name) * value)

        @property
        def significand(self):
            return int(getattr(self, attrname) / getattr(self, scl_name))

        @significand.setter
        def significand(self, value):
            setattr(self, attrname, int(value) * getattr(self, scl_name))


        setattr(cls, scl_name, scale)
        setattr(cls, sig_name, significand)

        return cls

    return decorator
