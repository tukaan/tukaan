from tukaan._system import Platform

if Platform.os == "macOS":
    BUTTON_NUMS = {"left": 1, "middle": 3, "right": 2}
else:
    BUTTON_NUMS = {"left": 1, "middle": 2, "right": 3}

MODIFIER_MAP = {
    1 << 12: "MouseWheel:Down",
    1 << 11: "MouseWheel:Up",
    1 << 10: "MouseButton:Right",
    1 << 9: "MouseButton:Middle",
    1 << 8: "MouseButton:Left",
    1 << 7: "Mod5",
    1 << 6: "Mod4",
    1 << 5: "Mod3",
    1 << 4: "Mod2",
    1 << 3: "Mod1",
    1 << 2: "Control",
    1 << 1: "CapsLock",
    1 << 0: "Shift",
}


BINDING_MODIFIER_MAP_X11 = {
    "Ctrl/Cmd": "Control",
    "Alt/Opt": "Alt",
    "NumLock": "Mod2",
    "AltGr": "Mod5",
}
BINDING_MODIFIER_MAP_WIN = {
    "Ctrl/Cmd": "Control",
    "Alt/Opt": "Alt",
    "NumLock": "Mod1",
    "AltGr": "Control-Alt",
}
BINDING_MODIFIER_MAP_MAC_AQUA = {"Ctrl/Cmd": "Command", "Alt/Opt": "Option"}
BINDING_MODIFIER_MAP_MAC_X11 = {"Ctrl/Cmd": "Mod2", "Alt/Opt": "Mod1"}

BINDING_MODIFIER_MAP = {"Control": "Control", "CapsLock": "Lock", "Shift": "Shift"}

if Platform.os == "Windows":
    BINDING_MODIFIER_MAP.update(BINDING_MODIFIER_MAP_WIN)
elif Platform.os == "macOS":
    BINDING_MODIFIER_MAP.update(BINDING_MODIFIER_MAP_MAC_AQUA)
elif Platform.os == "Linux":
    BINDING_MODIFIER_MAP.update(BINDING_MODIFIER_MAP_X11)

KEYBOARD_MODIFIERS_REGEX = f"({'|'.join(BINDING_MODIFIER_MAP.keys())})"
