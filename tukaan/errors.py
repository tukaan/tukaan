class AppAlreadyExistsError(Exception):
    def __init__(self, *args):
        super().__init__("cannot create multiple `App` instances in one process. App already exists.")


class AppDoesNotExistError(Exception):
    ...


class MainWindowAlreadyExistsError(Exception):
    ...


class TclCallError(Exception):
    ...
