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
import json
import urllib
import urllib2
import urlparse
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import xbmcvfs
import os
import sys
import platform
import stat
import inspect
import uuid
import time
import shutil
import threading

# Older Python versions (2.6) do not have a SSL module.
try: import ssl
except: pass

import database
import convert

class Downloader(database.Database):

	# Needed to retrieve addon settings, since downloader.py is started as a script.
	AddonName = 'Gaia'
	AddonId = 'plugin.video.gaia'
	AddonUpdate = AddonName + 'DownloaderUpdate'

	Database = 'downloads'

	UserAgent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'

	# How much data to read at once from the urllib buffer.
	ChunkSizeRead = 102400 # 100 KB

	# How much data to download before writing it to file.
	ChunkSizeWrite = 102400 # 100 KB

	# Types
	TypeManual = 'manual'
	TypeCache = 'cache'

	# Media
	# Must correspond with tools.Media.
	MediaMovie = 'movie'
	MediaShow = 'show'
	MediaDocumentary = 'documentary'
	MediaShort = 'short'
	MediaOther = 'other'

	# Actions
	ActionDownload = 'download'
	ActionDownloadNew = 'downloadnew'
	ActionObserve = 'observe'
	ActionContinue = 'continue'
	ActionHide = 'hide'
	ActionResume = 'resume'
	ActionRestart = 'restart'
	ActionDuplicate = 'duplicate'
	ActionPause = 'pause'
	ActionDelete = 'delete'
	ActionRemove = 'remove'
	ActionCancel = 'cancel'
	ActionPlay = 'play' # Stop download and play
	ActionStream = 'stream' # Continue download and play
	ActionRefresh = 'refresh' # Refresh the download directory item's progress and information

	# Statuses
	StatusQueued = 'queued'
	StatusInitialized = 'initialized'
	StatusRunning = 'running'
	StatusPaused = 'paused' # Only when the users pauses. If the downloader is forefully closed, it will still be running and the update time has to be checked.
	StatusCompleted = 'completed'
	StatusFailed = 'failed'
	StatusRemoved = 'removed'
	# Not a status that a download can have.
	StatusAll = 'all';
	StatusBusy = 'busy'; # StatusQueued, StatusInitialized, and StatusRunning

	# Commands
	CommandPause = 'pause' # Stop the download, but keep the partial file.
	CommandRemove = 'remove' # Stop the download, keep the partial file, and do not show the file in the download list.
	CommandDelete = 'delete' # Stop the download, delete the partial file, and do not show the file in the download list.

	# Colors
	ColorSpecial = 'FF6C3483'
	ColorUltra = 'FF2396FF'
	ColorExcellent = 'FF1E8449'
	ColorGood = 'FF668D2E'
	ColorMedium = 'FFB7950B'
	ColorPoor = 'FFBA4A00'
	ColorBad = 'FF922B21'

	# Font
	FontNewline = '[CR]'
	FontDivider = ' - '
	FontSeparator = ' | '

	# Progress Mode - Must correspond with settings XML
	ProgressNone = 0
	ProgressInterval = 1
	ProgressForeground = 2
	ProgressBackground = 3

	# Sorting
	SortNone = 0
	SortModified = 1
	SortAccessed = 2
	SortSizeSmallest = 3
	SortSizeLargest = 4

	# Notification Interval
	NotificationInterval = 10 # The percentage interval at which progress notifications are shown.

	# Speed
	# How many seconds of the past (and the chunks downloaded during that time) should be used to calculate the speed.
	# Do not make to low, otherwise speed can be inaccurate and jumpy too much.
	SpeedDuration = 60

	# Alive
	AliveUpdate = 5 # How often in seconds the keep-alive time should be updated.
	AliveLimitShort = AliveUpdate * 2 # After how many seconds since the last time update should the download be considered as stalled.
	AliveLimitLong = 120 # After how many seconds since the last time update should the download be considered as very long stalled, assumed to be paused (eg: Kodi exited before download was paused).

	# Prefixes
	PrefixSpecial = 'special://'
	PrefixSamba = 'smb://'

	# Paths
	PathDefault = 'Default'
	Paths = {
		'downloads.manual.path.combined' 		: 'special://userdata/addon_data/plugin.video.gaia/Downloads/Manual/',
		'downloads.manual.path.movies'			: 'special://userdata/addon_data/plugin.video.gaia/Downloads/Manual/Movies/',
		'downloads.manual.path.shows'			: 'special://userdata/addon_data/plugin.video.gaia/Downloads/Manual/Shows/',
		'downloads.manual.path.documentaries'	: 'special://userdata/addon_data/plugin.video.gaia/Downloads/Manual/Documentaries/',
		'downloads.manual.path.shorts'			: 'special://userdata/addon_data/plugin.video.gaia/Downloads/Manual/Shorts/',
		'downloads.manual.path.other'			: 'special://userdata/addon_data/plugin.video.gaia/Downloads/Manual/Other/',

		'downloads.cache.path.combined'			: 'special://userdata/addon_data/plugin.video.gaia/Downloads/Cache/',
		'downloads.cache.path.movies'			: 'special://userdata/addon_data/plugin.video.gaia/Downloads/Cache/Movies/',
		'downloads.cache.path.shows'			: 'special://userdata/addon_data/plugin.video.gaia/Downloads/Cache/Shows/',
		'downloads.cache.path.documentaries'	: 'special://userdata/addon_data/plugin.video.gaia/Downloads/Cache/Documentaries/',
		'downloads.cache.path.shorts'			: 'special://userdata/addon_data/plugin.video.gaia/Downloads/Cache/Shorts/',
		'downloads.cache.path.other'			: 'special://userdata/addon_data/plugin.video.gaia/Downloads/Cache/Other/',
	}

	# interaction shows dialogs and progress.
	#   None = yes for TypeManual, no for TypeCache
	#   True = yes
	#   False = no
	# If id is specified, will load the existing info from the database.
	def __init__(self, type = TypeManual, id = None):
		self.mType = type
		database.Database.__init__(self, Downloader.Database, addon = Downloader.AddonId)

		# Create the first time, in case they do not exist.
		self._fileCreateDirectory(self._locationMovies())
		self._fileCreateDirectory(self._locationShows())
		self._fileCreateDirectory(self._locationDocumentaries())
		self._fileCreateDirectory(self._locationOther())

		self._initialize()
		self._reset()

		self.mSkinPath = None
		self.mBackgroundPath = None
		self.mIconPath = None

		self.mDownloadId = id
		self._load(id)

	def __delete__(self):
		database.Database.__delete__(self)

	def _reset(self):
		# Must have a prefix "Download" otherwise mPath clashes with database.Database's mPath.
		self.mDownloadId = None
		self.mDownloadTimeStarted = None
		self.mDownloadTimeUpdated = None
		self.mDownloadStatus = None
		self.mDownloadLink = None
		self.mDownloadHeaders = None
		self.mDownloadMedia = None
		self.mDownloadTitle = None
		self.mDownloadName = None
		self.mDownloadPath = None
		self.mDownloadImage = None
		self.mDownloadSize = None
		self.mDownloadResumable = None
		self.mDownloadMetadata = None
		self.mDownloadSource = None
		self.mProgressParts = None
		self.mProgressPercentageCompleted = None
		self.mProgressPercentageRemaining = None
		self.mProgressSizeCompleted = None
		self.mProgressSizeRemaining = None
		self.mProgressTimeCompleted = None
		self.mProgressTimeRemaining = None
		self.mProgressSpeed = None

	def _log(self, message):
		xbmc.log(str(message))

	def _exit(self):
		sys.exit()

	def _run(self, action, observation = True):
		script = inspect.getfile(inspect.currentframe())
		command = 'RunScript(%s, %s, %s, %s, %d)' % (script, urllib.quote_plus(action), urllib.quote_plus(self.mType), urllib.quote_plus(self.mDownloadId), observation)
		xbmc.executebuiltin(command)

	def _response(self, link, headers, size, timeout = 30):
		try:
			if size > 0:
				size = int(size)
				headers['Range'] = 'bytes=%d-' % size
			if not 'user-agent' in [header.lower() for header in headers.keys()]:
				headers['User-Agent'] = Downloader.UserAgent
			request = urllib2.Request(link, headers = headers)

			try:
				secureContext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
				return urllib2.urlopen(request, timeout = timeout, context = secureContext)
			except:
				# SPMC (Python < 2.7.8) does not support TLS. Try to do it wihout SSL/TLS, otherwise bad luck.
				return urllib2.urlopen(request, timeout = timeout)
		except Exception as error:
			self._log(Downloader.AddonName.upper() + ' ERROR: Download Error [' + str(error) + ']')
			return None

	def _initialize(self):
		self._createAll('''
			CREATE TABLE IF NOT EXISTS %s (
				id TEXT,
				command TEXT,
				timeStarted INTEGER,
				timeUpdated INTEGER,
				status TEXT,
				link Text,
				headers TEXT,
				media TEXT,
				title Text,
				name TEXT,
				path TEXT,
				image TEXT,
				size INTEGER,
				resumable INTEGER,
				metadata TEXT,
				source TEXT,
				progressParts Text,
				progressPercentageCompleted REAL,
				progressPercentageRemaining REAL,
				progressSizeCompleted INTEGER,
				progressSizeRemaining INTEGER,
				progressTimeCompleted INTEGER,
				progressTimeRemaining INTEGER,
				progressSpeed INTEGER,
				UNIQUE(id)
			);
			''', [Downloader.TypeManual, Downloader.TypeCache])

	def _translate(self, string):
		if isinstance(string, int):
			string = xbmcaddon.Addon(Downloader.AddonId).getLocalizedString(string).encode('utf-8')
		return string

	def _translateSwitch(self, stringManual, stringCache):
		if self.mType == Downloader.TypeManual:
			return self._translate(stringManual)
		elif self.mType == Downloader.TypeCache:
			return self._translate(stringCache)
		else:
			return ''

	def _type(self, lower = False):
		type = 33051 if self.mType == Downloader.TypeManual else 33052
		type = self._translate(type)
		if lower: type = type.lower()
		return type

	def _title(self, extension = None, color = None, name = False, bold = True):
		title = xbmcaddon.Addon(Downloader.AddonId).getAddonInfo('name').encode('utf-8') if name else ''
		if not extension == None:
			if name: title += Downloader.FontDivider
			extension = self._translate(extension)
			if '%s' in extension: extension = extension % self._type()
			title += extension
		if color:
			title = self._fontColor(title, color)
		if bold:
			title = self._fontBold(title)
		return title

	@classmethod
	def _loaderType(self):
		try:
			if float(re.search('^\d+\.?\d+', xbmc.getInfoLabel('System.BuildVersion')).group(0)) >= 18:
				return 'busydialognocancel'
		except: pass
		return 'busydialog'

	def _loaderShow(self):
		xbmc.executebuiltin('ActivateWindow(%s)' % self._loaderType())

	def _loaderHide(self):
		xbmc.executebuiltin('Dialog.Close(%s)' % self._loaderType())

	def _icon(self, status = None, stalled = None, small = False):
		if self.mIconPath == None:
			theme = self._setting('interface.theme.icon', raw = True).lower()
			if 'glass' in theme:
				theme = theme.replace('(', '').replace(')', '')
			else:
				index = theme.find('(')
				if index >= 0: theme = theme[:index-1]
			if theme in ['default', '-', '']:
				self.mIconPath = ''
			else:
				theme = theme.replace(' ', '').lower()
				addon = 'script.gaia.resources' if theme == 'white' else 'script.gaia.icons'
				addon = xbmcaddon.Addon(addon).getAddonInfo('path')
				self.mIconPath = os.path.join(addon, 'resources', 'media', 'icons', theme)

		if self.mIconPath == '':
			return 'DefaultAddonsRepo.png'
		else:
			if status == None:
				status = self.mDownloadStatus
				if stalled == None:
					if status == Downloader.StatusRunning and self._stalled(long = True):
						status = Downloader.StatusPaused
					elif status == Downloader.StatusRunning and self._stalled(long = False):
						status = Downloader.StatusBusy
				elif stalled:
					status = Downloader.StatusPaused

			if status in [Downloader.StatusQueued, Downloader.StatusInitialized, Downloader.StatusRunning]:
				status = Downloader.StatusBusy

			type = 'small' if small else 'large'
			return os.path.join(self.mIconPath, type, 'downloads%s.png' % status)

	def _background(self):
		if self.mSkinPath == None:
			theme = self._setting(id = 'interface.theme.icon', raw = True)
			if theme in ['default', '-', '']:
				self.mSkinPath = '' # Ensures that this if-statement does not execute again.
			else:
				theme = theme.replace(' ', '').lower()
				index = theme.find('(')
				if index >= 0: theme = theme[:index]
				addon = 'script.gaia.resources' if theme == 'white' else 'script.gaia.skins'
				try:
					addon = xbmcaddon.Addon(addon).getAddonInfo('path')
				except: # script.gaia.skins is not installed
					addon = 'script.gaia.resources'
					addon = xbmcaddon.Addon(addon).getAddonInfo('path')
				self.mSkinPath = os.path.join(addon, 'resources', 'media', 'skins', theme)
				path = os.path.join(self.mSkinPath, 'background.jpg')
				if os.path.exists(path):
					self.mBackgroundPath = path
				else:
					path = os.path.join(self.mSkinPath, 'background.png') # Glass
					if os.path.exists(path):
						self.mBackgroundPath = path

		return self.mBackgroundPath

	def _colorToRgb(self, hex):
		return [int(hex[i:i+2], 16) for i in range(2,8,2)]

	def _colorToHex(self, rgb):
		rgb = [int(i) for i in rgb]
		return 'FF' + ''.join(['0{0:x}'.format(i) if i < 16 else '{0:x}'.format(i) for i in rgb])

	def _colorGradient(self, startHex, endHex, count = 10):
		# http://bsou.io/posts/color-gradients-with-python
		start = self._colorToRgb(startHex)
		end = self._colorToRgb(endHex)
		colors = [start]
		for i in range(1, count):
			vector = [int(start[j] + (float(i) / (count-1)) * (end[j] - start[j])) for j in range(3)]
			colors.append(vector)
		return [self._colorToHex(i) for i in colors]

	# messages = (message-foregound, message-background)
	def _notification(self, messages, status = None):
		setting = int(self._setting('notifications'))
		if setting == 0:
			return
		elif xbmc.Player().isPlaying(): # Always show a notification if playing. Otherwise the user has to click OK in the middle of playback.
			setting = 2

		path = xbmc.translatePath(xbmcaddon.Addon('script.gaia.resources').getAddonInfo('path').decode('utf-8'))
		path = os.path.join(path, 'resources', 'media', 'notifications')

		title = None
		icon = 'information.png'
		sound = False

		if status == Downloader.StatusCompleted:
			title = 33053
			sound = True
		elif status == Downloader.StatusFailed:
			title = 33054
			icon = 'error.png'
			sound = True
		elif status == Downloader.StatusQueued or status == Downloader.StatusInitialized or status == Downloader.StatusRunning:
			title = 33055
		elif status == Downloader.StatusPaused:
			title = 33057
		elif status == Downloader.StatusDeleted or status == Downloader.StatusRemoved:
			title = 33056

		icon = os.path.join(path, icon)

		self._loaderHide()
		if setting == 1:
			title = self._title(extension = title, name = True)
			message = self._translate(messages[1])
			if '%s' in message: message = self._translate(message) % self._type(lower = True)
			if not self.mDownloadTitle == None: message = self._translate(33071) + ': ' + self.mDownloadTitle + Downloader.FontNewline + message
			self._dialogConfirm(message, title = title, internal = True)
		elif setting == 2:
			title = self._title(extension = title, name = False, bold = False)
			message = self._translate(messages[0])
			if '%s' in message: message = self._translate(message) % self._type()
			self._dialogNotify(message, title = title, sound = sound, icon = icon, internal = True)

	def _dialogNotify(self, message, title = None, sound = False, icon = None, internal = False):
		if internal == False:
			title = self._title(extension = title, name = False, bold = False)
		self._loaderHide()
		if not self.mDownloadImage == None and not self.mDownloadImage == '':
			icon = self.mDownloadImage
		xbmcgui.Dialog().notification(self._translate(title), self._translate(message), icon, 8000, sound = sound)

	def _dialogConfirm(self, message, title = None, internal = False):
		if internal == False:
			title = self._title(extension = title, name = True)
		self._loaderHide()
		xbmcgui.Dialog().ok(title, self._translate(message))

	def _dialogProgress(self, message = None, background = False, title = None, internal = False):
		if internal == False:
			title = self._title(extension = title, name = True)
		self._loaderHide()
		if background:
			dialog = xbmcgui.DialogProgressBG()
		else:
			dialog = xbmcgui.DialogProgress()
		if not message:
			message = ''
		else:
			message = self._translate(message)
		dialog.create(title, message)
		if background:
			dialog.update(0, self._translate(title), message)
		else:
			dialog.update(0, message)
		return dialog

	def _dialogOption(self, message, labelConfirm = None, labelDeny = None, title = None, internal = False):
		if internal == False:
			title = self._title(extension = title, name = True)
		self._loaderHide()
		labelConfirm = self._translate(labelConfirm) if labelConfirm else labelConfirm
		labelDeny = self._translate(labelDeny) if labelDeny else labelDeny
		return xbmcgui.Dialog().yesno(title, self._translate(message), yeslabel = labelConfirm, nolabel = labelDeny)

	def _dialogOptions(self, items, title = None, internal = False):
		if internal == False:
			title = self._title(extension = title, name = True)
		self._loaderHide()
		return xbmcgui.Dialog().select(heading = title, list = items)

	def _fontCapitalize(self, text):
		return '[CAPITALIZE]' + str(text) + '[/CAPITALIZE]'

	def _fontUppercase(self, text):
		return '[UPPERCASE]' + str(text) + '[/UPPERCASE]'

	def _fontBold(self, text):
		return '[B]' + str(text) + '[/B]'

	def _fontItalic(self, text):
		return '[I]' + str(text) + '[/I]'

	def _fontColor(self, text, color):
		return '[COLOR ' + color + ']' + str(text) + '[/COLOR]'

	def _time(self):
		return int(time.time())

	def _time(self):
		return int(time.time())

	def _elapsed(self, start):
		return int(self_time() - start)

	def _setting(self, id, raw = False): # id excluding the prefix downloads.manual or downloads.cache.
		return xbmcaddon.Addon(Downloader.AddonId).getSetting(self._settingId(id = id, raw = raw))

	def _settingId(self, id, raw = False):
		if not raw: id = '.'.join(['downloads', self.mType, id])
		return id

	def _settingPath(self, id, raw = False):
		path = self._setting(id = id, raw = raw)
		if path == Downloader.PathDefault or path.strip() == '' or not path:
			path = Downloader.Paths[self._settingId(id = id, raw = raw)]
		return path

	def _enabled(self, full = False):
		result = self._setting('enabled') == 'true'
		if full and result:
			selection = int(self._setting('path.selection'))
			result = (selection == 0 and self._fileExistsDirectory(self._settingPath('path.combined'))) or (selection == 1 and (self._fileExistsDirectory(self._settingPath('path.movies') or self._fileExistsDirectory(self._settingPath('path.tvshows')))))
		return result

	def _location(self, media = None):
		if media == None:
			media = self.mDownloadMedia

		if media == Downloader.MediaMovie:
			return self._locationMovies()
		elif media == Downloader.MediaShow:
			return self._locationShows()
		elif media == Downloader.MediaDocumentary:
			return self._locationDocumentaries()
		elif media == Downloader.MediaShort:
			return self._locationShorts()
		elif media == Downloader.MediaOther:
			return self._locationOther()
		else:
			return None

	def _locationMovies(self):
		path = None
		if self._setting('path.selection') == '0':
			path = os.path.join(self._settingPath('path.combined'), self._translate(32001))
			try: xbmcvfs.mkdir(path)
			except: pass
		else:
			path = self._settingPath('path.movies')
		if not path.endswith('/') and not path.endswith('\\'): path += '/'
		return path

	def _locationShows(self):
		path = None
		if self._setting('path.selection') == '0':
			path = os.path.join(self._settingPath('path.combined'), self._translate(32002))
			try: xbmcvfs.mkdirs(path)
			except: pass
		else:
			path = self._settingPath('path.shows')
		if not path.endswith('/') and not path.endswith('\\'): path += '/'
		return path

	def _locationDocumentaries(self):
		path = None
		if self._setting('path.selection') == '0':
			path = os.path.join(self._settingPath('path.combined'), self._translate(33470))
			try: xbmcvfs.mkdirs(path)
			except: pass
		else:
			path = self._settingPath('path.documentaries')
		if not path.endswith('/') and not path.endswith('\\'): path += '/'
		return path

	def _locationShorts(self):
		path = None
		if self._setting('path.selection') == '0':
			path = os.path.join(self._settingPath('path.combined'), self._translate(33471))
			try: xbmcvfs.mkdirs(path)
			except: pass
		else:
			path = self._settingPath('path.shorts')
		if not path.endswith('/') and not path.endswith('\\'): path += '/'
		return path

	def _locationOther(self):
		path = None
		if self._setting('path.selection') == '0':
			path = os.path.join(self._settingPath('path.combined'), self._translate(35149))
			try: xbmcvfs.mkdirs(path)
			except: pass
		else:
			path = self._settingPath('path.other')
		if not path.endswith('/') and not path.endswith('\\'): path += '/'
		return path

	def _file(self, title, link):
		extension = os.path.splitext(urlparse.urlparse(link).path)[1][1:]
		if (extension == None or extension == '') and not extension in ['mp4', 'mpg', 'mpeg', 'mp2', 'm4v', 'm2v', 'mkv', 'avi', 'flv', 'asf', '3gp', '3g2', 'wmv', 'mov', 'qt', 'webm', 'vob']: extension = 'mkv'

		title = str(title) # For some reason the parameters sometimes comes in as non-strung. Maybe utf8-string?
		content = re.compile('(.+?)\sS(\d*)E\d*.*').findall(title)
		title = title.translate(None, '\/:*?"<>|').strip('.')

		# Remove old [x] version in title.
		title = re.sub('\[\d*\]', '', title).strip()

		path = self._location()
		if len(content) == 0:
			try: directoryName = os.path.splitext(title)[0] # Remove file extension.
			except: directoryName = title
			path = os.path.join(path, directoryName)
		else:
			show = content[0][0].translate(None, '\/:*?"<>|').strip('.')
			path = os.path.join(path, show, 'Season %01d' % int(content[0][1]))

		path = os.path.join(path, '') # Adds a trailing slash for xbmcvfs.exists to work.
		path = path.replace('\\', '/') # Otherwise smb paths on Windows have mixed slashes. And also avoids escape character. Kodi seems to handle both slashes fine on Windows.
		xbmcvfs.mkdirs(path)
		counter = 0
		if self._fileExists(path):
			fileName = title + '.' + extension
			filePath = os.path.join(path, fileName)
			counter = 1
			while self._fileExists(filePath, extension = False):
				counter += 1
				fileName = title + ' [' + str(counter) + '].' + extension
				filePath = os.path.join(path, fileName)
			counter -= 1
			title = os.path.splitext(fileName)[0]
			return counter, title, fileName, filePath
		else:
			return 0, None, None, None

	def _fileDelete(self, path, force = True, deleteParent = False):
		if path == None or path == '':
			return False

		try:
			# For samba paths
			try:
				if self._fileExists(path):
					xbmcvfs.delete(path)
			except:
				pass

			# All with force
			try:
				if self._fileExists(path):
					if force: os.chmod(path, stat.S_IWRITE) # Remove read only.
					os.remove(path) # xbmcvfs often has problems deleting files
			except:
				pass

			try:
				if deleteParent:
					path = os.path.dirname(path)
					directories, files = self._fileList(path)
					self._fileDeleteDirectory(path, force = True)
			except:
				pass

			return not self._fileExists(path)
		except:
			return False

	def _fileCreateDirectory(self, path):
		return xbmcvfs.mkdirs(path)

	def _fileDeleteDirectory(self, path, force = True):
		if path == None or path == '':
			return False

		try:
			# For samba paths
			try:
				if self._fileExistsDirectory(path):
					return xbmcvfs.rmdir(path)
			except:
				pass

			try:
				if self._fileExistsDirectory(path):
					return shutil.rmtree(path)
			except:
				pass

			# All with force
			try:
				if self._fileExistsDirectory(path):
					if force: os.chmod(path, stat.S_IWRITE) # Remove read only.
					return os.rmdir(path)
			except:
				pass

			return not self._fileExistsDirectory(path)
		except:
			return False

	def _fileMove(self, pathFrom, pathTo):
		xbmcvfs.rename(pathFrom, pathTo)

	def _fileRead(self, path):
		if self._fileExists(path):
			file = xbmcvfs.File(path)
			data = file.read()
			file.close()
			return data
		else:
			return None
		xbmcvfs.rename(pathFrom, pathTo)

	def _fileExists(self, path, extension = True, exact = True):
		# os.exists can not handle network (smb) paths.
		if extension:
			return xbmcvfs.exists(path)
		else:
			title = os.path.splitext(os.path.basename(path))[0]
			directory = os.path.dirname(path)
			if self._fileFind(directory, title, exact = exact) == None:
				return False
			else:
				return True

	def _fileExistsDirectory(self, path):
		if not path.endswith('/') and not path.endswith('\\'):
			path += '/'
		return xbmcvfs.exists(path)

	def _fileFind(self, path, title, exact = True):
		directories, files = self._fileList(path)
		for file in files:
			titleNew = os.path.splitext(os.path.basename(file))[0]
			match = False
			if exact:
				match = title == titleNew
			else:
				match = titleNew.startswith(title) or title.startswith(titleNew)
			if match:
				return os.path.join(path, file).replace('\\', '/') # Otherwise smb paths on Windows have mixed slashes. And also avoids escape character. Kodi seems to handle both slashes fine on Windows.
		return None

	def _fileList(self, path):
		return xbmcvfs.listdir(path)

	def _fileTimes(self, path):
		try:
			stats = xbmcvfs.Stat(path)
			return stats.st_mtime(), stats.st_atime()
		except:
			return None, None

	def _id(self):
		id = str(uuid.uuid4().hex)
		exists = self._exists('SELECT id FROM %s WHERE id IS "%s";' % (self.mType, id))
		while exists:
			id = str(uuid.uuid4().hex)
			exists = self._exists('SELECT id FROM %s WHERE id IS "%s";' % (self.mType, id))
		return id

	def _insertDownload(self, link, media, title, name, path, image = None, headers = None, metadata = None, source = None):
		self.mDownloadId = self._id()
		command = self._null()
		status = Downloader.StatusQueued
		timeCurrent = self._time()
		image = ('"%s"' % image) if not image == None else self._null()
		headers = ('"%s"' % json.dumps(headers).replace('"', '""').replace("'", "''")) if not headers == None else self._null()

		# Exchange single and double quotes, since JSON uses double quotes. Using two quotes instead \, is SQL's way of escaping characters.
		metadata = ('"%s"' % json.dumps(metadata).replace('"', '""').replace("'", "''")) if not metadata == None else self._null()
		source = ('"%s"' % json.dumps(source).replace('"', '""').replace("'", "''")) if not source == None else self._null()

		parts = json.dumps([])
		self._insert('''
			INSERT INTO %s
			(id, command, timeStarted, timeUpdated, status, link, headers, media, title, name, path, image, size, resumable, metadata, source, progressParts, progressPercentageCompleted, progressPercentageRemaining, progressSizeCompleted, progressSizeRemaining, progressTimeCompleted, progressTimeRemaining, progressSpeed)
			VALUES
			("%s", %s, %d, %d, "%s", "%s", %s, "%s", "%s", "%s", "%s", %s, %d, %d, %s, %s, "%s", %f, %f, %d, %d, %d, %d, %d);
		'''
		% (self.mType, self.mDownloadId, command, timeCurrent, timeCurrent, status, link, headers, media, title, name, path, image, 0, -1, metadata, source, parts, 0, 0, 0, 0, 0, 0, 0))
		return self.mDownloadId

	def _updateDownload(self, updated = None, full = False):
		if updated == None:
			updated = self._time()
		self.mDownloadTimeUpdated = updated

		if full:
			image = ('"%s"' % self.mDownloadImage) if not self.mDownloadImage == None else self._null()
			headers = ('"%s"' % json.dumps(self.mDownloadHeaders).replace('"', '""').replace("'", "''")) if not self.mDownloadHeaders == None else self._null()

			# Exchange single and double quotes, since JSON uses double quotes. Using two quotes instead \, is SQL's way of escaping characters.
			metadata = ('"%s"' % json.dumps(self.mDownloadMetadata).replace('"', '""').replace("'", "''")) if not self.mDownloadMetadata == None else self._null()
			source = ('"%s"' % json.dumps(self.mDownloadSource).replace('"', '""').replace("'", "''")) if not self.mDownloadSource == None else self._null()

			return self._update('''
				UPDATE
					%s
				SET
					timeStarted = %d,
					timeUpdated = %d,
					status = "%s",
					link = "%s",
					headers = %s,
					media = "%s",
					title = "%s",
					name = "%s",
					path = "%s",
					image = %s,
					size = %d,
					resumable = %d,
					metadata = %s,
					source = %s,
					progressParts = "%s",
					progressPercentageCompleted = %f,
					progressPercentageRemaining = %f,
					progressSizeCompleted = %d,
					progressSizeRemaining = %d,
					progressTimeCompleted = %d,
					progressTimeRemaining = %d,
					progressSpeed = %d
				WHERE
					id = "%s";
			''' % (self.mType, self.mDownloadTimeStarted, self.mDownloadTimeUpdated, self.mDownloadStatus, self.mDownloadLink, headers, self.mDownloadMedia, self.mDownloadTitle, self.mDownloadName, self.mDownloadPath, image, self.mDownloadSize, self.mDownloadResumable, metadata, source, self.mProgressParts, self.mProgressPercentageCompleted, self.mProgressPercentageRemaining, self.mProgressSizeCompleted, self.mProgressSizeRemaining, self.mProgressTimeCompleted, self.mProgressTimeRemaining, self.mProgressSpeed, self.mDownloadId))
		else:
			return self._update('''
				UPDATE
					%s
				SET
					timeUpdated = %d,
					status = "%s",
					size = %d,
					resumable = %d,
					progressParts = "%s",
					progressPercentageCompleted = %f,
					progressPercentageRemaining = %f,
					progressSizeCompleted = %d,
					progressSizeRemaining = %d,
					progressTimeCompleted = %d,
					progressTimeRemaining = %d,
					progressSpeed = %d
				WHERE
					id = "%s";
			''' % (self.mType, self.mDownloadTimeUpdated, self.mDownloadStatus, self.mDownloadSize, self.mDownloadResumable, self.mProgressParts, self.mProgressPercentageCompleted, self.mProgressPercentageRemaining, self.mProgressSizeCompleted, self.mProgressSizeRemaining, self.mProgressTimeCompleted, self.mProgressTimeRemaining, self.mProgressSpeed, self.mDownloadId))

	def _updateStatus(self, status = None):
		oldStatus = self.mDownloadStatus
		if status == None:
			status = self.mDownloadStatus
		else:
			self.mDownloadStatus = status

		if status == Downloader.StatusRemoved:
			result = self._deleteDownload()
		else:
			result = self._update('UPDATE %s SET status = "%s" WHERE id = "%s";' % (self.mType, status, self.mDownloadId))

		self.itemsRefresh() # Force refresh if the downloads directory is listed in the background and the status changes.
		self._updateLibrary(oldStatus)
		return result

	def _updateTime(self, updated = None):
		if updated == None:
			updated = self._time()
		self.mDownloadTimeUpdated = updated
		return self._update('UPDATE %s SET timeUpdated = %d WHERE id = "%s";' % (self.mType, updated, self.mDownloadId))

	def _updateCommand(self, command):
		return self._update('UPDATE %s SET command = "%s" WHERE id = "%s";' % (self.mType, command, self.mDownloadId))

	def _deleteDownload(self):
		return self._delete('DELETE FROM %s WHERE id IS "%s";' % (self.mType, self.mDownloadId))

	def _deleteItems(self, status = None):
		result = False
		if status == None or status == Downloader.StatusAll:
			result = self._delete('DELETE FROM %s;' % (self.mType))
		elif status == Downloader.StatusBusy:
			status = [Downloader.StatusQueued, Downloader.StatusInitialized, Downloader.StatusRunning]
			where = 'status = "%s"' % status[0]
			for i in range(1, len(status)):
				where += ' OR status = "%s"' % status[i]
			result = self._delete('DELETE FROM %s WHERE %s;' % (self.mType, where))
		else:
			result = self._delete('DELETE FROM %s WHERE status IS "%s";' % (self.mType, status))
		return result

	def _selectCommand(self, reset = True):
		result = self._selectValue('SELECT command FROM %s WHERE id IS "%s";' % (self.mType, self.mDownloadId))
		if not result == None and reset:
			self._update('UPDATE %s SET command = %s WHERE id = "%s";' % (self.mType, self._null(), self.mDownloadId))
		return result

	def _selectId(self, removed = False):
		if removed: removed = ''
		else: removed = ' WHERE NOT status IS "%s"' % Downloader.StatusRemoved
		items = self._select('SELECT id, link FROM %s%s;' % (self.mType, removed))
		for item in items:
			if self._sameLink(self.mDownloadLink, item[1]):
				return item[0]
		return None

	def _selectFind(self, path, removed = False):
		if removed: removed = ''
		else: removed = ' AND NOT status IS "%s"' % Downloader.StatusRemoved
		return self._selectValue('SELECT id FROM %s WHERE path IS "%s"%s;' % (self.mType, path, removed))

	def _selectPaths(self, status = None, removed = False):
		paths = []
		if status == None or status == Downloader.StatusAll:
			if removed: removed = ''
			else: removed = ' WHERE NOT status IS "%s"' % Downloader.StatusRemoved
			paths = self._selectValues('SELECT path FROM %s%s;' % (self.mType, removed))
		else:
			if removed: removed = ''
			else: removed = ' AND NOT status IS "%s"' % Downloader.StatusRemoved
			if status == Downloader.StatusBusy:
				status = [Downloader.StatusQueued, Downloader.StatusInitialized, Downloader.StatusRunning]
				where = 'status = "%s"' % status[0]
				for i in range(1, len(status)):
					where += ' OR status = "%s"' % status[i]
				paths = self._selectValues('SELECT path FROM %s WHERE %s%s;' % (self.mType, where, removed))
			else:
				paths = self._selectValues('SELECT path FROM %s WHERE status IS "%s"%s;' % (self.mType, status, removed))
		return paths

	def _selectItems(self, status = None, removed = False):
		items = []
		if status == None or status == Downloader.StatusAll:
			if removed:
				items = self._select('SELECT * FROM %s;' % (self.mType))
			else:
				items = self._select('SELECT * FROM %s WHERE NOT status IS "%s";' % (self.mType, Downloader.StatusRemoved))
		elif status == Downloader.StatusBusy:
			status = [Downloader.StatusQueued, Downloader.StatusInitialized, Downloader.StatusRunning]
			where = 'status = "%s"' % status[0]
			for i in range(1, len(status)):
				where += ' OR status = "%s"' % status[i]
			items = self._select('SELECT * FROM %s WHERE %s;' % (self.mType, where))
		else:
			items = self._select('SELECT * FROM %s WHERE status IS "%s";' % (self.mType, status))
		return items

	# Cached Premiumize items always return a different link containing a random string, which actually points to the same file.
	def _sameLink(self, link1, link2):
		if link1 == link2:
			return True
		else:
			domain = 'energycdn.com'
			index1 = link1.find(domain)
			index2 = link2.find(domain)
			if index1 >= 0 and index2 >= 0:
				items1 = link1[index1:].split('/')
				items2 = link2[index2:].split('/')
				if len(items1) >= 8 and len(items2) >= 8:
					return items1[-1] == items2[-1] and items1[-2] == items2[-2] and items1[-3] == items2[-3]
			return False

	def _load(self, id = None, data = None):
		if id == None and data == None:
			id = self.mDownloadId
		if id or data:
			if id:
				result = self._selectSingle('SELECT * FROM %s WHERE id IS "%s";' % (self.mType, id))
				if not result: # Download was removed/deleted.
					return False
			elif data:
				result = data

			self.mDownloadId = result[0]
			self.mDownloadTimeStarted = result[2]
			self.mDownloadTimeUpdated = result[3]
			self.mDownloadStatus = result[4]
			self.mDownloadLink = result[5]
			self.mDownloadHeaders = json.loads(result[6]) if result[6] else None
			self.mDownloadMedia = result[7]
			self.mDownloadTitle = result[8]
			self.mDownloadName = result[9]
			self.mDownloadPath = result[10]
			self.mDownloadImage = result[11]
			self.mDownloadSize = result[12]
			self.mDownloadResumable = result[13] == 1
			self.mDownloadMetadata = json.loads(result[14]) if result[14] else None
			self.mDownloadSource = json.loads(result[15]) if result[15] else None
			self.mProgressParts = json.loads(result[16]) if result[16] else None
			self.mProgressPercentageCompleted = result[17]
			self.mProgressPercentageRemaining = result[18]
			self.mProgressSizeCompleted = result[19]
			self.mProgressSizeRemaining = result[20]
			self.mProgressTimeCompleted = result[21]
			self.mProgressTimeRemaining = result[22]
			self.mProgressSpeed = result[23]
			return True
		else:
			return False

	def _aliveUpdate(self):
		# This is started from a new thread, hence there are concurrency issues, not allowing a database object to be accessed from different threads.
		# Create a new database object here, by creating a new downlaoder.
		downer = Downloader(type = self.mType, id = self.mDownloadId)
		while downer.mDownloadStatus in [downer.StatusQueued, downer.StatusInitialized, downer.StatusRunning]:
			downer._updateTime()
			self.mDownloadTimeUpdated = downer.mDownloadTimeUpdated
			time.sleep(downer.AliveUpdate)

	def _clear(self, status = None, automatic = False):
		files = False

		if not automatic:
			actionRemove = self._fontBold(self._translate(33286) + ': ') + self._translate(33287)
			actionDelete = self._fontBold(self._translate(33083) + ': ') + self._translate(33084)
			actionCancel = self._fontBold(self._translate(33288) + ': ') + self._translate(33289)
			actions = [actionRemove, actionDelete, actionCancel]
			actionChoice = self._dialogOptions(title = 33298, items = actions, internal = False)
			if actionChoice >= 0:
				actionChoice = actions[actionChoice]
				if actionChoice == actionRemove:
					files = False
				elif actionChoice == actionDelete:
					files = True
				elif actionChoice == actionCancel:
					return False
			else:
				return False

			answer = self._dialogOption(title = 33298, message = 33299, internal = False)
			if not answer:
				return False

		if files:
			paths = self._selectPaths(status)
			for path in paths:
				self._fileDelete(path, deleteParent = True)

		return self._deleteItems(status)

	def clear(self, status = None, automatic = False):
		return self._clear(status = status, automatic = automatic)

	def refresh(self):
		self._load()

	def type(self):
		return self.mType

	def id(self):
		return self.mDownloadId

	def status(self, refresh = False):
		if refresh: self.refresh()
		return self.mDownloadStatus

	def sizeTotal(self, refresh = False):
		if refresh: self.refresh()
		return self.mDownloadSize

	def sizeCompleted(self, refresh = False):
		if refresh: self.refresh()
		return self.mProgressSizeCompleted

	def sizeRemaining(self, refresh = False):
		if refresh: self.refresh()
		return self.mProgressSizeRemaining

	def progress(self, refresh = False):
		if refresh: self.refresh()
		progress = 0 if self.mProgressPercentageCompleted == None else self.mProgressPercentageCompleted
		return '%d%%' % int(progress)

	def speed(self, refresh = False):
		if refresh: self.refresh()
		speed = 0 if self.mProgressSpeed == None else self.mProgressSpeed
		return convert.ConverterSpeed(value = speed, unit = convert.ConverterSpeed.Byte).stringOptimal()

	def enabled(self, notification = True, full = False):
		if self._enabled(full = full):
			return True
		elif notification:
			self.notificationEnabled()
			return False

	def notificationEnabled(self):
		title = self._title(extension = 33300, name = True)
		message = self._translate(33066) % self.mType
		choice = self._dialogOption(title = title, message = message, labelConfirm = 33011, labelDeny = 33486, internal = True)
		if choice:
			xbmc.executebuiltin('Addon.OpenSettings(%s)' % Downloader.AddonId)
			xbmc.executebuiltin('SetFocus(%i)' % (8 + 100))

	def notificationLocation(self, confirmation = True):
		title = self._title(extension = 33054, name = True)
		message = self._translate(33068) % self.mType
		self._dialogConfirm(title = title, message = message, internal = True)

	# Will stop item updates and its thread.
	# Called from main gaia.py.
	@classmethod
	def itemsStop(self):
		window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
		window.clearProperty(Downloader.AddonUpdate)

	def itemsRefresh(self):
		try:
			window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
			if window.getProperty(Downloader.AddonUpdate) == 'true':
				xbmc.executebuiltin('Container.Refresh')
		except: pass

	def _itemsRun(self, status, windowId, window):
		while True:
			time.sleep(15) # Sleep first, because the first list was already shown and does not immediatly need a refresh.

			try: refresh = window.getProperty(Downloader.AddonUpdate) == 'true'
			except: refresh = False
			exited = not windowId == xbmcgui.getCurrentWindowId()
			if not refresh or exited:
				break

			self.itemsRefresh()

	def _itemsUpdate(self, status, handle, addon, colors):
		downer = Downloader(self.mType) # SQLite objects must be used from the same thread they were created in. So do not use self here.
		result = downer._selectItems(status)
		for item in result:
			self._load(data = item)

			stalledShort = self.mDownloadStatus == Downloader.StatusRunning and self._stalled(long = False)
			stalledLong = self.mDownloadStatus == Downloader.StatusRunning and self._stalled(long = True)
			url = '%s?action=download&downloadType=%s&downloadId=%s&refresh=%d' % (addon, self.mType, self.mDownloadId, True)

			try: title = os.path.splitext(os.path.basename(self.mDownloadPath))[0]
			except: title = self.mDownloadTitle
			labelTop = self._fontBold(title)

			info = []

			# Status
			if stalledLong:
				color = Downloader.ColorMedium
				state = 33292
			elif stalledShort:
				color = Downloader.ColorGood
				state = 33370
			elif self.mDownloadStatus == Downloader.StatusQueued or self.mDownloadStatus == Downloader.StatusInitialized or self.mDownloadStatus == Downloader.StatusRunning:
				color = Downloader.ColorExcellent
				state = 33291
			elif self.mDownloadStatus == Downloader.StatusPaused:
				color = Downloader.ColorMedium
				state = 33292
			elif self.mDownloadStatus == Downloader.StatusCompleted:
				color = Downloader.ColorSpecial
				state = 33294
			elif self.mDownloadStatus == Downloader.StatusFailed:
				color = Downloader.ColorBad
				state = 33295
			else:
				color = None
				state = None
			if not state == None:
				state = self._fontColor(self._translate(state), color)
				info.append(state)

			# Percentage
			percentage = int(self.mProgressPercentageCompleted)
			percentage = self._fontColor('%d%%' % percentage, colors[percentage])
			info.append(percentage)

			# Size
			if self.mProgressSizeCompleted > 0:
				size = convert.ConverterSize(value = self.mProgressSizeCompleted).stringOptimal(places = convert.ConverterSize.PlacesDouble)
				if self.mDownloadSize > 0:
					size += ' ' + self._translate(33073) + ' ' + convert.ConverterSize(value = self.mDownloadSize).stringOptimal(places = convert.ConverterSize.PlacesDouble)
				info.append(size)

			# Speed
			if (self.mDownloadStatus == Downloader.StatusRunning or stalledShort) and not stalledLong and self.mProgressSpeed > 0:
				speed = convert.ConverterSpeed(value = self.mProgressSpeed, unit = convert.ConverterSpeed.Byte).stringOptimal()
				info.append(speed)

			# Time
			if (self.mDownloadStatus == Downloader.StatusRunning or stalledShort) and not stalledLong and self.mDownloadSize > 0 and self.mProgressTimeRemaining > 0:
				timeRemaining = convert.ConverterDuration(value = self.mProgressTimeRemaining, unit = convert.ConverterDuration.UnitSecond).string()
				info.append(timeRemaining)

			labelBottom = Downloader.FontSeparator.join(info)

			# Esnures that the top part is always longer. Otherwise the speed & ETA will not be visible if the top label is very short.
			lengthTop = len(re.sub('\\[(.*?)\\]', '', labelTop))
			lengthBottom = len(re.sub('\\[(.*?)\\]', '', labelBottom))
			labelDifference = lengthBottom - lengthTop

			if labelDifference > 0:
				labelTop +=  (' ' * int(labelDifference * 2))

			label = labelTop + Downloader.FontNewline + labelBottom

			item = xbmcgui.ListItem(label = label)
			iconSmall = self._icon(small = True)
			iconLarge = self._icon(small = False)
			iconThumb = iconSmall if 'aeon.nox' in xbmc.getSkinDir() else iconLarge
			item.setArt({'icon': iconSmall, 'thumb': iconThumb, 'poster': iconLarge, 'banner': iconLarge})

			menu = []
			menu.append((self._translate(32072), 'RunPlugin(%s?action=downloadsRefresh&downloadType=%s&refresh=%d)' % (addon, self.mType, True)))
			menu.append((self._translate(33371), 'RunPlugin(%s)' % (url)))
			menu.append((self._translate(33379), 'RunPlugin(%s?action=downloadDetails&downloadType=%s&downloadId=%s)' % (addon, self.mType, self.mDownloadId)))
			menu.append((self._translate(33031), 'RunPlugin(%s?action=linkCopy&link=%s&resolve=false)' % (addon, self.mDownloadLink)))
			menu.append((self._translate(33393), 'RunPlugin(%s?action=linkCopy&link=%s&resolve=false)' % (addon, self.mDownloadPath)))
			item.addContextMenuItems(menu)

			try:
				fanart = self.mDownloadMetadata['fanart'] if 'fanart' in self.mDownloadMetadata else self.mDownloadMetadata['fanart2'] if 'fanart2' in self.mDownloadMetadata else self.mDownloadMetadata['fanart3'] if 'fanart3' in self.mDownloadMetadata else None
				if fanart == None or fanart == '':
					raise Exception()
			except:
				fanart = self._background()
			item.setProperty('Fanart_Image', fanart)

			xbmcplugin.addDirectoryItem(handle = handle, url = url, listitem = item, isFolder = False)

		xbmcplugin.setContent(handle, 'addons')
		xbmcplugin.endOfDirectory(handle, cacheToDisc = True)
		self._loaderHide()

	def items(self, status = None, refresh = True):
		addon = sys.argv[0]
		handle = int(sys.argv[1])
		colors = self._colorGradient(Downloader.ColorMedium, Downloader.ColorExcellent, 101) # One more, since it goes from 0 - 100

		windowId = xbmcgui.getCurrentWindowId()
		window = xbmcgui.Window(windowId)

		self._itemsUpdate(status, handle, addon, colors)
		try: wasRefreshed = window.getProperty(Downloader.AddonUpdate) == 'true'
		except: wasRefreshed = False
		if wasRefreshed:
			return

		window.setProperty(Downloader.AddonUpdate, 'true')

		if refresh:
			thread = threading.Thread(target = self._itemsRun, args = (status, windowId, window))
			thread.start()

	def details(self):
		items = []
		yes = self._translate(33341)
		no = self._translate(33342)

		# File
		name = '' if self.mDownloadName == None or self.mDownloadName == '' else os.path.splitext(self.mDownloadName)[0]
		try: extension = os.path.splitext(self.mDownloadPath)[1]
		except: extension = None
		extension = '' if extension == None or extension == '' else extension.upper()
		if extension.startswith('.'): extension = extension[1:]
		link = '' if self.mDownloadLink == None or self.mDownloadLink == '' else self.mDownloadLink
		path = '' if self.mDownloadPath == None or self.mDownloadPath == '' else self.mDownloadPath
		if self.mDownloadSize > 0:
			size = convert.ConverterSize(value = self.mDownloadSize).stringOptimal(places = convert.ConverterSize.PlacesDouble)
		else:
			size = ''
		accessible = yes if self._fileExists(path) else no
		if self.mDownloadTimeStarted == None or self.mDownloadTimeStarted == '':
			timeCreated = ''
		else:
			timeCreated = convert.ConverterTime(self.mDownloadTimeStarted).string(convert.ConverterTime.FormatDateTime)
		if self.mDownloadTimeUpdated == None or self.mDownloadTimeUpdated == '':
			timeModified = ''
		else:
			timeModified = convert.ConverterTime(self.mDownloadTimeUpdated).string(convert.ConverterTime.FormatDateTime)

		# Download
		status = self.mDownloadStatus.capitalize()
		resumable = yes if self.mDownloadResumable else no
		progressPercentage = '%.1f%%' % self.mProgressPercentageCompleted
		progressSize = convert.ConverterSize(value = self.mProgressSizeCompleted).stringOptimal(places = convert.ConverterSize.PlacesDouble)
		if self.mDownloadSize > 0:
			progressSize += ' ' + self._translate(33073) + ' ' + convert.ConverterSize(value = self.mDownloadSize).stringOptimal(places = convert.ConverterSize.PlacesDouble)
		if self.mDownloadStatus == Downloader.StatusRunning:
			progressSpeed = convert.ConverterSpeed(value = self.mProgressSpeed, unit = convert.ConverterSpeed.Byte).stringOptimal()
			progressTime = convert.ConverterDuration(value = self.mProgressTimeRemaining, unit = convert.ConverterDuration.UnitSecond).string()
		else:
			progressSpeed = ''
			progressTime = ''

		# File
		items.append(self._fontBold(self._fontUppercase(self._translate(33380))))
		items.append(self._fontBold(self._translate(33390) + ': ') + name)
		items.append(self._fontBold(self._translate(33391) + ': ') + extension)
		items.append(self._fontBold(self._translate(33383) + ': ') + size)
		items.append(self._fontBold(self._translate(33384) + ': ') + accessible)
		items.append(self._fontBold(self._translate(33385) + ': ') + timeCreated)
		items.append(self._fontBold(self._translate(33386) + ': ') + timeModified)
		items.append(self._fontBold(self._translate(33381) + ': ') + self._fontItalic(link))
		items.append(self._fontBold(self._translate(33382) + ': ') + self._fontItalic(path))

		# Download
		items.append('')
		items.append(self._fontBold(self._fontUppercase(self._translate(32403))))
		items.append(self._fontBold(self._translate(33389) + ': ') + status)
		items.append(self._fontBold(self._translate(33392) + ': ') + resumable)
		items.append(self._fontBold(self._translate(32037) + ': ') + progressPercentage)
		items.append(self._fontBold(self._translate(33075) + ': ') + progressSize)
		items.append(self._fontBold(self._translate(33074) + ': ') + progressSpeed)
		items.append(self._fontBold(self._translate(33388) + ': ') + progressTime)

		# Dialog
		self._dialogOptions(title = 33379, items = items)

	# Ask user for action to take for "stopping" the download.
	def stop(self, cacheOnly = False):
		if not cacheOnly or self.mType == Downloader.TypeCache:
			if self.mDownloadStatus in [Downloader.StatusQueued, Downloader.StatusInitialized, Downloader.StatusRunning]:
				self._downloadAction(stop = True)
				return True
		return False

	def _stalled(self, updated = None, long = False):
		threshold = Downloader.AliveLimitLong if long else Downloader.AliveLimitShort
		if updated == None:
			updated = self.mDownloadTimeUpdated if not self.mDownloadTimeUpdated == None else 0
		return self._time() - updated > threshold

	def _downloadChoiceManual(self, notification = True, forceAction = False, refresh = False):
		stalledLong = self._stalled(long = True)

		title = None
		message = None

		actionChoice = Downloader.ActionDownloadNew
		actions = []
		actionContinue = self._fontBold(self._translate(33077) + ': ') + self._translate(33285)
		actionHide = self._fontBold(self._translate(33079) + ': ') + self._translate(33080)
		actionResume = self._fontBold(self._translate(33085) + ': ') + self._translate(33086)
		actionRestart = self._fontBold(self._translate(33087) + ': ') + self._translate(33088)
		actionDuplicate = self._fontBold(self._translate(33089) + ': ') + self._translate(33090)
		actionPause = self._fontBold(self._translate(33081) + ': ') + self._translate(33082)
		actionRemove = self._fontBold(self._translate(33286) + ': ') + self._translate(33287)
		actionDelete = self._fontBold(self._translate(33083) + ': ') + self._translate(33084)
		actionStreamContinue = self._fontBold(self._translate(33093) + ': ') + self._translate(33095)
		actionStream = self._fontBold(self._translate(33091) + ': ') + self._translate(33094)
		actionPlay = self._fontBold(self._translate(33091) + ': ') + self._translate(33092)
		actionRefresh = self._fontBold(self._translate(33372) + ': ') + self._translate(33373)
		actionCancel = self._fontBold(self._translate(33288) + ': ') + self._translate(33289)

		if self._fileExists(self.mDownloadPath):
			if self.mDownloadStatus == Downloader.StatusPaused:
				title = 33057
				message = 33278
				actions = [actionRestart, actionDuplicate, actionRemove, actionDelete, actionStreamContinue, actionStream, actionCancel]
				if self.mDownloadResumable:
					actions.insert(0, actionResume)
				if refresh:
					actions.insert(len(actions) - 1, actionRefresh)
			elif self.mDownloadStatus == Downloader.StatusCompleted:
				title = 33053
				message = 33279
				actions = [actionRestart, actionDuplicate, actionRemove, actionDelete, actionStream, actionCancel]
				if refresh:
					actions.insert(len(actions) - 1, actionRefresh)
			elif self.mDownloadStatus == Downloader.StatusFailed:
				title = 33054
				message = 33374
				actions = [actionRestart, actionDuplicate, actionRemove, actionDelete, actionStreamContinue, actionStream, actionCancel]
				if self.mDownloadResumable:
					actions.insert(0, actionResume)
				if refresh:
					actions.insert(len(actions) - 1, actionRefresh)
			elif self.mDownloadStatus in [Downloader.StatusQueued, Downloader.StatusInitialized, Downloader.StatusRunning]:
				if stalledLong:
					title = 33282
					message = 33277
					actions = [actionRestart, actionDuplicate, actionRemove, actionDelete, actionStreamContinue, actionPlay, actionCancel]
					if self.mDownloadResumable:
						actions.insert(0, actionResume)
					if refresh:
						actions.insert(len(actions) - 1, actionRefresh)
				else:
					title = 33283
					message = 33280
					actions = [actionHide, actionContinue, actionRestart, actionDuplicate, actionPause, actionRemove, actionDelete, actionStreamContinue, actionPlay, actionCancel]
					if refresh:
						actions.insert(len(actions) - 1, actionRefresh)
		else:
			path = self.mDownloadPath
			count = 0
			if path == None:
				count, title, name, path = self._file(self.mDownloadTitle, self.mDownloadLink)
			exists = self._fileExists(path, extension = False, exact = False)
			if not exists:
				exists = count > 0

			if exists or forceAction:
				title = 33284
				message = 33281
				actions = [actionRestart, actionDuplicate, actionRemove, actionDelete, actionStreamContinue, actionCancel]
				if refresh:
					actions.insert(len(actions) - 1, actionRefresh)

		# Used in download() for pause/stop actions.
		if stalledLong and self.mDownloadStatus in [Downloader.StatusQueued, Downloader.StatusInitialized, Downloader.StatusRunning]:
			self._updateStatus(Downloader.StatusPaused)
			self.mDownloadStatus = Downloader.StatusPaused

		if len(actions) > 0:
			if notification:
				message = self._translate(message) % self._type(lower = True)
				self._dialogConfirm(message = message, title = title, internal = False)

			actionChoice = self._dialogOptions(title = 33096, items = actions, internal = False)
			if actionChoice >= 0:
				actionChoice = actions[actionChoice]
				if actionChoice == actionContinue:
					actionChoice = Downloader.ActionContinue
				elif actionChoice == actionHide:
					actionChoice = Downloader.ActionHide
				elif actionChoice == actionResume:
					actionChoice = Downloader.ActionResume
				elif actionChoice == actionRestart:
					actionChoice = Downloader.ActionRestart
				elif actionChoice == actionDuplicate:
					actionChoice = Downloader.ActionDuplicate
				elif actionChoice == actionPause:
					actionChoice = Downloader.ActionPause
				elif actionChoice == actionRemove:
					actionChoice = Downloader.ActionRemove
				elif actionChoice == actionDelete:
					actionChoice = Downloader.ActionDelete
				elif actionChoice == actionStreamContinue:
					actionChoice = Downloader.ActionStream
				elif actionChoice == actionStream or actionChoice == actionPlay:
					actionChoice = Downloader.ActionPlay
				elif actionChoice == actionRefresh:
					actionChoice = Downloader.ActionRefresh
				elif actionChoice == actionCancel:
					actionChoice = Downloader.ActionCancel
			else: # -1: Cancel button clicked.
				actionChoice = Downloader.ActionCancel

		return actionChoice

	def _downloadChoiceCache(self):
		stalledLong = self._stalled(long = True)
		actionChoice = Downloader.ActionDownloadNew

		if self._fileExists(self.mDownloadPath):
			if self.mDownloadStatus == Downloader.StatusPaused or self.mDownloadStatus == Downloader.StatusFailed:
				if self.mDownloadResumable:
					action = Downloader.ActionResume
				else:
					action = Downloader.ActionRestart
			elif self.mDownloadStatus == Downloader.StatusCompleted:
				actionChoice = Downloader.ActionStream
			elif self.mDownloadStatus in [Downloader.StatusQueued, Downloader.StatusInitialized, Downloader.StatusRunning]:
				if stalledLong:
					if self.mDownloadResumable:
						action = Downloader.ActionResume
					else:
						action = Downloader.ActionRestart
				else:
					action = Downloader.ActionContinue
		else:
			path = self.mDownloadPath
			count = 0
			if path == None:
				count, title, name, path = self._file(self.mDownloadTitle, self.mDownloadLink)
			exists = self._fileExists(path, extension = False, exact = False)
			if not exists:
				exists = count > 0
			if exists:
				action = Downloader.ActionDuplicate

	def _downloadChoiceStop(self):
		actionChoice = Downloader.ActionCancel
		actionContinue = self._fontBold(self._translate(33077) + ': ') + self._translate(33285)
		actionPause = self._fontBold(self._translate(33081) + ': ') + self._translate(33082)
		actionRemove = self._fontBold(self._translate(33286) + ': ') + self._translate(33287)
		actionDelete = self._fontBold(self._translate(33083) + ': ') + self._translate(33084)
		actions = [actionContinue, actionPause, actionRemove, actionDelete]

		self._dialogNotify(message = 33378, title = 33283, internal = False)
		actionChoice = self._dialogOptions(title = 33096, items = actions, internal = False)
		if actionChoice >= 0:
			actionChoice = actions[actionChoice]
			if actionChoice == actionContinue:
				actionChoice = Downloader.ActionContinue
			elif actionChoice == actionPause:
				actionChoice = Downloader.ActionPause
			elif actionChoice == actionRemove:
				actionChoice = Downloader.ActionRemove
			elif actionChoice == actionDelete:
				actionChoice = Downloader.ActionDelete
		return actionChoice

	def _downloadAction(self, notification = True, forceAction = False, refresh = False, automatic = False, stop = False):
		if stop:
			action = self._downloadChoiceStop()
		elif self.mType == Downloader.TypeCache and automatic:
			action = self._downloadChoiceCache()
		else:
			action = self._downloadChoiceManual(notification, forceAction, refresh)

		if action == Downloader.ActionContinue:
			self._run(Downloader.ActionObserve)
		elif action == Downloader.ActionResume:
			self._run(Downloader.ActionDownload)
		elif action == Downloader.ActionRestart:
			if self.mDownloadStatus in [Downloader.StatusQueued, Downloader.StatusInitialized, Downloader.StatusRunning] and not self._stalled(long = False):
				self._updateCommand(Downloader.CommandPause) # Otherwise the download continues and below the file is tried to be deleted.
				time.sleep(Downloader.AliveUpdate * 1.5)

			if self.mDownloadId == None:
				count, title, name, self.mDownloadPath = self._file(self.mDownloadTitle, self.mDownloadLink)
				path = self._fileFind(os.path.dirname(self.mDownloadPath), self.mDownloadTitle, exact = False)
				self.mDownloadId = self._selectFind(path)
				oldLink = self.mDownloadLink
				oldHeaders = self.mDownloadHeaders
				oldImage = self.mDownloadImage
				oldMetadata = self.mDownloadMetadata
				oldSource = self.mDownloadSource
				self._load(self.mDownloadId)
				self.mDownloadLink = oldLink
				self.mDownloadHeaders = oldHeaders
				self.mDownloadImage = oldImage
				self.mDownloadMetadata = oldMetadata
				self.mDownloadSource = oldSource

			self._fileDelete(self.mDownloadPath)
			self.mDownloadTimeStarted = self._time()
			self.mDownloadSize = 0
			self.mDownloadResumable = False
			self.mProgressPercentageCompleted = 0
			self.mProgressPercentageRemaining = 100
			self.mProgressSizeCompleted = 0
			self.mProgressSizeRemaining = 0
			self.mProgressTimeCompleted = 0
			self.mProgressTimeRemaining = 0
			self.mProgressSpeed = 0
			if self.mDownloadPath == None:
				self._notification((33063, 33068), Downloader.StatusFailed)
				return False
			self._updateDownload(updated = self.mDownloadTimeStarted, full = True)
			self._run(Downloader.ActionDownload)
		elif action == Downloader.ActionDuplicate:
			count, title, name, path = self._file(self.mDownloadTitle, self.mDownloadLink)
			if path == None:
				self._notification((33063, 33068), Downloader.StatusFailed)
				return False
			self._insertDownload(self.mDownloadLink, self.mDownloadMedia, title, name, path, image = self.mDownloadImage, headers = self.mDownloadHeaders, metadata = self.mDownloadMetadata, source = self.mDownloadSource)
			self._load()
			self._run(Downloader.ActionDownloadNew)
		elif action == Downloader.ActionPause:
			if self.mDownloadStatus == Downloader.StatusRunning:
				self._updateCommand(Downloader.CommandPause)
			else:
				self._updateStatus(Downloader.StatusPaused)
			return False
		elif action == Downloader.ActionRemove:
			if self.mDownloadStatus == Downloader.StatusRunning and not self._stalled(long = True): # Stalled must be long, otherwise cannot delete from cache playback stopped.
				self._updateCommand(Downloader.CommandRemove)
			else:
				self._updateStatus(Downloader.StatusRemoved)
			return False
		elif action == Downloader.ActionDelete:
			if self.mDownloadStatus == Downloader.StatusRunning and not self._stalled(long = True): # Stalled must be long, otherwise cannot delete from cache playback stopped.
				self._updateCommand(Downloader.CommandDelete)
			else:
				self._fileDelete(self.mDownloadPath, deleteParent = True)
				self._updateStatus(Downloader.StatusRemoved)
			return False
		elif action == Downloader.ActionStream:
			if self._stalled(long = True) or self.mDownloadStatus == Downloader.StatusPaused:
				self._run(Downloader.ActionDownload, observation = False)
			self._play()
			return False # Do not return path, because that might cause play, and play was already called above.
		elif action == Downloader.ActionPlay:
			if self.mDownloadStatus in [Downloader.StatusQueued, Downloader.StatusInitialized, Downloader.StatusRunning]:
				self._updateCommand(Downloader.CommandPause)
			self._play(buffering = False)
			return False # Do not return path, because that might cause play, and play was already called above.
		elif action == Downloader.ActionRefresh:
			self.itemsRefresh()
			return False
		elif action == Downloader.ActionCancel or action == Downloader.ActionHide:
			return False
		else:
			count, title, name, path = self._file(self.mDownloadTitle, self.mDownloadLink)
			if path == None:
				self._notification((33063, 33068), Downloader.StatusFailed)
				return False
			self._insertDownload(self.mDownloadLink, self.mDownloadMedia, title, name, path, image = self.mDownloadImage, headers = self.mDownloadHeaders, metadata = self.mDownloadMetadata, source = self.mDownloadSource)
			self._load()
			self._run(Downloader.ActionDownloadNew)

		return True

	# If title == None, will automatically extract title from metadata if present.
	# If image == None, will automatically extract image from metadata if present.
	def download(self, media = None, link = None, title = None, image = None, metadata = None, source = None, id = None, forceAction = False, refresh = False, automatic = False):
		if id == None:
			id = self.mDownloadId

		if id == None:
			if link == None or link == '':
				self._notification((33062, 33067), Downloader.StatusFailed)
				return False

			self.mDownloadLink = link.split('|')[0]
			self.mDownloadMetadata = metadata

			if source and 'metadata' in source: # Not serializable.
				del source['metadata']
			self.mDownloadSource = source

			# Media
			self.mDownloadMedia = media

			# Title
			# Always overwrite the title to ensure that it contains all info, irrespective of which label format the user selected in the settings.
			#if not metadata == None and title == None or title == '':
			if not metadata == None:
				if 'tvshowtitle' in metadata and 'season' in metadata and 'episode' in metadata:
					title = '%s S%02dE%02d' % (metadata['tvshowtitle'], int(metadata['season']), int(metadata['episode']))
				elif 'title' in metadata and 'year' in metadata:
					title = '%s (%s)' % (metadata['title'], metadata['year'])

			if not title:
				try: title = urllib.unquote(self.mDownloadLink.split('/')[-1])
				except: title =  Downloader.AddonName + ' Download'

			self.mDownloadTitle = title

			if self.mDownloadTitle == None:
				self._notification((33062, 33067), Downloader.StatusFailed)
				return False

			# Image
			if not metadata == None:
				keys = ['poster', 'poster1', 'poster2', 'poster3', 'thumb', 'thumb1', 'thumb2', 'thumb3', 'icon', 'icon1', 'icon2', 'icon3']
				for key in keys:
					if key in metadata:
						value = metadata[key]
						if not value == None and not value == '':
							image = value
							break
			self.mDownloadImage = image

			notification = True
		else:
			notification = False

		try:
			if not self._enabled():
				self._notification((33061, 33066), Downloader.StatusFailed)
				return False

			try: self.mDownloadHeaders = dict(urlparse.parse_qsl(link.rsplit('|', 1)[1]))
			except: self.mDownloadHeaders = dict('')

			if id == None:
				id = self._selectId()
			exists = not id == None
			if exists:
				self._load(id)

			if self._downloadAction(notification = notification, forceAction = forceAction, refresh = refresh, automatic = automatic):
				return self.mDownloadPath
			else:
				return False
		except:
			return False

	def start(self, comfirmation = False, observation = True):
		self._updateStatus(Downloader.StatusInitialized)
		self._progressIntialize()

		# Keep alive
		thread = threading.Thread(target = self._aliveUpdate)
		thread.start()

		file = self.mDownloadPath.rsplit(os.sep, 1)[-1]
		response = self._response(self.mDownloadLink, self.mDownloadHeaders, self.mProgressSizeCompleted)

		if not response:
			self._updateStatus(Downloader.StatusFailed)
			self._notification((33064, 33069), Downloader.StatusFailed)
			return False

		# Only check size the first time. Because if the download is started from a specific position (resumebale), then Content-Length is the size of the remainer of the request, not the size of the entire file.
		if self.mDownloadSize  == None or self.mDownloadSize == 0:
			try: self.mDownloadSize = int(response.headers['Content-Length'])
			except: self.mDownloadSize = 0

		# Free cache storage.
		if self.mType == Downloader.TypeCache and not self._cacheFree(self.mDownloadSize):
			self._updateStatus(Downloader.StatusFailed)
			self._notification((33365, 33366), Downloader.StatusFailed)
			return False

		# Only update resumable if not yet set or false. When downloads are resumed with byte-range, the server will not reply with Accept-Ranges, although the download is still resumable.
		if self.mDownloadResumable  == None or self.mDownloadResumable == False:
			try: self.mDownloadResumable = 'bytes' in response.headers['Accept-Ranges'].lower()
			except: self.mDownloadResumable = False

		self._updateDownload() # For size and resumable

		if comfirmation and self._setting('confirmation') == 'true':
			base = 33051 if self.mType == Downloader.TypeManual else 33052
			base = self._translate(base).lower()
			if self.mDownloadSize > 0:
				size = convert.ConverterSize(value = self.mDownloadSize).stringOptimal(places = convert.ConverterSize.PlacesDouble)
				message = self._translate(33275) % (base, self.mDownloadTitle, size)
			else:
				message = self._translate(33276) % (base, self.mDownloadTitle)
			if not self._dialogOption(title = 33274, message = message):
				self._updateStatus(Downloader.StatusRemoved)
				self._fileDelete(self.mDownloadPath, deleteParent = True)
				return False

		if observation:
			self._run(Downloader.ActionObserve)

		chunk = None
		chunks = []
		errors = 0
		count = 0
		resume = 0
		sleep = 0

		# xbmcvfs.File does not support append mode.
		if self._fileExists(self.mDownloadPath):
			oldPath = self.mDownloadPath + '.old'
			self._fileMove(self.mDownloadPath, oldPath)
			oldFile = xbmcvfs.File(oldPath)

			self.mFile = xbmcvfs.File(self.mDownloadPath, 'w')
			self.mFile.seek(self.mDownloadSize - 1, 0)
			self.mFile.write('\0')
			self.mFile.seek(0, 0)

			while True:
				data = oldFile.read(Downloader.ChunkSizeRead)
				if data == None or len(data) == 0:
					break
				self.mFile.write(data)
			oldFile.close()
			time.sleep(1) # Wait for lock to release.
			self._fileDelete(oldPath)
		else:
			self.mFile = xbmcvfs.File(self.mDownloadPath, 'w')
			self.mFile.seek(self.mDownloadSize - 1, 0)
			self.mFile.write('\0')
		self.mFile.seek(self.mProgressSizeCompleted, 0)

		self._updateStatus(Downloader.StatusRunning)
		while True:

			# Commands
			command = self._selectCommand()
			if command == Downloader.CommandPause:
				self.mFile.close()
				self._updateStatus(Downloader.StatusPaused)
				return False
			elif command == Downloader.CommandRemove:
				self.mFile.close()
				self._updateStatus(Downloader.StatusRemoved)
				return False
			elif command == Downloader.CommandDelete:
				self.mFile.close()
				time.sleep(2) # Wait for lock to be released.
				self._fileDelete(self.mDownloadPath, deleteParent = True)
				self._updateStatus(Downloader.StatusRemoved)
				return False

			downloaded = self.mProgressSizeCompleted

			for chunkSingle in chunks:
				downloaded += len(chunkSingle)

			percent = int(min((downloaded / float(self.mDownloadSize)) * 100, 100))
			chunk = None
			error = False

			try:
				chunk = response.read(Downloader.ChunkSizeRead)
				if not chunk:
					if percent < 99:
						error = True
					else:
						while len(chunks) > 0:
							chunkSingle = chunks.pop(0)
							self.mFile.write(chunkSingle)
							del chunkSingle
						self.mFile.close()
						self._finish()
						return True

			except Exception as exception:
				error = True
				errorNumber = 0
				sleep = 10

				if hasattr(exception, 'errno'):
					errorNumber = exception.errno

				# A non-blocking socket operation could not be completed immediately.
				if errorNumber == 10035:
					pass

				# An existing connection was forcibly closed by the remote host.
				if errorNumber == 10054:
					errors = 10 # Force resume.
					sleep = 30

				# getaddrinfo failed
				if errorNumber == 11001:
					errors = 10 # Force resume.
					sleep = 30

			if chunk:
				errors = 0
				chunks.append(chunk)
				if len(chunks) * Downloader.ChunkSizeRead >= Downloader.ChunkSizeWrite:
					chunkSingle = chunks.pop(0)
					self.mFile.write(chunkSingle)
					chunkSize = len(chunkSingle)
					del chunkSingle
					self._progressAppend(chunkSize)

			if error:
				errors += 1
				count += 1
				time.sleep(sleep)

			if (self.mDownloadResumable and errors > 0) or errors >= 10:
				if (not self.mDownloadResumable and resume >= 50) or resume >= 500: # Give up
					self.mFile.close()
					self._updateStatus(Downloader.StatusFailed)
					self._notification((33098, 33099), Downloader.StatusFailed)
					return False

				resume += 1
				errors = 0
				if self.mDownloadResumable:
					chunks = []
					response = self._response(self.mDownloadLink, self.mDownloadHeaders, self.mProgressSizeCompleted) # Create new response
				else:
					pass # Use existing response

		self.mFile.close()
		return False

	def _play(self, buffering = True):
		self._loaderShow()
		if buffering:
			command = 'RunPlugin(plugin://%s/?action=playLocal&type=%s&downloadType=%s&downloadId=%s&path=%s&metadata=%s&source=%s)' % (Downloader.AddonId, self.mDownloadMedia, urllib.quote_plus(self.mType), urllib.quote_plus(self.mDownloadId), urllib.quote_plus(self.mDownloadPath), urllib.quote_plus(json.dumps(self.mDownloadMetadata)), urllib.quote_plus(json.dumps(self.mDownloadSource)))
		else:
			command = 'RunPlugin(plugin://%s/?action=playLocal&type=%s&path=%s&metadata=%s&source=%s)' % (Downloader.AddonId, self.mDownloadMedia, urllib.quote_plus(self.mDownloadPath), urllib.quote_plus(json.dumps(self.mDownloadMetadata)), urllib.quote_plus(json.dumps(self.mDownloadSource)))
		xbmc.executebuiltin(command)

	def _observeCreate(self):
		self._observeClose()
		title = 33059
		message = self._fontBold(self._translate(33072))
		if self.mProgressType == Downloader.ProgressForeground:
			self.mProgressTitle = self._title(extension = title, name = True)
			self.mProgressDialog = self._dialogProgress(message = message, background = False, title = self.mProgressTitle, internal = True)
		elif self.mProgressType == Downloader.ProgressBackground:
			self.mProgressTitle = self._title(extension = title, name = False)
			self.mProgressDialog = self._dialogProgress(message = message, background = True, title = self.mProgressTitle, internal = True)
		else:
			self.mProgressDialog = None

	def _observeClose(self):
		try:
			self.mProgressDialog.close()
			self.mProgressDialog = None
		except:
			pass

	def observe(self):
		self.mProgressDialog = None
		self.mProgressTitle = None

		self.mProgressType = int(self._setting('progress'))
		if self.mProgressType == 1:
			self.mProgressType = Downloader.ProgressInterval
		elif self.mProgressType == 2:
			self.mProgressType = Downloader.ProgressForeground
		elif self.mProgressType == 3:
			self.mProgressType = Downloader.ProgressBackground
		else:
			self.mProgressType = Downloader.ProgressNone

		self._observeCreate()
		progressLast = 0
		dots = 0
		initialized = False

		while True:
			try:
				try: canceled = self.mProgressDialog.iscanceled()
				except: canceled = False
				if canceled:
					self._observeClose()
					try: cancel = self._downloadAction(notification = False, forceAction = True)
					except: cancel = False
					if cancel:
						self._observeCreate()
					else:
						break
			except:
				pass

			if not self._load():
				break

			if not self.mDownloadStatus in [Downloader.StatusQueued, Downloader.StatusInitialized, Downloader.StatusRunning]:
				self._observeClose()
				break

			if self.mDownloadStatus in [Downloader.StatusQueued, Downloader.StatusInitialized]:
				if self.mProgressDialog == None:
					if not initialized:
						initialized = True
						title = self._title(extension = 33059, name = True)
						self._dialogNotify(title = title, message = 33072)
				else:
					dots += 1
					if dots > 3: dots = 0
					progress = int(self.mProgressPercentageCompleted)
					line = self._fontBold(self._translate(33072) + ' ' + ('.' * dots))
					empty = ' '
					self.mProgressDialog.update(progress, line, empty, empty)
			elif self.mProgressSpeed > 0:
				progress = int(self.mProgressPercentageCompleted)
				speed = self._fontBold(self._translate(33074) + ': ') + convert.ConverterSpeed(value = self.mProgressSpeed, unit = convert.ConverterSpeed.Byte).stringOptimal()
				size = self._fontBold(self._translate(33075) + ': ') + convert.ConverterSize(value = self.mProgressSizeCompleted).stringOptimal(places = convert.ConverterSize.PlacesDouble)

				line1 = ''
				line2 = ''
				line3 = ''

				if self.mDownloadSize > 0:
					size += ' ' + self._translate(33073) + ' ' + convert.ConverterSize(value = self.mDownloadSize).stringOptimal(places = convert.ConverterSize.PlacesDouble)
					timeString = convert.ConverterDuration(value = self.mProgressTimeRemaining, unit = convert.ConverterDuration.UnitSecond).string()
					timeRemaining = self._fontBold(self._translate(33388) + ': ') + timeString
					line1 = speed
					line2 = timeRemaining
					line3 = size
				else:
					line1 = speed
					line2 = size

				if self.mProgressDialog == None:
					if progressLast == 0 or progress - progressLast >= Downloader.NotificationInterval:
						progressLast += Downloader.NotificationInterval
						title = self._title(extension = 33059, name = True)
						message = '%s%%' % progress
						if self.mDownloadSize > 0:
							message += ' - %s: %s' % (self._translate(33367), timeString)
						self._dialogNotify(title = title, message = message)
				else:
					self.mProgressDialog.update(progress, line1, line2, line3)

			time.sleep(0.5)

	def _progressIntialize(self):
		self.mProgressTimeStarted = self._time()
		self.mProgressTimeRunning = self.mProgressTimeCompleted # If resumed and time already in the database.
		self.mProgressSizes = []

	def _progressAppend(self, size):
		self.mProgressSizeCompleted += size
		self.mProgressSizes.append((self._time(), size))
		self._progressUpdate()

	def _progressUpdateSize(self):
		self.mProgressSizeRemaining = self.mDownloadSize - self.mProgressSizeCompleted

	def _progressUpdatePercentage(self):
		self.mProgressPercentageRemaining = (self.mProgressSizeRemaining / float(self.mDownloadSize)) * 100
		self.mProgressPercentageCompleted = 100 - self.mProgressPercentageRemaining

	def _progressUpdateSpeed(self):
		# Delete outdated sizes.
		updated = self._time() - Downloader.SpeedDuration
		key = self.mProgressSizes[0][0] if len(self.mProgressSizes) > 0 else None
		while len(self.mProgressSizes) > 0 and self.mProgressSizes[0][0] < updated:
			self.mProgressSizes.pop(0)

		# Calculate new speed.
		total = 0
		for size in self.mProgressSizes:
			total += size[1]
		try: updated = max(1, self.mProgressSizes[-1][0] - self.mProgressSizes[0][0])
		except: updated = 1
		self.mProgressSpeed = int(total / float(updated))

	def _progressUpdateTime(self):
		self.mProgressTimeCompleted = self.mProgressTimeRunning + (self._time() - self.mProgressTimeStarted)
		self.mProgressTimeRemaining = self.mProgressSizeRemaining / self.mProgressSpeed

	def _progressUpdate(self):
		self._progressUpdateSize()
		self._progressUpdatePercentage()
		self._progressUpdateSpeed()
		self._progressUpdateTime()
		self._updateDownload()

	def _finish(self):
		self._updateStatus(Downloader.StatusCompleted)
		self._updateDownload() # Make sure everything is updated.
		self._notification((33097, 33070), Downloader.StatusCompleted)

	def _updateLibrary(self, oldStatus = None):
		started = self.mDownloadStatus == Downloader.StatusRunning and (oldStatus == None or oldStatus == Downloader.StatusInitialized) and (self.mProgressSizeCompleted == None or self.mProgressSizeCompleted == 0)
		completed = self.mDownloadStatus == Downloader.StatusCompleted and (oldStatus == None or oldStatus == Downloader.StatusRunning)
		removed = self.mDownloadStatus == Downloader.StatusRemoved

		setting = int(self._setting('update'))
		if setting == 0: # Disabled
			return False
		elif setting == 1 and not started: # Started
			return False
		elif setting == 2 and not completed: # Completed
			return False
		elif setting == 3 and not removed: # Removed
			return False
		elif setting == 4 and not (started or removed): # Started and Removed
			return False
		elif setting == 5 and not (completed or removed): # Completed and Removed
			return False

		if self.mDownloadMetadata:
			if 'tvshowtitle' in self.mDownloadMetadata and not self.mDownloadMetadata['tvshowtitle'] == None and not self.mDownloadMetadata['tvshowtitle'] == '':
				path = [self._locationShows()]
			else:
				path = [self._locationMovies(), self._locationDocumentaries(), self._locationShorts()]
			path.append(self._locationOther())
			if removed:
				xbmc.executebuiltin('CleanLibrary(video)')
			else:
				# Updating specific paths creates problems, since the user might have a special:// path in Gaia settings and a C:/ path in the Kodi library.
				# Kodi does not see these two paths as the same, and will therefore not update the library.
				# Scan the entire library instead.
				'''path = list(set(path))
				for p in path:
					xbmc.executebuiltin('UpdateLibrary(video,%s)' % p)'''
				xbmc.executebuiltin('UpdateLibrary(video)')
			return True
		else:
			return False

	def _cacheSizeMaximum(self):
		size = int(self._setting('size'))
		if size == 1: # 10 GB
			size = 10737418240
		elif size == 2: # 20 GB
			size = 21474836480
		elif size == 3: # 50 GB
			size = 53687091200
		elif size == 4: # 100 GB
			size = 107374182400
		elif size == 5: # 150 GB
			size = 161061273600
		elif size == 6: # 200 GB
			size = 214748364800
		elif size == 7: # 250 GB
			size = 268435456000
		elif size == 8: # 300 GB
			size = 322122547200
		elif size == 9: # 350 GB
			size = 375809638400
		elif size == 10: # 400 GB
			size = 429496729600
		elif size == 11: # 450 GB
			size = 483183820800
		elif size == 12: # 500 GB
			size = 536870912000
		elif size == 13: # 600 GB
			size = 644245094400
		elif size == 14: # 700 GB
			size = 751619276800
		elif size == 15: # 800 GB
			size = 858993459200
		elif size == 16: # 900 GB
			size = 966367641600
		elif size == 17: # 1 TB
			size = 1099511627776
		elif size == 18: # 1.5 TB
			size = 1649267441664
		elif size == 19: # 2 TB
			size = 2199023255552
		elif size == 20: # 2.5 TB
			size = 2748779069440
		elif size == 21: # 3 TB
			size = 3298534883328
		elif size == 22: # 3.5 TB
			size = 3848290697216
		elif size == 23: # 4 TB
			size = 4398046511104
		elif size == 24: # 4.5 TB
			size = 4947802324992
		elif size == 25: # 5 TB
			size = 5497558138880
		else:
			size = 0
		return size

	def _cacheSizeUsed(self):
		paths = list(set([self._locationMovies(), self._locationShows(), self._locationDocumentaries(), self._locationShorts(), self._locationOther()]))
		result = 0
		for path in paths:
			result += self._cacheSizeDirectory(path)
		return result

	def _cacheSizeFree(self):
		size = self._cacheSizeMaximum()
		if size == 0:
			return None
		size -= self._cacheSizeUsed()
		if size < 0: size = 0
		return size

	def _cacheSizeDirectory(self, path):
		size = 0
		for item in self._cacheList(path):
			size += item['size']
		return size

	def _cacheList(self, path, list = None):
		result = []
		directories, files = self._fileList(path)
		for file in files:
			filePath = os.path.join(path, file)
			stats = xbmcvfs.Stat(filePath)
			result.append({'path' : filePath, 'size' : stats.st_size(), 'modified' : stats.st_mtime(), 'accessed' : stats.st_atime()})
		for directory in directories:
			result.extend(self._cacheList(os.path.join(path, directory)))
		return result

	def _cacheListSorted(self, path, sort = None, list = None):
		if sort == None:
			mode = int(self._setting('removal'))
			if mode == 1:
				sort = Downloader.SortModified
			elif mode == 2:
				sort = Downloader.SortAccessed
			elif mode == 3:
				sort = Downloader.SortSizeSmallest
			elif mode == 4:
				sort = Downloader.SortSizeLargest

		if list == None:
			list = self._cacheList(path)
		key = None
		reverse = False

		if sort == Downloader.SortModified:
			key = 'modified'
		elif sort == Downloader.SortAccessed:
			key = 'accessed'
		elif sort == Downloader.SortSizeSmallest:
			key = 'size'
		elif sort == Downloader.SortSizeLargest:
			key = 'size'
			reverse = True
		else: # Removal Mode == None
			return []

		return sorted(list, key = lambda k: k[key], reverse = reverse)

	def _cacheStorageFree(self, path):
		try:
			system = platform.system().lower()
			if system == 'windows' or system == 'nt':
				# http://stackoverflow.com/questions/51658/cross-platform-space-remaining-on-volume-using-python
				import ctypes

				# Convert samba paths to Windows network path, because smb:// paths can not be handled by ctypes
				if path.startswith(Downloader.PrefixSamba):
					path = path.replace(Downloader.PrefixSamba, '\\\\').replace('/', '\\')

				free = ctypes.c_ulonglong(0)
				ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(path), None, None, ctypes.pointer(free))
				return free.value
			else:
				if path.startswith(Downloader.PrefixSamba):
					import subprocess
					passwords = self._fileRead(Downloader.PrefixSpecial + 'userdata/passwords.xml')
					username = None
					password = None
					if not passwords == None:
						import xml.etree.ElementTree
						pathLower = path.lower()
						tree = xml.etree.ElementTree.fromstring(passwords)
						for item in tree.findall('path'):
							if pathLower.startswith(item.find('from').text.lower()):
								pathLogin = item.find('to').text
								indexStart = pathLogin.find('//')
								if indexStart >= 0:
									indexStart += 2
									indexEnd = pathLogin.find(':', indexStart)
									if indexEnd >= 0:
										username = pathLogin[indexStart : indexEnd]
										indexStart = indexEnd + 1
										indexEnd = pathLogin.find('@', indexStart)
										if indexEnd >= 0:
											password = pathLogin[indexStart : indexEnd]

					# smbclient needs Windows path notation. Everything needs to be double, since the string is passed twice (Python and terminal smbclient).
					path = path.replace(Downloader.PrefixSamba, '').replace('\\', '\\\\').replace('/', '\\\\')

					# Only use the root share directory, otherwise smbclient cannot resolve the path.
					indexStart = path.find('\\\\')
					if indexStart > 0:
						indexStart += 2
						indexStart = path.find('\\\\', indexStart) # Second occurance
						if indexStart > 0:
							path = path[:indexStart]

					# Add the \\ for Windows path notation.
					path = '\\\\\\\\' + path

					command = 'echo "dir" | smbclient ' + path
					if not username == None:
						command += ' -U=' + username
						if not password == None:
							command += '%' + password
					process = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
					result = process.stdout.read().decode('utf-8')

					indexStart = result.find('blocks of size ')
					if indexStart >= 0:
						indexStart += 15
						indexEnd = result.find('.', indexStart)
						if indexEnd >= 0:
							sizeBlock = int(result[indexStart : indexEnd])
							indexStart = indexEnd + 2
							indexEnd = result.find(' ', indexStart)
							if indexEnd >= 0:
								sizeFree = int(result[indexStart : indexEnd])
								return sizeFree * sizeBlock
				else:
					stats = os.statvfs(path)
					return stats.f_bavail * stats.f_frsize
		except:
			pass
		return -1

	def _cacheDelete(self, path, sizeNew, sizeFree, list = None):
		if list == None:
			list = self._cacheListSorted(path)

		for file in list:
			if sizeFree > sizeNew:
				break
			sizeFree += file['size']
			self._fileDelete(file['path'], force = True, deleteParent = True)

	def _cacheFree(self, size):
		if not self._enabled(full = True):
			return False

		if size == 0: # If unknown download size, use 1 GB free space.
			size = 1073741824
		size += 52428800 # Always keep 50 MB free.

		if int(self._setting('removal')) == 0: # No removals.
			return True
		else:
			path = self._location()
			list = self._cacheListSorted(path)
			storage = self._cacheStorageFree(path)
			if storage > 0:
				sizeFree = self._cacheSizeFree()
				if not sizeFree == None:
					sizeFree = min(storage, sizeFree)
					self._cacheDelete(path, size, sizeFree, list)
					return self._cacheStorageFree(path) > size

			# If the free space can not be retrieved, just continue with the download. The user must manually clear up the cache.
			return True

if __name__ == '__main__':
	if 'downloader.py' in sys.argv[0]:
		action = urllib.unquote_plus(sys.argv[1])
		type = urllib.unquote_plus(sys.argv[2])
		id = urllib.unquote_plus(sys.argv[3])
		observation = sys.argv[4] == 1 or sys.argv[4] == True or sys.argv[4] == '1' or sys.argv[4].lower() == 'true'
		downer = Downloader(type = type, id = id)
		if action == Downloader.ActionDownload:
			downer.start(comfirmation = False, observation = observation)
		elif action == Downloader.ActionDownloadNew:
			downer.start(comfirmation = True, observation = observation)
		elif action == Downloader.ActionObserve:
			downer.observe()
