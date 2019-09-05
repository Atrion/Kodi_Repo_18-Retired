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

import re,urllib,urlparse,threading
from resources.lib.modules import client
from resources.lib.extensions import provider
from resources.lib.extensions import metadata
from resources.lib.extensions import tools
from resources.lib.externals.beautifulsoup import BeautifulSoup

class source(provider.ProviderBase):

	def __init__(self):
		provider.ProviderBase.__init__(self, supportMovies = True, supportShows = True)

		self.pack = True # Checked by provider.py
		self.priority = 0
		self.language = ['un']
		self.domains = ['binzb.com']
		self.base_link = 'http://binzb.com'
		self.search_link = '/search?q=%s&p=%i'

	def _link(self, link):
		try:
			html = BeautifulSoup(client.request(link))
			html = html.find_all('table', class_ = 'list')[0]
			html = html.find_all('tr', recursive = False)[4]
			resolved = self.base_link + html.find_all('a')[0]['href']
			self.tLock.acquire()
			self.tLinks[link] = resolved
			self.tLock.release()
		except:
			tools.Logger.error()

	def sources(self, url, hostDict, hostprDict):
		sources = []
		found = []
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

			if not self._query(query): return sources

			url = urlparse.urljoin(self.base_link, self.search_link)

			pageLimit = tools.Settings.getInteger('scraping.providers.pages')
			pageCounter = 0

			page = 1
			added = False

			threads = []
			self.tLinks = {}
			self.tLock = threading.Lock()

			timerEnd = tools.Settings.getInteger('scraping.providers.timeout') - 8
			timer = tools.Time(start = True)

			while True:
				# Stop searching 8 seconds before the provider timeout, otherwise might continue searching, not complete in time, and therefore not returning any links.
				if timer.elapsed() > timerEnd:
					break

				pageCounter += 1
				if pageLimit > 0 and pageCounter > pageLimit:
					break

				urlNew = url % (urllib.quote_plus(query), page)
				html = BeautifulSoup(client.request(urlNew))

				page += 1
				added = False

				htmlTable = html.find_all('table', class_ = 'list')[0]
				htmlRows = htmlTable.find_all('tr', recursive = False)

				for i in range(1, len(htmlRows)):
					htmlRow = htmlRows[i]
					htmlColumns = htmlRow.find_all('td', recursive = False) # Use children and no further.

					# Name
					# Put through BeautifulSoup again to remove highlight HTML tags.
					htmlName = BeautifulSoup(htmlColumns[0].find_all('a')[0].getText()).text

					# Size
					htmlSize = htmlColumns[3].getText()

					# Link
					htmlLink = htmlColumns[0].find_all('a')[0]['href']

					# Age
					htmlAge = htmlColumns[1].getText().lower()
					if 'day' in htmlAge: htmlAge = int(htmlAge.replace('days', '').replace('day', '').strip())
					elif 'week' in htmlAge: htmlAge = int(htmlAge.replace('weeks', '').replace('week', '').strip()) * 7
					elif 'month' in htmlAge: htmlAge = int(htmlAge.replace('months', '').replace('month', '').strip()) * 30
					elif 'year' in htmlAge: htmlAge = int(htmlAge.replace('years', '').replace('year', '').strip()) * 365
					else: htmlAge = 0

					# Metadata
					meta = metadata.Metadata(name = htmlName, title = title, titles = titles, year = year, season = season, episode = episode, pack = pack, packCount = packCount, link = htmlLink, size = htmlSize, age = htmlAge)
					meta.mIgnoreLength *= 10 # Otherwise too restrictive for very long usenet titles.

					# Ignore
					meta.ignoreAdjust(contains = ignoreContains)
					if meta.ignore(False):
						continue

					# Resolve
					thread = threading.Thread(target = self._link, args = (htmlLink,))
					threads.append(thread)
					thread.start()

					# Add
					sources.append({'url' : htmlLink, 'debridonly' : False, 'direct' : False, 'source' : 'usenet', 'language' : self.language[0], 'quality':  meta.videoQuality(), 'metadata' : meta, 'file' : htmlName})
					added = True

				if not added: # Last page reached with a working torrent
					break
		except:
			pass

		while True:
			if timer.elapsed() > timerEnd: break
			if not any([thread.is_alive() for thread in threads]): break
			tools.Time.sleep(0.5)
		result = []
		self.tLock.acquire()
		for i in range(len(sources)):
			link = sources[i]['url']
			if link in self.tLinks:
				sources[i]['url'] = self.tLinks[link]
				result.append(sources[i])
		self.tLock.release()
		return result
