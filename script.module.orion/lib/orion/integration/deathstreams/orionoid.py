# -*- coding: utf-8 -*-

'''
	Orion Addon

	THE BEERWARE LICENSE (Revision 42)
	Orion (orionoid.com) wrote this file. As long as you retain this notice you
	can do whatever you want with this stuff. If we meet some day, and you think
	this stuff is worth it, you can buy me a beer in return.
'''

from orion import *
import urlparse
import base64
import time
import sys
import re
import xbmc
import kodi
import scraper
from deaths_lib import scraper_utils
from deaths_lib.constants import VIDEO_TYPES
from deaths_lib.constants import QUALITIES
from deaths_lib.constants import HOST_Q

BASE_URL = 'https://orionoid.com'

class Scraper(scraper.Scraper):
	base_url = BASE_URL

	def __init__(self, timeout = scraper.DEFAULT_TIMEOUT):
		self.base_url = kodi.get_setting('%s-base_url' % (self.get_name()))
		self.key = 'VkVOQ1VVbEdWV2RVYVVKSFNVWmpaMUpwUWtKSlJXTm5VbWxDVFVsRmQyZFNRMEpQU1VaUlowMTVRazlKUlVsblRubENTMGxHU1dkT2VVSkNTVVZWWjFSRFFYcEpSVzluVmtOQ1NFbEZaMmRQVTBKTw=='
		self.hosts = self._hosts()

	@classmethod
	def provides(self):
		return frozenset([VIDEO_TYPES.MOVIE, VIDEO_TYPES.TVSHOW, VIDEO_TYPES.EPISODE])

	@classmethod
	def get_name(self):
		return 'Orion'

	@classmethod
	def _hosts(self):
		hosts = []
		for key, value in HOST_Q.iteritems():
			hosts.extend(value)
		hosts = [i.lower() for i in hosts]
		return hosts

	def _error(self):
		type, value, traceback = sys.exc_info()
		filename = traceback.tb_frame.f_code.co_filename
		linenumber = traceback.tb_lineno
		name = traceback.tb_frame.f_code.co_name
		errortype = type.__name__
		errormessage = str(errortype) + ' -> ' + str(value.message)
		parameters = [filename, linenumber, name, errormessage]
		parameters = ' | '.join([str(parameter) for parameter in parameters])
		xbmc.log('DEATH STREAMS ORION [ERROR]: ' + parameters, xbmc.LOGERROR)

	def _link(self, data):
		links = data['links']
		for link in links:
			if link.lower().startswith('magnet:'):
				return link
		return links[0]

	def _quality(self, data):
		try:
			quality = data['video']['quality']
			if quality in [Orion.QualityHd8k, Orion.QualityHd6k, Orion.QualityHd4k, Orion.QualityHd2k]:
				return QUALITIES.HD4K
			elif quality in [Orion.QualityHd1080]:
				return QUALITIES.HD1080
			elif quality in [Orion.QualityHd720]:
				return QUALITIES.HD720
			elif quality in [Orion.QualityScr1080, Orion.QualityScr720, Orion.QualityScr]:
				return QUALITIES.MEDIUM
			elif quality in [Orion.QualityCam1080, Orion.QualityCam720, Orion.QualityCam]:
				return QUALITIES.LOW
		except: pass
		return QUALITIES.HIGH

	def _language(self, data):
		try:
			language = data['audio']['language']
			if 'en' in language: return 'en'
			return language[0]
		except: return 'en'

	def _source(self, data, label = True):
		if label:
			try: hoster = data['stream']['hoster']
			except: hoster = None
			if hoster: return hoster
			try: source = data['stream']['source']
			except: source = None
			return source if source else ''
		else:
			try: return data['stream']['source']
			except: return None

	def _days(self, data):
		try: days = (time.time() - data['time']['updated']) / 86400.0
		except: days = 0
		days = int(days)
		return str(days) + ' Day' + ('' if days == 1 else 's')

	def _popularity(self, data, percent = True):
		if percent:
			try: return data['popularity']['percent'] * 100
			except: return None
		else:
			try: return data['popularity']['count']
			except: return None

	def _domain(self, data):
		elements = urlparse.urlparse(self._link(data))
		domain = elements.netloc or elements.path
		domain = domain.split('@')[-1].split(':')[0]
		result = re.search('(?:www\.)?([\w\-]*\.[\w\-]{2,3}(?:\.[\w\-]{2,3})?)$', domain)
		if result: domain = result.group(1)
		return domain.lower()

	def _valid(self, data):
		if data['access']['direct']:
			return True
		else:
			domain = self._domain(data)
			for host in self.hosts:
				if domain.startswith(host) or host.startswith(domain):
					return True
			import resolveurl
			return resolveurl.HostedMediaFile(self._link(data)).valid_url()

	def get_sources(self, video):
		sources = []
		try:
			orion = Orion(base64.b64decode(base64.b64decode(base64.b64decode(self.key))).replace(' ', ''))
			if not orion.userEnabled() or not orion.userValid(): raise Exception()

			query = ''
			type = None
			if video.video_type == VIDEO_TYPES.MOVIE:
				type = Orion.TypeMovie
				query = '%s %s' % (str(video.title), str(video.year))
			else:
				type = Orion.TypeShow
				query = '%s S%sE%s' % (str(video.title), str(video.season), str(video.episode))

			results = orion.streams(
				type = type,
				query = query,
				streamType = Orion.StreamHoster
			)

			for data in results:
				try:
					if self._valid(data):
						orion = {}
						try: orion['stream'] = data['id']
						except: pass
						try: orion['item'] = data
						except: pass

						stream = {
							'orion' : orion,
							'class' : self,
							'multi-part' : False,
							'host' : self._source(data, True),
							'quality' : self._quality(data),
							'language' : self._language(data),
							'url' : self._link(data),
							'views' : self._popularity(data, False),
							'rating' : int(self._popularity(data, True)),
							'direct' : data['access']['direct'],
						}

						if data['video']['codec']:
							stream['format'] = data['video']['codec']

						if data['file']['size']:
							stream['size'] = scraper_utils.format_size(data['file']['size'])

						if data['video']['3d']:
							stream['3D'] = data['video']['3d']

						if data['subtitle']['languages'] and len(data['subtitle']['languages']) > 0:
							stream['subs'] = '-'.join(data['subtitle']['languages']).upper()

						sources.append(stream)
				except: self._error()
		except: self._error()
		return sources

	def search(self, video_type, title, year, season = ''):
		raise NotImplementedError
