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

import re,urllib,urlparse,json
from resources.lib.modules import client
from resources.lib.extensions import metadata
from resources.lib.extensions import tools
from resources.lib.extensions import debrid

class source:

	def __init__(self):
		self.pack = False # Checked by provider.py
		self.priority = 0
		self.language = ['un']

		self.domains = ['easynews.com']
		self.base_link = 'http://members.easynews.com'

		# safeO=1: removes adult content
		# u=1: removes duplicates
		self.search_link = '/2.0/search/solr-search/advanced?st=adv&safeO=1&sb=1&from=&ns=&fex=mkv%%2Cmp4%%2Cavi%%2Cmpg%%2Cwebm&vc=&ac=&s1=nsubject&s1d=%%2B&s2=nrfile&s2d=%%2B&s3=dsize&s3d=%%2B&fty[]=VIDEO&spamf=1&u=1&gx=1&pby=3000&pno=1&sS=3&d1=&d1t=&d2=&d2t=&b1=&b1t=11&b2=&b2t=&px1=&px1t=&px2=&px2t=&fps1=&fps1t=&fps2=&fps2t=&bps1=&bps1t=&bps2=&bps2t=&hz1=&hz1t=&hz2=&hz2t=&rn1=&rn1t=&rn2=&rn2t=&gps=%s&sbj=%s'

	def instanceEnabled(self):
		easynews = debrid.EasyNews()
		return easynews.accountEnabled() and easynews.accountValid()

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

			easynews = debrid.EasyNews()

			if not easynews.accountValid():
				raise Exception()

			cookie = easynews.accountCookie()

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
				movie = not 'tvshowtitle' in data
				title = data['title'] if movie else data['tvshowtitle']
				year = int(data['year']) if 'year' in data and not data['year'] == None else None
				season = int(data['season']) if 'season' in data and not data['season'] == None else None
				episode = int(data['episode']) if 'episode' in data and not data['episode'] == None else None

				if movie: query = '%s %d' % (title, year)
				else: query = '%s S%02dE%02d' % (title, season, episode)
				query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', ' ', query)

			query = urllib.quote_plus(query)
			query = self.search_link % (query, query)
			query = urlparse.urljoin(self.base_link, query)

			results = []

			data = client.request(query, cookie = cookie)
			data = json.loads(data)
			results += data['data']

			# EasyNews often does not return all the results on search.
			# Try a second time and combine the results.
			data = client.request(query, cookie = cookie)
			data = json.loads(data)
			results += data['data']

			links = []
			for result in results:
				try:
					jsonName = result['10']

					try: jsonSize = result['rawSize']
					except: jsonSize = result['4']

					jsonExtension = result['2'].replace('.', '')

					try:
						jsonLanguage = tools.Language.code(result['alangs'][0])
						if jsonLanguage == None: raise Exception()
					except:
						jsonLanguage = self.language[0]

					jsonPassword = result['passwd']
					jsonVirus = result['virus']
					jsonDuration = result['14']

					jsonAudio = result['18']
					if not jsonAudio == None: jsonName += ' ' + jsonAudio
					jsonVideo = result['12']
					if not jsonVideo == None: jsonName += ' ' + jsonVideo

					try: jsonWidth = int(result['width'])
					except: jsonWidth = 0
					try: jsonHeight = int(result['height'])
					except: jsonHeight = 0
					if jsonWidth == 0 and jsonHeight == 0: jsonQuality = meta.videoQuality()
					else: jsonQuality = metadata.Metadata.videoResolutionQuality(width = jsonWidth, height = jsonHeight)

					jsonLink = urllib.quote('%s%s/%s%s' % (result['0'], result['11'], result['10'], result['11']))
					jsonLink = '%s/dl/%s|Cookie=%s' % (self.base_link, jsonLink, urllib.quote_plus(cookie))
					jsonLink = jsonLink.encode('utf-8')
					if jsonLink in links:
						continue

					# Metadata
					meta = metadata.Metadata(name = jsonName, title = title, year = year, season = season, episode = episode, link = jsonLink, size = jsonSize, quality = jsonQuality)

					# Ignore
					if meta.ignore(False):
						continue

					if jsonPassword or jsonVirus:
						continue

					if jsonDuration.lower().startswith(('0m', '1m', '2m', '3m', '4m')):
						continue

					# Add
					sources.append({'url' : jsonLink, 'premium' : True, 'debridonly' : False, 'direct' : True, 'memberonly' : True, 'source' : 'EasyNews', 'language' : jsonLanguage, 'quality': meta.videoQuality(), 'metadata' : meta, 'file' : jsonName})
					links.append(jsonLink)

				except:
					pass

			return sources
		except:
			return sources

	def resolve(self, url):
		return url
