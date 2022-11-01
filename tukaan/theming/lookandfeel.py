from __future__ import annotations

from tukaan._system import Platform
from tukaan._utils import classproperty


class LookAndFeel:
    _is_current_theme_native: bool = False
    _kreadconfig_available: bool = False

    @classproperty
    def system_theme(cls) -> str | None:
        if Platform.os == "Windows":
            from winreg import HKEY_CURRENT_USER, OpenKey, QueryValueEx

            key_name = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize"

            try:
                reg_key = OpenKey(HKEY_CURRENT_USER, key_name)
                value = QueryValueEx(reg_key, "AppsUseLightTheme")[0]
            except FileNotFoundError:
                # Windows doesn't support dark theme
                return "light"
            else:
                return "light" if value else "dark"
        elif Platform.os == "macOS":
            # TODO: maybe move this to Idared?
            from subprocess import PIPE, Popen

            p = Popen(["defaults", "read", "-g", "AppleInterfaceStyle"], stdout=PIPE, stderr=PIPE)
            return "dark" if "dark" in p.stdout.read().decode().lower() else "light"

        # Linux. Can't be easily determined
        return None
