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

from resources.lib.extensions import tools
from resources.lib.extensions import network

class Core(object):

	# Modes
	ModeTorrent = 'torrent'
	ModeUsenet = 'usenet'
	ModeHoster = 'hoster'

	ErrorUnknown = 'unknown'
	ErrorUnavailable = 'unavailable'
	ErrorExternal = 'external'
	ErrorCancel = 'cancel'

	Exclusions = ('.txt', '.nfo', '.srt', '.nzb', '.torrent', '.rtf', '.exe', '.zip', '.7z', '.rar', '.par', '.pdf', '.doc', '.docx', '.ini', '.lnk', '.csvs', '.xml', '.html', '.json', '.jpg', '.jpeg', '.png', '.tiff', '.gif', '.bmp', '.md5', '.sha')

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, id, name):
		self.mId = id
		self.mName = name

	##############################################################################
	# GENERAL
	##############################################################################

	def id(self):
		return self.mId

	def name(self):
		return self.mName

	##############################################################################
	# ACCOUNT
	##############################################################################

	# Virtual
	def accountEnabled(self):
		return False

	# Virtual
	def accountValid(self):
		return False

	##############################################################################
	# SERVICES
	##############################################################################

	# Virtual
	def servicesList(self, onlyEnabled = False):
		return []

	##############################################################################
	# ADD
	##############################################################################

	@classmethod
	def addError(self):
		return self.addResult(error = Core.ErrorUnknown)

	@classmethod
	def addResult(self, error = None, id = None, link = None, extra = None, notification = None, items = None):
		if error == None:
			# Link can be to an external Kodi addon.
			if not link or (not network.Networker.linkIs(link) and not link.startswith('plugin:')):
				error = Core.ErrorUnknown
		result = {
			'success' : (error == None),
			'error' : error,
			'id' : id,
			'link' : link,
			'items' : items,
			'notification' : notification,
		}
		if extra:
			for key, value in extra.iteritems():
				result[key] = value
		return result

	##############################################################################
	# DELETE
	##############################################################################

	# Virtual
	def deletePlayback(self, id, pack = None, category = None):
		pass

	##############################################################################
	# CACHED
	##############################################################################

	@classmethod
	def cachedModes(self):
		return {}

	# Virtual
	def cached(self, id, timeout = None, callback = None, sources = None):
		pass

	##############################################################################
	# STREAMING
	##############################################################################

	def streaming(self, mode):
		return tools.Settings.getBoolean('streaming.%s.enabled' % mode) and tools.Settings.getBoolean('streaming.%s.%s.enabled' % (mode, self.mId))

	def streamingTorrent(self):
		return self.streaming(Core.ModeTorrent)

	def streamingUsenet(self):
		return self.streaming(Core.ModeUsenet)

	def streamingHoster(self):
		return self.streaming(Core.ModeHoster)
