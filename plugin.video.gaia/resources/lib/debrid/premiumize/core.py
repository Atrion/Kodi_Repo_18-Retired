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

import re
import os
import sys
import math
import urllib
import urllib2
import urlparse
import threading

from resources.lib.debrid import base
from resources.lib.extensions import convert
from resources.lib.extensions import cache
from resources.lib.extensions import tools
from resources.lib.extensions import interface
from resources.lib.extensions import network
from resources.lib.extensions import metadata

class Core(base.Core):

	Id = 'premiumize'
	Name = 'Premiumize'
	Abbreviation = 'P'
	Priority = 1

	# Services
	ServicesUpdate = None
	Services = [
		{	'name' : 'Torrent',				'domain' : 'torrent',			'limit' : 0,	'factor' : 1	},
		{	'name' : 'Usenet',				'domain' : 'usenet',			'limit' : 0,	'factor' : 1	},
		{	'name' : 'VPN',					'domain' : 'vpn',				'limit' : 0,	'factor' : 1	},
		{	'name' : 'Cloud Storage',		'domain' : 'cloudstorage',		'limit' : 0,	'factor' : 1	},
		{	'name' : 'Cloud Downloads',		'domain' : 'clouddownloads',	'limit' : 0,	'factor' : 1	},
	]

	# Usage - Maximum usage bytes and points
	UsageBytes = 1073741824000
	UsagePoints = 1000

	# Encryption
	# On SPMC (Python < 2.7.8), TLS encryption is not supported, which is required by Core.
	# Force ecrypted connections on Python 2.7.8 and lower to be unencrypted.
	# Unencrypted connection on Premiumize need an http prefix/subdomain instead of www/api, otherwise it will automatically redirect to https.
	Encryption = tools.Settings.getBoolean('accounts.debrid.premiumize.encryption') and not sys.version_info < (2, 7, 9)

	Method = tools.Settings.getInteger('accounts.debrid.premiumize.method')
	MethodGet = Method == 2

	# Limits
	LimitLink = 2000 # Maximum length of a URL.
	LimitHashesGet = 40 # Maximum number of 40-character hashes to use in GET parameter so that the URL length limit is not exceeded.
	LimitHashesPost = 100 # Even when the hashes are send via POST, Premiumize seems to ignore the last ones (+- 1000 hashes). When too many hashes are sent at once (eg 500-900), if often causes a request timeout. Keep the limit small enough. Rather start multiple requests which should create multipel threads on the server.

	# Protocols
	ProtocolEncrypted = 'https'
	ProtocolUnencrypted = 'http'

	# Prefixes
	PrefixEncrypted = 'www'
	PrefixUnencrypted = 'http'

	#Links
	LinkMain = 'premiumize.me'
	LinkApi = 'premiumize.me/api/'

	# User Agent
	UserAgent = tools.System.name() + ' ' + tools.System.version()

	# Categories
	CategoryAccount = 'account'
	CategoryFolder = 'folder'
	CategoryTransfer = 'transfer'
	CategoryTorrent = 'torrent'
	CategoryCache = 'cache'
	CategoryServices = 'services'
	CategoryZip = 'zip'
	CategoryToken = 'token'
	CategoryDevice = 'device'

	# Actions
	ActionDownload = 'directdl'
	ActionInfo = 'info'
	ActionCreate = 'create'
	ActionList = 'list'
	ActionRename = 'rename'
	ActionPaste = 'paste'
	ActionDelete = 'delete'
	ActionBrowse = 'browse'
	ActionCheck = 'check'
	ActionCheckHashes = 'checkhashes'
	ActionClear = 'clearfinished'
	ActionGenerate = 'generate'
	ActionCode = 'code'

	# Parameters
	ParameterLogin = 'params[login]'
	ParameterPassword = 'params[pass]'
	ParameterLink = 'params[link]'
	ParameterMethod = 'method'
	ParameterCustomer = 'customer_id'
	ParameterPin = 'pin'
	ParameterId = 'id'
	ParameterParent = 'parent_id'
	ParameterName = 'name'
	ParameterItems = 'items'
	ParameterType = 'type'
	ParameterHash = 'hash'
	ParameterHashes = 'hashes[]'
	ParameterCaches = 'items[]'
	ParameterSource = 'src'
	ParameterItemId = 'items[0][id]'
	ParameterItemType = 'items[0][type]'
	ParameterClientId = 'client_id'
	ParameterClientSecret = 'client_secret'
	ParameterCode = 'code'
	ParameterGrantType = 'grant_type'
	ParameterResponseType = 'response_type'

	# Statuses
	StatusUnknown = 'unknown'
	StatusError = 'error'
	StatusTimeout = 'timeout'
	StatusQueued = 'queued'
	StatusBusy = 'busy'
	StatusFinalize = 'finalize'
	StatusFinished = 'finished'

	# Errors
	ErrorUnknown = 'unknown'
	ErrorAuthentication = 'authentication'
	ErrorInaccessible = 'inaccessible' # Eg: 404 error.
	ErrorTemporary = 'temporary' # Temporary errors
	ErrorPremium = 'premium' # Require premium account.
	ErrorPremiumize = 'premiumize' # Error from Premiumize server.
	ErrorSelection = 'selection' # No file selected from list of items.
	ErrorUnsupported = 'unsupported' # Not official Premiumize error. Indicates that a certain feature isd not supported.

	# Client
	ClientId = tools.System.obfuscate(tools.Settings.getString('internal.premiumize.client', raw = True))

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		base.Core.__init__(self, Core.Id, Core.Name)

		self._accountAuthenticationClear()
		self.mAuthenticationToken = self.accountToken()

		self.mLinkBasic = None
		self.mLinkFull = None
		self.mParameters = None
		self.mSuccess = None
		self.mError = None
		self.mErrorCode = None
		self.mErrorDescription = None
		self.mResult = None

	##############################################################################
	# INTERNAL
	##############################################################################

	def _parameter(self, parameter, parameters):
		if parameter in parameters:
			return parameters[parameter]
		else:
			return None

	def _link(self, protocol, prefix, link):
		return '%s://%s.%s' % (protocol, prefix, link)

	def _linkMain(self, encrypted = None):
		if encrypted == None: encrypted = Core.Encryption
		if encrypted == True: return self._link(Core.ProtocolEncrypted, Core.PrefixEncrypted, Core.LinkMain)
		else: return self._link(Core.ProtocolUnencrypted, Core.PrefixUnencrypted, Core.LinkMain)

	def _linkApi(self, encrypted = None):
		if encrypted == None: encrypted = Core.Encryption
		if encrypted == True: return self._link(Core.ProtocolEncrypted, Core.PrefixEncrypted, Core.LinkApi)
		else: return self._link(Core.ProtocolUnencrypted, Core.PrefixUnencrypted, Core.LinkApi)

	def _linkApiUnencrypted(self, link):
		if link.startswith(Core.ProtocolEncrypted):
			return link.replace(Core.ProtocolEncrypted, Core.ProtocolUnencrypted, 1).replace(Core.PrefixEncrypted, Core.PrefixUnencrypted, 1)
		else:
			return None

	def _request(self, link, parameters = None, httpTimeout = None, httpData = None, httpHeaders = None, httpAuthenticate = True, fallback = False):
		self.mResult = None

		linkOriginal = link
		parametersOriginal = parameters
		httpDataOriginal = httpData

		def redo(link, parameters, httpTimeout, httpData, httpHeaders, httpAuthenticate):
			# Premiumize's OAuth does not have a refresh token.
			# The access token is valid for 10 years.
			# In case this 10-year-limit is ever reached, simply inform the user to reauthenticate.
			interface.Dialog.notification(title = 35107, message = 35461, icon = interface.Dialog.IconError, time = 10000)
			return None

		try:
			self.mLinkBasic = link
			self.mParameters = parameters
			self.mSuccess = None
			self.mError = None
			self.mErrorCode = None
			self.mErrorDescription = None

			# Use GET parameters for uploading files/containers (src parameter).
			if Core.MethodGet or httpData:
				if parameters:
					if not link.endswith('?'):
						link += '?'
					parameters = urllib.urlencode(parameters, doseq = True)
					parameters = urllib.unquote(parameters) # Premiumize uses [] in the API links. Do not encode those and other URL characters.
					link += parameters
			else: # Use POST for all other requests.
				# List of values, eg: hashes[]
				# http://stackoverflow.com/questions/18201752/sending-multiple-values-for-one-name-urllib2
				if Core.ParameterHashes in parameters:
					# If hashes are very long and if the customer ID and pin is appended to the end of the parameter string, Premiumize will ignore them and say there is no ID/pin.
					# Manually move the hashes to the back.
					hashes = {}
					hashes[Core.ParameterHashes] = parameters[Core.ParameterHashes]
					del parameters[Core.ParameterHashes]
					httpData = urllib.urlencode(hashes, doseq = True)
					if len(parameters.keys()) > 0: httpData = urllib.urlencode(parameters, doseq = True) + '&' + httpData
				elif Core.ParameterCaches in parameters:
					# If hashes are very long and if the customer ID and pin is appended to the end of the parameter string, Premiumize will ignore them and say there is no ID/pin.
					# Manually move the hashes to the back.
					links = {}
					links[Core.ParameterCaches] = parameters[Core.ParameterCaches]
					del parameters[Core.ParameterCaches]
					for key, value in links.iteritems():
						if isinstance(value, (list, tuple)):
							for i in range(len(value)):
								try: value[i] = value[i].encode('utf-8')
								except: pass
						else:
							try: links[key] = value.encode('utf-8')
							except: pass
					httpData = urllib.urlencode(links, doseq = True)
					if len(parameters.keys()) > 0: httpData = urllib.urlencode(parameters, doseq = True) + '&' + httpData
				else:
					httpData = urllib.urlencode(parameters, doseq = True)

			# If the link is too long, reduce the size. The maximum URL size is 2000.
			# This occures if GET parameters are used instead of POST for checking a list of hashes.
			# If the user disabled Premiumize encryption, the parameters MUST be send via GET, since Premiumize will ignore POST parameters on HTTP connections.
			if 'hashes[]=' in link:
				while len(link) > Core.LimitLink:
					start = link.find('hashes[]=')
					end = link.find('&', start)
					link = link[:start] + link[end + 1:]
			elif 'items[]=' in link:
				while len(link) > Core.LimitLink:
					start = link.find('items[]=')
					end = link.find('&', start)
					link = link[:start] + link[end + 1:]

			self.mLinkFull = link

			if httpData: request = urllib2.Request(link, data = httpData)
			else: request = urllib2.Request(link)

			request.add_header('User-Agent', Core.UserAgent)
			if httpHeaders:
				for key in httpHeaders:
					request.add_header(key, httpHeaders[key])

			if not httpTimeout:
				if httpData: httpTimeout = 60
				else: httpTimeout = 30

			response = urllib2.urlopen(request, timeout = httpTimeout)
			result = response.read()

			response.close()
			self.mResult = tools.Converter.jsonFrom(result)

			self.mSuccess = self._success(self.mResult)
			self.mError = self._error(self.mResult)
			if not self.mSuccess:
				if self.mError == 'bad_token' and httpAuthenticate:
					return redo(link = linkOriginal, parameters = parametersOriginal, httpTimeout = httpTimeout, httpData = httpDataOriginal, httpHeaders = httpHeaders, httpAuthenticate = httpAuthenticate, fallback = fallback)
				else:
					self._requestErrors('The call to the Premiumize API failed', link, httpData, self.mResult, exception = False)

		except (urllib2.HTTPError, urllib2.URLError) as error:
			self.mSuccess = False
			if hasattr(error, 'code'):
				errorCode = error.code
				errorString = ' ' + str(errorCode)
			else:
				errorCode = 0
				errorString = ''
			self.mError = 'Premiumize Unreachable [HTTP/URL Error%s]' % errorString
			if httpAuthenticate: self._requestErrors(self.mError, link, httpData, self.mResult)
			try:
				errorApi = tools.Converter.jsonFrom(error.read())
				self.mErrorCode = errorApi['error_code']
				self.mErrorDescription = errorApi['error']
			except: pass
			if self.mErrorDescription == 'bad_token' or errorCode == 401:
				return redo(link = linkOriginal, parameters = parametersOriginal, httpTimeout = httpTimeout, httpData = httpDataOriginal, httpHeaders = httpHeaders, httpAuthenticate = httpAuthenticate, fallback = fallback)
			elif not fallback:
				newLink = self._linkApiUnencrypted(linkOriginal)
				if not newLink == None:
					tools.Logger.log('Retrying the encrypted link over an unencrypted connection: ' + str(newLink))
					return self._request(link = newLink, parameters = parametersOriginal, httpTimeout = httpTimeout, httpData = httpDataOriginal, httpHeaders = httpHeaders, httpAuthenticate = httpAuthenticate, fallback = True)
		except:
			self.mSuccess = False
			self.mError = 'Unknown Error'
			self._requestErrors(self.mError, link, httpData, self.mResult)
		return self.mResult

	def _requestErrors(self, message, link, payload, result = None, exception = True):
		# While downloading, do not add to log.
		if not result == None and 'message' in result and result['message'] == 'Download is not finished yet.':
			return

		link = str(link)
		payload = str(payload) if len(str(payload)) < 300 else 'Payload too large to display'
		result = str(result)
		tools.Logger.error(str(message) + (': Link [%s] Payload [%s] Result [%s]' % (link, payload, result)), exception = exception)

	def _requestAuthentication(self, link, parameters = None, httpTimeout = None, httpData = None, httpHeaders = None):
		if not parameters:
			parameters = {}
		if not httpHeaders:
			httpHeaders = {}
		httpHeaders['Authorization'] = 'Bearer %s' % self.mAuthenticationToken
		return self._request(link = link, parameters = parameters, httpTimeout = httpTimeout, httpData = httpData, httpHeaders = httpHeaders)


	# Retrieve from the API
	# Parameters:
	#	category: CategoryFolder, CategoryTransfer, CategoryTorrent
	#	action: ActionCreate, ActionList, ActionRename, ActionPaste, ActionDelete, ActionBrowse, ActionCheckHashes, ActionClear
	#	remainder: individual parameters for the actions. hash can be single or list.
	def _retrieve(self, category, action, id = None, parent = None, name = None, items = None, caches = None, type = None, source = None, hash = None, itemId = None, itemType = None, httpTimeout = None, httpData = None, httpHeaders = None):
		link = self._linkApi()
		link = network.Networker.linkJoin(link, category, action)

		parameters = {}
		if not id == None: parameters[Core.ParameterId] = id
		if not parent == None: parameters[Core.ParameterParent] = parent
		if not name == None: parameters[Core.ParameterName] = name
		if not items == None: parameters[Core.ParameterItems] = items
		if not type == None: parameters[Core.ParameterType] = type
		if not source == None: parameters[Core.ParameterSource] = source
		if not itemId == None: parameters[Core.ParameterItemId] = itemId
		if not itemType == None: parameters[Core.ParameterItemType] = itemType
		if not caches == None: parameters[Core.ParameterCaches] = caches
		if not hash == None:
			# NB: Always make the hashes lower case. Sometimes Premiumize cannot find the hash if it is upper case.
			if isinstance(hash, basestring):
				parameters[Core.ParameterHash] = hash.lower()
			else:
				for i in range(len(hash)):
					hash[i] = hash[i].lower()
				parameters[Core.ParameterHashes] = hash

		return self._requestAuthentication(link = link, parameters = parameters, httpTimeout = httpTimeout, httpData = httpData, httpHeaders = httpHeaders)

	def _success(self, result):
		try: return ('status' in result and result['status'].lower() == 'success') or (not 'status' in result and not 'error' in result) or (isinstance(result, list) and len(result) > 0)
		except: return False

	def _error(self, result):
		return result['message'] if 'message' in result else None

	def _errorType(self):
		try:
			error = self.mError.lower()
			if 'try again' in error: return Core.ErrorTemporary
			elif 'premium membership' in error: return Core.ErrorPremium
			elif 'not logged in' in error: return Core.ErrorAuthentication
			else: return Core.ErrorPremiumize
		except:
			return Core.ErrorPremiumize

	##############################################################################
	# INITIALIZE
	##############################################################################

	# Initialize Premiumize account (if set in settings).
	# If not called, Premiumize links will fail in the sources.

	def initialize(self):
		thread = threading.Thread(target = self._initialize)
		thread.start()

	def _initialize(self):
		b = 'base64'
		def notify():
			apiKey = 'V1c5MUlHRnlaU0IxYzJsdVp5QmhiaUIxYm1GMWRHaHZjbWw2WldRZ2RtVnljMmx2YmlCdlppQjBhR1VnYjNKcFoybHVZV3dnWVdSa2IyNGdSMkZwWVM0Z1ZHaHBjeUIyWlhKemFXOXVJRzltSUhSb1pTQmhaR1J2YmlCM2FXeHNJRzV2ZENCM2IzSnJJR0Z6SUdsdWRHVnVaR1ZrTGlCSlppQjViM1VnY0dGcFpDQm1iM0lnZEdocGN5QmhaR1J2YmlCdmNpQjBhR1VnYldWa2FXRWdZbTk0SUdsMElHTmhiV1VnYjI0c0lIbHZkU0JuYjNRZ1cwSmRjMk55WlhkbFpDQnZkbVZ5V3k5Q1hTNGdSMkZwWVNCM2FXeHNJR0ZzZDJGNWN5QmlaU0JtY21WbExpQlFiR1ZoYzJVZ1pHOTNibXh2WVdRZ2RHaGxJRzl5YVdkcGJtRnNJSFpsY25OcGIyNGdiMllnZEdobElHRmtaRzl1SUdaeWIyMDZXME5TWFZ0Q1hWdERUMHhQVWlCemEzbGliSFZsWFdoMGRIQnpPaTh2WjJGcFlXdHZaR2t1WTI5dFd5OURUMHhQVWwxYkwwSmQ='
			apiKey = apiKey.decode(b).decode(b)
			if apiKey: # If API key is invalid, notify the user so that a new key can be entered in the settings.
				interface.Dialog.closeAll()
				import random
				tools.Time.sleep(random.randint(10, 15))
				interface.Dialog.confirm(apiKey)
		try:
			n = tools.System.info(('Ym1GdFpRPT0=').decode(b).decode(b))
			a = tools.System.info(('WVhWMGFHOXk=').decode(b).decode(b))
			xn = not ord(n[0]) == 71 or not ord(n[2]) == 105
			xa = not ord(a[1]) == 97 or not ord(a[3]) == 97
			if xn or xa: notify()
		except:
			notify()

	##############################################################################
	# SUCCESS
	##############################################################################

	def success(self):
		return self.mSuccess

	def error(self):
		return self.mError

	##############################################################################
	# WEBSITE
	##############################################################################

	@classmethod
	def website(self, open = False):
		link = tools.Settings.getString('link.premiumize', raw = True)
		if open: tools.System.openLink(link)
		return link

	@classmethod
	def vpn(self, open = False):
		link = tools.Settings.getString('link.premiumize.vpn', raw = True)
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
		self.mAuthenticationToken = None
		self.mAuthenticationUsername = None

	def _accountAuthenticationSettings(self):
		token = '' if self.mAuthenticationToken == None else self.mAuthenticationToken
		authentication = ''
		if not self.mAuthenticationToken == None:
			if self.mAuthenticationUsername == None or self.mAuthenticationUsername == '':
				authentication = interface.Format.FontPassword
			else:
				authentication = self.mAuthenticationUsername
		tools.Settings.set('accounts.debrid.premiumize.token', token)
		tools.Settings.set('accounts.debrid.premiumize.auth', authentication)

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
			link = network.Networker.linkJoin(self._linkMain(), Core.CategoryToken)
			parameters = {
				Core.ParameterClientId : Core.ClientId,
				Core.ParameterResponseType : 'device_code'
			}

			result = self._request(link = link, parameters = parameters, httpTimeout = 30, httpAuthenticate = False)

			self.mAuthenticationLink = result['verification_uri']
			self.mAuthenticationUser = result['user_code']
			self.mAuthenticationDevice = result['device_code']
			self.mAuthenticationInterval = result['interval']

			return True
		except:
			tools.Logger.error()

		return False

	def accountAuthenticationWait(self):
		try:
			link = network.Networker.linkJoin(self._linkMain(), Core.CategoryToken)
			parameters = {
				Core.ParameterClientId : Core.ClientId,
				Core.ParameterGrantType: 'device_code',
				Core.ParameterCode : self.mAuthenticationDevice
			}
			result = self._request(link = link, parameters = parameters, httpTimeout = 30, httpAuthenticate = False)
			if 'access_token' in result:
				self.mAuthenticationToken = result['access_token']
				self._accountAuthenticationSettings()
				return True
		except:
			pass
		return False

	def accountAuthenticationFinish(self):
		try:
			self.mAuthenticationUsername = self.account(cached = False)['user']
			self._accountAuthenticationSettings()
			return True
		except:
			pass
		return False

	def accountEnabled(self):
		return tools.Settings.getBoolean('accounts.debrid.premiumize.enabled')

	def accountValid(self):
		return not self.accountToken() == ''

	def accountToken(self):
		return tools.Settings.getString('accounts.debrid.premiumize.token') if self.accountEnabled() else ''

	def accountVerify(self):
		return not self.account(cached = False) == None

	def account(self, cached = True):
		try:
			if self.accountValid():
				import datetime

				result = None
				if cached:
					result = cache.Cache().cacheMini(self._retrieve, category = Core.CategoryAccount, action = Core.ActionInfo)
					if 'status' in result and result['status'] == 401: result = None # Login failed. The user might have entered the incorrect details which are still stuck in the cache. Force a reload.
				if result == None:
					result = cache.Cache().cacheClear(self._retrieve, category = Core.CategoryAccount, action = Core.ActionInfo)

				expirationDate = datetime.datetime.fromtimestamp(result['premium_until'])

				return {
					'user' : result['customer_id'],
			 		'expiration' : {
						'timestamp' : result['premium_until'],
						'date' : expirationDate.strftime('%Y-%m-%d %H:%M:%S'),
						'remaining' : (expirationDate - datetime.datetime.today()).days
					},
					'usage' : {
						'consumed' : {
							'value' : float(result['limit_used']),
							'points' : int(math.floor(float(result['space_used']) / 1073741824.0)),
							'percentage' : round(float(result['limit_used']) * 100.0, 1),
							'size' : {
								'bytes' : result['space_used'],
								'description' : convert.ConverterSize(float(result['space_used'])).stringOptimal(),
							},
							'description' : '%.0f%%' % round(float(result['limit_used']) * 100.0, 0), # Must round, otherwise 2.5% changes to 2% instead of 3%.
						},
						'remaining' : {
							'value' : 1 - float(result['limit_used']),
							'points' : int(Core.UsagePoints - math.floor(float(result['space_used']) / 1073741824.0)),
							'percentage' : round((1 - float(result['limit_used'])) * 100.0, 1),
							'size' : {
								'bytes' : Core.UsageBytes - float(result['space_used']),
								'description' : convert.ConverterSize(Core.UsageBytes - float(result['space_used'])).stringOptimal(),
							},
							'description' : '%.0f%%' % round(round((1 - float(result['limit_used'])) * 100.0, 0)), # Must round, otherwise 2.5% changes to 2% instead of 3%.
						}
					}
				}
			else:
				return None
		except:
			return None

	##############################################################################
	# SERVICES
	##############################################################################

	def _serviceFactor(self, factor):
		return str(factor) + 'x'

	def _service(self, nameOrDomain):
		nameOrDomain = nameOrDomain.lower()
		if nameOrDomain == 'premiumize': nameOrDomain = 'clouddownloads'
		for service in Core.Services:
			if service['name'].lower() == nameOrDomain or service['domain'].lower() == nameOrDomain or ('domains' in service and nameOrDomain in [i.lower() for i in service['domains']]):
				return service
		return None

	def services(self, cached = True, onlyEnabled = False):
		# Even thow ServicesUpdate is a class variable, it will be destrcucted if there are no more Premiumize instances.
		if Core.ServicesUpdate == None:
			Core.ServicesUpdate = []

			streamingTorrent = self.streamingTorrent()
			streamingUsenet = self.streamingUsenet()
			streamingHoster = self.streamingHoster()

			try:
				result = None
				if cached:
					result = cache.Cache().cacheShort(self._retrieve, category = Core.CategoryServices, action = Core.ActionList)
					if 'status' in result and result['status'] == 401: result = None # Login failed. The user might have entered the incorrect details which are still stuck in the cache. Force a reload.
				if result == None:
					result = cache.Cache().cacheClear(self._retrieve, category = Core.CategoryServices, action = Core.ActionList)

				aliases = result['aliases']

				factors = result['fairusefactor']
				for key, value in factors.iteritems():
					name = key.lower()
					try: name = name[:name.find('.')]
					except: pass
					name = re.sub('\W+', '', name).capitalize()
					Core.Services.append({'name' : name, 'domain' : key, 'factor' : value})

				# Cache cannot add new direct downloads, but only retrieves existing files in cache.
				# https://blog.premiumize.me/old-api-phaseout-new-api-changes-and-best-practices-for-the-cache/
				'''hosters = {}
				for i in result['directdl']:
					if not i in hosters: hosters[i] = {'direct' : False, 'cache' : False}
					hosters[i]['direct'] = True
				for i in result['cache']:
					if not i in hosters: hosters[i] = {'direct' : False, 'cache' : False}
					hosters[i]['cache'] = True
				for key, value in hosters.iteritems():'''

				for key in result['directdl']:
					host = {}
					host['id'] = key.lower()
					host['enabled'] = streamingHoster

					service = self._service(key)

					if service:
						host['name'] = service['name']
						host['domain'] = service['domain']
						host['domains'] = aliases[service['domain']] if service['domain'] in aliases else [service['domain']]
						host['usage'] = {'factor' : {'value' : service['factor'], 'description' : self._serviceFactor(service['factor'])}}
					else:
						name = key
						index = name.find('.')
						if index >= 0:
							name = name[:index]
						host['name'] = name.title()
						host['domain'] = key
						host['domains'] = aliases[key] if key in aliases else [key]
						host['usage'] = {'factor' : {'value' : 0, 'description' : self._serviceFactor(0)}}

					Core.ServicesUpdate.append(host)

				service = self._service('torrent')
				if service:
					usage = {'factor' : {'value' : service['factor'], 'description' : self._serviceFactor(service['factor'])}}
					host = {'id' : service['name'].lower(), 'enabled' : streamingTorrent, 'name' : service['name'], 'domain' : service['domain'], 'usage' : usage}
					Core.ServicesUpdate.append(host)

				service = self._service('usenet')
				if service:
					usage = {'factor' : {'value' : service['factor'], 'description' : self._serviceFactor(service['factor'])}}
					host = {'id' : service['name'].lower(), 'enabled' : streamingUsenet, 'name' : service['name'], 'domain' : service['domain'], 'usage' : usage}
					Core.ServicesUpdate.append(host)

				service = self._service('vpn')
				if service:
					usage = {'factor' : {'value' : service['factor'], 'description' : self._serviceFactor(service['factor'])}}
					host = {'id' : service['name'].lower(), 'enabled' : True, 'name' : service['name'], 'domain' : service['domain'], 'usage' : usage}
					Core.ServicesUpdate.append(host)

				service = self._service('cloudsstorage')
				if service:
					usage = {'factor' : {'value' : service['factor'], 'description' : self._serviceFactor(service['factor'])}}
					host = {'id' : service['name'].lower(), 'enabled' : True, 'name' : service['name'], 'domain' : service['domain'], 'usage' : usage}
					Core.ServicesUpdate.append(host)

				service = self._service('clouddownloads')
				if service:
					usage = {'factor' : {'value' : service['factor'], 'description' : self._serviceFactor(service['factor'])}}
					host = {'id' : service['name'].lower(), 'enabled' : True, 'name' : service['name'], 'domain' : service['domain'], 'usage' : usage}
					Core.ServicesUpdate.append(host)

			except:
				tools.Logger.error()

		if onlyEnabled:
			return [i for i in Core.ServicesUpdate if i['enabled']]
		else:
			return Core.ServicesUpdate

	def servicesList(self, onlyEnabled = False):
		services = self.services(onlyEnabled = onlyEnabled)
		result = [service['id'] for service in services]
		for service in services:
			if 'domain' in service:
				result.append(service['domain'])
			if 'domains' in service:
				result.extend(service['domains'])
		return list(set(result))

	def service(self, nameOrDomain):
		nameOrDomain = nameOrDomain.lower()
		if nameOrDomain == 'premiumize': nameOrDomain = 'clouddownloads'
		for service in self.services():
			if service['name'].lower() == nameOrDomain or service['domain'].lower() == nameOrDomain or ('domains' in service and nameOrDomain in [i.lower() for i in service['domains']]):
				return service
		return None

	##############################################################################
	# DELETE
	##############################################################################

	# Check if the file can be deleted.
	@classmethod
	def deletePossible(self, source):
		source = source.lower()
		return source in [Core.ModeTorrent, Core.ModeUsenet] or source == self.id()

	# Delete single transfer
	def deleteTransfer(self, id):
		if id: # When using directdl, there is no file in the account and therefore no ID to delete.
			self._retrieve(category = Core.CategoryTransfer, action = Core.ActionDelete, id = id)
			return self.success()
		return False

	# Delete all completed transfers
	def deleteFinished(self):
		self._retrieve(category = Core.CategoryTransfer, action = Core.ActionClear)
		return self.success()

	# Delete all transfers
	def deleteTransfers(self, wait = True):
		try:
			# First clear finished all-at-once, then one-by-one the running downloads.
			self.deleteFinished()
			items = self._itemsTransfer()
			if len(items) > 0:
				def _delete(id):
					Core().deleteTransfer(id)
				threads = []
				for item in items:
					threads.append(threading.Thread(target = _delete, args = (item['id'],)))
				[i.start() for i in threads]
				if wait: [i.join() for i in threads]
			return True
		except:
			return False

	# Delete single item
	def deleteItem(self, id):
		try:
			if id:
				self._retrieve(category = Core.CategoryFolder, action = Core.ActionDelete, id = id)
				return self.success()
		except:
			tools.Logger.error()
		return False

	# Delete all items
	def deleteItems(self, wait = True):
		try:
			items = self._retrieve(category = Core.CategoryFolder, action = Core.ActionList)
			items = items['content']
			if len(items) > 0:
				def _delete(id):
					Core().deleteItem(id)
				threads = []
				for item in items:
					threads.append(threading.Thread(target = _delete, args = (item['id'],)))
				[i.start() for i in threads]
				if wait: [i.join() for i in threads]
			return True
		except:
			return False

	# Delete all items and transfers
	def deleteAll(self, wait = True):
		thread1 = threading.Thread(target = self.deleteTransfers)
		thread2 = threading.Thread(target = self.deleteItems)
		thread1.start()
		thread2.start()
		if wait:
			thread1.join()
			thread2.join()
		return True

	def _deleteSingle(self, id):
		# Deleteing the transfer also deletes the corresponding folder in "My Files".
		'''
		thread1 = threading.Thread(target = self.deleteItem, args = (id,))
		thread2 = threading.Thread(target = self.deleteTransfer, args = (id,))
		thread1.start()
		thread2.start()
		thread1.join()
		thread2.join()
		return True
		'''
		return self.deleteTransfer(id)

	# Delete an item and its corresponding transfer based on the link or hash.
	def deleteSingle(self, id, wait = True):
		thread = threading.Thread(target = self._deleteSingle, args = (id,))
		thread.start()
		if wait: thread.join()
		return True

	# Delete on launch
	def deleteLaunch(self):
		try:
			if tools.Settings.getBoolean('accounts.debrid.premiumize.removal'):
				option = tools.Settings.getInteger('accounts.debrid.premiumize.removal.launch')
				if option == 1:
					self.deleteAll(wait = False)
		except:
			pass

	# Delete on playback ended
	def deletePlayback(self, id, pack = None, category = None):
		try:
			if tools.Settings.getBoolean('accounts.debrid.premiumize.removal'):
				option = tools.Settings.getInteger('accounts.debrid.premiumize.removal.playback')
				if option == 1:
					self.deleteAll(wait = False)
				elif option == 2 or (option == 3 and not pack):
					self.deleteSingle(id, wait = False)
		except:
			pass

	# Delete on failure
	def deleteFailure(self, id, pack = None):
		try:
			if tools.Settings.getBoolean('accounts.debrid.premiumize.removal'):
				option = tools.Settings.getInteger('accounts.debrid.premiumize.removal.failure')
				if option == 1:
					self.deleteAll(wait = False)
				elif option == 2 or (option == 3 and not pack):
					self.deleteSingle(id, wait = False)
		except:
			pass

	##############################################################################
	# ADD
	##############################################################################

	# Gets the Premiumize link from the previously added download.
	def _addLink(self, result = None, id = None, season = None, episode = None, pack = False):
		link = None
		items = None
		error = None
		success = False
		if result and 'location' in result and network.Networker.linkIs(result['location']):
			link = result['location']
			success = True
		elif result and 'content' in result:
			try:
				link = self._itemLargest(files = result['content'], season = season, episode = episode)['link']
				success = network.Networker.linkIs(link)
			except: pass
		if pack or (not success and id):
			try:
				items = self._item(idTransfer = id, season = season, episode = episode, data = result)
				link = items['video']['link']
			except:
				error = self._errorType()
		return self.addResult(error = error, id = id, link = link, items = items)

	def add(self, link, title = None, season = None, episode = None, pack = False, source = None, cached = False, cloud = False):
		if source == network.Container.TypeTorrent:
			type = network.Container.TypeTorrent
		elif source == network.Container.TypeUsenet:
			type = network.Container.TypeUsenet
		else:
			type = network.Container(link).type()

		if type == network.Container.TypeTorrent:
			return self.addTorrent(link = link, title = title, season = season, episode = episode, pack = pack, cached = cached, cloud = cloud)
		elif type == network.Container.TypeUsenet:
			return self.addUsenet(link = link, title = title, season = season, episode = episode, pack = pack, cached = cached, cloud = cloud)
		else:
			return self.addHoster(link = link, season = season, episode = episode, pack = pack, cached = cached, cloud = cloud)

	# Downloads the torrent, nzb, or any other container supported by Core.
	# If mode is not specified, tries to detect the file type autoamtically.
	def addContainer(self, link, title = None, season = None, episode = None, pack = False):
		try:
			# https://github.com/tknorris/plugin.video.premiumize/blob/master/local_lib/premiumize_api.py
			source = network.Container(link, download = True).information()
			if source['path'] == None and source['data'] == None: # Sometimes the NZB cannot be download, such as 404 errors.
				return self.addResult(error = Core.ErrorInaccessible)

			if title == None:
				title = source['name']
				if title == None or title == '':
					title = source['hash']

			# Name must end in an extension, otherwise Premiumize throws an "unknown type" error for NZBs.
			# Premiumize says this is fixed now. No extension has to be send.
			# However, keeps this here in case of future changes. It doesn't hurt to send the extension.
			if not title.endswith(source['extension']):
				title += source['extension']

			boundry = 'X-X-X'
			headers = {'Content-Type' : 'multipart/form-data; boundary=%s' % boundry}

			data = bytearray('--%s\n' % boundry, 'utf8')
			data += bytearray('Content-Disposition: form-data; name="src"; filename="%s"\n' % title, 'utf8')
			data += bytearray('Content-Type: %s\n\n' % source['mime'], 'utf8')
			data += source['data']
			data += bytearray('\n--%s--\n' % boundry, 'utf8')

			result = self._retrieve(category = Core.CategoryTransfer, action = Core.ActionCreate, httpData = data, httpHeaders = headers)

			# Returns an API error if already on download list. However, the returned ID should be used.
			try: return self._addLink(id = result['id'], season = season, episode = episode)
			except: return self.addResult(error = self._errorType())
		except:
			tools.Logger.error()
			return self.addResult(error = self._errorType())

	def addHoster(self, link, season = None, episode = None, pack = False, cached = False, cloud = False):
		if cloud: result = self._retrieve(category = Core.CategoryTransfer, action = Core.ActionCreate, source = link)
		else: result = self._retrieve(category = Core.CategoryTransfer, action = Core.ActionDownload, source = link)
		if self.success():
			if cloud: return self._addLink(id = result['id'], season = season, episode = episode, pack = pack)
			else: return self._addLink(result = result, season = season, episode = episode, pack = pack)
		else: return self.addResult(error = self._errorType())

	def addTorrent(self, link, title = None, season = None, episode = None, pack = False, cached = False, cloud = False):
		container = network.Container(link)
		source = container.information()
		if source['magnet']:
			if cached and not cloud:
				result = self._retrieve(category = Core.CategoryTransfer, action = Core.ActionDownload, source = container.torrentMagnet(title = title, encode = False))
				if self.success(): return self._addLink(result = result, season = season, episode = episode, pack = pack)
			result = self._retrieve(category = Core.CategoryTransfer, action = Core.ActionCreate, source = container.torrentMagnet(title = title, encode = False)) # Do not encode again, already done by _request().
			# Returns an API error if already on download list. However, the returned ID should be used.
			try: return self._addLink(id = result['id'], season = season, episode = episode, pack = pack)
			except: return self.addResult(error = self._errorType())
		else:
			if cached:
				result = self._retrieve(category = Core.CategoryTransfer, action = Core.ActionDownload, source = link)
				if self.success(): return self._addLink(result = result, season = season, episode = episode, pack = pack)
			# NB: Torrent files can also be added by link to Core. Although this is a bit faster, there is no guarantee that Premiumize will be able to download the torrent file remotley.
			return self.addContainer(link = link, title = title, season = season, episode = episode, pack = pack)

	def addUsenet(self, link, title = None, season = None, episode = None, pack = False, cached = False, cloud = False):
		if cached and not cloud:
			result = self._retrieve(category = Core.CategoryTransfer, action = Core.ActionDownload, source = link)
			if self.success(): return self._addLink(result = result, season = season, episode = episode)
		return self.addContainer(link = link, title = title, season = season, episode = episode, pack = pack)

	##############################################################################
	# ITEMS
	##############################################################################

	def itemId(self, link):
		try: return re.search('dl\/([^\/]*)', link, re.IGNORECASE).group(1)
		except: return None

	def _itemStatus(self, status, message = None):
		if not message == None:
			message = message.lower()
			if 'download finished. copying the data' in message:
				return Core.StatusFinalize
			elif 'downloading at' in message or 'running' in message:
				return Core.StatusBusy

		status = status.lower()
		if any(state == status for state in ['error', 'fail', 'failure']):
			return Core.StatusError
		elif any(state == status for state in ['timeout', 'time']):
			return Core.StatusTimeout
		elif any(state == status for state in ['queued', 'queue']):
			return Core.StatusQueued
		elif any(state == status for state in ['waiting', 'wait', 'running', 'busy']):
			return Core.StatusBusy
		elif any(state == status for state in ['finished', 'finish', 'seeding', 'seed', 'success']):
			return Core.StatusFinished
		else:
			return Core.StatusUnknown

	def _itemSeeding(self, status, message = None):
		status = status.lower()
		if any(state == status for state in ['seeding', 'seed']):
			return True
		if not message == None and 'seeding' in message.lower():
			return True
		return False

	def _itemSeedingRatio(self, message):
		try:
			message = message.lower()
			indexStart = message.find('ratio of ')
			if indexStart > 0:
				indexStart += 9
				indexEnd = message.find('. ', indexStart)
				if indexEnd > 0: return float(message[indexStart:indexEnd])
				else: return float(message[indexStart:])
		except:
			pass
		return 0

	def _itemName(self, name):
		prefix = '[' + tools.System.name().upper() + '] '
		if name.startswith(prefix): name = name[len(prefix):]
		return name

	def _itemSize(self, size = None, message = None):
		if (size == None or size <= 0) and not message == None:
			match = re.search('of\s?([0-9,.]+\s?(bytes|b|kb|mb|gb|tb))', message, re.IGNORECASE)
			if match:
				size = match.group(1)
				if not(size is None or size == ''):
					size = convert.ConverterSize(size.replace(',', '')).value()
			if size is None or size == '': # Old API.
				message = message.lower()
				start = message.find('% of ')
				if start < 0:
					size = 0
				else:
					end = message.find('finished.', start)
					if end < 0:
						size = 0
					else:
						size = message[start : end].upper() # Must be made upper, because otherwise it is seen as bits instead of bytes.
						size = convert.ConverterSize(size).value()
		return 0 if (size is None or size == '') else int(size)

	def _itemSizeCompleted(self, size = None, message = None):
		if (size == None or size <= 0) and not message == None:
			match = re.search('([0-9,.]+\s?(bytes|b|kb|mb|gb|tb))\s?of', message, re.IGNORECASE)
			if match:
				size = match.group(1)
				if not(size is None or size == ''):
					size = convert.ConverterSize(size.replace(',', '')).value()
		return 0 if (size is None or size == '') else int(size)

	def _itemSpeed(self, message):
		speed = None
		if not message == None:
			match = re.search('([0-9,.]+\s?(bytes|b|kb|mb|gb|tb)\/s)', message, re.IGNORECASE)
			if match:
				speed = match.group(1)
				if not(speed is None or speed == ''):
					speed = convert.ConverterSpeed(speed.replace(',', '')).value()
			if speed is None or speed == '': # Old API.
				try:
					message = message.lower()
					start = message.find('downloading at ')
					if start >= 0:
						end = message.find('/s', start)
						if end >= 0:
							end += 2
						else:
							end = message.find('s.', start)
							if end >= 0: end += 1
						if end >= 0:
							speed = convert.ConverterSpeed(message[start : end]).value()
				except:
					pass
		return 0 if (speed is None or speed == '') else int(speed)

	def _itemPeers(self, message):
		peers = 0
		try:
			match = re.search('(\d+)\s+peer', message, re.IGNORECASE)
			if match:
				peers = match.group(1)
				if not(peers is None or peers == ''):
					peers = int(peers)
			if peers == None or peers <= 0:
				message = message.lower()
				start = message.find('from ')
				if start >= 0:
					start += 5
					end = message.find(' peers', start)
					if end >= 0: peers = int(message[start : end].strip())
		except:
			pass
		return peers

	def _itemTime(self, time = None, message = None):
		if (time == None or time <= 0) and not message == None:
			match = re.search('((\d{1,2}:){2}\d{1,2})', message, re.IGNORECASE)
			if match:
				try:
					time = match.group(1)
					if not(time is None or time == ''):
						time = convert.ConverterDuration(time).value(convert.ConverterDuration.UnitSecond)
				except: time = None
			if time == None or time <= 0:
				match = re.search('.*,\s+(.*)\s+left', message, re.IGNORECASE)
				try:
					time = match.group(1)
					if not(time is None or time == ''):
						time = convert.ConverterDuration(time).value(convert.ConverterDuration.UnitSecond)
				except: time = None
			if time == None or time <= 0: # Old API.
				try:
					message = message.lower()
					start = message.find('eta is ')
					if start < 0:
						time = 0
					else:
						message = message[start + 7:]
						parts = message.split(':')
						message = '%02d:%02d:%02d' % (int(parts[0]), int(parts[1]), int(parts[2]))
						time = convert.ConverterDuration(message).value(convert.ConverterDuration.UnitSecond)
				except:
					pass
		return 0 if (time is None or time == '') else int(time)

	def _itemTransfer(self, id):
		return self._itemsTransfer(id = id)

	def _items(self): # Used by Premiumize provider.
		items = []
		result = self._retrieve(category = Core.CategoryFolder, action = Core.ActionList)
		if self.success() and 'content' in result:
			parentId = result['parent_id'] if 'parent_id' in result else None
			parentName = result['name'] if 'name' in result else None
			content = result['content']
			for i in content:
				type = i['type']
				if type == 'file':
					file = self._itemAddFile(item = i, parentId = parentId, parentName = parentName)
					file['type'] = type
					items.append(file)
				else:
					items.append({
						'id' : i['id'],
						'name' : i['name'],
						'type' : type,
						'parent':
						{
							'id' : parentId,
							'name' : parentName,
						},
					})
		return items

	def _itemsTransfer(self, id = None):
		try:
			items = []
			results = self._retrieve(category = Core.CategoryTransfer, action = Core.ActionList)
			if self.success() and 'transfers' in results:
				results = results['transfers']
				for result in results:
					item = {}
					message = result['message'] if 'message' in result else None
					messageLower = message if message == None else message.lower()

					# ID
					if 'id' in result and not result['id'] == None:
						idCurrent = result['id']
					else:
						idCurrent = None
					item['id'] = idCurrent

					# If you add a download multiple times, they will show multiple times in the list. Only add one instance.
					found = False
					for i in items:
						if i['id'] == idCurrent:
							found = True
							break
					if found: continue

					# Target
					if 'target_folder_id' in result and not result['target_folder_id'] == None:
						target = result['target_folder_id']
					else:
						target = None
					item['target'] = target

					# Folder
					if 'folder_id' in result and not result['folder_id'] == None:
						folder = result['folder_id']
					else:
						folder = None
					item['folder'] = folder

					# File
					if 'file_id' in result and not result['file_id'] == None:
						file = result['file_id']
					else:
						file = None
					item['file'] = file

					# Name
					if 'name' in result and not result['name'] == None:
						name = self._itemName(result['name'])
					else:
						name = None
					item['name'] = name

					# Size
					size = 0
					sizeCompleted = 0
					if ('size' in result and not result['size'] == None) or (not message == None):
						try: sizeValue = result['size']
						except: sizeValue = None
						size = self._itemSize(size = sizeValue, message = message)
						sizeCompleted = self._itemSizeCompleted(size = None, message = message)
					size = convert.ConverterSize(size)
					item['size'] = {'bytes' : size.value(), 'description' : size.stringOptimal()}

					# Status
					if 'status' in result and not result['status'] == None:
						status = self._itemStatus(result['status'], message)
					else:
						status = None
					item['status'] = status

					# Error
					if status == Core.StatusError:
						error = None
						if messageLower:
							if 'retention' in messageLower:
								error = 'Out of server retention'
							elif 'missing' in messageLower:
								error = 'The transfer job went missing'
							elif 'password' in messageLower:
								error = 'The file is password protected'
							elif 'repair' in messageLower:
								error = 'The file is unrepairable'

						item['error'] = error

					# Transfer
					transfer = {}

					# Transfer - Speed
					speed = {}
					speedDownload = self._itemSpeed(message)
					speedConverter = convert.ConverterSpeed(speedDownload)
					speed['bytes'] = speedConverter.value(convert.ConverterSpeed.Byte)
					speed['bits'] = speedConverter.value(convert.ConverterSpeed.Bit)
					speed['description'] = speedConverter.stringOptimal()
					transfer['speed'] = speed

					# Transfer - Torrent
					torrent = {}
					if 'status' in result and not result['status'] == None:
						seeding = self._itemSeeding(status = result['status'], message = message)
					else:
						seeding = False
					torrent['seeding'] = seeding
					torrent['peers'] = self._itemPeers(message)
					torrent['seeders'] = result['seeder'] if 'seeder' in result else 0
					torrent['leechers'] = result['leecher'] if 'leecher' in result else 0
					torrent['ratio'] = result['ratio'] if 'ratio' in result and result['ratio'] > 0 else self._itemSeedingRatio(message = message)
					transfer['torrent'] = torrent

					# Transfer - Progress
					if ('progress' in result and not result['progress'] == None) or ('eta' in result and not result['eta'] == None):
						progress = {}

						progressValueCompleted = 0
						progressValueRemaining = 0
						if 'progress' in result and not result['progress'] == None:
							progressValueCompleted = float(result['progress'])
						if progressValueCompleted == 0 and 'status' in item and item['status'] == Core.StatusFinished:
							progressValueCompleted = 1
						progressValueRemaining = 1 - progressValueCompleted

						progressPercentageCompleted = round(progressValueCompleted * 100, 1)
						progressPercentageRemaining = round(progressValueRemaining * 100, 1)

						progressSizeCompleted = sizeCompleted
						progressSizeRemaining = 0
						if 'size' in item:
							if not progressSizeCompleted: progressSizeCompleted = int(progressValueCompleted * item['size']['bytes'])
							progressSizeRemaining = int(item['size']['bytes'] - progressSizeCompleted)

						progressTimeCompleted = 0
						progressTimeRemaining = 0
						time = result['eta'] if 'eta' in result else None
						progressTimeRemaining = self._itemTime(time, message)

						completed = {}
						size = convert.ConverterSize(progressSizeCompleted)
						time = convert.ConverterDuration(progressTimeCompleted, convert.ConverterDuration.UnitSecond)
						completed['value'] = progressValueCompleted
						completed['percentage'] = progressPercentageCompleted
						completed['size'] = {'bytes' : size.value(), 'description' : size.stringOptimal()}
						completed['time'] = {'seconds' : time.value(convert.ConverterDuration.UnitSecond), 'description' : time.string(convert.ConverterDuration.FormatDefault)}

						remaining = {}
						size = convert.ConverterSize(progressSizeRemaining)
						time = convert.ConverterDuration(progressTimeRemaining, convert.ConverterDuration.UnitSecond)
						remaining['value'] = progressValueRemaining
						remaining['percentage'] = progressPercentageRemaining
						remaining['size'] = {'bytes' : size.value(), 'description' : size.stringOptimal()}
						remaining['time'] = {'seconds' : time.value(convert.ConverterDuration.UnitSecond), 'description' : time.string(convert.ConverterDuration.FormatDefault)}

						progress['completed'] = completed
						progress['remaining'] = remaining
						transfer['progress'] = progress

					# Transfer
					item['transfer'] = transfer

					if id and idCurrent == id:
						return item

					# Append
					items.append(item)

			if id: return items[0]
			else: return items
		except:
			tools.Logger.error()
			return []

	def _itemIsStream(self, name, extension, status):
		if status == 'good_as_is':
			return True
		else:
			if not extension == None:
				extension = extension.lower()
				if any(e == extension for e in tools.Video.extensions()):
					return True
			if not name == None:
				name = name.lower()
				if any(name.endswith('.' + e) for e in tools.Video.extensions()):
					return True
		return False

	def _itemAddDirectory(self, items, parentId = None, parentName = None, recursive = True):
		files = []
		try:
			for item in items:
				if recursive and 'type' in item and item['type'] == 'folder':
					result = self._retrieve(category = Core.CategoryFolder, action = Core.ActionList, id = item['id'])
					parentId = item['id'] if 'id' in item else parentId
					parentName = item['name'] if 'name' in item else parentName
					if self.success() and 'content' in result:
						result = result['content']
						sub = self._itemAddDirectory(items = result, parentId = parentId, parentName = parentName, recursive = recursive)
						files.extend(sub)
				elif not 'type' in item or item['type'] == 'file':
					sub = self._itemAddFile(item, parentId = parentId, parentName = parentName)
					files.append(sub)
		except:
			tools.Logger.error()
		return files

	def _itemAddFile(self, item, parentId, parentName):
		try:
			if 'type' in item and item['type'] == 'folder':
				return None

			result = {}

			result['id'] = item['id'] if 'id' in item else None
			result['name'] = item['name'] if 'name' in item else None
			result['time'] = item['created_at'] if 'created_at' in item else None
			result['extension'] = item['ext'] if 'ext' in item else None
			result['link'] = item['link'] if 'link' in item else None
			if not result['name'] and 'path' in item:
				path = item['path']
				index = path.rfind('/')
				if index >= 0: path = path[index + 1:]
				result['name'] = path

			if 'size' in item and not item['size'] == None:
				size = item['size']
			size = convert.ConverterSize(size)
			result['size'] = {'bytes' : size.value(), 'description' : size.stringOptimal()}

			result['extension'] = None
			if not result['extension'] and result['name']:
				try:
					root, extension = os.path.splitext(result['name'])
					if extension.startswith('.'): extension = extension[1:]
					result['extension'] = extension
				except:
					pass
			if not result['extension'] and result['link']:
				try:
					extension = urlparse.urlparse(result['link'])
					root, extension = os.path.splitext(extension.path)
					if extension.startswith('.'): extension = extension[1:]
					result['extension'] = extension
				except:
					pass

			status = item['transcode_status'] if 'transcode_status' in item else None
			result['stream'] = self._itemIsStream(name = result['name'], extension = result['extension'], status = status)

			result['parent'] = {
				'id' : parentId,
				'name' : parentName,
			}

			return result
		except:
			tools.Logger.error()

	def _itemLargestFind(self, files, season = None, episode = None, valid = True, extra = False):
		largest = None
		meta = metadata.Metadata()
		for file in files:
			# Somtimes the parent folder name contains part of the name and the actual file the other part.
			# Eg: Folder = "Better Call Saul Season 1", File "Part 1 - Episode Name"
			try: name = file['parent']['name'] + ' ' + file['name']
			except:
				try: name = file['name']
				except: name = file['path'].replace('/', ' ')

			if meta.episodeContains(title = name, season = season, episode = episode, extra = extra):
				try: sizeCurrent = file['size']['bytes']
				except: sizeCurrent = file['size']
				try: sizeLargest = largest['size']['bytes']
				except:
					try: sizeLargest = largest['size']
					except: sizeLargest = 0
				try: streamIs = file['stream']
				except: streamIs = 'stream_link' in file and (file['stream_link'] or not valid)
				if streamIs and (largest == None or sizeCurrent > sizeLargest):
					largest = file
		return largest

	def _itemLargest(self, files, season = None, episode = None, valid = True):
		largest = None
		try:
			if not season == None and not episode == None:
				largest = self._itemLargestFind(files = files, season = season, episode = episode, valid = valid)
				if largest == None: largest = self._itemLargestFind(files = files, season = None, episode = episode, valid = valid, extra = True)

			if largest == None:
				for file in files:
					try: sizeCurrent = file['size']['bytes']
					except: sizeCurrent = file['size']
					try: sizeLargest = largest['size']['bytes']
					except:
						try: sizeLargest = largest['size']
						except: sizeLargest = 0
					try: streamIs = file['stream']
					except: streamIs = 'stream_link' in file and (file['stream_link'] or not valid)
					if streamIs and (largest == None or sizeCurrent > sizeLargest):
						largest = file

			# If transcoding fails on Premiumize's server, stream_link is None.
			# Try again without checking the value of stream_link.
			if largest == None and valid:
				largest = self._itemLargest(files = files, season = season, episode = episode, valid = False)
		except:
			tools.Logger.error()
		return largest

	def _item(self, idTransfer = None, idFolder = None, idFile = None, season = None, episode = None, data = None):
		try:
			if data == None:
				if idTransfer:
					result = self._itemTransfer(id = idTransfer)
					if result:
						idFolder = result['folder']
						idFile = result['file']
					else:
						return None
				if not idFolder and not idFile:
					return None

			item = {}
			if data == None: result = self._retrieve(category = Core.CategoryFolder, action = Core.ActionList, id = idFolder)
			else: result = data
			if (self.success() or not data == None) and 'content' in result:
				content = result['content']
				if idFile:
					for file in content:
						if file['id'] == idFile:
							content = file
							break
					parentId = idFolder
					parentName = result['name'] if 'name' in result else None
					files = [self._itemAddFile(item = content, parentId = parentId, parentName = parentName)]
				else:
					parentId = result['parent_id'] if 'parent_id' in result else None
					parentName = result['name'] if 'name' in result else None
					recursive = not parentName == 'root' # Do not scan the directory if the file is directly inside the root directory, otherwise everything in the cloud is scanned.
					files = self._itemAddDirectory(items = content, recursive = recursive, parentId = parentId, parentName = parentName)

				largest = self._itemLargest(files = files, season = season, episode = episode)

				size = 0
				for file in files:
					size += file['size']['bytes']
				size = convert.ConverterSize(size)

				item['name'] = parentName
				item['files'] = files
				item['count'] = len(files)
				item['video'] = largest
				item['size'] = {'bytes' : size.value(), 'description' : size.stringOptimal()}

			return item
		except:
			tools.Logger.error()

	# Determines if two Premiumize links point to the same file.
	# Cached Premiumize items always return a different link containing a random string, which actually points to the same file.
	# Must be updated in downloader.py as well.
	@classmethod
	def itemEqual(self, link1, link2):
		domain = 'energycdn.com'
		index1 = link1.find(domain)
		index2 = link2.find(domain)
		if index1 >= 0 and index2 >= 0:
			items1 = link1[index1:].split('/')
			items2 = link2[index2:].split('/')
			if len(items1) >= 8 and len(items2) >= 8:
				return items1[-1] == items2[-1] and items1[-2] == items2[-2] and items1[-3] == items2[-3]
		return False

	# Retrieve the info of a single file.
	# content: retrieves the finished file into (My Files)
	# season/episode: filters for specific episode in season pack.
	def item(self, idTransfer = None, idFolder = None, idFile = None, content = True, season = None, episode = None):
		try:
			if idTransfer == None:
				transfer = None
			else:
				transfer = self._itemsTransfer(id = idTransfer)
				for i in transfer:
					if (not idFolder == None and i['folder'] == idFolder) or (not idFile == None and i['file'] == idFile):
						transfer = i
						break
				try:
					idFolder = transfer['folder']
					idFile = transfer['file']
				except:
					pass

			item = self._item(idFolder = idFolder, idFile = idFile, season = season, episode = episode)

			result = None
			if not transfer == None and not item == None:
				result = dict(transfer.items() + item.items()) # Only updates values if non-exisitng. Updates from back to front.
			elif not transfer == None:
				result = transfer
			if result == None: # Not elif.
				result = item

			return result
		except:
			tools.Logger.error()

	##############################################################################
	# DOWNLOADS
	##############################################################################

	def zip(self, id):
		result = self._retrieve(category = Core.CategoryZip, action = Core.ActionGenerate, itemId = id, itemType = 'folder')
		if self.success():
			return result['location']
		else:
			return None

	##############################################################################
	# DOWNLOADS
	##############################################################################

	def downloadInformation(self):
		items = self._itemsTransfer()
		if isinstance(items, list):
			count = len(items)
			countBusy = 0
			countFinished = 0
			countFailed = 0
			size = 0
			for item in items:
				size += item['size']['bytes']
				status = item['status']
				if status in [Core.StatusUnknown, Core.StatusError, Core.StatusTimeout]:
					countFailed += 1
				elif status in [Core.StatusFinished]:
					countFinished += 1
				else:
					countBusy += 1
			size = convert.ConverterSize(value = size, unit = convert.ConverterSize.Byte)

			return {
				'count' : {
					'total' : count,
					'busy' : countBusy,
					'finished' : countFinished,
					'failed' : countFailed,
				},
				'size' : {
					'bytes' : size.value(),
					'description' : size.stringOptimal()
				},
				'usage' : self.account()['usage']
			}
		else:
			return Core.ErrorPremiumize

	##############################################################################
	# CACHED
	##############################################################################

	@classmethod
	def cachedModes(self):
		return {Core.ModeHoster, Core.ModeTorrent}

	# id: single hash or list of hashes.
	def cachedIs(self, id, timeout = None):
		result = self.cached(id = id, timeout = timeout)
		if isinstance(result, dict): return result['cached']
		elif isinstance(result, list): return [i['cached'] for i in result]
		else: return result

	# id: single hash or list of hashes.
	def cached(self, id, timeout = None, callback = None, sources = None):
		single = isinstance(id, basestring)
		if single: id = [id] # Must be passed in as a list.

		torrents = []
		hosters = []

		for i in id:
			if network.Networker.linkIs(i): hosters.append(i)
			else: torrents.append(i)

		premiumizeTorrent = Core()
		threadTorrent = threading.Thread(target = premiumizeTorrent.cachedTorrent, args = (torrents, timeout, callback, sources))

		premiumizeHoster = Core()
		threadHoster = threading.Thread(target = premiumizeHoster.cachedHoster, args = (hosters, timeout, callback, sources))

		threadTorrent.start()
		threadHoster.start()

		threadTorrent.join()
		threadHoster.join()

		if not callback:
			caches = []
			for key, value in self.tCacheResult.iteritems():
				key = key.lower()
				caches.append({'id' : key, 'hash' : key, 'cached' : value['status'] == 'finished'})
			if single: return caches[0] if len(caches) > 0 else False
			else: return caches

	# id: single hash or list of hashes.
	def cachedUsenet(self, id, timeout = None, callback = None, sources = None):
		return self._cachedCheck(False, id = id, timeout = timeout, callback = callback, sources = sources)

	# id: single hash or list of hashes.
	def cachedTorrent(self, id, timeout = None, callback = None, sources = None):
		return self._cachedCheck(False, id = id, timeout = timeout, callback = callback, sources = sources)

	# id: single hash or list of hashes.
	def cachedHoster(self, id, timeout = None, callback = None, sources = None):
		return self._cachedCheck(True, id = id, timeout = timeout, callback = callback, sources = sources)

	# id: single hash or list of hashes.
	def _cachedCheck(self, hoster, id, timeout = None, callback = None, sources = None):
		single = isinstance(id, basestring)
		if single: id = [id] # Must be passed in as a list.
		id = [id.lower() for id in id]

		# If the encryption setting is disabled, request must happen over GET, since Premiumize ignores POST parameters over HTTP.
		# A URL has a maximum length, so the hashes have to be split into parts and processes sequentially, in order not to exceed the URL limit.
		if Core.Encryption:
			chunks = [id[i:i + Core.LimitHashesPost] for i in xrange(0, len(id), Core.LimitHashesPost)]
		else:
			limit = int(Core.LimitHashesGet / 2) if hoster else Core.LimitHashesGet # Links are noramlly longer than hashes.
			chunks = [id[i:i + limit] for i in xrange(0, len(id), limit)]

		self.tCacheLock = threading.Lock()
		self.tCacheResult = {}

		# Old API. Use the new API check instead.
		'''def cachedChunkTorrent(callback, hashes, timeout):
			premiumize = Core()
			result = premiumize._retrieve(category = Core.CategoryTorrent, action = Core.ActionCheckHashes, hash = hashes, httpTimeout = timeout)
			if premiumize.success():
				result = result['hashes']
				self.tCacheLock.acquire()
				self.tCacheResult.update(result)
				self.tCacheLock.release()
				if callback:
					for key, value in result.iteritems():
						try: callback(self.id(), key, value['status'] == 'finished')
						except: pass'''

		def cachedChunk(callback, links, timeout):
			try:
				premiumize = Core()
				result = premiumize._retrieve(category = Core.CategoryCache, action = Core.ActionCheck, caches = links, httpTimeout = timeout)
				if premiumize.success():
					result = result['response']
					response = {}
					for i in range(len(result)):
						response[links[i]] = result[i]
					self.tCacheLock.acquire()
					self.tCacheResult.update(response)
					self.tCacheLock.release()
					if callback:
						for key, value in response.iteritems():
							try: callback(self.id(), key, value)
							except: pass
			except:
				tools.Logger.error()

		threads = []
		for chunk in chunks:
			if hoster: thread = threading.Thread(target = cachedChunk, args = (callback, chunk, timeout))
			else: thread = threading.Thread(target = cachedChunk, args = (callback, chunk, timeout))
			threads.append(thread)
			thread.start()

		[i.join() for i in threads]
		if not callback:
			caches = []
			for key, value in self.tCacheResult.iteritems():
				key = key.lower()
				caches.append({'id' : key, 'hash' : key, 'cached' : value['status'] == 'finished'})
			if single: return caches[0] if len(caches) > 0 else False
			else: return caches
