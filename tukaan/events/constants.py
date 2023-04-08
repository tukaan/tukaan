from tukaan._system import Platform

if Platform.os == "macOS":
    BUTTON_NUMS = {"left": 1, "middle": 3, "right": 2}
else:
    BUTTON_NUMS = {"left": 1, "middle": 2, "right": 3}


BINDING_MODIFIER_MAP_X11 = {
    "Ctrl/Cmd": "Control",
    "Alt/Opt": "Mod1",
    "NumLock": "Mod2",
    "AltGr": "Mod5",
}
BINDING_MODIFIER_MAP_WIN = {
    "Ctrl/Cmd": "Control",
    "Alt/Opt": "Mod2",
    "NumLock": "Mod1",
    "AltGr": "Control-Alt",
}
BINDING_MODIFIER_MAP_MAC_AQUA = {"Ctrl/Cmd": "Mod1", "Alt/Opt": "Mod2"}
BINDING_MODIFIER_MAP_MAC_X11 = {"Ctrl/Cmd": "Mod2", "Alt/Opt": "Mod1"}

BINDING_MODIFIER_MAP = {"Control": "Control", "CapsLock": "Lock", "Shift": "Shift"}

if Platform.os == "Windows":
    BINDING_MODIFIER_MAP.update(BINDING_MODIFIER_MAP_WIN)
elif Platform.os == "macOS":
    BINDING_MODIFIER_MAP.update(BINDING_MODIFIER_MAP_MAC_AQUA)
elif Platform.os == "Linux":
    BINDING_MODIFIER_MAP.update(BINDING_MODIFIER_MAP_X11)

rev_BINDING_MODIFIER_MAP = {v: k for k, v in BINDING_MODIFIER_MAP.items()}

MOD_STATE_MAP = {
    1 << 12: "MouseWheel:Down",
    1 << 11: "MouseWheel:Up",
    1 << 10: "MouseButton:Right",
    1 << 9: "MouseButton:Middle",
    1 << 8: "MouseButton:Left",
    1 << 7: rev_BINDING_MODIFIER_MAP.get("Mod5", "Mod5"),
    1 << 6: rev_BINDING_MODIFIER_MAP.get("Mod4", "Mod4"),
    1 << 5: rev_BINDING_MODIFIER_MAP.get("Mod3", "Mod3"),
    1 << 4: rev_BINDING_MODIFIER_MAP.get("Mod2", "Mod2"),
    1 << 3: rev_BINDING_MODIFIER_MAP.get("Mod1", "Mod1"),
    1 << 2: "Control",
    1 << 1: "CapsLock",
    1 << 0: "Shift",
}

KEYBOARD_MODIFIERS_REGEX = f"({'|'.join(BINDING_MODIFIER_MAP.keys())})"
KEYBOARD_EVENT_REGEX = r"<Key(Down|Up):\((.*?)\)>"
