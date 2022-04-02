from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from tukaan._tcl import Tcl

from .theme import Theme


@dataclass
class ThemeContainer:
    name: str
    parent_theme: str
    image_resource_path: Path
    rules: dict[tuple[str, ...], dict[str, str]]


class CssThemeParser:
    bundle_re = re.compile(r"([a-z*:,]*\s*){(.*?)}")
    comment_re = re.compile(r"/\*.*?\*/")
    parent_re = re.compile(r"@parent\(['|\"](.*?)['|\"]\);")
    property_re = re.compile(r"([a-z-]*):\s*(.*)")
    rule_re = re.compile(r"[^{; ]+:[^};]+")
    source_re = re.compile(r"@source\(['|\"](.*?)['|\"]\);")
    variables_re = re.compile(r"\$([a-z-]*):\s*(.*?);")

    @classmethod
    def read_file(cls, path: Path) -> str:
        with open(path, "r") as file:
            return str(file.read())

    @classmethod
    def cleanup(cls, file_content: str) -> str:
        cleaned = file_content.replace("\n", "").replace("\t", "")
        for comment in re.findall(cls.comment_re, cleaned):
            cleaned = cleaned.replace(comment, "")

        return cleaned

    @classmethod
    def get_parent_theme(cls, css_theme_str: str) -> str:
        parent_list = re.findall(cls.parent_re, css_theme_str)
        if parent_list:
            return parent_list[-1]

        return "clam"

    @classmethod
    def get_image_resource_paths(cls, css_theme_str: str) -> Path:
        result = re.findall(cls.source_re, css_theme_str)
        return Path(result[-1]).resolve()

    @classmethod
    def get_variables(cls, css_theme_str: str) -> dict[str, str]:
        result = re.findall(cls.variables_re, css_theme_str)
        variables_dict = {}
        for var_key_value in result:
            variables_dict[var_key_value[0]] = var_key_value[1]

        return variables_dict

    @classmethod
    def parse_bundle(cls, selectors_rules_list: list[str]) -> dict[str, str]:
        splitted_rules = re.findall(cls.rule_re, selectors_rules_list[1])
        rules_dict = {}
        for property_ in splitted_rules:
            key, value = re.findall(cls.property_re, property_)[0]
            rules_dict[key] = value

        selectors = tuple(selectors_rules_list[0].strip().split(","))

        return selectors, rules_dict

    @classmethod
    def get_rules(cls, css_theme_str: str) -> dict[str, dict[str, dict[str, str]]]:
        result: dict[str, dict[str, dict[str, str]]] = {}
        for bundle in re.findall(cls.bundle_re, css_theme_str):
            selectors, rules_dict = cls.parse_bundle(bundle)
            for selector in selectors:
                element, *other = selector.split(":")
                if element not in result:
                    result[element] = {}

                if element == selector:
                    result[element]["rest"] = rules_dict
                else:
                    result[element][":".join(filter(bool, other))] = rules_dict

        return result

    @classmethod
    def load(cls, filename: Path) -> ThemeContainer:
        file_content = cls.cleanup(cls.read_file(filename))
        parent = cls.get_parent_theme(file_content)
        img_res_path = cls.get_image_resource_paths(file_content)
        rules_dict = cls.get_rules(file_content)

        return ThemeContainer(filename.stem, parent, img_res_path, rules_dict)


class TclThemeGenerator:
    def __init__(self, info: ThemeContainer) -> None:
        self.info = info

    def generate(self) -> str:
        return ""

    def generate_theme_use(self) -> str:
        return ""


class CssTheme(Theme):
    def __init__(self, file_path: Path):
        css_theme_info = CssThemeParser.load(file_path)
        tcl_theme_generator = TclThemeGenerator(css_theme_info)

        Tcl.eval(None, tcl_theme_generator.generate())

        self._script = tcl_theme_generator.generate_theme_use()
        self._name = css_theme_info.name
        self._path = file_path

    def _set_theme(self):
        Tcl.eval(None, self._script)

    def __repr__(self) -> str:
        return f"<tukaan.themes.CssTheme {self._name!r}: path={self._path!r}>"
