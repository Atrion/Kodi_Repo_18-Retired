# -*- coding: utf-8 -*-

'''
	Orion
    https://orionoid.com

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

##############################################################################
# ORIONNETWORKER
##############################################################################
# Class for making network requests.
##############################################################################

import ssl
import random

try: from urllib.parse import urlencode
except: from urllib import urlencode

try: from urllib.request import urlopen
except: from urllib2 import urlopen

try: from urllib.request import Request
except: from urllib2 import Request

try: from urllib.error import HTTPError
except: from urllib2 import HTTPError

try: from urllib.error import URLError
except: from urllib2 import URLError

from orion.modules.oriontools import *
from orion.modules.orionplatform import *

class OrionNetworker:

	##############################################################################
	# CONSTANTS
	##############################################################################

	Timeout = 30

	AgentOrion = 0
	AgentDesktopFixed = 1
	AgentDesktopRandom = 2
	AgentMobileFixed = 3
	AgentMobileRandom = 4

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, link = None, parameters = None, timeout = Timeout, agent = AgentOrion, debug = True, json = False):
		self.mDebug = debug
		self.mLink = link if OrionTools.isString(link) else ''
		self.mParameters = parameters
		self.mTimeout = timeout
		self.mAgent = self.userAgent(agent)
		self.mFrom = self.userFrom(agent)
		self.mError = False
		self.mJson = json
		self.mErrorCode = None
		self.mStatus = None
		self.mHeaders = None
		self.mResponse = None

	##############################################################################
	# LINK
	##############################################################################

	@classmethod
	def userAgent(self, type = AgentOrion):
		if type == OrionNetworker.AgentOrion:
			return OrionPlatform.agent()
		elif type == OrionNetworker.AgentDesktopFixed:
			return 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'
		elif type == OrionNetworker.AgentDesktopRandom:
			browserVersions = [['%s.0' % i for i in xrange(18, 43)], ['37.0.2062.103', '37.0.2062.120', '37.0.2062.124', '38.0.2125.101', '38.0.2125.104', '38.0.2125.111', '39.0.2171.71', '39.0.2171.95', '39.0.2171.99', '40.0.2214.93', '40.0.2214.111', '40.0.2214.115', '42.0.2311.90', '42.0.2311.135', '42.0.2311.152', '43.0.2357.81', '43.0.2357.124', '44.0.2403.155', '44.0.2403.157', '45.0.2454.101', '45.0.2454.85', '46.0.2490.71', '46.0.2490.80', '46.0.2490.86', '47.0.2526.73', '47.0.2526.80'], ['11.0']]
			windowsVersions = ['Windows NT 10.0', 'Windows NT 7.0', 'Windows NT 6.3', 'Windows NT 6.2', 'Windows NT 6.1', 'Windows NT 6.0', 'Windows NT 5.1', 'Windows NT 5.0']
			features = ['; WOW64', '; Win64; IA64', '; Win64; x64', '']
			agents = ['Mozilla/5.0 ({windowsVersion}{feature}; rv:{browserVersion}) Gecko/20100101 Firefox/{browserVersion}', 'Mozilla/5.0 ({windowsVersion}{feature}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{browserVersion} Safari/537.36', 'Mozilla/5.0 ({windowsVersion}{feature}; Trident/7.0; rv:{browserVersion}) like Gecko']
			index = random.randrange(len(agents))
			return agents[index].format(windowsVersion = random.choice(windowsVersions), feature = random.choice(features), browserVersion = random.choice(browserVersions[index]))
		elif type == OrionNetworker.AgentMobileFixed:
			return 'Mozilla/5.0 (Linux; Android 6.0.1; SM-G920V Build/MMB29K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.98 Mobile Safari/537.36'
		elif type == OrionNetworker.AgentMobileRandom:
			agents = ['Mozilla/5.0 (Linux; Android 6.0.1; SM-G920V Build/MMB29K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.98 Mobile Safari/537.36', 'Apple-iPhone/701.341', 'Mozilla/5.0 (Linux; U; Android 4.0.3; ko-kr; LG-L160L Build/IML74K) AppleWebkit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30', 'Mozilla/5.0 (Linux; Android 7.0; Pixel C Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/52.0.2743.98 Safari/537.36']
			return random.choice(agents)
		else:
			return None

	@classmethod
	def userFrom(self, type = AgentOrion):
		if type == OrionNetworker.AgentOrion:
			return OrionTools.hash(OrionTools.addonId(id = False))
		else:
			return None

	##############################################################################
	# LINK
	##############################################################################

	def link(self):
		return self.mLink

	##############################################################################
	# ERROR
	##############################################################################

	def error(self):
		return self.mError

	def errorCode(self):
		return self.mErrorCode

	##############################################################################
	# STATUS
	##############################################################################

	def status(self):
		return self.mStatus

	##############################################################################
	# RESPONSE
	##############################################################################

	def response(self):
		return self.mResponse

	##############################################################################
	# HEADERS
	##############################################################################

	def headers(self):
		return self.mHeaders

	##############################################################################
	# REQUEST
	##############################################################################

	def request(self, link = None, parameters = None, timeout = None, agent = None, json = None):
		try:
			if link is None: link = self.mLink
			if parameters is None: parameters = self.mParameters
			if timeout is None: timeout = self.mTimeout
			if json is None: json = self.mJson
			self.mError = False
			self.mErrorCode = None
			self.mResponse = None
			self.mHeaders = None
			self.mStatus = None
			jsonRequest = False
			if self.mLink:
				try:
					if OrionTools.pythonOld():
						if OrionTools.isDictionary(parameters):
							for key, value in OrionTools.iterator(parameters):
								if OrionTools.isStructure(value):
									jsonRequest = True
									break
						if jsonRequest: parameters = OrionTools.jsonTo(parameters)
						elif not OrionTools.isString(parameters): parameters = urlencode(parameters, doseq = True)
					else:
						if OrionTools.isDictionary(parameters):
							jsonRequest = True
							parameters = bytes(OrionTools.jsonTo(parameters), 'utf-8')
						elif not OrionTools.isString(parameters):
							parameters = urlencode(parameters, doseq = True)
				except: pass

				request = Request(self.mLink, data = parameters)

				if agent:
					self.mAgent = self.userAgent(agent)
					self.mFrom = self.userFrom(agent)
				if self.mAgent: request.add_header('User-Agent', self.mAgent)
				if self.mFrom: request.add_header('From', self.mFrom)
				if jsonRequest: request.add_header('Content-Type', 'application/json')

				try:
					self.mResponse = urlopen(request, timeout = timeout)
				except Exception as error:
					# SPMC (Python < 2.7.8) does not support TLS. Try to do it wihout SSL/TLS, otherwise bad luck.
					message = OrionTools.unicodeString(error).lower()
					if 'ssl' in message or 'cert' in message:
						if self.mDebug: OrionTools.error()
						secureContext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
						self.mResponse = urlopen(request, context = secureContext, timeout = timeout)
					else:
						raise error

			try: self.mHeaders = self.mResponse.info().dict
			except: pass
			try: self.mStatus = self.mResponse.getcode()
			except: pass
			result = self.mResponse.read()
			self.mResponse.close()
			if json: result = OrionTools.jsonFrom(result)
			return result
		except HTTPError as error:
			self.mError = True
			self.mErrorCode = error.code
			if self.mDebug: OrionTools.error('Network HTTP Error (' + OrionTools.unicodeString(self.mErrorCode) + '): ' + OrionTools.unicodeString(self.mLink))
		except URLError as error:
			self.mError = True
			self.mErrorCode = error.args
			if self.mDebug: OrionTools.error('Network URL Error (' + OrionTools.unicodeString(self.mErrorCode) + '): ' + OrionTools.unicodeString(self.mLink))
		except:
			self.mError = True
			self.mErrorCode = None
			if self.mDebug: OrionTools.error()
		return None
