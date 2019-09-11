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

import os,re,imp,json,urlparse,time,base64,threading,xbmc

from resources.lib.modules import control
from resources.lib.modules import cleandate
from resources.lib.modules import client
from resources.lib.modules import utils
from resources.lib.extensions import tools
from resources.lib.extensions import cache
from resources.lib.extensions import interface
from resources.lib.extensions import database
from resources.lib.extensions import clipboard

trakt1 = None
trakt2 = None

def getTrakt1():
	global trakt1
	if trakt1 == None: trakt1 = tools.System.obfuscate(tools.Settings.getString('internal.trakt.api.1', raw = True))
	return trakt1

def getTrakt2():
	global trakt2
	if trakt2 == None: trakt2 = tools.System.obfuscate(tools.Settings.getString('internal.trakt.api.2', raw = True))
	return trakt2

databaseName = control.cacheFile
databaseTable = 'trakt'

def getTrakt(url, post = None, cache = True, check = True, timestamp = None, extended = False, direct = False, authentication = None, timeout = 30):
	try:
		if not url.startswith('http://api-v2launch.trakt.tv'):
			url = urlparse.urljoin('http://api-v2launch.trakt.tv', url)

		if authentication:
			valid = True
			token = authentication['token']
			refresh = authentication['refresh']
		else:
			valid = getTraktCredentialsInfo() == True
			token = tools.Settings.getString('accounts.informants.trakt.token')
			refresh = tools.Settings.getString('accounts.informants.trakt.refresh')

		headers = {'Content-Type': 'application/json', 'trakt-api-key': getTrakt1(), 'trakt-api-version': '2'}

		if not post == None: post = json.dumps(post)

		if direct or not valid:
			result = client.request(url, post = post, headers = headers, timeout = timeout)
			return result

		headers['Authorization'] = 'Bearer %s' % token
		result = client.request(url, post = post, headers = headers, output = 'extended', error = True, timeout = timeout)
		if result and not (result[1] == '401' or result[1] == '405'):
			if check: _cacheCheck()
			if extended: return result[0], result[2]
			else: return result[0]

		try: code = str(result[1])
		except: code = ''

		if code.startswith('5') or (result and isinstance(result, basestring) and '<html' in result) or not result:
			return _error(url = url, post = post, timestamp = timestamp, message = 33676)

		oauth = 'http://api-v2launch.trakt.tv/oauth/token'
		opost = {'client_id': getTrakt1(), 'client_secret': getTrakt2(), 'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob', 'grant_type': 'refresh_token', 'refresh_token': refresh}

		result = client.request(oauth, post = json.dumps(opost), headers = headers, error = True, timeout = timeout)

		try: code = str(result[1])
		except: code = ''

		if code.startswith('5') or not result or (result and isinstance(result, basestring) and '<html' in result):
			return _error(url = url, post = post, timestamp = timestamp, message = 33676)
		elif result and code in ['404']:
			return _error(url = url, post = post, timestamp = timestamp, message = 33786)
		elif result and code in ['401', '405']:
			return _error(url = url, post = post, timestamp = timestamp, message = 33677)

		result = json.loads(result)

		token, refresh = result['access_token'], result['refresh_token']
		tools.Settings.set('accounts.informants.trakt.token', token)
		tools.Settings.set('accounts.informants.trakt.refresh', refresh)

		headers['Authorization'] = 'Bearer %s' % token

		result = client.request(url, post = post, headers = headers, output = 'extended', timeout = timeout)
		if check: _cacheCheck()

		if extended: return result[0], result[2]
		else: return result[0]
	except:
		tools.Logger.error()

	return None


def _error(url, post, timestamp, message):
	_cache(url = url, post = post, timestamp = timestamp)
	if tools.Settings.getBoolean('accounts.informants.trakt.notifications'):
		interface.Dialog.notification(title = 32315, message = message, icon = interface.Dialog.IconError)
	interface.Loader.hide()
	return None

def _cache(url, post = None, timestamp = None):
	return cache.Cache().traktCache(link = url, data = post, timestamp = timestamp)

def _cacheCheck():
	thread = threading.Thread(target = _cacheProcess)
	thread.start()

def _cacheProcess():
	while True:
		item = cache.Cache().traktRetrieve()
		if not item: break
		getTrakt(url = item['link'], post = json.loads(item['data']) if item['data'] else None, cache = True, check = False, timestamp = item['time'])

def authTrakt(openSettings = True):
	# NB: Seems like there is a Kodi bug that you can't write the same setting twice in one execution.
	# After writing the second time, the settings still contains the first value.
	# Only write once.
	user = ''
	token = ''
	refresh = ''

	try:
		if getTraktCredentialsInfo() == True:
			if interface.Dialog.option(title = 32315, message = control.lang(32511).encode('utf-8') + ' ' + control.lang(32512).encode('utf-8')):
				pass
			else:
				return False

		result = getTrakt('/oauth/device/code', {'client_id': getTrakt1()}, direct = True)
		result = json.loads(result)
		expires_in = int(result['expires_in'])
		device_code = result['device_code']
		interval = result['interval']

		# Link and token on top for skins that don't scroll text in a progress dialog.
		message = ''
		message += interface.Format.fontBold(interface.Translation.string(33381) + ': ' + result['verification_url'])
		message += interface.Format.newline()
		message += interface.Format.fontBold(interface.Translation.string(33495) + ': ' + result['user_code'])
		message += interface.Format.newline() + interface.Translation.string(33494) + ' ' + interface.Translation.string(33978)

		clipboard.Clipboard.copy(result['user_code'])
		progressDialog = interface.Dialog.progress(title = 32315, message = message, background = False)

		for i in range(0, expires_in):
			try:
				if progressDialog.iscanceled(): break
				time.sleep(1)
				if not float(i) % interval == 0: raise Exception()
				r = getTrakt('/oauth/device/token', {'client_id': getTrakt1(), 'client_secret': getTrakt2(), 'code': device_code}, direct = True)
				r = json.loads(r)
				if 'access_token' in r: break
			except:
				pass

		try: progressDialog.close()
		except: pass

		token, refresh = r['access_token'], r['refresh_token']

		headers = {'Content-Type': 'application/json', 'trakt-api-key': getTrakt1(), 'trakt-api-version': '2', 'Authorization': 'Bearer %s' % token}

		result = client.request('http://api-v2launch.trakt.tv/users/me', headers=headers)
		result = json.loads(result)

		user = result['username']
	except:
		tools.Logger.error()

	tools.Settings.set('accounts.informants.trakt.user', user)
	tools.Settings.set('accounts.informants.trakt.token', token)
	tools.Settings.set('accounts.informants.trakt.refresh', refresh)

	if openSettings:
		tools.Settings.launch(category = tools.Settings.CategoryAccounts)

	return {'user' : user, 'token' : token, 'refresh' : refresh}


def getTraktCredentialsInfo():
	enabled = tools.Settings.getString('accounts.informants.trakt.enabled') == 'true'
	user = tools.Settings.getString('accounts.informants.trakt.user').strip()
	token = tools.Settings.getString('accounts.informants.trakt.token')
	refresh = tools.Settings.getString('accounts.informants.trakt.refresh')
	if (not enabled or user == '' or token == '' or refresh == ''): return False
	return True


def getTraktIndicatorsInfo():
	indicators = tools.Settings.getString('playback.track.status') if getTraktCredentialsInfo() == False else tools.Settings.getString('playback.track.status.alternative')
	indicators = True if indicators == '1' else False
	return indicators


def getTraktAddonMovieInfo():
	try: scrobble = control.addon('script.trakt').getSetting('scrobble_movie')
	except: scrobble = ''
	try: ExcludeHTTP = control.addon('script.trakt').getSetting('ExcludeHTTP')
	except: ExcludeHTTP = ''
	try: authorization = control.addon('script.trakt').getSetting('authorization')
	except: authorization = ''
	if scrobble == 'true' and ExcludeHTTP == 'false' and not authorization == '': return True
	else: return False


def getTraktAddonEpisodeInfo():
	try: scrobble = control.addon('script.trakt').getSetting('scrobble_episode')
	except: scrobble = ''
	try: ExcludeHTTP = control.addon('script.trakt').getSetting('ExcludeHTTP')
	except: ExcludeHTTP = ''
	try: authorization = control.addon('script.trakt').getSetting('authorization')
	except: authorization = ''
	if scrobble == 'true' and ExcludeHTTP == 'false' and not authorization == '': return True
	else: return False

def watch(type = None, imdb = None, tmdb = None, tvdb = None, season = None, episode = None, refresh = True, notification = False):
	if type is None: type = tools.Media.TypeMovie if season is None else tools.Media.TypeEpisode
	if tools.Media.typeTelevision(type):
		if not episode == None:
			markEpisodeAsWatched(imdb = imdb, tvdb = tvdb, season = season, episode = episode)
			syncShowCache(imdb = imdb, cached = False)
		elif not season == None:
			markSeasonAsWatched(imdb = imdb, tvdb = tvdb, season = season)
			syncShowCache(imdb = imdb, cached = False)
		elif not tvdb == None:
			markTVShowAsWatched(imdb = imdb, tvdb = tvdb)
			syncShowCache(imdb = imdb, cached = False)
	else:
		markMovieAsWatched(imdb = imdb, tmdb = tmdb)
		syncMoviesCache(cached = False)

	if refresh: interface.Directory.refresh(position = True)
	if notification: interface.Dialog.notification(title = 32315, message = 35502, icon = interface.Dialog.IconSuccess)

	try:
		from resources.lib.extensions import video
		video.Trailer().watch(imdb = imdb)
	except:
		tools.Logger.error()

def unwatch(type = None, imdb = None, tmdb = None, tvdb = None, season = None, episode = None, refresh = True, notification = False):
	if type is None: type = tools.Media.TypeMovie if season is None else tools.Media.TypeEpisode
	if tools.Media.typeTelevision(type):
		if not episode == None:
			markEpisodeAsNotWatched(imdb = imdb, tvdb = tvdb, season = season, episode = episode)
			syncShowCache(imdb = imdb, cached = False)
		elif not season == None:
			markSeasonAsNotWatched(imdb = imdb, tvdb = tvdb, season = season)
			syncShowCache(imdb = imdb, cached = False)
		elif not tvdb == None:
			markTVShowAsNotWatched(imdb = imdb, tvdb = tvdb)
			syncShowCache(imdb = imdb, cached = False)
	else:
		markMovieAsNotWatched(imdb = imdb, tmdb = tmdb)
		syncMoviesCache(cached = False)

	if refresh: interface.Directory.refresh(position = True)
	if notification: interface.Dialog.notification(title = 32315, message = 35503, icon = interface.Dialog.IconSuccess)

	try:
		from resources.lib.extensions import video
		video.Trailer().unwatch(imdb = imdb)
	except:
		tools.Logger.error()

def manager(imdb = None, tvdb = None, season = None, episode = None, refresh = True):
	try:
		interface.Loader.show()
		if not season == None: season = int(season)
		if not episode == None: episode = int(episode)

		lists = []
		try:
			result = getTrakt('/users/me/lists')
			result = tools.Converter.jsonFrom(result)
			result = [(i['name'], i['ids']['slug']) for i in result]
			for i in result:
				lists.append({
					'title' : i[0],
					'items' : [
						{'title' : interface.Translation.string(32521) % i[0], 'value' : interface.Translation.string(33580) % i[0], 'return' : '/users/me/lists/%s/items' % i[1]},
						{'title' : interface.Translation.string(32522) % i[0], 'value' : interface.Translation.string(33581) % i[0], 'return' : '/users/me/lists/%s/items/remove' % i[1]},
					],
				})
		except:
			tools.Logger.error()

		items = [
			{'title' : interface.Dialog.prefixBack(33486), 'close' : True},
			{
				'title' : 35500,
				'items' : [
					{'title' : 33651, 'value' : 33655, 'return' : 'watch'},
					{'title' : 33652, 'value' : 33656, 'return' : 'unwatch'},
				],
			},
			{
				'title' : 35501,
				'items' : [
					{'title' : 33653, 'value' : 33657, 'return' : 'rate'},
					{'title' : 33654, 'value' : 33658, 'return' : 'unrate'},
				],
			},
			{
				'title' : 32032,
				'items' : [
					{'title' : 32516, 'value' : 33575, 'return' : '/sync/collection'},
					{'title' : 32517, 'value' : 33576, 'return' : '/sync/collection/remove'},
				],
			},
			{
				'title' : 32033,
				'items' : [
					{'title' : 32518, 'value' : 33577, 'return' : '/sync/watchlist'},
					{'title' : 32519, 'value' : 33578, 'return' : '/sync/watchlist/remove'},
				],
			},
		]
		items += lists
		items += [{
			'title' : 33002,
			'items' : [
				{'title' : 32520, 'value' : 33579, 'return' : '/users/me/lists/%s/items'},
			],
		}]

		interface.Loader.hide()
		select = interface.Dialog.information(title = 32070, items = items)

		if select:
			if select in ['watch', 'unwatch']:
				interface.Loader.show()
				globals()[select](imdb = imdb, tvdb = tvdb, season = season, episode = episode, refresh = refresh, notification = True)
				interface.Loader.hide()
			elif select in ['rate', 'unrate']:
				interface.Loader.show()
				globals()[select](imdb = imdb, tvdb = tvdb, season = season, episode = episode)
				interface.Loader.hide()
			else:
				interface.Loader.show()
				if tvdb == None:
					post = {"movies": [{"ids": {"imdb": imdb}}]}
				else:
					if not episode == None:
						post = {"shows": [{"ids": {"imdb": imdb, "tvdb": tvdb}, "seasons": [{"number": season, "episodes": [{"number": episode}]}]}]}
					elif not season == None:
						post = {"shows": [{"ids": {"imdb": imdb, "tvdb": tvdb}, "seasons": [{"number": season}]}]}
					else:
						post = {"shows": [{"ids": {"imdb": imdb, "tvdb": tvdb}}]}

				if select == '/users/me/lists/%s/items':
					slug = listAdd(successNotification = False)
					if not slug == None: getTrakt(select % slug, post = post)
				else:
					getTrakt(select, post = post)

				interface.Loader.hide()
				interface.Dialog.notification(title = 32315, message = 33583 if '/remove' in select else 33582, icon = interface.Dialog.IconSuccess)
	except:
		tools.Logger.error()
		interface.Loader.hide()


def listAdd(successNotification = True):
	t = control.lang(32520).encode('utf-8')
	k = control.keyboard('', t) ; k.doModal()
	new = k.getText() if k.isConfirmed() else None
	if (new == None or new == ''): return
	result = getTrakt('/users/me/lists', post = {"name" : new, "privacy" : "private"})

	try:
		slug = json.loads(result)['ids']['slug']
		if successNotification:
			interface.Dialog.notification(title = 32070, message = 33661, icon = interface.Dialog.IconSuccess)
		return slug
	except:
		interface.Dialog.notification(title = 32070, message = 33584, icon = interface.Dialog.IconError)
		return None


def lists(id = None):
	return cache.Cache().cacheMedium(getTraktAsJson, 'https://api.trakt.tv/users/me/lists' + ('' if id == None else ('/' + str(id))))


def list(id):
	return lists(id = id)


def slug(name):
	name = name.strip()
	name = name.lower()
	name = re.sub('[^a-z0-9_]', '-', name)
	name = re.sub('--+', '-', name)
	return name


def verify(authentication = None):
	try:
		if getTraktAsJson('/sync/last_activities', authentication = authentication):
			return True
	except: pass
	return False


def getActivity():
	try:
		i = getTraktAsJson('/sync/last_activities')

		activity = []
		activity.append(i['movies']['collected_at'])
		activity.append(i['episodes']['collected_at'])
		activity.append(i['movies']['watchlisted_at'])
		activity.append(i['shows']['watchlisted_at'])
		activity.append(i['seasons']['watchlisted_at'])
		activity.append(i['episodes']['watchlisted_at'])
		activity.append(i['lists']['updated_at'])
		activity.append(i['lists']['liked_at'])
		activity = [int(cleandate.iso_2_utc(i)) for i in activity]
		activity = sorted(activity, key=int)[-1]

		return activity
	except:
		pass


def getWatchedActivity():
	try:
		i = getTraktAsJson('/sync/last_activities')

		activity = []
		activity.append(i['movies']['watched_at'])
		activity.append(i['episodes']['watched_at'])
		activity = [int(cleandate.iso_2_utc(i)) for i in activity]
		activity = sorted(activity, key=int)[-1]

		return activity
	except:
		pass


def syncMoviesCache(cached = True):
	if cached: return cache.Cache().cacheRefresh(syncMovies)
	else: return cache.Cache().cacheClear(syncMovies)


def syncMovies():
	try:
		if getTraktCredentialsInfo() == False: return
		indicators = getTraktAsJson('/users/me/watched/movies')
		indicators = [i['movie']['ids'] for i in indicators]
		indicators = [str(i['imdb']) for i in indicators if 'imdb' in i]
		return indicators
	except:
		pass


# Gaia
def watchedMovies():
	try:
		if getTraktCredentialsInfo() == False: return
		return getTraktAsJson('/users/me/watched/movies?extended=full')
	except:
		pass


# Gaia
def watchedMoviesTime(imdb):
	try:
		imdb = str(imdb)
		items = watchedMovies()
		for item in items:
			if str(item['movie']['ids']['imdb']) == imdb:
				return item['last_watched_at']
	except:
		pass


def syncShowCache(imdb, cached = True):
	threads = [threading.Thread(target = syncShowsCache, args = (cached,)), threading.Thread(target = syncSeasonsCache, args = (imdb, cached))]
	[i.start() for i in threads]
	[i.join() for i in threads]


def syncShowsCache(cached = True):
	if cached: return cache.Cache().cacheRefresh(syncShows)
	else: return cache.Cache().cacheClear(syncShows)


def syncSeasonsCache(imdb, cached = True):
	if cached: return cache.Cache().cacheRefresh(syncSeasons, imdb)
	else: return cache.Cache().cacheClear(syncSeasons, imdb)


def syncShows():
	try:
		if getTraktCredentialsInfo() == False: return
		indicators = getTraktAsJson('/users/me/watched/shows?extended=full')
		indicators = [(i['show']['ids']['tvdb'], i['show']['aired_episodes'], sum([[(s['number'], e['number']) for e in s['episodes']] for s in i['seasons']], [])) for i in indicators]
		indicators = [(str(i[0]), int(i[1]), i[2]) for i in indicators]
		return indicators
	except:
		pass


def syncSeasons(imdb):
	try:
		if getTraktCredentialsInfo() == False: return
		indicators = getTraktAsJson('/shows/%s/progress/watched?specials=true&hidden=false' % imdb)
		indicators = indicators['seasons']
		indicators = [(i['number'], [x['completed'] for x in i['episodes']]) for i in indicators]
		indicators = ['%01d' % int(i[0]) for i in indicators if not False in i[1]]
		return indicators
	except:
		pass


# Gaia
def watchedShows():
	try:
		if getTraktCredentialsInfo() == False: return
		return getTraktAsJson('/users/me/watched/shows?extended=full')
	except:
		pass


# Gaia
def watchedShowsTime(tvdb, season, episode):
	try:
		tvdb = str(tvdb)
		season = int(season)
		episode = int(episode)
		items = watchedShows()
		for item in items:
			if str(item['show']['ids']['tvdb']) == tvdb:
				seasons = item['seasons']
				for s in seasons:
					if s['number'] == season:
						episodes = s['episodes']
						for e in episodes:
							if e['number'] == episode:
								return e['last_watched_at']
	except:
		pass


# Gaia
def showCount(imdb, refresh = True, wait = False):
	try:
		if not imdb: return None
		result = {'total' : 0, 'watched' : 0, 'unwatched' : 0}
		indicators = seasonCount(imdb = imdb, refresh = refresh, wait = wait)
		for key, value in indicators.iteritems():
			result['total'] += value['total']
			result['watched'] += value['watched']
			result['unwatched'] += value['unwatched']
		return result
	except:
		return None

def seasonCount(imdb = None, items = None, refresh = True, wait = False):
	try:
		single = items == None
		if single: items = [imdb]
		items = [('tt' + i.replace('tt', '')) for i in items if i]
		if len(items) == 0: return None

		indicators = [cache.Cache().cacheRetrieve(_seasonCountRetrieve, i) for i in items]
		if refresh:
			# NB: Do not retrieve a fresh count, otherwise loading show/season menus are slow.
			threads = [threading.Thread(target = _seasonCountCache, args = (i,)) for i in items]
			[i.start() for i in threads]
			if wait:
				[i.join() for i in threads]
				indicators = [cache.Cache().cacheRetrieve(_seasonCountRetrieve, i) for i in items]

		return indicators[0] if single else indicators
	except:
		return None

def _seasonCountCache(imdb):
	return cache.Cache().cacheRefresh(_seasonCountRetrieve, imdb)

def _seasonCountRetrieve(imdb):
	try:
		if getTraktCredentialsInfo() == False: return
		special = tools.Settings.getBoolean('interface.tvshows.special.seasons') or tools.Settings.getBoolean('interface.tvshows.special.episodes')
		indicators = getTraktAsJson('/shows/%s/progress/watched?specials=%s&hidden=false' % (imdb, 'true' if special else 'false'))
		seasons = indicators['seasons']
		return {season['number'] : {'total' : season['aired'], 'watched' : season['completed'], 'unwatched' : season['aired'] - season['completed']} for season in seasons}
	except:
		return None


def request(imdb = None, tmdb = None, tvdb = None, season = None, episode = None, rating = None, items = None):
	result = []
	if items == None: items = [{'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'season' : season, 'episode' : episode, 'rating' : rating}]
	for item in items:
		value = {'ids' : {}}
		if 'imdb' in item and item['imdb']: value['ids']['imdb'] = 'tt' + item['imdb'].replace('tt', '')
		if 'tmdb' in item and item['tmdb']: value['ids']['tmdb'] = int(item['tmdb'])
		if 'tvdb' in item and item['tvdb']: value['ids']['tvdb'] = int(item['tvdb'])
		if 'season' in item and item['season']:
			value['seasons'] = [{'number' : int(item['season'])}]
			if 'episode' in item and item['episode']:
				value['seasons'][0]['episodes'] = [{'number' : int(item['episode'])}]
				if 'rating' in item and not item['rating'] is None: value['seasons'][0]['episodes'][0]['rating'] = int(item['rating'])
			elif 'rating' in item and not item['rating'] is None:
				value['seasons'][0]['rating'] = int(item['rating'])
		elif 'rating' in item and not item['rating'] is None:
			value['rating'] = int(item['rating'])
		result.append(value)
	return result

def timeout(items):
	return max(30, len(items) * 2)

def markMovieAsWatched(imdb = None, tmdb = None, items = None):
	items = request(imdb = imdb, tmdb = tmdb, items = items)
	return getTrakt('/sync/history', {"movies": items}, timeout = timeout(items))

def markMovieAsNotWatched(imdb = None, tmdb = None, items = None):
	items = request(imdb = imdb, tmdb = tmdb, items = items)
	return getTrakt('/sync/history/remove', {"movies": items}, timeout = timeout(items))

def markTVShowAsWatched(imdb = None, tvdb = None, items = None):
	items = request(imdb = imdb, tvdb = tvdb, items = items)
	result = getTrakt('/sync/history', {"shows": items}, timeout = timeout(items))
	seasonCount(imdb = imdb, items = items)
	return result

def markTVShowAsNotWatched(imdb = None, tvdb = None, items = None):
	items = request(imdb = imdb, tvdb = tvdb, items = items)
	result = getTrakt('/sync/history/remove', {"shows": items}, timeout = timeout(items))
	seasonCount(imdb = imdb, items = items)
	return result

def markSeasonAsWatched(imdb = None, tvdb = None, season = None, items = None):
	items = request(imdb = imdb, tvdb = tvdb, season = season, items = items)
	result = getTrakt('/sync/history', {"shows": items}, timeout = timeout(items))
	seasonCount(imdb = imdb, items = items)
	return result

def markSeasonAsNotWatched(imdb = None, tvdb = None, season = None, items = None):
	items = request(imdb = imdb, tvdb = tvdb, season = season, items = items)
	result = getTrakt('/sync/history/remove', {"shows": items}, timeout = timeout(items))
	seasonCount(imdb = imdb, items = items)
	return result

def markEpisodeAsWatched(imdb = None, tvdb = None, season = None, episode = None, items = None):
	items = request(imdb = imdb, tvdb = tvdb, season = season, episode = episode, items = items)
	result = getTrakt('/sync/history', {"shows": items}, timeout = timeout(items))
	seasonCount(imdb = imdb, items = items)
	return result

def markEpisodeAsNotWatched(imdb = None, tvdb = None, season = None, episode = None, items = None):
	items = request(imdb = imdb, tvdb = tvdb, season = season, episode = episode, items = items)
	result = getTrakt('/sync/history/remove', {"shows": items}, timeout = timeout(items))
	seasonCount(imdb = imdb, items = items)
	return result

def rateMovie(imdb = None, tmdb = None, rating = None, items = None):
	items = request(imdb = imdb, tmdb = tmdb, rating = rating, items = items)
	return getTrakt('/sync/ratings', {"movies": items}, timeout = timeout(items))

def rateShow(imdb = None, tvdb = None, rating = None, items = None):
	items = request(imdb = imdb, tvdb = tvdb, rating = rating, items = items)
	return getTrakt('/sync/ratings', {"shows": items}, timeout = timeout(items))

def rateSeason(imdb = None, tvdb = None, season = None, rating = None, items = None):
	items = request(imdb = imdb, tvdb = tvdb, season = season, rating = rating, items = items)
	return getTrakt('/sync/ratings', {"shows": items}, timeout = timeout(items))

def rateEpisode(imdb = None, tvdb = None, season = None, episode = None, rating = None, items = None):
	items = request(imdb = imdb, tvdb = tvdb, season = season, episode = episode, rating = rating, items = items)
	return getTrakt('/sync/ratings', {"shows": items}, timeout = timeout(items))

def rate(imdb = None, tvdb = None, season = None, episode = None):
	return _rate(action = 'rate', imdb = imdb, tvdb = tvdb, season = season, episode = episode)

def unrate(imdb = None, tvdb = None, season = None, episode = None):
	return _rate(action = 'unrate', imdb = imdb, tvdb = tvdb, season = season, episode = episode)

def rateManual(imdb = None, tvdb = None, season = None, episode = None):
	if tools.Settings.getInteger('accounts.informants.trakt.rating') == 1:
		rate(imdb = imdb, tvdb = tvdb, season = season, episode = episode)

def _rate(action, imdb = None, tvdb = None, season = None, episode = None):
	try:
		addon = 'script.trakt'
		if tools.System.installed(addon):
			data = {}
			data['action'] = action
			if not tvdb == None:
				data['video_id'] = tvdb
				if not episode == None:
					data['media_type'] = 'episode'
					data['dbid'] = 1
					data['season'] = int(season)
					data['episode'] = int(episode)
				elif not season == None:
					data['media_type'] = 'season'
					data['dbid'] = 5
					data['season'] = int(season)
				else:
					data['media_type'] = 'show'
					data['dbid'] = 2
			else:
				data['video_id'] = imdb
				data['media_type'] = 'movie'
				data['dbid'] = 4

			script = os.path.join(tools.System.path(addon), 'resources', 'lib', 'sqlitequeue.py')
			sqlitequeue = imp.load_source('sqlitequeue', script)
			data = {'action' : 'manualRating', 'ratingData' : data}
			sqlitequeue.SqliteQueue().append(data)
		else:
			interface.Dialog.notification(title = 32315, message = 33659)
	except:
		tools.Logger.error()

def getMovieTranslation(id, lang, full=False):
	url = '/movies/%s/translations/%s' % (id, lang)
	try:
		item = cache.Cache().cacheLong(getTraktAsJson, url)[0]
		result = item if full else item.get('title')
		return None if result == 'none' else result
	except:
		pass


def getTVShowTranslation(id, lang, season=None, episode=None, full=False):
	if season and episode:
		url = '/shows/%s/seasons/%s/episodes/%s/translations/%s' % (id, season, episode, lang)
	else:
		url = '/shows/%s/translations/%s' % (id, lang)
	try:
		item = cache.Cache().cacheLong(getTraktAsJson, url)[0]
		result = item if full else item.get('title')
		return None if result == 'none' else result
	except:
		pass


def getMovieSummary(id, full = True):
	try:
		url = '/movies/%s' % id
		if full: url += '?extended=full'
		return cache.Cache().cacheLong(getTraktAsJson, url)
	except:
		return


def getTVShowSummary(id, full = True):
	try:
		url = '/shows/%s' % id
		if full: url += '?extended=full'
		return cache.Cache().cacheLong(getTraktAsJson, url)
	except:
		return


def sort_list(sort_key, sort_direction, list_data):
	reverse = False if sort_direction == 'asc' else True
	if sort_key == 'rank':
		return sorted(list_data, key=lambda x: x['rank'], reverse=reverse)
	elif sort_key == 'added':
		return sorted(list_data, key=lambda x: x['listed_at'], reverse=reverse)
	elif sort_key == 'title':
		return sorted(list_data, key=lambda x: utils.title_key(x[x['type']].get('title')), reverse=reverse)
	elif sort_key == 'released':
		return sorted(list_data, key=lambda x: x[x['type']].get('first_aired', ''), reverse=reverse)
	elif sort_key == 'runtime':
		return sorted(list_data, key=lambda x: x[x['type']].get('runtime', 0), reverse=reverse)
	elif sort_key == 'popularity':
		return sorted(list_data, key=lambda x: x[x['type']].get('votes', 0), reverse=reverse)
	elif sort_key == 'percentage':
		return sorted(list_data, key=lambda x: x[x['type']].get('rating', 0), reverse=reverse)
	elif sort_key == 'votes':
		return sorted(list_data, key=lambda x: x[x['type']].get('votes', 0), reverse=reverse)
	else:
		return list_data


def getTraktAsJson(url, post = None, authentication = None):
	try:
		res_headers = {}
		r = getTrakt(url = url, post = post, extended = True, authentication = authentication)
		if isinstance(r, tuple) and len(r) == 2:
			res_headers = r[1]
			r = r[0]
		r = utils.json_loads_as_str(r)
		res_headers = dict((k.lower(), v) for k, v in res_headers.iteritems())
		if 'x-sort-by' in res_headers and 'x-sort-how' in res_headers:
			r = sort_list(res_headers['x-sort-by'], res_headers['x-sort-how'], r)
		return r
	except:
		pass

def getMovieAliases(id):
	try: return cache.Cache().cacheLong(getTraktAsJson, '/movies/%s/aliases' % id)
	except: return []

def getTVShowAliases(id):
	try: return cache.Cache().cacheLong(getTraktAsJson, '/shows/%s/aliases' % id)
	except: return []

def getPeople(id, content_type, full=True):
	try:
		url = '/%s/%s/people' % (content_type, id)
		if full: url += '?extended=full'
		return cache.Cache().cacheLong(getTraktAsJson, url)
	except:
		return

def SearchAll(title, year, full=True):
	try:
		return SearchMovie(title, year, full) + SearchTVShow(title, year, full)
	except:
		return

def SearchMovie(title, year, full=True):
	try:
		url = '/search/movie?query=%s' % title

		if year: url += '&year=%s' % year
		if full: url += '&extended=full'
		return getTraktAsJson(url)
	except:
		return

def SearchTVShow(title, year, full=True):
	try:
		url = '/search/show?query=%s' % title

		if year: url += '&year=%s' % year
		if full: url += '&extended=full'
		return getTraktAsJson(url)
	except:
		return


def getGenre(content, type, type_id):
	try:
		r = '/search/%s/%s?type=%s&extended=full' % (type, type_id, content)
		r = cache.Cache().cacheLong(getTraktAsJson, r)
		r = r[0].get(content, {}).get('genres', [])
		return r
	except:
		return []

# GAIA

def _scrobbleType(type):
	if tools.Media.typeTelevision(type):
		return 'episode'
	else:
		return 'movie'

def scrobbleProgress(type, imdb = None, tvdb = None, season = None, episode = None):
	try:
		type = _scrobbleType(type)
		if not imdb == None: imdb = str(imdb)
		if not tvdb == None: tvdb = int(tvdb)
		if not episode == None: episode = int(episode)
		if not episode == None: episode = int(episode)
		link = '/sync/playback/type'
		items = getTraktAsJson(link)

		if type == 'episode':
			if imdb and items:
				for item in items:
					if 'show' in item and 'imdb' in item['show']['ids'] and item['show']['ids']['imdb'] == imdb:
						if item['episode']['season'] == season and item['episode']['number'] == episode:
							return item['progress']
			if tvdb:
				for item in items:
					if 'show' in item and 'tvdb' in item['show']['ids'] and item['show']['ids']['tvdb'] == tvdb:
						if item['episode']['season'] == season and item['episode']['number'] == episode:
		 					return item['progress']
		else:
			if imdb and items:
				for item in items:
					if 'movie' in item and 'imdb' in item['movie']['ids'] and item['movie']['ids']['imdb'] == imdb:
						return item['progress']
	except:
		tools.Logger.error()
	return 0

# action = start, pause, stop
# type = tools.Media.Type
# progress = float in [0, 100]
def scrobbleUpdate(action, type, imdb = None, tvdb = None, season = None, episode = None, progress = 0):
	try:
		if action:
			type = _scrobbleType(type)
			if not imdb == None: imdb = str(imdb)
			if not tvdb == None: tvdb = int(tvdb)
			if not season == None: season = int(season)
			if not episode == None: episode = int(episode)

			if imdb: link = '/search/imdb/' + str(imdb)
			elif tvdb: link = '/search/tvdb/' + str(tvdb)
			if type == 'episode': link += '?type=show'
			else: link += '?type=movie'
			items = cache.Cache().cacheLong(getTraktAsJson, link)

			if len(items) > 0:
				item = items[0]
				if type == 'episode':
					slug = item['show']['ids']['slug']
					link = '/shows/%s/seasons/%d/episodes/%d' % (slug, season, episode)
					item = cache.Cache().cacheLong(getTraktAsJson, link)
				else:
					item = item['movie']

				if item:
					link = '/scrobble/' + action
					data = {
						type : item,
						'progress' : progress,
						'app_version' : tools.System.version(),
					}
					result = getTrakt(url = link, post = data)
					return 'progress' in result
	except:
		pass
	return False

def imdbImportCheck(importWatched, importRatings):
	from resources.lib.indexers import movies

	def check(method, result, index):
		indexer = movies.movies(type = tools.Media.TypeMovie)
		getattr(indexer, method)()
		result[index] = indexer.imdb_public

	threads = []
	values = [None, None]
	if any(importWatched):
		values[0] = False
		threads.append(threading.Thread(target = check, args = ('imdb_watched', values, 0)))
	if any(importRatings):
		values[1] = False
		threads.append(threading.Thread(target = check, args = ('imdb_ratings', values, 1)))

	[i.start() for i in threads]
	[i.join() for i in threads]
	return values[0], values[1]

def imdbImportRetrieve(importWatched, importRatings, ratings):
	from resources.lib.indexers import movies
	from resources.lib.indexers import tvshows

	def retrieve(type, method, result, index):
		if tools.Media.typeTelevision(type): result[index] = getattr(tvshows.tvshows(), method)()
		else: result[index] = getattr(movies.movies(type = type), method)()

	threads = []
	valuesWatched = [None, None, None, None]
	valuesRatings = [None, None, None, None]

	if importWatched[0]: threads.append(threading.Thread(target = retrieve, args = (tools.Media.TypeMovie, 'imdb_watched', valuesWatched, 0)))
	if importWatched[1]: threads.append(threading.Thread(target = retrieve, args = (tools.Media.TypeDocumentary, 'imdb_watched', valuesWatched, 1)))
	if importWatched[2]: threads.append(threading.Thread(target = retrieve, args = (tools.Media.TypeShort, 'imdb_watched', valuesWatched, 2)))
	if importWatched[3]: threads.append(threading.Thread(target = retrieve, args = (tools.Media.TypeShow, 'imdb_watched', valuesWatched, 3)))

	if importRatings[0]: threads.append(threading.Thread(target = retrieve, args = (tools.Media.TypeMovie, 'imdb_ratings', valuesRatings, 0)))
	if importRatings[1]: threads.append(threading.Thread(target = retrieve, args = (tools.Media.TypeDocumentary, 'imdb_ratings', valuesRatings, 1)))
	if importRatings[2]: threads.append(threading.Thread(target = retrieve, args = (tools.Media.TypeShort, 'imdb_ratings', valuesRatings, 2)))
	if importRatings[3]: threads.append(threading.Thread(target = retrieve, args = (tools.Media.TypeShow, 'imdb_ratings', valuesRatings, 3)))

	[i.start() for i in threads]
	[i.join() for i in threads]

	if ratings:
		if importWatched[0] and importRatings[0]: valuesWatched[0] = movies.movies(type = tools.Media.TypeMovie).imdb_account(ratings = valuesRatings[0], watched = valuesWatched[0])
		if importWatched[1] and importRatings[1]: valuesWatched[1] = movies.movies(type = tools.Media.TypeDocumentary).imdb_account(ratings = valuesRatings[1], watched = valuesWatched[1])
		if importWatched[2] and importRatings[2]: valuesWatched[2] = movies.movies(type = tools.Media.TypeShort).imdb_account(ratings = valuesRatings[2], watched = valuesWatched[2])
		if importWatched[3] and importRatings[3]: valuesWatched[3] = tvshows.tvshows().imdb_account(ratings = valuesRatings[3], watched = valuesWatched[3])

	return valuesWatched, valuesRatings

def imdbImportSync(itemsWatched, itemsRatings):
	def syncWatched(type, items):
		if tools.Media.typeTelevision(type): markTVShowAsWatched(items = items)
		else: markMovieAsWatched(items = items)

	def syncRatings(type, items):
		if tools.Media.typeTelevision(type): rateShow(items = items)
		else: rateMovie(items = items)

	threads = []

	if itemsWatched[0]: threads.append(threading.Thread(target = syncWatched, args = (tools.Media.TypeMovie, itemsWatched[0])))
	if itemsWatched[1]: threads.append(threading.Thread(target = syncWatched, args = (tools.Media.TypeDocumentary, itemsWatched[1])))
	if itemsWatched[2]: threads.append(threading.Thread(target = syncWatched, args = (tools.Media.TypeShort, itemsWatched[2])))
	if itemsWatched[3]: threads.append(threading.Thread(target = syncWatched, args = (tools.Media.TypeShow, itemsWatched[3])))

	if itemsRatings[0]: threads.append(threading.Thread(target = syncRatings, args = (tools.Media.TypeMovie, itemsRatings[0])))
	if itemsRatings[1]: threads.append(threading.Thread(target = syncRatings, args = (tools.Media.TypeDocumentary, itemsRatings[1])))
	if itemsRatings[2]: threads.append(threading.Thread(target = syncRatings, args = (tools.Media.TypeShort, itemsRatings[2])))
	if itemsRatings[3]: threads.append(threading.Thread(target = syncRatings, args = (tools.Media.TypeShow, itemsRatings[3])))

	[i.start() for i in threads]
	[i.join() for i in threads]

def imdbImport():
	from resources.lib.indexers import movies
	from resources.lib.indexers import tvshows

	if interface.Dialog.option(title = 32034, message = 35610):
		yes = interface.Format.fontBold(interface.Format.fontColor(interface.Translation.string(33341), interface.Format.colorExcellent()))
		no = interface.Format.fontBold(interface.Format.fontColor(interface.Translation.string(33342), interface.Format.colorBad()))

		importWatched = [True, True, True, True]
		importRatings = [True, True, True, True]

		initial = True
		while initial:
			choice = 1
			while choice > 0:
				items = [
					interface.Format.fontBold(interface.Translation.string(33821)),

					interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(35212), interface.Translation.string(32001), interface.Translation.string(32033))) + (yes if importWatched[0] else no),
					interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(35212), interface.Translation.string(33470), interface.Translation.string(32033))) + (yes if importWatched[1] else no),
					interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(35212), interface.Translation.string(33471), interface.Translation.string(32033))) + (yes if importWatched[2] else no),
					interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(35212), interface.Translation.string(32002), interface.Translation.string(32033))) + (yes if importWatched[3] else no),

					interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(35212), interface.Translation.string(32001), interface.Translation.string(35602))) + (yes if importRatings[0] else no),
					interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(35212), interface.Translation.string(33470), interface.Translation.string(35602))) + (yes if importRatings[1] else no),
					interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(35212), interface.Translation.string(33471), interface.Translation.string(35602))) + (yes if importRatings[2] else no),
					interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(35212), interface.Translation.string(32002), interface.Translation.string(35602))) + (yes if importRatings[3] else no),
				]
				choice = interface.Dialog.options(title = 32034, items = items)
				if choice < 0: return False
				elif choice == 0: break
				elif choice < 5: importWatched[choice - 1] = not importWatched[choice - 1]
				else: importRatings[choice - 5] = not importRatings[choice - 5]

			while True:
				publicWatched, publicRatings = imdbImportCheck(importWatched, importRatings)
				if publicWatched is False:
					if interface.Dialog.option(title = 32034, message = 35608, labelConfirm = 35606, labelDeny = 35374): continue
				elif publicRatings is False:
					if interface.Dialog.option(title = 32034, message = 35609, labelConfirm = 35606, labelDeny = 35374): continue
				else:
					initial = False
				break

		ratings = interface.Dialog.option(title = 32034, message = 35611) if any(importRatings) else False
		itemsWatched, itemsRatings = imdbImportRetrieve(importWatched, importRatings, ratings)

		items = [interface.Format.fontBold(interface.Translation.string(33821))]
		if not itemsWatched[0] is None: items.append(interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(32001), interface.Translation.string(32033), interface.Translation.string(35607))) + str(len(itemsWatched[0])))
		if not itemsWatched[1] is None: items.append(interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(33470), interface.Translation.string(32033), interface.Translation.string(35607))) + str(len(itemsWatched[1])))
		if not itemsWatched[2] is None: items.append(interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(33471), interface.Translation.string(32033), interface.Translation.string(35607))) + str(len(itemsWatched[2])))
		if not itemsWatched[3] is None: items.append(interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(32002), interface.Translation.string(32033), interface.Translation.string(35607))) + str(len(itemsWatched[3])))
		if not itemsRatings[0] is None: items.append(interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(32001), interface.Translation.string(35602), interface.Translation.string(35607))) + str(len(itemsRatings[0])))
		if not itemsRatings[1] is None: items.append(interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(33470), interface.Translation.string(35602), interface.Translation.string(35607))) + str(len(itemsRatings[1])))
		if not itemsRatings[2] is None: items.append(interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(33471), interface.Translation.string(35602), interface.Translation.string(35607))) + str(len(itemsRatings[2])))
		if not itemsRatings[3] is None: items.append(interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(32002), interface.Translation.string(35602), interface.Translation.string(35607))) + str(len(itemsRatings[3])))
		choice = interface.Dialog.options(title = 32034, items = items)
		if choice < 0: return False

		if interface.Dialog.option(title = 32034, message = 35612):
			interface.Loader.show()
			imdbImportSync(itemsWatched, itemsRatings)
			interface.Loader.hide()
			interface.Dialog.confirm(title = 32034, message = 35613)
			return True

	interface.Loader.hide()
	return False
