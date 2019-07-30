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

class Trailer(database.Database):

	Name = 'trailers' # The name of the file. Update version number of the database structure changes.

	TrailerCount = 5
	TrailerDuration = 5

	Keys = ['QUl6YVN5RDd2aFpDLTYta2habTVuYlVyLTZ0Q0JRQnZWcnFkeHNz', 'QUl6YVN5Q2RiNEFNenZpVG0yaHJhSFY3MXo2Nl9HNXBhM2ZvVXd3']

	LinkBase = 'http://www.youtube.com'
	LinkSearch = 'https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&maxResults=5&videoDuration=short&q=%s'
	LinkYoutubeSearch = 'https://www.googleapis.com/youtube/v3/search?q='
	LinkYoutubeWatch = 'http://www.youtube.com/watch?v=%s'
	LinkKey = '&key=' + tools.Converter.base64From((random.choice(Keys)), url = True)

	def __init__(self, type = tools.Media.TypeMovie, kids = tools.Selection.TypeUndefined):
		database.Database.__init__(self, Trailer.Name)
		self.mType = type
		self.mKids = kids
		self.mPlayer = interface.Player()
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

	@classmethod
	def _search(self, link):
		try:
			query = urlparse.parse_qs(urlparse.urlparse(link).query)['q'][0]
			link = Trailer.LinkSearch % urllib.quote_plus(query) + Trailer.LinkKey
			result = network.Networker(link).retrieve()
			items = tools.Converter.jsonFrom(result)['items']
			items = [(i['id']['videoId']) for i in items]
			for link in items:
				link = self._extract(link)
				if not link is None: return link
		except:
			tools.Logger.error()

	@classmethod
	def _extract(self, link):
		try:
			id = link.split('?v=')[-1].split('/')[-1].split('?')[0].split('&')[0]
			link = self.LinkYoutubeWatch % id
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

	@classmethod
	def _resolve(self, title, link = None):
		try:
			if link.startswith(Trailer.LinkBase):
				link = self._extract(link)
				if link == None: raise Exception()
				return link
			elif not link.startswith('http://'):
				link = Trailer.LinkYoutubeWatch % link
				link = self._extract(link)
				if link == None: raise Exception()
				return link
			else:
				raise Exception()
		except:
			query = title + ' trailer'
			query = Trailer.LinkYoutubeSearch + query
			link = self._search(query)
			if link == None: return
			return link

	def play(self, title = None, link = None, art = None, items = None, resolve = True, loader = True):
		try:
			if loader: interface.Loader.show()

			single = items == None
			if single: items = [{'title' : title, 'link' : link, 'art' : art}]

			if resolve:
				for i in range(len(items)):
					items[i]['link'] = self._resolve(items[i]['title'], items[i]['link'])

			items = [item for item in items if not item['link'] == None]
			if len(items) == 0: return None

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

			landscape = '0'
			if landscape == '0' and 'landscape' in i: landscape = i['landscape']

			art = {}
			if not poster == '0' and not poster == None: art.update({'poster' : poster})
			if not icon == '0' and not icon == None: art.update({'icon' : icon})
			if not thumb == '0' and not thumb == None: art.update({'thumb' : thumb})
			if not banner == '0' and not banner == None: art.update({'banner' : banner})
			if not clearlogo == '0' and not clearlogo == None: art.update({'clearlogo' : clearlogo})
			if not clearart == '0' and not clearart == None: art.update({'clearart' : clearart})
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
					result.append({'imdb' : item['imdb'], 'title' : '%s (%s)' % (item['title'], str(item['year'])), 'art' : item['art']})
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
					result.append({'imdb' : item['imdb'], 'title' : '%s Season 1' % title, 'art' : item['art']})
			except: pass
		return result

	def _cinemaSearch(self, item):
		try:
			link = self._resolve(item['title'])
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
