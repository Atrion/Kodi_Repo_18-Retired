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

import re,urllib,urlparse,datetime,math,locale,threading
from resources.lib.modules import client
from resources.lib.extensions import provider
from resources.lib.extensions import metadata
from resources.lib.extensions import tools
from resources.lib.extensions import convert
from resources.lib.externals.beautifulsoup import BeautifulSoup

class source(provider.ProviderBase):

	def __init__(self):
		provider.ProviderBase.__init__(self, supportMovies = True, supportShows = True)

		self.pack = True # Checked by provider.py
		self.priority = 0
		self.language = ['un']
		self.domains = ['nzbfriends.com']
		self.base_link = 'http://nzbfriends.com'
		self.search_link = '/?init=form&type=subject&age=0&group=&min=50&max=&sort=relevance&limit=200&q=%s&page=%d'
		self.download_link = '/nzb/?collection=%s&uuid=%s&getnzb_transparent=1'

	def _link(self, url, index):
		try:
			html = BeautifulSoup(client.request(url))
			htmlCollection = html.find('input', {'name': 'collection'})['value']
			htmlUuid = html.find('input', {'name': 'uuid'})['value']
			self.tLock.acquire()
			if htmlUuid and htmlCollection: self.tSources[index]['url'] = urlparse.urljoin(self.base_link, self.download_link) % (htmlCollection, htmlUuid)
		except:
			tools.Logger.error()
		finally:
			try: self.tLock.release()
			except: pass

	def sources(self, url, hostDict, hostprDict):
		self.tSources = []
		try:
			if url == None: raise Exception()

			ignoreContains = None
			data = self._decode(url)

			if 'exact' in data and data['exact']:
				query = title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
				titles = None
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

				if 'tvshowtitle' in data:
					# Search special episodes by name. All special episodes are added to season 0 by Trakt and TVDb. Hence, do not search by filename (eg: S02E00), since the season is not known.
					if (season == 0 or episode == 0) and ('title' in data and not data['title'] == None and not data['title'] == ''):
						title = '%s %s' % (data['tvshowtitle'], data['title']) # Change the title for metadata filtering.
						query = title
						ignoreContains = len(data['title']) / float(len(title)) # Increase the required ignore ration, since otherwise individual episodes and season packs are found as well.
					else:
						if pack: query = '%s %d' % (title, season)
						else: query = '%s S%02dE%02d' % (title, season, episode)
				else:
					query = '%s %d' % (title, year)
				query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', ' ', query)

			query = urllib.quote_plus(query)
			if not self._query(query): return sources
			
			url = urlparse.urljoin(self.base_link, self.search_link)

			pageLimit = tools.Settings.getInteger('scraping.providers.pages')
			pageCounter = 0 # Page starts at 1, but incremented before first request.

			timerTimeout = tools.Settings.getInteger('scraping.providers.timeout')
			timerEnd = timerTimeout - 8
			timer = tools.Time(start = True)

			threads = []
			self.tLock = threading.Lock()

			while True:
				try:
					# Stop searching 8 seconds before the provider timeout, otherwise might continue searching, not complete in time, and therefore not returning any links.
					if timer.elapsed() > timerEnd: break

					added = False
					pageCounter += 1
					if pageLimit > 0 and pageCounter > pageLimit: break

					html = BeautifulSoup(client.request(url % (query, pageCounter)))
					htmlTable = html.find_all('table', class_ = 'results')
					htmlTable = htmlTable[len(htmlTable) - 1]
					htmlRows = htmlTable.find_all('tr')

					for i in range(1, len(htmlRows)):
						try:
							htmlRow = htmlRows[i]
							htmlColumns = htmlRow.find_all('td', recursive = False) # Use children and no further.

							# Name
							htmlName = htmlColumns[0].find_all('a')[0].getText()

							# Link
							htmlLink = urlparse.urljoin(self.base_link, htmlColumns[0].find_all('a')[0]['href'])

							# Size
							htmlSize = htmlColumns[1].getText()

							# Age
							htmlAge = htmlColumns[3].getText()
							htmlAge = int(convert.ConverterDuration(htmlAge).value(convert.ConverterDuration.UnitDay))

							# Metadata
							meta = metadata.Metadata(name = htmlName, title = title, titles = titles, year = year, season = season, episode = episode, pack = pack, packCount = packCount, link = htmlLink, size = htmlSize, age = htmlAge)

							# Ignore
							meta.ignoreAdjust(contains = ignoreContains, length = 0.3)
							if meta.ignore(False): continue

							# Add
							self.tLock.acquire()
							self.tSources.append({'url' : None, 'debridonly' : False, 'direct' : False, 'source' : 'usenet', 'language' : self.language[0], 'quality':  meta.videoQuality(), 'metadata' : meta, 'file' : htmlName})
							self.tLock.release()
							added = True

							# Link
							thread = threading.Thread(target = self._link, args = (htmlLink, len(self.tSources) - 1))
							threads.append(thread)
							thread.start()

						except:
							pass

					if not added: break
				except:
					break

			# First filter out all non-related links before doing the hash lookup.
			timerTimeout -= 2
			while True:
				if timer.elapsed() > timerTimeout: break
				if not any([thread.is_alive() for thread in threads]): break
				tools.Time.sleep(0.5)

			try: self.tLock.release()
			except: pass
		except:
			try: self.tLock.release()
			except: pass

		return [i for i in self.tSources if i['url']]
