# -*- coding: utf-8 -*-

"""
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
"""

##############################################################################
# ORIONAPI
##############################################################################
# API connection and queries to the Orion server
##############################################################################

import copy
from orion.modules.oriontools import *
from orion.modules.orionsettings import *
from orion.modules.orioninterface import *
from orion.modules.orionnetworker import *

class OrionApi:

	##############################################################################
	# CONSTANTS
	##############################################################################

	# Used by OrionSettings.
	# Determines which API results to not show a notification for.
	TypesNonessential = ['exception', 'success', 'streammissing']
	TypesBlock = ['streamvoteabuse', 'streamremoveabuse']

	IgnoreExcludes = ['alluc', 'alluc.ee', 'prontv', 'pron.tv', 'llucy', 'llucy.net']

	SuccessStreamVote = 'streamvote'
	SuccessStreamRemove = 'streamremove'

	ParameterMode = 'mode'
	ParameterAction = 'action'
	ParameterKeyApp = 'keyapp'
	ParameterKeyUser = 'keyuser'
	ParameterKey = 'key'
	ParameterId = 'id'
	ParameterEmail = 'email'
	ParameterPassword = 'password'
	ParameterLink = 'link'
	ParameterResult = 'result'
	ParameterQuery = 'query'
	ParameterStatus = 'status'
	ParameterType = 'type'
	ParameterItem = 'item'
	ParameterStream = 'stream'
	ParameterType = 'type'
	ParameterDescription = 'description'
	ParameterMessage = 'message'
	ParameterData = 'data'
	ParameterCount = 'count'
	ParameterFiltered = 'filtered'
	ParameterTotal = 'total'
	ParameterTime = 'time'
	ParameterDirection = 'direction'
	ParameterVersion = 'version'
	ParameterAll = 'all'

	StatusUnknown = 'unknown'
	StatusBusy = 'busy'
	StatusSuccess = 'success'
	StatusError = 'error'

	ModeStream = 'stream'
	ModeApp = 'app'
	ModeUser = 'user'
	ModeNotification = 'notification'
	ModeServer = 'server'
	ModeFlare = 'flare'

	ActionUpdate = 'update'
	ActionRetrieve = 'retrieve'
	ActionAnonymous = 'anonymous'
	ActionLogin = 'login'
	ActionRemove = 'remove'
	ActionVote = 'vote'
	ActionTest = 'test'

	TypeMovie = 'movie'
	TypeShow = 'show'

	StreamTorrent = 'torrent'
	StreamUsenet = 'usenet'
	StreamHoster = 'hoster'

	AudioStandard = 'standard'
	AudioDubbed = 'dubbed'

	SubtitleSoft = 'soft'
	SubtitleHard = 'hard'

	VoteUp = 'up'
	VoteDown = 'down'

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		self.mStatus = None
		self.mType = None
		self.mDescription = None
		self.mMessage = None
		self.mData = None

	##############################################################################
	# DESTRUCTOR
	##############################################################################

	def __del__(self):
		pass

	##############################################################################
	# INTERNAL
	##############################################################################

	@classmethod
	def _keyInternal(self):
		return OrionSettings.getString('internal.api.orion', raw = True, obfuscate = True)

	def _logMessage(self):
		result = []
		if not self.mStatus == None: result.append(self.mStatus)
		if not self.mType == None: result.append(self.mType)
		if not self.mDescription == None: result.append(self.mDescription)
		if not self.mMessage == None: result.append(self.mMessage)
		return ' | '.join(result)

	##############################################################################
	# REQUEST
	##############################################################################

	def _request(self, mode = None, action = None, parameters = {}, raw = False, silent = False):
		self.mStatus = None
		self.mType = None
		self.mDescription = None
		self.mMessage = None
		self.mData = None

		data = None
		networker = None

		try:
			if not mode == None: parameters[OrionApi.ParameterMode] = mode
			if not action == None: parameters[OrionApi.ParameterAction] = action

			from orion.modules.orionapp import OrionApp
			keyApp = OrionApp.instance().key()
			if keyApp == None and mode == OrionApi.ModeApp and action == OrionApi.ActionRetrieve: keyApp = self._keyInternal()
			if not keyApp == None and not keyApp == '': parameters[OrionApi.ParameterKeyApp] = keyApp

			from orion.modules.orionuser import OrionUser
			keyUser = OrionUser.instance().key()
			if not keyUser == None and not keyUser == '': parameters[OrionApi.ParameterKeyUser] = keyUser

			if not OrionSettings.silent():
				query = copy.deepcopy(parameters)
				if query:
					truncate = [OrionApi.ParameterId, OrionApi.ParameterKey, OrionApi.ParameterKeyApp, OrionApi.ParameterKeyUser, OrionApi.ParameterData]
					for key, value in query.iteritems():
						if key in truncate: query[key] = '-- truncated --'
				OrionTools.log('ORION API REQUEST: ' + OrionTools.jsonTo(query))

			networker = OrionNetworker(
				link = OrionTools.linkApi(),
				parameters = parameters,
				timeout = max(30, OrionSettings.getInteger('general.scraping.timeout')),
				agent = OrionNetworker.AgentOrion,
				debug = not OrionSettings.silent()
			)
			data = networker.request()
			if raw: return {'status' : networker.status(), 'headers' : networker.headers(), 'body' : data, 'response' : networker.response()}
			json = OrionTools.jsonFrom(data)

			result = json[OrionApi.ParameterResult]
			if OrionApi.ParameterStatus in result: self.mStatus = result[OrionApi.ParameterStatus]
			if OrionApi.ParameterType in result: self.mType = result[OrionApi.ParameterType]
			if OrionApi.ParameterDescription in result: self.mDescription = result[OrionApi.ParameterDescription]
			if OrionApi.ParameterMessage in result: self.mMessage = result[OrionApi.ParameterMessage]

			if OrionApi.ParameterData in json: self.mData = json[OrionApi.ParameterData]

			if self.mStatus == OrionApi.StatusError:
				if not OrionSettings.silent():
					OrionTools.log('ORION API ERROR: ' + self._logMessage())
				if not silent and OrionSettings.silentAllow(self.mType):
					OrionInterface.dialogNotification(title = 32048, message = self.mDescription, icon = OrionInterface.IconError)
			elif self.mStatus == OrionApi.StatusSuccess:
				if not OrionSettings.silent():
					OrionTools.log('ORION API SUCCESS: ' + self._logMessage())
				if not silent and OrionSettings.silentAllow(self.mStatus):
					if self.mType == OrionApi.SuccessStreamVote:
						OrionInterface.dialogNotification(title = 32202, message = 33029, icon = OrionInterface.IconSuccess)
					elif self.mType == OrionApi.SuccessStreamRemove:
						OrionInterface.dialogNotification(title = 32203, message = 33030, icon = OrionInterface.IconSuccess)
					else:
						try:
							if self.mData and OrionApi.ParameterCount in self.mData:
								count = self.mData[OrionApi.ParameterCount]
								message = OrionTools.translate(32062) + ': ' + str(count[OrionApi.ParameterTotal]) + ' • ' + OrionTools.translate(32063) + ': ' + str(count[OrionApi.ParameterFiltered])
								OrionTools.log('ORION STREAMS FOUND: ' + message)
								OrionInterface.dialogNotification(title = 32060, message = message, icon = OrionInterface.IconSuccess)
						except: pass
		except:
			try:
				self.mStatus = OrionApi.StatusError
				if not networker == None and networker.error() and not silent and not OrionSettings.silent():
					OrionInterface.dialogNotification(title = 32064, message = 33007, icon = OrionInterface.IconError)
				else:
					if not OrionSettings.silent():
						OrionTools.error('ORION API EXCEPTION')
						OrionTools.log('ORION API DATA: ' + str(data))
					if not silent and OrionSettings.silentAllow('exception'):
						OrionInterface.dialogNotification(title = 32061, message = 33006, icon = OrionInterface.IconError)
			except:
				OrionTools.error('ORION UNKNOWN API EXCEPTION')

		return self.statusSuccess()

	##############################################################################
	# STATUS
	##############################################################################

	def status(self):
		return self.mStatus

	def statusHas(self):
		return not self.mStatus == None

	def statusSuccess(self):
		return self.mStatus == OrionApi.StatusSuccess

	def statusError(self):
		return self.mStatus == OrionApi.StatusError

	##############################################################################
	# TYPE
	##############################################################################

	def type(self):
		return self.mType

	def typeHas(self):
		return not self.mType == None

	##############################################################################
	# DESCRIPTION
	##############################################################################

	def description(self):
		return self.mDescription

	def descriptionHas(self):
		return not self.mDescription == None

	##############################################################################
	# MESSAGE
	##############################################################################

	def message(self):
		return self.mMessage

	def messageHas(self):
		return not self.mMessage == None

	##############################################################################
	# DATA
	##############################################################################

	def data(self):
		return self.mData

	def dataHas(self):
		return not self.mData == None

	##############################################################################
	# RANGE
	##############################################################################

	@classmethod
	def range(self, value):
		if OrionTools.isArray(value):
			result = ''
			if len(value) == 0: return result
			if len(value) > 1 and not value[0] == None: result += str(value[0])
			result += '_'
			if len(value) > 1 and not value[1] == None: result += str(value[1])
			else: result += str(value[0])
			return result
		else:
			return str(value)

	##############################################################################
	# APP
	##############################################################################

	def appRetrieve(self, id = None, key = None):
		single = False
		if not id == None:
			single = OrionTools.isString(id)
			result = self._request(mode = OrionApi.ModeApp, action = OrionApi.ActionRetrieve, parameters = {OrionApi.ParameterId : id})
		elif not key == None:
			single = OrionTools.isString(key)
			result = self._request(mode = OrionApi.ModeApp, action = OrionApi.ActionRetrieve, parameters = {OrionApi.ParameterKey : key})
		else:
			result = self._request(mode = OrionApi.ModeApp, action = OrionApi.ActionRetrieve, parameters = {OrionApi.ParameterAll : True})
		try:
			if single: self.mData = self.mData[0]
			elif OrionTools.isDictionary(self.mData): self.mData = [self.mData]
		except: pass
		return result

	##############################################################################
	# USER
	##############################################################################

	def userRetrieve(self):
		return self._request(mode = OrionApi.ModeUser, action = OrionApi.ActionRetrieve)

	def userLogin(self, email, password):
		return self._request(mode = OrionApi.ModeUser, action = OrionApi.ActionLogin, parameters = {OrionApi.ParameterEmail : email, OrionApi.ParameterPassword : password})

	def userAnonymous(self):
		x = [OrionTools.randomInteger(1,9) for i in range(3)]
		return self._request(mode = OrionApi.ModeUser, action = OrionApi.ActionAnonymous, parameters = {OrionApi.ParameterKey : str(str(x[0])+str(x[1])+str(x[2])+str(x[0]+x[1]*x[2]))[::-1]})

	##############################################################################
	# STREAM
	##############################################################################

	def streamRetrieve(self, filters):
		return self._request(mode = OrionApi.ModeStream, action = OrionApi.ActionRetrieve, parameters = {OrionApi.ParameterData : filters})

	def streamUpdate(self, item):
		return self._request(mode = OrionApi.ModeStream, action = OrionApi.ActionUpdate, parameters = {OrionApi.ParameterData : item})

	def streamVote(self, item, stream, vote = VoteUp, silent = True):
		return self._request(mode = OrionApi.ModeStream, action = OrionApi.ActionVote, parameters = {OrionApi.ParameterItem : item, OrionApi.ParameterStream : stream, OrionApi.ParameterDirection : vote}, silent = silent)

	def streamRemove(self, item, stream, silent = True):
		return self._request(mode = OrionApi.ModeStream, action = OrionApi.ActionRemove, parameters = {OrionApi.ParameterItem : item, OrionApi.ParameterStream : stream}, silent = silent)

	##############################################################################
	# NOTIFICATION
	##############################################################################

	def notificationRetrieve(self, time = None):
		parameters = {}
		parameters[OrionApi.ParameterVersion] = OrionTools.addonVersion()
		if not time == None: parameters[OrionApi.ParameterTime] = time
		return self._request(mode = OrionApi.ModeNotification, action = OrionApi.ActionRetrieve, parameters = parameters)

	##############################################################################
	# SERVER
	##############################################################################

	def serverRetrieve(self, time = None):
		parameters = {}
		if not time == None: parameters[OrionApi.ParameterTime] = time
		return self._request(mode = OrionApi.ModeServer, action = OrionApi.ActionRetrieve, parameters = parameters)

	def serverTest(self):
		return self._request(mode = OrionApi.ModeServer, action = OrionApi.ActionTest)

	##############################################################################
	# FLARE
	##############################################################################

	def flare(self, link):
		return self._request(mode = OrionApi.ModeFlare, parameters = {OrionApi.ParameterLink : link}, raw = True)
