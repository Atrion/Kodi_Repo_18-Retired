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
# ORIONTOOLS
##############################################################################
# Class for additional utilities.
##############################################################################

import re
import os
import sys
import json
import time
import stat
import shutil
import datetime
import random
import hashlib
import urllib
import urlparse
import traceback
import webbrowser
import subprocess
import xbmc
import xbmcaddon
import xbmcvfs

class OrionTools:

	##############################################################################
	# CONSTANTS
	##############################################################################

	# Must be set manual in order to retrieve addon info through Kodi.
	# Otherwise Kodi uses the addon ID that is calling Orion.
	Id = 'script.module.orion'

	LogNotice = xbmc.LOGNOTICE
	LogError = xbmc.LOGERROR
	LogSevere = xbmc.LOGSEVERE
	LogFatal = xbmc.LOGFATAL
	LogDefault = LogNotice

	FormatDateTime = '%Y-%m-%d %H:%M:%S'
	FormatDate = '%Y-%m-%d'
	FormatTime = '%H:%M:%S'

	PrefixPlugin = 'plugin://'

	LanguageNames = ['Abkhaz', 'Afar', 'Afrikaans', 'Akan', 'Albanian', 'Amharic', 'Arabic', 'Aragonese', 'Armenian', 'Assamese', 'Avaric', 'Avestan', 'Aymara', 'Azerbaijani', 'Bambara', 'Bashkir', 'Basque', 'Belarusian', 'Bengali', 'Bihari', 'Bislama', 'Bokmal', 'Bosnian', 'Breton', 'Bulgarian', 'Burmese', 'Catalan', 'Chamorro', 'Chechen', 'Chichewa', 'Chinese', 'Chuvash', 'Cornish', 'Corsican', 'Cree', 'Croatian', 'Czech', 'Danish', 'Divehi', 'Dutch', 'Dzongkha', 'English', 'Esperanto', 'Estonian', 'Ewe', 'Faroese', 'Fijian', 'Finnish', 'French', 'Fula', 'Gaelic', 'Galician', 'Ganda', 'Georgian', 'German', 'Greek', 'Guarani', 'Gujarati', 'Haitian', 'Hausa', 'Hebrew', 'Herero', 'Hindi', 'Hiri Motu', 'Hungarian', 'Icelandic', 'Ido', 'Igbo', 'Indonesian', 'Interlingua', 'Interlingue', 'Inuktitut', 'Inupiaq', 'Irish', 'Italian', 'Japanese', 'Javanese', 'Kalaallisut', 'Kannada', 'Kanuri', 'Kashmiri', 'Kazakh', 'Khmer', 'Kikuyu', 'Kinyarwanda', 'Kirundi', 'Komi', 'Kongo', 'Korean', 'Kurdish', 'Kwanyama', 'Kyrgyz', 'Lao', 'Latin', 'Latvian', 'Limburgish', 'Lingala', 'Lithuanian', 'Luba-Katanga', 'Luxembourgish', 'Macedonian', 'Malagasy', 'Malay', 'Malayalam', 'Maltese', 'Manx', 'Maori', 'Marathi', 'Marshallese', 'Mongolian', 'Nauruan', 'Navajo', 'Ndonga', 'Nepali', 'Northern Ndebele', 'Northern Sami', 'Norwegian', 'Nuosu', 'Nynorsk', 'Occitan', 'Ojibwe', 'Oriya', 'Oromo', 'Ossetian', 'Pali', 'Pashto', 'Persian', 'Polish', 'Portuguese', 'Punjabi', 'Quechua', 'Romanian', 'Romansh', 'Russian', 'Samoan', 'Sango', 'Sanskrit', 'Sardinian', 'Serbian', 'Shona', 'Sindhi', 'Sinhalese', 'Slavonic', 'Slovak', 'Slovene', 'Somali', 'Southern Ndebele', 'Southern Sotho', 'Spanish', 'Sundanese', 'Swahili', 'Swati', 'Swedish', 'Tagalog', 'Tahitian', 'Tajik', 'Tamil', 'Tatar', 'Telugu', 'Thai', 'Tibetan', 'Tigrinya', 'Tonga', 'Tsonga', 'Tswana', 'Turkish', 'Turkmen', 'Twi', 'Ukrainian', 'Urdu', 'Uyghur', 'Uzbek', 'Venda', 'Vietnamese', 'Volapuk', 'Walloon', 'Welsh', 'Western Frisian', 'Wolof', 'Xhosa', 'Yiddish', 'Yoruba', 'Zhuang', 'Zulu']
	LanguageCodes = ['ab', 'aa', 'af', 'ak', 'sq', 'am', 'ar', 'an', 'hy', 'as', 'av', 'ae', 'ay', 'az', 'bm', 'ba', 'eu', 'be', 'bn', 'bh', 'bi', 'nb', 'bs', 'br', 'bg', 'my', 'ca', 'ch', 'ce', 'ny', 'zh', 'cv', 'kw', 'co', 'cr', 'hr', 'cs', 'da', 'dv', 'nl', 'dz', 'en', 'eo', 'et', 'ee', 'fo', 'fj', 'fi', 'fr', 'ff', 'gd', 'gl', 'lg', 'ka', 'de', 'el', 'gn', 'gu', 'ht', 'ha', 'he', 'hz', 'hi', 'ho', 'hu', 'is', 'io', 'ig', 'id', 'ia', 'ie', 'iu', 'ik', 'ga', 'it', 'ja', 'jv', 'kl', 'kn', 'kr', 'ks', 'kk', 'km', 'ki', 'rw', 'rn', 'kv', 'kg', 'ko', 'ku', 'kj', 'ky', 'lo', 'la', 'lv', 'li', 'ln', 'lt', 'lu', 'lb', 'mk', 'mg', 'ms', 'ml', 'mt', 'gv', 'mi', 'mr', 'mh', 'mn', 'na', 'nv', 'ng', 'ne', 'nd', 'se', 'no', 'ii', 'nn', 'oc', 'oj', 'or', 'om', 'os', 'pi', 'ps', 'fa', 'pl', 'pt', 'pa', 'qu', 'ro', 'rm', 'ru', 'sm', 'sg', 'sa', 'sc', 'sr', 'sn', 'sd', 'si', 'cu', 'sk', 'sl', 'so', 'nr', 'st', 'es', 'su', 'sw', 'ss', 'sv', 'tl', 'ty', 'tg', 'ta', 'tt', 'te', 'th', 'bo', 'ti', 'to', 'ts', 'tn', 'tr', 'tk', 'tw', 'uk', 'ur', 'ug', 'uz', 've', 'vi', 'vo', 'wa', 'cy', 'fy', 'wo', 'xh', 'yi', 'yo', 'za', 'zu']

	##############################################################################
	# LOG
	##############################################################################

	@classmethod
	def log(self, message, message2 = None, message3 = None, message4 = None, message5 = None, name = True, parameters = None, level = LogDefault):
		divider = ' '
		message = str(message)
		if message2: message += divider + str(message2)
		if message3: message += divider + str(message3)
		if message4: message += divider + str(message4)
		if message5: message += divider + str(message5)
		if name:
			nameValue = self.addonName().upper()
			if not name == True:
				nameValue += ' ' + name
			nameValue += ' ' + self.addonVersion()
			if parameters:
				nameValue += ' ['
				if self.isString(parameters):
					nameValue += parameters
				else:
					nameValue += ', '.join([str(parameter) for parameter in parameters])
				nameValue += ']'
			nameValue += ': '
			message = nameValue + message
		xbmc.log(message, level)

	@classmethod
	def error(self, message = None, exception = True):
		if exception:
			type, value, traceback = sys.exc_info()
			filename = traceback.tb_frame.f_code.co_filename
			linenumber = traceback.tb_lineno
			name = traceback.tb_frame.f_code.co_name
			errortype = type.__name__
			errormessage = value.message
			if message:
				message += ' -> '
			else:
				message = ''
			message += str(errortype) + ' -> ' + str(errormessage)
			parameters = [filename, linenumber, name]
		else:
			parameters = None
		self.log(message, name = 'ERROR', parameters = parameters, level = OrionTools.LogError)

	@classmethod
	def errorCustom(self, message):
		self.log(message, name = 'ERROR', level = OrionTools.LogError)

	##############################################################################
	# TRANSLATE
	##############################################################################

	@classmethod
	def translate(self, id, utf8 = True, system = False):
		if isinstance(id, (int, long)):
			# Needs ID when called from RunScript(vpn.py)
			if system: result = xbmc.getLocalizedString(id)
			else: result = self.addon().getLocalizedString(id)
		else:
			try: result = str(id)
			except: result = id
		if utf8:
			try:
				if not '•' in result: result = self.unicode(string = result).encode('utf-8')
			except:
				result = self.unicode(string = result).encode('utf-8')
		return result

	##############################################################################
	# UNICODE
	##############################################################################

	@classmethod
	def unicode(self, string):
		try:
			if string == None: return string
			return unidecode(string.decode('utf-8'))
		except:
			try: return string.encode('ascii', 'ignore')
			except: return string

	##############################################################################
	# RANDOM
	##############################################################################

	@classmethod
	def randomInteger(self, minimum = 1, maximum = 100):
		return random.randint(minimum, maximum)

	##############################################################################
	# PATH
	##############################################################################

	@classmethod
	def pathJoin(self, path, *paths):
		return os.path.join(path, *paths)

	@classmethod
	def pathAbsolute(self, path):
		return os.path.abspath(path)

	@classmethod
	def pathResolve(self, path):
		return xbmc.translatePath(path)

	@classmethod
	def pathHome(self): # OS user home directory
		try: return os.path.expanduser('~')
		except: return None

	##############################################################################
	# FILE
	##############################################################################

	@classmethod
	def fileExists(self, path):
		if self.linkIs(path): return os.path.exists(path)
		else: return xbmcvfs.exists(path)

	@classmethod
	def fileDelete(self, path):
		try:
			try:
				if self.fileExists(path): xbmcvfs.delete(path)
			except: pass
			try:
				if self.fileExists(path):
					if force: os.chmod(path, stat.S_IWRITE)
					return os.remove(path)
			except: pass
			return not self.fileExists(path)
		except:
			return False

	@classmethod
	def fileMove(self, pathFrom, pathTo, overwrite = True):
		if pathFrom == pathTo: return False
		if overwrite:
			try: os.remove(pathTo)
			except: pass
		try:
			shutil.move(pathFrom, pathTo)
			return True
		except: return False

	@classmethod
	def fileCopy(self, pathFrom, pathTo, bytes = None, overwrite = False):
		if not xbmcvfs.exists(pathFrom):
			return False
		if overwrite and xbmcvfs.exists(pathTo):
			try: xbmcvfs.delete(pathTo)
			except: pass
		if bytes == None:
			xbmcvfs.copy(pathFrom, pathTo)
			return xbmcvfs.exists(pathTo)
		else:
			try:
				fileFrom = xbmcvfs.File(pathFrom)
				fileTo = xbmcvfs.File(pathTo, 'w')
				chunk = min(bytes, 1048576) # 1 MB
				while bytes > 0:
					size = min(bytes, chunk)
					fileTo.write(fileFrom.read(size))
					bytes -= size
				fileFrom.close()
				fileTo.close()
				return True
			except:
				return False

	@classmethod
	def fileRead(self, path):
		file = xbmcvfs.File(path)
		result = file.read()
		file.close()
		return result.decode('utf-8')

	@classmethod
	def fileWrite(self, path, data):
		file = xbmcvfs.File(path, 'w')
		result = file.write(str(data.encode('utf-8')))
		file.close()
		return result

	@classmethod
	def fileInsert(self, path, after, data):
		content = self.fileRead(path)
		try: index = re.search(after, content).end()
		except: index = -1
		if index < 0: return False
		split1 = content[:index]
		split2 = content[index:]
	 	content = split1 + data + split2
		self.fileWrite(path, content)
		return True

	@classmethod
	def fileClean(self, path, expression, replace = ''):
		content = self.fileRead(path)
		content = re.sub(expression, replace, content, flags = re.S|re.M)
		self.fileWrite(path, content)
		return True

	@classmethod
	def fileContains(self, path, expression):
		content = self.fileRead(path)
		return bool(re.search(expression, content))

	##############################################################################
	# DIRECTORY
	##############################################################################

	@classmethod
	def directoryExists(self, path):
		if not path.endswith('/') and not path.endswith('\\'): path += '/'
		return xbmcvfs.exists(path)

	@classmethod
	def directoryList(self, path, absolute = False):
		directories, files = xbmcvfs.listdir(path)
		if absolute:
			for i in range(len(files)):
				files[i] = self.pathJoin(path, files[i])
			for i in range(len(directories)):
				directories[i] = self.pathJoin(path, directories[i])
		return directories, files

	@classmethod
	def directoryCreate(self, path):
		return xbmcvfs.mkdirs(path)

	@classmethod
	def directoryName(self, path):
		return os.path.dirname(self.pathAbsolute(path))

	@classmethod
	def directoryDelete(self, path, force = True):
		try:
			try:
				if self.directoryExists(path):
					xbmcvfs.rmdir(path)
					if not self.directoryExists(path): return True
			except: pass
			try:
				if self.directoryExists(path):
					shutil.rmtree(path)
					if not self.directoryExists(path): return True
			except: pass
			try:
				if self.directoryExists(path):
					if force: os.chmod(path, stat.S_IWRITE)
					os.rmdir(path)
					if not self.directoryExists(path): return True
			except: pass
			try:
				if self.directoryExists(path):
					directories, files = self.listDirectory(path)
					for i in files: self.delete(os.path.join(path, i), force = force)
					for i in directories: self.deleteDirectory(os.path.join(path, i), force = force)
					try: xbmcvfs.rmdir(path)
					except: pass
					try: shutil.rmtree(path)
					except: pass
					try: os.rmdir(path)
					except: pass
			except: pass
			return not self.directoryExists(path)
		except: return False

	##############################################################################
	# ADDON
	##############################################################################

	@classmethod
	def addon(self, id = None):
		if id == None: id = OrionTools.Id
		return xbmcaddon.Addon(id)

	@classmethod
	def addonEnabled(self, id = None):
		try:
			xbmcaddon.Addon(id).getAddonInfo('id')
			return True
		except:
			return False

	@classmethod
	def addonId(self, id = None):
		return self.addon(id = id).getAddonInfo('id')

	@classmethod
	def addonName(self, id = None):
		return self.addon(id = id).getAddonInfo('name')

	@classmethod
	def addonAuthor(self, id = None):
		return self.addon(id = id).getAddonInfo('author')

	@classmethod
	def addonVersion(self, id = None):
		return self.addon(id = id).getAddonInfo('version')

	@classmethod
	def addonProfile(self, id = None):
		return self.pathResolve(self.addon(id = id).getAddonInfo('profile').decode('utf-8'))

	@classmethod
	def addonDescription(self, id = None):
		return self.addon(id = id).getAddonInfo('description')

	@classmethod
	def addonDisclaimer(self, id = None):
		return self.addon(id = id).getAddonInfo('disclaimer')

	@classmethod
	def addonPath(self, id = None):
		try: addon = self.addon(id = id)
		except: addon = None
		if addon == None: return ''
		else: return self.pathResolve(addon.getAddonInfo('path').decode('utf-8'))

	@classmethod
	def addonHandle(self):
		try: return int(sys.argv[1])
		except: return 0

	@classmethod
	def addonParameters(self):
		try: return dict(urlparse.parse_qsl(sys.argv[2].replace('?','')))
		except: return {}

	@classmethod
	def addonLaunch(self, id = None):
		return self.execute('RunAddon(%s)' % self.addonId(id))

	##############################################################################
	# KODI
	##############################################################################

	@classmethod
	def kodiInfo(self, value):
		return xbmc.getInfoLabel(value)

	@classmethod
	def kodiVersion(self, full = False):
		version = self.kodiInfo('System.BuildVersion')
		if not full:
			try: version = float(re.search('^\d+\.?\d+', version).group(0))
			except: pass
		return version

	@classmethod
	def kodiVersionNew(self):
		try: return self.kodiVersion() >= 18
		except: return False

	##############################################################################
	# EXECUTE
	##############################################################################

	@classmethod
	def execute(self, command):
		return xbmc.executebuiltin(command)

	@classmethod
	def executeScript(self, script, parameters = None):
		command = 'RunScript(' + script
		if parameters == None:
			for parameter in parameters:
				command += ',' + str(parameter)
		command += ')'
		return self.execute(command)

	@classmethod
	def executePlugin(self, action = None, parameters = None, duplicates = False, run = True, execute = False, addon = None):
		if parameters == None: parameters = {}
		if not action == None: parameters['action'] = action
		parameters = urllib.urlencode(parameters, doseq = duplicates)
		if addon == None: addon = self.addonId()
		command = '%s%s?%s' % (OrionTools.PrefixPlugin, addon, parameters)
		if run: command = 'RunPlugin(%s)' % command
		if execute: return self.execute(command)
		else: return command

	##############################################################################
	# TO
	##############################################################################

	@classmethod
	def toBoolean(self, value, string = False):
		if string:
			return 'true' if value else 'false'
		else:
			if value == None:
				return False
			elif value == True or value == False:
				return value
			elif self.isNumber(value):
				return value > 0
			elif self.isString(value):
				value = value.lower()
				return value == 'true' or value == 'yes' or value == 't' or value == 'y' or value == '1'
			else:
				return False

	##############################################################################
	# IS
	##############################################################################

	@classmethod
	def isNumber(self, value):
		return isinstance(value, (int, long, float))

	@classmethod
	def isString(self, value):
		return isinstance(value, basestring)

	@classmethod
	def isTuple(self, value):
		return isinstance(value, tuple)

	@classmethod
	def isList(self, value):
		return isinstance(value, list)

	@classmethod
	def isDictionary(self, value):
		return isinstance(value, dict)

	@classmethod
	def isArray(self, value):
		return self.isTuple(value) or self.isList(value)

	@classmethod
	def isStructure(self, value):
		return self.isArray(value) or self.isDictionary(value)

	##############################################################################
	# HASH
	##############################################################################

	@classmethod
	def hash(self, data):
		try: data = str(data)
		except: data = data.encode('utf-8') # Required for links with non-ASCII characters.
		return hashlib.sha256(data).hexdigest().upper()

	@classmethod
	def hashFile(self, path):
		return self.hash(self.fileRead(path))

	##############################################################################
	# BASE64
	##############################################################################

	@classmethod
	def base64From(self, data, iterations = 1):
		data = str(data)
		for i in range(iterations):
			data = data.decode('base64')
		return data

	@classmethod
	def base64To(self, data, iterations = 1):
		data = str(data)
		for i in range(iterations):
			data = data.encode('base64').replace('\n', '')
		return data

	##############################################################################
	# JSON
	##############################################################################

	@classmethod
	def jsonFrom(self, data):
		try: return json.loads(data)
		except: return None

	@classmethod
	def jsonTo(self, data):
		try: return json.dumps(data)
		except: return None

	##############################################################################
	# TIME
	##############################################################################

	@classmethod
	def sleep(self, seconds):
		time.sleep(seconds)

	@classmethod
	def timestamp(self, fixed = None):
		if fixed == None:
			# Do not use time.clock(), gives incorrect result for search.py
			return int(time.time())
		else:
			return int(time.mktime(fixed.timetuple()))

	@classmethod
	def timeFormat(self, time = None, format = FormatDateTime):
		if time == None: time = self.timestamp()
		elif time == '': return time
		time = datetime.datetime.utcfromtimestamp(time)
		return time.strftime(format)

	@classmethod
	def timeDays(self, timeFrom = None, timeTo = None, format = False):
		if timeFrom == None: timeFrom = self.timestamp()
		if timeTo == None: timeTo = self.timestamp()
		days = timeTo - timeFrom
		if days == None or days <= 0: return OrionTools.translate(32030)
		else: days = self.round(days / 86400.0, 0)
		if format: days = str(days) + ' ' + self.translate(32035)
		return days

	##############################################################################
	# MATH
	##############################################################################

	@classmethod
	def round(self, value, places = 0):
		value = round(value, places)
		if places == 0: return int(value)
		else: return value

	@classmethod
	def thousands(self, value):
		return "{:,}".format(value)

	##############################################################################
	# OBFUSCATE
	##############################################################################

	@classmethod
	def obfuscate(self, data, inverse = True, iterations = 5):
		if inverse:
			for i in range(iterations):
				data = self.base64From(data)[::-1]
		else:
			for i in range(iterations):
				data = self.base64To(data[::-1])
		return data

	##############################################################################
	# LINK
	##############################################################################

	@classmethod
	def link(self):
		from orion.modules.orionsettings import OrionSettings
		return OrionSettings.getString('internal.link', raw = True)

	@classmethod
	def linkApi(self):
		from orion.modules.orionsettings import OrionSettings
		base = None
		if OrionSettings.getBoolean('general.advanced.enabled'):
			connection = OrionSettings.getInteger('general.advanced.connection')
			if connection == 0: base = OrionSettings.getString('internal.domain', raw = True)
			elif connection == 1: base = OrionSettings.getString('internal.ip', raw = True)
			elif connection == 2: base = OrionSettings.getString('general.advanced.connection.domain')
			elif connection == 3: base = OrionSettings.getString('general.advanced.connection.ip')
		else:
			base = OrionSettings.getString('internal.domain', raw = True)
		if base == 'localhost' or base == '127.0.0.1': return 'http://%s/orion/api' % base
		else: return 'https://%s/api' % base

	@classmethod
	def linkIs(self, link, magnet = True):
		if magnet and link.startswith('magnet:'): return True
		else: return link.startswith('http:') or link.startswith('https:') or link.startswith('ftp:') or link.startswith('ftps:')

	@classmethod
	def linkOpen(self, link = None, dialog = True, front = True):
		from orion.modules.orioninterface import OrionInterface
		default = link == None
		if default: link = self.link()
		success = False
		if sys.platform == 'darwin':
			try:
				subprocess.Popen(['open', link])
				success = True
			except: pass
		if not success: webbrowser.open(link, autoraise = front, new = 2)
		if default and dialog: OrionInterface.dialogConfirm(message = self.translate(33002) + (OrionInterface.fontNewline() * 2) + OrionInterface.fontBold(link))

	##############################################################################
	# CLEAN
	##############################################################################

	@classmethod
	def cleanSettings(self):
		self.fileDelete(self.pathJoin(self.addonProfile(), 'settings.xml'))

	@classmethod
	def cleanCache(self):
		from orion.modules.orionsettings import OrionSettings
		from orion.modules.orionuser import OrionUser
		OrionSettings.set('internal.api.user', '')
		OrionSettings.set('internal.api.apps', '')
		OrionSettings.set('internal.api.cache', '')
		OrionUser.instance().update()

	##############################################################################
	# LANGUAGE
	##############################################################################

	@classmethod
	def language(self, id):
		id = id.lower()
		if len(id) == 2:
			for i in range(len(OrionTools.LanguageCodes)):
				if id == OrionTools.LanguageCodes[i]:
					return (OrionTools.LanguageCodes[i], OrionTools.LanguageNames[i])
		else:
			for i in range(len(OrionTools.LanguageCodes)):
				if id == OrionTools.LanguageNames[i].lower():
					return (OrionTools.LanguageCodes[i], OrionTools.LanguageNames[i])
		return None

	@classmethod
	def languageCode(self, id):
		return self.language(id)[0]

	@classmethod
	def languageName(self, id):
		return self.language(id)[1]

	@classmethod
	def languages(self):
		result = []
		for i in range(len(OrionTools.LanguageCodes)):
			result.append((OrionTools.LanguageCodes[i], OrionTools.LanguageNames[i]))
		return result

	@classmethod
	def languageCodes(self):
		return OrionTools.LanguageCodes

	@classmethod
	def languageNames(self):
		return OrionTools.LanguageNames
