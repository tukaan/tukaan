from __future__ import annotations

_window_pos: set[str] = {"center", "top-left", "top-right", "bottom-left", "bottom-right"}

_VALID_STATES: set[str] = {
    "active",
    "alternate",
    "background",
    "disabled",
    "focus",
    "hover",
    "invalid",
    "pressed",
    "readonly",
    "selected",
}

_keysym_aliases = {
    # general
    "Alt_L": "Alt:Left",
    "Alt_R": "Alt:Right",
    "App": "Menu",
    "BackSpace": "Backspace",
    "Caps_Lock": "CapsLock",
    "Control_L": "Control:Left",
    "Control_R": "Control:Right",
    "Hyper_L": "Hyper:Left",
    "Hyper_R": "Hyper:Right",
    "ISO_Left_Tab": "Tab",
    "ISO_Level3_Shift": "AltGr",
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
    # XF86 stuff
    "XF86AddFavorite": "XF86AddFavorite",
    "XF86ApplicationLeft": "XF86ApplicationLeft",
    "XF86ApplicationRight": "XF86ApplicationRight",
    "XF86AudioCycleTrack": "XF86AudioCycleTrack",
    "XF86AudioForward": "Audio:Forward",
    "XF86AudioLowerVolume": "Audio:VolumeDown",
    "XF86AudioMedia": "XF86AudioMedia",
    "XF86AudioMicMute": "XF86AudioMicMute",
    "XF86AudioMute": "Audio:Mute",
    "XF86AudioNext": "Audio:Next",
    "XF86AudioPause": "Audio:Pause",
    "XF86AudioPlay": "Audio:Play",
    "XF86AudioPreset": "XF86AudioPreset",
    "XF86AudioPrev": "Audio:Prev",
    "XF86AudioRaiseVolume": "Audio:VolumeUp",
    "XF86AudioRandomPlay": "Audio:Shuffle",
    "XF86AudioRecord": "Audio:Record",
    "XF86AudioRepeat": "Audio:Repeat",
    "XF86AudioRewind": "Audio:Rewind",
    "XF86AudioStop": "Audio:Stop",
    "XF86Away": "XF86Away",
    "XF86Back": "Action:Back",
    "XF86BackForward": "XF86BackForward",
    "XF86Battery": "XF86Battery",
    "XF86Blue": "Color:Blue",
    "XF86Bluetooth": "XF86Bluetooth",
    "XF86Book": "XF86Book",
    "XF86BrightnessAdjust": "XF86BrightnessAdjust",
    "XF86CD": "XF86CD",
    "XF86Calculator": "App:Calculator",
    "XF86Calendar": "App:Calendar",
    "XF86Clear": "Action:Clear",
    "XF86ClearGrab": "XF86ClearGrab",
    "XF86Close": "Action:Close",
    "XF86Community": "XF86Community",
    "XF86ContrastAdjust": "XF86ContrastAdjust",
    "XF86Copy": "Action:Copy",
    "XF86Cut": "Action:Cut",
    "XF86CycleAngle": "XF86CycleAngle",
    "XF86DOS": "XF86DOS",
    "XF86Display": "XF86Display",
    "XF86Documents": "Place:Documents",
    "XF86Eject": "Eject",
    "XF86Excel": "App:Excel",
    "XF86Explorer": "App:Explorer",
    "XF86Favorites": "Favorites",
    "XF86Finance": "XF86Finance",
    "XF86Forward": "Action:Forward",
    "XF86FrameBack": "XF86FrameBack",
    "XF86FrameForward": "XF86FrameForward",
    "XF86Game": "Game",
    "XF86Go": "Go",
    "XF86Green": "Color:Green",
    "XF86Hibernate": "Power:Hibernate",
    "XF86History": "History",
    "XF86HomePage": "HomePage",
    "XF86HotLinks": "XF86HotLinks",
    "XF86KbdBrightnessDown": "Keyboard:BrightnessDown",
    "XF86KbdBrightnessUp": "Keyboard:BrightnessUp",
    "XF86KbdLightOnOff": "Keyboard:BacklightToggle",
    "XF86Keyboard": "Keyboard",
    "XF86Launch0": "XF86Launch0",
    "XF86Launch1": "XF86Launch1",
    "XF86Launch2": "XF86Launch2",
    "XF86Launch3": "XF86Launch3",
    "XF86Launch4": "XF86Launch4",
    "XF86Launch5": "XF86Launch5",
    "XF86Launch6": "XF86Launch6",
    "XF86Launch7": "XF86Launch7",
    "XF86Launch8": "XF86Launch8",
    "XF86Launch9": "XF86Launch9",
    "XF86LaunchA": "XF86LaunchA",
    "XF86LaunchB": "XF86LaunchB",
    "XF86LaunchC": "XF86LaunchC",
    "XF86LaunchD": "XF86LaunchD",
    "XF86LaunchE": "XF86LaunchE",
    "XF86LaunchF": "XF86LaunchF",
    "XF86LightBulb": "XF86LightBulb",
    "XF86LogGrabInfo": "XF86LogGrabInfo",
    "XF86LogOff": "Power:Logoff",
    "XF86LogWindowTree": "XF86LogWindowTree",
    "XF86Mail": "App:Mail",
    "XF86MailForward": "XF86MailForward",
    "XF86Market": "XF86Market",
    "XF86Meeting": "Meeting",
    "XF86Memo": "XF86Memo",
    "XF86MenuKB": "XF86MenuKB",
    "XF86MenuPB": "XF86MenuPB",
    "XF86Messenger": "App:Messages",
    "XF86ModeLock": "XF86ModeLock",
    "XF86MonBrightnessCycle": "Monitor:BrightnessCycle",
    "XF86MonBrightnessDown": "Monitor:BrightnessDown",
    "XF86MonBrightnessUp": "Monitor:BrightnessUp",
    "XF86Music": "Place:Music",
    "XF86MyComputer": "Place:ThisPC",
    "XF86MySites": "XF86MySites",
    "XF86New": "Action:New",
    "XF86News": "App:News",
    "XF86Next_VMode": "XF86Next_VMode",
    "XF86OfficeHome": "XF86OfficeHome",
    "XF86Open": "Action:Open",
    "XF86OpenURL": "XF86OpenURL",
    "XF86Option": "XF86Option",
    "XF86Paste": "Action:Paste",
    "XF86Phone": "Phone",
    "XF86Pictures": "Place:Pictures",
    "XF86PowerDown": "Power:ShutDown",
    "XF86PowerOff": "Power:PowerOff",
    "XF86Prev_VMode": "XF86Prev_VMode",
    "XF86Q": "XF86Q",
    "XF86RFKill": "XF86RFKill",
    "XF86Red": "Color:Red",
    "XF86Refresh": "Action:Refresh",
    "XF86Reload": "Action:Reload",
    "XF86Reply": "Action:Reply",
    "XF86RockerDown": "XF86RockerDown",
    "XF86RockerEnter": "XF86RockerEnter",
    "XF86RockerUp": "XF86RockerUp",
    "XF86RotateWindows": "XF86RotateWindows",
    "XF86RotationKB": "XF86RotationKB",
    "XF86RotationLockToggle": "XF86RotationLockToggle",
    "XF86RotationPB": "XF86RotationPB",
    "XF86Save": "Action:Save",
    "XF86ScreenSaver": "Power:ScreenSaver",
    "XF86ScrollClick": "Scroll:Click",
    "XF86ScrollDown": "Scroll:Down",
    "XF86ScrollUp": "Scroll:Up",
    "XF86Search": "Action:Search",
    "XF86Select": "Action:Select",
    "XF86Send": "Action:Send",
    "XF86Shop": "XF86Shop",
    "XF86Sleep": "Power:Sleep",
    "XF86Spell": "XF86Spell",
    "XF86SplitScreen": "Action:SplitScreen",
    "XF86Standby": "Power:Standby",
    "XF86Start": "Action:Start",
    "XF86Stop": "Action:Stop",
    "XF86Subtitle": "XF86Subtitle",
    "XF86Support": "XF86Support",
    "XF86Suspend": "Power:Suspend",
    "XF86Switch_VT_1": "XF86Switch_VT_1",
    "XF86Switch_VT_10": "XF86Switch_VT_10",
    "XF86Switch_VT_11": "XF86Switch_VT_11",
    "XF86Switch_VT_12": "XF86Switch_VT_12",
    "XF86Switch_VT_2": "XF86Switch_VT_2",
    "XF86Switch_VT_3": "XF86Switch_VT_3",
    "XF86Switch_VT_4": "XF86Switch_VT_4",
    "XF86Switch_VT_5": "XF86Switch_VT_5",
    "XF86Switch_VT_6": "XF86Switch_VT_6",
    "XF86Switch_VT_7": "XF86Switch_VT_7",
    "XF86Switch_VT_8": "XF86Switch_VT_8",
    "XF86Switch_VT_9": "XF86Switch_VT_9",
    "XF86TaskPane": "XF86TaskPane",
    "XF86Terminal": "App:Terminal",
    "XF86Time": "XF86Time",
    "XF86ToDoList": "XF86ToDoList",
    "XF86Tools": "Tools",
    "XF86TopMenu": "XF86TopMenu",
    "XF86TouchpadOff": "Touchpad:Off",
    "XF86TouchpadOn": "Touchpad:On",
    "XF86TouchpadToggle": "Touchpad:Toggle",
    "XF86Travel": "XF86Travel",
    "XF86UWB": "XF86UWB",
    "XF86Ungrab": "XF86Ungrab",
    "XF86User1KB": "XF86User1KB",
    "XF86User2KB": "XF86User2KB",
    "XF86UserPB": "XF86UserPB",
    "XF86VendorHome": "XF86VendorHome",
    "XF86Video": "XF86Video",
    "XF86View": "XF86View",
    "XF86WLAN": "XF86WLAN",
    "XF86WWAN": "XF86WWAN",
    "XF86WWW": "XF86WWW",
    "XF86WakeUp": "XF86WakeUp",
    "XF86WebCam": "XF86WebCam",
    "XF86WheelButton": "XF86WheelButton",
    "XF86Word": "App:Word",
    "XF86Xfer": "XF86Xfer",
    "XF86Yellow": "Color:Yellow",
    "XF86ZoomIn": "Action:ZoomIn",
    "XF86ZoomOut": "Action:ZoomOut",
    "XF86iTouch": "iTouch",
}
