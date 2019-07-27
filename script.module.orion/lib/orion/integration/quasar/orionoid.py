# -*- coding: utf-8 -*-

'''
	Orion Addon

	THE BEERWARE LICENSE (Revision 42)
	Orion (orionoid.com) wrote this file. As long as you retain this notice you
	can do whatever you want with this stuff. If we meet some day, and you think
	this stuff is worth it, you can buy me a beer in return.
'''

from burst import burst
from burst.utils import Magnet
from orion import *
from orion.modules.oriontools import *
from orion.modules.orioninterface import *

class Orionoid:

	Id = 'orion'
	Name = Orion.Name
	Key = 'VVdsQ1JrbEZNR2RSZVVKU1NVVnZaMUZwUWxGSlJsRm5Wa05DUkVsRVRXZFZRMEpKU1VWeloxWnBRa2xKUmtWblZVTkNURWxGU1dkUmFVSkRTVVZ6WjFKVFFUVkpSVWxuVDFOQ1RVbEZOR2RSVTBKRw=='

	SizeMegaByte = 1048576
	SizeGigaByte = 1073741824

	@classmethod
	def _error(self):
		OrionTools.error('QUASAR ORION ERROR')

	@classmethod
	def _link(self, data):
		result = None
		links = data['links']
		for link in links:
			if link.lower().startswith('magnet:'):
				result = link
				break
		if not result: result = links[0]
		if result and result.lower().startswith('magnet'):
			# For some reason, some magnets have UTF characters in their hash. Ignore them.
			hash = Magnet(result).info_hash
			if not hash: return None
		return result.encode('utf-8')

	@classmethod
	def _quality(self, data):
		try:
			quality = data['video']['quality']
			if quality in [Orion.QualityHd8k, Orion.QualityHd6k, Orion.QualityHd4k]:
				return 'filter_4k'
			elif quality in [Orion.QualityHd2k]:
				return 'filter_2k'
			elif quality in [Orion.QualityHd1080]:
				return 'filter_1080p'
			elif quality in [Orion.QualityHd720]:
				return 'filter_720p'
			elif quality in [Orion.QualityScr1080, Orion.QualityScr720, Orion.QualityScr]:
				return 'filter_240p'
			elif quality in [Orion.QualityCam1080, Orion.QualityCam720, Orion.QualityCam]:
				return 'filter_240p'
		except: pass
		return 'filter_480p'

	@classmethod
	def _qualityIndex(self, data):
		qualities = ['filter_240p', 'filter_480p', 'filter_720p', 'filter_1080p', 'filter_2k', 'filter_4k']
		quality = self._quality(data)
		return qualities.index(quality) + 1

	@classmethod
	def _seeds(self, data):
		try: seeds = data['stream']['seeds']
		except: seeds  = None
		return seeds if seeds else 0

	@classmethod
	def _name(self, data):
		try: name = data['file']['name']
		except: name = None
		name = (name + ' ') if name else ''
		quality = self._quality(data).replace('filter_', '')
		name += '[%s]' % quality # Otherwise Quasar incorrectly detects the quality.
		return name

	@classmethod
	def _hash(self, data):
		try: hash = data['file']['hash']
		except: hash = None
		return hash if hash else ''

	@classmethod
	def _size(self, data):
		try:
			size = data['file']['size']
			if size:
				if size < Orionoid.SizeGigaByte: return '%d MB' % int(size / float(Orionoid.SizeMegaByte))
				else: return '%0.1f GB' % (size / float(Orionoid.SizeGigaByte))
		except: pass
		return ''

	@classmethod
	def _language(self, data):
		try: return data['audio']['languages'][0]
		except: return 'en'

	@classmethod
	def _provider(self, data):
		provider = OrionInterface.fontColor(Orionoid.Name, OrionInterface.ColorPrimary)
		try: provider += ' - ' + OrionInterface.fontColor(data['stream']['source'].capitalize(), OrionInterface.ColorQuaternary)
		except: pass
		return provider

	@classmethod
	def limit(self):
		return 100000

	@classmethod
	def streams(self, filtering):
		try:
			addon = OrionTools.addon('script.quasar.burst')
			if addon.getSetting('orion') == 'true':
				if burst.timeout < 60: burst.timeout = 60
				icon = OrionTools.pathJoin(addon.getAddonInfo('path').decode('utf-8'), 'burst', 'providers', 'icons', '%s.png' % Orionoid.Id)

				try: idImdb = filtering.info['imdb_id']
				except: idImdb = None
				try: idTmdb = filtering.info['tmdb_id']
				except: idTmdb = None
				try: idTvdb = filtering.info['tvdb_id']
				except: idTvdb = None

				try: numberSeason = filtering.info['season']
				except: numberSeason = None
				try: numberEpisode = filtering.info['episode']
				except: numberEpisode = None

				orion = Orion(OrionTools.base64From(OrionTools.base64From(OrionTools.base64From(Orionoid.Key))).replace(' ', ''))
				streams = orion.streams(
					type = Orion.TypeMovie if numberSeason is None else Orion.TypeShow,
					idImdb = idImdb,
					idTmdb = idTmdb,
					idTvdb = idTvdb,
					numberSeason = numberSeason,
					numberEpisode = numberEpisode,
					streamType = Orion.StreamTorrent,
					filePack = Orion.ChoiceRequire if numberSeason is not None and numberEpisode is None else Orion.ChoiceInclude
				)

				results = []
				for data in streams:
					link = self._link(data)
					if not link: continue
					seeds = self._seeds(data)
					sortResolution = self._qualityIndex(data)
					sortBalance = seeds * 3 * sortResolution
					results.append({
						'name' : self._name(data),
						'uri' : link,
						'info_hash' : self._hash(data),
						'size' : self._size(data),
						'seeds' : seeds,
						'peers' : seeds,
						'language' : self._language(data),
						'provider' : self._provider(data),
						'icon' : icon,
						'sort_resolution': sortResolution,
						'sort_balance': sortBalance,
					})

				filtering.results.extend(results)
				return filtering.results
		except:
			self._error()
		return None
