Switcher between applications (written in python 2).
Each X window can be associated with a custom virtual path. Then, you can switch
to a specific window by entering the type.

# Usage

`python switcher.py [wid]`

where wid is the window id associated with the window you want to set the custom
 path.

The way to use it is to assign a shortcut launching switcher.py with the current
window pid (using xdotool for example)

# Requirements

Python libraries: xlib, ewmh, anytree, getkey.

System requirements: xprop
(because I don't understand how to set a 
custom xproperty of some specific window using the xlib python library).


# How it works

The custom virtual path of a specific window is saved in a custom x property.
