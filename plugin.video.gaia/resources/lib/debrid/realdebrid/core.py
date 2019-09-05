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

import urllib
import urllib2
import threading

from resources.lib.debrid import base
from resources.lib.extensions import convert
from resources.lib.extensions import cache
from resources.lib.extensions import tools
from resources.lib.extensions import interface
from resources.lib.extensions import network
from resources.lib.extensions import metadata

class Core(base.Core):

	Id = 'realdebrid'
	Name = 'RealDebrid'
	Abbreviation = 'R'
	Priority = 3

	# Service Statuses
	ServiceStatusUp = 'up'
	ServiceStatusDown = 'down'
	ServiceStatusUnsupported = 'unsupported'

	ServicesUpdate = None
	ServicesTorrent = [
		{	'name' : 'Torrent',		'id' : 'torrent',	'domain' : '',	'status' : ServiceStatusUp,	'supported' : True	},
	]

	#Links
	LinkMain = 'https://real-debrid.com'
	LinkApi = 'https://api.real-debrid.com/rest/1.0'
	LinkAuthentication = 'https://api.real-debrid.com/oauth/v2'

	# Modes
	ModeGet = 'get'
	ModePost = 'post'
	ModePut = 'put'
	ModeDelete = 'delete'

	# Types
	TypeTorrent = 'torrent'

	# Statuses
	StatusUnknown = 'unknown'
	StatusError = 'error'
	StatusMagnetError = 'magnet_error'
	StatusMagnetConversion = 'magnet_conversion'
	StatusFileSelection = 'waiting_files_selection'
	StatusQueued = 'queued'
	StatusBusy = 'downloading'
	StatusFinished = 'downloaded'
	StatusVirus = 'virus'
	StatusCompressing = 'compressing'
	StatusUploading = 'uploading'
	StatusDead = 'dead'

	# Categories
	CategoryUser = 'user'
	CategoryHosts = 'hosts'
	CategoryToken = 'token'
	CategoryDevice = 'device'
	CategoryUnrestrict = 'unrestrict'
	CategoryTorrents = 'torrents'
	CategoryTime = 'time'

	# Actions
	ActionStatus = 'status'
	ActionCode = 'code'
	ActionCredentials = 'credentials'
	ActionLink = 'link'
	ActionAddTorrent = 'addTorrent'
	ActionAddMagnet = 'addMagnet'
	ActionActive = 'activeCount'
	ActionInfo = 'info'
	ActionAvailableHosts = 'availableHosts'
	ActionSelectFiles = 'selectFiles'
	ActionDelete = 'delete'
	ActionInstantAvailability = 'instantAvailability'
	ActionDomains = 'domains'

	# Parameters
	ParameterClientId = 'client_id'
	ParameterClientSecret = 'client_secret'
	ParameterCode = 'code'
	ParameterGrantType = 'grant_type'
	ParameterNewCredentials = 'new_credentials'
	ParameterLink = 'link'
	ParameterMagnet = 'magnet'
	ParameterFiles = 'files'

	# Errors
	ErrorUnknown = 'unknown'
	ErrorInaccessible = 'inaccessible' # Eg: 404 error.
	ErrorUnavailable = 'unavailable' # When season pack does not contain a certain episode. Or if there is not usable file in the download.
	ErrorRealDebrid = 'realdebrid' # Error from RealDebrid server.
	ErrorBlocked = 'blocked' # User IP address blocked.
	ErrorSelection = 'selection' # No file selected from list of items.

	# Selection
	SelectionAll = 'all'
	SelectionName = 'name'
	SelectionLargest = 'largest'

	# Limits
	LimitLink = 2000 # Maximum length of a URL.
	LimitHashesGet = 40 # Maximum number of 40-character hashes to use in GET parameter so that the URL length limit is not exceeded.

	# Time
	TimeOffset = None

	# User Agent
	UserAgent = tools.System.name() + ' ' + tools.System.version()

	# Client
	ClientId = tools.System.obfuscate(tools.Settings.getString('internal.realdebrid.client', raw = True))
	ClientGrant = 'http://oauth.net/grant_type/device/1.0'

	# Authentication
	AuthenticationToken = None
	AuthenticationLock = None

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, debug = True):
		base.Core.__init__(self, Core.Id, Core.Name)

		self._accountAuthenticationClear()
		self.mAuthenticationToken = self.accountToken()

		self.mDebug = debug
		self.mLinkBasic = None
		self.mLinkFull = None
		self.mParameters = None
		self.mSuccess = None
		self.mError = None
		self.mErrorCode = None
		self.mErrorDescription = None
		self.mResult = None
		self.mLock = None

	##############################################################################
	# INTERNAL
	##############################################################################

	def _request(self, mode, link, parameters = None, httpTimeout = None, httpData = None, httpHeaders = None, httpAuthenticate = True):
		self.mResult = None

		linkOriginal = link
		parametersOriginal = parameters
		httpDataOriginal = httpData

		def redo(mode, link, parameters, httpTimeout, httpData, httpHeaders, httpAuthenticate):
			if httpAuthenticate:
				if self._accountAuthentication():
					httpHeaders['Authorization'] = 'Bearer %s' % self.mAuthenticationToken # Update token in headers.
					return self._request(mode = mode, link = link, parameters = parameters, httpTimeout = httpTimeout, httpData = httpData, httpHeaders = httpHeaders, httpAuthenticate = False)
			return None

		try:
			if not httpTimeout:
				if httpData: httpTimeout = 60
				else: httpTimeout = 30

			self.mLinkBasic = link
			self.mParameters = parameters
			self.mSuccess = None
			self.mError = None
			self.mErrorCode = None
			self.mErrorDescription = None

			if mode == Core.ModeGet or mode == Core.ModePut or mode == Core.ModeDelete:
				if parameters:
					if not link.endswith('?'):
						link += '?'
					parameters = urllib.urlencode(parameters, doseq = True)
					link += parameters
			elif mode == Core.ModePost:
				if parameters:
					httpData = urllib.urlencode(parameters, doseq = True)

			self.mLinkFull = link

			if httpData: request = urllib2.Request(link, data = httpData)
			else: request = urllib2.Request(link)

			if mode == Core.ModePut or mode == Core.ModeDelete:
				request.get_method = lambda: mode.upper()

			request.add_header('User-Agent', Core.UserAgent)
			if httpHeaders:
				for key in httpHeaders:
					request.add_header(key, httpHeaders[key])

			response = urllib2.urlopen(request, timeout = httpTimeout)
			self.mResult = response.read()
			response.close()

			self.mResult = tools.Converter.jsonFrom(self.mResult, default = self.mResult)
			self.mSuccess = self._success(self.mResult)
			self.mError = self._error(self.mResult)

			if not self.mSuccess:
				if self.mError == 'bad_token' and httpAuthenticate:
					return redo(mode = mode, link = linkOriginal, parameters = parametersOriginal, httpTimeout = httpTimeout, httpData = httpDataOriginal, httpHeaders = httpHeaders, httpAuthenticate = httpAuthenticate)
				else:
					self._requestErrors('The call to the RealDebrid API failed', link, httpData, self.mResult)

		except (urllib2.HTTPError, urllib2.URLError) as error:
			self.mSuccess = False
			if hasattr(error, 'code'):
				errorCode = error.code
				errorString = ' ' + str(errorCode)
			else:
				errorCode = 0
				errorString = ''
			self.mError = 'RealDebrid Unavailable [HTTP/URL Error%s]' % errorString
			self._requestErrors(self.mError, link, httpData, self.mResult)
			try:
				errorApi = tools.Converter.jsonFrom(error.read())
				self.mErrorCode = errorApi['error_code']
				self.mErrorDescription = errorApi['error']
			except: pass
			if self.mErrorDescription == 'bad_token' or errorCode == 401:
				return redo(mode = mode, link = linkOriginal, parameters = parametersOriginal, httpTimeout = httpTimeout, httpData = httpDataOriginal, httpHeaders = httpHeaders, httpAuthenticate = httpAuthenticate)
			elif not self.mErrorDescription == None:
				if 'ip_not_allowed' in self.mErrorDescription:
					interface.Dialog.closeAllProgress() # The stream connection progress dialog is still showing.
					interface.Dialog.confirm(title = 33567, message = 35060)
					self.mErrorCode = Core.ErrorBlocked
		except Exception as error:
			self.mSuccess = False
			self.mError = 'Unknown Error'
			try:
				self.mErrorCode = 0
				self.mErrorDescription = str(error)
			except: pass
			self._requestErrors(self.mError, link, httpData, self.mResult)

		return self.mResult

	def _requestErrors(self, message, link, payload, result = None):
		if self.mDebug:
			try: link = str(link)
			except: link = ''
			try: payload = str(payload) if len(str(payload)) < 300 else 'Payload too large to display'
			except: payload = ''
			try: result = str(result)
			except: result = ''
			tools.Logger.error(str(message) + (': Link [%s] Payload [%s] Result [%s]' % (link, payload, result)))

	def _requestAuthentication(self, mode, link, parameters = None, httpTimeout = None, httpData = None, httpHeaders = None):
		if not parameters:
			parameters = {}
		if not httpHeaders:
			httpHeaders = {}
		httpHeaders['Authorization'] = 'Bearer %s' % self.mAuthenticationToken
		return self._request(mode = mode, link = link, parameters = parameters, httpTimeout = httpTimeout, httpData = httpData, httpHeaders = httpHeaders)

	def _retrieve(self, mode, category, action = None, id = None, link = None, magnet = None, files = None, hashes = None, httpTimeout = None, httpData = None, httpHeaders = None):
		linkApi = network.Networker.linkJoin(Core.LinkApi, category, action)
		if not id == None: linkApi = network.Networker.linkJoin(linkApi, id)

		if not hashes == None:
			for hash in hashes:
				linkApi = network.Networker.linkJoin(linkApi, hash)

		parameters = {}
		if not link == None: parameters[Core.ParameterLink] = link
		if not magnet == None: parameters[Core.ParameterMagnet] = magnet
		if not files == None: parameters[Core.ParameterFiles] = files

		return self._requestAuthentication(mode = mode, link = linkApi, parameters = parameters, httpTimeout = httpTimeout, httpData = httpData, httpHeaders = httpHeaders)

	##############################################################################
	# SUCCESS
	##############################################################################

	def _success(self, result):
		if isinstance(result, dict): return not 'error' in result
		else: return not result == None and not result == ''

	def _error(self, result):
		if isinstance(result, dict): return result['error'] if 'error' in result else None
		else: return None

	def success(self):
		return self.mSuccess

	def error(self):
		return self.mError

	##############################################################################
	# WEBSITE
	##############################################################################

	@classmethod
	def website(self, open = False):
		link = tools.Settings.getString('link.realdebrid', raw = True)
		if open: tools.System.openLink(link)
		return link

	##############################################################################
	# ACCOUNT
	##############################################################################

	def _accountAuthenticationClear(self):
		self.mAuthenticationLink = None
		self.mAuthenticationUser = None
		self.mAuthenticationDevice = None
		self.mAuthenticationInterval = None
		self.mAuthenticationId = None
		self.mAuthenticationSecret = None
		self.mAuthenticationToken = None
		self.mAuthenticationRefresh = None
		self.mAuthenticationUsername = None

	def _accountAuthenticationSettings(self):
		id = '' if self.mAuthenticationId == None else self.mAuthenticationId
		secret = '' if self.mAuthenticationSecret == None else self.mAuthenticationSecret
		token = '' if self.mAuthenticationToken == None else self.mAuthenticationToken
		refresh = '' if self.mAuthenticationRefresh == None else self.mAuthenticationRefresh
		authentication = ''
		if not self.mAuthenticationToken == None:
			if self.mAuthenticationUsername == None or self.mAuthenticationUsername == '':
				authentication = interface.Format.FontPassword
			else:
				authentication = self.mAuthenticationUsername

		tools.Settings.set('accounts.debrid.realdebrid.id', id)
		tools.Settings.set('accounts.debrid.realdebrid.secret', secret)
		tools.Settings.set('accounts.debrid.realdebrid.token', token)
		tools.Settings.set('accounts.debrid.realdebrid.refresh', refresh)
		tools.Settings.set('accounts.debrid.realdebrid.auth', authentication)

	def _accountAuthentication(self):
		# Only refresh once, in case multiple requests are submitted with an expiered token.
		# Otherwise every parallel request will try to refresh the token itself.
		if Core.AuthenticationLock is None: Core.AuthenticationLock = threading.Lock()
		Core.AuthenticationLock.acquire()

		if Core.AuthenticationToken is None:
			try:
				tools.Logger.log('The RealDebrid token expired. The token is being refreshed.')
				link = network.Networker.linkJoin(Core.LinkAuthentication, Core.CategoryToken)
				parameters = {
					Core.ParameterClientId : self.accountId(),
					Core.ParameterClientSecret : self.accountSecret(),
					Core.ParameterCode : self.accountRefresh(),
					Core.ParameterGrantType : Core.ClientGrant
				}

				result = self._request(mode = Core.ModePost, link = link, parameters = parameters, httpTimeout = 20, httpAuthenticate = False)
				if result and not 'error' in result and 'access_token' in result:
					self.mAuthenticationToken = result['access_token']
					Core.AuthenticationToken = self.mAuthenticationToken
					tools.Settings.set('accounts.debrid.realdebrid.token', self.mAuthenticationToken)
			except:
				tools.Logger.error()
		else:
			self.mAuthenticationToken = Core.AuthenticationToken

		Core.AuthenticationLock.release()
		return not Core.AuthenticationToken is None

	def accountAuthenticationLink(self):
		return self.mAuthenticationLink

	def accountAuthenticationCode(self):
		return self.mAuthenticationUser

	def accountAuthenticationInterval(self):
		return self.mAuthenticationInterval

	def accountAuthenticationReset(self, save = True):
		self._accountAuthenticationClear()
		if save: self._accountAuthenticationSettings()

	def accountAuthenticationStart(self):
		self._accountAuthenticationClear()

		try:
			link = network.Networker.linkJoin(Core.LinkAuthentication, Core.CategoryDevice, Core.ActionCode)
			parameters = {
				Core.ParameterClientId : Core.ClientId,
				Core.ParameterNewCredentials : 'yes'
			}

			result = self._request(mode = Core.ModeGet, link = link, parameters = parameters, httpTimeout = 30, httpAuthenticate = False)

			self.mAuthenticationLink = result['verification_url']
			self.mAuthenticationUser = result['user_code']
			self.mAuthenticationDevice = result['device_code']
			self.mAuthenticationInterval = result['interval']

			return True
		except:
			tools.Logger.error()

		return False

	def accountAuthenticationWait(self):
		try:
			link = network.Networker.linkJoin(Core.LinkAuthentication, Core.CategoryDevice, Core.ActionCredentials)
			parameters = {
				Core.ParameterClientId : Core.ClientId,
				Core.ParameterCode : self.mAuthenticationDevice
			}

			result = self._request(mode = Core.ModeGet, link = link, parameters = parameters, httpTimeout = 30, httpAuthenticate = False)

			if 'client_secret' in result:
				self.mAuthenticationId = result['client_id']
				self.mAuthenticationSecret = result['client_secret']
				return True
		except:
			pass

		return False

	def accountAuthenticationFinish(self):
		try:
			link = network.Networker.linkJoin(Core.LinkAuthentication, Core.CategoryToken)
			parameters = {
				Core.ParameterClientId : self.mAuthenticationId,
				Core.ParameterClientSecret : self.mAuthenticationSecret,
				Core.ParameterCode : self.mAuthenticationDevice,
				Core.ParameterGrantType : Core.ClientGrant
			}

			result = self._request(mode = Core.ModePost, link = link, parameters = parameters, httpTimeout = 30, httpAuthenticate = False)

			if 'access_token' in result and 'refresh_token' in result:
				self.mAuthenticationToken = result['access_token']
				self.mAuthenticationRefresh = result['refresh_token']

				try:
					account = self.account()
					self.mAuthenticationUsername = account['user']
					if self.mAuthenticationUsername == None or self.mAuthenticationUsername == '':
						self.mAuthenticationUsername = account['email']
				except:
					self.mAuthenticationUsername = None

				self._accountAuthenticationSettings()
				return True
		except:
			tools.Logger.error()

		return False

	def accountEnabled(self):
		return tools.Settings.getBoolean('accounts.debrid.realdebrid.enabled')

	def accountValid(self):
		return not self.accountId() == '' and not self.accountSecret() == '' and not self.accountToken() == '' and not self.accountRefresh() == ''

	def accountId(self):
		return tools.Settings.getString('accounts.debrid.realdebrid.id') if self.accountEnabled() else ''

	def accountSecret(self):
		return tools.Settings.getString('accounts.debrid.realdebrid.secret') if self.accountEnabled() else ''

	def accountToken(self):
		return tools.Settings.getString('accounts.debrid.realdebrid.token') if self.accountEnabled() else ''

	def accountRefresh(self):
		return tools.Settings.getString('accounts.debrid.realdebrid.refresh') if self.accountEnabled() else ''

	def accountVerify(self):
		return not self.account(cached = False) == None

	def account(self, cached = True):
		try:
			if self.accountValid():
				import datetime

				if cached: result = cache.Cache().cacheShort(self._retrieve, mode = Core.ModeGet, category = Core.CategoryUser)
				else: result = cache.Cache().cacheClear(self._retrieve, mode = Core.ModeGet, category = Core.CategoryUser)

				#if not self.success(): # Do not use this, since it will be false for cache calls.
				if result and isinstance(result, dict) and 'id' in result and result['id']:
					expiration = result['expiration']
					index = expiration.find('.')
					if index >= 0: expiration = expiration[:index]
					expiration = expiration.strip().lower().replace('t', ' ')
					expiration = tools.Time.datetime(expiration, '%Y-%m-%d %H:%M:%S')

					return {
						'user' : result['username'],
						'id' : result['id'],
						'email' : result['email'],
						'type' : result['type'],
						'locale' : result['locale'],
						'points' : result['points'],
						'expiration' : {
							'timestamp' : tools.Time.timestamp(expiration),
							'date' : expiration.strftime('%Y-%m-%d %H:%M:%S'),
							'remaining' : (expiration - datetime.datetime.today()).days
						}
					}
				else:
					return None
			else:
				return None
		except:
			tools.Logger.error()
			return None

	##############################################################################
	# SERVICES
	##############################################################################

	# If available is False, will return all services, including those that are currently down.
	def services(self, available = True, cached = True, onlyEnabled = False):
		# Even thow ServicesUpdate is a class variable, it will be destrcucted if there are no more Premiumize instances.
		if Core.ServicesUpdate == None:
			Core.ServicesUpdate = []

			streamingTorrent = self.streamingTorrent()
			streamingHoster = self.streamingHoster()

			try:
				# NB: The /hosts/status always throws errors, sometimes 401 errors, sometimes unknow errors. Just use /hosts

				'''
				if cached: result = cache.Cache().cacheShort(self._retrieve, mode = Core.ModeGet, category = Core.CategoryHosts, action = Core.ActionStatus)
				else: result = cache.Cache().cacheClear(self._retrieve, mode = Core.ModeGet, category = Core.CategoryHosts, action = Core.ActionStatus)

				for service in Core.ServicesTorrent:
					service['enabled'] = streamingTorrent
					Core.ServicesUpdate.append(service)

				if not result == None:
					for key, value in result.iteritems():
						if not available or value['status'] == Core.ServiceStatusUp:
							Core.ServicesUpdate.append({
								'name' : value['name'],
								'id' : key.lower(),
								'identifier' : value['id'],
								'enabled' : streamingHoster,
								'domain' : key,
								'status' : value['status'],
								'supported' : value['supported'] == 1,
							})
				'''

				if cached: result = cache.Cache().cacheShort(self._retrieve, mode = Core.ModeGet, category = Core.CategoryHosts)
				else: result = cache.Cache().cacheClear(self._retrieve, mode = Core.ModeGet, category = Core.CategoryHosts)

				for service in Core.ServicesTorrent:
					service['enabled'] = streamingTorrent
					Core.ServicesUpdate.append(service)

				if not result == None:
					for key, value in result.iteritems():
						if key: # Exclude "Remote".
							Core.ServicesUpdate.append({
								'name' : value['name'],
								'id' : key.lower(),
								'identifier' : value['id'],
								'enabled' : streamingHoster,
								'domain' : key,
								'status' : 'up',
								'supported' : True,
							})

			except:
				tools.Logger.error()

		if onlyEnabled:
			return [i for i in Core.ServicesUpdate if i['enabled']]
		else:
			return Core.ServicesUpdate

	def servicesDomains(self, cached = True):
		if cached: return cache.Cache().cacheShort(self._retrieve, mode = Core.ModeGet, category = Core.CategoryHosts, action = Core.ActionDomains)
		else: return cache.Cache().cacheClear(self._retrieve, mode = Core.ModeGet, category = Core.CategoryHosts, action = Core.ActionDomains)

	def servicesList(self, onlyEnabled = False, domains = True):
		services = self.services(onlyEnabled = onlyEnabled)
		services = [service['id'] for service in services]
		if domains:
			try: services.extend(self.servicesDomains())
			except: tools.Logger.error()
		return list(set(services))

	def service(self, nameOrDomain):
		nameOrDomain = nameOrDomain.lower()
		for service in self.services():
			if service['name'].lower() == nameOrDomain or service['domain'].lower() == nameOrDomain:
				return service
		return None

	##############################################################################
	# ADD
	##############################################################################

	def _addLink(self, result):
		try: id = result['id']
		except: id = None
		try: link = result['download']
		except: link = None
		return self.addResult(id = id, link = link)

	def add(self, link, title = None, season = None, episode = None, pack = False, source = None):
		container = network.Container(link)
		if source == network.Container.TypeTorrent:
			type = network.Container.TypeTorrent
		else:
			type = container.type()
		if type == network.Container.TypeTorrent:
			try:
				hash = container.hash()
				if not hash: raise Exception()
				exisitng = self._itemHash(hash, season = season, episode = episode)
				if not exisitng: raise Exception()
				return self._addLink(exisitng)
			except:
				return self.addTorrent(link = link, title = title, season = season, episode = episode)
		else:
			return self.addHoster(link)

	def addContainer(self, link, title = None):
		try:
			source = network.Container(link, download = True).information()
			if source['path'] == None and source['data'] == None:
				return Core.ErrorInaccessible

			data = source['data']
			result = self._retrieve(mode = Core.ModePut, category = Core.CategoryTorrents, action = Core.ActionAddTorrent, httpData = data)

			if self.success() and 'id' in result: return self._addLink(result)
			elif self.mErrorCode == Core.ErrorBlocked: return self.addResult(error = Core.ErrorBlocked, notification = True)
			else: return self.addResult(error = Core.ErrorRealDebrid)
		except:
			tools.Logger.error()
			return self.addResult(error = Core.ErrorRealDebrid)

	def addHoster(self, link):
		result = self._retrieve(mode = Core.ModePost, category = Core.CategoryUnrestrict, action = Core.ActionLink, link = link)
		if self.success() and 'download' in result: return self._addLink(result)
		elif self.mErrorCode == Core.ErrorBlocked: return self.addResult(error = Core.ErrorBlocked, notification = True)
		else: return self.addResult(error = Core.ErrorRealDebrid)

	def addTorrent(self, link, title = None, season = None, episode = None):
		container = network.Container(link)
		source = container.information()
		if source['magnet']:
			magnet = container.torrentMagnet(title = title, encode = False)
			result = self._retrieve(mode = Core.ModePost, category = Core.CategoryTorrents, action = Core.ActionAddMagnet, magnet = magnet)
			if self.success() and 'id' in result: return self._addLink(result)
			elif self.mErrorCode == Core.ErrorBlocked: return self.addResult(error = Core.ErrorBlocked, notification = True)
			else: return self.addResult(error = Core.ErrorRealDebrid)
		else:
			return self.addContainer(link = link, title = title)

	##############################################################################
	# SELECT
	##############################################################################

	# Selects the files in the torrent to download.
	# files can be an id, a list of ids, or a Selection type.
	def selectList(self, id, files = None, item = None, season = None, episode = None, manual = False, pack = False):
		if manual:
			if item == None: item = self.item(id)
			items = {}
			items['items'] = item
			items['link'] = None
			items['selection'] = None
			return items
		else:
			result = None
			largest = None
			try:
				if files == Core.SelectionAll:
					result = Core.SelectionAll
				elif files == Core.SelectionName:
					if item == None: item = self.item(id)
					meta = metadata.Metadata()
					if item and 'files' in item:
						for file in item['files']:
							if meta.episodeContains(title = file['path'], season = season, episode = episode):
								if largest == None or file['size']['bytes'] > largest['size']['bytes']:
									largest = file
						if largest == None:
							for file in item['files']:
								if meta.episodeContains(title = file['path'], season = None, episode = episode, extra = True):
									if largest == None or file['size']['bytes'] > largest['size']['bytes']:
										largest = file
					if largest == None:
						return result
					else:
						# Always download all files in season packs.
						# Otherwise RealDebrid will only download a single episode, but still show the torrent as being cached.
						# Subsequent episodes from the pack might therefore have to be downloaded first even though they show up as being cached.
						if pack: result = ','.join([str(file['id']) for file in item['files']])
						else: result = str(largest['id'])
				elif files == Core.SelectionLargest:
					if item == None:
						item = self.item(id)
					if item and 'files' in item:
						largestId = None
						largestSize = 0
						for file in item['files']:
							size = file['size']['bytes']
							if size > largestSize:
								largestSize = size
								largestId = file['id']
								largest = file
						if largestId == None:
							return result
						else:
							result = str(largestId)
					else:
						return Core.ErrorUnavailable
				elif not isinstance(files, basestring):
					if isinstance(files, list):
						result = ','.join(files)
					else:
						result = str(files)
			except:
				pass

			items = {}
			items['items'] = item
			items['link'] = largest['link'] if largest and 'link' in largest else None
			items['selection'] = result
			return items

	# Selects the files in the torrent to download.
	# files can be an id, a list of ids, or a Selection type.
	def select(self, id, files, item = None, season = None, episode = None, pack = False):
		try:
			items = self.selectList(id = id, files = files, item = item, season = season, episode = episode, pack = pack)
			if items == None or items['selection'] == None: return Core.ErrorUnavailable
			result = self._retrieve(mode = Core.ModePost, category = Core.CategoryTorrents, action = Core.ActionSelectFiles, id = id, files = items['selection'])
			if self.success(): return True
			else: return Core.ErrorRealDebrid
		except:
			# If there are no seeders and RealDebrid cannot retrieve a list of files.
			return Core.ErrorRealDebrid

	def selectAll(self, id, pack = False):
		return self.select(id = id, files = Core.SelectionAll, pack = pack)

	def selectName(self, id, item = None, season = None, episode = None, pack = False):
		return self.select(id = id, files = Core.SelectionName, item = item, season = season, episode = episode, pack = pack)

	def selectLargest(self, id, item = None, pack = False):
		return self.select(id = id, files = Core.SelectionLargest, item = item, pack = pack)

	def selectManualInitial(self, id, item = None, pack = False):
		try:
			items = self.selectList(id = id, item = item, manual = True, pack = pack)
			if items == None or items['items'] == None: return Core.ErrorUnavailable
			else: return items
		except:
			# If there are no seeders and RealDebrid cannot retrieve a list of files.
			return Core.ErrorRealDebrid

	def selectManualFinal(self, id, selection):
		try:
			self._retrieve(mode = Core.ModePost, category = Core.CategoryTorrents, action = Core.ActionSelectFiles, id = id, files = str(selection))
			if self.success() or self.mError == 'action_already_done': return True
			else: return Core.ErrorRealDebrid
		except:
			# If there are no seeders and RealDebrid cannot retrieve a list of files.
			return Core.ErrorRealDebrid

	##############################################################################
	# CACHED
	##############################################################################

	@classmethod
	def cachedModes(self):
		return {Core.ModeTorrent}

	# id: single hash or list of hashes.
	def cachedIs(self, id, timeout = None):
		result = self.cached(id = id, timeout = timeout)
		if isinstance(result, dict): return result['cached']
		elif isinstance(result, list): return[i['cached'] for i in result]
		else: return False

	# id: single hash or list of hashes.
	def cached(self, id, timeout = None, callback = None, sources = None):
		single = isinstance(id, basestring)
		if single: id = [id] # Must be passed in as a list.
		id = [id.lower() for id in id]

		# A URL has a maximum length, so the hashes have to be split into parts and processes independently, in order not to exceed the URL limit.
		chunks = [id[i:i + Core.LimitHashesGet] for i in xrange(0, len(id), Core.LimitHashesGet)]
		if sources: chunksSources = [sources[i:i + Core.LimitHashesGet] for i in xrange(0, len(sources), Core.LimitHashesGet)]
		else: chunksSources = None

		self.tCacheLock = threading.Lock()
		self.tCacheResult = {}
		def cachedChunk(callback, hashes, sources, timeout):
			try:
				realdebrid = Core()
				result = realdebrid._retrieve(mode = Core.ModeGet, category = Core.CategoryTorrents, action = Core.ActionInstantAvailability, hashes = hashes, httpTimeout = timeout)
				if realdebrid.success():
					for key, value in result.iteritems():
						key = key.lower()
						result = False
						try:
							files = []
							value = value['rd']
							for group in value:
								# NG says that season packs can be properley detected in the new RD API.
								# For now, include torrents with multiple files.
								#if len(group.keys()) == 1: # More than 1 file means the unrestricted link will be a RAR file.
									for fileKey, fileValue in group.iteritems():
										if tools.Video.extensionValid(path = fileValue['filename']):
											files.append(fileValue['filename'])
							if len(files) > 0:
								if sources:
									source = sources[hashes.index(key)]
									if source['metadata'].pack() or (source['metadata'].isEpisode() and len(files) > 1):
										for file in files:
											meta = metadata.Metadata(name = file, title = source['metadata'].title(raw = True), season = source['metadata'].season(), episode = source['metadata'].episode()) # Do not add pack here, since these are individual files.
											if not meta.ignore(size = False, seeds = False):
												result = True
									else:
										result = True
								else:
									result = True
						except: pass

						self.tCacheLock.acquire()
						self.tCacheResult[key] = result
						self.tCacheLock.release()
						if callback:
							try: callback(self.id(), key, result)
							except: pass
			except:
				tools.Logger.error()

		threads = []
		for i in range(len(chunks)):
			try: thread = threading.Thread(target = cachedChunk, args = (callback, chunks[i], chunksSources[i], timeout))
			except: thread = threading.Thread(target = cachedChunk, args = (callback, chunks[i], None, timeout))
			threads.append(thread)
			thread.start()

		[i.join() for i in threads]
		if not callback:
			caches = []
			for key, value in self.tCacheResult.iteritems():
				caches.append({'id' : key, 'hash' : key, 'cached' : value})
			if single: return caches[0] if len(caches) > 0 else False
			else: return caches

	##############################################################################
	# DELETE
	##############################################################################

	# Check if the file can be deleted.
	@classmethod
	def deletePossible(self, source):
		source = source.lower()
		return source in [Core.ModeTorrent] or source == self.id()

	def delete(self, id):
		result = self._retrieve(mode = Core.ModeDelete, category = Core.CategoryTorrents, action = Core.ActionDelete, id = id)
		if self.success() or self.mErrorCode == 0: # The delete request does not return and data, only HTTP 204.
			return True
		else:
			return Core.ErrorRealDebrid

	def deleteAll(self, wait = True):
		items = self.items()
		if isinstance(items, list):
			if len(items) > 0:
				def _deleteAll(id):
					Core().delete(id)
				threads = []
				for item in items:
					threads.append(threading.Thread(target = _deleteAll, args = (item['id'],)))

				# Complete the first thread in case the token has to be refreshed.
				threads[0].start()
				threads[0].join()

				for i in range(1, len(threads)):
					threads[i].start()
				if wait:
					for i in range(1, len(threads)):
						threads[i].join()
			return True
		else:
			return Core.ErrorRealDebrid

	def _deleteSingle(self, hashOrLink):
		id = None
		items = self.items()
		if network.Networker.linkIs(hashOrLink):
			for item in items:
				if item['link'] == hashOrLink:
					id = item['id']
		else:
			hashOrLink = hashOrLink.lower()
			for item in items:
				if item['hash'].lower() == hashOrLink:
					id = item['id']
			if id == None: # If RealDebrid ID was passed instead of hash.
				id = hashOrLink

		if id == None: return False
		self.delete(id)
		return True

	# Delete an item and its corresponding transfer based on the link or hash.
	def deleteSingle(self, hashOrLink, wait = True):
		thread = threading.Thread(target = self._deleteSingle, args = (hashOrLink,))
		thread.start()
		if wait: thread.join()
		return True

	# Delete on launch
	def deleteLaunch(self):
		try:
			if tools.Settings.getBoolean('accounts.debrid.realdebrid.removal'):
				option = tools.Settings.getInteger('accounts.debrid.realdebrid.removal.launch')
				if option == 1:
					self.deleteAll(wait = False)
		except:
			pass

	# Delete on playback ended
	def deletePlayback(self, id, pack = None, category = None):
		try:
			if tools.Settings.getBoolean('accounts.debrid.realdebrid.removal'):
				option = tools.Settings.getInteger('accounts.debrid.realdebrid.removal.playback')
				if option == 1:
					self.deleteAll(wait = False)
				elif option == 2:
					self.deleteSingle(id, wait = False)
		except:
			pass

	# Delete on failure
	def deleteFailure(self, hashOrLink):
		try:
			if tools.Settings.getBoolean('accounts.debrid.realdebrid.removal'):
				option = tools.Settings.getInteger('accounts.debrid.realdebrid.removal.failure')
				if option == 1:
					self.deleteAll(wait = False)
				elif option == 2:
					self.deleteSingle(hashOrLink, wait = False)
		except:
			pass

	##############################################################################
	# TIME
	##############################################################################

	def _timeOffset(self):
		try:
			timeServer = self._retrieve(mode = Core.ModeGet, category = Core.CategoryTime)
			timeServer = convert.ConverterTime(timeServer, format = convert.ConverterTime.FormatDateTime).timestamp()
			timeUtc = tools.Time.timestamp()
			timeOffset = timeServer - timeUtc
			return int(3600 * round(timeOffset / float(3600))) # Round to the nearest hour
		except:
			return 0

	def timeOffset(self):
		# Only initialize TimeOffset if it was not already intialized before.
		# There is an issue with RealDebrid servers being flooded with /time API requests.
		# Not sure why this happens, but might be because the cache is not working (eg: write permission on Android).
		# Always check if TimeOffset is already in memory from a previous request, so that issues with caching the value to disk do not cause continues API calls.
		if Core.TimeOffset is None:
			Core.TimeOffset = cache.Cache().cacheMedium(self._timeOffset)
		return Core.TimeOffset

	##############################################################################
	# ITEMS
	##############################################################################

	def _itemHash(self, hash, season = None, episode = None):
		try:
			hash = hash.lower()
			items = self.items()
			meta = metadata.Metadata()
			for item in items:
				if item['hash'].lower() == hash:
					# Also check for the season/episode for season packs.
					# Otherwise RealDebrid will always return the first ever episode downloaded in the pack, since the hash for the torrent is the same.
					# Force to download again, if the episode does not match, that is a different episode is selected from the season pack.
					if meta.episodeContains(title = item['name'], season = season, episode = episode):
						return item
			for item in items:
				if item['hash'].lower() == hash:
					# Also check for the season/episode for season packs.
					# Otherwise RealDebrid will always return the first ever episode downloaded in the pack, since the hash for the torrent is the same.
					# Force to download again, if the episode does not match, that is a different episode is selected from the season pack.
					if meta.episodeContains(title = item['name'], season = None, episode = episode, extra = True):
						return item
		except:
			pass
		return None

	def _item(self, dictionary, season = None, episode = None, pack = False):
		result = {}
		try:
			status = dictionary['status']
			sizeBytes = dictionary['bytes']
			if sizeBytes == 0: # Seems to be a bug in RealDebrid that sometimes the size shows up as 0. Use the largest file instead.
				if 'files' in dictionary:
					for file in dictionary['files']:
						size = file['bytes']
						if size > sizeBytes: sizeBytes = size
				if sizeBytes == 0 and 'original_bytes' in dictionary:
					sizeBytes = dictionary['original_bytes']
			size = convert.ConverterSize(value = sizeBytes, unit = convert.ConverterSpeed.Byte)

			split = convert.ConverterSize(value = dictionary['split'], unit = convert.ConverterSpeed.ByteGiga)
			speed = convert.ConverterSpeed(value = dictionary['speed'] if 'speed' in dictionary else 0, unit = convert.ConverterSpeed.Byte)

			offset = self.timeOffset()
			started = convert.ConverterTime(value = dictionary['added'], format = convert.ConverterTime.FormatDateTimeJson, offset = offset)
			if 'ended' in dictionary:
				finished = convert.ConverterTime(value = dictionary['ended'], format = convert.ConverterTime.FormatDateTimeJson, offset = offset)
				# RealDebrid seems to do caching in the background. In such a case, the finished time might be before the started time, since it was previously downloaded by another user.
				if finished.timestamp() < started.timestamp():
					finished = started
			else:
				finished = None

			seeders = dictionary['seeders'] if 'seeders' in dictionary else 0

			completedProgress = dictionary['progress'] / 100.0
			completedBytes = int(sizeBytes * completedProgress)
			completedSize = convert.ConverterSize(value = completedBytes, unit = convert.ConverterSpeed.Byte)
			if finished == None:
				difference = tools.Time.timestamp() - started.timestamp()
			else: difference = finished.timestamp() - started.timestamp()
			completedDuration = convert.ConverterDuration(value = difference, unit = convert.ConverterDuration.UnitSecond)
			completedSeconds = completedDuration.value(convert.ConverterDuration.UnitSecond)

			remainingProgress = 1 - completedProgress
			remainingBytes = sizeBytes - completedBytes
			remainingSize = convert.ConverterSize(value = remainingBytes, unit = convert.ConverterSpeed.Byte)
			remainingSeconds = int(remainingBytes * (completedSeconds / float(completedBytes))) if completedBytes > 0 else 0
			remainingDuration = convert.ConverterDuration(value = remainingSeconds, unit = convert.ConverterDuration.UnitSecond)

			result = {
				'id' : dictionary['id'],
				'hash' : dictionary['hash'],
				'name' : dictionary['filename'],
				'type' : Core.TypeTorrent,
				'status' : status,
				'host' : dictionary['host'],
				'time' : {
					'started' : started.string(convert.ConverterTime.FormatDateTime),
					'finished' : finished.string(convert.ConverterTime.FormatDateTime) if finished else None
				},
				'size' : {
					'bytes' : size.value(),
					'description' : size.stringOptimal()
				},
				'split' : {
					'bytes' : split.value(),
					'description' : split.stringOptimal()
				},
				'transfer' : {
					'speed' : {
						'bytes' : speed.value(convert.ConverterSpeed.Byte),
						'bits' : speed.value(convert.ConverterSpeed.Bit),
						'description' : speed.stringOptimal()
					},
					'torrent' : {
						'seeding' : status == Core.StatusUploading,
						'seeders' : seeders,
					},
					'progress' : {
						'completed' : {
							'value' : completedProgress,
							'percentage' : int(completedProgress * 100),
							'size' : {
								'bytes' : completedSize.value(),
								'description' : completedSize.stringOptimal()
							},
							'time' : {
								'seconds' : completedDuration.value(convert.ConverterDuration.UnitSecond),
								'description' : completedDuration.string(convert.ConverterDuration.FormatDefault)
							}
						},
						'remaining' : {
							'value' : remainingProgress,
							'percentage' : int(remainingProgress * 100),
							'size' : {
								'bytes' : remainingSize.value(),
								'description' : remainingSize.stringOptimal()
							},
							'time' : {
								'seconds' : remainingDuration.value(convert.ConverterDuration.UnitSecond),
								'description' : remainingDuration.string(convert.ConverterDuration.FormatDefault)
							}
						}
					}
				}
			}

			# Link
			if 'links' in dictionary and len(dictionary['links']) > 0:
				index = None
				largest = None
				try:
					files = dictionary['files']
					if pack:
						meta = metadata.Metadata()
						for i in range(len(files)):
							file = files[i]
							if file['selected'] and meta.episodeContains(title = file['path'], season = season, episode = episode):
								if largest == None or file['bytes'] > largest['bytes']:
									largest = file
									index = i
						if index == None:
							for i in range(len(files)):
								file = files[i]
								if file['selected'] and meta.episodeContains(title = file['path'], season = None, episode = episode, extra = True):
									if largest == None or file['bytes'] > largest['bytes']:
										largest = file
										index = i
					if index == None:
						for i in range(len(files)):
							file = files[i]
							if file['selected'] and (largest == None or file['bytes'] > largest['bytes']):
								largest = file
								index = i
				except: pass # If there is not 'files' attribute in the results.
				if index == None: index = 0
				try: result['link'] = dictionary['links'][index]
				except: result['link'] = dictionary['links'][0] # Sometimes RD only has 1 link for all the files.
			else:
				result['link'] = None

			# Files
			if 'files' in dictionary and len(dictionary['files']) > 0:
				files = []
				for file in dictionary['files']:
					size = convert.ConverterSize(value = file['bytes'], unit = convert.ConverterSpeed.Byte)

					name = file['path']
					index = name.rfind('/')
					if index >= 0: name = name[index + 1:]

					files.append({
						'id' : file['id'],
						'path' : file['path'],
						'name' : name,
						'selected' : tools.Converter.boolean(file['selected']),
						'size' : {
							'bytes' : size.value(),
							'description' : size.stringOptimal()
						}
					})
				result['files'] = files
			else:
				result['files'] = None

		except:
			tools.Logger.error()
			pass
		return result

	def items(self, season = None, episode = None, pack = False):
		results = self._retrieve(mode = Core.ModeGet, category = Core.CategoryTorrents)
		if self.success():
			items = []
			for result in results:
				items.append(self._item(result, season = season, episode = episode, pack = pack))
			return items
		else:
			return Core.ErrorRealDebrid

	def item(self, id, season = None, episode = None, pack = False):
		result = self._retrieve(mode = Core.ModeGet, category = Core.CategoryTorrents, action = Core.ActionInfo, id = id)
		if self.success():
			return self._item(result, season = season, episode = episode, pack = pack)
		else:
			return Core.ErrorRealDebrid

	##############################################################################
	# DOWNLOAD
	##############################################################################

	# Number of torrent download slots available.
	def downloadSlots(self):
		results = self._retrieve(mode = Core.ModeGet, category = Core.CategoryTorrents, action = Core.ActionActive)
		if self.success():
			try: return results['limit'] - results['nb']
			except: return 0
		else:
			return Core.ErrorRealDebrid

	def downloadHosts(self):
		results = self._retrieve(mode = Core.ModeGet, category = Core.CategoryTorrents, action = Core.ActionAvailableHosts)
		if self.success():
			items = []
			for result in results:
				size = convert.ConverterSize(value = result['max_file_size'], unit = convert.ConverterSpeed.ByteGiga)
				items.append({
					'domain' : result['host'],
					'size' : {
						'bytes' : size.value(),
						'description' : size.stringOptimal()
					}
				})
			return items
		else:
			return Core.ErrorRealDebrid

	def downloadInformation(self):
		items = self.items()
		if isinstance(items, list):
			count = len(items)
			countBusy = 0
			countFinished = 0
			countFailed = 0
			size = 0
			for item in items:
				size += item['size']['bytes']
				status = item['status']
				if status in [Core.StatusUnknown, Core.StatusError, Core.StatusMagnetConversion, Core.StatusVirus, Core.StatusDead]:
					countFailed += 1
				elif status in [Core.StatusFinished, Core.StatusUploading]:
					countFinished += 1
				else:
					countBusy += 1
			size = convert.ConverterSize(value = size, unit = convert.ConverterSize.Byte)

			result = {
				'count' : {
					'total' : count,
					'busy' : countBusy,
					'finished' : countFinished,
					'failed' : countFailed,
				},
				'size' : {
					'bytes' : size.value(),
					'description' : size.stringOptimal()
				}
			}

			hosts = self.downloadHosts()
			if isinstance(hosts, list) and len(hosts) > 0:
				result['host'] = hosts[0]

			return result
		else:
			return Core.ErrorRealDebrid
