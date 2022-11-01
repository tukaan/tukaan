namespace eval ttk::theme::clam {{
  proc configure_colors {{}} {{
    ttk::style configure . \
      -background {view_bg} \
      -foreground {button_fg} \
      -troughcolor {view_bg} \
      -focuscolor {select_bg} \
      -selectbackground {select_bg} \
      -selectforeground {select_fg} \
      -insertcolor {button_fg} \
      -fieldbackground {view_bg}

    tk_setPalette \
      background {view_bg} \
      foreground {button_fg} \
      highlightColor {select_bg} \
      selectBackground {select_bg} \
      selectForeground {select_fg} \
      activeBackground {select_bg} \
      activeForeground {select_fg}

    option add *TCombobox*Listbox.background {button_bg}
    option add *TCombobox*Listbox.bordercolor {button_hover_bg}
  }}
  
  ttk::style theme settings clam {{
    # Frames
    ttk::style configure TFrame -background {view_bg}
    ttk::style configure TLabelframe \
      -background {view_bg} \
      -bordercolor {button_hover_bg} \
      -darkcolor {view_bg} \
      -lightcolor {view_bg}

    # Button
    ttk::style layout TButton {{
      Button.border -sticky nsew -children {{
        Button.padding -sticky nsew -children {{
          Button.label -sticky nsew
        }}
      }}
    }}

    ttk::style configure TButton \
      -background {button_bg} \
      -foreground {button_fg} \
      -bordercolor {button_hover_bg} \
      -darkcolor {button_bg} \
      -lightcolor {button_bg} \
      -borderwidth 1 \
      -relief ridge \
      -padding {{0 4}}
    
    ttk::style map TButton \
      -background  [list pressed {button_bg} active {button_hover_bg} focus {button_bg}] \
      -foreground [list disabled {disabled_fg} pressed {button_fg} active {button_hover_fg}] \
      -bordercolor [list pressed {button_hover_bg} focus {select_bg}] \
      -darkcolor [list pressed {button_hover_bg} focus {select_bg}] \
      -lightcolor [list pressed {button_hover_bg} focus {select_bg}]

    # MenuButton
    ttk::style configure TMenubutton {{
      Menubutton.border -sticky nsew -children {{
        Menubutton.indicator -side right -sticky {{}}
        Menubutton.padding -sticky we -children {{
          Menubutton.label -side left -sticky {{}}
        }}
      }}
    }}

    ttk::style configure TMenubutton \
      -background {button_bg} \
      -foreground {button_fg} \
      -focuscolor {button_bg} \
      -bordercolor {button_hover_bg} \
      -darkcolor {button_bg} \
      -lightcolor {button_bg} \
      -arrowcolor {button_fg} \
      -arrowsize 5 \
      -padding 4
    
    ttk::style map TMenubutton \
      -background  [list pressed {button_bg} active {button_hover_bg} focus {button_bg}] \
      -foreground [list disabled {disabled_fg} pressed {button_fg} active {button_hover_fg}] \
      -focuscolor [list pressed {button_bg} active {button_hover_bg} focus {button_bg}] \
      -bordercolor [list pressed {button_hover_bg} focus {select_bg}] \
      -darkcolor [list pressed {button_hover_bg} focus {select_bg}] \
      -lightcolor [list pressed {button_hover_bg} focus {select_bg}]

    # CheckBox
    ttk::style configure TCheckbutton \
      -foreground {button_fg} \
      -indicatorbackground {button_bg} \
      -indicatorsize 14 \
      -indicatormargin 8

    ttk::style map TCheckbutton \
      -background [list focus {view_bg} active {view_bg}] \
      -foreground [list disabled {disabled_fg}] \
      -indicatorbackground [list disabled {view_bg} focus {focus_color} active {button_hover_bg}]

    # RadioButton
    ttk::style configure TRadiobutton \
      -foreground {button_fg} \
      -indicatorbackground {button_bg} \
      -indicatorsize 14 \
      -indicatormargin 8

    ttk::style map TRadiobutton \
      -background [list focus {view_bg} active {view_bg}] \
      -foreground [list disabled {disabled_fg}] \
      -indicatorbackground [list disabled {view_bg} focus {focus_color} active {button_hover_bg}]

    # TextBox
    ttk::style configure TEntry \
      -background {button_bg} \
      -foreground {button_fg} \
      -highlightcolor {button_bg} \
      -bordercolor {button_hover_bg} \
      -lightcolor {view_bg} \
      -darkcolor {view_bg} \
      -padding 6

    ttk::style map TEntry \
      -background [list readonly {button_bg} focus {view_bg}] \
      -foreground [list disabled {disabled_fg}] \
      -bordercolor [list focus {select_bg} active {button_hover_bg}] \
      -lightcolor [list focus {select_bg} active {button_hover_bg}] \
      -darkcolor [list focus {select_bg} active {button_hover_bg}] \

    # SpinBox
    ttk::style configure TSpinbox \
      -background {button_bg} \
      -foreground {button_fg} \
      -highlightcolor {button_bg} \
      -bordercolor {button_hover_bg} \
      -lightcolor {view_bg} \
      -darkcolor {view_bg} \
      -padding 6 \
      -arrowcolor {button_fg} \
      -arrowsize 14

    ttk::style map TSpinbox \
      -background [list readonly {button_bg} focus {view_bg}] \
      -foreground [list disabled {disabled_fg}] \
      -bordercolor [list focus {select_bg} active {button_hover_bg}] \
      -lightcolor [list focus {select_bg} active {button_hover_bg}] \
      -darkcolor [list focus {select_bg} active {button_hover_bg}] \
      -fieldbackground [list readonly {button_bg} focus {view_bg}]

    # ComboBox
    ttk::style configure TCombobox \
      -background {button_bg} \
      -foreground {button_fg} \
      -highlightcolor {button_bg} \
      -bordercolor {button_hover_bg} \
      -lightcolor {view_bg} \
      -darkcolor {view_bg} \
      -padding 6 \
      -arrowcolor {button_fg} \
      -arrowsize 18

    ttk::style map TCombobox \
      -background [list readonly {button_bg} focus {view_bg}] \
      -foreground [list disabled {disabled_fg}] \
      -bordercolor [list focus {select_bg} active {button_hover_bg}] \
      -darkcolor [list {{readonly focus}} {focus_color} focus {select_bg} active {button_hover_bg}] \
      -lightcolor [list {{readonly focus}} {focus_color} focus {select_bg} active {button_hover_bg}] \
      -selectbackground [list readonly {button_bg}] \
      -selectforeground [list readonly {button_fg}] \
      -fieldbackground [list readonly {button_bg} focus {view_bg}]

    ttk::style configure ComboboxPopdownFrame -borderwidth 1 -bordercolor {select_bg}

    # Slider
    ttk::style configure TScale \
      -background {focus_color} \
      -bordercolor {button_hover_bg} \
      -darkcolor {focus_color} \
      -lightcolor {focus_color} \
      -troughcolor {button_bg}

    ttk::style map TScale -background [list active {button_hover_bg}]

    # ScrollBar
    ttk::style configure TScrollbar \
      -background {focus_color} \
      -troughcolor {button_bg} \
      -lightcolor {focus_color} \
      -darkcolor {focus_color} \
      -bordercolor {button_hover_bg} \
      -arrowcolor {button_hover_fg}

    ttk::style map TScrollbar -background [list active {button_hover_bg}]

    # ProgressBar
    ttk::style configure TProgressbar \
      -background {focus_color} \
      -troughcolor {button_bg} \
      -lightcolor {focus_color} \
      -darkcolor {focus_color} \
      -bordercolor {button_hover_bg}

    ttk::style configure TNotebook \
      -background {view_bg} \
      -bordercolor {button_hover_bg} \
      -darkcolor {view_bg} \
      -lightcolor {view_bg}

    # Tooltip
    ttk::style layout Tooltip {{
      Label.border -sticky nsew -border 1 -children {{
        Label.padding -sticky nsew -border 1 -children {{
          Label.label -sticky nsew
        }}
      }}
    }}

    ttk::style configure Tooltip \
      -background {tooltip_bg} \
      -foreground {tooltip_fg} \
      -bordercolor {tooltip_border} \
      -lightcolor {tooltip_bg} \
      -darkcolor {tooltip_bg} \
      -borderwidth 1 \
      -relief ridge \
      -padding {{4 2}}

    # TabView
    ttk::style configure TNotebook.Tab \
      -background {button_bg} \
      -foreground {button_fg} \
      -bordercolor {button_hover_bg} \
      -darkcolor {button_bg} \
      -lightcolor {button_bg} \
      -focuscolor {button_fg}

    ttk::style map TNotebook.Tab \
      -background  [list selected {focus_color} active {button_hover_bg} disabled {button_bg}] \
      -foreground [list disabled {disabled_fg} selected {button_hover_fg} active {button_hover_fg}] \
      -darkcolor [list selected {button_hover_bg} active {button_hover_bg} disabled {button_hover_bg}] \
      -lightcolor [list selected {button_hover_bg} active {button_hover_bg} disabled {button_hover_bg}]

    # Treeview
#    ttk::style configure Treeview \
#      -background {view_bg} \
#      -foreground {button_fg} \
#      -lightcolor {view_bg} \
#      -darkcolor {view_bg} \
#      -bordercolor {button_hover_bg} \
#      -fieldbackground {view_bg}
#
#    ttk::style map Treeview -background [list selected {select_bg}] -foreground [list selected {select_fg}]
#
#    ttk::style configure Heading -background {button_bg} -foreground {button_fg} -borderwidth 0
#    ttk::style map Heading -background [list active {button_hover_bg}] -foreground [list active {button_hover_fg}]

    # Divider
    ttk::style configure TSeparator -width 0 -height 0 -bordercolor {view_bg} -background {button_bg}

    # SplitView
    ttk::style configure Sash \
      -lightcolor {button_hover_bg} \
      -darkcolor {button_hover_bg} \
      -bordercolor {button_hover_bg} \
      -sashthickness 4 \
      -gripcount 20
  }}
}}
