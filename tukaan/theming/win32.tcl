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
    ttk::style configure TLabelframe.Label -foreground SystemButtonText
    ttk::style configure TButton -anchor center -padding {1 1} -width -11
    ttk::style configure TRadiobutton -padding 2
    ttk::style configure TCheckbutton -padding 2
    ttk::style configure Toolbutton -padding {4 4}
    ttk::style configure TMenubutton -padding {8 4}

    ttk::style element create Menubutton.dropdown vsapi \
      TOOLBAR 4 {
        {selected active} 6 \
        {selected !active} 5 \
        disabled 4 \
        pressed 3 \
        active 2 \
        {} 1 \
      } -syssize {SM_CXVSCROLL SM_CYVSCROLL}

    # Entry
    ttk::style layout TEntry {
      Entry.field -sticky nsew -border 0 -children {
        Entry.background -sticky nsew -children {
          Entry.padding -sticky nsew -children {
            Entry.textarea -sticky nsew
          }
        }
      }
    }

    ttk::style configure TEntry -padding {1 1 1 1}

    ttk::style element create Entry.field vsapi EDIT 6 \
      {disabled 4 focus 3 hover 2 {} 1} -padding {2 2 2 2}

    ttk::style element create Entry.background vsapi EDIT 3 \
      {disabled 3 readonly 3 focus 4 hover 2 {} 1}

    ttk::style map TEntry \
      -selectbackground [list !focus SystemWindow] \
      -selectforeground [list !focus SystemWindowText]

    # Spinbox
    ttk::style layout TSpinbox {
      Spinbox.field -sticky nsew -children {
        Spinbox.background -sticky nsew -children {
          Spinbox.padding -sticky nsew -children {
            Spinbox.innerbg -sticky nsew -children {
              Spinbox.textarea
            }
          }
          Spinbox.uparrow -side top -sticky ens
          Spinbox.downarrow -side bottom -sticky ens
        }
      }
    }

    ttk::style configure TSpinbox -padding 0

    ttk::style element create Spinbox.field vsapi EDIT 9 \
      {disabled 4 focus 3 hover 2 {} 1} -padding {1 1 1 2}

    ttk::style element create Spinbox.background vsapi EDIT 3 \
      {disabled 3 readonly 3 focus 4 hover 2 {} 1}

    ttk::style element create Spinbox.innerbg vsapi EDIT 3 \
      {disabled 3 readonly 3 focus 4 hover 2 {} 1} -padding {2 0 15 2}

    ttk::style element create Spinbox.uparrow vsapi SPIN 1 \
      {disabled 4 pressed 3 active 2 {} 1} \
      -padding 1 \
      -halfheight 1 \
      -syssize {SM_CXVSCROLL SM_CYVSCROLL}

    ttk::style element create Spinbox.downarrow vsapi SPIN 2 \
      {disabled 4 pressed 3 active 2 {} 1} \
      -padding 1 \
      -halfheight 1 \
      -syssize {SM_CXVSCROLL SM_CYVSCROLL}

    ttk::style map TSpinbox \
      -selectbackground [list !focus SystemWindow] \
      -selectforeground [list !focus SystemWindowText]

    # Combobox
    ttk::style layout TCombobox {
      Combobox.border -sticky nsew -border 0 -children {
        Combobox.rightdownarrow -side right -sticky ns
        Combobox.padding -sticky nsew -children {
          Combobox.background -sticky nsew -children {
            Combobox.focus -sticky nsew -children {
              Combobox.textarea -sticky nsew
            }
          }
        }
      }
    }

    ttk::style layout ComboboxPopdownFrame {
      ComboboxPopdownFrame.background -sticky nsew -border 1 -children {
        ComboboxPopdownFrame.padding -sticky nsew
      }
    }

    ttk::style configure TCombobox -padding 2

    ttk::style element create Combobox.border vsapi COMBOBOX 4 \
      {disabled 4 focus 3 active 2 hover 2 {} 1}

    ttk::style element create Combobox.background vsapi EDIT 3 \
      {disabled 3 readonly 5 focus 4 hover 2 {} 1}

    ttk::style element create Combobox.rightdownarrow vsapi COMBOBOX 6 \
      {disabled 4 pressed 3 active 2 {} 1} -syssize {SM_CXVSCROLL SM_CYVSCROLL}

    ttk::style element create ComboboxPopdownFrame.background vsapi LISTBOX 3 \
      {disabled 4 active 3 focus 2 {} 1}
      
    ttk::style map TCombobox \
      -foreground [list disabled SystemGrayText {readonly focus} SystemHighlightText ] \
      -selectbackground [list !focus SystemWindow] \
      -selectforeground [list !focus SystemWindowText] \
      -focusfill  [list {readonly focus} SystemHighlight]

      # Scrollbar
      ttk::style element create Horizontal.Scrollbar.trough vsapi SCROLLBAR 5 \
        {disabled 4 pressed 3 active 2 hover 5 {} 1}

      ttk::style element create Horizontal.Scrollbar.thumb vsapi SCROLLBAR 2 \
        {disabled 4 pressed 3 active 2 hover 5 {} 1} -syssize {SM_CXHSCROLL SM_CYHSCROLL}

      ttk::style element create Horizontal.Scrollbar.grip vsapi SCROLLBAR 8 \
        {disabled 4 pressed 3 active 2 hover 5 {} 1} -syssize {SM_CXHSCROLL SM_CYHSCROLL}

      ttk::style element create Horizontal.Scrollbar.leftarrow vsapi SCROLLBAR 1 \
        {disabled 12 pressed 11 active 10 hover 19 {} 9} -syssize {SM_CXHSCROLL SM_CYHSCROLL}

      ttk::style element create Horizontal.Scrollbar.rightarrow vsapi SCROLLBAR 1 \
        {disabled 16 pressed 15 active 14 hover 20 {} 13} -syssize {SM_CXHSCROLL SM_CYHSCROLL}

      ttk::style element create Vertical.Scrollbar.trough vsapi SCROLLBAR 7 \
        {disabled 4 pressed 3 active 2 hover 5 {} 1}

      ttk::style element create Vertical.Scrollbar.thumb vsapi SCROLLBAR 3 \
        {disabled 4 pressed 3 active 2 hover 5 {} 1} -syssize {SM_CXVSCROLL SM_CYVSCROLL}

      ttk::style element create Vertical.Scrollbar.grip vsapi SCROLLBAR 9 \
        {disabled 4 pressed 3 active 2 hover 5 {} 1} -syssize {SM_CXVSCROLL SM_CYVSCROLL}

      ttk::style element create Vertical.Scrollbar.uparrow vsapi SCROLLBAR 1 \
        {disabled 4 pressed 3 active 2 hover 17 {} 1} -syssize {SM_CXVSCROLL SM_CYVSCROLL}

      ttk::style element create Vertical.Scrollbar.downarrow vsapi SCROLLBAR 1 \
        {disabled 8 pressed 7 active 6 hover 18 {} 5} -syssize {SM_CXVSCROLL SM_CYVSCROLL}

      # Progressbar
      ttk::style layout Horizontal.TProgressbar {
        Horizontal.Progressbar.trough -sticky nsew -children {
          Horizontal.Progressbar.pbar -side left -sticky ns
          Horizontal.Progressbar.text -sticky nesw
        }
      }

      ttk::style layout Vertical.TProgressbar {
        Vertical.Progressbar.trough -sticky nsew -children {
          Vertical.Progressbar.pbar -side bottom -sticky we
        }
      }

      ttk::style element create Horizontal.Progressbar.pbar vsapi PROGRESS 3 {{} 1} -padding 8
      ttk::style element create Vertical.Progressbar.pbar vsapi PROGRESS 3 {{} 1} -padding 8

      # Scale
      ttk::style layout Horizontal.TScale {
        Scale.focus -sticky nsew -children {
          Horizontal.Scale.trough -sticky nsew -children {
            Horizontal.Scale.track -sticky we
            Horizontal.Scale.slider -side left -sticky {}
          }
        }
      }

      ttk::style layout Vertical.TScale {
        Scale.focus -sticky nsew -children {
          Vertical.Scale.trough -sticky nsew -children {
            Vertical.Scale.track -sticky ns
            Vertical.Scale.slider -side top -sticky {}
          }
        }
      }

      ttk::style element create Horizontal.Scale.slider vsapi TRACKBAR 3 \
        {disabled 5 focus 4 pressed 3 active 2 {} 1} \
        -width 6 \
        -height 12
      
      ttk::style element create Vertical.Scale.slider vsapi TRACKBAR 6 \
        {disabled 5 focus 4 pressed 3 active 2 {} 1} \
        -width 12 \
        -height 6

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

    # Notebook
    ttk::style configure TNotebook -tabmargins {2 2 2 0}
    ttk::style map TNotebook.Tab -expand [list selected {2 2 2 2}]

    # Treeview
    ttk::style configure Treeview -background SystemWindow  -stripedbackground System3dLight
    ttk::style configure Treeview.Separator  -background System3dLight
    ttk::style map Treeview \
      -background [list disabled SystemButtonFace selected SystemHighlight] \
      -foreground [list disabled SystemGrayText selected SystemHighlightText]

    ttk::style configure Heading -font TkHeadingFont
    ttk::style configure Item -padding {4 0 0 0}
  }
}
