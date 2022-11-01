namespace eval ttk::theme::vista {
  proc configure_colors {} {
    ttk::style configure . \
      -background SystemButtonFace \
      -foreground SystemWindowText \
      -selectforeground SystemHighlightText \
      -selectbackground SystemHighlight \
      -insertcolor SystemWindowText \
      -font TkDefaultFont

    ttk::style map . -foreground [list disabled SystemGrayText] 
  }

  ttk::style theme settings vista {
    # Tooltip
    ttk::style layout Tooltip {
      Tooltip.border -sticky nsew -border 1
      Label.padding -sticky nsew -border 1 -children {
        Label.label -sticky nsew
      }
    }

    ttk::style configure Tooltip \
      -font TkTooltipFont \
      -borderwidth 0 \
      -padding 4 \
      -foreground systemInfoText

    ttk::style element create Tooltip.border vsapi TOOLTIP 1 {{} 1}
  }
}
