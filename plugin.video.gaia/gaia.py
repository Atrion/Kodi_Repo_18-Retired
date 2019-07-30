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

import urlparse
import sys

from resources.lib.extensions import tools
from resources.lib.extensions import shortcuts

params = dict(urlparse.parse_qsl(sys.argv[2].replace('?','')))

action = params.get('action')
name = params.get('name')
title = params.get('title')
year = params.get('year')
imdb = params.get('imdb')
tmdb = params.get('tmdb')
tvdb = params.get('tvdb')
season = params.get('season')
episode = params.get('episode')
tvshowtitle = params.get('tvshowtitle')
premiered = params.get('premiered')
url = params.get('url')
link = params.get('link')
image = params.get('image')
query = params.get('query')
content = params.get('content')

type = params.get('type')
kids = params.get('kids')
kids = 0 if kids == None or kids == '' else int(kids)

source = params.get('source')
if not source == None:
	source = tools.Converter.dictionary(source)
	if isinstance(source, list):
		source = source[0]

metadata = params.get('metadata')
if not metadata == None: metadata = tools.Converter.dictionary(metadata)

# LEAVE THIS HERE. Can be used by downloadsList for updating the directory list automatically in a thread.
# Stops downloader directory Updates
#if not action == 'download' and not (action == 'downloadsList' and not params.get('status') == None):
#	from resources.lib.extensions import downloader
#	downloader.Downloader.itemsStop()

shortcuts.Shortcuts.process(params)

# Always check, not only on the main menu (action == None), since skin widgets also call the addon.
tools.System.observe()

# Execute on first launch.
if action == None:
	tools.System.launch()

if action == None or action == 'home':
	from resources.lib.indexers import navigator
	navigator.navigator(type = type, kids = kids).root()

####################################################
# MOVIE
####################################################

elif action.startswith('movies'):

	if action == 'movies':
		from resources.lib.indexers import navigator
		lite = tools.Converter.boolean(params.get('lite'))
		navigator.navigator(type = type, kids = kids).movies(lite = lite)

	elif action == 'moviesFavourites':
		from resources.lib.indexers import navigator
		lite = tools.Converter.boolean(params.get('lite'))
		navigator.navigator(type = type, kids = kids).moviesFavourites(lite = lite)

	elif action == 'moviesRetrieve':
		from resources.lib.indexers import movies
		movies.movies(type = type, kids = kids).get(url)

	elif action == 'moviesSearch':
		from resources.lib.indexers import movies
		movies.movies(type = type, kids = kids).search(params.get('terms'))

	elif action == 'moviesSearches':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).moviesSearches()

	elif action == 'moviesPerson':
		from resources.lib.indexers import movies
		movies.movies(type = type, kids = kids).person(params.get('terms'))

	elif action == 'moviesPersons':
		from resources.lib.indexers import movies
		movies.movies(type = type, kids = kids).persons(url)

	elif action == 'moviesHome':
		from resources.lib.indexers import movies
		movies.movies(type = type, kids = kids).home()

	elif action == 'moviesArrivals':
		from resources.lib.indexers import movies
		movies.movies(type = type, kids = kids).arrivals()

	elif action == 'moviesCollections':
		from resources.lib.indexers import movies
		movies.movies(type = type, kids = kids).collections()

	elif action == 'moviesGenres':
		from resources.lib.indexers import movies
		movies.movies(type = type, kids = kids).genres()

	elif action == 'moviesLanguages':
		from resources.lib.indexers import movies
		movies.movies(type = type, kids = kids).languages()

	elif action == 'moviesCertificates':
		from resources.lib.indexers import movies
		movies.movies(type = type, kids = kids).certifications()

	elif action == 'moviesAge':
		from resources.lib.indexers import movies
		movies.movies(type = type, kids = kids).age()

	elif action == 'moviesYears':
		from resources.lib.indexers import movies
		movies.movies(type = type, kids = kids).years()

	elif action == 'moviesUserlists':
		from resources.lib.indexers import movies
		movies.movies(type = type, kids = kids).userlists(mode = params.get('mode'))

	elif action == 'moviesDrugs':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).moviesDrugs()

	elif action == 'moviesRandom':
		from resources.lib.indexers import movies
		movies.movies(type = type, kids = kids).random()

	elif action == 'moviesCategories':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).moviesCategories()

	elif action == 'moviesLists':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).moviesLists()

	elif action == 'moviesPeople':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).moviesPeople()

	elif action == 'moviesWatch':
		from resources.lib.indexers import movies
		movies.movies.markWatch(imdb = imdb, tmdb = tmdb)

	elif action == 'moviesUnwatch':
		from resources.lib.indexers import movies
		movies.movies.markUnwatch(imdb = imdb, tmdb = tmdb)

####################################################
# TV
####################################################

elif action.startswith('shows'):

	if action == 'shows':
		from resources.lib.indexers import navigator
		lite = tools.Converter.boolean(params.get('lite'))
		navigator.navigator(type = type, kids = kids).shows(lite = lite)

	elif action == 'showsFavourites':
		from resources.lib.indexers import navigator
		lite = tools.Converter.boolean(params.get('lite'))
		navigator.navigator(type = type, kids = kids).showsFavourites(lite = lite)

	elif action == 'showsRetrieve':
		from resources.lib.indexers import tvshows
		tvshows.tvshows(type = type, kids = kids).get(url)

	elif action == 'showsSearch':
		from resources.lib.indexers import tvshows
		tvshows.tvshows(type = type, kids = kids).search(params.get('terms'))

	elif action == 'showsSearches':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).showsSearches()

	elif action == 'showsGenres':
		from resources.lib.indexers import tvshows
		tvshows.tvshows(type = type, kids = kids).genres()

	elif action == 'showsNetworks':
		from resources.lib.indexers import tvshows
		tvshows.tvshows(type = type, kids = kids).networks()

	elif action == 'showsCertificates':
		from resources.lib.indexers import tvshows
		tvshows.tvshows(type = type, kids = kids).certifications()

	elif action == 'showsAge':
		from resources.lib.indexers import tvshows
		tvshows.tvshows(type = type, kids = kids).age()

	elif action == 'showsPerson':
		from resources.lib.indexers import tvshows
		tvshows.tvshows(type = type, kids = kids).person(params.get('terms'))

	elif action == 'showsPersons':
		from resources.lib.indexers import tvshows
		tvshows.tvshows(type = type, kids = kids).persons(url)

	elif action == 'showsUserlists':
		from resources.lib.indexers import tvshows
		tvshows.tvshows(type = type, kids = kids).userlists(mode = params.get('mode'))

	elif action == 'showsRandom':
		from resources.lib.indexers import tvshows
		tvshows.tvshows(type = type, kids = kids).random()

	elif action == 'showsHome':
		from resources.lib.indexers import episodes
		episodes.episodes(type = type, kids = kids).home()

	elif action == 'showsArrivals':
		from resources.lib.indexers import episodes
		episodes.episodes(type = type, kids = kids).arrivals()

	elif action == 'showsCalendar':
		from resources.lib.indexers import episodes
		episodes.episodes(type = type, kids = kids).calendar(url)

	elif action == 'showsCalendars':
		from resources.lib.indexers import episodes
		episodes.episodes(type = type, kids = kids).calendars()

	elif action == 'showsCategories':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).showsCategories()

	elif action == 'showsLists':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).showsLists()

	elif action == 'showsPeople':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).showsPeople()

	elif action == 'showsYears':
		from resources.lib.indexers import tvshows
		tvshows.tvshows(type = type, kids = kids).years()

	elif action == 'showsLanguages':
		from resources.lib.indexers import tvshows
		tvshows.tvshows(type = type, kids = kids).languages()

	elif action == 'showsWatch':
		from resources.lib.indexers import tvshows
		tvshows.tvshows.markWatch(title = title, imdb = imdb, tvdb = tvdb)

	elif action == 'showsUnwatch':
		from resources.lib.indexers import tvshows
		tvshows.tvshows.markUnwatch(title = title, imdb = imdb, tvdb = tvdb)

	elif action == 'showsBinge':
		from resources.lib.indexers import tvshows
		tvshows.tvshows(type = type, kids = kids).next(scrape = True, title = title, year = year, imdb = imdb, tvdb = tvdb, season = season, episode = episode)

####################################################
# SEASON
####################################################

elif action.startswith('seasons'):

	if action == 'seasonsRetrieve':
		from resources.lib.indexers import seasons
		seasons.seasons(type = type, kids = kids).get(tvshowtitle, year, imdb, tvdb)

	elif action == 'seasonsUserlists':
		from resources.lib.indexers import seasons
		seasons.seasons(type = type, kids = kids).userlists()

	elif action == 'seasonsList':
		from resources.lib.indexers import seasons
		seasons.seasons(type = type, kids = kids).seasonList(url)

	elif action == 'seasonsWatch':
		from resources.lib.indexers import seasons
		seasons.seasons.markWatch(title = title, imdb = imdb, tvdb = tvdb, season = season)

	elif action == 'seasonsUnwatch':
		from resources.lib.indexers import seasons
		seasons.seasons.markUnwatch(title = title, imdb = imdb, tvdb = tvdb, season = season)

####################################################
# EPISODE
####################################################

elif action.startswith('episodes'):

	if action == 'episodesRetrieve':
		from resources.lib.indexers import episodes
		episodes.episodes(type = type, kids = kids).get(tvshowtitle, year, imdb, tvdb, season, episode)

	elif action == 'episodesUserlists':
		from resources.lib.indexers import episodes
		episodes.episodes(type = type, kids = kids).userlists()

	elif action == 'episodesUnfinished':
		from resources.lib.indexers import episodes
		episodes.episodes(type = type, kids = kids).unfinished()

	elif action == 'episodesWatch':
		from resources.lib.indexers import episodes
		episodes.episodes.markWatch(title = title, imdb = imdb, tvdb = tvdb, season = season, episode = episode)

	elif action == 'episodesUnwatch':
		from resources.lib.indexers import episodes
		episodes.episodes.markUnwatch(title = title, imdb = imdb, tvdb = tvdb, season = season, episode = episode)

####################################################
# SYSTEM
####################################################

elif action.startswith('system'):

	if action == 'systemNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).systemNavigator()

	elif action == 'systemInformation':
		tools.System.information()

	elif action == 'systemManager':
		tools.System.manager()

	elif action == 'systemClean':
		tools.System.clean()

####################################################
# INFORMATION
####################################################

elif action.startswith('information'):

	if action == 'informationNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).informationNavigator()

	elif action == 'informationPremium':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).informationPremium()

	elif action == 'informationSplash':
		from resources.lib.extensions import interface
		interface.Splash.popupFull()

	elif action == 'informationChangelog':
		from resources.lib.extensions import interface
		interface.Changelog.show()

	elif action == 'informationAnnouncement':
		tools.Announcements.show(True)

	elif action == 'informationAbout':
		from resources.lib.extensions import interface
		interface.Splash.popupAbout()

	elif action == 'informationDialog':
		imdb = params.get('imdb')
		tvdb = params.get('tvdb')
		season = params.get('season')
		episode = params.get('episode')
		tools.Information.show(imdb = imdb, tvdb = tvdb, title = title, season = season, episode = episode)

####################################################
# PROMOTIONS
####################################################

elif action.startswith('promotions'):

	if action == 'promotionsNavigator':
		tools.Promotions.navigator(force = tools.Converter.boolean(params.get('force')))

	elif action == 'promotionsSelect':
		tools.Promotions.select(provider = params.get('provider'))

####################################################
# PLAYLIST
####################################################

elif action.startswith('playlist'): # Must be before the 'play' section.

	if action == 'playlistShow':
		tools.Playlist.show()

	elif action == 'playlistClear':
		tools.Playlist.clear()

	elif action == 'playlistAdd':
		label = params.get('label')
		art = params.get('art')
		context = params.get('context')
		tools.Playlist.add(link = link, label = label, metadata = metadata, art = art, context = context)

	elif action == 'playlistRemove':
		label = params.get('label')
		tools.Playlist.remove(label = label)

####################################################
# PLAY
####################################################

elif action.startswith('play'):

	if action == 'play':
		from resources.lib.extensions import interface
		from resources.lib.extensions import core
		interface.Loader.show() # Immediately show the loader, since slow system will take long to show it in play().
		try: binge = int(params.get('binge'))
		except: binge = None
		downloadType = params.get('downloadType')
		downloadId = params.get('downloadId')
		handleMode = params.get('handleMode')
		core.Core(type = type, kids = kids).play(source = source, metadata = metadata, downloadType = downloadType, downloadId = downloadId, handleMode = handleMode, binge = binge)

	if action == 'playCache':
		from resources.lib.extensions import core
		try: binge = int(params.get('binge'))
		except: binge = None
		handleMode = params.get('handleMode')
		core.Core(type = type, kids = kids).playCache(source = source, metadata = metadata, handleMode = handleMode, binge = binge)

	elif action == 'playLocal':
		from resources.lib.extensions import core
		try: binge = int(params.get('binge'))
		except: binge = None
		path = params.get('path')
		downloadType = params.get('downloadType')
		downloadId = params.get('downloadId')
		core.Core(type = type, kids = kids).playLocal(path = path, source = source, metadata = metadata, downloadType = downloadType, downloadId = downloadId, binge = binge)

####################################################
# CLEAR
####################################################

elif action.startswith('clear'):

	if action == 'clearNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).clearNavigator()

	elif action == 'clearAll':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).clearAll()

	elif action == 'clearCache':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).clearCache()

	elif action == 'clearProviders':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).clearProviders()

	elif action == 'clearHistory':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).clearHistory()

	elif action == 'clearShortcuts':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).clearShortcuts()

	elif action == 'clearSearches':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).clearSearches()

	elif action == 'clearTrailers':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).clearTrailers()

	elif action == 'clearDownloads':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).clearDownloads()

	elif action == 'clearTemporary':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).clearTemporary()

	elif action == 'clearViews':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).clearViews()

####################################################
# VERIFICATION
####################################################

elif action.startswith('verification'):

	if action == 'verificationProviders':
		from resources.lib.extensions import verification
		verification.Verification().verifyProviders()

	elif action == 'verificationAccounts':
		from resources.lib.extensions import verification
		verification.Verification().verifyAccounts()

	elif action == 'verificationNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).verificationNavigator()

####################################################
# SEARCH
####################################################

elif action.startswith('search'):

	if action == 'search':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).search()

	elif action == 'searchExact':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).searchExact()

	elif action == 'searchRecent':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).searchRecent()

	elif action == 'searchRecentMovies':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).searchRecentMovies()

	elif action == 'searchRecentShows':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).searchRecentShows()

####################################################
# PROVIDERS
####################################################

elif action.startswith('providers'):

	if action == 'providersNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).providersNavigator()

	elif action == 'providersSettings':
		tools.Settings.launch(category = tools.Settings.CategoryProviders)

	elif action == 'providersSort':
		from resources.lib.extensions import provider
		mode = params.get('mode')
		slot = params.get('slot')
		provider.Provider.sortDialog(mode = mode, slot = slot)

	elif action == 'providersPreset':
		from resources.lib.extensions import provider
		slot = params.get('slot')
		provider.Provider.presetDialog(slot = slot)

	elif action == 'providersOptimization':
		from resources.lib.extensions import provider
		settings = params.get('settings')
		provider.Provider().optimization(settings = settings)

	elif action == 'providersCustomization':
		from resources.lib.extensions import provider
		settings = params.get('settings')
		provider.Provider().customization(settings = settings)

####################################################
# ACCOUNTS
####################################################

elif action.startswith('accounts'):

	if action == 'accountsNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).accountsNavigator()

	elif action == 'accountsSettings':
		tools.Settings.launch(category = tools.Settings.CategoryAccounts)

####################################################
# DOWNLOADS
####################################################

elif action.startswith('download'):

	if action == 'download':
		try:
			from resources.lib.extensions import core
			from resources.lib.extensions import downloader
			from resources.lib.extensions import interface
			interface.Loader.show()
			downloadType = params.get('downloadType')
			downloadId = params.get('downloadId')
			refresh = tools.Converter.boolean(params.get('refresh'))
			downer = downloader.Downloader(downloadType)
			if downloadId == None:
				image = params.get('image')
				handleMode = params.get('handleMode')
				link = core.Core(type = type, kids = kids).sourcesResolve(source, info = True, internal = False, download = True, handleMode = handleMode)['link']
				if link == None:
					interface.Loader.hide()
				else:
					title = tools.Media.title(type = type, metadata = metadata)
					downer.download(media = type, title = title, link = link, image = image, metadata = metadata, source = source, refresh = refresh)
			else:
				downer.download(id = downloadId, forceAction = True, refresh = refresh)
		except:
			interface.Loader.hide()
			tools.Logger.error()

	elif action == 'downloadDetails':
		from resources.lib.extensions import downloader
		downloadType = params.get('downloadType')
		downloadId = params.get('downloadId')
		downloader.Downloader(type = downloadType, id = downloadId).details()

	elif action == 'downloads':
		from resources.lib.indexers import navigator
		downloadType = params.get('downloadType')
		navigator.navigator(type = type, kids = kids).downloads(downloadType)

	elif action == 'downloadsManager':
		from resources.lib.extensions import downloader
		downloadType = params.get('downloadType')
		if downloadType == None: downloadType = downloader.Downloader.TypeManual
		downer = downloader.Downloader(type = downloadType)
		downer.items(status = downloader.Downloader.StatusAll, refresh = False)

	elif action == 'downloadsBrowse':
		from resources.lib.indexers import navigator
		downloadType = params.get('downloadType')
		downloadError = params.get('downloadError')
		navigator.navigator(type = type, kids = kids).downloadsBrowse(downloadType, downloadError)

	elif action == 'downloadsList':
		downloadType = params.get('downloadType')
		downloadStatus = params.get('downloadStatus')
		if downloadStatus == None:
			from resources.lib.indexers import navigator
			navigator.navigator(type = type, kids = kids).downloadsList(downloadType)
		else:
			from resources.lib.extensions import downloader
			downer = downloader.Downloader(downloadType)
			# Do not refresh the list using a thread. Seems like the thread is not always stopped and then it ends with multiple threads updating the list.
			# During the update duration multiple refreshes sometimes happen due to this. Hence, you will see the loader flash multiple times during the 10 secs.
			# Also, with a fresh the front progress dialog also flashes and reset it's focus.
			#downer.items(status = status, refresh = True)
			downer.items(status = downloadStatus, refresh = False)

	elif action == 'downloadsClear':
		downloadType = params.get('downloadType')
		downloadStatus = params.get('downloadStatus')
		if downloadStatus == None:
			from resources.lib.indexers import navigator
			navigator.navigator(type = type, kids = kids).downloadsClear(downloadType)
		else:
			from resources.lib.extensions import downloader
			downer = downloader.Downloader(downloadType)
			downer.clear(status = downloadStatus)

	elif action == 'downloadsRefresh':
		from resources.lib.extensions import downloader
		downloadType = params.get('downloadType')
		downer = downloader.Downloader(downloadType)
		downer.itemsRefresh()

	elif action == 'downloadsSettings':
		from resources.lib.modules import control
		tools.Settings.launch(category = tools.Settings.CategoryDownloads)

	elif action == 'downloadCloud':
		from resources.lib.extensions import core
		core.Core(type = type, kids = kids).sourcesCloud(source)

####################################################
# LIGHTPACK
####################################################

elif action.startswith('lightpack'):

	if action == 'lightpackNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).lightpackNavigator()

	elif action == 'lightpackSwitchOn':
		tools.Lightpack().switchOn(message = True)

	elif action == 'lightpackSwitchOff':
		tools.Lightpack().switchOff(message = True)

	elif action == 'lightpackAnimate':
		force = params.get('force')
		force = True if force == None else tools.Converter.boolean(force)
		tools.Lightpack().animate(force = force, message = True, delay = True)

	elif action == 'lightpackSettings':
		tools.Lightpack().settings()

####################################################
# KIDS
####################################################

elif action.startswith('kids'):

	if action == 'kids':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).kids()

	elif action == 'kidsLock':
		tools.Kids.lock()

	elif action == 'kidsUnlock':
		tools.Kids.unlock()

####################################################
# DOCUMENTARIES
####################################################

elif action.startswith('documentaries'):

	if action == 'documentaries':
		from resources.lib.indexers import navigator
		navigator.navigator(type = tools.Media.TypeDocumentary, kids = kids).movies()

####################################################
# SHORTS
####################################################

elif action.startswith('shorts'):

	if action == 'shorts':
		from resources.lib.indexers import navigator
		navigator.navigator(type = tools.Media.TypeShort, kids = kids).movies()

####################################################
# SHORTS
####################################################

elif action.startswith('channels'):

	if action == 'channels':
		from resources.lib.indexers import channels
		channels.channels(type = type, kids = kids).getGroups()

	elif action == 'channelsRetrieve':
		from resources.lib.indexers import channels
		group = params.get('group')
		channels.channels(type = type, kids = kids).getChannels(group = group)

####################################################
# SERVICES
####################################################

elif action.startswith('services'):

	if action == 'servicesNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).servicesNavigator()

	elif action == 'servicesPremiumNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).servicesPremiumNavigator()

	elif action == 'servicesScraperNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).servicesScraperNavigator()

	elif action == 'servicesResolverNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).servicesResolverNavigator()

	elif action == 'servicesDownloaderNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).servicesDownloaderNavigator()

	elif action == 'servicesUtilityNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).servicesUtilityNavigator()

####################################################
# PREMIUMIZE
####################################################

elif action.startswith('premiumize'):

	if action == 'premiumizeAuthentication':
		from resources.lib.extensions import debrid
		debrid.PremiumizeInterface().accountAuthentication()

	elif action == 'premiumizeNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).premiumizeNavigator()

	elif action == 'premiumizeDownloadsNavigator':
		from resources.lib.indexers import navigator
		lite = tools.Converter.boolean(params.get('lite'))
		navigator.navigator(type = type, kids = kids).premiumizeDownloadsNavigator(lite = lite)

	elif action == 'premiumizeList':
		from resources.lib.extensions import debrid
		debrid.PremiumizeInterface().directoryList()

	elif action == 'premiumizeListAction':
		from resources.lib.extensions import debrid
		item = params.get('item')
		context = params.get('context')
		debrid.PremiumizeInterface().directoryListAction(item, context)

	elif action == 'premiumizeItem':
		from resources.lib.extensions import debrid
		item = params.get('item')
		debrid.PremiumizeInterface().directoryItem(item)

	elif action == 'premiumizeItemAction':
		from resources.lib.extensions import debrid
		item = params.get('item')
		debrid.PremiumizeInterface().directoryItemAction(item)

	elif action == 'premiumizeAdd':
		from resources.lib.extensions import debrid
		debrid.PremiumizeInterface().addManual()

	elif action == 'premiumizeInformation':
		from resources.lib.extensions import debrid
		debrid.PremiumizeInterface().downloadInformation()

	elif action == 'premiumizeAccount':
		from resources.lib.extensions import debrid
		debrid.PremiumizeInterface().account()

	elif action == 'premiumizeWebsite':
		from resources.lib.extensions import debrid
		debrid.Premiumize().website(open = True)

	elif action == 'premiumizeVpn':
		from resources.lib.extensions import debrid
		debrid.Premiumize().vpn(open = True)

	elif action == 'premiumizeClear':
		from resources.lib.extensions import debrid
		debrid.PremiumizeInterface().clear()

	elif action == 'premiumizeSettings':
		tools.Settings.launch(category = tools.Settings.CategoryAccounts)

####################################################
# PREMIUMIZE
####################################################

elif action.startswith('offcloud'):

	if action == 'offcloudNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).offcloudNavigator()

	elif action == 'offcloudDownloadsNavigator':
		from resources.lib.indexers import navigator
		lite = tools.Converter.boolean(params.get('lite'))
		category = params.get('category')
		navigator.navigator(type = type, kids = kids).offcloudDownloadsNavigator(lite = lite, category = category)

	elif action == 'offcloudList':
		from resources.lib.extensions import debrid
		category = params.get('category')
		debrid.OffCloudInterface().directoryList(category = category)

	elif action == 'offcloudListAction':
		from resources.lib.extensions import debrid
		item = params.get('item')
		context = params.get('context')
		debrid.OffCloudInterface().directoryListAction(item = item, context = context)

	elif action == 'poffcloudItem':
		from resources.lib.extensions import debrid
		item = params.get('item')
		debrid.OffCloudInterface().directoryItem(item)

	elif action == 'offcloudItemAction':
		from resources.lib.extensions import debrid
		item = params.get('item')
		debrid.OffCloudInterface().directoryItemAction(item)

	elif action == 'offcloudAdd':
		from resources.lib.extensions import debrid
		category = params.get('category')
		debrid.OffCloudInterface().addManual(category = category)

	elif action == 'offcloudInformation':
		from resources.lib.extensions import debrid
		category = params.get('category')
		debrid.OffCloudInterface().downloadInformation(category = category)

	elif action == 'offcloudAdd':
		from resources.lib.extensions import debrid
		debrid.OffCloudInterface().addManual()

	elif action == 'offcloudAccount':
		from resources.lib.extensions import debrid
		debrid.OffCloudInterface().account()

	elif action == 'offcloudWebsite':
		from resources.lib.extensions import debrid
		debrid.OffCloud().website(open = True)

	elif action == 'offcloudClear':
		from resources.lib.extensions import debrid
		category = params.get('category')
		debrid.OffCloudInterface().clear(category = category)

	elif action == 'offcloudSettings':
		tools.Settings.launch(category = tools.Settings.CategoryAccounts)

	elif action == 'offcloudSettingsLocation':
		from resources.lib.extensions import debrid
		debrid.OffCloudInterface().settingsLocation()

####################################################
# REALDEBRID
####################################################

elif action.startswith('realdebrid'):

	if action == 'realdebridAuthentication':
		from resources.lib.extensions import debrid
		debrid.RealDebridInterface().accountAuthentication()

	elif action == 'realdebridNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).realdebridNavigator()

	elif action == 'realdebridDownloadsNavigator':
		from resources.lib.indexers import navigator
		lite = tools.Converter.boolean(params.get('lite'))
		navigator.navigator(type = type, kids = kids).realdebridDownloadsNavigator(lite = lite)

	elif action == 'realdebridList':
		from resources.lib.extensions import debrid
		debrid.RealDebridInterface().directoryList()

	elif action == 'realdebridListAction':
		from resources.lib.extensions import debrid
		item = params.get('item')
		debrid.RealDebridInterface().directoryListAction(item)

	elif action == 'realdebridAdd':
		from resources.lib.extensions import debrid
		debrid.RealDebridInterface().addManual()

	elif action == 'realdebridInformation':
		from resources.lib.extensions import debrid
		debrid.RealDebridInterface().downloadInformation()

	elif action == 'realdebridAccount':
		from resources.lib.extensions import debrid
		debrid.RealDebridInterface().account()

	elif action == 'realdebridWebsite':
		from resources.lib.extensions import debrid
		debrid.RealDebrid().website(open = True)

	elif action == 'realdebridClear':
		from resources.lib.extensions import debrid
		debrid.RealDebridInterface().clear()

	elif action == 'realdebridSettings':
		tools.Settings.launch(category = tools.Settings.CategoryAccounts)

####################################################
# EASYNEWS
####################################################

elif action.startswith('easynews'):

	if action == 'easynewsNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).easynewsNavigator()

	elif action == 'easynewsAccount':
		from resources.lib.extensions import debrid
		debrid.EasyNewsInterface().account()

	elif action == 'easynewsWebsite':
		from resources.lib.extensions import debrid
		debrid.EasyNews().website(open = True)

	elif action == 'easynewsVpn':
		from resources.lib.extensions import debrid
		debrid.EasyNews().vpn(open = True)

	elif action == 'easynewsSettings':
		tools.Settings.launch(category = tools.Settings.CategoryAccounts)

####################################################
# EMBY
####################################################

elif action.startswith('emby'):

	if action == 'embyNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).embyNavigator()

	elif action == 'embySettings':
		from resources.lib.extensions import emby
		emby.Emby().settings()

	elif action == 'embyWebsite':
		from resources.lib.extensions import emby
		emby.Emby().website(open = True)

####################################################
# ELEMENTUM
####################################################

elif action.startswith('elementum'):

	if action == 'elementumNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).elementumNavigator()

	elif action == 'elementumConnect':
		tools.Elementum.connect(confirm = True)

	elif action == 'elementumInstall':
		tools.Elementum.install()

	elif action == 'elementumLaunch':
		tools.Elementum.launch()

	elif action == 'elementumInterface':
		tools.Elementum.interface()

	elif action == 'elementumSettings':
		tools.Elementum.settings()

####################################################
# QUASAR
####################################################

elif action.startswith('quasar'):

	if action == 'quasarNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).quasarNavigator()

	elif action == 'quasarConnect':
		tools.Quasar.connect(confirm = True)

	elif action == 'quasarInstall':
		tools.Quasar.install()

	elif action == 'quasarLaunch':
		tools.Quasar.launch()

	elif action == 'quasarInterface':
		tools.Quasar.interface()

	elif action == 'quasarSettings':
		tools.Quasar.settings()

####################################################
# RESOLVEURL
####################################################

elif action.startswith('resolveurl'):

	if action == 'resolveurlNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).resolveurlNavigator()

	elif action == 'resolveurlSettings':
		tools.ResolveUrl.settings()

	elif action == 'resolveurlInstall':
		tools.ResolveUrl.enable(refresh = True)

####################################################
# URLRESOLVER
####################################################

elif action.startswith('urlresolver'):

	if action == 'urlresolverNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).urlresolverNavigator()

	elif action == 'urlresolverSettings':
		tools.UrlResolver.settings()

	elif action == 'urlresolverInstall':
		tools.UrlResolver.enable(refresh = True)

####################################################
# OPECRAPERS
####################################################

elif action.startswith('opescrapers'):

	if action == 'opescrapersNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).opescrapersNavigator()

	elif action == 'opescrapersSettings':
		tools.OpeScrapers.settings()

	elif action == 'opescrapersProviders':
		tools.OpeScrapers.providers()

	elif action == 'opescrapersInstall':
		tools.OpeScrapers.enable(refresh = True)

####################################################
# LAMSCRAPERS
####################################################

elif action.startswith('lamscrapers'):

	if action == 'lamscrapersNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).lamscrapersNavigator()

	elif action == 'lamscrapersSettings':
		tools.LamScrapers.settings()

	elif action == 'lamscrapersProviders':
		tools.LamScrapers.providers()

	elif action == 'lamscrapersInstall':
		tools.LamScrapers.enable(refresh = True)

####################################################
# CIVCRAPERS
####################################################

elif action.startswith('civscrapers'):

	if action == 'civscrapersNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).civscrapersNavigator()

	elif action == 'civscrapersSettings':
		tools.CivScrapers.settings()

	elif action == 'civscrapersProviders':
		tools.CivScrapers.providers()

	elif action == 'civscrapersInstall':
		tools.CivScrapers.enable(refresh = True)

####################################################
# GLOSCRAPERS
####################################################

elif action.startswith('gloscrapers'):

	if action == 'gloscrapersNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).gloscrapersNavigator()

	elif action == 'gloscrapersSettings':
		tools.GloScrapers.settings()

	elif action == 'gloscrapersProviders':
		tools.GloScrapers.providers()

	elif action == 'gloscrapersInstall':
		tools.GloScrapers.enable(refresh = True)

####################################################
# UNISCRAPERS
####################################################

elif action.startswith('uniscrapers'):

	if action == 'uniscrapersNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).uniscrapersNavigator()

	elif action == 'uniscrapersSettings':
		tools.UniScrapers.settings()

	elif action == 'uniscrapersProviders':
		tools.UniScrapers.providers()

	elif action == 'uniscrapersInstall':
		tools.UniScrapers.enable(refresh = True)

####################################################
# NANSCRAPERS
####################################################

elif action.startswith('nanscrapers'):

	if action == 'nanscrapersNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).nanscrapersNavigator()

	elif action == 'nanscrapersSettings':
		tools.NanScrapers.settings()

	elif action == 'nanscrapersProviders':
		tools.NanScrapers.providers()

	elif action == 'nanscrapersInstall':
		tools.NanScrapers.enable(refresh = True)

####################################################
# INCSCRAPERS
####################################################

elif action.startswith('incscrapers'):

	if action == 'incscrapersNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).incscrapersNavigator()

	elif action == 'incscrapersSettings':
		tools.IncScrapers.settings()

	elif action == 'incscrapersProviders':
		tools.IncScrapers.providers()

	elif action == 'incscrapersInstall':
		tools.IncScrapers.enable(refresh = True)

####################################################
# PLASCRAPERS
####################################################

elif action.startswith('plascrapers'):

	if action == 'plascrapersNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).plascrapersNavigator()

	elif action == 'plascrapersSettings':
		tools.PlaScrapers.settings()

	elif action == 'plascrapersProviders':
		tools.PlaScrapers.providers()

	elif action == 'plascrapersInstall':
		tools.PlaScrapers.enable(refresh = True)

####################################################
# YODSCRAPERS
####################################################

elif action.startswith('yodscrapers'):

	if action == 'yodscrapersNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).yodscrapersNavigator()

	elif action == 'yodscrapersSettings':
		tools.YodScrapers.settings()

	elif action == 'yodscrapersProviders':
		tools.YodScrapers.providers()

	elif action == 'yodscrapersInstall':
		tools.YodScrapers.enable(refresh = True)

####################################################
# EXTENDEDINFO
####################################################

elif action.startswith('extendedinfo'):

	if action == 'extendedinfoNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).extendedinfoNavigator()

	elif action == 'extendedinfoSettings':
		tools.ExtendedInfo.settings()

	elif action == 'extendedinfoInstall':
		tools.ExtendedInfo.enable()

	elif action == 'extendedinfoLaunch':
		tools.ExtendedInfo.launch()

####################################################
# YOUTUBE
####################################################

elif action.startswith('youtube'):

	if action == 'youtubeNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).youtubeNavigator()

	elif action == 'youtubeSettings':
		tools.YouTube.settings()

	elif action == 'youtubeInstall':
		tools.YouTube.enable()

	elif action == 'youtubeLaunch':
		tools.YouTube.launch()

	elif action == 'youtubeWebsite':
		tools.YouTube.website(open = True)

####################################################
# METAHANDLER
####################################################

elif action.startswith('metahandler'):

	if action == 'metahandlerNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).metahandlerNavigator()

	elif action == 'metahandlerSettings':
		tools.MetaHandler.settings()

	elif action == 'metahandlerInstall':
		tools.MetaHandler.enable(refresh = True)

####################################################
# SPEEDTEST
####################################################

elif action.startswith('speedtest'):

	if action == 'speedtestNavigator':
		from resources.lib.indexers import navigator
		from resources.lib.extensions import speedtest
		speedtest.SpeedTester.participation()
		navigator.navigator().speedtestNavigator()

	elif action == 'speedtest':
		from resources.lib.extensions import speedtest
		speedtest.SpeedTester.select(params.get('update'))

	elif action == 'speedtestGlobal':
		from resources.lib.extensions import speedtest
		speedtest.SpeedTesterGlobal().show(params.get('update'))

	elif action == 'speedtestPremiumize':
		from resources.lib.extensions import speedtest
		speedtest.SpeedTesterPremiumize().show(params.get('update'))

	elif action == 'speedtestOffCloud':
		from resources.lib.extensions import speedtest
		speedtest.SpeedTesterOffCloud().show(params.get('update'))

	elif action == 'speedtestRealDebrid':
		from resources.lib.extensions import speedtest
		speedtest.SpeedTesterRealDebrid().show(params.get('update'))

	elif action == 'speedtestEasyNews':
		from resources.lib.extensions import speedtest
		speedtest.SpeedTesterEasyNews().show(params.get('update'))

	elif action == 'speedtestParticipation':
		from resources.lib.extensions import speedtest
		speedtest.SpeedTester.participation(force = True)

	elif action == 'speedtestComparison':
		from resources.lib.extensions import speedtest
		speedtest.SpeedTester.comparison()

####################################################
# LOTTERY
####################################################

elif action.startswith('lottery'):

	if action == 'lotteryVoucher':
		from resources.lib.extensions import api
		api.Api.lotteryVoucher()

####################################################
# VIEWS
####################################################

elif action.startswith('views'):

	if action == 'viewsNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).viewsNavigator()

	elif action == 'viewsCategoriesNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).viewsCategoriesNavigator()

	elif action == 'views':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).views(content = params.get('content'))

####################################################
# HISTORY
####################################################

elif action.startswith('history'):

	if action == 'history':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).history()

	elif action == 'historyType':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).historyType()

	elif action == 'historyStream':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).historyStream()

####################################################
# IMDB
####################################################

elif action.startswith('imdb'):

	if action == 'imdbMovies':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).imdbMovies()

	elif action == 'imdbTv':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).imdbTv()

	elif action == 'imdbExport':
		from resources.lib.modules import trakt
		trakt.imdbImport()

####################################################
# TRAKT
####################################################

elif action.startswith('trakt'):

	if action == 'traktMovies':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).traktMovies()

	elif action == 'traktMoviesLists':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).traktMoviesLists()

	elif action == 'traktTv':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).traktTv()

	elif action == 'traktTvLists':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).traktTvLists()

	elif action == 'traktManager':
		from resources.lib.modules import trakt
		refresh = params.get('refresh')
		if refresh == None: refresh = True
		else: refresh = tools.Converter.boolean(refresh)
		trakt.manager(imdb = imdb, tvdb = tvdb, season = season, episode = episode, refresh = refresh)

	elif action == 'traktAuthorize':
		from resources.lib.modules import trakt
		trakt.authTrakt()

	elif action == 'traktListAdd':
		from resources.lib.modules import trakt
		trakt.listAdd()

	elif action == 'traktNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).traktNavigator()

	elif action == 'traktImport':
		from resources.lib.modules import trakt
		trakt.imdbImport()

	elif action == 'traktSettings':
		tools.Trakt.settings()

	elif action == 'traktInstall':
		tools.Trakt.enable()

	elif action == 'traktLaunch':
		tools.Trakt.launch()

	elif action == 'traktWebsite':
		tools.Trakt.website(open = True)

####################################################
# NETWORK
####################################################

elif action.startswith('network'):

	if action == 'networkNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).networkNavigator()

	elif action == 'networkInformation':
		from resources.lib.extensions import network
		network.Networker.informationDialog()

####################################################
# VPN
####################################################

elif action.startswith('vpn'):

	if action == 'vpnNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).vpnNavigator()

	elif action == 'vpnVerification':
		from resources.lib.extensions import vpn
		settings = tools.Converter.boolean(params.get('settings'))
		vpn.Vpn().verification(settings = settings)

	elif action == 'vpnConfiguration':
		from resources.lib.extensions import vpn
		settings = tools.Converter.boolean(params.get('settings'))
		vpn.Vpn().configuration(settings = settings)

	elif action == 'vpnSettings':
		from resources.lib.extensions import vpn
		vpn.Vpn().settings()

	elif action == 'vpnLaunch':
		from resources.lib.extensions import vpn
		execution = params.get('execution')
		vpn.Vpn().launch(execution = execution)

####################################################
# EXTENSIONS
####################################################

elif action.startswith('extensions'):

	if action == 'extensions':
		id = params.get('id')
		tools.Extensions.dialog(id = id)

	elif action == 'extensionsNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).extensionsNavigator()

	elif action == 'extensionsAvailableNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).extensionsAvailableNavigator()

	elif action == 'extensionsInstalledNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).extensionsInstalledNavigator()

####################################################
# THEME
####################################################

elif action.startswith('theme'):

	if action == 'themeSkinSelect':
		from resources.lib.extensions import interface
		interface.Skin.select()

	elif action == 'themeIconSelect':
		from resources.lib.extensions import interface
		interface.Icon.select()

####################################################
# BACKUP
####################################################

elif action.startswith('backup'):

	if action == 'backupNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).backupNavigator()

	elif action == 'backupAutomatic':
		tools.Backup.automatic()

	elif action == 'backupImport':
		tools.Backup.manualImport()

	elif action == 'backupExport':
		tools.Backup.manualExport()

	elif action == 'backupReaper':
		tools.Backup.reaper()

####################################################
# SETTINGS
####################################################

elif action.startswith('settings'):

	if action == 'settings':
		from resources.lib.extensions import settings
		settings.Selection().show()

	elif action == 'settingsNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).settingsNavigator()

	elif action == 'settingsHelp':
		try: category = int(params.get('category'))
		except: category = None
		tools.Settings.help(category = category)

	elif action == 'settingsAdvanced':
		from resources.lib.extensions import settings
		settings.Advanced().show()

	elif action == 'settingsWizard':
		from resources.lib.extensions import settings
		settings.Wizard().show()

	elif action == 'settingsAdapt':
		from resources.lib.extensions import settings
		settings.Adaption().show()

	elif action == 'settingsExternal':
		tools.Settings.externalSave(params)

	elif action == 'settingsCustomReleases':
		tools.Settings.customSetReleases(type = type)

	elif action == 'settingsCustomUploaders':
		tools.Settings.customSetUploaders(type = type)

	elif action == 'settingsColor':
		from resources.lib.extensions import interface
		interface.Format.settingsColorUpdate(type = type)

	elif action == 'settingsAlluc':
		from resources.lib.extensions import settings
		settings.Alluc.apiShow()

	elif action == 'settingsProntv':
		from resources.lib.extensions import settings
		settings.Prontv.apiShow()

####################################################
# DONATIONS
####################################################

elif action.startswith('donations'):

	if action == 'donationsNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).donationsNavigator()

	elif action == 'donationsCrypto':
		from resources.lib.extensions import tools
		tools.Donations.show(type = type)

	elif action == 'donationsOther':
		from resources.lib.extensions import tools
		tools.Donations.other()

####################################################
# LEGAL
####################################################

elif action.startswith('legal'):

	if action == 'legalDisclaimer':
		from resources.lib.extensions import interface
		interface.Legal.show(exit = True)

####################################################
# SHORTCUTS
####################################################

elif action.startswith('shortcuts'):

	if action == 'shortcutsShow':
		from resources.lib.extensions import shortcuts
		location = params.get('location')
		id = params.get('id')
		link = params.get('link')
		create = tools.Converter.boolean(params.get('create'))
		delete = tools.Converter.boolean(params.get('delete'))
		shortcuts.Shortcuts().show(location = location, id = id, link = link, name = name, create = create, delete = delete)

	elif action == 'shortcutsNavigator':
		from resources.lib.indexers import navigator
		location = params.get('location')
		navigator.navigator(type = type, kids = kids).shortcutsNavigator(location = location)

	elif action == 'shortcutsOpen':
		from resources.lib.extensions import shortcuts
		location = params.get('location')
		id = params.get('id')
		shortcuts.Shortcuts().open(location = location, id = id)

####################################################
# LIBRARY
####################################################

elif action.startswith('library'):

	if action == 'libraryNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).libraryNavigator()

	elif action == 'libraryLocalNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).libraryLocalNavigator()

	elif action == 'libraryBrowseNavigator':
		from resources.lib.indexers import navigator
		error = tools.Converter.boolean(params.get('error'))
		navigator.navigator(type = type, kids = kids).libraryBrowseNavigator(error = error)

	elif action == 'libraryAdd':
		from resources.lib.extensions import library
		precheck = tools.Converter.boolean(params.get('precheck'), none = True)
		metadata = params.get('metadata')
		title = tools.Converter.quoteFrom(title)
		library.Library(type = type, kids = kids).add(link = link, title = title, year = year, season = season, episode = episode, imdb = imdb, tmdb = tmdb, tvdb = tvdb, metadata = metadata, precheck = precheck)

	elif action == 'libraryResolve':
		from resources.lib.extensions import library
		metadata = params.get('location')
		title = tools.Converter.quoteFrom(title)
		library.Library(type = type, kids = kids).resolve(title = title, year = year, season = season, episode = episode)

	elif action == 'libraryRefresh':
		from resources.lib.extensions import library
		library.Library(type = type).refresh()

	elif action == 'libraryUpdate':
		from resources.lib.extensions import library
		force = tools.Converter.boolean(params.get('force'))
		library.Library(type = type).update(force = force)

	elif action == 'libraryService':
		from resources.lib.extensions import library
		library.Library.service(background = False)

	elif action == 'libraryLocal':
		from resources.lib.extensions import library
		library.Library(type = type).local()

	elif action == 'librarySettings':
		from resources.lib.extensions import library
		library.Library.settings()

####################################################
# SUPPORT
####################################################

elif action.startswith('support'):

	if action == 'supportGuide':
		from resources.lib.extensions import support
		support.Support.guide()

	elif action == 'supportBugs':
		from resources.lib.extensions import support
		support.Support.bugs()

	elif action == 'supportNavigator':
		from resources.lib.extensions import support
		support.Support.navigator()

	elif action == 'supportCategories':
		from resources.lib.extensions import support
		support.Support.categories()

	elif action == 'supportQuestions':
		from resources.lib.extensions import support
		support.Support.questions(int(params.get('id')))

	elif action == 'supportQuestion':
		from resources.lib.extensions import support
		support.Support.question(int(params.get('id')))

####################################################
# ORION
####################################################

elif action.startswith('orion'):

	if action == 'orionNavigator':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).orionNavigator()

	elif action == 'orionSettings':
		try:
			from resources.lib.extensions import orionoid
			orionoid.Orionoid().addonSettings()
		except: pass

	elif action == 'orionLaunch':
		try:
			from resources.lib.extensions import orionoid
			orionoid.Orionoid().addonLaunch()
		except: pass

	elif action == 'orionUninstall':
		try:
			from resources.lib.extensions import orionoid
			orionoid.Orionoid.uninstall()
		except: pass

	elif action == 'orionWebsite':
		try:
			from resources.lib.extensions import orionoid
			orionoid.Orionoid().addonWebsite(open = True)
		except: pass

	elif action == 'orionAccount':
		try:
			from resources.lib.extensions import orionoid
			orionoid.Orionoid().accountDialog()
		except: pass

	elif action == 'orionAnonymous':
		try:
			from resources.lib.extensions import orionoid
			orionoid.Orionoid().accountAnonymous()
		except: pass

	elif action == 'orionVoteUp':
		try:
			from resources.lib.extensions import orionoid
			notification = tools.Converter.boolean(params.get('notification'), none = True)
			orionoid.Orionoid().streamVote(idItem = params.get('idItem'), idStream = params.get('idStream'), vote = orionoid.Orionoid.VoteUp, notification = True if notification == None else notification)
		except: pass

	elif action == 'orionVoteDown':
		try:
			from resources.lib.extensions import orionoid
			notification = tools.Converter.boolean(params.get('notification'), none = True)
			orionoid.Orionoid().streamVote(idItem = params.get('idItem'), idStream = params.get('idStream'), vote = orionoid.Orionoid.VoteDown, notification = True if notification == None else notification)
		except: pass

	elif action == 'orionRemove':
		try:
			from resources.lib.extensions import orionoid
			notification = tools.Converter.boolean(params.get('notification'), none = True)
			orionoid.Orionoid().streamRemove(idItem = params.get('idItem'), idStream = params.get('idStream'), notification = True if notification == None else notification)
		except: pass

####################################################
# SCRAPE
####################################################

elif action.startswith('scrape'):

	if action == 'scrape':
		from resources.lib.extensions import core
		from resources.lib.extensions import interface
		from resources.lib.extensions import trailer
		if not trailer.Trailer.cinemaEnabled() or tools.Settings.getBoolean('automatic.enabled'): interface.Loader.show() # Already show here, since getConstants can take long when retrieving debrid service list.
		try: binge = int(params.get('binge'))
		except: binge = None
		library = tools.Converter.boolean(params.get('library'))
		autoplay = tools.Converter.boolean(params.get('autoplay'), none = True)
		preset = params.get('preset')
		cache = tools.Converter.boolean(params.get('cache'), none = True)
		try: seasoncount = int(params.get('seasoncount'))
		except: seasoncount = None
		items = params.get('items')
		core.Core(type = type, kids = kids).scrape(title = title, year = year, imdb = imdb, tvdb = tvdb, season = season, episode = episode, tvshowtitle = tvshowtitle, premiered = premiered, metadata = metadata, autoplay = autoplay, library = library, preset = preset, binge = binge, cache = cache, seasoncount = seasoncount, items = items)

	elif action == 'scrapeAgain':
		from resources.lib.extensions import core
		core.Core(type = type, kids = kids).scrapeAgain(link = link)

	elif action == 'scrapeManual':
		from resources.lib.extensions import core
		core.Core(type = type, kids = kids).scrapeManual(link = link)

	elif action == 'scrapeAutomatic':
		from resources.lib.extensions import core
		core.Core(type = type, kids = kids).scrapeAutomatic(link = link)

	elif action == 'scrapePreset':
		from resources.lib.extensions import core
		core.Core(type = type, kids = kids).scrapePreset(link = link)

	elif action == 'scrapeSingle':
		from resources.lib.extensions import core
		core.Core(type = type, kids = kids).scrapeSingle(link = link)

	elif action == 'scrapeBinge':
		from resources.lib.extensions import core
		core.Core(type = type, kids = kids).scrapeBinge(link = link)

	elif action == 'scrapeExact':
		from resources.lib.extensions import core
		terms = params.get('terms')
		core.Core(type = type, kids = kids).scrapeExact(terms)

####################################################
# STREAMS
####################################################

elif action.startswith('streams'):

	if action == 'streamsShow':
		from resources.lib.extensions import core
		from resources.lib.extensions import interface
		autoplay = tools.Converter.boolean(params.get('autoplay'))
		if autoplay: interface.Loader.show() # Only for autoplay, since showing the directory has its own loader.
		direct = tools.Converter.boolean(params.get('direct'))
		filter = tools.Converter.boolean(params.get('filterx'))
		library = tools.Converter.boolean(params.get('library'))
		initial = tools.Converter.boolean(params.get('initial'))
		new = tools.Converter.boolean(params.get('new'))
		add = tools.Converter.boolean(params.get('add'))
		process = tools.Converter.boolean(params.get('process'))
		try: binge = int(params.get('binge'))
		except: binge = None
		core.Core(type = type, kids = kids).showStreams(direct = direct, filter = filter, autoplay = autoplay, library = library, initial = initial, new = new, add = add, process = process, binge = binge)

	elif action == 'streamsFilter':
		from resources.lib.extensions import core
		core.Core(type = type, kids = kids).showFilters()

	elif action == 'streamsInformation':
		from resources.lib.extensions import metadata as metadatax
		metadatax.Metadata.showDialog(source = source, metadata = metadata)

	elif action == 'streamsTrailer':
		from resources.lib.extensions import trailer
		art = params.get('art')
		trailer.Trailer(type = type, kids = kids).play(title = title, link = link, art = art)

####################################################
# CONTEXT
####################################################

elif action.startswith('context'):

	if action == 'contextShow':
		from resources.lib.extensions import interface
		context = params.get('context')
		menu = interface.Context()
		menu.jsonFrom(context)
		menu.show()

####################################################
# LINK
####################################################

elif action.startswith('link'):

	if action == 'linkOpen':
		from resources.lib.extensions import network
		from resources.lib.extensions import interface
		try:
			interface.Loader.show() # Needs some time to load. Show busy.
			if 'link' in params:
				link = params.get('link')
			elif 'source' in params:
				link = source['url']
				if 'resolve' in params:
					resolve = params.get('resolve')
					if resolve:
						if 'urlresolved' in source:
							link = source['urlresolved']
						else:
							link = network.Networker().resolve(source, clean = True, resolve = resolve)
				if not link: # Sometimes resolving does not work. Eg: 404 errors.
					link = source['url']
				link = network.Networker(link).link() # Clean link
			tools.System.openLink(link)
		except: pass
		interface.Loader.hide()

	elif action == 'linkCopy':
		from resources.lib.extensions import interface
		from resources.lib.extensions import clipboard
		from resources.lib.extensions import network
		try:
			interface.Loader.show() # Needs some time to load. Show busy.
			if 'link' in params:
				link = params.get('link')
			elif 'source' in params:
				link = source['url']
				if 'resolve' in params:
					resolve = params.get('resolve')
					if resolve:
						if 'urlresolved' in source:
							link = source['urlresolved']
						else:
							link = network.Networker().resolve(source, clean = True, resolve = resolve)
				if not link: # Sometimes resolving does not work. Eg: 404 errors.
					link = source['url']
				link = network.Networker(link).link() # Clean link
			clipboard.Clipboard.copyLink(link, True)
		except: pass
		interface.Loader.hide()

	elif action == 'linkAdd':
		from resources.lib.extensions import core
		core.Core(type = type, kids = kids).addLink(url)

####################################################
# NAVIGATOR
####################################################

elif action.startswith('navigator'):

	if action == 'navigatorTools':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).tools()

	elif action == 'navigatorRefresh':
		from resources.lib.modules import control
		control.refresh()

	elif action == 'navigatorView':
		from resources.lib.modules import views
		views.addView(content)

	elif action == 'navigatorFavourites':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).favourites()

	elif action == 'navigatorArrivals':
		from resources.lib.indexers import navigator
		navigator.navigator(type = type, kids = kids).arrivals()
