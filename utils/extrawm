#!/usr/bin/env bash

# Kudos to rich from MX Linux forum:
# https://forum.mxlinux.org/viewtopic.php?f=27&t=45123

#Check if window is maximized or tiled
windowstate=$(xprop -id $(xdotool getwindowfocus) _NET_WM_STATE | cut -d' '  -f3,4,5)

function maximize()
{
	if [ "$windowstate" != "_NET_WM_STATE_MAXIMIZED_HORZ, _NET_WM_STATE_MAXIMIZED_VERT, _NET_WM_STATE_FOCUSED" ] # if window's not maximized,...
		then 
		wmctrl -r :ACTIVE: -b remove,maximized_vert,maximized_horz # restore to allow maximzation from tiled/vert maximized state (a little hacky...)
		wmctrl -r :ACTIVE: -b add,maximized_vert,maximized_horz # and, maximize!
	fi
}

function restoreorminimize()
{
	if [ "$windowstate" == "_NET_WM_STATE_MAXIMIZED_HORZ, _NET_WM_STATE_MAXIMIZED_VERT, _NET_WM_STATE_FOCUSED" ] # if window is maximized,...
		then 
		wmctrl -r :ACTIVE: -b remove,maximized_vert,maximized_horz # restore 
	elif [ "$windowstate" == "_NET_WM_STATE_MAXIMIZED_VERT, _NET_WM_STATE_FOCUSED" ] # if window is tiled...
		then 
		wmctrl -r :ACTIVE: -b remove,maximized_vert,maximized_horz # restore 
	else # if it's not maxmized or tiled...
		xdotool windowminimize $(xdotool getactivewindow) #minimize
	fi
}

if [ "$1" = "up" ]; then
    $(maximize)
elif [ "$1" = "down" ]; then
	$(restoreorminimize)
fi
