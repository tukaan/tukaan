class TukaanTclError(Exception):
    ...


class AppError(Exception):
    ...


class WidgetError(Exception):
    ...


class ColorError(Exception):
    ...


class FontError(Exception):
    ...


class LayoutError(Exception):
    ...


class CellNotFoundError(LayoutError):
    ...
