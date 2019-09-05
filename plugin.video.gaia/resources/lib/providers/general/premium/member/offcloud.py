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

import re,time,threading
from resources.lib.modules import client
from resources.lib.modules import control
from resources.lib.extensions import provider
from resources.lib.extensions import metadata
from resources.lib.extensions import tools
from resources.lib.debrid import offcloud

class source(provider.ProviderBase):

	def __init__(self):
		provider.ProviderBase.__init__(self, supportMovies = True, supportShows = True)

		self.pack = True # Checked by provider.py
		self.priority = 0
		self.language = ['un']
		self.domains = ['offcloud.com']
		self.base_link = 'https://offcloud.com'
		self.mutex = threading.Lock()
		self.items = []

	def instanceEnabled(self):
		core = offcloud.Core()
		return core.accountEnabled() and core.accountValid()

	def _item(self, category, id, season, episode):
		try:
			item = offcloud.Core().item(category = category, id = id, transfer = True, files = True, season = season, episode = episode)
			try: self.mutex.acquire()
			except: pass
			if item: self.items.append(item)
			try: self.mutex.release()
			except: pass
		except:
			tools.Logger.error()

	def _items(self, category, title, titles, year, season, episode, pack):
		try:
			timerEnd = tools.Settings.getInteger('scraping.providers.timeout') - 3
			timer = tools.Time(start = True)

			items = offcloud.Core().items(category = category)
			try: self.mutex.acquire()
			except: pass

			threads = []
			for item in items:
				if item['status'] == offcloud.Core.StatusFinished: # Only finished downloads.
					id = item['id']
					if not id in self.ids:
						meta = metadata.Metadata(name = item['name'], title = title, titles = titles, year = year, season = season, episode = episode, pack = pack)
						if not meta.ignore(size = False):
							self.ids.append(id)
							if category == offcloud.Core.CategoryInstant:
								self.items.append(item)
							else:
								threads.append(threading.Thread(target = self._item, args = (category, id, season, episode)))

			try: self.mutex.release()
			except: pass

			if len(threads) > 0:
				[thread.start() for thread in threads]

				while True:
					if timer.elapsed() > timerEnd:
						break
					if all([not thread.is_alive() for thread in threads]):
						break
					time.sleep(0.5)
		except:
			tools.Logger.error()

	def sources(self, url, hostDict, hostprDict):
		self.items = [] # NB: The same object of the provider is used for both normal episodes and season packs. Make sure it is cleared from the previous run.
		sources = []
		try:
			if url == None: raise Exception()
			if not offcloud.Core().accountValid(): raise Exception()

			data = self._decode(url)

			if 'exact' in data and data['exact']:
				title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
				titles = None
				year = None
				season = None
				episode = None
				pack = False
				packCount = 0
			else:
				title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
				titles = data['alternatives'] if 'alternatives' in data else None
				year = int(data['year']) if 'year' in data and not data['year'] == None else None
				season = int(data['season']) if 'season' in data and not data['season'] == None else None
				episode = int(data['episode']) if 'episode' in data and not data['episode'] == None else None
				pack = data['pack'] if 'pack' in data else False
				packCount = data['packcount'] if 'packcount' in data else False

			if not self._query(title, year, season, episode, pack): return sources

			timerEnd = tools.Settings.getInteger('scraping.providers.timeout') - 3
			timer = tools.Time(start = True)

			threads = []
			self.ids = []
			threads.append(threading.Thread(target = self._items, args = (offcloud.Core.CategoryCloud, title, titles, year, season, episode, pack)))
			threads.append(threading.Thread(target = self._items, args = (offcloud.Core.CategoryInstant, title, titles, year, season, episode, pack)))
			[thread.start() for thread in threads]

			while True:
				if timer.elapsed() > timerEnd:
					break
				if all([not thread.is_alive() for thread in threads]):
					break
				time.sleep(0.5)

			try: self.mutex.acquire()
			except: pass
			items = self.items
			try: self.mutex.release()
			except: pass

			for item in items:
				try:
					jsonName = item['video']['name']
					try:
						if not item['name'] == jsonName:
							jsonName = item['name'] + ' - ' + jsonName # Sometimes metadata, like quality, is only in the folder name, not the file name.
					except: pass

					jsonLink = item['video']['link']
					try: jsonSize = item['size']['bytes']
					except: jsonSize = None

					# Metadata
					meta = metadata.Metadata(name = jsonName, title = title, titles = titles, year = year, season = season, episode = episode, size = jsonSize, pack = pack, packCount = packCount)

					# Add
					sources.append({'url' : jsonLink, 'premium' : True, 'debridonly' : True, 'direct' : True, 'memberonly' : True, 'source' : 'OffCloud', 'language' : self.language[0], 'quality':  meta.videoQuality(), 'metadata' : meta, 'file' : jsonName})
				except:
					pass
			return sources
		except:
			return sources
