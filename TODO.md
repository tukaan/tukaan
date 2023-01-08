# TODO

* Write more documentation
* Write more tests
* Add more TODO items and indicate their priority (task mostly for [@rdbende](https://github.com/rdbende))

# Simple tasks
- Add window icon

  Currently it's not possible to add any window icon. It should be a `property` in the `WindowManager` class, that accepts either a `pathlib.Path` object, or a `tukaan.Icon` object, and sets the window icon. Cross-platform twist: it should be possible to set a `png` file on every system, an `ico` Windows, and `icns` on macOS
- Add button variants

  `variant` option for the `Button` widget to set styles like "outlined" (`Outline.TButton` internally), "filled" (`Filled.TButton`) and "link" (`Link.TButton`)
- Add button color variants

  `color` option for the `Button` widget to set styles like "primary" (`Pimary.TButton` internally), "secondary" (`Secondary.TButton`), "normal" (`TButton`) and "danger" (`Danger.TButton`)
- Add cursors

  Implement specifying a cursor for widgets. There should be enums containing the default, **native** cursors (we don't need all that "gumby", "coffe_mug" and others that Tk has). Some clever solution is needed for the platform specific cursors. Also support loading cursors from a file (Windows only) with a `Cursor` object
- Make the sidebar of the docs on the website sticky. It shouldn't disappear as you scroll.

# New widgets

## Simpler ones
- `Switch` widget

  Really just a checkbutton with different style applied. Should check if the `Switch` layout is available in the current theme, and use `TCheckbutton` with some sane layout-modifications otherwise
- `ToggleButton` widget

  Similar as the switch just with another style (`ToggleButton`)
- `LabeledView` widget (see [#120](https://github.com/tukaan/tukaan/issues/120))
- `ButtonGroup` widget (see [#119](https://github.com/tukaan/tukaan/issues/119))
- `LinkLabel`

  Label with a pointing hand cursor, and blue color (should use the `LinkLabel` ttk style if available), which opens a hyperlink when clicked

## Not so simple ones
- `NumberBox`

  There should be a `NumberBox` class that accepts numbers only, and has up and down arrows as well.
  The `SpinBox` should no longer accept a range of numbers, but take a list of values instead.
- `TreeView`

  Some sane treeview implementation
- `ListView`

  It should use a `ttk::treeview` under the hood with only one columns and no headers, because Tk's listbox widget **sucks**
- `StackView`

  A frame that arranges its children in a row automatically, and wraps when there's not enough space
- `TopNav`

  Navigation bar at the top of the window. It could have navigation buttons, plain buttons, dropdowns, search field and static and flexible placeholders
  ![image](https://user-images.githubusercontent.com/77941087/209965672-d487d245-d555-4d92-8bd4-cb4ad4e5fcd2.png)

- `SideNav`

  Similar to `TopNav`, but in a column on the left side
- `ToolBar`

  A toolbar widget with buttons, dropdowns and togglebuttons
- `Menu`
  
  Menus and menubars aren't so simple. It should use Tk's built in menu when a native theme is used on Windows or macOS (`LookAndFeel._is_current_theme_native`), and some custom, themeable implementaion on Linux, or when the current theme isn't native. 
  Menubars cannot be themed on macOS, and so neither should their submenus
- `Dropdown`

  Button that opens a dropdown menu when clicked
- `TextView`
  
  There used to be a [text widget](https://github.com/tukaan/tukaan/blob/v0.0.1.dev1/tukaan/widgets/textbox.py), but then it was removed. It should be reimplemented in a similar way.
- `TableView`
- `ExpandView`
- `FlipView` (carousel)
- `Pager`
- `SplitButton`


# For tinkerers
- Implement multiple monitor support
- Implement UI scaling support
- Implement new theme engines:
  If you'd like to work on this, we can discuss the details in https://github.com/tukaan/tukaan/issues/62
  - CSS + SVG image based
  - CSS + Dynamic canvas drawing


# Harder tasks
- Implement custom cursor support on Linux with the `xcursor` library. C programming, separate repo. Example implementation: https://wiki.tcl-lang.org/page/xcursor
- Implement an API for for Mac's touchbar. Objective-C programming. Repo: [tukaan/Idared](https://github.com/tukaan/Idared)

  Touchbar simulator: https://github.com/sindresorhus/touch-bar-simulator
