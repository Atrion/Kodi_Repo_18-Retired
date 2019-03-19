import xbmcgui
from resources.lib.xswift2 import plugin

def get_property(name):
	return xbmcgui.Window(10000).getProperty(get_id(name))

def set_property(name, value):
	xbmcgui.Window(10000).setProperty(get_id(name), str(value))

def clear_property(name):
	xbmcgui.Window(10000).clearProperty(get_id(name))

def get_id(name):
	if '.' not in name:
		name = plugin.id + '.' + name
	return name