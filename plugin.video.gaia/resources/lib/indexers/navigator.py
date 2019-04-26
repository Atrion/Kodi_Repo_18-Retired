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


import os,sys,urlparse,urllib,json,re

from resources.lib.modules import control
from resources.lib.modules import trakt
from resources.lib.modules import views
from resources.lib.extensions import api
from resources.lib.extensions import tools
from resources.lib.extensions import search
from resources.lib.extensions import interface
from resources.lib.extensions import downloader
from resources.lib.extensions import library
from resources.lib.extensions import debrid
from resources.lib.extensions import handler
from resources.lib.extensions import network
from resources.lib.extensions import shortcuts
from resources.lib.extensions import speedtest
from resources.lib.extensions import orionoid
from resources.lib.extensions import metadata as metadatax
from resources.lib.extensions import history as historyx

sysaddon = sys.argv[0]
syshandle = int(sys.argv[1])
addonFanart = control.addonFanart()

class navigator:

	def __init__(self, type = tools.Media.TypeNone, kids = tools.Selection.TypeUndefined):
		self.mType = type
		self.mKids = kids

	def parameterize(self, action, type = None, kids = None, lite = None):
		if type == None: type = self.mType
		if not type == None: action += '&type=%s' % type
		if kids == None: kids = self.mKids
		if not kids == None: action += '&kids=%d' % kids
		if not lite == None: action += '&lite=%d' % lite
		return action

	def kidsOnly(self):
		return self.mKids == tools.Selection.TypeInclude

	def addDirectoryItem(self, name, query, thumb, icon, isAction = True, isFolder = True, iconSpecial = interface.Icon.SpecialNone, library = None):
		try: name = control.lang(name).encode('utf-8')
		except: pass
		url = ('%s?action=%s' % (sysaddon, query)) if isAction == True else query

		if isinstance(library, (tuple, list)):
			type = library[1]
			library = library[0]
		else:
			type = self.mType

		item = control.item(label = name)
		item.addContextMenuItems([interface.Context(mode = interface.Context.ModeGeneric, type = type, kids = self.mKids, link = url, title = name, create = True, library = library).menu()])

		iconIcon, iconThumb, iconPoster, iconBanner = interface.Icon.pathAll(icon = thumb, default = icon, special = iconSpecial)
		item.setArt({'icon': iconIcon, 'thumb': iconThumb, 'poster': iconPoster, 'banner': iconBanner})

		if not addonFanart == None: item.setProperty('Fanart_Image', addonFanart)
		control.addItem(handle = syshandle, url = url, listitem = item, isFolder = isFolder)

	def endDirectory(self, cache = True):
		control.content(syshandle, 'addons')
		control.directory(syshandle, cacheToDisc = cache)

	def root(self):
		if self.kidsRedirect(): return

		promotions = tools.Promotions.enabled()
		if promotions: self.addDirectoryItem(35442, 'promotionsNavigator', 'promotion.png', 'DefaultAddonProgram.png')

		if tools.Settings.getBoolean('interface.menu.shortcuts'): self.shortcutsItems(location = shortcuts.Shortcuts.LocationMain)

		if tools.Settings.getBoolean('interface.menu.movies'): self.addDirectoryItem(32001, self.parameterize('movies', type = tools.Media.TypeMovie), 'movies.png', 'DefaultMovies.png')
		if tools.Settings.getBoolean('interface.menu.shows'): self.addDirectoryItem(32002, self.parameterize('shows', type = tools.Media.TypeShow), 'shows.png', 'DefaultTVShows.png')
		if tools.Settings.getBoolean('interface.menu.documentaries'): self.addDirectoryItem(33470, self.parameterize('documentaries', type = tools.Media.TypeDocumentary), 'documentaries.png', 'DefaultVideo.png')
		if tools.Settings.getBoolean('interface.menu.shorts'): self.addDirectoryItem(33471, self.parameterize('shorts', type = tools.Media.TypeShort), 'shorts.png', 'DefaultVideo.png')
		if tools.Settings.getBoolean('interface.menu.kids'): self.addDirectoryItem(33429, self.parameterize('kids', kids = tools.Selection.TypeInclude), 'kids.png', 'DefaultVideo.png')

		if tools.Settings.getBoolean('interface.menu.favourites'): self.addDirectoryItem(33000, 'navigatorFavourites', 'favourites.png', 'DefaultFavourite.png')
		if tools.Settings.getBoolean('interface.menu.arrivals'): self.addDirectoryItem(33490, self.parameterize('navigatorArrivals'), 'new.png', 'DefaultAddSource.png')
		if tools.Settings.getBoolean('interface.menu.search'): self.addDirectoryItem(32010, 'search', 'search.png', 'DefaultAddonsSearch.png')

		self.addDirectoryItem(32008, 'navigatorTools', 'tools.png', 'DefaultAddonProgram.png')

		self.endDirectory(cache = not promotions) # Do not cache to hide the promotions entry.

	def movies(self, lite = False):
		if tools.Settings.getBoolean('interface.menu.shortcuts'):
			if self.mType == tools.Media.TypeDocumentary: self.shortcutsItems(location = shortcuts.Shortcuts.LocationDocumentaries)
			elif self.mType == tools.Media.TypeShort: self.shortcutsItems(location = shortcuts.Shortcuts.LocationShorts)
			else: self.shortcutsItems(location = shortcuts.Shortcuts.LocationMovies)
		if not self.kidsOnly() and lite == False: self.addDirectoryItem(33000, self.parameterize('moviesFavourites', lite = True), 'favourites.png', 'DefaultFavourite.png')
		self.addDirectoryItem(33490, self.parameterize('moviesArrivals'), 'new.png', 'DefaultAddSource.png', library = 'arrivals')
		self.addDirectoryItem(33001, self.parameterize('moviesCategories'), 'categories.png', 'DefaultTags.png')
		self.addDirectoryItem(33002, self.parameterize('moviesLists'), 'lists.png', 'DefaultVideoPlaylists.png')
		self.addDirectoryItem(32013, self.parameterize('moviesPeople'), 'people.png', 'DefaultActor.png')
		if lite == False: self.addDirectoryItem(32010, self.parameterize('moviesSearches'), 'search.png', 'DefaultAddonsSearch.png')
		self.endDirectory()

	def moviesFavourites(self, lite = False):
		if tools.Settings.getBoolean('interface.menu.shortcuts'):
			if self.mType == tools.Media.TypeDocumentary: self.shortcutsItems(location = shortcuts.Shortcuts.LocationDocumentariesFavourites)
			elif self.mType == tools.Media.TypeShort: self.shortcutsItems(location = shortcuts.Shortcuts.LocationShortsFavourites)
			else: self.shortcutsItems(location = shortcuts.Shortcuts.LocationMoviesFavourites)
		self.addDirectoryItem(32315, self.parameterize('traktMovies'), 'trakt.png', 'DefaultAddonWebSkin.png')
		self.addDirectoryItem(32034, self.parameterize('imdbMovies'), 'imdb.png', 'DefaultAddonWebSkin.png')
		self.addDirectoryItem(32036, self.parameterize('history'), 'history.png', 'DefaultYear.png')
		if not self.kidsOnly() and tools.Settings.getBoolean('library.enabled'): self.addDirectoryItem(35170, self.parameterize('libraryLocal'), 'library.png', 'DefaultAddonLibrary.png', isAction = True, isFolder = False)
		if lite == False: self.addDirectoryItem(32031, self.parameterize('movies', lite = True), 'discover.png', 'DefaultMovies.png')
		self.endDirectory()

	def history(self):
		self.addDirectoryItem(33481, self.parameterize('historyStream', type = self.mType), 'historystreams.png', 'DefaultYear.png', isAction = True, isFolder = False)
		if self.mType in [None, tools.Media.TypeMovie]: self.addDirectoryItem(32001, self.parameterize('historyType', type = tools.Media.TypeMovie), 'historymovies.png', 'DefaultYear.png')
		if self.mType in [None, tools.Media.TypeDocumentary]: self.addDirectoryItem(33470, self.parameterize('historyType', type = tools.Media.TypeDocumentary), 'historydocumentaries.png', 'DefaultYear.png')
		if self.mType in [None, tools.Media.TypeShort]: self.addDirectoryItem(33471, self.parameterize('historyType', type = tools.Media.TypeShort), 'historyshorts.png', 'DefaultYear.png')
		if self.mType in [None, tools.Media.TypeShow, tools.Media.TypeSeason, tools.Media.TypeEpisode]:
			self.addDirectoryItem(32002, self.parameterize('historyType', type = tools.Media.TypeShow), 'historyshows.png', 'DefaultYear.png')
			self.addDirectoryItem(32054, self.parameterize('historyType', type = tools.Media.TypeSeason), 'historyshows.png', 'DefaultYear.png')
			self.addDirectoryItem(32326, self.parameterize('historyType', type = tools.Media.TypeEpisode), 'historyshows.png', 'DefaultYear.png')
		self.endDirectory()

	def historyType(self):
		items = []
		ids = []

		type = self.mType
		if type in [tools.Media.TypeSeason, tools.Media.TypeEpisode]:
			type = tools.Media.TypeShow
		histories = historyx.History().retrieve(type = type, kids = self.mKids)

		for history in histories:
			metadata = tools.Converter.dictionary(history[4])
			id = str(metadata['imdb'])
			if not id in ids:
				items.append(metadata)
				ids.append(id)

		for i in range(len(items)):
			if 'duration' in items[i]:
				try: items[i]['duration'] = int(int(items[i]['duration']) / 60.0)
				except: pass

		if self.mType in [tools.Media.TypeMovie, tools.Media.TypeDocumentary, tools.Media.TypeShort]:
			from resources.lib.indexers import movies
			movies.movies(type = self.mType, kids = self.mKids).movieDirectory(items = items, next = False)
		elif self.mType in [tools.Media.TypeShow]:
			for i in range(len(items)):
				items[i]['title'] = items[i]['tvshowtitle']
				items[i]['rating'] = None # Episode rating, not show's rating.
				items[i]['duration'] = None
			from resources.lib.indexers import tvshows
			tvshows.tvshows(kids = self.mKids).tvshowDirectory(items = items, next = False)
		elif self.mType in [tools.Media.TypeSeason]:
			for i in range(len(items)):
				items[i]['title'] = items[i]['tvshowtitle']
				items[i]['rating'] = None # Episode rating, not season's rating.
				items[i]['duration'] = None
				if 'poster' in items[i]: items[i]['thumb'] = items[i]['poster']
			from resources.lib.indexers import seasons
			seasons.seasons(kids = self.mKids).seasonDirectory(items = items)
		if self.mType in [tools.Media.TypeEpisode]:
			from resources.lib.indexers import episodes
			episodes.episodes(type = self.mType, kids = self.mKids).episodeDirectory(items = items)

	def historyStream(self):
		from resources.lib.extensions import core
		interface.Loader.show()
		items = []
		histories = historyx.History().retrieve(type = self.mType, kids = self.mKids)
		for history in histories:
			metadata = tools.Converter.dictionary(history[4])
			item = tools.Converter.dictionary(history[5])
			if isinstance(item, list): item = item[0]
			item['meta'] = metadata
			items.append(item)
		core.Core(type = self.mType, kids = self.mKids).scrape(items = items, process = False)

	def favourites(self):
		self.addDirectoryItem(32001, self.parameterize('moviesFavourites', type = tools.Media.TypeMovie), 'moviesfavourites.png', 'DefaultFavourite.png')
		self.addDirectoryItem(32002, self.parameterize('showsFavourites', type = tools.Media.TypeShow), 'showsfavourites.png', 'DefaultFavourite.png')
		self.addDirectoryItem(33470, self.parameterize('moviesFavourites', type = tools.Media.TypeDocumentary), 'documentariesfavourites.png', 'DefaultFavourite.png')
		self.addDirectoryItem(33471, self.parameterize('moviesFavourites', type = tools.Media.TypeShort), 'shortsfavourites.png', 'DefaultFavourite.png')
		self.addDirectoryItem(32036, self.parameterize('history', type = None), 'historyfavourites.png', 'DefaultFavourite.png')
		if tools.Settings.getBoolean('library.enabled'):
			self.addDirectoryItem(35170, self.parameterize('libraryLocalNavigator', type = None), 'libraryfavourites.png', 'DefaultAddonProgram.png')
		self.endDirectory()

	def arrivals(self):
		self.addDirectoryItem(32001, self.parameterize('moviesArrivals', type = tools.Media.TypeMovie), 'moviesnew.png', 'DefaultAddSource.png', library = ('arrivals', tools.Media.TypeMovie))
		self.addDirectoryItem(32002, self.parameterize('showsArrivals', type = tools.Media.TypeShow), 'showsnew.png', 'DefaultAddSource.png', library = ('arrivals', tools.Media.TypeShow))
		self.addDirectoryItem(33470, self.parameterize('moviesArrivals', type = tools.Media.TypeDocumentary), 'documentariesnew.png', 'DefaultAddSource.png', library = ('arrivals', tools.Media.TypeDocumentary))
		self.addDirectoryItem(33471, self.parameterize('moviesArrivals', type = tools.Media.TypeShort), 'shortsnew.png', 'DefaultAddSource.png', library = ('arrivals', tools.Media.TypeShort))
		self.endDirectory()

	def search(self):
		self.addDirectoryItem(32001, self.parameterize('moviesSearch', type = tools.Media.TypeMovie), 'searchmovies.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(32002, self.parameterize('showsSearch', type = tools.Media.TypeShow), 'searchshows.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(33470, self.parameterize('moviesSearch', type = tools.Media.TypeDocumentary), 'searchdocumentaries.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(33471, self.parameterize('moviesSearch', type = tools.Media.TypeShort), 'searchshorts.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(32013, self.parameterize('moviesPerson'), 'searchpeople.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(33038, self.parameterize('searchRecent'), 'searchhistory.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(35157, self.parameterize('searchExact'), 'searchexact.png', 'DefaultAddonsSearch.png')
		self.endDirectory()

	def searchExact(self):
		self.addDirectoryItem(32001, self.parameterize('scrapeExact'), 'searchmovies.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(32002, self.parameterize('scrapeExact'), 'searchshows.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(33470, self.parameterize('scrapeExact'), 'searchdocumentaries.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(33471, self.parameterize('scrapeExact'), 'searchshorts.png', 'DefaultAddonsSearch.png')
		self.endDirectory()

	def searchRecent(self):
		searches = search.Searches().retrieveAll(kids = self.mKids)
		for item in searches:
			if item[0] == search.Searches.TypeMovies:
				icon = 'searchmovies.png'
				action = self.parameterize('moviesSearch', type = tools.Media.TypeMovie)
			elif item[0] == search.Searches.TypeShows:
				icon = 'searchshows.png'
				action = self.parameterize('showsSearch', type = tools.Media.TypeShow)
			elif item[0] == search.Searches.TypeDocumentaries:
				icon = 'searchdocumentaries.png'
				action = self.parameterize('moviesSearch', type = tools.Media.TypeDocumentary)
			elif item[0] == search.Searches.TypeShorts:
				icon = 'searchshorts.png'
				action = self.parameterize('moviesSearch', type = tools.Media.TypeShort)
			elif item[0] == search.Searches.TypePeople:
				icon = 'searchpeople.png'
				action = self.parameterize('moviesPerson')
			else:
				continue

			if item[2]:
				icon = 'searchkids.png'

			self.addDirectoryItem(item[1], '%s&terms=%s' % (action, urllib.quote_plus(item[1])), icon, 'DefaultAddonsSearch.png')
		self.endDirectory()

	def searchRecentMovies(self):
		searches = search.Searches().retrieveMovies(kids = self.mKids)
		for item in searches:
			self.addDirectoryItem(item[0], self.parameterize('moviesSearch&terms=%s' % urllib.quote_plus(item[0]), type = tools.Media.TypeMovie), 'searchmovies.png', 'DefaultAddonsSearch.png')
		self.endDirectory()

	def searchRecentShows(self):
		searches = search.Searches().retrieveShows(kids = self.mKids)
		for item in searches:
			self.addDirectoryItem(item[0], self.parameterize('showsSearch&terms=%s' % urllib.quote_plus(item[0]), type = tools.Media.TypeShow), 'searchshows.png', 'DefaultAddonsSearch.png')
		self.endDirectory()

	def searchRecentDocumentaries(self):
		searches = search.Searches().retrieveDocumentaries(kids = self.mKids)
		for item in searches:
			self.addDirectoryItem(item[0], self.parameterize('moviesSearch&terms=%s' % urllib.quote_plus(item[0]), type = tools.Media.TypeDocumentary), 'searchdocumentaries.png', 'DefaultAddonsSearch.png')
		self.endDirectory()

	def searchRecentShorts(self):
		searches = search.Searches().retrieveShorts(kids = self.mKids)
		for item in searches:
			self.addDirectoryItem(item[0], self.parameterize('moviesSearch&terms=%s' % urllib.quote_plus(item[0]), type = tools.Media.TypeShort), 'searchshorts.png', 'DefaultAddonsSearch.png')
		self.endDirectory()

	def tools(self):
		if tools.Settings.getBoolean('interface.menu.shortcuts'): self.shortcutsItems(location = shortcuts.Shortcuts.LocationTools)
		if api.Api.lotteryValid(): self.addDirectoryItem(33876, 'lotteryVoucher', 'tickets.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33011, 'settingsNavigator', 'settings.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33502, 'servicesNavigator', 'services.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33719, 'networkNavigator', 'network.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(32009, 'downloads', 'downloads.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35170, 'libraryNavigator', 'library.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33014, 'providersNavigator', 'provider.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(32346, 'accountsNavigator', 'account.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33017, 'verificationNavigator', 'verification.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33720, 'extensionsNavigator', 'extensions.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33406, 'lightpackNavigator', 'lightpack.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33773, 'backupNavigator', 'backup.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33012, 'viewsNavigator', 'views.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33013, 'clearNavigator', 'clear.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33344, 'informationNavigator', 'information.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(interface.Format.color(33505, 'FFB700'), 'donationsNavigator', 'donations.png', 'DefaultAddonProgram.png', iconSpecial = interface.Icon.SpecialDonations)
		self.endDirectory()

	def settingsNavigator(self):
		self.addDirectoryItem(33894, 'settingsAdvanced', 'settingsadvanced.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33893, 'settingsWizard', 'settingswizard.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		if tools.System.versionKodiNew(): self.addDirectoryItem(35325, 'settingsAdapt', 'settingsadapt.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def backupNavigator(self):
		self.addDirectoryItem(33800, 'backupAutomatic', 'backupautomatic.png', 'DefaultHardDisk.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33774, 'backupImport', 'backupimport.png', 'DefaultHardDisk.png', isAction = True, isFolder = False)
		self.addDirectoryItem(35212, 'backupExport', 'backupexport.png', 'DefaultHardDisk.png', isAction = True, isFolder = False)
		self.endDirectory()

	def viewsNavigator(self):
		self.addDirectoryItem(33001, 'viewsCategoriesNavigator', 'viewscategories.png', 'DefaultHardDisk.png')
		self.addDirectoryItem(33013, 'clearViews', 'viewsclear.png', 'DefaultHardDisk.png', isAction = True, isFolder = False)
		self.endDirectory()

	def viewsCategoriesNavigator(self):
		# NB: Handle is -1 (invalid) when called like this. Open up a dialog instead
		interface.Loader.show()
		items = [
			(control.lang(32001).encode('utf-8'), 'movies'),
			(control.lang(33491).encode('utf-8'), 'documentaries'),
			(control.lang(33471).encode('utf-8'), 'shorts'),
			(control.lang(32002).encode('utf-8'), 'shows'),
			(control.lang(32054).encode('utf-8'), 'seasons'),
			(control.lang(32038).encode('utf-8'), 'episodes'),
		]
		select = interface.Dialog.options(title = 33012, items = [i[0] for i in items])
		interface.Loader.hide()
		if select == -1: return
		self.views(content = items[select][1])

		'''self.addDirectoryItem(32001, 'views&content=movies', 'viewsmovies.png', 'DefaultHardDisk.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33491, 'views&content=documentaries', 'viewsdocumentaries.png', 'DefaultHardDisk.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33471, 'views&content=shorts', 'viewsshorts.png', 'DefaultHardDisk.png', isAction = True, isFolder = False)
		self.addDirectoryItem(32002, 'views&content=shows', 'viewsshows.png', 'DefaultHardDisk.png', isAction = True, isFolder = False)
		self.addDirectoryItem(32054, 'views&content=seasons', 'viewsshows.png', 'DefaultHardDisk.png', isAction = True, isFolder = False)
		self.addDirectoryItem(32326, 'views&content=episodes', 'viewsshows.png', 'DefaultHardDisk.png', isAction = True, isFolder = False)
		self.endDirectory()'''

	def views(self, content):
		try:
			title = control.lang(32059).encode('utf-8')
			url = '%s?action=navigatorView&content=%s' % (sys.argv[0], content)

			item = control.item(label = title)
			item.setInfo(type = 'Video', infoLabels = {'title': title})

			iconIcon, iconThumb, iconPoster, iconBanner = interface.Icon.pathAll(icon = 'views.png', default = 'DefaultProgram.png')
			item.setArt({'icon': iconIcon, 'thumb': iconThumb, 'poster': iconPoster, 'banner': iconBanner})

			fanart = control.addonFanart()
			item.setProperty('Fanart_Image', fanart)

			control.addItem(handle = int(sys.argv[1]), url = url, listitem = item, isFolder = False)
			control.content(int(sys.argv[1]), views.convertView(content))
			control.directory(int(sys.argv[1]), cacheToDisc=True)

			views.setView(content, {})
		except:
			tools.Logger.error()
			return

	def clearNavigator(self):
		self.addDirectoryItem(33029, 'clearAll', 'clear.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33014, 'clearProviders', 'clearproviders.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33353, 'clearWebcache', 'clearcache.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(32036, 'clearHistory', 'clearhistory.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(35119, 'clearShortcuts', 'clearshortcuts.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33041, 'clearSearches', 'clearsearches.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(32009, 'clearDownloads', 'cleardownloads.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33466, 'clearTemporary', 'cleartemporary.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33012, 'clearViews', 'clearviews.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def _clearConfirm(self):
		interface.Loader.hide()
		result = interface.Dialog.option(title = 33013, message = 33042)
		if result: interface.Loader.show()
		return result

	def _clearNotify(self):
		interface.Loader.hide()
		interface.Dialog.notification(title = 33013, message = 33043, icon = interface.Dialog.IconSuccess)

	def clearAll(self, force = False):
		if force or self._clearConfirm():
			self.clearProviders(confirm = False)
			self.clearWebcache(confirm = False)
			self.clearHistory(confirm = False)
			self.clearShortcuts(confirm = False)
			self.clearSearches(confirm = False)
			self.clearDownloads(confirm = False, automatic = True)
			self.clearTemporary(confirm = False)
			self.clearViews(confirm = False)
			self._clearNotify()

	def clearProviders(self, confirm = True):
		if not confirm or self._clearConfirm():
			from resources.lib.extensions import core
			from resources.lib.extensions import provider
			core.Core().clearSources(confirm = False)
			provider.Provider.databaseClear()
			provider.Provider.failureClear()
			if confirm: self._clearNotify()

	def clearWebcache(self, confirm = True):
		if not confirm or self._clearConfirm():
			from resources.lib.modules import cache
			cache.cache_clear()
			if confirm: self._clearNotify()

	def clearHistory(self, confirm = True):
		if not confirm or self._clearConfirm():
			historyx.History().clear(confirm = False)
			if confirm: self._clearNotify()

	def clearShortcuts(self, confirm = True):
		if not confirm or self._clearConfirm():
			shortcuts.Shortcuts().clear(confirm = False)
			if confirm: self._clearNotify()

	def clearSearches(self, confirm = True):
		if not confirm or self._clearConfirm():
			search.Searches().clear(confirm = False)
			if confirm: self._clearNotify()

	def clearDownloads(self, confirm = True, automatic = False):
		from resources.lib.extensions import downloader
		if automatic:
			if not confirm or self._clearConfirm():
				downloader.Downloader(downloader.Downloader.TypeManual).clear(status = downloader.Downloader.StatusAll, automatic = True)
				downloader.Downloader(downloader.Downloader.TypeCache).clear(status = downloader.Downloader.StatusAll, automatic = True)
				if confirm: self._clearNotify()
		else:
			self.addDirectoryItem(33290, 'downloadsClear&type=%s' % downloader.Downloader.TypeManual, 'clearmanual.png', 'DefaultAddonProgram.png')
			self.addDirectoryItem(33016, 'downloadsClear&type=%s' % downloader.Downloader.TypeCache, 'clearcache.png', 'DefaultAddonProgram.png')
			self.endDirectory()

	def clearTemporary(self, confirm = True):
		if not confirm or self._clearConfirm():
			tools.System.temporaryClear()
			if confirm: self._clearNotify()

	def clearViews(self, confirm = True):
		if not confirm or self._clearConfirm():
			from resources.lib.modules import views
			views.clearViews()
			if confirm: self._clearNotify()

	def systemNavigator(self):
		self.addDirectoryItem(33344, 'systemInformation', 'systeminformation.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33472, 'systemManager', 'systemmanager.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33719, 'networkInformation', 'systemnetwork.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33468, 'systemClean', 'systemclear.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def informationNavigator(self):
		self.addDirectoryItem(35442, 'promotionsNavigator&force=1', 'promotion.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33467, 'systemNavigator', 'system.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33239, 'supportNavigator', 'help.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33354, 'linkOpen&link=%s' % tools.Settings.getString('link.website', raw = True), 'network.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33412, 'linkOpen&link=%s' % tools.Settings.getString('link.repository', raw = True), 'cache.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33921, 'linkOpen&link=%s' % tools.Settings.getString('link.support', raw = True), 'help.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(35109, 'legalDisclaimer', 'legal.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33768, 'informationPremium', 'premium.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33503, 'informationChangelog', 'change.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33037, 'informationSplash', 'splash.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(35201, 'informationAnnouncement', 'announcements.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33358, 'informationAbout', 'information.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def donationsNavigator(self):
		for type in tools.Donations.types():
			self.addDirectoryItem(interface.Format.color(type['name'], type['color']), 'donationsCrypto&type=%s' % type['identifier'], type['icon'], 'DefaultAddonProgram.png', iconSpecial = interface.Icon.SpecialDonations)
		self.addDirectoryItem(interface.Format.color('Other Methods', 'FFFFFF'), 'donationsOther', 'donationsother.png', 'DefaultAddonProgram.png', iconSpecial = interface.Icon.SpecialDonations)
		self.endDirectory()

	def informationPremium(self):
		full = ' (%s)' % interface.Translation.string(33458)
		limited = ' (%s)' % interface.Translation.string(33459)
		minimal = ' (%s)' % interface.Translation.string(33460)
		self.addDirectoryItem(interface.Translation.string(33566) + full, 'linkOpen&link=%s' % debrid.Premiumize.website(), 'premiumize.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(interface.Translation.string(35200) + full, 'linkOpen&link=%s' % debrid.OffCloud.website(), 'offcloud.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(interface.Translation.string(33567) + full, 'linkOpen&link=%s' % debrid.RealDebrid.website(), 'realdebrid.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(interface.Translation.string(33794) + limited, 'linkOpen&link=%s' % debrid.EasyNews.website(), 'easynews.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(interface.Translation.string(33568) + minimal, 'linkOpen&link=%s' % debrid.AllDebrid.website(), 'alldebrid.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(interface.Translation.string(33569) + minimal, 'linkOpen&link=%s' % debrid.RapidPremium.website(), 'rapidpremium.png', 'DefaultAddonProgram.png')
		self.endDirectory()

	def traktAccount(self):
		credentials = trakt.getTraktCredentialsInfo()
		if not credentials:
			if interface.Dialog.option(title = 33339, message = 33646, labelConfirm = 33011, labelDeny = 33486):
				tools.Settings.launch(category = tools.Settings.CategoryAccounts)
		return credentials

	def imdbAccount(self):
		if not tools.Settings.getBoolean('accounts.informants.imdb.enabled') or tools.Settings.getString('accounts.informants.imdb.user') == '':
			if interface.Dialog.option(title = 33339, message = 33647, labelConfirm = 33011, labelDeny = 33486):
				tools.Settings.launch(category = tools.Settings.CategoryAccounts)
			return False
		return True

	def traktMovies(self):
		if self.traktAccount():
			self.addDirectoryItem(35308, self.parameterize('moviesRetrieve&url=traktunfinished'), 'traktunfinished.png', 'DefaultAddonWebSkin.png', library = 'traktunfinished')
			self.addDirectoryItem(32036, self.parameterize('moviesRetrieve&url=trakthistory'), 'trakthistory.png', 'DefaultAddonWebSkin.png', library = 'trakthistory')
			self.addDirectoryItem(32032, self.parameterize('moviesRetrieve&url=traktcollection'), 'traktcollections.png', 'DefaultAddonWebSkin.png', library = 'traktcollection')
			self.addDirectoryItem(33662, self.parameterize('moviesRetrieve&url=traktrecommendations'), 'traktfeatured.png', 'DefaultAddonWebSkin.png', library = 'traktrecommendations')
			self.addDirectoryItem(33002, self.parameterize('traktMoviesLists'), 'traktlists.png', 'DefaultAddonWebSkin.png')
			self.endDirectory()

	def traktMoviesLists(self):
		if self.traktAccount():
			self.addDirectoryItem(32520, self.parameterize('traktListAdd'), 'traktadd.png', 'DefaultVideoPlaylists.png')
			self.addDirectoryItem(32033, self.parameterize('moviesRetrieve&url=traktwatchlist'), 'traktwatch.png', 'DefaultVideoPlaylists.png', library = 'traktwatchlist')

			if self.mType == tools.Media.TypeDocumentary: label = 33663
			elif self.mType == tools.Media.TypeShort: label = 33664
			else: label = 32039
			self.addDirectoryItem(label, self.parameterize('moviesUserlists'), 'traktlists.png', 'DefaultVideoPlaylists.png')

			self.endDirectory()

	def traktTv(self):
		if self.traktAccount():
			self.addDirectoryItem(32037, self.parameterize('showsCalendar&url=progress'), 'traktprogress.png', 'DefaultAddonWebSkin.png', library = 'progress')
			self.addDirectoryItem(32027, self.parameterize('showsCalendar&url=mycalendar'), 'traktcalendar.png', 'DefaultAddonWebSkin.png', library = 'mycalendar')
			self.addDirectoryItem(35308, self.parameterize('episodesUnfinished'), 'traktunfinished.png', 'DefaultAddonWebSkin.png', library = 'traktunfinished')
			self.addDirectoryItem(32036, self.parameterize('showsCalendar&url=trakthistory'), 'trakthistory.png', 'DefaultAddonWebSkin.png', library = 'trakthistory')
			self.addDirectoryItem(32032, self.parameterize('showsRetrieve&url=traktcollection'), 'traktcollections.png', 'DefaultAddonWebSkin.png', library = 'traktcollection')
			self.addDirectoryItem(33662, self.parameterize('showsRetrieve&url=traktrecommendations'), 'traktfeatured.png', 'DefaultAddonWebSkin.png', library = 'traktrecommendations')
			self.addDirectoryItem(33002, self.parameterize('traktTvLists'), 'traktlists.png', 'DefaultAddonWebSkin.png')
			self.endDirectory()

	def traktTvLists(self):
		if self.traktAccount():
			self.addDirectoryItem(32520, self.parameterize('traktListAdd'), 'traktadd.png', 'DefaultVideoPlaylists.png')
			self.addDirectoryItem(32033, self.parameterize('showsRetrieve&url=traktwatchlist'), 'traktwatch.png', 'DefaultVideoPlaylists.png', library = 'traktwatchlist')
			self.addDirectoryItem(32040, self.parameterize('showsUserlists'), 'traktlists.png', 'DefaultVideoPlaylists.png')
			self.addDirectoryItem(33665, self.parameterize('seasonsUserlists'), 'traktlists.png', 'DefaultVideoPlaylists.png')
			self.addDirectoryItem(32041, self.parameterize('episodesUserlists'), 'traktlists.png', 'DefaultVideoPlaylists.png')
			self.endDirectory()

	def imdbMovies(self):
		if self.imdbAccount():
			self.addDirectoryItem(32032, self.parameterize('moviesRetrieve&url=imdbwatchlist'), 'imdbcollections.png', 'DefaultAddonWebSkin.png', library = 'imdbwatchlist')
			self.addDirectoryItem(32033, self.parameterize('moviesRetrieve&url=imdbwatchlist2'), 'imdblists.png', 'DefaultAddonWebSkin.png', library = 'imdbwatchlist2')
			self.addDirectoryItem(32035, self.parameterize('moviesRetrieve&url=featured'), 'imdbfeatured.png', 'DefaultAddonWebSkin.png', library = 'featured')
			self.endDirectory()

	def imdbTv(self):
		if self.imdbAccount():
			self.addDirectoryItem(32032, self.parameterize('showsRetrieve&url=imdbwatchlist'), 'imdbcollections.png', 'DefaultTVShows.png', library = 'imdbwatchlist')
			self.addDirectoryItem(32033, self.parameterize('showsRetrieve&url=imdbwatchlist2'), 'imdblists.png', 'DefaultTVShows.png', library = 'imdbwatchlist2')
			self.addDirectoryItem(32035, self.parameterize('showsRetrieve&url=featured'), 'imdbfeatured.png', 'DefaultTVShows.png', library = 'featured')
			self.endDirectory()

	def moviesCategories(self):
		self.addDirectoryItem(35375, self.parameterize('moviesRandom'), 'random.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(32011, self.parameterize('moviesGenres'), 'genres.png', 'DefaultGenre.png')
		self.addDirectoryItem(35526, self.parameterize('moviesYears'), 'calendar.png', 'DefaultYear.png')
		if self.mType == tools.Media.TypeMovie and not self.kidsOnly():
			self.addDirectoryItem(32016, self.parameterize('channels'), 'networks.png', 'DefaultNetwork.png')
			self.addDirectoryItem(33504, self.parameterize('moviesCollections'), 'collections.png', 'DefaultSets.png')
		self.addDirectoryItem(32014, self.parameterize('moviesLanguages'), 'languages.png', 'DefaultCountry.png')
		self.addDirectoryItem(32013, self.parameterize('moviesPersons'), 'people.png', 'DefaultActor.png')
		self.addDirectoryItem(32015, self.parameterize('moviesCertificates'), 'certificates.png', 'DefaultFile.png')
		self.addDirectoryItem(33437, self.parameterize('moviesAge'), 'age.png', 'DefaultYear.png')
		if self.mType == tools.Media.TypeMovie and not self.kidsOnly():
			self.addDirectoryItem(35368, self.parameterize('moviesDrugs'), 'drugs.png', 'DefaultVideoPlaylists.png')
		self.endDirectory()

	def moviesLists(self):
		self.addDirectoryItem(33004, self.parameterize('moviesRetrieve&url=new'), 'new.png', 'DefaultVideoPlaylists.png', library = 'new')
		self.addDirectoryItem(33571, self.parameterize('moviesRetrieve&url=home'), 'home.png', 'DefaultVideoPlaylists.png', library = 'home')
		self.addDirectoryItem(33005, self.parameterize('moviesRetrieve&url=rating'), 'rated.png', 'DefaultVideoPlaylists.png', library = 'rating')
		self.addDirectoryItem(32018, self.parameterize('moviesRetrieve&url=popular'), 'popular.png', 'DefaultVideoPlaylists.png', library = 'popular')
		self.addDirectoryItem(33008, self.parameterize('moviesRetrieve&url=oscars'), 'awards.png', 'DefaultVideoPlaylists.png', library = 'oscars')
		self.addDirectoryItem(33010, self.parameterize('moviesRetrieve&url=boxoffice'), 'tickets.png', 'DefaultVideoPlaylists.png', library = 'boxoffice')
		self.addDirectoryItem(33006, self.parameterize('moviesRetrieve&url=theaters'), 'premiered.png', 'DefaultVideoPlaylists.png', library = 'theaters')
		self.addDirectoryItem(33007, self.parameterize('moviesRetrieve&url=trending'), 'trending.png', 'DefaultVideoPlaylists.png', library = 'trending')
		self.endDirectory()

	def moviesDrugs(self):
		if self.mType == tools.Media.TypeMovie and not self.kidsOnly():
			self.addDirectoryItem(32310, self.parameterize('moviesRetrieve&url=drugsgeneral'), 'drugs.png', 'DefaultVideoPlaylists.png', library = 'drugsgeneral')
			self.addDirectoryItem(35369, self.parameterize('moviesRetrieve&url=drugsalcohol'), 'drugsalcohol.png', 'DefaultVideoPlaylists.png', library = 'drugsalcohol')
			self.addDirectoryItem(35370, self.parameterize('moviesRetrieve&url=drugsmarijuana'), 'drugsmarijuana.png', 'DefaultVideoPlaylists.png', library = 'drugsmarijuana')
			self.addDirectoryItem(35371, self.parameterize('moviesRetrieve&url=drugspsychedelics'), 'drugspsychedelics.png', 'DefaultVideoPlaylists.png', library = 'drugspsychedelics')
			self.endDirectory()

	def moviesPeople(self):
		self.addDirectoryItem(33003, self.parameterize('moviesPersons'), 'browse.png', 'DefaultAddonContextItem.png')
		self.addDirectoryItem(32010, self.parameterize('moviesPerson'), 'search.png', 'DefaultAddonsSearch.png')
		self.endDirectory()

	def moviesSearches(self):
		self.addDirectoryItem(33039, self.parameterize('moviesSearch'), 'searchtitle.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(33040, self.parameterize('moviesSearch'), 'searchdescription.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(32013, self.parameterize('moviesPerson'), 'searchpeople.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(33038, self.parameterize('searchRecentMovies'), 'searchhistory.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(35157, self.parameterize('scrapeExact'), 'searchexact.png', 'DefaultAddonsSearch.png')
		self.endDirectory()

	def shows(self, lite = False):
		if tools.Settings.getBoolean('interface.menu.shortcuts'): self.shortcutsItems(location = shortcuts.Shortcuts.LocationShows)
		if not self.kidsOnly() and lite == False: self.addDirectoryItem(33000, self.parameterize('showsFavourites', lite = True), 'favourites.png', 'DefaultFavourite.png')
		self.addDirectoryItem(33490, self.parameterize('showsArrivals'), 'new.png', 'DefaultAddSource.png', library = 'arrivals')
		self.addDirectoryItem(33001, self.parameterize('showsCategories'), 'categories.png', 'DefaultTags.png')
		self.addDirectoryItem(33002, self.parameterize('showsLists'), 'lists.png', 'DefaultVideoPlaylists.png')
		self.addDirectoryItem(32013, self.parameterize('showsPeople'), 'people.png', 'DefaultTags.png')
		if lite == False: self.addDirectoryItem(32010, self.parameterize('showsSearches'), 'search.png', 'DefaultAddonsSearch.png')
		self.endDirectory()

	def showsFavourites(self, lite = False):
		if tools.Settings.getBoolean('interface.menu.shortcuts'): self.shortcutsItems(location = shortcuts.Shortcuts.LocationShowsFavourites)
		self.addDirectoryItem(32315, self.parameterize('traktTv'), 'trakt.png', 'DefaultAddonWebSkin.png')
		self.addDirectoryItem(32034, self.parameterize('imdbTv'), 'imdb.png', 'DefaultAddonWebSkin.png')
		if not self.kidsOnly(): self.addDirectoryItem(32027, self.parameterize('showsCalendars'), 'calendar.png', 'DefaultYear.png') # Calendar does not have rating, so do not show for kids.
		self.addDirectoryItem(32036, self.parameterize('history'), 'history.png', 'DefaultYear.png')
		if not self.kidsOnly() and tools.Settings.getBoolean('library.enabled'): self.addDirectoryItem(35170, self.parameterize('libraryLocal'), 'library.png', 'DefaultAddonLibrary.png', isAction = True, isFolder = False)
		if lite == False: self.addDirectoryItem(32031, self.parameterize('shows', lite = True), 'discover.png', 'DefaultTVShows.png')
		self.endDirectory()

	def showsCategories(self):
		self.addDirectoryItem(35375, self.parameterize('showsRandom'), 'random.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(32011, self.parameterize('showsGenres'), 'genres.png', 'DefaultGenre.png')
		self.addDirectoryItem(35526, self.parameterize('showsYears'), 'calendar.png', 'DefaultYear.png')
		self.addDirectoryItem(32016, self.parameterize('showsNetworks'), 'networks.png', 'DefaultNetwork.png')
		self.addDirectoryItem(32014, self.parameterize('showsLanguages'), 'languages.png', 'DefaultCountry.png')
		self.addDirectoryItem(32013, self.parameterize('showsPersons'), 'people.png', 'DefaultActor.png')
		self.addDirectoryItem(32015, self.parameterize('showsCertificates'), 'certificates.png', 'DefaultFile.png')
		self.addDirectoryItem(33437, self.parameterize('showsAge'), 'age.png', 'DefaultYear.png')
		self.endDirectory()

	def showsLists(self):
		self.addDirectoryItem(33004, self.parameterize('showsCalendar&url=added'), 'new.png', 'DefaultVideoPlaylists.png', library = 'added')
		self.addDirectoryItem(33571, self.parameterize('showsHome'), 'home.png', 'DefaultVideoPlaylists.png', library = 'home')
		self.addDirectoryItem(33005, self.parameterize('showsRetrieve&url=rating'), 'rated.png', 'DefaultVideoPlaylists.png', library = 'added')
		self.addDirectoryItem(32018, self.parameterize('showsRetrieve&url=popular'), 'popular.png', 'DefaultVideoPlaylists.png', library = 'popular')
		self.addDirectoryItem(33008, self.parameterize('showsRetrieve&url=emmies'), 'awards.png', 'DefaultVideoPlaylists.png', library = 'emmies')
		self.addDirectoryItem(33009, self.parameterize('showsRetrieve&url=airing'), 'aired.png', 'DefaultVideoPlaylists.png', library = 'airing')
		self.addDirectoryItem(33006, self.parameterize('showsRetrieve&url=premiere'), 'premiered.png', 'DefaultVideoPlaylists.png', library = 'premiere')
		self.addDirectoryItem(33007, self.parameterize('showsRetrieve&url=trending'), 'trending.png', 'DefaultVideoPlaylists.png', library = 'trending')
		self.endDirectory()

	def showsPeople(self):
		self.addDirectoryItem(33003, self.parameterize('showsPersons'), 'browse.png', 'DefaultAddonContextItem.png')
		self.addDirectoryItem(32010, self.parameterize('showsPerson'), 'search.png', 'DefaultAddonsSearch.png')
		self.endDirectory()

	def showsSearches(self):
		self.addDirectoryItem(33039, self.parameterize('showsSearch'), 'searchtitle.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(33040, self.parameterize('showsSearch'), 'searchdescription.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(32013, self.parameterize('showsPerson'), 'searchpeople.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(33038, self.parameterize('searchRecentShows'), 'searchhistory.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(35157, self.parameterize('scrapeExact'), 'searchexact.png', 'DefaultAddonsSearch.png')
		self.endDirectory()

	def verificationNavigator(self):
		self.addDirectoryItem(32346, 'verificationAccounts', 'verificationaccount.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33014, 'verificationProviders', 'verificationprovider.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def networkNavigator(self):
		self.addDirectoryItem(33030, 'speedtestNavigator', 'networkspeed.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33344, 'networkInformation', 'networkinformation.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33801, 'vpnNavigator', 'networkvpn.png', 'DefaultAddonProgram.png')
		self.endDirectory()

	def speedtestNavigator(self):
		self.addDirectoryItem(33509, 'speedtestGlobal', 'speedglobal.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33566, 'speedtestPremiumize', 'speedpremiumize.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(35200, 'speedtestOffCloud', 'speedoffcloud.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33567, 'speedtestRealDebrid', 'speedrealdebrid.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33794, 'speedtestEasyNews', 'speedeasynews.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33851, 'speedtestComparison', 'speedcomparison.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33846, 'speedtestParticipation', 'speedparticipation.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def vpnNavigator(self):
		self.addDirectoryItem(33017, 'vpnVerification', 'vpnverification.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33802, 'vpnConfiguration', 'vpnconfiguration.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33011, 'vpnSettings', 'vpnsettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		if debrid.Premiumize().accountValid():
			self.addDirectoryItem(33566, 'premiumizeVpn', 'vpnpremiumize.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		if debrid.EasyNews().accountValid():
			self.addDirectoryItem(33794, 'easynewsVpn', 'vpneasynews.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def libraryNavigator(self):
		self.addDirectoryItem(35183, 'libraryUpdate', 'libraryupdate.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(32314, 'libraryLocalNavigator', 'librarylocal.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33003, 'libraryBrowseNavigator', 'librarybrowse.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33011, 'librarySettings', 'librarysettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def libraryLocalNavigator(self):
		self.addDirectoryItem(32001, self.parameterize('libraryLocal', type = tools.Media.TypeMovie), 'librarymovies.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(32002, self.parameterize('libraryLocal', type = tools.Media.TypeShow), 'libraryshows.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33491, self.parameterize('libraryLocal', type = tools.Media.TypeDocumentary), 'librarydocumentaries.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33471, self.parameterize('libraryLocal', type = tools.Media.TypeShort), 'libraryshorts.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def libraryBrowseNavigator(self, error = False):
		if error:
			message = interface.Translation.string(33068) % self.mType
			interface.Dialog.confirm(title = 35170, message = message)
		else:
			for item in [(tools.Media.TypeMovie, 'movies', 32001), (tools.Media.TypeShow, 'shows', 32002), (tools.Media.TypeDocumentary, 'documentaries', 33491), (tools.Media.TypeShort, 'shorts', 33471)]:
				path = library.Library(type = item[0]).location()
				if tools.File.exists(path):
					action = path
					actionIs = False
				else:
					action = 'libraryBrowse&type=%s&error=%d' % (item[0], int(True))
					actionIs = True
				self.addDirectoryItem(item[2], action, 'library%s.png' % item[1], 'DefaultAddonProgram.png', isAction = actionIs)
			self.endDirectory()

	def providersNavigator(self):
		self.addDirectoryItem(33017, 'verificationProviders', 'providerverification.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(35016, 'providersOptimization', 'providerconfiguration.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33013, 'clearProviders', 'providerclear.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33011, 'providersSettings', 'providersettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def accountsNavigator(self):
		orion = orionoid.Orionoid()
		if orion.accountValid(): self.addDirectoryItem(35400, 'orionAccount', 'accountorion.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33566, 'premiumizeAccount', 'accountpremiumize.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(35200, 'offcloudAccount', 'accountoffcloud.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33567, 'realdebridAccount', 'accountrealdebrid.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33794, 'easynewsAccount', 'accounteasynews.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33017, 'verificationAccounts', 'accountverification.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33011, 'accountsSettings', 'accountsettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def downloads(self, type = None):
		if type == None:
			self.addDirectoryItem(33290, 'downloads&downloadType=%s' % downloader.Downloader.TypeManual, 'downloadsmanual.png', 'DefaultAddonProgram.png')
			self.addDirectoryItem(33016, 'downloads&downloadType=%s' % downloader.Downloader.TypeCache, 'downloadscache.png', 'DefaultAddonProgram.png')
			self.addDirectoryItem(33566, 'premiumizeDownloadsNavigator', 'downloadspremiumize.png', 'DefaultAddonProgram.png')
			self.addDirectoryItem(35200, 'offcloudDownloadsNavigator', 'downloadsoffcloud.png', 'DefaultAddonProgram.png')
			self.addDirectoryItem(33567, 'realdebridDownloadsNavigator', 'downloadsrealdebrid.png', 'DefaultAddonProgram.png')
			self.addDirectoryItem(35316, 'elementumNavigator', 'downloadselementum.png', 'DefaultAddonProgram.png')
			self.addDirectoryItem(33570, 'quasarNavigator', 'downloadsquasar.png', 'DefaultAddonProgram.png')
			self.addDirectoryItem(33011, 'downloadsSettings', 'downloadssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.endDirectory()
		else:
			if downloader.Downloader(type).enabled(notification = True): # Do not use full check, since the download directory might be temporarley down (eg: network), and you still want to access the downloads.
				if tools.Settings.get('downloads.%s.path.selection' % type) == '0':
					path = tools.Settings.path('downloads.%s.path.combined' % type)
					if tools.File.exists(path):
						action = 'downloadsBrowse&downloadType=%s' % (type)
					else:
						action = 'downloadsBrowse&downloadType=%s&downloadError=%d' % (type, int(True))
				else:
					action = 'downloadsBrowse&downloadType=%s' % type
				self.addDirectoryItem(33297, 'downloadsList&downloadType=%s' % type, 'downloadslist.png', 'DefaultAddonProgram.png')
				self.addDirectoryItem(33003, action, 'downloadsbrowse.png', 'DefaultAddonProgram.png', isAction = True)
				self.addDirectoryItem(33013, 'downloadsClear&downloadType=%s' % type, 'downloadsclear.png', 'DefaultAddonProgram.png')
				self.addDirectoryItem(33011, 'downloadsSettings&downloadType=%s' % type, 'downloadssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
				self.endDirectory()

	def downloadsBrowse(self, type = None, error = False):
		if error:
			downloader.Downloader(type).notificationLocation()
		else:
			downer = downloader.Downloader(type = type)
			for item in [(downloader.Downloader.MediaMovie, 'movies', 32001), (downloader.Downloader.MediaShow, 'shows', 32002), (downloader.Downloader.MediaDocumentary, 'documentaries', 33491), (downloader.Downloader.MediaShort, 'shorts', 33471), (downloader.Downloader.MediaOther, 'other', 35149)]:
				path = downer._location(item[0])
				if tools.File.exists(path):
					action = path
					actionIs = False
				else:
					action = 'downloadsBrowse&downloadType=%s&downloadError=%d' % (type, int(True))
					actionIs = True
				self.addDirectoryItem(item[2], action, 'downloads%s.png' % item[1], 'DefaultAddonProgram.png', isAction = actionIs)
			self.endDirectory()

	def downloadsList(self, type):
		self.addDirectoryItem(33029, 'downloadsList&downloadType=%s&downloadStatus=%s' % (type, downloader.Downloader.StatusAll), 'downloadslist.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33291, 'downloadsList&downloadType=%s&downloadStatus=%s' % (type, downloader.Downloader.StatusBusy), 'downloadsbusy.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33292, 'downloadsList&downloadType=%s&downloadStatus=%s' % (type, downloader.Downloader.StatusPaused), 'downloadspaused.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33294, 'downloadsList&downloadType=%s&downloadStatus=%s' % (type, downloader.Downloader.StatusCompleted), 'downloadscompleted.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33295, 'downloadsList&downloadType=%s&downloadStatus=%s' % (type, downloader.Downloader.StatusFailed), 'downloadsfailed.png', 'DefaultAddonProgram.png')
		self.endDirectory()

	def downloadsClear(self, type):
		self.addDirectoryItem(33029, 'downloadsClear&downloadType=%s&downloadStatus=%s' % (type, downloader.Downloader.StatusAll), 'clearlist.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33291, 'downloadsClear&downloadType=%s&downloadStatus=%s' % (type, downloader.Downloader.StatusBusy), 'clearbusy.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33292, 'downloadsClear&downloadType=%s&downloadStatus=%s' % (type, downloader.Downloader.StatusPaused), 'clearpaused.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33294, 'downloadsClear&downloadType=%s&downloadStatus=%s' % (type, downloader.Downloader.StatusCompleted), 'clearcompleted.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33295, 'downloadsClear&downloadType=%s&downloadStatus=%s' % (type, downloader.Downloader.StatusFailed), 'clearfailed.png', 'DefaultAddonProgram.png')
		self.endDirectory()

	def servicesNavigator(self):
		self.addDirectoryItem(35400, 'orionNavigator', 'orion.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33768, 'servicesPremiumNavigator', 'premium.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33749, 'servicesScraperNavigator', 'scraper.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35328, 'servicesResolverNavigator', 'change.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35329, 'servicesDownloaderNavigator', 'downloads.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35330, 'servicesUtilityNavigator', 'utility.png', 'DefaultAddonProgram.png')
		self.endDirectory()

	def servicesPremiumNavigator(self):
		self.addDirectoryItem(33566, 'premiumizeNavigator', 'premiumize.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35200, 'offcloudNavigator', 'offcloud.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33567, 'realdebridNavigator', 'realdebrid.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33794, 'easynewsNavigator', 'easynews.png', 'DefaultAddonProgram.png')
		self.endDirectory()

	def servicesScraperNavigator(self):
		self.addDirectoryItem(35548, 'opescrapersNavigator', 'opescrapers.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35431, 'lamscrapersNavigator', 'lamscrapers.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35504, 'civscrapersNavigator', 'civscrapers.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35460, 'gloscrapersNavigator', 'gloscrapers.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35331, 'uniscrapersNavigator', 'uniscrapers.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35332, 'nanscrapersNavigator', 'nanscrapers.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35334, 'incscrapersNavigator', 'incscrapers.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35333, 'plascrapersNavigator', 'plascrapers.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35456, 'yodscrapersNavigator', 'yodscrapers.png', 'DefaultAddonProgram.png')
		self.endDirectory()

	def servicesResolverNavigator(self):
		self.addDirectoryItem(35310, 'resolveurlNavigator', 'resolveurl.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33747, 'urlresolverNavigator', 'urlresolver.png', 'DefaultAddonProgram.png')
		self.endDirectory()

	def servicesDownloaderNavigator(self):
		self.addDirectoryItem(35316, 'elementumNavigator', 'elementum.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33570, 'quasarNavigator', 'quasar.png', 'DefaultAddonProgram.png')
		self.endDirectory()

	def servicesUtilityNavigator(self):
		self.addDirectoryItem(32315, 'traktNavigator', 'trakt.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35296, 'youtubeNavigator', 'youtube.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35203, 'metahandlerNavigator', 'metahandler.png', 'DefaultAddonProgram.png')
		self.endDirectory()

	def orionNavigator(self):
		orion = orionoid.Orionoid()
		self.addDirectoryItem(33256, 'orionLaunch', 'orionlaunch.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		if orion.accountAnonymousEnabled(): self.addDirectoryItem(35428, self.parameterize('orionAnonymous'), 'orion.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		if orion.accountValid(): self.addDirectoryItem(33339, 'orionAccount', 'orionaccount.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		if orion.accountFree(): self.addDirectoryItem(33768, 'orionWebsite', 'orionpremium.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33011, 'orionSettings', 'orionsettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33354, 'orionWebsite', 'orionweb.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def premiumizeNavigator(self):
		valid = debrid.Premiumize().accountValid()
		if valid:
			self.addDirectoryItem(32009, 'premiumizeDownloadsNavigator&lite=1', 'premiumizedownloads.png', 'DefaultAddonProgram.png')
			self.addDirectoryItem(33339, 'premiumizeAccount', 'premiumizeaccount.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33030, 'speedtestPremiumize', 'premiumizespeed.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33011, 'premiumizeSettings', 'premiumizesettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33354, 'premiumizeWebsite', 'premiumizeweb.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def premiumizeDownloadsNavigator(self, lite = False):
		valid = debrid.Premiumize().accountValid()
		if valid:
			self.addDirectoryItem(33297, 'premiumizeList', 'downloadslist.png', 'DefaultAddonProgram.png')
			self.addDirectoryItem(35069, 'premiumizeAdd', 'downloadsadd.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33013, 'premiumizeClear', 'downloadsclear.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33344, 'premiumizeInformation', 'downloadsinformation.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		if not lite:
			self.addDirectoryItem(33011, 'premiumizeSettings', 'downloadssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def offcloudNavigator(self):
		valid = debrid.OffCloud().accountValid()
		if valid:
			self.addDirectoryItem(32009, 'offcloudDownloadsNavigator&lite=1', 'offclouddownloads.png', 'DefaultAddonProgram.png')
			self.addDirectoryItem(33339, 'offcloudAccount', 'offcloudaccount.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33030, 'speedtestOffCloud', 'offcloudspeed.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33011, 'offcloudSettings', 'offcloudsettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33354, 'offcloudWebsite', 'offcloudweb.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def offcloudDownloadsNavigator(self, lite = False, category = None):
		valid = debrid.OffCloud().accountValid()
		if category == None:
			self.addDirectoryItem(35205, 'offcloudDownloadsNavigator&category=instant', 'downloadsinstant.png', 'DefaultAddonProgram.png')
			self.addDirectoryItem(35206, 'offcloudDownloadsNavigator&category=cloud', 'downloadscloud.png', 'DefaultAddonProgram.png')
			if valid:
				self.addDirectoryItem(35069, 'offcloudAdd', 'downloadsadd.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
				self.addDirectoryItem(33013, 'offcloudClear', 'downloadsclear.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
				self.addDirectoryItem(33344, 'offcloudInformation', 'downloadsinformation.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			if not lite:
				self.addDirectoryItem(33011, 'offcloudSettings', 'downloadssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else:
			if valid:
				self.addDirectoryItem(33297, 'offcloudList&category=%s' % category, 'downloadslist.png', 'DefaultAddonProgram.png')
				self.addDirectoryItem(35069, 'offcloudAdd&category=%s' % category, 'downloadsadd.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			if not lite:
				if valid: self.addDirectoryItem(33013, 'offcloudClear&category=%s' % category, 'downloadsclear.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			if valid:
				self.addDirectoryItem(33344, 'offcloudInformation&category=%s' % category, 'downloadsinformation.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def realdebridNavigator(self):
		valid = debrid.RealDebrid().accountValid()
		if valid:
			self.addDirectoryItem(32009, 'realdebridDownloadsNavigator&lite=1', 'realdebriddownloads.png', 'DefaultAddonProgram.png')
			self.addDirectoryItem(33339, 'realdebridAccount', 'realdebridaccount.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33030, 'speedtestRealDebrid', 'realdebridspeed.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33011, 'realdebridSettings', 'realdebridsettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33354, 'realdebridWebsite', 'realdebridweb.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def realdebridDownloadsNavigator(self, lite = False):
		valid = debrid.RealDebrid().accountValid()
		if valid:
			self.addDirectoryItem(33297, 'realdebridList', 'downloadslist.png', 'DefaultAddonProgram.png')
			self.addDirectoryItem(35069, 'realdebridAdd', 'downloadsadd.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33013, 'realdebridClear', 'downloadsclear.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33344, 'realdebridInformation', 'downloadsinformation.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		if not lite:
			self.addDirectoryItem(33011, 'realdebridSettings', 'downloadssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def easynewsNavigator(self):
		if debrid.EasyNews().accountValid():
			self.addDirectoryItem(33339, 'easynewsAccount', 'easynewsaccount.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33030, 'speedtestEasyNews', 'easynewsspeed.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33354, 'easynewsWebsite', 'easynewsweb.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def elementumNavigator(self):
		if tools.Elementum.connected():
			self.addDirectoryItem(33256, 'elementumLaunch', 'elementumlaunch.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33477, 'elementumInterface', 'elementumweb.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33011, 'elementumSettings', 'elementumsettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else:
			self.addDirectoryItem(33474, 'elementumInstall', 'elementuminstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def quasarNavigator(self):
		if tools.Quasar.connected():
			self.addDirectoryItem(33256, 'quasarLaunch', 'quasarlaunch.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33477, 'quasarInterface', 'quasarweb.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33011, 'quasarSettings', 'quasarsettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else:
			self.addDirectoryItem(33474, 'quasarInstall', 'quasarinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def traktNavigator(self):
		if tools.Trakt.installed():
			self.addDirectoryItem(33256, 'traktLaunch', 'traktlaunch.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33011, 'traktSettings', 'traktsettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else:
			self.addDirectoryItem(33474, 'traktInstall', 'traktinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33354, 'traktWebsite', 'traktweb.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def resolveurlNavigator(self):
		if tools.ResolveUrl.installed():
			self.addDirectoryItem(33011, 'resolveurlSettings', 'resolveurlsettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else:
			self.addDirectoryItem(33474, 'resolveurlInstall', 'resolveurlinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def urlresolverNavigator(self):
		if tools.UrlResolver.installed():
			self.addDirectoryItem(33011, 'urlresolverSettings', 'urlresolversettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else:
			self.addDirectoryItem(33474, 'urlresolverInstall', 'urlresolverinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def opescrapersNavigator(self):
		if tools.OpeScrapers.installed():
			self.addDirectoryItem(33011, 'opescrapersSettings', 'opescraperssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else:
			self.addDirectoryItem(33474, 'opescrapersInstall', 'opescrapersinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def lamscrapersNavigator(self):
		if tools.LamScrapers.installed():
			self.addDirectoryItem(33011, 'lamscrapersSettings', 'lamscraperssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else:
			self.addDirectoryItem(33474, 'lamscrapersInstall', 'lamscrapersinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def civscrapersNavigator(self):
		if tools.CivScrapers.installed():
			self.addDirectoryItem(33011, 'civscrapersSettings', 'civscraperssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else:
			self.addDirectoryItem(33474, 'civscrapersInstall', 'civscrapersinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def gloscrapersNavigator(self):
		if tools.GloScrapers.installed():
			self.addDirectoryItem(33011, 'gloscrapersSettings', 'gloscraperssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else:
			self.addDirectoryItem(33474, 'gloscrapersInstall', 'gloscrapersinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def uniscrapersNavigator(self):
		if tools.UniScrapers.installed():
			self.addDirectoryItem(33011, 'uniscrapersSettings', 'uniscraperssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else:
			self.addDirectoryItem(33474, 'uniscrapersInstall', 'uniscrapersinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def nanscrapersNavigator(self):
		if tools.NanScrapers.installed():
			self.addDirectoryItem(33011, 'nanscrapersSettings', 'nanscraperssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else:
			self.addDirectoryItem(33474, 'nanscrapersInstall', 'nanscrapersinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def incscrapersNavigator(self):
		if tools.IncScrapers.installed():
			self.addDirectoryItem(33011, 'incscrapersSettings', 'incscraperssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else:
			self.addDirectoryItem(33474, 'incscrapersInstall', 'incscrapersinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def plascrapersNavigator(self):
		if tools.PlaScrapers.installed():
			self.addDirectoryItem(33011, 'plascrapersSettings', 'plascraperssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else:
			self.addDirectoryItem(33474, 'plascrapersInstall', 'plascrapersinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def yodscrapersNavigator(self):
		if tools.YodScrapers.installed():
			self.addDirectoryItem(33011, 'yodscrapersSettings', 'yodscraperssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else:
			self.addDirectoryItem(33474, 'yodscrapersInstall', 'yodscrapersinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def youtubeNavigator(self):
		if tools.YouTube.installed():
			self.addDirectoryItem(33256, 'youtubeLaunch', 'youtubelaunch.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33011, 'youtubeSettings', 'youtubesettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else:
			self.addDirectoryItem(33474, 'youtubeInstall', 'youtubeinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33354, 'youtubeWebsite', 'youtubeweb.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def metahandlerNavigator(self):
		if tools.MetaHandler.installed():
			self.addDirectoryItem(33011, 'metahandlerSettings', 'metahandlersettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else:
			self.addDirectoryItem(33474, 'metahandlerInstall', 'metahandlerinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def extensionsNavigator(self):
		self.addDirectoryItem(33721, 'extensionsAvailableNavigator', 'extensionsavailable.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33722, 'extensionsInstalledNavigator', 'extensionsinstalled.png', 'DefaultAddonProgram.png')
		self.endDirectory()

	def extensionsAvailableNavigator(self):
		extensions = tools.Extensions.list()
		for extension in extensions:
			if not extension['installed']:
				self.addDirectoryItem(extension['name'], 'extensions&id=%s' % extension['id'], extension['icon'], 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def extensionsInstalledNavigator(self):
		extensions = tools.Extensions.list()
		for extension in extensions:
			if extension['installed']:
				self.addDirectoryItem(extension['name'], 'extensions&id=%s' % extension['id'], extension['icon'], 'DefaultAddonProgram.png')
		self.endDirectory()

	def lightpackNavigator(self):
		if tools.Lightpack().enabled():
			self.addDirectoryItem(33407, 'lightpackSwitchOn', 'lightpackon.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33408, 'lightpackSwitchOff', 'lightpackoff.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33409, 'lightpackAnimate', 'lightpackanimate.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33011, 'lightpackSettings', 'lightpacksettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def kidsRedirect(self):
		if tools.Kids.locked():
			self.kids()
			return True
		return False

	def kids(self):
		kids = tools.Selection.TypeInclude
		if tools.Settings.getBoolean('interface.menu.movies'):
			self.addDirectoryItem(32001, self.parameterize('movies', type = tools.Media.TypeMovie, kids = kids), 'movies.png', 'DefaultMovies.png')
		if tools.Settings.getBoolean('interface.menu.shows'):
			self.addDirectoryItem(32002, self.parameterize('shows', type = tools.Media.TypeShow, kids = kids), 'shows.png', 'DefaultTVShows.png')
		if tools.Settings.getBoolean('interface.menu.documentaries'):
			self.addDirectoryItem(33470, self.parameterize('documentaries', type = tools.Media.TypeDocumentary, kids = kids), 'documentaries.png', 'DefaultVideo.png')
		if tools.Settings.getBoolean('interface.menu.shorts'):
			self.addDirectoryItem(33471, self.parameterize('shorts', type = tools.Media.TypeShort, kids = kids), 'shorts.png', 'DefaultVideo.png')

		if tools.Settings.getBoolean('interface.menu.arrivals'):
			self.addDirectoryItem(33490, self.parameterize('navigatorArrivals', kids = kids), 'new.png', 'DefaultAddSource.png')
		if tools.Settings.getBoolean('interface.menu.search'):
			self.addDirectoryItem(32010, self.parameterize('search', kids = kids), 'search.png', 'DefaultAddonsSearch.png')

		if tools.Kids.lockable():
			self.addDirectoryItem(33442, 'kidsLock', 'lock.png', 'DefaultAddonService.png')
		elif tools.Kids.unlockable():
			self.addDirectoryItem(33443, 'kidsUnlock', 'unlock.png', 'DefaultAddonService.png')

		self.endDirectory()

	def shortcutsNavigator(self, location):
		values = shortcuts.Shortcuts().retrieve(location = location)
		if len(values) > 1:
			for value in values:
				self.shortcutsItem(location, value[0], value[1], value[2])
			self.endDirectory()

	def shortcutsItems(self, location):
		values = shortcuts.Shortcuts().retrieve(location = location)
		if len(values) == 1:
			self.shortcutsItem(location, values[0][0], values[0][1], values[0][2])
		elif len(values) > 1:
			self.addDirectoryItem(35119, self.parameterize('shortcutsNavigator&location=%s' % location), 'shortcuts.png', 'DefaultAddonProgram.png')

	def shortcutsItem(self, location, id, link, name):
		link = shortcuts.Shortcuts.parameterize(link, location, id)
		id = str(id)
		item = control.item(label = name)
		item.addContextMenuItems([interface.Context(mode = interface.Context.ModeGeneric, type = self.mType, kids = self.mKids, id = id, location = location, delete = True).menu()])

		iconIcon, iconThumb, iconPoster, iconBanner = interface.Icon.pathAll(icon = 'shortcuts.png', default = 'DefaultAddonProgram.png')
		item.setArt({'icon': iconIcon, 'thumb': iconThumb, 'poster': iconPoster, 'banner': iconBanner})
		if not addonFanart == None: item.setProperty('Fanart_Image', addonFanart)

		# Kodi 18 has problems with calling Container.Update/RunPlugin from another plugin call.
		# Instead, show the content directly here without going through shortcutsOpen first.
		# shortcuts.Shortcuts.process(params) was added to gaia.py top handle the count update with the new way.
		#control.addItem(handle = syshandle, url = '%s?action=shortcutsOpen&location=%s&id=%s' % (sysaddon, location, id), listitem = item, isFolder = True)
		control.addItem(handle = syshandle, url = link, listitem = item, isFolder = not shortcuts.Shortcuts.direct(link))
