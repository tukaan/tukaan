# 
# Copyright (C) 1997-99 Kare Sjolander <kare@speech.kth.se>
#
# This file is part of the Snack sound extension for Tcl/Tk.
# The latest version can be found at http://www.speech.kth.se/snack/
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

package provide snack 2.2

# Set playback latency according to the environment variable PLAYLATENCY

if {$::tcl_platform(platform) == "unix"} {
    if {[info exists env(PLAYLATENCY)] && $env(PLAYLATENCY) > 0} {
	snack::audio playLatency $env(PLAYLATENCY)
    }
}

namespace eval snack {
    namespace export deleteInvalidShapeFile makeShapeFileDeleteable

    proc deleteInvalidShapeFile {fileName} {
	if {$fileName == ""} return
	if ![file exists $fileName] return
	set shapeName ""
	if [file exists [file rootname $fileName].shape] {
	    set shapeName [file rootname $fileName].shape
	}
	if [file exists [file rootname [file tail $fileName]].shape] {
	    set shapeName [file rootname [file tail $fileName]].shape
	}
	if {$shapeName != ""} {
	    set fileTime [file mtime $fileName]
	    set shapeTime [file mtime $shapeName]
	    if {$fileTime > $shapeTime} {

		# Delete shape file if older than sound file

		file delete -force $shapeName
	    } else {
		set s [snack::sound]
		$s config -file $fileName
		set soundSize [expr {200 * [$s length -unit seconds] * \
		    [$s cget -channels]}]
		set shapeSize [file size $shapeName]
		if {[expr {$soundSize*0.95}] > $shapeSize || \
			[expr {$soundSize*1.05}] < $shapeSize} {

		    # Delete shape file with incorrect size

		    file delete -force $shapeName
		}
		$s destroy
	    }
	}
    }

    proc makeShapeFileDeleteable {fileName} {
	if {$::tcl_platform(platform) == "unix"} {
	    if [file exists [file rootname $fileName].shape] {
		set shapeName [file rootname $fileName].shape
		catch {file attributes $shapeName -permissions 0777}
	    }
	    if [file exists [file rootname [file tail $fileName]].shape] {
		set shapeName [file rootname [file tail $fileName]].shape
		catch {file attributes $shapeName -permissions 0777}
	    }
	}
    }
}
