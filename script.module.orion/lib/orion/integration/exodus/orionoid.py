# -*- coding: utf-8 -*-

'''
	Orion Addon

	THE BEERWARE LICENSE (Revision 42)
	Orion (orionoid.com) wrote this file. As long as you retain this notice you
	can do whatever you want with this stuff. If we meet some day, and you think
	this stuff is worth it, you can buy me a beer in return.
'''

from orion import *
import urllib
import urlparse
import pkgutil
import base64
import json
import time
import sys
import os
import re
import xbmc
import xbmcvfs
import xbmcaddon

class source:

	TimeDays = 86400

	SizeMegaByte = 1048576
	SizeGigaByte = 1073741824

	SettingNone = 0
	SettingStreamProvider = 1
	SettingStreamHoster = 2
	SettingStreamSeeds = 3
	SettingFileSize = 4
	SettingFilePack = 5
	SettingMetaEdition = 6
	SettingMetaRelease = 7
	SettingMetaUploader = 8
	SettingVideoQuality = 9
	SettingVideoCodec = 10
	SettingVideo3D = 11
	SettingAudioChannels = 12
	SettingAudioSystem = 13
	SettingAudioCodec = 14
	SettingAudioLanguages = 15
	SettingPopularity = 16
	SettingAge = 17

	def __init__(self):
		self.addon = xbmcaddon.Addon('script.module.exoscrapers')
		self.priority = 1
		self.language = ['ab', 'aa', 'af', 'ak', 'sq', 'am', 'ar', 'an', 'hy', 'as', 'av', 'ae', 'ay', 'az', 'bm', 'ba', 'eu', 'be', 'bn', 'bh', 'bi', 'nb', 'bs', 'br', 'bg', 'my', 'ca', 'ch', 'ce', 'ny', 'zh', 'cv', 'kw', 'co', 'cr', 'hr', 'cs', 'da', 'dv', 'nl', 'dz', 'en', 'eo', 'et', 'ee', 'fo', 'fj', 'fi', 'fr', 'ff', 'gd', 'gl', 'lg', 'ka', 'de', 'el', 'gn', 'gu', 'ht', 'ha', 'he', 'hz', 'hi', 'ho', 'hu', 'is', 'io', 'ig', 'id', 'ia', 'ie', 'iu', 'ik', 'ga', 'it', 'ja', 'jv', 'kl', 'kn', 'kr', 'ks', 'kk', 'km', 'ki', 'rw', 'rn', 'kv', 'kg', 'ko', 'ku', 'kj', 'ky', 'lo', 'la', 'lv', 'li', 'ln', 'lt', 'lu', 'lb', 'mk', 'mg', 'ms', 'ml', 'mt', 'gv', 'mi', 'mr', 'mh', 'mn', 'na', 'nv', 'ng', 'ne', 'nd', 'se', 'no', 'ii', 'nn', 'oc', 'oj', 'or', 'om', 'os', 'pi', 'ps', 'fa', 'pl', 'pt', 'pa', 'qu', 'ro', 'rm', 'ru', 'sm', 'sg', 'sa', 'sc', 'sr', 'sn', 'sd', 'si', 'cu', 'sk', 'sl', 'so', 'nr', 'st', 'es', 'su', 'sw', 'ss', 'sv', 'tl', 'ty', 'tg', 'ta', 'tt', 'te', 'th', 'bo', 'ti', 'to', 'ts', 'tn', 'tr', 'tk', 'tw', 'uk', 'ur', 'ug', 'uz', 've', 'vi', 'vo', 'wa', 'cy', 'fy', 'wo', 'xh', 'yi', 'yo', 'za', 'zu']
		self.key = 'VWxOQ1JVbEVZMmRSVTBKSlNVVm5aMVJUUVRSSlJUUm5UbmxDUzBsRlVXZE9VMEpHU1VWSloxUlRRbE5KUmtWblZHbENUVWxFWTJkU2VVSlNTVVJyWjFOcFFraEpSV2RuVkVOQk5VbEZNR2RXUTBKSg=='
		self.domains = ['https://orionoid.com']
		self.providers = []
		self.cachePath = os.path.join(xbmc.translatePath(self.addon.getAddonInfo('profile').decode('utf-8')), 'orion.cache')
		self.cacheData = None
		self.resolvers = None
		try: self.seeds = int(self.addon.getSetting('torrent.min.seeders'))
		except: self.seeds = 1

	def movie(self, imdb, title, localtitle, aliases, year):
		try: return urllib.urlencode({'imdb' : imdb, 'title' : title, 'year' : year})
		except: return None

	def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
		try: return urllib.urlencode({'imdb' : imdb, 'tvdb' : tvdb, 'tvshowtitle' : tvshowtitle, 'year' : year})
		except: return None

	def episode(self, url, imdb, tvdb, title, premiered, season, episode):
		try: return urllib.urlencode({'imdb' : imdb, 'tvdb' : tvdb, 'season' : season, 'episode' : episode})
		except: return None

	def _error(self):
		type, value, traceback = sys.exc_info()
		filename = traceback.tb_frame.f_code.co_filename
		linenumber = traceback.tb_lineno
		name = traceback.tb_frame.f_code.co_name
		errortype = type.__name__
		errormessage = str(errortype) + ' -> ' + str(value.message)
		parameters = [filename, linenumber, name, errormessage]
		parameters = ' | '.join([str(parameter) for parameter in parameters])
		xbmc.log('EXODUS ORION [ERROR]: ' + parameters, xbmc.LOGERROR)

	def _settings(self):
		settings = []
		for i in range(1, 16):
			setting = int(self.addon.getSetting('provider.orionoid.info.' + str(i)))
			if setting > 0: settings.append(setting)
		return settings

	def _cacheSave(self, data):
		self.cacheData = data
		file = xbmcvfs.File(self.cachePath, 'w')
		file.write(json.dumps(data))
		file.close()

	def _cacheLoad(self):
		if self.cacheData == None:
			file = xbmcvfs.File(self.cachePath)
			self.cacheData = json.loads(file.read())
			file.close()
		return self.cacheData

	def _cacheFind(self, url):
		cache = self._cacheLoad()
		for i in cache:
			if i['url'] == url:
				return i
		return None

	def _link(self, data):
		links = data['links']
		for link in links:
			if link.lower().startswith('magnet:'):
				return link
		return links[0]

	def _quality(self, data):
		try:
			quality = data['video']['quality']
			if quality in [Orion.QualityHd8k, Orion.QualityHd6k, Orion.QualityHd4k]:
				return '4K'
			elif quality in [Orion.QualityHd2k]:
				return '1440p'
			elif quality in [Orion.QualityHd1080]:
				return '1080p'
			elif quality in [Orion.QualityHd720]:
				return '720p'
			elif quality in [Orion.QualityScr1080, Orion.QualityScr720, Orion.QualityScr]:
				return 'SCR'
			elif quality in [Orion.QualityCam1080, Orion.QualityCam720, Orion.QualityCam]:
				return 'CAM'
		except: pass
		return 'SD'

	def _language(self, data):
		try:
			language = data['audio']['language']
			if 'en' in language: return 'en'
			return language[0]
		except: return 'en'

	def _source(self, data, label = True):
		if data['stream']['type'] == OrionStream.TypeTorrent:
			return 'Torrent'
		elif label:
			try: hoster = data['stream']['hoster']
			except: hoster = None
			if hoster: return hoster
			try: source = data['stream']['source']
			except: source = None
			return source if source else ''
		else:
			try: return data['stream']['source']
			except: return None

	def _size(self, data):
		size = data['file']['size']
		if size:
			if size < source.SizeGigaByte: return '%d MB' % int(size / float(source.SizeMegaByte))
			else: return '%0.1f GB' % (size / float(source.SizeGigaByte))
		return None

	def _seeds(self, data):
		seeds = data['stream']['seeds']
		if seeds:
			seeds = int(seeds)
			return str(seeds) + ' Seed' + ('' if seeds == 1 else 's')
		return None

	def _days(self, data):
		try: days = (time.time() - data['time']['updated']) / float(source.TimeDays)
		except: days = 0
		days = int(days)
		return str(days) + ' Day' + ('' if days == 1 else 's')

	def _popularity(self, data):
		try: popularity = data['popularity']['percent'] * 100
		except: popularity = 0
		return '+' + str(int(popularity)) + '%'

	def _domain(self, data):
		elements = urlparse.urlparse(self._link(data))
		domain = elements.netloc or elements.path
		domain = domain.split('@')[-1].split(':')[0]
		result = re.search('(?:www\.)?([\w\-]*\.[\w\-]{2,3}(?:\.[\w\-]{2,3})?)$', domain)
		if result: domain = result.group(1)
		return domain.lower()

	def _provider(self, id, create = True):
		if len(self.providers) == 0:
			try:
				path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
				paths = [i[1] for i in os.walk(path)][0]
				for i in paths:
					for loader, name, pkg in pkgutil.walk_packages([os.path.join(path, i)]):
						if pkg: continue
						try:
							name = re.sub(ur'[^\w\d\s]+', '', name.lower())
							module = loader.find_module(name)
							if module: self.providers.append((name, module.load_module(name)))
						except: self._error()
			except: self._error()

		id = id.lower()
		for i in self.providers:
			if id == i[0]: return i[1].source() if create else i[1]
		for i in self.providers:
			if id in i[0] or i[0] in id: return i[1].source() if create else i[1]
		return None

	def _debrid(self, data):
		link = self._link(data)
		for resolver in self.resolvers:
			if resolver.valid_url(url = link, host = None):
				return True
		return False

	def sources(self, url, hostDict, hostprDict):
		sources = []
		try:
			if url == None: raise Exception()
			orion = Orion(base64.b64decode(base64.b64decode(base64.b64decode(self.key))).replace(' ', ''))
			if not orion.userEnabled() or not orion.userValid(): raise Exception()
			settings = self._settings()

			data = urlparse.parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			imdb = data['imdb'] if 'imdb' in data else None
			tmdb = data['tmdb'] if 'tmdb' in data else None
			tvdb = data['tvdb'] if 'tvdb' in data else None

			season = None
			episode = None
			type = Orion.TypeShow if 'tvshowtitle' in data else Orion.TypeMovie
			if type == Orion.TypeShow:
				try:
					season = int(data['season']) if 'season' in data else None
					episode = int(data['episode']) if 'episode' in data else None
				except: pass
				if season == None or season == '': raise Exception()
				if episode == None or episode == '': raise Exception()

			results = orion.streams(
				type = type,
				idImdb = imdb,
				idTmdb = tmdb,
				idTvdb = tvdb,
				numberSeason = season,
				numberEpisode = episode,
				streamType = orion.streamTypes([OrionStream.TypeTorrent, OrionStream.TypeHoster]),
				protocolTorrent = Orion.ProtocolMagnet
			)

			from resources.lib.modules import debrid
			debridResolvers = debrid.debrid_resolvers
			debridProviders = ['premiumize', 'realdebrid', 'alldebrid', 'rpnet', 'megadebrid', 'debridlink', 'zevera', 'smoozed', 'simplydebrid']
			self.resolvers = []
			for debridResolver in debridResolvers:
				try:
					provider = re.sub('[^0-9a-zA-Z]+', '', debridResolver.name.lower())
					if any([i in provider or provider in i for i in debridProviders]):
						self.resolvers.append(debridResolver)
				except: pass

			for data in results:
				try:
					try: seeds = data['stream']['seeds']
					except: seeds = None
					if seeds and self.seeds and seeds < self.seeds: continue

					info = []
					for setting in settings:
						if setting == source.SettingStreamProvider:
							try: info.append(data['stream']['source'])
							except: pass
						elif setting == source.SettingStreamHoster:
							try: info.append(data['stream']['hoster'])
							except: pass
						elif setting == source.SettingStreamSeeds:
							try: info.append(self._seeds(data))
							except: pass
						elif setting == source.SettingFileSize:
							try: info.append(self._size(data))
							except: pass
						elif setting == source.SettingFilePack:
							try: info.append('Pack' if data['file']['pack'] else None)
							except: pass
						elif setting == source.SettingMetaEdition:
							try: info.append(data['meta']['edition'])
							except: pass
						elif setting == source.SettingMetaRelease:
							try: info.append(data['meta']['release'])
							except: pass
						elif setting == source.SettingMetaUploader:
							try: info.append(data['meta']['uploader'])
							except: pass
						elif setting == source.SettingVideoQuality:
							try: info.append(data['video']['quality'].upper())
							except: pass
						elif setting == source.SettingVideoCodec:
							try: info.append(data['video']['codec'].upper())
							except: pass
						elif setting == source.SettingVideo3D:
							try: info.append('3D' if data['video']['3d'] else None)
							except: pass
						elif setting == source.SettingAudioChannels:
							try: info.append('%d CH' % data['audio']['channels'] if data['audio']['channels'] else None)
							except: pass
						elif setting == source.SettingAudioSystem:
							try: info.append(data['audio']['system'].upper())
							except: pass
						elif setting == source.SettingAudioCodec:
							try: info.append(data['audio']['codec'].upper())
							except: pass
						elif setting == source.SettingAudioLanguages:
							try: info.append('-'.join(data['audio']['languages'].upper()))
							except: pass
						elif setting == source.SettingPopularity:
							try: info.append(self._popularity(data))
							except: pass
						elif setting == source.SettingAge:
							try: info.append(self._days(data))
							except: pass
					info = [i for i in info if i]

					orion = {}
					try: orion['stream'] = data['id']
					except: pass
					try: orion['item'] = data
					except: pass

					sources.append({
						'orion' : orion,
						'provider' : self._source(data, False),
						'source' : self._source(data, True),
						'quality' : self._quality(data),
						'language' : self._language(data),
						'url' : self._link(data),
						'info' : ' | '.join(info) if len(info) > 0 else None,
						'direct' : data['access']['direct'],
						'debridonly' : self._debrid(data)
					})
				except: self._error()
		except: self._error()
		self._cacheSave(sources)
		return sources

	def resolve(self, url):
		item = self._cacheFind(url)
		try:
			provider = self._provider(item['provider'], True)
			if provider: url = provider.resolve(url)
		except: self._error()
		return url
