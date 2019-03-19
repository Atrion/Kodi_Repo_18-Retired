# -*- coding: utf-8 -*-

'''
	Gaia Add-on
	Copyright (C) 2016 Gaia

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


import urlparse,os,sys

import xbmc,xbmcaddon,xbmcplugin,xbmcgui,xbmcvfs
from resources.lib.extensions import tools
from resources.lib.extensions import interface

integer = 1000

addonObject = xbmcaddon.Addon()

lang = addonObject.getLocalizedString

lang2 = xbmc.getLocalizedString

addon = xbmcaddon.Addon

addItem = xbmcplugin.addDirectoryItem

addItems = xbmcplugin.addDirectoryItems

item = xbmcgui.ListItem

directory = xbmcplugin.endOfDirectory

content = xbmcplugin.setContent

property = xbmcplugin.setProperty

addonInfo = addonObject.getAddonInfo

infoLabel = xbmc.getInfoLabel

condVisibility = xbmc.getCondVisibility

jsonrpc = xbmc.executeJSONRPC

window = xbmcgui.Window(10000)

progressDialogBG = xbmcgui.DialogProgressBG

button = xbmcgui.ControlButton

image = xbmcgui.ControlImage

keyboard = xbmc.Keyboard

sleep = xbmc.sleep

execute = xbmc.executebuiltin

skin = xbmc.getSkinDir

player = xbmc.Player

resolve = xbmcplugin.setResolvedUrl

openFile = xbmcvfs.File

makeFile = xbmcvfs.mkdir

deleteFile = xbmcvfs.delete

deleteDir = xbmcvfs.rmdir

listDir = xbmcvfs.listdir

transPath = xbmc.translatePath

kodiSkinPath = xbmc.translatePath('special://skin/')

addonPath = xbmc.translatePath(addonInfo('path'))

dataPath = xbmc.translatePath(addonInfo('profile')).decode('utf-8')

viewsFile = os.path.join(dataPath, 'views.db')

playbackFile = os.path.join(dataPath, 'playback.db')

providercacheFile = os.path.join(dataPath, 'providers.db')

metacacheFile = os.path.join(dataPath, 'metadata.db')

cacheFile = os.path.join(dataPath, 'cache.db')  # Used by trakt.py

def addonIcon():
	return addonInfo('icon')

def addonThumb():
	path = skinPath()
	theme = skinAppearance()
	default = theme in ['default', '-', '']
	if default:
		return 'DefaultFolder.png'
	elif not path == None:
		type = tools.Settings.getInteger('interface.theme.poster')
		name = None
		if type == 0: return None
		elif type == 1: name = 'plain'
		elif type == 2: name = 'artwork'
		elif type == 3: name = 'discbox'
		if name == None:
			return None
		else:
			result = os.path.join(path, 'posters', name + '.png')
			if os.path.exists(result):
				return result
	return addonInfo('icon')

def addonPoster():
	path = skinPath()
	theme = skinAppearance()
	default = theme in ['default', '-', '']
	if default:
		return 'DefaultVideo.png'
	elif not path == None:
		type = tools.Settings.getInteger('interface.theme.poster')
		name = None
		if type == 0: return None
		elif type == 1: name = 'plain'
		elif type == 2: name = 'artwork'
		elif type == 3: name = 'discbox'
		if name == None:
			return None
		else:
			result = os.path.join(path, 'posters', name + '.png')
			if os.path.exists(result):
				return result
	return addonInfo('icon')

def addonBanner():
	path = skinPath()
	theme = skinAppearance()
	default = theme in ['default', '-', '']
	if default:
		return 'DefaultVideo.png'
	elif not path == None:
		type = tools.Settings.getInteger('interface.theme.banner')
		name = None
		if type == 0: return None
		elif type == 1: name = 'plain'
		elif type == 2: name = 'artwork'
		if name == None:
			return None
		else:
			result = os.path.join(path, 'banners', name + '.png')
			if os.path.exists(result):
				return result
	return addonInfo('icon')

def addonFanart():
	if tools.Settings.getBoolean('interface.theme.background'):
		path = skinPath()
		theme = skinAppearance()
		if not path == None:
			result = os.path.join(path, 'background.jpg')
			if os.path.exists(result):
				return result
			else:
				result = os.path.join(path, 'background.png') # Glass
				if os.path.exists(result):
					return result
	return None

def skinPath():
	theme = skinAppearance()
	theme = theme.replace(' ', '').lower()
	index = theme.find('(')
	if index >= 0: theme = theme[:index]
	addon = tools.System.pathResources() if theme == 'default' or 'gaia1' in theme else tools.System.pathSkins()
	return os.path.join(addon, 'resources', 'media', 'skins', theme)

def iconAppearance():
	return tools.Settings.getString('interface.theme.icon').lower()

def skinAppearance():
	return tools.Settings.getString('interface.theme.skin').lower()


def yesnoDialog(line1, line2, line3, heading=addonInfo('name'), nolabel='', yeslabel=''):
	return xbmcgui.Dialog().yesno(heading, line1, line2, line3, nolabel, yeslabel)


def selectDialog(list, heading=addonInfo('name')):
	return xbmcgui.Dialog().select(heading, list)


def metaFile():
	return os.path.join(tools.System.pathArtwork(), 'resources', 'data', 'artwork', 'artwork.db')


def apiLanguage():
	trakt = ['bg','cs','da','de','el','en','es','fi','fr','he','hr','hu','it','ja','ko','nl','no','pl','pt','ro','ru','sk','sl','sr','sv','th','tr','uk','zh']
	tvdb = ['en','sv','no','da','fi','nl','de','it','es','fr','pl','hu','el','tr','ru','he','ja','pt','zh','cs','sl','hr','ko']

	if tools.Language.customization():
		language = tools.Settings.getString('interface.language.information')
	else:
		language = tools.Language.Automatic
	language = tools.Language.code(language)

	languages = {}
	languages['trakt'] = language if language in trakt else tools.Language.EnglishCode
	languages['tvdb'] = language if language in tvdb else tools.Language.EnglishCode

	return languages


def version():
	num = ''
	try: version = addon('xbmc.addon').getAddonInfo('version')
	except: version = '999'
	for i in version:
		if i.isdigit(): num += i
		else: break
	return int(num)


def cdnImport(uri, name):
	import imp
	from resources.lib.modules import client

	path = os.path.join(dataPath, 'py')
	path = path.decode('utf-8')

	deleteDir(os.path.join(path, ''), force=True)
	makeFile(dataPath)
	makeFile(path)

	r = client.request(uri)
	p = os.path.join(path, name + '.py')
	f = openFile(p, 'w')
	f.write(r)
	f.close()
	m = imp.load_source(name, p)

	deleteDir(os.path.join(path, ''), force=True)
	return m


def refresh():
	return execute('Container.Refresh')


def queueItem():
	return execute('Action(Queue)')
