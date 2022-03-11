package ifneeded snack 2.2 "[list load [file join $dir libsnack[info sharedlibextension]]];[list source [file join $dir snack.tcl]]"

package ifneeded sound 2.2 [list load [file join $dir libsound[info sharedlibextension]]]
