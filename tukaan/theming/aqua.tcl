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
    # Tooltip
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
  }
}
