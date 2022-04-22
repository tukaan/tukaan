from __future__ import annotations


class Time:
    def __init__(self, *args, **kwargs):
        if args and not kwargs:
            if len(args) == 3:
                h, m, s = args
                if s is None and m is None:  # comes from a slice
                    h, m, s = 0, 0, h
                elif s is None:
                    h, m, s = 0, h, m
            elif len(args) == 2:
                h, m, s = 0, *args
            elif len(args) == 1:
                h, m, s = 0, 0, args[0]
        elif kwargs and not args:
            h = kwargs.pop("hours", 0)
            m = kwargs.pop("minutes", 0)
            s = kwargs.pop("seconds", 0)
        else:
            raise ValueError

        if s >= 60:
            plus_m, s = divmod(s, 60)
            m += plus_m
        if m >= 60:
            plus_h, m = divmod(m, 60)
            h += plus_h

        self.hours = int(h)
        self.minutes = int(m)
        self.seconds = s

    def __repr__(self):
        time_values = [self.hours, self.minutes, self.seconds]
        if not time_values[0]:
            del time_values[0]

        return f"Time[{':'.join(map(str, time_values))}]"

    @property
    def total_seconds(self):
        return self.hours * 3600 + self.minutes * 60 + self.seconds


class _TimeConstructor:
    def __getitem__(self, key):
        if isinstance(key, slice):
            return Time(key.start, key.stop, key.step)
        elif isinstance(key, (int, float)):
            return Time(seconds=key)

    def __call__(self, *args, **kwargs):
        return Time(*args, **kwargs)

    def __instancecheck__(self, other):
        return isinstance(other, (_TimeConstructor, Time))

    def __repr__(self):
        return "<tukaan.Time; usage: Time[h:min:sec] or Time(h, min, sec)>"

    @staticmethod
    def from_secs(seconds: int):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return Time(h, m, s)


TimeConstructor = _TimeConstructor()
