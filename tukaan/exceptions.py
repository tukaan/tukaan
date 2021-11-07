class TclError(Exception):
    ...


class ColorError(Exception):
    ...


class FontError(Exception):
    ...


class LayoutError(Exception):
    ...


class CellNotFoundError(LayoutError):
    ...
