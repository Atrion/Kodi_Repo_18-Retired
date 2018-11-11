#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcaddon
import time

# Get global paths
addon = xbmcaddon.Addon(id='plugin.program.carpc-xtouch')
addonpath = addon.getAddonInfo('path').decode("utf-8")
monitor=xbmc.Monitor()

xbmcgui.Window(10000).setProperty('xtouch.daynight',addon.getSetting('state'))
xbmcgui.Window(10000).setProperty('xtouch.updating','false')

old  = int(time.strftime("%H%M")) - 1

while True:
    autoswitch = addon.getSetting('autoswitch')
    if autoswitch == "true":
	now = int(time.strftime("%H%M"))
	if old != now:
	    state = str(addon.getSetting('state'))
	    startday = addon.getSetting('startday')
	    startnight = addon.getSetting('startnight')
	    # failsavecheck
	    if str(startday) != "":
		triggerday = int(startday.replace(":",""))
	    else:
		triggerday = "08:00"
	    if str(startnight) != "":
		triggernight = int(startnight.replace(":",""))
	    else:
		triggernight = "20:00"
	    old = int(time.strftime("%H%M"))
	    if autoswitch == "true" and str(xbmc.getSkinDir()) == "skin.carpc-xtouch":
		if now >= triggerday  and now < triggernight and state == "night":
		    xbmc.executebuiltin("XBMC.RunScript(" + addonpath + "/addon.py,loadday)")
		if now >= triggernight and state == "day":
		    xbmc.executebuiltin("XBMC.RunScript(" + addonpath + "/addon.py,loadnight)")

    if monitor.abortRequested():
	break

    time.sleep(1.0)
quit()

