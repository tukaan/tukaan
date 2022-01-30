import re
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from ._base import TkWidget
from ._misc import Color
from ._utils import from_tcl, get_tcl_interp, reversed_dict, to_tcl


DND_SEQUENCES = {
    "<<Drop>>": "<<Drop>>",
    "<<Drop:Any>>": "<<Drop:*>>",
    "<<Drop:App>>": "<<Drop:DND_App>>",
    "<<Drop:Color>>": "<<Drop:DND_Color>>",
    "<<Drop:Custom>>": "<<Drop:DND_UserDefined>>",
    "<<Drop:File>>": "<<Drop:DND_Files>>",
    "<<Drop:HTML>>": "<<Drop:DND_HTML>>",
    "<<Drop:RTF>>": "<<Drop:DND_RTF>>",
    "<<Drop:Text>>": "<<Drop:DND_Text>>",
    "<<Drop:URL>>": "<<Drop:DND_URL>>",
    "<<DragEnter>>": "<<DropEnter>>",
    "<<DragLeave>>": "<<DropLeave>>",
    "<<DragMotion>>": "<<DropPosition>>",
    "<<DragEnd>>": "<<DragEndCmd>>",
    "<<DragStart>>": "<<DragInitCmd>>",
}


ALIASES = {
    "app": "DND_App",
    "color": "DND_Color",
    "custom": "DND_UserDefined",
    "file": "DND_Files",
    "html": "DND_HTML",
    "rtf": "DND_RTF",
    "text": "DND_Text",
    "url": "DND_URL",
}

ALL_TYPES = {
    "DND_App",
    "DND_Color",
    "DND_Files",
    "DND_HTML",
    "DND_RTF",
    "DND_Text",
    "DND_URL",
    # tkdnd_macosx.tcl
    "NSPasteboardTypeString",
    "NSFilenamesPboardType",
    "NSPasteboardTypeHTML",
    # tkdnd_windows.tcl
    "CF_UNICODETEXT",
    "CF_TEXT",
    "CF_HDROP",
    "UniformResourceLocator",
    "CF_HTML",
    "HTML Format",
    "CF_RTF",
    "CF_RTFTEXT",
    "Rich Text Format",
    # tkdnd_unix.tcl
    "text/plain\;charset=utf-8",
    "UTF8_STRING",
    "text/plain",
    "text/rtf",
    "text/richtext",
    "STRING",
    "TEXT",
    "COMPOUND_TEXT",
    "text/uri-list",
    "text/html\;charset=utf-8",
    "text/html",
    "application/x-color",
    "application/x-orgkdeplasmataskmanager_taskbuttonitem",
    "text/x-orgkdeplasmataskmanager_taskurl",
    "text/x-orgkdeplasmataskmanager_taskurl",
}

_DND_BINDING_SUBSTS = (
    ("%A", str, "action"),
    ("%L", (str,), "formats"),
    ("%D", str, "data"),
    ("%T", str, "format"),
    (r"%W", TkWidget, "widget"),
    (r"%X", int, "x"),
    (r"%Y", int, "y"),
    ("%CPT", str, "type"),
)


class DragObject:
    def __new__(cls, data, action="copy", type=None):
        type_name = type

        if type_name is None:
            if isinstance(data, str):
                type_name = cls.TEXT
            elif isinstance(data, (Path, tuple, list)):  # List or tuple of Paths
                type_name = cls.FILE
            elif isinstance(data, Color):
                type_name = cls.COLOR
            else:
                raise ValueError("can't detect DnD type automatically. Please specify it!")
        else:
            try:
                type_name = ALIASES[type_name]
            except KeyError:
                pass

        if type_name not in ALL_TYPES:
            get_tcl_interp()._init_tkdnd()
            get_tcl_interp()._tcl_eval(
                None,
                f"lappend tkdnd::generic::_platform2tkdnd {type_name} DND_UserDefined"
                "\n"
                f"lappend tkdnd::generic::_tkdnd2platform [dict get $tkdnd::generic::_platform2tkdnd {type_name}] {type_name}",
            )

        return (action, type, to_tcl(data))


class DnDEvent:
    def __repr__(self) -> str:
        if self.type == "custom":
            more_useful_type_info = f", format={self.format!r}"
        else:
            more_useful_type_info = f", type={self.type!r}"

        return f"<DnDEvent: data={self.data!r}, action={self.action!r}{more_useful_type_info}>"

    def _set_values(self, *args):
        result = {}

        for (_, type_, attr), string_value in zip(_DND_BINDING_SUBSTS, args):
            if string_value == "??":
                value = None
            else:
                value = from_tcl(type_, string_value)

            result[attr] = value

        try:
            cpt = result["type"] = reversed_dict(ALIASES)[result["type"]]
        except KeyError:
            cpt = None

        if cpt == "file":
            data = from_tcl([str], result["data"])

            if len(data) > 1:
                result["data"] = [Path(x) for x in data]
            else:
                result["data"] = Path(data[0])

        elif cpt == "html":
            # search for an image url in the dropped html, and return a PIL.Image.Image object
            regex = re.compile(r'(.*?)<img (.*?)src="(.*?)"(.*?)>(.*?)', re.DOTALL)

            try:
                if re.match(regex, result["data"]):
                    import tempfile

                    import requests

                    path = re.search(regex, result["data"]).group(3)

                    r = requests.get(path)
                    _, name = tempfile.mkstemp()  # TODO: cleanup on quit

                    with open(name, "wb") as file:
                        file.write(r.content)

                    result["data"] = Image.open(name)
            except (requests.exceptions.ConnectionError, UnidentifiedImageError):
                pass

        elif cpt == "color":
            color = "#"
            splitted_color = from_tcl([str], result["data"])

            if len(splitted_color) == 4:
                for i in splitted_color[:3]:
                    color += i[4:]
            else:
                color = result["data"]

            result["data"] = Color(color)

        elif cpt == "custom":
            ord_list = from_tcl([str], result["data"])
            char_tuple = tuple(
                chr(int(x)) for x in ord_list
            )  # faster to int() here than in from_tcl

            result["data"] = "".join(char_tuple)

        for key, value in result.items():
            setattr(self, key, value)

    ignore = lambda self: "refuse_drop"
    move = lambda self: "move"
    copy = lambda self: "copy"
    link = lambda self: "link"
