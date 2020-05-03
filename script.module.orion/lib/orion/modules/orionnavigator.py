# -*- coding: utf-8 -*-

"""
	Orion
    https://orionoid.com

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
"""

##############################################################################
# ORIONNAVIGATOR
##############################################################################
# Class for interface navigation.
##############################################################################

import xbmcgui
import xbmcplugin
from orion.modules.oriontools import *
from orion.modules.orionsettings import *
from orion.modules.orioninterface import *
from orion.modules.orionapp import *
from orion.modules.orionuser import *
from orion.modules.orionticket import *
from orion.modules.orionstream import *
from orion.modules.orionserver import *
from orion.modules.orionintegration import *
from orion.modules.orionnotification import *

class OrionNavigator:

	##############################################################################
	# CONSTANTS
	##############################################################################

	ContentAddons = 'addons'
	ContentFiles = 'files'
	ContentSongs = 'songs'
	ContentArtists = 'artists'
	ContentAlbums = 'albums'
	ContentMovies = 'movies'
	ContentShows = 'tvshows'
	ContentEpisodes = 'episodes'
	ContentMusicVideos = 'musicvideos'

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, content = ContentAddons, cache = False):
		self.mContent = content
		self.mCache = cache
		self.mHandle = OrionTools.addonHandle()

	##############################################################################
	# INTERNAL
	##############################################################################

	# context = [{'label', 'action', 'parameters'}]
	# Optional 'command' parameter to specify a custom command instead of construction one from action and parameters.
	def buildAdd(self, label, action = None, parameters = None, context = [], folder = False, icon = None, theme = OrionInterface.ThemeDefault, default = None):
		link = OrionTools.executePlugin(action = action, parameters = parameters, run = False)
		item = xbmcgui.ListItem(label = OrionTools.translate(label))

		if len(context) > 0:
			contextMenu = []
			for c in context:
				contextLabel = OrionTools.translate(c['label'])
				if 'command' in c:
					command = c['command']
				else:
					contextAction = c['action'] if 'action' in c else None
					contextParameters = c['parameters'] if 'parameters' in c else None
					command = OrionTools.executePlugin(action = contextAction, parameters = contextParameters)
				contextMenu.append((contextLabel, command))
			item.addContextMenuItems(contextMenu)

		icon = OrionInterface.iconPath(icon, theme = theme)
		if default and not OrionTools.fileExists(icon): icon = OrionInterface.iconPath(default, theme = OrionInterface.ThemeDefault)

		item.setArt({'icon': icon, 'thumb': icon})
		if OrionSettings.getBoolean('general.interface.background'): item.setProperty('Fanart_Image', OrionTools.pathJoin(OrionTools.addonPath(), 'fanart.jpg'))
		xbmcplugin.addDirectoryItem(handle = self.mHandle, url = link, listitem = item, isFolder = folder)

	def buildFinish(self):
		xbmcplugin.setContent(self.mHandle, self.mContent)
		xbmcplugin.endOfDirectory(self.mHandle, cacheToDisc = self.mCache)

	##############################################################################
	# MENU
	##############################################################################

	@classmethod
	def menuMain(self, wizard = True):
		menu = OrionNavigator()
		user = OrionUser.instance()
		if user.subscriptionPackageFree(): menu.buildAdd(label = 32044, action = 'dialogPremium', folder = False, icon = 'premium')
		if user.valid(): menu.buildAdd(label = 32017, action = 'menuAccount', folder = True, icon = 'account')
		else:
			menu.buildAdd(label = 32248, action = 'dialogFree', folder = False, icon = 'free')
			menu.buildAdd(label = 32253, action = 'dialogLogin', folder = False, icon = 'authenticate')
		menu.buildAdd(label = 32284, action = 'menuSupport', folder = True, icon = 'support')
		menu.buildAdd(label = 32002, action = 'menuApps', folder = True, icon = 'app')
		menu.buildAdd(label = 32004, action = 'menuTools', folder = True, icon = 'tools')
		menu.buildFinish()
		if wizard and not user.valid() and not OrionSettings.getBoolean('internal.initial'):
			OrionSettings.wizard()
		OrionSettings.set('internal.initial', True)

	@classmethod
	def menuAccount(self):
		menu = OrionNavigator()
		user = OrionUser.instance()
		if user.valid(): menu.buildAdd(label = 32010, action = 'dialogUser', folder = False, icon = 'details')
		menu.buildAdd(label = 32271, action = 'dialogVoucher', folder = False, icon = 'voucher')
		menu.buildFinish()

	@classmethod
	def menuApps(self):
		OrionInterface.loaderShow()
		apps = OrionApp.instances(update = True, wait = True, orion = False, sort = True)
		menu = OrionNavigator()
		menu.buildAdd(label = 32174, action = 'menuIntegration', folder = True, icon = 'integration')
		for app in apps:
			menu.buildAdd(label = app.name(), action = 'dialogApp', parameters = {'id' : app.id()}, icon = OrionIntegration.id(app.name()), theme = OrionInterface.ThemeApps, default = 'app')
		menu.buildFinish()
		OrionInterface.loaderHide()

	@classmethod
	def menuSupport(self):
		menu = OrionNavigator()
		menu.buildAdd(label = 32285, action = 'menuTickets', folder = True, icon = 'ticket')
		menu.buildAdd(label = 32056, action = 'menuNotifications', folder = True, icon = 'notification')
		menu.buildAdd(label = 32314, action = 'dialogPromotion', folder = False, icon = 'promotion')
		menu.buildFinish()

	@classmethod
	def menuTickets(self):
		if not OrionSettings.getBoolean('internal.tickets'):
			OrionInterface.dialogConfirm(title = 32285, message = 33062)
			OrionSettings.set('internal.tickets', True)
		OrionInterface.loaderShow()
		OrionTicket.dialogSupport()
		tickets = OrionTicket.retrieveAll()
		menu = OrionNavigator()
		menu.buildAdd(label = 32287, action = 'dialogTicket', folder = False, icon = 'write')
		for ticket in tickets:
			menu.buildAdd(label = ticket.label(), action = 'dialogTicket', parameters = {'id' : ticket.id(), 'status' : ticket.status()}, icon = 'ticket')
		menu.buildFinish()
		OrionInterface.loaderHide()

	@classmethod
	def menuNotifications(self):
		OrionInterface.loaderShow()
		notifications = OrionNotification.update()
		if len(notifications) == 0:
			OrionInterface.dialogNotification(title = 32157, message = 33009, icon = OrionInterface.IconError)
		else:
			menu = OrionNavigator()
			for notification in notifications:
				menu.buildAdd(label = notification.label(), action = 'dialogNotification', parameters = {'data' : notification.data()}, icon = 'notification')
			menu.buildFinish()
		OrionInterface.loaderHide()

	@classmethod
	def menuTools(self):
		menu = OrionNavigator()
		menu.buildAdd(label = 32005, action = 'dialogSettings', parameters = {'option' : True}, folder = False, icon = 'settings')
		menu.buildAdd(label = 32174, action = 'menuIntegration', folder = True, icon = 'integration')
		menu.buildAdd(label = 32006, action = 'menuClean', folder = False, icon = 'clean')
		menu.buildAdd(label = 32156, action = 'dialogServer', folder = False, icon = 'server')
		menu.buildAdd(label = 32170, action = 'dialogBackup', folder = False, icon = 'backup')
		menu.buildAdd(label = 32007, action = 'dialogLink', folder = False, icon = 'network')
		menu.buildAdd(label = 32008, action = 'menuAbout', folder = False, icon = 'about')
		menu.buildFinish()

	@classmethod
	def menuIntegration(self):
		# Only show warning message once a day, just so that refreshing the container does not cause another popup.
		current = OrionTools.timestamp()
		time = current - OrionSettings.getInteger('internal.integration')
		if time < 86400 or OrionInterface.dialogOption(title = 32174, message = 33028):
			OrionSettings.set('internal.integration', current)
			menu = OrionNavigator()
			addons = OrionIntegration.addons(sort = True)
			for addon in addons:
				menu.buildAdd(label = addon['format'], action = addon['action'], folder = False, icon = addon['id'], theme = OrionInterface.ThemeApps)
			menu.buildFinish()

	@classmethod
	def menuClean(self):
		OrionInterface.loaderShow()
		items = [[32047, 33044], [32005, 33045]]
		items = [OrionInterface.fontBold(OrionTools.translate(item[0]) + ': ') + OrionTools.translate(item[1]) for item in items]
		choice = OrionInterface.dialogOptions(title = 32006, items = items)
		if choice == 0:
			OrionTools.cleanCache()
			OrionInterface.dialogNotification(title = 32006, message = 33005, icon = OrionInterface.IconSuccess)
		elif choice == 1:
			if OrionInterface.dialogOption(title = 32006, message = 33003):
				OrionTools.cleanSettings()
				OrionInterface.dialogNotification(title = 32006, message = 33004, icon = OrionInterface.IconSuccess)
		OrionInterface.loaderHide()

	@classmethod
	def menuAbout(self):
		message = ''
		message += OrionInterface.font(OrionTools.addonName(), bold = True, color = OrionInterface.ColorPrimary, uppercase = True)
		message += OrionInterface.fontNewline() + OrionInterface.fontNewline()
		message += OrionInterface.font(OrionTools.translate(32045) + ' ' + OrionTools.addonVersion(), bold = True)
		message += OrionInterface.fontNewline()
		message += OrionInterface.font(OrionTools.link(), bold = True)
		message += OrionInterface.fontNewline() + OrionInterface.fontNewline()
		message += OrionInterface.font(32012, bold = True, color = OrionInterface.ColorPrimary, uppercase = True)
		message += OrionInterface.fontNewline() + OrionInterface.fontNewline()
		message += OrionTools.addonDescription()
		message += OrionInterface.fontNewline() + OrionInterface.fontNewline()
		message += OrionInterface.font(32046, bold = True, color = OrionInterface.ColorPrimary, uppercase = True)
		message += OrionInterface.fontNewline() + OrionInterface.fontNewline()
		message += OrionTools.addonDisclaimer()
		OrionInterface.dialogPage(title = 32008, message = message)

	##############################################################################
	# DIALOG
	##############################################################################

	@classmethod
	def dialogSettings(self, option = False):
		if option:
			choice = OrionInterface.dialogOption(title = 32005, message = 33036, labelConfirm = 32249, labelDeny = 32186)
			if choice: OrionSettings.wizard()
			else: OrionSettings.launch()
		else:
			OrionSettings.launch()

	@classmethod
	def dialogApp(self, id):
		OrionApp(id = id).dialog()

	@classmethod
	def dialogUser(self):
		OrionInterface.loaderShow()
		user = OrionUser.instance()
		success = not user.valid() or user.update()
		OrionInterface.loaderHide()
		if success: user.dialog()

	@classmethod
	def dialogVoucher(self):
		choice = OrionInterface.dialogOption(title = 32271, message = 33046, labelConfirm = 32250, labelDeny = 32251)
		if choice:
			if OrionUser.instance().subscriptionPackageAnonymous():
				choice = OrionInterface.dialogOption(title = 32271, message = 33047, labelConfirm = 32250, labelDeny = 32251)
			if choice:
				token = OrionInterface.dialogInput(title = 32272)
				OrionInterface.loaderShow()
				api = OrionApi()
				api.couponRedeem(token = token)
				if api.statusSuccess():
					user = OrionUser.instance()
					user.update()
					message = OrionTools.translate(33048) % (OrionInterface.fontBold(user.subscriptionPackageName()), OrionInterface.fontBold(OrionTools.timeDays(timeTo = user.subscriptionTimeExpiration(), format = True)))
				else:
					message = api.message()
				OrionInterface.loaderHide()
				OrionInterface.dialogConfirm(title = 32271, message = message)

	@classmethod
	def dialogTicket(self, id = None, status = None):
		ticket = OrionTicket(id = id, status = status)
		ticket.dialog()

	@classmethod
	def dialogServer(self):
		server = OrionServer.instance()
		OrionInterface.loaderShow()
		server.update()
		OrionInterface.loaderHide()
		server.dialog()

	@classmethod
	def dialogBackup(self):
		items = [[32264, 33039], [32265, 33040], [32266, 33041], [32267, 33042]]
		items = [OrionInterface.fontBold(OrionTools.translate(item[0]) + ': ') + OrionTools.translate(item[1]) for item in items]
		choice = OrionInterface.dialogOptions(title = 32170, items = items)
		if choice == 0: OrionSettings.backupImport()
		elif choice == 1: OrionSettings.backupExport()
		elif choice == 2: OrionSettings.backupImportOnline()
		elif choice == 3: OrionSettings.backupExportOnline()

	@classmethod
	def dialogNotification(self, data):
		OrionNotification(data = data).dialog()

	@classmethod
	def dialogLink(self, link = None):
		OrionTools.linkOpen(link)

	@classmethod
	def dialogPremium(self):
		OrionInterface.dialogConfirm(title = 32044, message = OrionTools.translate(33035) +  (OrionInterface.fontNewline() * 2) + OrionInterface.fontBold(OrionTools.link()))
		OrionTools.linkOpen(dialog = False)

	@classmethod
	def dialogFree(self):
		OrionInterface.dialogConfirm(title = 32248, message = (OrionTools.translate(33033) % (OrionInterface.fontBold(str(OrionUser.LinksAnonymous)), OrionInterface.fontBold(str(OrionUser.LinksFree)))) +  (OrionInterface.fontNewline() * 2) + OrionInterface.fontBold(OrionTools.link()))
		if OrionInterface.dialogOption(title = 32248, message = 33034):
			OrionUser.anonymous()
			OrionInterface.containerRefresh()

	@classmethod
	def dialogLogin(self):
		return self.settingsAccountLogin(settings = False, refresh = True)

	##############################################################################
	# SETTINGS
	##############################################################################

	@classmethod
	def settingsAccountLogin(self, key = None, settings = True, refresh = True):
		if key == None: key = self.settingsAccountKey(loader = True, hide = False)
		else: OrionInterface.loaderShow()

		user = OrionUser.instance()
		if key:
			user.settingsKeySet(key)
			if self.settingsAccountRefresh(launch = False, notification = True):
				OrionIntegration.check()

				# Reduce the limits for free users.
				if user.subscriptionPackageAnonymous():
					OrionSettings.setFiltersLimitCount(OrionUser.LinksAnonymous)
					OrionSettings.setFiltersLimitRetry(0)
				elif user.subscriptionPackageFree():
					OrionSettings.setFiltersLimitCount(OrionUser.LinksFree)
					OrionSettings.setFiltersLimitRetry(0)

				if user.addonKodi() and OrionInterface.dialogOption(title = 32170, message = 33012):
					OrionSettings.backupImportOnline(refresh = False)
		else:
			user.settingsKeySet('') # Remove key and disable account.
			user.update(disable = True)

		if settings: OrionSettings.launch(category = OrionSettings.CategoryAccount)
		if refresh: OrionInterface.containerRefresh()
		OrionInterface.loaderHide()
		return user.valid(True)

	@classmethod
	def settingsAccountKey(self, loader = True, hide = True):
		instance = OrionUser.instance()
		choice = OrionInterface.dialogOptions(title = 32034, items = [32273, 32274, 32275])
		if choice == 0:
			return self.settingsAccountInput(title = 32018, default = instance.key())
		elif choice > 0:
			user = self.settingsAccountInput(title = 32020 if choice == 1 else 32276)
			password = self.settingsAccountInput(title = 32168)
			if loader: OrionInterface.loaderShow()
			result = instance.login(user = user, password = password)
			if loader and hide: OrionInterface.loaderHide()
			return result
		return None

	@classmethod
	def settingsAccountInput(self, title, default = ''):
		return OrionInterface.dialogInput(title = title, default = default)

	@classmethod
	def settingsAccountRefresh(self, launch = True, loader = True, notification = False):
		user = OrionUser.instance()
		if loader: OrionInterface.loaderShow()
		user.update()
		valid = user.enabled() and user.valid(True)
		if loader: OrionInterface.loaderHide()
		if notification and valid: OrionInterface.dialogNotification(title = 32169, message = 33011, icon = OrionInterface.IconSuccess)
		if launch: OrionSettings.launch(category = OrionSettings.CategoryAccount)
		return valid

	@classmethod
	def _settingsFilters(self, title, settingsGet, settingsSet, type = None):
		OrionInterface.dialogConfirm(title = title, message = 33008)
		OrionTools.sleep(0.1)
		OrionInterface.loaderShow()
		enabled = ': ' + OrionInterface.fontColor(32096, OrionInterface.ColorEnabled)
		disabled = ': ' + OrionInterface.fontColor(32057, OrionInterface.ColorDisabled)
		values = getattr(OrionSettings, settingsGet)(type)
		OrionInterface.loaderHide()
		if values == None or len(values) == 0:
			OrionSettings.externalCategory(type)
			return
		while True:
			ids = []
			items = []
			for key, value in OrionTools.iterator(values):
				ids.append(key)
				items.append(value['name'] + (enabled if value['enabled'] else disabled))
			items, ids = zip(*sorted(zip(items, ids))) # Sort alphabetically
			ids = [None, None, None] + list(ids)
			items = [OrionInterface.fontBold(32151), OrionInterface.fontBold(32149), OrionInterface.fontBold(32150)] + list(items)
			choice = OrionInterface.dialogOptions(title = title, items = items)
			if choice <= 0:
				break
			elif choice == 1:
				for i in values.iterkeys():
					values[i]['enabled'] = True
			elif choice == 2:
				for i in values.iterkeys():
					values[i]['enabled'] = False
			else:
				values[ids[choice]]['enabled'] = not values[ids[choice]]['enabled']
			getattr(OrionSettings, settingsSet)(values, type)
		OrionSettings.externalCategory(type)

	@classmethod
	def _settingsFiltersLanguages(self, title, settingsGet, settingsSet, type = None):
		OrionInterface.loaderShow()
		enabled = ': ' + OrionInterface.fontColor(32096, OrionInterface.ColorEnabled)
		disabled = ': ' + OrionInterface.fontColor(32057, OrionInterface.ColorDisabled)
		values = getattr(OrionSettings, settingsGet)(type)
		OrionInterface.loaderHide()
		if values == None or len(values) == 0:
			OrionSettings.externalCategory(type)
			return
		while True:
			ids = []
			items = []
			for key, value in OrionTools.iterator(values):
				ids.append(key)
				items.append('[' + OrionInterface.fontUppercase(value['code']) + '] ' + value['name'] + (enabled if value['enabled'] else disabled)) # Do not use Python upper function, otherwise it results in [CR] which means a line break in Kodi.
			items, ids = zip(*sorted(zip(items, ids))) # Sort alphabetically
			ids = [None, None, None] + list(ids)
			items = [OrionInterface.fontBold(32151), OrionInterface.fontBold(32149), OrionInterface.fontBold(32150)] + list(items)
			choice = OrionInterface.dialogOptions(title = title, items = items)
			if choice <= 0:
				break
			elif choice == 1:
				for i in values.iterkeys():
					values[i]['enabled'] = True
			elif choice == 2:
				for i in values.iterkeys():
					values[i]['enabled'] = False
			else:
				values[ids[choice]]['enabled'] = not values[ids[choice]]['enabled']
			getattr(OrionSettings, settingsSet)(values, type)
		OrionSettings.externalCategory(type)

	@classmethod
	def settingsFiltersStreamOrigin(self, type = None):
		OrionInterface.dialogConfirm(title = 32201, message = 33008)
		OrionTools.sleep(0.1)
		OrionInterface.loaderShow()
		enabled = ': ' + OrionInterface.fontColor(32096, OrionInterface.ColorEnabled)
		disabled = ': ' + OrionInterface.fontColor(32057, OrionInterface.ColorDisabled)
		values = OrionSettings.getFiltersStreamOrigin(type)
		OrionInterface.loaderHide()
		if values == None or len(values) == 0:
			OrionSettings.externalCategory(type)
			return
		while True:
			ids = []
			items = []
			for key, value in OrionTools.iterator(values):
				ids.append(key)
				items.append(value['name'].upper() + (enabled if value['enabled'] else disabled))
			items, ids = zip(*sorted(zip(items, ids))) # Sort alphabetically
			ids = [None, None, None] + list(ids)
			items = [OrionInterface.fontBold(32151), OrionInterface.fontBold(32149), OrionInterface.fontBold(32150)] + list(items)
			choice = OrionInterface.dialogOptions(title = 32201, items = items)
			if choice <= 0:
				break
			elif choice == 1:
				for i in values.iterkeys():
					values[i]['enabled'] = True
			elif choice == 2:
				for i in values.iterkeys():
					values[i]['enabled'] = False
			else:
				values[ids[choice]]['enabled'] = not values[ids[choice]]['enabled']
			OrionSettings.setFiltersStreamOrigin(values, type)
		OrionSettings.externalCategory(type)

	@classmethod
	def settingsFiltersStreamSource(self, type = None):
		OrionInterface.dialogConfirm(title = 32094, message = 33008)
		OrionTools.sleep(0.1)
		OrionInterface.loaderShow()
		types = {OrionStream.TypeTorrent : OrionTools.translate(32097).upper(), OrionStream.TypeUsenet : OrionTools.translate(32089).upper(), OrionStream.TypeHoster : OrionTools.translate(32098).upper()}
		enabled = ': ' + OrionInterface.fontColor(32096, OrionInterface.ColorEnabled)
		disabled = ': ' + OrionInterface.fontColor(32057, OrionInterface.ColorDisabled)
		values = OrionSettings.getFiltersStreamSource(type)
		OrionInterface.loaderHide()
		if values == None or len(values) == 0:
			OrionSettings.externalCategory(type)
			return
		while True:
			ids = []
			items = []
			for key, value in OrionTools.iterator(values):
				ids.append(key)
				items.append('[' + types[value['type']] + '] ' + value['name'].upper() + (enabled if value['enabled'] else disabled))
			items, ids = zip(*sorted(zip(items, ids))) # Sort alphabetically
			ids = [None, None, None] + list(ids)
			items = [OrionInterface.fontBold(32151), OrionInterface.fontBold(32149), OrionInterface.fontBold(32150)] + list(items)
			choice = OrionInterface.dialogOptions(title = 32094, items = items)
			if choice <= 0:
				break
			elif choice == 1:
				for i in values.iterkeys():
					values[i]['enabled'] = True
			elif choice == 2:
				for i in values.iterkeys():
					values[i]['enabled'] = False
			else:
				values[ids[choice]]['enabled'] = not values[ids[choice]]['enabled']
			OrionSettings.setFiltersStreamSource(values, type)
		OrionSettings.externalCategory(type)

	@classmethod
	def settingsFiltersStreamHoster(self, type = None):
		OrionInterface.dialogConfirm(title = 32173, message = 33008)
		OrionTools.sleep(0.1)
		OrionInterface.loaderShow()
		enabled = ': ' + OrionInterface.fontColor(32096, OrionInterface.ColorEnabled)
		disabled = ': ' + OrionInterface.fontColor(32057, OrionInterface.ColorDisabled)
		values = OrionSettings.getFiltersStreamHoster(type)
		OrionInterface.loaderHide()
		if values == None or len(values) == 0:
			OrionSettings.externalCategory(type)
			return
		while True:
			ids = []
			items = []
			for key, value in OrionTools.iterator(values):
				ids.append(key)
				items.append(value['name'].upper() + (enabled if value['enabled'] else disabled))
			items, ids = zip(*sorted(zip(items, ids))) # Sort alphabetically
			ids = [None, None, None] + list(ids)
			items = [OrionInterface.fontBold(32151), OrionInterface.fontBold(32149), OrionInterface.fontBold(32150)] + list(items)
			choice = OrionInterface.dialogOptions(title = 32173, items = items)
			if choice <= 0:
				break
			elif choice == 1:
				for i in values.iterkeys():
					values[i]['enabled'] = True
			elif choice == 2:
				for i in values.iterkeys():
					values[i]['enabled'] = False
			else:
				values[ids[choice]]['enabled'] = not values[ids[choice]]['enabled']
			OrionSettings.setFiltersStreamHoster(values, type)
		OrionSettings.externalCategory(type)

	@classmethod
	def settingsFiltersMetaRelease(self, type = None):
		self._settingsFilters(32114, 'getFiltersMetaRelease', 'setFiltersMetaRelease', type)

	@classmethod
	def settingsFiltersMetaUploader(self, type = None):
		self._settingsFilters(32114, 'getFiltersMetaUploader', 'setFiltersMetaUploader', type)

	@classmethod
	def settingsFiltersMetaEdition(self, type = None):
		self._settingsFilters(32114, 'getFiltersMetaEdition', 'setFiltersMetaEdition', type)

	@classmethod
	def settingsFiltersVideoCodec(self, type = None):
		self._settingsFilters(32134, 'getFiltersVideoCodec', 'setFiltersVideoCodec', type)

	@classmethod
	def settingsFiltersAudioType(self, type = None):
		self._settingsFilters(32137, 'getFiltersAudioType', 'setFiltersAudioType', type)

	@classmethod
	def settingsFiltersAudioSystem(self, type = None):
		self._settingsFilters(32200, 'getFiltersAudioSystem', 'setFiltersAudioSystem', type)

	@classmethod
	def settingsFiltersAudioCodec(self, type = None):
		self._settingsFilters(32147, 'getFiltersAudioCodec', 'setFiltersAudioCodec', type)

	@classmethod
	def settingsFiltersAudioLanguages(self, type = None):
		self._settingsFiltersLanguages(32148, 'getFiltersAudioLanguages', 'setFiltersAudioLanguages', type)

	@classmethod
	def settingsFiltersSubtitleType(self, type = None):
		self._settingsFilters(32153, 'getFiltersSubtitleType', 'setFiltersSubtitleType', type)

	@classmethod
	def settingsFiltersSubtitleLanguages(self, type = None):
		self._settingsFiltersLanguages(32154, 'getFiltersSubtitleLanguages', 'setFiltersSubtitleLanguages', type)
