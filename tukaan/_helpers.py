def convert_4side(to_parse):
    if to_parse is None:
        return None

    elif isinstance(to_parse, int):
        return (to_parse,) * 4

    elif len(to_parse) == 1:
        return to_parse * 4

    elif len(to_parse) == 2:
        return (to_parse[1], to_parse[0], to_parse[1], to_parse[0])

    elif len(to_parse) == 3:
        return (to_parse[1], to_parse[0], to_parse[1], to_parse[2])

    elif len(to_parse) == 4:
        return (to_parse[3], to_parse[0], to_parse[1], to_parse[2])


def convert_4side_back(to_parse):
    if len(to_parse) == 1:
        return (to_parse[0],) * 4

    elif len(to_parse) == 4:
        return (to_parse[1], to_parse[2], to_parse[3], to_parse[0])

    return (0,) * 4
