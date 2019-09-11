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

import re
import urllib
import urlparse
import threading
import random
import copy

from resources.lib.modules import client
from resources.lib.extensions import tools
from resources.lib.extensions import interface
from resources.lib.extensions import network
from resources.lib.extensions import database

class Video(object):

	# Must correspond with the settings.
	ModeDisabled = 0
	ModeDirect = 1
	ModeAutomatic = 2
	ModeManual = 3

	Keys = ['QUl6YVN5RDd2aFpDLTYta2habTVuYlVyLTZ0Q0JRQnZWcnFkeHNz', 'QUl6YVN5Q2RiNEFNenZpVG0yaHJhSFY3MXo2Nl9HNXBhM2ZvVXd3']
	Key = tools.Converter.base64From((random.choice(Keys)), url = True)

	LinkBase = 'http://www.youtube.com'
	LinkSearch = 'https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&maxResults=20&order=relevance&key=%s&q=%s'
	LinkDetails = 'https://www.googleapis.com/youtube/v3/videos?part=contentDetails&key=%s&id=%s'
	LinkWatch = 'http://www.youtube.com/watch?v=%s'

	def __init__(self, type = tools.Media.TypeMovie, kids = tools.Selection.TypeUndefined):
		self.mType = type
		self.mKids = kids
		self.mPlayer = interface.Player()

	@classmethod
	def setting(self):
		return tools.Settings.getInteger('general.videos.' + self.Id)

	@classmethod
	def enabled(self):
		return self.setting() > 0

	def _prefer(self, season = None):
		return None

	def _include(self, season = None):
		return None

	def _exclude(self, season = None):
		return None

	def _filter(self, items, filters = None):
		for i in range(len(items)):
			filtered = True
			if filters:
				for filter in filters:
					if not items[i][filter]:
						filtered = False
						break
			if filtered:
				if items[i]['link'] == False:
					link = self._extract(items[i]['id'])
					if link: return link
					else: items[i]['link'] = True
		return None

	def _search(self, query, title = None, selection = None, prefer = None, include = None, exclude = None):
		try:
			from resources.lib.extensions import cache

			if selection is None:
				selection = self.setting()
				if selection == Video.ModeDisabled: selection = Video.ModeAutomatic # In case it was disabled in the settings, but launched from the Kodi info window or some external addon.

			# Search videos.
			items = []
			if not isinstance(query, (list, tuple)): query = [query]
			for q in query:
				link = Video.LinkSearch % (Video.Key, urllib.quote_plus(q))
				result = cache.Cache().cacheMedium(network.Networker().retrieve, link)
				items.extend(tools.Converter.jsonFrom(result)['items'])

			# Extra details.
			link = Video.LinkDetails % (Video.Key, ','.join([i['id']['videoId'] for i in items]))
			result = cache.Cache().cacheMedium(network.Networker().retrieve, link)
			result = tools.Converter.jsonFrom(result)['items']
			for i in result:
				for j in range(len(items)):
					if i['id'] == items[j]['id']['videoId']:
						items[j]['contentDetails'] = i['contentDetails']
						duration = re.search('^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$', items[j]['contentDetails']['duration'])
						try: duration = (int(duration.group(1) if duration.group(1) else 0) * 3600) + (int(duration.group(2) if duration.group(2) else 0) * 60) + (int(duration.group(3) if duration.group(3) else 0))
						except: duration = 0
						items[j]['contentDetails']['duration'] = duration
						break

			# Details not found.
			for i in range(len(items)):
				if not 'contentDetails' in items[i]:
					items[i]['contentDetails'] = {'definition' : 'sd', 'duration' : 0}

			# Filter duration.
			items = [i for i in items if i['contentDetails'] and i['contentDetails']['duration'] <= self.Duration]

			if include:
				for i in range(len(include)):
					if isinstance(include[i], (list, tuple)):
						include[i] = [j.lower() for j in include[i]]
					else:
						include[i] = include[i].lower()
			if exclude:
				for i in range(len(exclude)):
					if isinstance(exclude[i], (list, tuple)):
						exclude[i] = [j.lower() for j in exclude[i]]
					else:
						exclude[i] = exclude[i].lower()

			try: title = title.encode('utf-8')
			except: pass
			title = re.split('[-!$%^&*()_+|~=`{}\[\]:";\'<>?,.\/\s]', title.lower())
			countTitle = len(title)

			from resources.lib.externals.beautifulsoup import BeautifulSoup
			for i in range(len(items)):
				id = items[i]['id']['videoId']
				name = items[i]['snippet']['title']
				try: name = unicode(BeautifulSoup(name).contents[0]) # Unescape HTML entities.
				except: pass
				try: name = name.encode('utf-8')
				except: pass
				split = [j for j in re.split('[-!$%^&*()_+|~=`{}\[\]:";\'<>?,.\/\s]', name.lower()) if j]

				hasPrefer = True
				if prefer:
					for j in prefer:
						found = False
						if not isinstance(j, (list, tuple)): j = [j]
						for k in j:
							if '+' in k:
								sub = re.split('[+]', k)
								try: first = split.index(sub[0])
								except: first = -1
								try: second = split.index(sub[1])
								except: second = -1
								if first >= 0 and second >= 0 and first == (second - 1):
									found = True
									break
							elif k in split:
								found = True
								break
						if not found:
							hasPrefer = False
							break

				hasInclude = True
				if include:
					for j in include:
						found = False
						if not isinstance(j, (list, tuple)): j = [j]
						for k in j:
							if '+' in k:
								sub = re.split('[+]', k)
								try: first = split.index(sub[0])
								except: first = -1
								try: second = split.index(sub[1])
								except: second = -1
								if first >= 0 and second >= 0 and first == (second - 1):
									found = True
									break
							elif k in split:
								found = True
								break
						if not found:
							hasInclude = False
							break

				hasExclude = True
				if exclude and any(j in split for j in exclude): hasExclude = False

				hasOfficial = 'official' in split

				# Some videos are marked as HD by YouTube, but they are actually not. Check name instead.
				#hasHd = items[i]['contentDetails']['definition'].lower() == 'hd'
				hasHd = items[i]['contentDetails']['definition'].lower() == 'hd' and 'hd' in split

				countOverlap = len(set(title) & set(split))
				if countTitle > 2: hasTitle = (countOverlap / float(countTitle)) >= 0.6
				else: hasTitle = countOverlap == countTitle

				if any(j['id'] == id for j in items if j and 'id' in j): # Cheeck if the id is already present
					items[i] = None
				else:
					items[i] = {'id' : id, 'link' : False, 'name' : name, 'split' : split, 'official' : hasOfficial, 'hd' : hasHd, 'title' : hasTitle, 'prefer' : hasPrefer, 'include' : hasInclude, 'exclude' : hasExclude}

			items = [i for i in items if i]

			if selection == Video.ModeDirect or selection == Video.ModeAutomatic:
				link = self._filter(items, ['title', 'include', 'exclude', 'prefer', 'official', 'hd'])
				if link: return link
				link = self._filter(items, ['title', 'include', 'exclude', 'prefer', 'official'])
				if link: return link
				link = self._filter(items, ['title', 'include', 'exclude', 'prefer', 'hd'])
				if link: return link
				link = self._filter(items, ['title', 'include', 'exclude', 'prefer'])
				if link: return link
				link = self._filter(items, ['title', 'include', 'exclude', 'official', 'hd'])
				if link: return link
				link = self._filter(items, ['title', 'include', 'exclude', 'official'])
				if link: return link
				link = self._filter(items, ['title', 'include', 'exclude', 'hd'])
				if link: return link
				link = self._filter(items, ['title', 'include', 'exclude'])
				if link: return link

			if selection == Video.ModeDirect:
				link = self._filter(items, ['title', 'prefer', 'exclude'])
				if link: return link
				link = self._filter(items, ['title', 'prefer', 'include'])
				if link: return link
				link = self._filter(items, ['title', 'prefer'])
				if link: return link
				link = self._filter(items, ['include', 'exclude', 'prefer'])
				if link: return link
				link = self._filter(items, ['title', 'exclude'])
				if link: return link
				link = self._filter(items, ['title', 'include'])
				if link: return link
				link = self._filter(items, ['title'])
				if link: return link
				link = self._filter(items, ['include', 'exclude'])
				if link: return link
				link = self._filter(items, ['prefer'])
				if link: return link
				link = self._filter(items)
				if link: return link

			# Show a manual selection list.
			if selection == Video.ModeAutomatic or selection == Video.ModeManual:
				if selection == Video.ModeAutomatic:
					interface.Dialog.notification(title = self.Label, message = interface.Translation.string(35645) % interface.Translation.string(self.Label), icon = interface.Dialog.IconError)
				while len(items) > 0:
					names = [i['name'] for i in items]
					choice = interface.Dialog.options(title = self.Label, items = names)
					if choice < 0: return None
					link = self._extract(items[choice]['id'])
					if link:
						return link
					else:
						interface.Dialog.notification(title = self.Label, message = 35361, icon = interface.Dialog.IconError)
						del items[choice]

			if len(items) == 0 and not selection == Video.ModeDirect:
				interface.Dialog.notification(title = self.Label, message = 35361, icon = interface.Dialog.IconError)
		except:
			tools.Logger.error()

	def _extract(self, link):
		try:
			id = link.split('?v=')[-1].split('/')[-1].split('?')[0].split('&')[0]
			link = Video.LinkWatch % id
			result = network.Networker(link).request()
			message = client.parseDOM(result, 'div', attrs = {'id': 'unavailable-submessage'})
			message = ''.join(message)
			alert = client.parseDOM(result, 'div', attrs = {'id': 'watch7-notification-area'})
			if len(alert) > 0: raise Exception()
			if re.search('[a-zA-Z]', message): raise Exception()
			link = 'plugin://plugin.video.youtube/play/?video_id=%s' % id
			return link
		except:
			tools.Logger.error()
			return None

	def _resolve(self, query, title = None, link = None, selection = None, prefer = None, include = None, exclude = None):
		try:
			if link.startswith(Video.LinkBase):
				link = self._extract(link)
				if link == None: raise Exception()
				return link
			elif not link.startswith('http://'):
				link = Video.LinkWatch % link
				link = self._extract(link)
				if link == None: raise Exception()
				return link
			else:
				raise Exception()
		except:
			# This returns too many fan-created videos. Eg: Game of Thrones Season 2 Recap.
			# If this is ever added back, remember that query can also be a list instead of a string.
			#if exclude: query += ' -' + (' -'.join(exclude))
			return self._search(query, title = title, selection = selection, prefer = prefer, include = include, exclude = exclude)

	def play(self, query = None, title = None, link = None, art = None, items = None, resolve = True, loader = True, selection = None, prefer = None, include = None, exclude = None):
		try:
			if loader: interface.Loader.show()

			single = items == None
			if single: items = [{'query' : query, 'title' : title, 'link' : link, 'art' : art}]

			if resolve:
				for i in range(len(items)):
					items[i]['link'] = self._resolve(query = items[i]['query'], title = items[i]['title'], link = items[i]['link'], selection = selection, prefer = prefer, include = include, exclude = exclude)

			items = [item for item in items if not item['link'] == None]
			if len(items) == 0:
				interface.Loader.hide()
				return None

			entries = []
			for item in items:
				try:
					art = tools.Converter.jsonFrom(item['art'])
					if art: item['art'] = art
				except: pass
				try: icon = item['art']['poster']
				except:
					try: icon = item['art']['icon']
					except: icon = None
				try: thumbnail = item['art']['poster']
				except:
					try: thumbnail = item['art']['thumb']
					except: thumbnail = None
				entry = interface.Item(path = item['link'], iconImage = icon, thumbnailImage = thumbnail)
				entry.setInfo(type = 'Video', infoLabels = {'title' : item['title']})
				try: entry.setArt(item['art'])
				except: pass
				entries.append(entry)

			# Gaia: Must hide loader here and then sleep, otherwise the YouTube addon crashes Kodi.
			# Sleeping for 0.2 is not enough.
			interface.Loader.hide()
			tools.Time.sleep(0.5)

			if single:
				self.mPlayer.play(items[0]['link'], entries[0])
			else:
				playlist = tools.Playlist.playlist()
				for i in range(len(items)):
					playlist.add(items[i]['link'], entries[i])
				self.mPlayer.play(playlist)
		except:
			tools.Logger.error()
			interface.Loader.hide()

class Trailer(Video, database.Database):

	Name = 'trailers'
	Id = 'trailer'
	Duration = 300 # 5 minutes.
	Label = 35536
	Description = 35656

	TrailerCount = 5
	TrailerDuration = 5

	def __init__(self, type = tools.Media.TypeMovie, kids = tools.Selection.TypeUndefined):
		Video.__init__(self, type = type, kids = kids)
		database.Database.__init__(self, Trailer.Name)
		self.mCinemaPlaylist = tools.Playlist.playlist()
		self.mCinemaStop = False
		self.mCinemaRunning = None
		self.mCinemaInterrupt = False
		self.mCinemaLock = threading.Lock()
		self.mCinemaItems = []

	def _initialize(self):
		self._create('CREATE TABLE IF NOT EXISTS %s (imdb TEXT, time INTEGER, UNIQUE(imdb));' % Trailer.Name)

	def watched(self, imdb):
		return self._exists('SELECT imdb FROM %s WHERE imdb = "%s";' % (Trailer.Name, imdb))

	def watch(self, imdb):
		self._insert('INSERT OR IGNORE INTO %s (imdb) VALUES ("%s");' % (Trailer.Name, imdb))
		self._update('UPDATE %s SET time = %d;' % (Trailer.Name, tools.Time.timestamp()))

	def unwatch(self, imdb):
		self._delete('DELETE FROM %s WHERE imdb = "%s";' % (Trailer.Name, imdb))

	def _query(self, title = None, year = None, season = None):
		query = []
		if tools.Media.typeTelevision(self.mType):
			if season is None:
				season = 1
				query.append('"%s" trailer' % (title))
			query.append('"%s" "season %s"|s%s trailer' % (title, str(season), str(season)))
		else:
			query.append('"%s" %s trailer' % (title, str(year)))
		return query

	def _prefer(self, season = None):
		result = []
		if tools.Media.typeTelevision(self.mType) and season is None: result.append(['season+1', 's+1', 's1', 'part+1'])
		return result

	def _include(self, season = None):
		result = [['trailer', 'trailers']]
		if tools.Media.typeTelevision(self.mType) and not season is None: result.append(['season+%d' % season, 's+%d' % season, 's%d' % season, 'part+%d' % season])
		return result

	def _exclude(self, season = None):
		return ['recap', 'recaps', 'summary', 'episode']

	def play(self, title = None, year = None, season = None, link = None, art = None, items = None, resolve = True, loader = True, selection = None):
		if not season is None: season = int(season)
		return Video.play(self, query = self._query(title = title, year = year, season = season), title = title, link = link, art = art, items = items, resolve = resolve, loader = loader, selection = selection, prefer = self._prefer(season = season), include = self._include(season = season), exclude = self._exclude(season = season))

	@classmethod
	def cinemaEnabled(self):
		return tools.Settings.getBoolean('interface.navigation.cinema')

	@classmethod
	def cinemaProgress(self):
		return tools.Settings.getBoolean('interface.navigation.cinema.progress')

	@classmethod
	def cinemaInterrupt(self):
		return tools.Settings.getBoolean('interface.navigation.cinema.interrupt')

	def _cinemaFilter(self, type, items):
		from resources.lib.modules import playcount
		trailer = Trailer()
		items = [item for item in items if not trailer.watched(item['imdb'])]
		try:
			if tools.Media.typeTelevision(type):
				indicators = playcount.getShowIndicators()
				items = [item for item in items if not int(playcount.getEpisodeWatched(indicators, item['imdb'], item['tvdb'], item['season'], item['episode'])) == 7]
			else:
				indicators = playcount.getMovieIndicators()
				items = [item for item in items if not int(playcount.getMovieWatched(indicators, item['imdb']))]
		except:
			tools.Logger.error()
		return items

	def _cinemaArt(self, items):
		result = []
		for i in items:
			poster = None
			if poster == '0' and 'poster3' in i: poster = i['poster3']
			if poster == '0' and 'poster2' in i: poster = i['poster2']
			if poster == '0' and 'poster' in i: poster = i['poster']

			icon = '0'
			if icon == '0' and 'icon3' in i: icon = i['icon3']
			if icon == '0' and 'icon2' in i: icon = i['icon2']
			if icon == '0' and 'icon' in i: icon = i['icon']

			thumb = '0'
			if thumb == '0' and 'thumb3' in i: thumb = i['thumb3']
			if thumb == '0' and 'thumb2' in i: thumb = i['thumb2']
			if thumb == '0' and 'thumb' in i: thumb = i['thumb']

			banner = '0'
			if banner == '0' and 'banner3' in i: banner = i['banner3']
			if banner == '0' and 'banner2' in i: banner = i['banner2']
			if banner == '0' and 'banner' in i: banner = i['banner']

			fanart = '0'
			if fanart == '0' and 'fanart3' in i: fanart = i['fanart3']
			if fanart == '0' and 'fanart2' in i: fanart = i['fanart2']
			if fanart == '0' and 'fanart' in i: fanart = i['fanart']

			clearlogo = '0'
			if clearlogo == '0' and 'clearlogo' in i: clearlogo = i['clearlogo']

			clearart = '0'
			if clearart == '0' and 'clearart' in i: clearart = i['clearart']

			fanart = '0'
			if fanart == '0' and 'fanart' in i: fanart = i['fanart']

			landscape = '0'
			if landscape == '0' and 'landscape' in i: landscape = i['landscape']

			art = {}
			if not poster == '0' and not poster == None: art.update({'poster' : poster})
			if not icon == '0' and not icon == None: art.update({'icon' : icon})
			if not thumb == '0' and not thumb == None: art.update({'thumb' : thumb})
			if not banner == '0' and not banner == None: art.update({'banner' : banner})
			if not clearlogo == '0' and not clearlogo == None: art.update({'clearlogo' : clearlogo})
			if not clearart == '0' and not clearart == None: art.update({'clearart' : clearart})
			if not fanart == '0' and not fanart == None: art.update({'fanart' : fanart})
			if not landscape == '0' and not landscape == None: art.update({'landscape' : landscape})
			i['art'] = art
			result.append(i)

		return result

	def _cinemaMovies(self, minimum = TrailerCount):
		from resources.lib.indexers import movies
		movie = movies.movies(type = self.mType, kids = self.mKids)
		items = movie.home(idx = False)
		all = copy.deepcopy(items)
		items = self._cinemaFilter(type, items)
		nexts = []
		while len(items) < minimum:
			next = None
			for item in reversed(items):
				if 'next' in item and not item['next'] == None and not item['next'] == '':
					next = item['next']
					break
			if next == None or next in nexts: break
			nexts.append(next)
			itemsNew = movie.get(next, idx = False)
			all.extend(itemsNew)
			itemsNew = self._cinemaFilter(type, itemsNew)
			items.extend(itemsNew)
		lists = ['views', 'featured', 'boxoffice', 'oscars', 'theaters_link']
		while len(items) < minimum and len(lists) > 0:
			itemsNew = movie.get(lists.pop(0), idx = False)
			all.extend(itemsNew)
			itemsNew = self._cinemaFilter(type, itemsNew)
			items.extend(itemsNew)
		if len(items) < minimum:
			items = all
			random.shuffle(items)
		items = self._cinemaArt(items)
		result = []
		for item in items:
			try:
				if item['imdb'].startswith('tt'): # Some do not have an IMdb ID.
					result.append({'imdb' : item['imdb'], 'query' : self._query(title = item['title'], year = item['year']), 'title' : item['title'], 'art' : item['art']})
			except: pass
		return result

	def _cinemaShows(self, minimum = TrailerCount):
		from resources.lib.indexers import tvshows
		from resources.lib.indexers import episodes
		show = tvshows.tvshows(type = self.mType, kids = self.mKids)
		episode = episodes.episodes(type = self.mType, kids = self.mKids)
		items = episode.home(idx = False)
		all = copy.deepcopy(items)
		items = self._cinemaFilter(type, items)
		nexts = []
		while len(items) < minimum:
			next = None
			for item in reversed(items):
				if 'next' in item and not item['next'] == None and not item['next'] == '':
					next = item['next']
					break
			if next == None or next in nexts: break
			nexts.append(next)
			itemsNew = episode.get(next, idx = False)
			all.extend(itemsNew)
			itemsNew = self._cinemaFilter(type, itemsNew)
			items.extend(itemsNew)
		lists = ['views', 'featured', 'popular', 'airing', 'premiere']
		while len(items) < minimum and len(lists) > 0:
			itemsNew = show.get(lists.pop(0), idx = False)
			all.extend(itemsNew)
			itemsNew = self._cinemaFilter(type, itemsNew)
			items.extend(itemsNew)
		if len(items) < minimum:
			items = all
			random.shuffle(items)
		items = self._cinemaArt(items)
		result = []
		for item in items:
			try:
				if item['imdb'].startswith('tt'): # Some do not have an IMdb ID.
					try: title = item['tvshowtitle']
					except: title = item['title']
					result.append({'imdb' : item['imdb'], 'query' : self._query(title = title), 'title' : title, 'art' : item['art']})
			except: pass
		return result

	def _cinemaSearch(self, item):
		try:
			link = self._resolve(query = item['query'], title = item['title'], selection = Video.ModeDirect, include = self._include(), exclude = self._exclude())
			if link:
				item['watched'] = False
				item['link'] = link
				self.mCinemaLock.acquire()

				try:
					art = tools.Converter.jsonFrom(item['art'])
					if art: item['art'] = art
				except: pass
				try: icon = item['art']['poster']
				except:
					try: icon = item['art']['icon']
					except: icon = None
				try: thumbnail = item['art']['poster']
				except:
					try: thumbnail = item['art']['thumb']
					except: thumbnail = None
				entry = interface.Item(path = item['link'], iconImage = icon, thumbnailImage = thumbnail)
				entry.setInfo(type = 'Video', infoLabels = {'title' : item['title']})
				try: entry.setArt(item['art'])
				except: pass
				self.mCinemaPlaylist.add(item['link'], entry)

				self.mCinemaItems.append(item)
				self.mCinemaLock.release()
		except:
			tools.Logger.error()

	def _cinemaStart(self, type = tools.Media.TypeMovie, background = None):
		try:
			from resources.lib.extensions import window

			loaderNone = tools.Settings.getInteger('interface.navigation.cinema.loader') == 0
			if loaderNone: interface.Loader.show()
			else: window.WindowCinema.show(background = background)

			self.mCinemaLock.acquire()
			self.mCinemaRunning = True
			self.mCinemaStop = False
			self.mCinemaInterrupt = False
			self.mCinemaItems = []
			self.mCinemaPlaylist.clear()
			self.mCinemaLock.release()
			if tools.Media.typeTelevision(type): items = self._cinemaShows()
			else: items = self._cinemaMovies()
			random.shuffle(items)
			try: items = items[:Trailer.TrailerCount]
			except: pass
			threads = [threading.Thread(target = self._cinemaSearch, args = (item,)) for item in items]
			[thread.start() for thread in threads]
			if loaderNone: interface.Loader.show()
			while len(self.mCinemaItems) == 0:
				tools.Time.sleep(0.5)
			if not self.mCinemaStop:
				if loaderNone: interface.Loader.hide()
				self.mPlayer.play(self.mCinemaPlaylist)

				while True:
					try:
						if self.mPlayer.isPlaying() and self.mPlayer.isPlayingVideo() and self.mPlayer.getTime() >= 0: break
					except: pass
					tools.Time.sleep(0.5)
				if not loaderNone: window.WindowCinema.close()

				# Callbacks don't seem to work with YouTube addon URLs. Check manually.
				while not self.mCinemaStop:
					self.mCinemaRunning = bool(len(self.mPlayer.getAvailableVideoStreams()) > 0 or self.mPlayer.isPlayingVideo()) # Must be wrapped in bool, otherwise returns 0.
					if not self.mCinemaRunning: break

					index = self.mCinemaPlaylist.getposition()
					try: time = self.mPlayer.getTime()
					except: time = 0
					if not self.mCinemaItems[index]['watched'] and time > Trailer.TrailerDuration:
						self.mCinemaItems[index]['watched'] = True
						self.watch(self.mCinemaItems[index]['imdb'])
					tools.Time.sleep(1)
		except:
			tools.Logger.error()

	def cinemaStart(self, type = tools.Media.TypeMovie, background = None, wait = False):
		thread = threading.Thread(target = self._cinemaStart, args = (type, background))
		thread.start()
		if wait: thread.join()

	def cinemaStop(self):
		# This is important.
		# The YouTube plugin needs some time to find and start playing the video.
		# Before the YouTube plugin is ready, Gaia might interrupt the trailer and start the actual episode.
		# A few seconds later, the YouTube plugin finally starts playing and then replaces the episode playback with the trailer playback.
		# In such a case, wait until the trailer starts playing, then stop playback and continue.
		self._cinemaWait1()

		interface.Loader.hide()
		self.mCinemaLock.acquire()
		self.mCinemaStop = True
		self.mCinemaRunning = False
		try: self.mCinemaPlaylist.clear()
		except: pass
		self.mCinemaLock.release()

		if self.cinemaInterrupt(): self.mPlayer.stop()
		self._cinemaWait2()
		if not tools.Settings.getInteger('interface.navigation.cinema.loader') == 0:
			from resources.lib.extensions import window
			window.WindowCinema.close()

	def _cinemaPlaylist(self):
		try:
			file = self.mPlayer.getPlayingFile()
			return self.mCinemaPlaylist.size() > 0 and ('googlevideo.com' in file or 'youtube.com' in file or 'youtu.be' in file)
		except: return False

	def _cinemaStop(self):
		if self._cinemaPlaylist():
			self.mPlayer.stop()

	def _cinemaWait1(self):
		if self.mCinemaRunning:
			count = 0
			while count < 40:
				try:
					if self.mPlayer.isPlaying() and self.mPlayer.isPlayingVideo() and self.mPlayer.getTime() >= 0: break
				except: pass
				tools.Time.sleep(0.5)
			if self.cinemaInterrupt(): self.mPlayer.stop()

	def _cinemaWait2(self):
		if not self.cinemaInterrupt():
			while self.mPlayer.isPlaying():
				tools.Time.sleep(0.5)
			self.mPlayer.stop()

	def cinemaRunning(self):
		return self.mCinemaRunning is True

	def cinemaCanceled(self):
		return self.mCinemaRunning is False # Can be None.

class Recap(Video):

	Id = 'recap'
	Duration = 600 # 10 minutes.
	Label = 35535
	Description = 35657

	def __init__(self, type = tools.Media.TypeMovie, kids = tools.Selection.TypeUndefined):
		Video.__init__(self, type = type, kids = kids)

	def _query(self, title = None, year = None, season = None):
		if season is None: return '"%s" recap|summary' % (title)
		else: return '"%s" "season %s"|s%s recap|summary' % (title, str(season), str(season))

	def _prefer(self, season = None):
		return []

	def _include(self, season = None):
		result = [['recap', 'recaps', 'summary']]
		if not season is None: result.append(['season+%d' % season, 's+%d' % season, 's%d' % season])
		return result

	def _exclude(self, season = None):
		result = ['trailer', 'episode', 'promo', 'promos']
		if not season is None:
			for episode in range(1, 101):
				result.append('s%02de%02d' % (season, episode))
				result.append('s%de%d' % (season, episode))
				result.append('e%02d' % (episode))
				result.append('e%d' % (episode))
		return result

	def play(self, title = None, year = None, season = None, link = None, art = None, items = None, resolve = True, loader = True, selection = None):
		if not season is None: season = int(season)
		return Video.play(self, query = self._query(title = title, year = year, season = season), title = title, link = link, art = art, items = items, resolve = resolve, loader = loader, selection = selection, prefer = self._prefer(season = season), include = self._include(season = season), exclude = self._exclude(season = season))

class Review(Video):

	Id = 'review'
	Duration = 1200 # 20 minutes.
	Label = 35651
	Description = 35658

	def __init__(self, type = tools.Media.TypeMovie, kids = tools.Selection.TypeUndefined):
		Video.__init__(self, type = type, kids = kids)

	def _query(self, title = None, year = None, season = None):
		if season is None: return '"%s" "review"' % (title)
		else: return '"%s" "season %s"|s%s "review"' % (title, str(season), str(season))

	def _prefer(self, season = None):
		return []

	def _include(self, season = None):
		result = [['review', 'reviews']]
		if not season is None: result.append(['season+%d' % season, 's+%d' % season, 's%d' % season])
		return result

	def _exclude(self, season = None):
		result = ['trailer', 'episode', 'promo', 'promos', 'recap', 'recaps']
		if not season is None:
			for episode in range(1, 101):
				result.append('s%02de%02d' % (season, episode))
				result.append('s%de%d' % (season, episode))
				result.append('e%02d' % (episode))
				result.append('e%d' % (episode))
		return result

	def play(self, title = None, year = None, season = None, link = None, art = None, items = None, resolve = True, loader = True, selection = None):
		if not season is None: season = int(season)
		return Video.play(self, query = self._query(title = title, year = year, season = season), title = title, link = link, art = art, items = items, resolve = resolve, loader = loader, selection = selection, prefer = self._prefer(season = season), include = self._include(season = season), exclude = self._exclude(season = season))

class Extra(Video):

	Id = 'extra'
	Duration = 1200 # 20 minutes.
	Label = 35653
	Description = 35659

	def __init__(self, type = tools.Media.TypeMovie, kids = tools.Selection.TypeUndefined):
		Video.__init__(self, type = type, kids = kids)

	def _query(self, title = None, year = None, season = None):
		# Do not search for "easter eggs", since this returns no results (eg: Gaame of Thrones).
		if season is None: return '"%s" "extra"|"extras"' % (title)
		else: return '"%s" "season %s"|s%s "extra"|"extras"' % (title, str(season), str(season))

	def _prefer(self, season = None):
		return []

	def _include(self, season = None):
		result = [['extra', 'extras', 'easter+egg', 'easter+eggs']]
		if not season is None: result.append(['season+%d' % season, 's+%d' % season, 's%d' % season])
		return result

	def _exclude(self, season = None):
		result = ['trailer', 'episode', 'promo', 'promos', 'recap', 'recaps']
		if not season is None:
			for episode in range(1, 101):
				result.append('s%02de%02d' % (season, episode))
				result.append('s%de%d' % (season, episode))
				result.append('e%02d' % (episode))
				result.append('e%d' % (episode))
		return result

	def play(self, title = None, year = None, season = None, link = None, art = None, items = None, resolve = True, loader = True, selection = None):
		if not season is None: season = int(season)
		return Video.play(self, query = self._query(title = title, year = year, season = season), title = title, link = link, art = art, items = items, resolve = resolve, loader = loader, selection = selection, prefer = self._prefer(season = season), include = self._include(season = season), exclude = self._exclude(season = season))

class Deleted(Video):

	Id = 'deleted'
	Duration = 1200 # 20 minutes.
	Label = 35654
	Description = 35660

	def __init__(self, type = tools.Media.TypeMovie, kids = tools.Selection.TypeUndefined):
		Video.__init__(self, type = type, kids = kids)

	def _query(self, title = None, year = None, season = None):
		if season is None: return '"%s" "deleted"|"extended"' % (title)
		else: return '"%s" "season %s"|s%s "deleted"|"extended"' % (title, str(season), str(season))

	def _prefer(self, season = None):
		return []

	def _include(self, season = None):
		result = [['deleted', 'delete', 'extended']]
		if not season is None: result.append(['season+%d' % season, 's+%d' % season, 's%d' % season])
		return result

	def _exclude(self, season = None):
		result = ['trailer', 'episode', 'promo', 'promos', 'recap', 'recaps']
		if not season is None:
			for episode in range(1, 101):
				result.append('s%02de%02d' % (season, episode))
				result.append('s%de%d' % (season, episode))
				result.append('e%02d' % (episode))
				result.append('e%d' % (episode))
		return result

	def play(self, title = None, year = None, season = None, link = None, art = None, items = None, resolve = True, loader = True, selection = None):
		if not season is None: season = int(season)
		return Video.play(self, query = self._query(title = title, year = year, season = season), title = title, link = link, art = art, items = items, resolve = resolve, loader = loader, selection = selection, prefer = self._prefer(season = season), include = self._include(season = season), exclude = self._exclude(season = season))

class Making(Video):

	Id = 'making'
	Duration = 1800 # 30 minutes.
	Label = 35650
	Description = 35661

	def __init__(self, type = tools.Media.TypeMovie, kids = tools.Selection.TypeUndefined):
		Video.__init__(self, type = type, kids = kids)

	def _query(self, title = None, year = None, season = None):
		if season is None: return '"%s" "making of"|"behind the scenes"|"inside"|"backstage"' % (title)
		else: return '"%s" "season %s"|s%s "making of"|"behind the scenes"|"inside"|"backstage"' % (title, str(season), str(season))

	def _prefer(self, season = None):
		return []

	def _include(self, season = None):
		result = [['making+of', 'behind+the+scenes', 'inside', 'backstage']]
		if not season is None: result.append(['season+%d' % season, 's+%d' % season, 's%d' % season])
		return result

	def _exclude(self, season = None):
		result = ['trailer', 'episode', 'promo', 'promos', 'recap', 'recaps', 'summary']
		if not season is None:
			for episode in range(1, 101):
				result.append('s%02de%02d' % (season, episode))
				result.append('s%de%d' % (season, episode))
				result.append('e%02d' % (episode))
				result.append('e%d' % (episode))
		return result

	def play(self, title = None, year = None, season = None, link = None, art = None, items = None, resolve = True, loader = True, selection = None):
		if not season is None: season = int(season)
		return Video.play(self, query = self._query(title = title, year = year, season = season), title = title, link = link, art = art, items = items, resolve = resolve, loader = loader, selection = selection, prefer = self._prefer(season = season), include = self._include(season = season), exclude = self._exclude(season = season))

class Director(Video):

	Id = 'director'
	Duration = 1800 # 30 minutes.
	Label = 35377
	Description = 35662

	def __init__(self, type = tools.Media.TypeMovie, kids = tools.Selection.TypeUndefined):
		Video.__init__(self, type = type, kids = kids)

	def _query(self, title = None, year = None, season = None):
		if season is None: return '"%s" "director"' % (title)
		else: return '"%s" "season %s"|s%s "director"' % (title, str(season), str(season))

	def _prefer(self, season = None):
		return []

	def _include(self, season = None):
		result = [['director', 'directors']]
		if not season is None: result.append(['season+%d' % season, 's+%d' % season, 's%d' % season])
		return result

	def _exclude(self, season = None):
		result = ['trailer', 'episode', 'promo', 'promos', 'recap', 'recaps', 'summary']
		if not season is None:
			for episode in range(1, 101):
				result.append('s%02de%02d' % (season, episode))
				result.append('s%de%d' % (season, episode))
				result.append('e%02d' % (episode))
				result.append('e%d' % (episode))
		return result

	def play(self, title = None, year = None, season = None, link = None, art = None, items = None, resolve = True, loader = True, selection = None):
		if not season is None: season = int(season)
		return Video.play(self, query = self._query(title = title, year = year, season = season), title = title, link = link, art = art, items = items, resolve = resolve, loader = loader, selection = selection, prefer = self._prefer(season = season), include = self._include(season = season), exclude = self._exclude(season = season))

class Interview(Video):

	Id = 'interview'
	Duration = 1800 # 30 minutes.
	Label = 35655
	Description = 35663

	def __init__(self, type = tools.Media.TypeMovie, kids = tools.Selection.TypeUndefined):
		Video.__init__(self, type = type, kids = kids)

	def _query(self, title = None, year = None, season = None):
		if season is None: return '"%s" "interview"' % (title)
		else: return '"%s" "season %s"|s%s "interview"' % (title, str(season), str(season))

	def _prefer(self, season = None):
		return []

	def _include(self, season = None):
		result = [['interview', 'interviews']]
		if not season is None: result.append(['season+%d' % season, 's+%d' % season, 's%d' % season])
		return result

	def _exclude(self, season = None):
		result = ['trailer', 'episode', 'promo', 'promos', 'recap', 'recaps', 'summary']
		if not season is None:
			for episode in range(1, 101):
				result.append('s%02de%02d' % (season, episode))
				result.append('s%de%d' % (season, episode))
				result.append('e%02d' % (episode))
				result.append('e%d' % (episode))
		return result

	def play(self, title = None, year = None, season = None, link = None, art = None, items = None, resolve = True, loader = True, selection = None):
		if not season is None: season = int(season)
		return Video.play(self, query = self._query(title = title, year = year, season = season), title = title, link = link, art = art, items = items, resolve = resolve, loader = loader, selection = selection, prefer = self._prefer(season = season), include = self._include(season = season), exclude = self._exclude(season = season))

class Explanation(Video):

	Id = 'explanation'
	Duration = 1200 # 20 minutes.
	Label = 35652
	Description = 35664

	def __init__(self, type = tools.Media.TypeMovie, kids = tools.Selection.TypeUndefined):
		Video.__init__(self, type = type, kids = kids)

	def _query(self, title = None, year = None, season = None):
		if season is None: return '"%s" "explained"|"explanation"|"ending"' % (title)
		else: return '"%s" "season %s"|s%s "explained"|"explanation"|"ending"' % (title, str(season), str(season))

	def _prefer(self, season = None):
		return []

	def _include(self, season = None):
		result = [['explained', 'explanation', 'ending']]
		if not season is None: result.append(['season+%d' % season, 's+%d' % season, 's%d' % season])
		return result

	def _exclude(self, season = None):
		result = ['trailer', 'episode', 'promo', 'promos', 'recap', 'recaps', 'summary']
		if not season is None:
			for episode in range(1, 101):
				result.append('s%02de%02d' % (season, episode))
				result.append('s%de%d' % (season, episode))
				result.append('e%02d' % (episode))
				result.append('e%d' % (episode))
		return result

	def play(self, title = None, year = None, season = None, link = None, art = None, items = None, resolve = True, loader = True, selection = None):
		if not season is None: season = int(season)
		return Video.play(self, query = self._query(title = title, year = year, season = season), title = title, link = link, art = art, items = items, resolve = resolve, loader = loader, selection = selection, prefer = self._prefer(season = season), include = self._include(season = season), exclude = self._exclude(season = season))
