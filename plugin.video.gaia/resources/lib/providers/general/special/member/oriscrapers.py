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

import copy
import threading

from resources.lib import debrid
from resources.lib.extensions import provider
from resources.lib.extensions import metadata
from resources.lib.extensions import tools
from resources.lib.extensions import network
from resources.lib.extensions import orionoid

class source(provider.ProviderBase):

	def __init__(self):
		provider.ProviderBase.__init__(self, supportMovies = True, supportShows = True)

		self.orion = orionoid.Orionoid()

		self.pack = False # Checked by provider.py
		self.priority = 0
		self.language = ['un']

		self.base_link = self.orion.link()
		self.domains = [network.Networker.linkDomain(self.base_link)]

		enabledPremiumize = debrid.premiumize.Core().accountValid() and (tools.Settings.getBoolean('streaming.torrent.premiumize.enabled') or tools.Settings.getBoolean('streaming.usenet.premiumize.enabled'))
		enabledOffCloud = debrid.offcloud.Core().accountValid() and (tools.Settings.getBoolean('streaming.torrent.offcloud.enabled') or tools.Settings.getBoolean('streaming.usenet.offcloud.enabled'))
		enabledRealDebrid = debrid.realdebrid.Core().accountValid() and tools.Settings.getBoolean('streaming.torrent.realdebrid.enabled')
		self.cache = tools.Settings.getBoolean('scraping.cache.enabled') and ((enabledPremiumize and tools.Settings.getBoolean('scraping.cache.premiumize')) or (enabledOffCloud and tools.Settings.getBoolean('scraping.cache.offcloud')) or (enabledRealDebrid and tools.Settings.getBoolean('scraping.cache.realdebrid')))

	def instanceEnabled(self):
		# Do not check if accountValid(), since the account status might not have been updated in a while.
		# Just check if an API key exists and if invalid, the API request will return an error.
		return self.orion.accountEnabled()

	# Called by verification.py
	# Do not waste user's links when doing a verification.
	def verify(self):
		return self.orion.serverTest()

	def silent(self, silent = True):
		self.orion = orionoid.Orionoid(silent = silent)

	def _streams(self, streams, item, metabase):
		for stream in streams:
			try:
				links = stream['links']
				try: link = links[0]
				except: continue

				# Copying the object is a lot faster than creating a new one every time.
				meta = copy.deepcopy(metabase)

				try: meta.setOrion(True)
				except: pass
				try: meta.setPopularity(stream['popularity']['percent'])
				except: pass
				try: meta.setLink(link)
				except: pass

				try:
					if stream['stream']['seeds'] > 0: meta.setSeeds(stream['stream']['seeds'])
				except: pass

				try:
					if stream['stream']['type'] == orionoid.Orionoid.StreamUsenet and stream['stream']['time'] and stream['stream']['time'] >= 0:
						age = stream['stream']['time']
					else:
						age = stream['time']['updated']
					meta.setAge(int(round(max(1, tools.Time.timestamp() - age) / 86400)))
				except: pass

				try: meta.setName(stream['file']['name'])
				except: pass
				try: meta.setSize(stream['file']['size'])
				except: pass
				try: meta.setPack(stream['file']['pack'])
				except: pass

				try: meta.setRelease(stream['meta']['release'])
				except: pass
				try: meta.setUploader(stream['meta']['uploader'])
				except: pass
				try: meta.setEdition(stream['meta']['edition'])
				except: pass

				try: meta.setVideoQuality(stream['video']['quality'])
				except: pass
				try: meta.setVideoCodec(stream['video']['codec'])
				except: pass
				try: meta.setVideo3D(stream['video']['3d'])
				except: pass

				try:
					if stream['audio']['type'] == orionoid.Orionoid.AudioDubbed: meta.setAudioDubbed()
				except: pass
				try: meta.setAudioChannels(stream['audio']['channels'])
				except: pass
				try: meta.setAudioSystem(stream['audio']['system'])
				except: pass
				try: meta.setAudioCodec(stream['audio']['codec'])
				except: pass
				try: meta.setAudioLanguages(stream['audio']['languages'])
				except: pass

				try:
					if stream['subtitle']['type'] == orionoid.Orionoid.SubtitleSoft: meta.setSubtitlesSoft()
				except: pass
				try:
					if stream['subtitle']['type'] == orionoid.Orionoid.SubtitleHard: meta.setSubtitlesHard()
				except: pass

				try: reference = stream['stream']['reference']
				except: reference = None

				try: direct = stream['access']['direct']
				except: direct = False
				meta.setDirect(direct)

				# Only set the cache status if cache inspection is disabled.
				# If cache inspection is enabled, do not use the old/inaccurate values from Orion.
				cache = {}
				if not self.cache:
					try: cache['premiumize'] = stream['access']['premiumize']
					except: pass
					try: cache['offcloud'] = stream['access']['offcloud']
					except: pass
					try: cache['realdebrid'] = stream['access']['realdebrid']
					except: pass
					try: meta.setType(stream['stream']['type'])
					except: pass

				try:
					if stream['stream']['type'] == orionoid.Orionoid.StreamHoster:
						if stream['stream']['hoster']:
							source = stream['stream']['hoster']
						else:
							source = network.Networker.linkDomain(link, subdomain = False, ip = False).lower()
							if source:
								if 'gvideo' in source or ('google' in source and 'vid' in source) or ('google' in source and 'link' in source):
									source = 'GoogleVideo'
								elif 'google' in source and ('usercontent' in source or 'cloud' in source):
									source = 'GoogleCloud'
								elif 'google' in source and 'doc' in source:
									source = 'GoogleDocs'
								elif 'google' in source and 'drive' in source:
									source = 'GoogleDrive'
					else:
						source = stream['stream']['type']
				except: source = None
				if not source: source = ''
				try: provider = stream['stream']['source']
				except: provider = None

				try: origin = stream['stream']['origin']
				except: origin = None

				try: language = stream['audio']['languages'][0]
				except: language = None

				try: quality = stream['video']['quality']
				except: quality = None

				try: filename = stream['file']['name']
				except: filename = None

				try: hash = stream['file']['hash']
				except: hash = None

				orion = {
					'item' : item,
					'stream' : stream['id'],
				}

				self.tSources.append({'orion' : orion, 'url' : link, 'links' : links, 'direct' : direct, 'cache' : cache, 'origin' : origin, 'source' : source, 'provider' : provider, 'hash' : hash, 'language' : language, 'quality': quality, 'file' : filename, 'metadata' : meta, 'pack' : meta.pack(), 'external' : True})
			except:
				tools.Logger.error()

	def sources(self, url, hostDict, hostprDict):
		self.tSources = []
		try:
			if url == None: raise Exception()
			if not self.orion.accountEnabled(): raise Exception()

			data = self._decode(url)

			type = orionoid.Orionoid.TypeShow if 'tvshowtitle' in data else orionoid.Orionoid.TypeMovie
			imdb = data['imdb'] if 'imdb' in data else None
			if 'exact' in data and data['exact']:
				query = data['tvshowtitle'] if type == orionoid.Orionoid.TypeShow else data['title']
				title = None
				year = None
				season = None
				episode = None
			else:
				query = None
				title = data['tvshowtitle'] if type == orionoid.Orionoid.TypeShow else data['title']
				year = int(data['year']) if 'year' in data and not data['year'] == None else None
				season = int(data['season']) if 'season' in data and not data['season'] == None else None
				episode = int(data['episode']) if 'episode' in data and not data['episode'] == None else None

			if not self._query(query, imdb, season, episode): return self.tSources
			streams = self.orion.streamRetrieve(type = type, query = query, imdb = imdb, title = title, year = year, season = season, episode = episode)
			if not streams: return self.tSources

			if type == orionoid.Orionoid.TypeMovie:
				item = streams['movie']['id']['orion']
			elif type == orionoid.Orionoid.TypeShow:
				item = streams['episode']['id']['orion']

			threads = []
			threadsCount = tools.Hardware.processors()

			streams = streams['streams']
			chunk = int(len(streams) / float(threadsCount))
			streams = [streams[i:i + threadsCount] for i in xrange(0, len(streams), threadsCount)]

			metabase = metadata.Metadata()
			for stream in streams:
				thread = threading.Thread(target  =self._streams, args = (stream, item, metabase))
				threads.append(thread)
				thread.start()
			[thread.join() for thread in threads]
		except:
			tools.Logger.error()

		return self.tSources
