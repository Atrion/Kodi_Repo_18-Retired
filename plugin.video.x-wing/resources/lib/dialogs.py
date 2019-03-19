import xbmc, xbmcgui

def ok(title, msg):
	xbmcgui.Dialog().ok(title, msg)

def yesno(title, msg, no='No', yes='Yes'):
	return xbmcgui.Dialog().yesno(title, msg, nolabel=no, yeslabel=yes)

def select(title, items):
	return xbmcgui.Dialog().select(title, items)

def notify(msg, title, delay, image, sound=False):
	if xbmc.getInfoLabel('Window.Property(xmlfile)') != 'VideoFullScreen.xml':
		return xbmcgui.Dialog().notification(heading=title, message=msg, time=delay, icon=image, sound=sound)
	else:
		pass