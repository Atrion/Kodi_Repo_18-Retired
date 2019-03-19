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

import re,urllib,urlparse,json,datetime
from resources.lib.modules import client
from resources.lib.extensions import metadata
from resources.lib.extensions import tools

class source:
	def __init__(self):
		self.pack = True # Checked by provider.py
		self.priority = 0
		self.language = ['un']
		self.domains = ['abnzb.com']
		self.base_link = 'https://abnzb.com'
		self.search_link = '/api?t=search&q=%s&extended=1&o=json&apikey=%s'
		self.enabled = tools.Settings.getBoolean('accounts.providers.abnzb.enabled')
		self.api = tools.Settings.getString('accounts.providers.abnzb.api')

	def movie(self, imdb, title, localtitle, year):
		try:
			url = {'imdb': imdb, 'title': title, 'year': year}
			url = urllib.urlencode(url)
			return url
		except:
			return

	def tvshow(self, imdb, tvdb, tvshowtitle, localtitle, year):
		try:
			url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'year': year}
			url = urllib.urlencode(url)
			return url
		except:
			return

	def episode(self, url, imdb, tvdb, title, premiered, season, episode):
		try:
			if url == None: return
			url = urlparse.parse_qs(url)
			url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
			url['title'], url['premiered'], url['season'], url['episode'] = title, premiered, season, episode
			url = urllib.urlencode(url)
			return url
		except:
			return

	def sources(self, url, hostDict, hostprDict):
		sources = []
		try:
			if url == None:
				raise Exception()

			if not (self.enabled and self.api and not self.api == ''):
				raise Exception()

			data = urlparse.parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			if 'exact' in data and data['exact']:
				query = title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
				year = None
				season = None
				episode = None
				pack = False
				packCount = None
			else:
				title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
				year = int(data['year']) if 'year' in data and not data['year'] == None else None
				season = int(data['season']) if 'season' in data and not data['season'] == None else None
				episode = int(data['episode']) if 'episode' in data and not data['episode'] == None else None
				pack = data['pack'] if 'pack' in data else False
				packCount = data['packcount'] if 'packcount' in data else None

				if 'tvshowtitle' in data:
					if pack: query = '%s %d' % (title, season)
					else: query = '%s S%02dE%02d' % (title, season, episode)
				else:
					query = '%s %d' % (title, year)
				query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', ' ', query)

			url = self.search_link % (urllib.quote_plus(query), self.api)
			url = urlparse.urljoin(self.base_link, url)

			result = json.loads(client.request(url))
			if 'channel' in result:
				result = result['channel']
				if 'item' in result:
					if isinstance(result['item'], dict):
						result['item'] = [result['item']]
					for item in result['item']:
						jsonName = item['title']
						jsonLink = item['link']
						jsonSize = None
						jsonPassword = False
						jsonAge = None
						if 'attr' in item:
							for attribute in item['attr']:
								if '@attributes' in attribute:
									attribute = attribute['@attributes']
								if 'size' in attribute['name']:
									jsonSize = int(attribute['value'])
								if 'password' in attribute['name']:
									jsonPassword = int(attribute['value'])
								if 'usenetdate' in attribute['name']:
									try:
										jsonAge = attribute['value']
										jsonAge = jsonAge[jsonAge.find(',') + 2 : jsonAge.find(':') - 3]

										# Don't use %b to detect the month, since this is depended on the local settings.
										jsonAge = jsonAge.lower()
										jsonAge = jsonAge.replace('jan', '01').replace('feb', '02').replace('mar', '03').replace('apr', '04').replace('may', '05').replace('jun', '06')
										jsonAge = jsonAge.replace('jul', '07').replace('aug', '08').replace('sep', '09').replace('oct', '10').replace('nov', '11').replace('dec', '12')

										jsonAge = tools.Time.datetime(jsonAge, '%d %m %Y')
										jsonAge = datetime.datetime.today() - jsonAge
										jsonAge = jsonAge.days
									except:
										jsonAge = None

						# Metadata
						meta = metadata.Metadata(name = jsonName, title = title, year = year, season = season, episode = episode, pack = pack, packCount = packCount, link = jsonLink, size = jsonSize, age = jsonAge)

						# Ignore
						if meta.ignore(False) or jsonPassword:
							continue

						# Add
						sources.append({'url' : jsonLink, 'debridonly' : False, 'direct' : False, 'memberonly' : True, 'source' : 'usenet', 'language' : self.language[0], 'quality':  meta.videoQuality(), 'metadata' : meta, 'file' : jsonName})

			return sources
		except:
			return sources

	def resolve(self, url):
		return url
