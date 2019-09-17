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

import re, math, urlparse, urllib, threading
from resources.lib.modules import client
from resources.lib.extensions import provider
from resources.lib.extensions import metadata
from resources.lib.extensions import tools

class source(provider.ProviderBase):

	def __init__(self):
		provider.ProviderBase.__init__(self, supportMovies = True, supportShows = True)

		self.pack = True # Checked by provider.py
		self.priority = 0
		self.language = ['un']

		self.domains = ['torrent-paradise.ml']
		self.base_link = 'https://torrent-paradise.ml'
		self.meta_link = 'generated/inx.meta.json'
		self.magnet_link = 'magnet:?xt=urn:btih:%s&tr=&tr=udp%%3A%%2F%%2Ftracker.leechers-paradise.org%%3A6969&tr=udp%%3A%%2F%%2Ftracker.opentrackr.org%%3A1337%%2Fannounce'

		self.pathDirectory = tools.System.pathProviders('TorrentParadise')
		self.pathCurrent = None

		self.timeoutOther = 20 # 15 seconds is too little for the post-processing and the stuff that core.py has to do.
		self.timeoutTotal = tools.Settings.getInteger('scraping.providers.timeout') - self.timeoutOther
		if self.timeoutTotal < self.timeoutOther: self.timeoutTotal = self.timeoutOther
		self.timeoutCurrent = 0

		self.lock = threading.Lock()
		self.items = []

		self.thresholdWords = 3
		self.thresholdCount = 0.30
		self.thresholdQuery = 0.75
		self.exclusions = ['the', 'an', 'a', 'and', 'of', 'for', 'nor', 'or', 'but', 'so', 'if', 'as', 'in', 'to', 'on']

		self.inv_prefix = 'inv'
		self.inv_split = []
		self.inv_items = []
		self.inv_required = []
		self.inv_count = 0
		self.inv_total = 0
		self.inv_link = None

		self.inx_prefix = 'inx'
		self.inx_split = []
		self.inx_items = []
		self.inx_link = None

	def _duplicates(self, items):
		return list(set(items))

	def _tempPath(self, prefix, index):
		return tools.File.joinPath(self.pathCurrent, str(prefix) + str(index))

	def _tempLoad(self, prefix, index, json = False):
		try:
			path = self._tempPath(prefix, index)
			if tools.File.exists(path):
				result = tools.File.readNow(path)
				if json: result = tools.Converter.jsonFrom(result)
				return result
		except: pass
		return None

	def _tempSave(self, prefix, index, data, json = False):
		try:
			if data:
				if json: data = tools.Converter.jsonTo(data)
				return tools.File.writeNow(self._tempPath(prefix, index), data)
		except: pass
		return False

	def _queryCreate(self, query, exclude = True, mini = False):
		if not query: return None
		query = re.sub('[^\w\s]', '', query) # Remove symbols
		query = query.lower().split(' ')
		query = [i for i in query if i]
		query = self._duplicates(query)

		if exclude:
			for i in self.exclusions:
				while True:
					try: query.remove(i)
					except: break

		if mini: # Only search for the main words in the title.
			query.sort(key = lambda i : len(i))
			query = query[::-1][:self.thresholdWords]

		return query

	def _request(self, section, timeout = 60, json = False):
		link = urlparse.urljoin(self.base_link, section)
		result = client.request(link, timeout = timeout)
		if json: result = tools.Converter.jsonFrom(result)
		return result

	def _indexes(self, query, split):
		indexes = []
		for i in query:
			try:
				index = 0
				while split[index] < i: index += 1
				if index > 0: index -= 1
				indexes.append(index)
			except: pass # When not found.
		return self._duplicates(indexes)

	def _meta(self, query):
		try:
			result = self._request(self.meta_link, json = True)
			self.lock.acquire()
			self.inv_split = result['invsplits']
			self.inx_split = result['inxsplits']
			self.inv_link = result['invURLBase']
			self.inx_link = result['inxURLBase']

			created = str(result['created'])
			self.pathCurrent = tools.File.joinPath(self.pathDirectory, created)
			if not tools.File.existsDirectory(self.pathCurrent):
				tools.File.deleteDirectory(self.pathDirectory)
				tools.File.makeDirectory(self.pathCurrent)
			return True
		except:
			tools.Logger.error()
			return False
		finally:
			try: self.lock.release()
			except: pass

	def _filterCount(self, query):
		threshold = len(query)
		if threshold > 2: threshold = math.ceil(threshold * self.thresholdCount)
		self.lock.acquire()
		self.inv_items = dict((i, self.inv_items.count(i)) for i in set(self.inv_items))
		self.inv_items = {key : value for key, value in self.inv_items.iteritems() if value >= threshold}
		self.inv_items = sorted(self.inv_items.items(), key = lambda i : i[1])
		self.inv_items = self.inv_items[-200:] # Limit the items, otherwise the scraping takes too long.
		self.inv_items = [key for key, value in self.inv_items]
		self.lock.release()

	def _filterQuery(self, query, required):
		threshold = math.ceil(len(query) * self.thresholdQuery)
		self.items = [dict(i, **{'textlower' : i['text'].lower()}) for i in self.items]
		if required: self.items = [i for i in self.items if all(j in i['textlower'] for j in required)]
		self.items = [i for i in self.items if sum(int(j in i['textlower']) for j in query) >= threshold]

	def _select(self):
		self.lock.acquire()
		self.items = []
		for i in self.inv_items:
			for j in range(len(self.inx_items)):
				if self.inx_items[j]['id'] == i:
					self.items.append(self.inx_items[j])
					break
		self.lock.release()

	def _fetchInv(self, index, query, timeout = 60, required = False):
		try:
			result = self._tempLoad(self.inv_prefix, index, False)
			if result == None:
				result = self._request(self.inv_link + str(index), timeout = timeout, json = False)
				self._tempSave(self.inv_prefix, index, result, False)

			if result == None: return False
			if not required:
				while not self.inv_count == self.inv_total:
					tools.Time.sleep(0.2)
			empty = len(self.inv_required) == 0

			result = result.split('\n')
			version = int(result[0])
			if not version == 1 and not version == 2:
				return tools.Logger.log('TorrentParadise: Invalid invinx version')
			result = result[1:]
			content = []
			for i in result:
				try:
					columns = i.split(',')
					try: key = urllib.unquote(columns[0]).decode('utf8')
					except: key = urllib.unquote(columns[0])
					values = columns[1:]
					if key in query:
						if version == 2: values = [j.replace('%2C', ',') for j in values]
						if required or empty: content.extend(values)
						else: content.extend([j for j in values if j in self.inv_required])
				except:
					tools.Logger.error()
			self.lock.acquire()
			if required: self.inv_required.extend(content)
			else: self.inv_items.extend(content)
			return True
		except:
			tools.Logger.error()
			return False
		finally:
			if required: self.inv_count += 1
			try: self.lock.release()
			except: pass

	def _retrieveInv(self, query, required = None):
		timeout = self.timeoutTotal / 2
		timeoutThread = timeout - 2
		threads = []

		if required:
			indexes = self._indexes(required, self.inv_split)
			self.inv_count = 0
			self.inv_total = len(indexes)
			for i in indexes:
				threads.append(threading.Thread(target = self._fetchInv, args = (i, required, timeoutThread, True)))

		indexes = self._indexes(query, self.inv_split)
		for i in indexes:
			threads.append(threading.Thread(target = self._fetchInv, args = (i, query, timeoutThread, False)))
		[i.start() for i in threads]

		tools.Time.sleep(0.5)
		timer = tools.Time(start = True)
		while timer.elapsed() < timeout and any(i.is_alive() for i in threads):
			tools.Time.sleep(0.5)
		self.timeoutCurrent = timer.elapsed()

		# For short titles, like "V for Vendetta".
		# Do not search for the required keywords by default, since these often contain a bunch of links, causing the query to be extremely slow.
		if len(query) < self.thresholdWords:
			self.inv_items.extend(self.inv_required)

	def _fetchInx(self, index, query, timeout = 60):
		try:
			result = self._tempLoad(self.inx_prefix, index, True)
			if result == None:
				result = self._request(self.inx_link + str(index), timeout = timeout, json = True)
				self._tempSave(self.inx_prefix, index, result, True)
			if result == None: return False
			result = [i for i in result if i['id'] in self.inv_items]
			self.lock.acquire()
			self.inx_items.extend(result)
			return True
		except:
			tools.Logger.error()
			return False
		finally:
			try: self.lock.release()
			except: pass

	def _retrieveInx(self, query):
		timeout = self.timeoutTotal - self.timeoutCurrent
		timeoutThread = timeout - 2
		threads = []

		indexes = self._indexes(self.inv_items, self.inx_split)
		for i in indexes:
			threads.append(threading.Thread(target = self._fetchInx, args = (i, query, timeoutThread)))
		[i.start() for i in threads]

		tools.Time.sleep(0.5)
		timer = tools.Time(start = True)
		while timer.elapsed() < timeout and any(i.is_alive() for i in threads):
			tools.Time.sleep(0.5)

	def sources(self, url, hostDict, hostprDict):
		sources = []
		try:
			if url == None: raise Exception()

			ignoreContains = None
			data = self._decode(url)

			if 'exact' in data and data['exact']:
				query = title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
				titles = None
				required = None
				year = None
				season = None
				episode = None
				pack = False
				packCount = None
			else:
				title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
				titles = data['alternatives'] if 'alternatives' in data else None
				year = int(data['year']) if 'year' in data and not data['year'] == None else None
				season = int(data['season']) if 'season' in data and not data['season'] == None else None
				episode = int(data['episode']) if 'episode' in data and not data['episode'] == None else None
				pack = data['pack'] if 'pack' in data else False
				packCount = data['packcount'] if 'packcount' in data else None

				query = title
				if 'tvshowtitle' in data:
					# Search special episodes by name. All special episodes are added to season 0 by Trakt and TVDb. Hence, do not search by filename (eg: S02E00), since the season is not known.
					if (season == 0 or episode == 0) and ('title' in data and not data['title'] == None and not data['title'] == ''):
						title = '%s %s' % (data['tvshowtitle'], data['title']) # Change the title for metadata filtering.
						required = data['title']
						ignoreContains = len(data['title']) / float(len(title)) # Increase the required ignore ration, since otherwise individual episodes and season packs are found as well.
					else:
						if pack: required = 'Season %d' % (season)
						else: required = 'S%02dE%02d' % (season, episode)
				else:
					required = str(year)

			if not self._query(query): return sources
			queryFull = self._queryCreate(query, True)
			query = self._queryCreate(query, True, True)
			required = self._queryCreate(required, False)

			if self._meta(query):
				self._retrieveInv(query, required)
				self._filterCount(query)
				self._retrieveInx(query)
				self._select()
				self._filterQuery(queryFull, required)

				for item in self.items:

					# Name
					jsonName = item['text']

					# Size
					jsonSize = item['len']

					# Seeds
					jsonSeeds = item['s']

					# Link
					jsonLink = self.magnet_link % item['id']

					# Metadata
					meta = metadata.Metadata(name = jsonName, title = title, titles = titles, year = year, season = season, episode = episode, pack = pack, packCount = packCount, link = jsonLink, size = jsonSize, seeds = jsonSeeds)

					# Ignore
					meta.ignoreAdjust(contains = ignoreContains)
					if meta.ignore(True): continue

					# Add
					sources.append({'url' : jsonLink, 'debridonly' : False, 'direct' : False, 'source' : 'torrent', 'language' : self.language[0], 'quality': meta.videoQuality(), 'metadata' : meta, 'file' : jsonName})

			return sources
		except:
			tools.Logger.error()
			return sources
