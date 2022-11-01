namespace eval ttk::theme::clam {
  proc configure_colors {} {
    ttk::style configure . \
	    -background $::ttk::theme::clam::colors(-frame) \
	    -foreground black \
	    -bordercolor $::ttk::theme::clam::colors(-darkest) \
	    -darkcolor $::ttk::theme::clam::colors(-dark) \
	    -lightcolor $::ttk::theme::clam::colors(-lighter) \
	    -troughcolor $::ttk::theme::clam::colors(-darker) \
	    -selectbackground $::ttk::theme::clam::colors(-selectbg) \
	    -selectforeground $::ttk::theme::clam::colors(-selectfg) \
	    -selectborderwidth 0 \
	    -font TkDefaultFont

    ttk::style map . \
      -background  [list \
        disabled $::ttk::theme::clam::colors(-frame) \
        active $::ttk::theme::clam::colors(-lighter) \
      ] \
	    -foreground [list disabled $::ttk::theme::clam::colors(-disabledfg)] \
	    -selectbackground [list !focus $::ttk::theme::clam::colors(-darkest)] \
	    -selectforeground [list !focus white] \
  }
  
  ttk::style theme settings clam {
    # Tooltip
    ttk::style layout Tooltip {
      Label.border -sticky nswe -border 1 -children {
        Label.padding -sticky nswe -border 1 -children {
          Label.label -sticky nswe
        }
      }
    }

    ttk::style configure Tooltip \
      -background $colors(-lighter) \
      -bordercolor $colors(-darkest) \
      -darkcolor $colors(-lighter) \
      -lightcolor $colors(-lighter) \
      -font TkTooltipFont \
      -borderwidth 1 \
      -relief ridge \
      -padding 4
  }
}
