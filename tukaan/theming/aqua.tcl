namespace eval ttk::theme::aqua {
  proc configure_colors {} {
    ttk::style configure . \
      -font TkDefaultFont \
      -background systemWindowBackgroundColor \
      -foreground systemLabelColor \
      -selectbackground systemSelectedTextBackgroundColor \
      -selectforeground systemSelectedTextColor \
      -selectborderwidth 0 \
      -insertwidth 1 \
      -stipple {}

    ttk::style map . \
      -foreground {
        disabled systemDisabledControlTextColor
        background systemLabelColor
      } \
      -selectbackground {
        background systemSelectedTextBackgroundColor
        !focus systemSelectedTextBackgroundColor
      } \
      -selectforeground {
        background systemSelectedTextColor
        !focus systemSelectedTextColor
      }
  }

  ttk::style theme settings aqua {
    ttk::style configure TButton -anchor center -foreground systemControlTextColor
    ttk::style map TButton -foreground {
      pressed white
      {alternate !pressed !background} white
      disabled systemDisabledControlTextColor
    }

    ttk::style configure TMenubutton -anchor center -padding {2 0 0 2}

    ttk::style configure Toolbutton -anchor center

    ttk::style layout Tooltip {
      Label.border -sticky nswe -border 1 -children {
        Label.padding -sticky nswe -border 1 -children {
          Label.label -sticky nswe
        }
      }
    }

    ttk::style configure Tooltip \
      -background systemButtonFace \
      -foreground systemControlTextColor \
      -font TkTooltipFont \
      -borderwidth 0 \
      -padding 4

    ttk::style configure TEntry -foreground systemTextColor -background systemTextBackgroundColor
    ttk::style map TEntry \
      -foreground {
        disabled systemDisabledControlTextColor
      } \
      -selectbackground {
        !focus systemUnemphasizedSelectedTextBackgroundColor
      }

    ttk::style map TCombobox \
      -foreground {
        disabled systemDisabledControlTextColor
      } \
      -selectbackground {
        !focus systemUnemphasizedSelectedTextBackgroundColor
      }

    ttk::style configure TSpinbox -foreground systemTextColor -background systemTextBackgroundColor
    ttk::style map TSpinbox \
      -foreground {
        disabled systemDisabledControlTextColor
      } \
      -selectbackground {
        !focus systemUnemphasizedSelectedTextBackgroundColor
      }

    ttk::style configure TNotebook -tabmargins {10 0} -tabposition n
    ttk::style configure TNotebook -padding {18 8 18 17}
    ttk::style configure TNotebook.Tab -padding {12 3 12 2}
    ttk::style configure TNotebook.Tab -foreground systemControlTextColor
    ttk::style map TNotebook.Tab -foreground {
      {background !selected} systemControlTextColor
      {background selected} black
      {!background selected} systemSelectedTabTextColor
      disabled systemDisabledControlTextColor
    }

    ttk::style configure Heading -font TkHeadingFont -foreground systemTextColor -background systemWindowBackgroundColor
    ttk::style configure Treeview \
      -rowheight 18 \
      -background systemTextBackgroundColor \
      -stripedbackground systemDisabledControlTextColor \
      -foreground systemTextColor \
      -fieldbackground systemTextBackgroundColor

    ttk::style map Treeview -background {
      selected systemSelectedTextBackgroundColor
    }

    ttk::style configure TProgressbar -period 100 -maxphase 120

    ttk::style configure TLabelframe -labeloutside true -labelmargins {14 0 14 2}
    ttk::style configure TLabelframe.Label -font TkSmallCaptionFont
  }
}
