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

import os
import re
import sys
import urlparse
import datetime
from resources.lib.modules import client
from resources.lib.extensions import provider
from resources.lib.extensions import tools
from resources.lib.extensions import metadata
from resources.lib.extensions import network

class NewzNab(provider.ProviderBase):

	TypeMovie = 'movie'
	TypeShow = 'tvsearch'
	TypeSearch = 'search'
	TypeDownload = 'get'

	ParameterKey = 'apikey'
	ParameterType = 't'
	ParameterOutput = 'o'
	ParameterId = 'id'
	ParameterQuery = 'q'
	ParameterImdb = 'imdbid'
	ParameterTvdb = 'tvdbid'
	ParameterSeason = 'season'
	ParameterEpisode = 'ep'

	# String length of GUIDs.
	# Sort descending in order to always try longer string first.
	IdLengths = (40, 32)

	def __init__(self, id, link, domains = []):
		provider.ProviderBase.__init__(self, supportMovies = True, supportShows = True)

		self.domains = [domain.lower() for domain in domains]
		domain = network.Networker.linkDomain(link, subdomain = False, topdomain = True).lower()
		if not domain in self.domains: self.domains.insert(0, domain)

		self.base_link = link
		self.api_link = '/api'

		self.pack = True
		self.priority = 0
		self.language = ['un']

		self.api = tools.Settings.getString('accounts.providers.%s.api' % id)
		self.enabled = tools.Settings.getBoolean('accounts.providers.%s.enabled' % id) and self.api

	def authenticationAdd(self, links):
		return self._authentication(links = links, key = True)

	def authenticationRemove(self, links):
		return self._authentication(links = links, key = False)

	def _authentication(self, links, key):
		result = []
		multiple = isinstance(links, (list, tuple))
		if not multiple: links = [links]
		for i in range(len(links)):
			if self._linkValid(links[i]): # If authenticationAdd sends in links that are not from the providers domain (eg: Orion links).
				if self.enabled: result.append(self._link(NewzNab.TypeDownload, key = key, id = links[i])) # Remove links if there is no API key.
			else:
				result.append(links[i])
		if multiple: return result
		elif len(result) > 0: return result[0]
		else: return None

	def _id(self, link):
		try:
			parameters = urlparse.parse_qs(urlparse.urlparse(link).query)
			if parameters[NewzNab.ParameterType] == NewzNab.TypeDownload:
				return parameters[NewzNab.ParameterId]
		except: pass
		for length in NewzNab.IdLengths:
			try: return re.search('^.*\/([a-zA-Z0-9]{%d,}).*$' % length, link).group(1) # In case API key has the same length and can be confused with the ID.
			except: pass
		for length in NewzNab.IdLengths:
			try: return re.search('^.*([a-zA-Z0-9]{%d,}).*$' % length, link).group(1)
			except: pass
		return None

	def _link(self, type, key = True, id = None, query = None, imdb = None, tvdb = None, season = None, episode = None):
		# Always use the same order of parameters to ensure the link is always exactly the same. Required for Orion.
		parameters = []
		if key: parameters.append([NewzNab.ParameterKey, self.api])
		if not type == NewzNab.TypeDownload: parameters.append([NewzNab.ParameterOutput, 'json'])
		parameters.append([NewzNab.ParameterType, type])
		if not id is None: parameters.append([NewzNab.ParameterId, self._id(id)])
		if not query is None: parameters.append([NewzNab.ParameterQuery, query])
		if not tvdb is None: parameters.append([NewzNab.ParameterTvdb, tvdb])
		elif not imdb is None: parameters.append([NewzNab.ParameterImdb, imdb.replace('tt', '')]) # Do not attach an IMDb ID if there is already one for TVDb, otherwise no results are returned.
		if not season is None: parameters.append([NewzNab.ParameterSeason, season])
		if not episode is None: parameters.append([NewzNab.ParameterEpisode, episode])

		parameters = ['%s=%s' % (str(i[0]), str(i[1])) for i in parameters]
		parameters = '&'.join(parameters)
		return self.base_link + self.api_link + '?' + parameters

	def _linkValid(self, link):
		domain = network.Networker.linkDomain(link, subdomain = False, topdomain = True).lower()
		return domain in self.domains

	@classmethod
	def _extract(self, item, name):
		try:
			try: attributes = item['newznab:attr']
			except: attributes = item['attr']
			for attribute in attributes:
				try: attribute = attribute['@attributes']
				except: pass
				try: attributeName = attribute['name']
				except: attributeName = attribute['_name']
				if attributeName == name:
					try: return attribute['value']
					except: return attribute['_value']
		except:
			return None

	def sources(self, url, hostDict, hostprDict):
		sources = []
		try:
			if not url == None and self.enabled:
				ignoreContains = None
				data = self._decode(url)

				show = 'tvshowtitle' in data
				title = data['tvshowtitle'] if show else data['title']

				if 'exact' in data and data['exact']:
					titles = None
					year = None
					season = None
					episode = None
					pack = False
					packCount = None
					link = self._link(type = NewzNab.TypeSearch, query = title)
				else:
					titles = data['alternatives'] if 'alternatives' in data else None
					year = int(data['year']) if 'year' in data and not data['year'] is None else None
					season = int(data['season']) if show and 'season' in data and not data['season'] is None else None
					episode = int(data['episode']) if show and 'episode' in data and not data['episode'] is None else None
					imdb = data['imdb'] if 'imdb' in data else None
					tvdb = data['tvdb'] if 'tvdb' in data else None
					pack = data['pack'] if 'pack' in data else False
					packCount = data['packcount'] if 'packcount' in data else None
					if show:
						# Search special episodes by name. All special episodes are added to season 0 by Trakt and TVDb. Hence, do not search by filename (eg: S02E00), since the season is not known.
						if (season == 0 or episode == 0) and ('title' in data and not data['title'] == None and not data['title'] == ''):
							title = '%s %s' % (data['tvshowtitle'], data['title']) # Change the title for metadata filtering.
							link = self._link(type = NewzNab.TypeShow, query = title)
							ignoreContains = len(data['title']) / float(len(title)) # Increase the required ignore ration, since otherwise individual episodes and season packs are found as well.
						else:
							if pack: link = self._link(type = NewzNab.TypeShow, query = '%s %d' % (title, season)) # Do not use geenral search, but TV search instead.
							else: link = self._link(type = NewzNab.TypeShow, imdb = imdb, tvdb = tvdb, season = season, episode = episode)
					else:
						link = self._link(type = NewzNab.TypeMovie, imdb = imdb)

				if not self._query(link): return sources

				data = client.request(link, ignoreErrors = 429)
				try:
					result = tools.Converter.jsonFrom(data)
					try: result = result['item']
					except: result = result['channel']['item']
					if isinstance(result, dict): result = [result]
				except:

					if data:
						data = data.lower() # Returned as XML.
						provider = os.path.splitext(os.path.basename(sys.modules[self.__module__].__file__))[0].upper()
						if any(i in data for i in ['code="429"', 'code="500"', 'code="501"', 'limit reached']): tools.Logger.log(provider + ' API Limit Reached')
						elif any(i in data for i in ['upgrade to']): tools.Logger.log(provider + ' Premium Account Required') # Also error 100.
						elif any(i in data for i in ['code="100"', 'incorrect user credentials']): tools.Logger.log(provider + ' Invalid User Credentials')
						else: tools.Logger.error()
					return sources

				for item in result:
					try:
						# Name
						jsonName = item['title']

						# Link
						# Do not use the default item['link'], since it is a non-API link requiring the user ID besides the user API key.
						try: jsonLink = item['guid']['text']
						except:
							try: jsonLink = item['guid']
							except: jsonLink = self._extract(item, 'guid')
						if jsonLink == None: jsonLink = item['link']
						jsonLink = self._link(type = NewzNab.TypeDownload, id = jsonLink)

						# Age
						try: jsonAge = item['pubDate']
						except:
							try: jsonAge = item['usenetdate']
							except:
								jsonAge = self._extract(item, 'pubDate')
								if not jsonAge: jsonAge = self._extract(item, 'usenetdate')
						try:
							jsonAge = re.search('^(.*?)\s?[+-]?\d{4}$', jsonAge).group(1) # The timezone (%z) is not always supported.
							jsonAge = tools.Time.datetime(jsonAge, '%a, %d %b %Y %H:%M:%S')
							jsonAge = (datetime.datetime.today() - jsonAge).days
						except:
							jsonAge = None

						# Size
						jsonSize = int(self._extract(item, 'size'))

						# Metadata
						meta = metadata.Metadata(name = jsonName, title = title, titles = titles, year = year, season = season, episode = episode, pack = pack, packCount = packCount, link = jsonLink, size = jsonSize, age = jsonAge)

						# Ignore
						meta.ignoreAdjust(contains = ignoreContains)
						if meta.ignore(True): continue

						# Add
						sources.append({'url' : jsonLink, 'debridonly' : False, 'direct' : False, 'memberonly' : True, 'source' : 'usenet', 'language' : self.language[0], 'quality': meta.videoQuality(), 'metadata' : meta, 'file' : jsonName})
					except:
						tools.Logger.error()
		except:
			tools.Logger.error()
		return sources
