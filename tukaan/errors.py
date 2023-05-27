class AppAlreadyExistsError(Exception):
    def __init__(self, *args):
        super().__init__(
            "application context already exists. Can't create more than one in the same program."
        )


class AppDoesNotExistError(Exception):
    ...


class MainWindowAlreadyExistsError(Exception):
    ...


class TclCallError(Exception):
    ...


class WrongWidgetError(Exception):
    ...
