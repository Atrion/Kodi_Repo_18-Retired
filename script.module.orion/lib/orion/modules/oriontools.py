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
import math
import shutil
import datetime
import random
import hashlib
import urllib
import traceback
import webbrowser
import subprocess
import xbmc
import xbmcaddon
import xbmcvfs

try: from urllib.parse import urlparse
except: import urlparse

try: from urllib.parse import urlencode
except: from urllib import urlencode

try: from urllib.parse import parse_qsl
except: from urlparse import parse_qsl

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
	FormatDateReadable = '%-d %B %Y'

	PrefixPlugin = 'plugin://'

	PythonVersion = None

	Base64Url = [['+', '.'], ['/', '_'], ['=', '-']]

	# Higher numbers means bigger sub-version values.
	# Eg: 1000 means valueues can be between 0 and 999.
	VersionMain = 1000
	VersionDev = 100 # Cannot divide by more than 100.

	ArchiveExtension = 'zip'

	SizeUnits = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
	SizePlaces = [0, 1, 1, 2, 2, 3]

	LanguageNames = ['Abkhaz', 'Afar', 'Afrikaans', 'Akan', 'Albanian', 'Amharic', 'Arabic', 'Aragonese', 'Armenian', 'Assamese', 'Avaric', 'Avestan', 'Aymara', 'Azerbaijani', 'Bambara', 'Bashkir', 'Basque', 'Belarusian', 'Bengali', 'Bihari', 'Bislama', 'Bokmal', 'Bosnian', 'Breton', 'Bulgarian', 'Burmese', 'Catalan', 'Chamorro', 'Chechen', 'Chichewa', 'Chinese', 'Chuvash', 'Cornish', 'Corsican', 'Cree', 'Croatian', 'Czech', 'Danish', 'Divehi', 'Dutch', 'Dzongkha', 'English', 'Esperanto', 'Estonian', 'Ewe', 'Faroese', 'Fijian', 'Finnish', 'French', 'Fula', 'Gaelic', 'Galician', 'Ganda', 'Georgian', 'German', 'Greek', 'Guarani', 'Gujarati', 'Haitian', 'Hausa', 'Hebrew', 'Herero', 'Hindi', 'Hiri Motu', 'Hungarian', 'Icelandic', 'Ido', 'Igbo', 'Indonesian', 'Interlingua', 'Interlingue', 'Inuktitut', 'Inupiaq', 'Irish', 'Italian', 'Japanese', 'Javanese', 'Kalaallisut', 'Kannada', 'Kanuri', 'Kashmiri', 'Kazakh', 'Khmer', 'Kikuyu', 'Kinyarwanda', 'Kirundi', 'Komi', 'Kongo', 'Korean', 'Kurdish', 'Kwanyama', 'Kyrgyz', 'Lao', 'Latin', 'Latvian', 'Limburgish', 'Lingala', 'Lithuanian', 'Luba-Katanga', 'Luxembourgish', 'Macedonian', 'Malagasy', 'Malay', 'Malayalam', 'Maltese', 'Manx', 'Maori', 'Marathi', 'Marshallese', 'Mongolian', 'Nauruan', 'Navajo', 'Ndonga', 'Nepali', 'Northern Ndebele', 'Northern Sami', 'Norwegian', 'Nuosu', 'Nynorsk', 'Occitan', 'Ojibwe', 'Oriya', 'Oromo', 'Ossetian', 'Pali', 'Pashto', 'Persian', 'Polish', 'Portuguese', 'Punjabi', 'Quechua', 'Romanian', 'Romansh', 'Russian', 'Samoan', 'Sango', 'Sanskrit', 'Sardinian', 'Serbian', 'Shona', 'Sindhi', 'Sinhalese', 'Slavonic', 'Slovak', 'Slovene', 'Somali', 'Southern Ndebele', 'Southern Sotho', 'Spanish', 'Sundanese', 'Swahili', 'Swati', 'Swedish', 'Tagalog', 'Tahitian', 'Tajik', 'Tamil', 'Tatar', 'Telugu', 'Thai', 'Tibetan', 'Tigrinya', 'Tonga', 'Tsonga', 'Tswana', 'Turkish', 'Turkmen', 'Twi', 'Ukrainian', 'Urdu', 'Uyghur', 'Uzbek', 'Venda', 'Vietnamese', 'Volapuk', 'Walloon', 'Welsh', 'Western Frisian', 'Wolof', 'Xhosa', 'Yiddish', 'Yoruba', 'Zhuang', 'Zulu']
	LanguageCodes = ['ab', 'aa', 'af', 'ak', 'sq', 'am', 'ar', 'an', 'hy', 'as', 'av', 'ae', 'ay', 'az', 'bm', 'ba', 'eu', 'be', 'bn', 'bh', 'bi', 'nb', 'bs', 'br', 'bg', 'my', 'ca', 'ch', 'ce', 'ny', 'zh', 'cv', 'kw', 'co', 'cr', 'hr', 'cs', 'da', 'dv', 'nl', 'dz', 'en', 'eo', 'et', 'ee', 'fo', 'fj', 'fi', 'fr', 'ff', 'gd', 'gl', 'lg', 'ka', 'de', 'el', 'gn', 'gu', 'ht', 'ha', 'he', 'hz', 'hi', 'ho', 'hu', 'is', 'io', 'ig', 'id', 'ia', 'ie', 'iu', 'ik', 'ga', 'it', 'ja', 'jv', 'kl', 'kn', 'kr', 'ks', 'kk', 'km', 'ki', 'rw', 'rn', 'kv', 'kg', 'ko', 'ku', 'kj', 'ky', 'lo', 'la', 'lv', 'li', 'ln', 'lt', 'lu', 'lb', 'mk', 'mg', 'ms', 'ml', 'mt', 'gv', 'mi', 'mr', 'mh', 'mn', 'na', 'nv', 'ng', 'ne', 'nd', 'se', 'no', 'ii', 'nn', 'oc', 'oj', 'or', 'om', 'os', 'pi', 'ps', 'fa', 'pl', 'pt', 'pa', 'qu', 'ro', 'rm', 'ru', 'sm', 'sg', 'sa', 'sc', 'sr', 'sn', 'sd', 'si', 'cu', 'sk', 'sl', 'so', 'nr', 'st', 'es', 'su', 'sw', 'ss', 'sv', 'tl', 'ty', 'tg', 'ta', 'tt', 'te', 'th', 'bo', 'ti', 'to', 'ts', 'tn', 'tr', 'tk', 'tw', 'uk', 'ur', 'ug', 'uz', 've', 'vi', 'vo', 'wa', 'cy', 'fy', 'wo', 'xh', 'yi', 'yo', 'za', 'zu']

	Countries = {'af':'Afghanistan','ax':'Aland Islands','al':'Albania','dz':'Algeria','as':'American Samoa','ad':'Andorra','ao':'Angola','ai':'Anguilla','aq':'Antarctica','ag':'Antigua And Barbuda','ar':'Argentina','am':'Armenia','aw':'Aruba','au':'Australia','at':'Austria','az':'Azerbaijan','bs':'Bahamas','bh':'Bahrain','bd':'Bangladesh','bb':'Barbados','by':'Belarus','be':'Belgium','bz':'Belize','bj':'Benin','bm':'Bermuda','bt':'Bhutan','bo':'Bolivia','ba':'Bosnia And Herzegovina','bw':'Botswana','bv':'Bouvet Island','br':'Brazil','io':'British Indian Ocean Territory','bn':'Brunei Darussalam','bg':'Bulgaria','bf':'Burkina Faso','bi':'Burundi','kh':'Cambodia','cm':'Cameroon','ca':'Canada','cv':'Cape Verde','ky':'Cayman Islands','cf':'Central African Republic','td':'Chad','cl':'Chile','cn':'China','cx':'Christmas Island','cc':'Cocos (Keeling) Islands','co':'Colombia','km':'Comoros','cg':'Congo','cd':'Congo, Democratic Republic','ck':'Cook Islands','cr':'Costa Rica','ci':'Cote D\'Ivoire','hr':'Croatia','cu':'Cuba','cy':'Cyprus','cz':'Czech Republic','dk':'Denmark','dj':'Djibouti','dm':'Dominica','do':'Dominican Republic','ec':'Ecuador','eg':'Egypt','sv':'El Salvador','gq':'Equatorial Guinea','er':'Eritrea','ee':'Estonia','et':'Ethiopia','fk':'Falkland Islands (Malvinas)','fo':'Faroe Islands','fj':'Fiji','fi':'Finland','fr':'France','gf':'French Guiana','pf':'French Polynesia','tf':'French Southern Territories','ga':'Gabon','gm':'Gambia','ge':'Georgia','de':'Germany','gh':'Ghana','gi':'Gibraltar','gr':'Greece','gl':'Greenland','gd':'Grenada','gp':'Guadeloupe','gu':'Guam','gt':'Guatemala','gg':'Guernsey','gn':'Guinea','gw':'Guinea-Bissau','gy':'Guyana','ht':'Haiti','hm':'Heard Island & Mcdonald Islands','va':'Holy See (Vatican City State)','hn':'Honduras','hk':'Hong Kong','hu':'Hungary','is':'Iceland','in':'India','id':'Indonesia','ir':'Iran, Islamic Republic Of','iq':'Iraq','ie':'Ireland','im':'Isle Of Man','il':'Israel','it':'Italy','jm':'Jamaica','jp':'Japan','je':'Jersey','jo':'Jordan','kz':'Kazakhstan','ke':'Kenya','ki':'Kiribati','kr':'Korea','kw':'Kuwait','kg':'Kyrgyzstan','la':'Lao People\'s Democratic Republic','lv':'Latvia','lb':'Lebanon','ls':'Lesotho','lr':'Liberia','ly':'Libyan Arab Jamahiriya','li':'Liechtenstein','lt':'Lithuania','lu':'Luxembourg','mo':'Macao','mk':'Macedonia','mg':'Madagascar','mw':'Malawi','my':'Malaysia','mv':'Maldives','ml':'Mali','mt':'Malta','mh':'Marshall Islands','mq':'Martinique','mr':'Mauritania','mu':'Mauritius','yt':'Mayotte','mx':'Mexico','fm':'Micronesia, Federated States Of','md':'Moldova','mc':'Monaco','mn':'Mongolia','me':'Montenegro','ms':'Montserrat','ma':'Morocco','mz':'Mozambique','mm':'Myanmar','na':'Namibia','nr':'Nauru','np':'Nepal','nl':'Netherlands','an':'Netherlands Antilles','nc':'New Caledonia','nz':'New Zealand','ni':'Nicaragua','ne':'Niger','ng':'Nigeria','nu':'Niue','nf':'Norfolk Island','mp':'Northern Mariana Islands','no':'Norway','om':'Oman','pk':'Pakistan','pw':'Palau','ps':'Palestinian Territory, Occupied','pa':'Panama','pg':'Papua New Guinea','py':'Paraguay','pe':'Peru','ph':'Philippines','pn':'Pitcairn','pl':'Poland','pt':'Portugal','pr':'Puerto Rico','qa':'Qatar','re':'Reunion','ro':'Romania','ru':'Russian Federation','rw':'Rwanda','bl':'Saint Barthelemy','sh':'Saint Helena','kn':'Saint Kitts And Nevis','lc':'Saint Lucia','mf':'Saint Martin','pm':'Saint Pierre And Miquelon','vc':'Saint Vincent And Grenadines','ws':'Samoa','sm':'San Marino','st':'Sao Tome And Principe','sa':'Saudi Arabia','sn':'Senegal','rs':'Serbia','sc':'Seychelles','sl':'Sierra Leone','sg':'Singapore','sk':'Slovakia','si':'Slovenia','sb':'Solomon Islands','so':'Somalia','za':'South Africa','gs':'South Georgia And Sandwich Isl.','es':'Spain','lk':'Sri Lanka','sd':'Sudan','sr':'Suriname','sj':'Svalbard And Jan Mayen','sz':'Swaziland','se':'Sweden','ch':'Switzerland','sy':'Syrian Arab Republic','tw':'Taiwan','tj':'Tajikistan','tz':'Tanzania','th':'Thailand','tl':'Timor-Leste','tg':'Togo','tk':'Tokelau','to':'Tonga','tt':'Trinidad And Tobago','tn':'Tunisia','tr':'Turkey','tm':'Turkmenistan','tc':'Turks And Caicos Islands','tv':'Tuvalu','ug':'Uganda','ua':'Ukraine','ae':'United Arab Emirates','gb':'United Kingdom','us':'United States','um':'United States Outlying Islands','uy':'Uruguay','uz':'Uzbekistan','vu':'Vanuatu','ve':'Venezuela','vn':'Viet Nam','vg':'Virgin Islands, British','vi':'Virgin Islands, U.S.','wf':'Wallis And Futuna','eh':'Western Sahara','ye':'Yemen','zm':'Zambia','zw':'Zimbabwe'}

	##############################################################################
	# LOG
	##############################################################################

	@classmethod
	def log(self, message, message2 = None, message3 = None, message4 = None, message5 = None, name = True, parameters = None, level = LogDefault):
		divider = ' '
		message = self.unicodeString(message)
		if message2: message += divider + self.unicodeString(message2)
		if message3: message += divider + self.unicodeString(message3)
		if message4: message += divider + self.unicodeString(message4)
		if message5: message += divider + self.unicodeString(message5)
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
					nameValue += ', '.join([self.unicodeString(parameter) for parameter in parameters])
				nameValue += ']'
			nameValue += ': '
			message = nameValue + message
		xbmc.log(message, level)

	@classmethod
	def error(self, message = None, exception = True):
		if exception:
			import traceback
			type, value, traceobject = sys.exc_info()
			filename = traceobject.tb_frame.f_code.co_filename
			linenumber = traceobject.tb_lineno
			name = traceobject.tb_frame.f_code.co_name
			errortype = type.__name__
			try: errormessage = value.message
			except: errormessage = traceback.format_exception(type, value, traceobject)
			if message:
				message += ' -> '
			else:
				message = ''
			message += self.unicodeString(errortype) + ' -> ' + self.unicodeString(errormessage)
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
		if self.isInteger(id):
			# Needs ID when called from RunScript(vpn.py)
			if system: result = xbmc.getLocalizedString(id)
			else: result = self.addon().getLocalizedString(id)
		else:
			try: result = self.unicodeString(id)
			except: result = id
		if utf8: result = self.unicodeEncode(self.unicode(string = result))
		return result

	##############################################################################
	# UNICODE
	##############################################################################

	@classmethod
	def unicodeString(self, string):
		if self.pythonOld():
			return str(string)
		else:
			try:
				if not self.isString(string): string = str(string)
			except: pass
			try: return str(string, 'utf-8')
			except: return string

	@classmethod
	def unicodeEncode(self, string):
		if self.pythonOld():
			try: return string.encode('utf-8')
			except: pass
		else:
			try: string = str(string, 'utf-8')
			except: pass
		return string

	@classmethod
	def unicodeDecode(self, string):
		if self.pythonOld():
			try: return string.decode('utf-8')
			except: pass
		return string

	@classmethod
	def unicode(self, string):
		try:
			if string == None: return string
			return unidecode(self.unicodeDecode(string))
		except:
			try:
				return self.unicodeDecode(string)
			except:
				try: return string.encode('ascii', 'ignore')
				except: return string

	##############################################################################
	# RANDOM
	##############################################################################

	@classmethod
	def randomInteger(self, minimum = 1, maximum = 100):
		return random.randint(minimum, maximum)

	@classmethod
	def randomHash(self):
		return self.hash(self.unicodeString(self.randomInteger(1, 9999999999)) + self.unicodeString(self.timestamp()))

	##############################################################################
	# QUIT
	##############################################################################

	@classmethod
	def quit(self):
		sys.exit()

	##############################################################################
	# FILE
	##############################################################################

	@classmethod
	def syntaxValid(self, code, identation = False):
		import ast
		valid = True
		try:
			ast.parse(code)
		except SyntaxError as error:
			if identation:
				errors = ['indent', 'invalid syntax'] # "invalid syntax" errors can appear if indetation is not correct in a try-catch statetment.
				error = str(error).lower()
				if any(e in error for e in errors):
					valid = False
			else:
				valid = False
		except:
			pass
		return valid

	@classmethod
	def syntaxIndentation(self, code):
		maximum = 64
		indentation = re.search('\n*([ \t]*).*', code, re.IGNORECASE).group(1)
		code = code.split('\n')
		for i in range(maximum):
			yield '\n'.join([c.replace(indentation, ' ' * i, 1) for c in code])
			yield '\n'.join([c.replace(indentation, '\t' * i, 1) for c in code])

	##############################################################################
	# PATH
	##############################################################################

	@classmethod
	def pathJoin(self, path, *paths):
		if path is None: return os.path.join(*paths)
		else: return os.path.join(path, *paths)

	@classmethod
	def pathAbsolute(self, path):
		return os.path.abspath(path)

	@classmethod
	def pathResolve(self, path):
		return self.unicodeEncode(xbmc.translatePath(path))

	@classmethod
	def pathHome(self): # OS user home directory
		try: return os.path.expanduser('~')
		except: return None

	@classmethod
	def pathKodi(self): # Kodi data directory
		try: return self.pathResolve('special://home')
		except: return None

	@classmethod
	def pathLog(self): # Kodi log file path
		try:
			path = self.pathResolve('special://logpath')
			if not path.endswith('.log'): path = self.pathJoin(path, 'kodi.log')
			return path
		except: return None

	@classmethod
	def pathAddon(self, id = None): # Kodi addon directory
		try:
			path = self.pathJoin(self.pathKodi(), 'addons')
			if id: path = self.pathJoin(path, id)
			return path
		except: return None

	@classmethod
	def pathTemporary(self, orion = True, create = False, directory = None):
		path = self.pathResolve('special://temp')
		if orion: path = self.pathJoin(path, self.addonName().lower())
		if directory: path = self.pathJoin(path, directory)
		if create: self.directoryCreate(path)
		return path

	##############################################################################
	# FILE
	##############################################################################

	@classmethod
	def fileExists(self, path):
		if self.linkIs(path): return os.path.exists(path)
		else: return bool(xbmcvfs.exists(path))

	@classmethod
	def fileName(self, path):
		return os.path.basename(path)

	@classmethod
	def fileExtension(self, path):
		return os.path.splitext(path)[1].replace('.', '')

	@classmethod
	def fileSize(self, path):
		return xbmcvfs.File(path).size()

	@classmethod
	def fileSizeFormat(self, bytes, places = None):
		i = 0
		size = len(OrionTools.SizeUnits) - 1
		while bytes >= 1024 and i < size:
			bytes /= 1024.0
			i += 1
		places = OrionTools.SizePlaces[i] if places is None else places
		return ('%.' + self.unicodeString(places) + 'f %s') % (bytes, OrionTools.SizeUnits[i])

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
	def fileRead(self, path, binary = False):
		try:
			file = xbmcvfs.File(path)
			result = file.readBytes() if binary else file.read()
			file.close()
			if binary: return bytes(result)
			else: return self.unicodeDecode(result)
		except:
			self.error()
			return None

	@classmethod
	def fileWrite(self, path, data, binary = False):
		try:
			if binary: data = bytearray(data)
			else: data = self.unicodeString(self.unicodeEncode(data))
			file = xbmcvfs.File(path, 'w')
			result = file.write(data)
			file.close()
			return result
		except:
			self.error()
			return False

	@classmethod
	def fileInsert(self, path, after, data, flags = None, validate = False, replace = False):
		content = self.fileRead(path)
		if not self.isArray(after): after = [after]
		if not self.isArray(data): data = [data]
		if flags and not self.isArray(flags): flags = [flags]
		for i in range(len(after)):
			afterValue = after[i]
			dataValue = data[i]
			try: flagsValue = flags[i]
			except: flagsValue = None
			try:
				match = re.search(afterValue, content, flagsValue if flagsValue else 0)
				index = (match.start(), match.end()) if replace else match.end()
			except: index = -1

			if replace:
				if self.isInteger(index) and index < 0: return False
				split1 = content[:index[0]]
				split2 = content[index[1]:]
			else:
				if index < 0: return False
				split1 = content[:index]
				split2 = content[index:]

			content = split1 + dataValue + split2
			if validate and not self.syntaxValid(code = content, identation = True):
				valid = False
				for dataIndentation in self.syntaxIndentation(dataValue):
					content = split1 + dataIndentation + split2
					if self.syntaxValid(code = content, identation = True):
						valid = True
						break
				if not valid: return False
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
		path = self.directoryNameClean(path)
		return bool(xbmcvfs.exists(path))

	@classmethod
	def directoryList(self, path, absolute = False, files = True, directories = True, recursive = False):
		itemsDirectories, itemFiles = xbmcvfs.listdir(path)
		if recursive:
			for directory in itemsDirectories:
				subDirectories, subFiles = self.directoryList(path = self.pathJoin(path, directory), absolute = absolute, files = True, directories = True, recursive = True)
				if subDirectories: itemsDirectories.extend(subDirectories)
				if subFiles: itemFiles.extend(subFiles)
		if absolute:
			if itemFiles:
				for i in range(len(itemFiles)):
					itemFiles[i] = self.pathJoin(path, itemFiles[i])
			if itemsDirectories:
				for i in range(len(itemsDirectories)):
					itemsDirectories[i] = self.pathJoin(path, itemsDirectories[i])
		if files and directories: return itemsDirectories, itemFiles
		elif files: return itemFiles
		elif directories: return itemsDirectories
		else: return None

	@classmethod
	def directoryCreate(self, path):
		return xbmcvfs.mkdirs(path)

	@classmethod
	def directorySeparator(self):
		return os.path.sep

	@classmethod
	def directoryName(self, path):
		return os.path.dirname(self.pathAbsolute(path))

	@classmethod
	def directoryNameClean(self, path):
		if not path.endswith('/') and not path.endswith('\\'): path += self.directorySeparator()
		return path

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
	# ARCHIVE
	##############################################################################

	@classmethod
	def archiveName(self, path):
		extension = '.' + OrionTools.ArchiveExtension
		if not path.lower().endswith(extension): path += extenssion
		return path

	@classmethod
	def archiveNameClean(self, path):
		extension = '.' + OrionTools.ArchiveExtension
		if path.lower().endswith(extension): path = path[:-len(extension)]
		return path

	@classmethod
	def archiveCheck(self, path):
		import zipfile
		try:
			if self.fileExists(path):
				file = zipfile.ZipFile(path, 'r')
				file.close()
				return True
		except: pass
		return False

	@classmethod
	def _archivePrepare(self, files, names):
		temp = self.pathJoin(self.pathTemporary(), 'archives')
		path = None
		while True:
			path = self.pathJoin(temp, self.randomHash())
			if not self.directoryExists(path): break
		self.directoryCreate(path)
		for i in range(len(files)):
			if not self.fileCopy(files[i], self.pathJoin(path, names[i])):
				self.log('Could not copy archive file: ' + self.unicodeString(file))
		return path

	@classmethod
	def _archiveClean(self, path):
		if path.startswith(self.pathTemporary()): return self.directoryDelete(path, force = True)
		else: return False

	# files: single file path, list of files paths, or directory path.
	# parent: if archiving a directory, if false includes only the folder content, if true includes the folder and its content.
	@classmethod
	def archiveCreate(self, path, files, names = None, parent = False):
		if self.isString(files):
			if self.directoryExists(files):
				directory = self.directoryNameClean(files)
				parent = self.directoryNameClean(self.directoryName(directory)) if parent else directory
				files = self.directoryList(path = directory, absolute = True, files = True, directories = False, recursive = True)
				names = [file.replace(parent , '') for file in files]
			else:
				files = [files]
				names = [self.fileName(files[0])]
		elif not names:
			names = [self.fileName(file) for file in files]

		# On some Android devices, the zipfile library creates corrupted archives.
		# First try to create an archive with shutil, also because it creates smaller files than zipfile.
		try:
			pathFiles = self._archivePrepare(files, names)
			shutil.make_archive(self.archiveNameClean(path), 'zip', pathFiles)
			self._archiveClean(pathFiles)
		except: pass

		if self.archiveCheck(path):
			return True
		else:
			self.log('Primary archive creation failed. Trying alternative approach.')
			import zipfile
			file = zipfile.ZipFile(path, 'w')
			if names:
				for i in range(len(files)):
					try: file.write(files[i], names[i])
					except: pass
			else:
				for i in range(len(files)):
					try: file.write(files[i])
					except: pass
			file.close()
			return self.archiveCheck(path)

	@classmethod
	def archiveExtract(self, path, directory):
		try:
			import zipfile
			self.directoryCreate(directory)
			file = zipfile.ZipFile(path, 'r')
			file.extractall(directory)
			count = len(file.namelist())
			file.close()
			if count == 0: return True
			directories, files = self.directoryList(directory)
			return len(directories) > 0 or len(files) > 0
		except:
			return False

	##############################################################################
	# ADDON
	##############################################################################

	@classmethod
	def addon(self, id = None):
		if id is False: # Get calling addon.
			return xbmcaddon.Addon()
		else:
			if id is None: id = OrionTools.Id
			return xbmcaddon.Addon(id)

	@classmethod
	def addonEnabled(self, id = None):
		try:
			xbmcaddon.Addon(id).getAddonInfo('id')
			return True
		except:
			return False

	@classmethod
	def addonInstalled(self, id = None):
		# https://forum.kodi.tv/showthread.php?tid=347854
		# https://github.com/xbmc/xbmc/pull/16707
		try:
			if id is None: id = self.addonId()
			if self.kodiVersion(major = True) >= 19:
				return xbmc.getCondVisibility('System.HasAddon(%s)' % id) == 1
			else:
				return self.directoryExists(self.pathAddon(id))
		except:
			return False

	@classmethod
	def addonId(self, id = None, default = None):
		try: return self.addon(id = id).getAddonInfo('id')
		except: return default

	@classmethod
	def addonName(self, id = None, default = None):
		try: return self.addon(id = id).getAddonInfo('name')
		except: return default

	@classmethod
	def addonAuthor(self, id = None, default = None):
		try: return self.addon(id = id).getAddonInfo('author')
		except: return default

	@classmethod
	def addonVersion(self, id = None, default = None):
		try: return self.addon(id = id).getAddonInfo('version')
		except: return default

	@classmethod
	def addonProfile(self, id = None, default = None):
		try: return self.pathResolve(self.unicodeDecode(self.addon(id = id).getAddonInfo('profile')))
		except: return default

	@classmethod
	def addonDescription(self, id = None, default = None):
		try: return self.addon(id = id).getAddonInfo('description')
		except: return default

	@classmethod
	def addonDisclaimer(self, id = None, default = None):
		try: return self.addon(id = id).getAddonInfo('disclaimer')
		except: return default

	@classmethod
	def addonPath(self, id = None):
		try: addon = self.addon(id = id)
		except: addon = None
		if addon == None: return ''
		else: return self.pathResolve(self.unicodeDecode(addon.getAddonInfo('path')))

	@classmethod
	def addonHandle(self):
		try: return int(sys.argv[1])
		except: return 0

	@classmethod
	def addonParameters(self):
		try: return dict(parse_qsl(sys.argv[2].replace('?','')))
		except: return {}

	@classmethod
	def addonLaunch(self, id = None):
		return self.execute('RunAddon(%s)' % self.addonId(id))

	##############################################################################
	# VERSION
	##############################################################################

	# Convert a version string to a comparable float, including alpha and betea versions.
	@classmethod
	def versionValue(self, version):
		result = 0
		try:
			matches = re.search('(\d+)\.(\d+)\.(\d+)(~alpha(\d+))?(~beta(\d+))?', version)
			try: result += float(matches.group(1)) * (OrionTools.VersionMain * OrionTools.VersionMain) # Major
			except: pass
			try: result += float(matches.group(2)) * OrionTools.VersionMain # Minor
			except: pass
			try: result += float(matches.group(3)) # Patch
			except: pass
			try: result += float(matches.group(5)) / (OrionTools.VersionDev * OrionTools.VersionDev) # Alpha
			except: pass
			try: result += float(matches.group(7)) / OrionTools.VersionDev # Beta
			except: pass
		except: pass
		return result

	##############################################################################
	# KODI
	##############################################################################

	@classmethod
	def kodiInfo(self, value):
		return xbmc.getInfoLabel(value)

	@classmethod
	def kodiPlugin(self):
		return self.kodiInfo('Container.PluginName')

	@classmethod
	def kodiRestart(self):
		# On both Linux and Windows, seems to close Kodi, but not start it up again.
		self.execute('XBMC.RestartApp()')

	@classmethod
	def kodiDebugging(self):
		result = self.executeJson(method = 'Settings.GetSettingValue', parameters = {'setting' : 'debug.showloginfo'})
		return bool(result['result']['value'])

	@classmethod
	def kodiVersion(self, full = False, major = False):
		version = self.kodiInfo('System.BuildVersion')
		if not full or major:
			try: version = float(re.search('^\d+\.?\d+', version).group(0))
			except: pass
		if major:
			import math
			try: version = int(math.floor(version))
			except: pass
		return version

	@classmethod
	def kodiVersionOld(self):
		try: return self.kodiVersion(major = True) <= 17
		except: return False

	@classmethod
	def kodiVersionNew(self):
		try: return self.kodiVersion(major = True) >= 18
		except: return False

	@classmethod
	def kodiVersion17(self):
		try: return self.kodiVersion(major = True) <= 17
		except: return False

	@classmethod
	def kodiVersion18(self):
		try: return self.kodiVersion(major = True) == 18
		except: return False

	@classmethod
	def kodiVersion19(self):
		try: return self.kodiVersion(major = True) == 19
		except: return False

	##############################################################################
	# PYTHON
	##############################################################################

	@classmethod
	def pythonVersion(self):
		if OrionTools.PythonVersion is None: OrionTools.PythonVersion = sys.version_info[0]
		return OrionTools.PythonVersion

	@classmethod
	def python2(self):
		return self.pythonVersion() == 2

	@classmethod
	def python3(self):
		return self.pythonVersion() == 3

	@classmethod
	def pythonOld(self):
		return self.python2()

	@classmethod
	def pythonNew(self):
		return self.python3()

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
				command += ',' + self.unicodeString(parameter)
		command += ')'
		return self.execute(command)

	@classmethod
	def executePlugin(self, action = None, parameters = None, duplicates = False, run = True, execute = False, addon = None):
		if parameters == None: parameters = {}
		if not action == None: parameters['action'] = action
		for key, value in self.iterator(parameters):
			if self.isStructure(value): parameters[key] = self.jsonTo(value)
		parameters = urlencode(parameters, doseq = duplicates)
		if addon == None: addon = self.addonId()
		command = '%s%s?%s' % (OrionTools.PrefixPlugin, addon, parameters)
		if run: command = 'RunPlugin(%s)' % command
		if execute: return self.execute(command)
		else: return command

	@classmethod
	def executeJson(self, query = None, method = None, parameters = None, version = '2.0', id = 1, addon = False, decode = True):
		if query == None:
			if parameters == None: parameters = {}
			if addon == True: parameters['addonid'] = self.addonId()
			elif addon: parameters['addonid'] = addon
			query = {}
			query['jsonrpc'] = version
			query['id'] = id
			query['method'] = method
			query['params'] = parameters
			query = self.jsonTo(query)
		result = xbmc.executeJSONRPC(query)
		if decode: result = self.jsonFrom(self.unicode(result))
		return result

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
	def isBoolean(self, value):
		return isinstance(value, bool)

	@classmethod
	def isNumber(self, value):
		try: return isinstance(value, (int, long, float))
		except: return isinstance(value, (int, float))

	@classmethod
	def isInteger(self, value):
		try: return isinstance(value, (int, long))
		except: return isinstance(value, (int))

	@classmethod
	def isString(self, value):
		try: return isinstance(value, basestring)
		except: return isinstance(value, (str, bytes))

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
		if self.pythonOld():
			try: data = self.unicodeString(data)
			except: data = self.unicodeEncode(data) # Required for links with non-ASCII characters.
		else:
			data = bytes(data, 'utf-8')
		return hashlib.sha256(data).hexdigest().upper()

	@classmethod
	def hashFile(self, path):
		return self.hash(self.fileRead(path))

	##############################################################################
	# BASE64
	##############################################################################

	@classmethod
	def base64From(self, data, iterations = 1, url = False):
		import base64
		data = self.unicodeString(data)
		if self.pythonNew(): data = bytes(data, 'utf-8')
		for i in range(iterations):
			if url:
				for j in OrionTools.Base64Url:
					data = data.replace(j[1], j[0])
			data = base64.b64decode(data)
		return data

	@classmethod
	def base64To(self, data, iterations = 1, url = False):
		import base64
		data = self.unicodeString(data)
		if self.pythonOld():
			for i in range(iterations):
				data = self.unicodeString(base64.b64encode(data))
				data = data.replace('\n', '')
				if url:
					for j in OrionTools.Base64Url:
						data = data.replace(j[0], j[1])
		else:
			for i in range(iterations):
				try: data = bytes(data, 'utf-8')
				except: pass # Already bytes object.
				data = self.unicodeString(base64.b64encode(data))
				data = data.replace('\n', '')
				if url:
					for j in OrionTools.Base64Url:
						data = data.replace(j[0], j[1])
		return data

	##############################################################################
	# JSON
	##############################################################################

	@classmethod
	def jsonClean(self, data):
		if self.pythonNew():
			for key, value in data.items():
				if self.isString(value):
					data[key] = self.unicodeString(value)
				elif self.isDictionary(value):
					data[key] = self.jsonClean(value)
				elif self.isList(value):
					for i in range(len(value)):
						value[i] = self.jsonClean(value[i])
					data[key] = value
		return data

	@classmethod
	def jsonFrom(self, data):
		try: return json.loads(data)
		except: return None

	@classmethod
	def jsonTo(self, data):
		try: return json.dumps(self.jsonClean(data))
		except: return None

	@classmethod
	def jsonIs(self, data):
		try:
			json.loads(data)
			return True
		except: return False

	##############################################################################
	# COMPRESS
	##############################################################################

	@classmethod
	def compress(self, data, level = 9, raw = True, base64 = True, url = False):
		import zlib
		object = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION, zlib.DEFLATED, -zlib.MAX_WBITS if raw else 0, 8, zlib.Z_DEFAULT_STRATEGY)
		data = object.compress(data)
		data += object.flush()
		if base64: data = self.base64To(data, url = url)
		return data

	@classmethod
	def decompress(self, data, raw = True, base64 = True, url = False):
		import zlib
		if base64: data = self.base64From(data, url = url)
		object = zlib.decompressobj(-zlib.MAX_WBITS if raw else 0)
		data = object.decompress(data)
		data += object.flush()
		return data

	##############################################################################
	# ITERATOR
	##############################################################################

	@classmethod
	def iterator(self, struct):
		try: return struct.iteritems()
		except: return struct.items()

	@classmethod
	def iteratorValues(self, struct):
		try: return struct.itervalues()
		except: return struct.values()

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
	def timeFormat(self, date = None, format = FormatDateTime, local = False, default = None):
		if date is None:
			if default is None: date = self.timestamp()
			else: return default
		date = datetime.datetime.utcfromtimestamp(date)
		if local:
			if time.localtime().tm_isdst: date = date - datetime.timedelta(seconds = time.altzone)
			else: date = date - datetime.timedelta(seconds = time.timezone)
		return date.strftime(format)

	@classmethod
	def timeDays(self, timeFrom = None, timeTo = None, format = False):
		if timeFrom == None: timeFrom = self.timestamp()
		if timeTo == None: timeTo = self.timestamp()
		days = timeTo - timeFrom
		if days == None or days <= 0: return OrionTools.translate(32030)
		else: days = self.round(days / 86400.0, 0)
		if format: days = self.unicodeString(days) + ' ' + (self.translate(32221) if days == 1 else self.translate(32222))
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
	def roundDown(self, value, nearest = None):
		if nearest is None: return math.floor(value)
		else: return value - (value % nearest)

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
		if magnet and self.linkIsMagnet(link): return True
		else: return link.lower().startswith(('http:', 'https:', 'ftp:', 'ftps:'))

	@classmethod
	def linkIsMagnet(self, link, magnet = True):
		return link.lower().startswith('magnet:')

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

	##############################################################################
	# COUNTRY
	##############################################################################

	@classmethod
	def country(self, id):
		try: return OrionTools.Countries[id]
		except: return None

	##############################################################################
	# BUGS
	##############################################################################

	@classmethod
	def bugs(self, path = None):
		from orion.modules.orionsettings import OrionSettings
		name = self.addonName() + ' Bug Report %s.%s' % (self.timeFormat(format = '%Y-%m-%d %H.%M.%S', local = True), OrionTools.ArchiveExtension)
		path = self.pathJoin(self.pathTemporary() if path == None else path, name)
		self.fileDelete(path)
		self._bugsLog()
		files = OrionSettings.backupFiles()
		files.append(self.pathLog())
		if self.archiveCreate(path, files): return path
		else: return None

	@classmethod
	def _bugsLog(self):
		try:
			import platform
			from orion.modules.orionuser import OrionUser
			from orion.modules.orionplatform import OrionPlatform
			from orion.modules.orionintegration import OrionIntegration

			# Takes some time to retrieve.
			requests = ['System.CpuUsage', 'System.Memory(free)', 'System.Memory(total)', 'System.FreeSpace', 'System.TotalSpace', 'System.BuildVersion', 'System.BuildDate', 'System.Uptime']
			for request in requests:
				counter = 0
				while 'busy' in self.kodiInfo(request).lower():
					counter += 1
					if counter > 100: break
					self.sleep(0.1)

			empty = ''
			line = '#' * 59
			text = [empty, line, ' ORION BUG REPORT', line, empty]

			# System
			processor = self.kodiInfo('System.CpuUsage')
			try:
				usage = re.findall(':\s*(.*?)%', processor)
				average = sum(float(i) for i in usage) / len(usage)
				processor = self.unicodeString(int(100 - average)) + '% free of ' + self.unicodeString(len(usage)) + ' cores'
			except: pass
			text.extend([
				'   SYSTEM',
				'      Operating System: ' + OrionPlatform.label(),
				'      Processor: ' + processor,
				'      Memory: ' + self._bugsSize('System.Memory(free)') + ' free of ' + self._bugsSize('System.Memory(total)'),
				'      Disk: ' + self._bugsSize('System.FreeSpace') + ' free of ' + self._bugsSize('System.TotalSpace'),
			])

			# Python
			text.extend([
				'',
				'   PYTHON',
				'      Version: ' + self.unicodeString(platform.python_version()),
				'      Implementation: ' + self.unicodeString(platform.python_implementation()),
				'      Architecture: ' + self.unicodeString(platform.architecture()[0]),
			])

			# Kodi
			text.extend([
				'',
				'   KODI',
				'      Build Version: ' + self.kodiInfo('System.BuildVersion'),
				'      Build Date: ' + self.kodiInfo('System.BuildDate'),
				'      Up Time: ' + self.kodiInfo('System.Uptime'),
			])

			# Orion
			user = OrionUser.instance()
			user.update()
			userStreams = str(self.round(100 * user.requestsStreamsDailyUsed(0, True), 0)) + '% (' + str(user.requestsStreamsDailyUsed(0)) + ' of ' + str(user.requestsStreamsDailyLimit('Unlimited')) + ')'
			userHashes = str(self.round(100 * user.requestsHashesDailyUsed(0, True), 0)) + '% (' + str(user.requestsHashesDailyUsed(0)) + ' of ' + str(user.requestsHashesDailyLimit('Unlimited')) + ')'
			userContainers = str(self.round(100 * user.requestsContainersDailyUsed(0, True), 0)) + '% (' + str(user.requestsContainersDailyUsed(0)) + ' of ' + str(user.requestsContainersDailyLimit('Unlimited')) + ')'
			text.extend([
				'',
				'   ORION',
				'      Addon Version: ' + self.addonVersion(),
				'      User ID: ' + self.unicodeString(user.id()),
				'      Subscription Package: ' + self.unicodeString(user.subscriptionPackageName('')),
				'      Subscription Started: ' + self.timeFormat(user.subscriptionTimeStarted(), format = self.FormatDateTime),
				'      Subscription Expiration: ' + self.timeFormat(user.subscriptionTimeExpiration(), format = self.FormatDateTime, default = 'None'),
				'      Stream Usage: ' + userStreams,
				'      Hash Usage: ' + userHashes,
				'      Container Usage: ' + userContainers,
			])

			# Integration
			text.extend([
				'',
				'   INTEGRATION',
			])
			addons = OrionIntegration.addons()
			for addon in addons:
				if addon['integrated'] and addon['installed']:
					text.append('      ' + self.unicodeString(addon['name']) + ': ' + self.unicodeString(addon['version']))

			text.extend([empty, line, empty])
			[self.log('#' + i, name = False) for i in text]
		except:
			self.error(message = 'Could not generate debug information')

	@classmethod
	def _bugsSize(self, type):
		size = self.kodiInfo(type)
		data = size.lower()
		if 'mb' in data:
			try: size = ('%0.1f' % (float(re.search('\d*', data).group(0)) / 1024.0)) + ' GB'
			except: pass
		elif 'gb' in data:
			try: size = ('%0.1f' % float(re.search('\d*', data).group(0))) + ' GB'
			except: pass
		elif 'tb' in data:
			try: size = ('%0.1f' % float(re.search('\d*', data).group(0))) + ' TB'
			except: pass
		return size
