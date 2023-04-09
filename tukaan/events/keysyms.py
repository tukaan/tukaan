from tukaan._system import Platform


class KeySeq:
    ...


KEYSYM_ALIASES = {
    # general
    "Alt_L": "Alt:Left",
    "Alt_R": "Alt:Right",
    "BackSpace": "Backspace",
    "Caps_Lock": "CapsLock",
    "Control_L": "Control:Left",
    "Control_R": "Control:Right",
    "Hyper_L": "Hyper:Left",
    "Hyper_R": "Hyper:Right",
    "Meta_L": "Meta:Left",
    "Meta_R": "Meta:Right",
    "Mode_switch": "ModeSwitch",
    "Next": "PageDown",
    "Num_Lock": "NumLock",
    "Pause": "PauseBreak",
    "Print": "PrintScreen",
    "Prior": "PageUp",
    "Return": "Enter",
    "Scroll_Lock": "ScrollLock",
    "Shift_L": "Shift:Left",
    "Shift_Lock": "ShiftLock",
    "Shift_R": "Shift:Right",
    "Super_L": "Super:Left",
    "Super_R": "Super:Right",
    "Win_L": "Windows:Left",
    "Win_R": "Windows:Right",
    "Kana_Lock": "KanaLock",
    "Kana_Shift": "KanaShift",
    "space": "Space",
    # numpad
    "KP_0": "NumPad:0",
    "KP_1": "NumPad:1",
    "KP_2": "NumPad:2",
    "KP_3": "NumPad:3",
    "KP_4": "NumPad:4",
    "KP_5": "NumPad:5",
    "KP_6": "NumPad:6",
    "KP_7": "NumPad:7",
    "KP_8": "NumPad:8",
    "KP_9": "NumPad:9",
    "KP_Add": "NumPad:Add",
    "KP_Begin": "NumPad:Begin",
    "KP_Decimal": "NumPad:Decimal",
    "KP_Delete": "NumPad:Delete",
    "KP_Divide": "NumPad:Divide",
    "KP_Down": "NumPad:Down",
    "KP_End": "NumPad:End",
    "KP_Enter": "NumPad:Enter",
    "KP_Equal": "NumPad:Equal",
    "KP_F1": "NumPad:F1",
    "KP_F2": "NumPad:F2",
    "KP_F3": "NumPad:F3",
    "KP_F4": "NumPad:F4",
    "KP_Home": "NumPad:Home",
    "KP_Insert": "NumPad:Insert",
    "KP_Left": "NumPad:Left",
    "KP_Multiply": "NumPad:Multiply",
    "KP_Next": "NumPad:PageDown",
    "KP_Prior": "NumPad:PageUp",
    "KP_Right": "NumPad:Right",
    "KP_Separator": "NumPad:Separator",
    "KP_Space": "NumPad:Space",
    "KP_Subtract": "NumPad:Substract",
    "KP_Tab": "NumPad:Tab",
    "KP_Up": "NumPad:Up",
}

if Platform.os == "Windows":
    KEYSYM_ALIASES["App"] = "Menu"
elif Platform.os == "Linux":
    KEYSYM_ALIASES.update({"ISO_Left_Tab": "Tab", "ISO_Level3_Shift": "AltGr"})

REV_KEYSYM_ALIASES = {v: k for k, v in KEYSYM_ALIASES.items()}
