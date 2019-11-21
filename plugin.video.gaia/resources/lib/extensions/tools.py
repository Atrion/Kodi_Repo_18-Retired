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

import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs
import xbmcgui

import sys
import os
import re
import threading


class Time(object):

	# Use time.clock() instead of time.time() for processing time.
	# NB: Do not use time.clock(). Gives the wrong answer in timestamp() AND runs very fast in Linux. Hence, in the stream finding dialog, for every real second, Linux progresses 5-6 seconds.
	# http://stackoverflow.com/questions/85451/python-time-clock-vs-time-time-accuracy
	# https://www.tutorialspoint.com/python/time_clock.htm

	ZoneUtc = 'utc'
	ZoneLocal = 'local'

	FormatTimestamp = None
	FormatDateTime = '%Y-%m-%d %H:%M:%S'
	FormatDate = '%Y-%m-%d'
	FormatTime = '%H:%M:%S'
	FormatTimeShort = '%H:%M'

	def __init__(self, start = False):
		self.mStart = None
		if start: self.start()

	def start(self):
		import time
		self.mStart = time.time()
		return self.mStart

	def restart(self):
		return self.start()

	def elapsed(self, milliseconds = False):
		import time
		if self.mStart == None:
			self.mStart = time.time()
		if milliseconds: return int((time.time() - self.mStart) * 1000)
		else: return int(time.time() - self.mStart)

	def expired(self, expiration):
		return self.elapsed() >= expiration

	@classmethod
	def sleep(self, seconds):
		import time
		time.sleep(seconds)

	# UTC timestamp
	@classmethod
	def timestamp(self, fixedTime = None, format = None):
		import time
		if fixedTime == None:
			# Do not use time.clock(), gives incorrect result for search.py
			return int(time.time())
		else:
			if format: fixedTime = self.datetime(fixedTime, format)
			try: return int(time.mktime(fixedTime.timetuple()))
			except: return int(time.strftime('%s')) # Somtimes mktime fails (mktime argument out of range), which seems to be an issue with very large dates (eg 2120-02-03) on Android.

	@classmethod
	def format(self, timestamp = None, format = FormatDateTime):
		import time
		import datetime
		if timestamp == None: timestamp = self.timestamp()
		return datetime.datetime.utcfromtimestamp(timestamp).strftime(format)

	# datetime object from string
	@classmethod
	def datetime(self, string, format = FormatDateTime):
		import time
		import datetime
		try:
			return datetime.datetime.strptime(string, format)
		except:
			# Older Kodi Python versions do not have the strptime function.
			# http://forum.kodi.tv/showthread.php?tid=112916
			return datetime.datetime.fromtimestamp(time.mktime(time.strptime(string, format)))

	@classmethod
	def past(self, seconds = 0, minutes = 0, days = 0, format = FormatTimestamp):
		result = self.timestamp() - seconds - (minutes * 60) - (days * 86400)
		if not format == self.FormatTimestamp: result = self.format(timestamp = result, format = format)
		return result

	@classmethod
	def future(self, seconds = 0, minutes = 0, days = 0, format = FormatTimestamp):
		result = self.timestamp() + seconds + (minutes * 60) + (days * 86400)
		if not format == self.FormatTimestamp: result = self.format(timestamp = result, format = format)
		return result

	@classmethod
	def localZone(self):
		import time
		if time.daylight:
			offsetHour = time.altzone / 3600
		else:
			offsetHour = time.timezone / 3600
		return 'Etc/GMT%+d' % offsetHour

	@classmethod
	def convert(self, stringTime, stringDay = None, abbreviate = False, formatInput = FormatTimeShort, formatOutput = None, zoneFrom = ZoneUtc, zoneTo = ZoneLocal):
		import datetime
		from resources.lib.externals import pytz
		result = ''
		try:
			# If only time is given, the date will be set to 1900-01-01 and there are conversion problems if this goes down to 1899.
			if formatInput == '%H:%M':
				# Use current datetime (now) in order to accomodate for daylight saving time.
				stringTime = '%s %s' % (datetime.datetime.now().strftime('%Y-%m-%d'), stringTime)
				formatNew = '%Y-%m-%d %H:%M'
			else:
				formatNew = formatInput

			if zoneFrom == Time.ZoneUtc: zoneFrom = pytz.timezone('UTC')
			elif zoneFrom == Time.ZoneLocal: zoneFrom = pytz.timezone(self.localZone())
			else: zoneFrom = pytz.timezone(zoneFrom)

			if zoneTo == Time.ZoneUtc: zoneTo = pytz.timezone('UTC')
			elif zoneTo == Time.ZoneLocal: zoneTo = pytz.timezone(self.localZone())
			else: zoneTo = pytz.timezone(zoneTo)

			timeobject = self.datetime(string = stringTime, format = formatNew)

			if stringDay:
				stringDay = stringDay.lower()
				if stringDay.startswith('mon'): weekday = 0
				elif stringDay.startswith('tue'): weekday = 1
				elif stringDay.startswith('wed'): weekday = 2
				elif stringDay.startswith('thu'): weekday = 3
				elif stringDay.startswith('fri'): weekday = 4
				elif stringDay.startswith('sat'): weekday = 5
				else: weekday = 6
				weekdayCurrent = datetime.datetime.now().weekday()
				timeobject += datetime.timedelta(days = weekday) - datetime.timedelta(days = weekdayCurrent)

			timeobject = zoneFrom.localize(timeobject)
			timeobject = timeobject.astimezone(zoneTo)

			if not formatOutput: formatOutput = formatInput

			stringTime = timeobject.strftime(formatOutput)
			if stringDay:
				import calendar
				if abbreviate: stringDay = calendar.day_abbr[timeobject.weekday()]
				else: stringDay = calendar.day_name[timeobject.weekday()]
				return (stringTime, stringDay)
			else:
				return stringTime
		except:
			Logger.error()
			return stringTime

class Math(object):

	@classmethod
	def scale(self, value, fromMinimum = 0, fromMaximum = 1, toMinimum = 0, toMaximum = 1):
		return toMinimum + (value - fromMinimum) * ((toMaximum - toMinimum) / (fromMaximum - fromMinimum))

class Language(object):

	# Cases
	CaseCapital = 0
	CaseUpper = 1
	CaseLower = 2

	# Codes
	CodePrimary = 0
	CodeSecondary = 1
	CodeTertiary = 2
	CodeDefault = CodePrimary

	Automatic = 'automatic'
	Alternative = 'alternative'

	UniversalName = 'Universal'
	UniversalCode = 'un'
	UniversalCountry = 'un'

	EnglishName = 'English'
	EnglishCode = 'en'
	EnglishCountry = 'gb'

	Replacements = {'gr' : 'el'}
	Detection = None

	Languages = [
	    {'name' : UniversalName,		'code' : [UniversalCode, UniversalCode, UniversalCode],		'country' : UniversalCountry},
	    {'name' : 'Abkhazian',			'code' : ['ab', 'abk', 'abk'],		'country' : None},
	    {'name' : 'Afar',				'code' : ['aa', 'aar', 'aar'],		'country' : 'dj'},
	    {'name' : 'Afrikaans',			'code' : ['af', 'afr', 'afr'],		'country' : 'za'},
	    {'name' : 'Akan',				'code' : ['ak', 'aka', 'aka'],		'country' : None},
	    {'name' : 'Albanian',			'code' : ['sq', 'sqi', 'alb'],		'country' : 'al'},
	    {'name' : 'Amharic',			'code' : ['am', 'amh', 'amh'],		'country' : 'et'},
	    {'name' : 'Arabic',				'code' : ['ar', 'ara', 'ara'],		'country' : 'sa'},
	    {'name' : 'Aragonese',			'code' : ['an', 'arg', 'arg'],		'country' : None},
	    {'name' : 'Armenian',			'code' : ['hy', 'hye', 'arm'],		'country' : 'am'},
	    {'name' : 'Assamese',			'code' : ['as', 'asm', 'asm'],		'country' : 'in'},
	    {'name' : 'Avaric',				'code' : ['av', 'ava', 'ava'],		'country' : None},
	    {'name' : 'Avestan',			'code' : ['ae', 'ave', 'ave'],		'country' : None},
	    {'name' : 'Aymara',				'code' : ['ay', 'aym', 'aym'],		'country' : 'bo'},
	    {'name' : 'Azerbaijani',		'code' : ['az', 'aze', 'aze'],		'country' : 'az'},
	    {'name' : 'Bambara',			'code' : ['bm', 'bam', 'bam'],		'country' : None},
	    {'name' : 'Bashkir',			'code' : ['ba', 'bak', 'bak'],		'country' : 'ru'},
	    {'name' : 'Basque',				'code' : ['eu', 'eus', 'baq'],		'country' : 'es'},
	    {'name' : 'Belarusian',			'code' : ['be', 'bel', 'bel'],		'country' : 'by'},
	    {'name' : 'Bengali',			'code' : ['bn', 'ben', 'ben'],		'country' : 'bd'},
	    {'name' : 'Bihari',				'code' : ['bh', 'bih', 'bih'],		'country' : None},
	    {'name' : 'Bislama',			'code' : ['bi', 'bis', 'bis'],		'country' : 'vu'},
	    {'name' : 'Bosnian',			'code' : ['bs', 'bos', 'bos'],		'country' : 'ba'},
	    {'name' : 'Breton',				'code' : ['br', 'bre', 'bre'],		'country' : 'fr'},
	    {'name' : 'Bulgarian',			'code' : ['bg', 'bul', 'bul'],		'country' : 'bg'},
	    {'name' : 'Burmese',			'code' : ['my', 'mya', 'bur'],		'country' : 'mm'},
	    {'name' : 'Catalan',			'code' : ['ca', 'cat', 'cat'],		'country' : 'es'},
	    {'name' : 'Chamorro',			'code' : ['ch', 'cha', 'cha'],		'country' : 'gu'},
	    {'name' : 'Chechen',			'code' : ['ce', 'che', 'che'],		'country' : 'ru'},
	    {'name' : 'Chichewa',			'code' : ['ny', 'nya', 'nya'],		'country' : 'mw'},
	    {'name' : 'Chinese',			'code' : ['zh', 'zho', 'chi'],		'country' : 'cn'},
	    {'name' : 'Chuvash',			'code' : ['cv', 'chv', 'chv'],		'country' : None},
	    {'name' : 'Cornish',			'code' : ['kw', 'cor', 'cor'],		'country' : 'gb'},
	    {'name' : 'Corsican',			'code' : ['co', 'cos', 'cos'],		'country' : 'fr'},
	    {'name' : 'Cree',				'code' : ['cr', 'cre', 'cre'],		'country' : None},
	    {'name' : 'Croatian',			'code' : ['hr', 'hrv', 'hrv'],		'country' : 'hr'},
	    {'name' : 'Czech',				'code' : ['cs', 'ces', 'cze'],		'country' : 'cz'},
	    {'name' : 'Danish',				'code' : ['da', 'dan', 'dan'],		'country' : 'dk'},
	    {'name' : 'Divehi',				'code' : ['dv', 'div', 'div'],		'country' : 'mv'},
	    {'name' : 'Dutch',				'code' : ['nl', 'nld', 'dut'],		'country' : 'nl'},
	    {'name' : 'Dzongkha',			'code' : ['dz', 'dzo', 'dzo'],		'country' : None},
	    {'name' : 'English',			'code' : ['en', 'eng', 'eng'],		'country' : 'gb'},
	    {'name' : 'Esperanto',			'code' : ['eo', 'epo', 'epo'],		'country' : None},
	    {'name' : 'Estonian',			'code' : ['et', 'est', 'est'],		'country' : 'ee'},
	    {'name' : 'Ewe',				'code' : ['ee', 'ewe', 'ewe'],		'country' : None},
	    {'name' : 'Faroese',			'code' : ['fo', 'fao', 'fao'],		'country' : 'fo'},
	    {'name' : 'Fijian',				'code' : ['fj', 'fij', 'fij'],		'country' : 'fj'},
	    {'name' : 'Finnish',			'code' : ['fi', 'fin', 'fin'],		'country' : 'fi'},
	    {'name' : 'French',				'code' : ['fr', 'fra', 'fre'],		'country' : 'fr'},
	    {'name' : 'Fulah',				'code' : ['ff', 'ful', 'ful'],		'country' : 'bf'},
	    {'name' : 'Galician',			'code' : ['gl', 'glg', 'glg'],		'country' : 'es'},
	    {'name' : 'Georgian',			'code' : ['ka', 'kat', 'geo'],		'country' : 'ge'},
	    {'name' : 'German',				'code' : ['de', 'deu', 'ger'],		'country' : 'de'},
	    {'name' : 'Greek',				'code' : ['el', 'ell', 'gre'],		'country' : 'gr'},
	    {'name' : 'Guarani',			'code' : ['gn', 'grn', 'grn'],		'country' : 'py'},
	    {'name' : 'Gujarati',			'code' : ['gu', 'guj', 'guj'],		'country' : 'in'},
	    {'name' : 'Haitian',			'code' : ['ht', 'hat', 'hat'],		'country' : 'ht'},
	    {'name' : 'Hausa',				'code' : ['ha', 'hau', 'hau'],		'country' : 'ng'},
	    {'name' : 'Hebrew',				'code' : ['he', 'heb', 'heb'],		'country' : 'il'},
	    {'name' : 'Herero',				'code' : ['hz', 'her', 'her'],		'country' : None},
	    {'name' : 'Hindi',				'code' : ['hi', 'hin', 'hin'],		'country' : 'in'},
	    {'name' : 'Hiri Motu',			'code' : ['ho', 'hmo', 'hmo'],		'country' : 'pg'},
	    {'name' : 'Hungarian',			'code' : ['hu', 'hun', 'hun'],		'country' : 'hu'},
	    {'name' : 'Interlingua',		'code' : ['ia', 'ina', 'ina'],		'country' : None},
	    {'name' : 'Indonesian',			'code' : ['id', 'ind', 'ind'],		'country' : 'id'},
	    {'name' : 'Interlingue',		'code' : ['ie', 'ile', 'ile'],		'country' : None},
	    {'name' : 'Irish',				'code' : ['ga', 'gle', 'gle'],		'country' : 'ie'},
	    {'name' : 'Igbo',				'code' : ['ig', 'ibo', 'ibo'],		'country' : 'ng'},
	    {'name' : 'Inupiaq',			'code' : ['ik', 'ipk', 'ipk'],		'country' : None},
	    {'name' : 'Ido',				'code' : ['io', 'ido', 'ido'],		'country' : None},
	    {'name' : 'Icelandic',			'code' : ['is', 'isl', 'ice'],		'country' : 'is'},
	    {'name' : 'Italian',			'code' : ['it', 'ita', 'ita'],		'country' : 'it'},
	    {'name' : 'Inuktitut',			'code' : ['iu', 'iku', 'iku'],		'country' : None},
	    {'name' : 'Japanese',			'code' : ['ja', 'jpn', 'jpn'],		'country' : 'jp'},
	    {'name' : 'Javanese',			'code' : ['jv', 'jav', 'jav'],		'country' : None},
	    {'name' : 'Kalaallisut',		'code' : ['kl', 'kal', 'kal'],		'country' : 'gl'},
	    {'name' : 'Kannada',			'code' : ['kn', 'kan', 'kan'],		'country' : 'in'},
	    {'name' : 'Kanuri',				'code' : ['kr', 'kau', 'kau'],		'country' : None},
	    {'name' : 'Kashmiri',			'code' : ['ks', 'kas', 'kas'],		'country' : None},
	    {'name' : 'Kazakh',				'code' : ['kk', 'kaz', 'kaz'],		'country' : 'kz'},
	    {'name' : 'Central Khmer',		'code' : ['km', 'khm', 'khm'],		'country' : 'kh'},
	    {'name' : 'Kikuyu',				'code' : ['ki', 'kik', 'kik'],		'country' : None},
	    {'name' : 'Kinyarwanda',		'code' : ['rw', 'kin', 'kin'],		'country' : 'rw'},
	    {'name' : 'Kirghiz',			'code' : ['ky', 'kir', 'kir'],		'country' : 'kg'},
	    {'name' : 'Komi',				'code' : ['kv', 'kom', 'kom'],		'country' : None},
	    {'name' : 'Kongo',				'code' : ['kg', 'kon', 'kon'],		'country' : 'cd'},
	    {'name' : 'Korean',				'code' : ['ko', 'kor', 'kor'],		'country' : 'kr'},
	    {'name' : 'Kurdish',			'code' : ['ku', 'kur', 'kur'],		'country' : 'iq'},
	    {'name' : 'Kuanyama',			'code' : ['kj', 'kua', 'kua'],		'country' : None},
	    {'name' : 'Latin',				'code' : ['la', 'lat', 'lat'],		'country' : None},
	    {'name' : 'Luxembourgish',		'code' : ['lb', 'ltz', 'ltz'],		'country' : 'lu'},
	    {'name' : 'Ganda',				'code' : ['lg', 'lug', 'lug'],		'country' : None},
	    {'name' : 'Limburgan',			'code' : ['li', 'lim', 'lim'],		'country' : None},
	    {'name' : 'Lingala',			'code' : ['ln', 'lin', 'lin'],		'country' : None},
	    {'name' : 'Lao',				'code' : ['lo', 'lao', 'lao'],		'country' : 'la'},
	    {'name' : 'Lithuanian',			'code' : ['lt', 'lit', 'lit'],		'country' : 'lt'},
	    {'name' : 'Luba-Katanga',		'code' : ['lu', 'lub', 'lub'],		'country' : None},
	    {'name' : 'Latvian',			'code' : ['lv', 'lav', 'lav'],		'country' : 'lv'},
	    {'name' : 'Manx',				'code' : ['gv', 'glv', 'glv'],		'country' : None},
	    {'name' : 'Macedonian',			'code' : ['mk', 'mkd', 'mac'],		'country' : 'mk'},
	    {'name' : 'Malagasy',			'code' : ['mg', 'mlg', 'mlg'],		'country' : 'mg'},
	    {'name' : 'Malay',				'code' : ['ms', 'msa', 'may'],		'country' : 'my'},
	    {'name' : 'Malayalam',			'code' : ['ml', 'mal', 'mal'],		'country' : None},
	    {'name' : 'Maltese',			'code' : ['mt', 'mlt', 'mlt'],		'country' : 'mt'},
	    {'name' : 'Maori',				'code' : ['mi', 'mri', 'mao'],		'country' : 'nz'},
	    {'name' : 'Marathi',			'code' : ['mr', 'mar', 'mar'],		'country' : None},
	    {'name' : 'Marshallese',		'code' : ['mh', 'mah', 'mah'],		'country' : 'mh'},
	    {'name' : 'Mongolian',			'code' : ['mn', 'mon', 'mon'],		'country' : 'mn'},
	    {'name' : 'Nauru',				'code' : ['na', 'nau', 'nau'],		'country' : 'nr'},
	    {'name' : 'Navajo',				'code' : ['nv', 'nav', 'nav'],		'country' : None},
	    {'name' : 'North Ndebele',		'code' : ['nd', 'nde', 'nde'],		'country' : 'zw'},
	    {'name' : 'Nepali',				'code' : ['ne', 'nep', 'nep'],		'country' : 'np'},
	    {'name' : 'Ndonga',				'code' : ['ng', 'ndo', 'ndo'],		'country' : None},
	    {'name' : 'Norwegian Bokmal',	'code' : ['nb', 'nob', 'nob'],		'country' : 'no'},
	    {'name' : 'Norwegian Nynorsk',	'code' : ['nn', 'nno', 'nno'],		'country' : 'no'},
	    {'name' : 'Norwegian',			'code' : ['no', 'nor', 'nor'],		'country' : 'no'},
	    {'name' : 'Sichuan Yi',			'code' : ['ii', 'iii', 'iii'],		'country' : 'cn'},
	    {'name' : 'South Ndebele',		'code' : ['nr', 'nbl', 'nbl'],		'country' : 'za'},
	    {'name' : 'Occitan',			'code' : ['oc', 'oci', 'oci'],		'country' : None},
	    {'name' : 'Ojibwa',				'code' : ['oj', 'oji', 'oji'],		'country' : None},
	    {'name' : 'Old Slavonic',		'code' : ['cu', 'chu', 'chu'],		'country' : None},
	    {'name' : 'Oromo',				'code' : ['om', 'orm', 'orm'],		'country' : None},
	    {'name' : 'Oriya',				'code' : ['or', 'ori', 'ori'],		'country' : None},
	    {'name' : 'Ossetian',			'code' : ['os', 'oss', 'oss'],		'country' : None},
	    {'name' : 'Panjabi',			'code' : ['pa', 'pan', 'pan'],		'country' : None},
	    {'name' : 'Pali',				'code' : ['pi', 'pli', 'pli'],		'country' : None},
	    {'name' : 'Persian',			'code' : ['fa', 'fas', 'per'],		'country' : None},
	    {'name' : 'Polish',				'code' : ['pl', 'pol', 'pol'],		'country' : 'pl'},
	    {'name' : 'Pashto',				'code' : ['ps', 'pus', 'pus'],		'country' : None},
	    {'name' : 'Portuguese',			'code' : ['pt', 'por', 'por'],		'country' : 'pt'},
	    {'name' : 'Quechua',			'code' : ['qu', 'que', 'que'],		'country' : None},
	    {'name' : 'Romansh',			'code' : ['rm', 'roh', 'roh'],		'country' : 'ch'},
	    {'name' : 'Rundi',				'code' : ['rn', 'run', 'run'],		'country' : None},
	    {'name' : 'Romanian',			'code' : ['ro', 'ron', 'rum'],		'country' : 'ro'},
	    {'name' : 'Russian',			'code' : ['ru', 'rus', 'rus'],		'country' : 'ru'},
	    {'name' : 'Sanskrit',			'code' : ['sa', 'san', 'san'],		'country' : None},
	    {'name' : 'Sardinian',			'code' : ['sc', 'srd', 'srd'],		'country' : None},
	    {'name' : 'Sindhi',				'code' : ['sd', 'snd', 'snd'],		'country' : None},
	    {'name' : 'Northern Sami',		'code' : ['se', 'sme', 'sme'],		'country' : 'se'},
	    {'name' : 'Samoan',				'code' : ['sm', 'smo', 'smo'],		'country' : 'ws'},
	    {'name' : 'Sango',				'code' : ['sg', 'sag', 'sag'],		'country' : None},
	    {'name' : 'Serbian',			'code' : ['sr', 'srp', 'srp'],		'country' : 'rs'},
	    {'name' : 'Gaelic',				'code' : ['gd', 'gla', 'gla'],		'country' : 'gb'},
	    {'name' : 'Shona',				'code' : ['sn', 'sna', 'sna'],		'country' : 'zw'},
	    {'name' : 'Sinhala',			'code' : ['si', 'sin', 'sin'],		'country' : 'lk'},
	    {'name' : 'Slovak',				'code' : ['sk', 'slk', 'slo'],		'country' : 'sk'},
	    {'name' : 'Slovenian',			'code' : ['sl', 'slv', 'slv'],		'country' : 'si'},
	    {'name' : 'Somali',				'code' : ['so', 'som', 'som'],		'country' : 'so'},
	    {'name' : 'Southern Sotho',		'code' : ['st', 'sot', 'sot'],		'country' : 'za'},
	    {'name' : 'Spanish',			'code' : ['es', 'spa', 'spa'],		'country' : 'es'},
	    {'name' : 'Sundanese',			'code' : ['su', 'sun', 'sun'],		'country' : None},
	    {'name' : 'Swahili',			'code' : ['sw', 'swa', 'swa'],		'country' : 'tz'},
	    {'name' : 'Swati',				'code' : ['ss', 'ssw', 'ssw'],		'country' : 'sz'},
	    {'name' : 'Swedish',			'code' : ['sv', 'swe', 'swe'],		'country' : 'se'},
	    {'name' : 'Tamil',				'code' : ['ta', 'tam', 'tam'],		'country' : 'in'},
	    {'name' : 'Telugu',				'code' : ['te', 'tel', 'tel'],		'country' : None},
	    {'name' : 'Tajik',				'code' : ['tg', 'tgk', 'tgk'],		'country' : 'tj'},
	    {'name' : 'Thai',				'code' : ['th', 'tha', 'tha'],		'country' : 'th'},
	    {'name' : 'Tigrinya',			'code' : ['ti', 'tir', 'tir'],		'country' : None},
	    {'name' : 'Tibetan',			'code' : ['bo', 'bod', 'tib'],		'country' : 'cn'},
	    {'name' : 'Turkmen',			'code' : ['tk', 'tuk', 'tuk'],		'country' : 'tm'},
	    {'name' : 'Tagalog',			'code' : ['tl', 'tgl', 'tgl'],		'country' : 'ph'},
	    {'name' : 'Tswana',				'code' : ['tn', 'tsn', 'tsn'],		'country' : 'zaz'},
	    {'name' : 'Tonga',				'code' : ['to', 'ton', 'ton'],		'country' : None},
	    {'name' : 'Turkish',			'code' : ['tr', 'tur', 'tur'],		'country' : 'tr'},
	    {'name' : 'Tsonga',				'code' : ['ts', 'tso', 'tso'],		'country' : None},
	    {'name' : 'Tatar',				'code' : ['tt', 'tat', 'tat'],		'country' : None},
	    {'name' : 'Twi',				'code' : ['tw', 'twi', 'twi'],		'country' : None},
	    {'name' : 'Tahitian',			'code' : ['ty', 'tah', 'tah'],		'country' : None},
	    {'name' : 'Uighur',				'code' : ['ug', 'uig', 'uig'],		'country' : None},
	    {'name' : 'Ukrainian',			'code' : ['uk', 'ukr', 'ukr'],		'country' : 'ua'},
	    {'name' : 'Urdu',				'code' : ['ur', 'urd', 'urd'],		'country' : 'pk'},
	    {'name' : 'Uzbek',				'code' : ['uz', 'uzb', 'uzb'],		'country' : 'uz'},
	    {'name' : 'Venda',				'code' : ['ve', 'ven', 'ven'],		'country' : 'za'},
	    {'name' : 'Vietnamese',			'code' : ['vi', 'vie', 'vie'],		'country' : 'vn'},
	    {'name' : 'Volapük',			'code' : ['vo', 'vol', 'vol'],		'country' : None},
	    {'name' : 'Walloon',			'code' : ['wa', 'wln', 'wln'],		'country' : None},
	    {'name' : 'Welsh',				'code' : ['cy', 'cym', 'wel'],		'country' : 'gb'},
	    {'name' : 'Wolof',				'code' : ['wo', 'wol', 'wol'],		'country' : None},
	    {'name' : 'Western Frisian',	'code' : ['fy', 'fry', 'fry'],		'country' : None},
	    {'name' : 'Xhosa',				'code' : ['xh', 'xho', 'xho'],		'country' : 'za'},
	    {'name' : 'Yiddish',			'code' : ['yi', 'yid', 'yid'],		'country' : 'il'},
	    {'name' : 'Yoruba',				'code' : ['yo', 'yor', 'yor'],		'country' : None},
	    {'name' : 'Zhuang',				'code' : ['za', 'zha', 'zha'],		'country' : None},
	    {'name' : 'Zulu',				'code' : ['zu', 'zul', 'zul'],		'country' : 'za'},
	]

	@classmethod
	def _process(self, language):
		if type(language) is tuple: language = language[0]
		elif type(language) is dict: language = language['code'][Language.CodeDefault]
		language = language.lower().strip()
		try: language = Language.Replacements[language]
		except: pass
		return language

	@classmethod
	def customization(self):
		return Settings.getBoolean('general.language.customization')

	@classmethod
	def settings(self, single = False):
		languages = []

		language = Settings.getString('general.language.primary')
		if not language == 'None':
			language = self.language(language)
			if language:
				if single: return language
				if not language in languages: languages.append(language)

		language = Settings.getString('general.language.secondary')
		if not language == 'None':
			language = self.language(language)
			if language:
				if single: return language
				if not language in languages: languages.append(language)

		language = Settings.getString('general.language.tertiary')
		if not language == 'None':
			language = self.language(language)
			if language:
				if single: return language
				if not language in languages: languages.append(language)

		if len(languages) == 0: languages.append(self.language(Language.EnglishCode))

		if single: return languages[0]
		else: return languages

	@classmethod
	def isUniversal(self, language):
		if language == None: return False
		language = self._process(language)
		return language == Language.UniversalCode.lower() or language == Language.UniversalName.lower()

	@classmethod
	def isEnglish(self, language):
		if language == None: return False
		language = self._process(language)
		return language == Language.EnglishCode.lower() or language == Language.EnglishName.lower()

	@classmethod
	def languages(self, universal = True):
		if universal: return Language.Languages
		else: return Language.Languages[1:]

	@classmethod
	def names(self, case = CaseCapital, universal = True):
		names = [i['name'] for i in Language.Languages]
		if not universal: names = names[1:]
		if case == Language.CaseUpper: names = [i.upper() for i in names]
		elif case == Language.CaseLower: names = [i.lower() for i in names]
		return names

	@classmethod
	def codes(self, case = CaseLower, universal = True, code = CodeDefault):
		codes = [i['code'][code] for i in Language.Languages]
		if not universal: codes = codes[1:]
		if case == Language.CaseCapital: codes = [i.capitalize() for i in codes]
		elif case == Language.CaseUpper: codes = [i.upper() for i in codes]
		return codes

	@classmethod
	def detection(self):
		if Language.Detection == None:
			Language.Detection = self.names(case = Language.CaseLower, universal = False)
			Language.Detection += self.codes(case = Language.CaseLower, universal = False, code = Language.CodeSecondary)
			Language.Detection += self.codes(case = Language.CaseLower, universal = False, code = Language.CodeTertiary)
			Language.Detection = list(set(Language.Detection))
		return Language.Detection

	@classmethod
	def index(self, language):
		if language == None: return None
		language = self._process(language)

		for i in range(len(Language.Languages)):
			if language in Language.Languages[i]['code']:
				return i

		for i in range(len(Language.Languages)):
			if language == Language.Languages[i]['name'].lower():
				return i

		return None

	@classmethod
	def language(self, language):
		if language == None: return None
		language = self._process(language)

		if Language.Automatic in language:
			return self.settings(single = True)
		elif Language.Alternative in language:
			languages = self.settings()
			for i in languages:
				if not i['code'][code] == Language.EnglishCode:
					return i
			return languages[0]

		for i in Language.Languages:
			if language in i['code']:
				return i

		for i in Language.Languages:
			if language == i['name'].lower():
				return i

		return None

	@classmethod
	def name(self, language):
		if language == None: return None
		language = self._process(language)

		if Language.Automatic in language:
			return self.settings(single = True)['name']
		elif Language.Alternative in language:
			languages = self.settings()
			for i in languages:
				if not i['code'][code] == Language.EnglishCode:
					return i['name']
			return languages[0]['name']

		for i in Language.Languages:
			if language in i['code']:
				return i['name']

		for i in Language.Languages:
			if language == i['name'].lower():
				return i['name']

		return None

	@classmethod
	def code(self, language, code = CodeDefault):
		if language == None: return None
		language = self._process(language)

		if Language.Automatic in language:
			return self.settings(single = True)['code'][code]
		elif Language.Alternative in language:
			languages = self.settings()
			for i in languages:
				if not i['code'][code] == Language.EnglishCode:
					return i['code'][code]
			return languages[0]['code'][code]

		for i in Language.Languages:
			if language in i['code']:
				return i['code'][code]

		for i in Language.Languages:
			if language == i['name'].lower():
				return i['code'][code]

		return None

	@classmethod
	def ununiversalize(self, languages, english = True):
		for i in range(len(languages)):
			if self.isUniversal(languages[i]):
				del languages[i]
				if english:
					has = False
					for j in range(len(languages)):
						if self.isEnglish(languages[j]):
							has = True
							break
					if not has: languages.append(self.language(Language.EnglishCode))
				break
		return languages

	@classmethod
	def clean(self, languages):
		current = []
		result = []
		for i in languages:
			if i and not i['name'] in current:
				current.append(i['name'])
				result.append(i)
		return result

	@classmethod
	def country(self, language):
		if language == None: return None
		try: return self.language(language)['country']
		except: return Language.UniversalCountry


class Hash(object):

	@classmethod
	def random(self):
		import uuid
		return str(uuid.uuid4().hex).upper()

	@classmethod
	def sha1(self, data):
		import hashlib
		try: return hashlib.sha1(data.encode('utf-8')).hexdigest().upper()
		except: return hashlib.sha1(data).hexdigest().upper() # If data contains non-encoable characters, like YggTorrent containers.

	@classmethod
	def sha256(self, data):
		import hashlib
		try: return hashlib.sha256(data.encode('utf-8')).hexdigest().upper()
		except: return hashlib.sha256(data).hexdigest().upper() # If data contains non-encoable characters, like YggTorrent containers.

	@classmethod
	def sha512(self, data):
		import hashlib
		try: return hashlib.sha512(data.encode('utf-8')).hexdigest().upper()
		except: return hashlib.sha512(data).hexdigest().upper() # If data contains non-encoable characters, like YggTorrent containers.

	@classmethod
	def md5(self, data):
		import hashlib
		try: return hashlib.md5(data.encode('utf-8')).hexdigest().upper()
		except: return hashlib.md5(data).hexdigest().upper() # If data contains non-encoable characters, like YggTorrent containers.

	@classmethod
	def file(self, path):
		return self.fileSha256(path)

	@classmethod
	def fileSha1(self, path):
		return self.sha1(File.readNow(path))

	@classmethod
	def fileSha256(self, path):
		return self.sha256(File.readNow(path))

	@classmethod
	def fileSha512(self, path):
		return self.sha512(File.readNow(path))

	@classmethod
	def fileMd5(self, path):
		return self.md5(File.readNow(path))

	@classmethod
	def valid(self, hash, length = 40):
		return hash and len(hash) == length and bool(re.match('^[a-fA-F0-9]+', hash))

class Video(object):

	Extensions = ['mp4', 'mpg', 'mpeg', 'mp2', 'm4v', 'm2v', 'mkv', 'avi', 'flv', 'asf', '3gp', '3g2', 'wmv', 'mov', 'qt', 'webm', 'vob']

	@classmethod
	def extensions(self):
		return Video.Extensions

	@classmethod
	def extensionValid(self, extension = None, path = None):
		if extension == None: extension = os.path.splitext(path)[1][1:]
		extension = extension.replace('.', '').replace(' ', '').lower()
		return extension in Video.Extensions

class Audio(object):

	# Values must correspond to settings.
	StartupNone = 0
	Startup1 = 1
	Startup2 = 2
	Startup3 = 3
	Startup4 = 4
	Startup5 = 5

	@classmethod
	def startup(self, type = None):
		if type == None:
			type = Settings.getInteger('general.launch.sound')
		if type == 0 or type == None:
			return False
		else:
			path = os.path.join(System.pathResources(), 'resources', 'media', 'audio', 'startup', 'startup%d' % type, 'Gaia')
			return self.play(path = path, notPlaying = True)

	@classmethod
	def play(self, path, notPlaying = True):
		player = xbmc.Player()
		if not notPlaying or not player.isPlaying():
			player.play(path)
			return True
		else:
			return False

# Kodi's thumbnail cache
class Thumbnail(object):

	Directory = 'special://thumbnails'

	@classmethod
	def hash(self, path):
		try:
			path = path.lower()
			bs = bytearray(path.encode())
			crc = 0xffffffff
			for b in bs:
				crc = crc ^ (b << 24)
				for i in range(8):
					if crc & 0x80000000:
						crc = (crc << 1) ^ 0x04C11DB7
					else:
						crc = crc << 1
				crc = crc & 0xFFFFFFFF
			return '%08x' % crc
		except:
			return None

	@classmethod
	def delete(self, path):
		name = self.hash(path)
		if name == None:
			return None
		name += '.jpg'
		file = None
		directories, files = File.listDirectory(Thumbnail.Directory)
		for f in files:
			if f == name:
				file = os.path.join(Thumbnail.Directory, f)
				break
		for d in directories:
			dir = os.path.join(Thumbnail.Directory, d)
			directories2, files2 = File.listDirectory(dir)
			for f in files2:
				if f == name:
					file = os.path.join(dir, f)
					break
			if not file == None:
				break
		if not file == None:
			File.delete(file, force = True)

class Selection(object):

	# Must be integers
	TypeExclude = -1
	TypeUndefined = 0
	TypeInclude = 1

class Kids(object):

	Restriction7 = 0
	Restriction13 = 1
	Restriction16 = 2
	Restriction18 = 3

	@classmethod
	def enabled(self):
		return Settings.getBoolean('general.kids.enabled')

	@classmethod
	def restriction(self):
		return Settings.getInteger('general.kids.restriction')

	@classmethod
	def password(self, hash = True):
		password = Settings.getString('general.kids.password')
		if hash and not(password == None or password == ''): password = Hash.md5(password).lower()
		return password

	@classmethod
	def passwordEmpty(self):
		password = self.password()
		return password == None or password == ''

	@classmethod
	def verify(self, password):
		return not self.enabled() or self.passwordEmpty() or password.lower() == self.password().lower()

	@classmethod
	def locked(self):
		return Settings.getBoolean('general.kids.locked')

	@classmethod
	def lockable(self):
		return not self.passwordEmpty() and not self.locked()

	@classmethod
	def unlockable(self):
		return not self.passwordEmpty() and self.locked()

	@classmethod
	def lock(self):
		if self.locked():
			return True
		else:
			from resources.lib.extensions import interface # Circular import.
			Settings.set('general.kids.locked', True)
			System.restart() # Kodi still keeps the old menus in cache (when going BACK). Clear them by restarting the addon.
			interface.Dialog.confirm(title = 33438, message = 33445)
			return True

	@classmethod
	def unlock(self, internal = False):
		if self.locked():
			from resources.lib.extensions import interface # Circular import.
			password = self.password()
			if password and not password == '':
				match = interface.Dialog.inputPassword(title = 33440, verify = password)
				if not match:
					interface.Dialog.confirm(title = 33440, message = 33441)
					return False
			Settings.set('general.kids.locked', False)
			System.restart() # Kodi still keeps the old menus in cache (when going BACK). Clear them by restarting the addon.
			if not internal:
				interface.Dialog.confirm(title = 33438, message = 33444)
			return True
		else:
			return True

	@classmethod
	def allowed(self, certificate):
		if certificate == None or certificate == '':
			return False

		certificate = certificate.lower().replace(' ', '').replace('-', '').replace('_', '').strip()
		restriction = self.restriction()

		if (certificate  == 'g' or certificate  == 'tvy'):
			return True
		elif (certificate == 'pg' or certificate == 'tvy7') and restriction >= 1:
			return True
		elif (certificate == 'pg13' or certificate == 'tvpg') and restriction >= 2:
			return True
		elif (certificate == 'r' or certificate == 'tv14') and restriction >= 3:
			return True
		return False

class Converter(object):

	Base64 = 'base64'

	@classmethod
	def roman(self, number):
		number = number.lower().replace(' ', '')
		numerals = {'i' : 1, 'v' : 5, 'x' : 10, 'l' : 50, 'c' : 100, 'd' : 500, 'm' : 1000}
		result = 0
		for i, c in enumerate(number):
			if not c in numerals:
				return None
			elif (i + 1) == len(number) or numerals[c] > numerals[number[i + 1]]:
				result += numerals[c]
			else:
				result -= numerals[c]
		return result

	@classmethod
	def boolean(self, value, string = False, none = False):
		if none and value is None:
			return value
		elif string:
			return 'true' if value else 'false'
		else:
			import numbers
			if value == True or value == False:
				return value
			elif isinstance(value, numbers.Number):
				return value > 0
			elif isinstance(value, basestring):
				value = value.lower()
				return value == 'true' or value == 'yes' or value == 't' or value == 'y' or value == '1'
			else:
				return False

	@classmethod
	def dictionary(self, jsonData):
		try:
			import json

			if jsonData == None: return None
			jsonData = json.loads(jsonData)

			# In case the quotes in the string were escaped, causing the first json.loads to return a unicode string.
			try: jsonData = json.loads(jsonData)
			except: pass

			return jsonData
		except:
			return jsonData

	@classmethod
	def unicode(self, string, umlaut = False):
		try:
			if string == None:
				return string
			from resources.lib.externals.unidecode import unidecode
			if umlaut:
				try: string = string.replace(unichr(196), 'AE').replace(unichr(203), 'EE').replace(unichr(207), 'IE').replace(unichr(214), 'OE').replace(unichr(220), 'UE').replace(unichr(228), 'ae').replace(unichr(235), 'ee').replace(unichr(239), 'ie').replace(unichr(246), 'oe').replace(unichr(252), 'ue')
				except: pass
			return unidecode(string.decode('utf-8'))
		except:
			try: return string.encode('ascii', 'ignore')
			except: return string

	@classmethod
	def base64From(self, data, iterations = 1, url = False):
		data = str(data)
		if url:
			import base64
			for i in range(iterations):
				data = base64.urlsafe_b64decode(data)
		else:
			for i in range(iterations):
				data = data.decode(Converter.Base64)
		return data

	@classmethod
	def base64To(self, data, iterations = 1):
		data = str(data)
		for i in range(iterations):
			data = data.encode(Converter.Base64).replace('\n', '')
		return data

	@classmethod
	def jsonFrom(self, data, default = None):
		import json
		try: return json.loads(data)
		except: return default

	@classmethod
	def jsonTo(self, data, default = None):
		import json
		try: return json.dumps(data)
		except: return default

	@classmethod
	def quoteFrom(self, data, default = None):
		import urllib
		try: return urllib.unquote_plus(data).decode('utf8')
		except: return default

	@classmethod
	def quoteTo(self, data, default = None):
		import urllib
		try: return urllib.quote_plus(data)
		except: return default

	@classmethod
	def serialize(self, data):
		try:
			import pickle
			return pickle.dumps(data)
		except:
			return None

	@classmethod
	def unserialize(self, data):
		try:
			import pickle
			return pickle.loads(data)
		except:
			return None

	# Convert HTML entities to ASCII.
	@classmethod
	def htmlFrom(self, data):
		try:
			try: from HTMLParser import HTMLParser
			except: from html.parser import HTMLParser
			return str(HTMLParser().unescape(data))
		except:
			return data


class Logger(object):

	TypeNotice = xbmc.LOGNOTICE
	TypeError = xbmc.LOGERROR
	TypeSevere = xbmc.LOGSEVERE
	TypeFatal = xbmc.LOGFATAL
	TypeDefault = TypeNotice

	@classmethod
	def log(self, message, message2 = None, message3 = None, message4 = None, message5 = None, name = True, parameters = None, level = TypeDefault):
		divider = ' '
		message = str(message)
		if message2: message += divider + str(message2)
		if message3: message += divider + str(message3)
		if message4: message += divider + str(message4)
		if message5: message += divider + str(message5)
		if name:
			nameValue = System.name().upper()
			if not name == True:
				nameValue += ' ' + name
			nameValue += ' ' + System.version()
			if parameters:
				nameValue += ' ['
				if isinstance(parameters, basestring):
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
		self.log(message, name = 'ERROR', parameters = parameters, level = Logger.TypeError)

	@classmethod
	def errorCustom(self, message):
		self.log(message, name = 'ERROR', level = Logger.TypeError)

class File(object):

	PrefixSpecial = 'special://'
	PrefixSamba = 'smb://'

	DirectoryHome = PrefixSpecial + 'home'
	DirectoryTemporary = PrefixSpecial + 'temp'

	@classmethod
	def freeSpace(self, path = '/'):
		free = 0
		directory = os.path.realpath(path)
		try:
			if not free:
				import shutil
				total, used, free = shutil.disk_usage(directory)
		except: pass
		try:
			if not free:
				import psutil
				free = psutil.disk_usage(directory).free
		except: pass
		try:
			if not free:
				windows = Platform.familyType() == Platform.FamilyWindows
				if windows:
					try:
						if not free:
							import ctypes
							bytes = ctypes.c_ulonglong(0)
							ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(directory), None, None, ctypes.pointer(bytes))
							free = bytes.value
					except: pass
					try:
						if not free:
							import win32file
							sectorsPerCluster, bytesPerSector, freeClusters, totalClusters = win32file.GetDiskFreeSpace(directory)
							free = sectorsPerCluster * bytesPerSector * freeClusters
					except: pass
				else:
					try:
						if not free:
							stats = os.statvfs(dirname)
							free = stats.f_bavail * stats.f_frsize
					except: pass
					try:
						if free == 0:
							import subprocess
							stats = subprocess.Popen(['df', '-Pk', directory], stdout = subprocess.PIPE).communicate()[0]
							free = int(stats.splitlines()[1].split()[3]) * 1024
					except: pass
		except: pass
		return free

	@classmethod
	def translate(self, path):
		if path.startswith(File.PrefixSpecial):
			path = xbmc.translatePath(path)
		return path

	@classmethod
	def name(self, path):
		name = os.path.basename(os.path.splitext(path)[0])
		if name == '': name = None
		return name

	@classmethod
	def makeDirectory(self, path):
		return xbmcvfs.mkdirs(path)

	@classmethod
	def translatePath(self, path):
		return xbmc.translatePath(path)

	@classmethod
	def legalPath(self, path):
		return xbmc.makeLegalFilename(path)

	@classmethod
	def joinPath(self, path, *paths):
		parts = []
		for p in paths:
			if isinstance(p, (list, tuple)): parts.extend(p)
			else: parts.append(p)
		return os.path.join(path, *parts)

	@classmethod
	def exists(self, path): # Directory must end with slash
		# Do not use xbmcvfs.exists, since it returns true for http links.
		if path.startswith('http:') or path.startswith('https:') or path.startswith('ftp:') or path.startswith('ftps:'):
			return os.path.exists(path)
		else:
			return xbmcvfs.exists(path)

	@classmethod
	def existsDirectory(self, path):
		if not path.endswith('/') and not path.endswith('\\'):
			path += '/'
		return xbmcvfs.exists(path)

	# If samba file or directory.
	@classmethod
	def samba(self, path):
		return path.startswith(File.PrefixSamba)

	# If network (samba or any other non-local supported Kodi path) file or directory.
	# Path must point to a valid file or directory.
	@classmethod
	def network(self, path):
		return self.samba(path) or (self.exists(path) and not os.path.exists(path))

	@classmethod
	def delete(self, path, force = True):
		try:
			# For samba paths
			try:
				if self.exists(path):
					xbmcvfs.delete(path)
			except:
				pass

			# All with force
			try:
				if self.exists(path):
					if force:
						import stat
						os.chmod(path, stat.S_IWRITE) # Remove read only.
					return os.remove(path) # xbmcvfs often has problems deleting files
			except:
				pass

			return not self.exists(path)
		except:
			return False

	@classmethod
	def directory(self, path):
		return os.path.dirname(path)

	@classmethod
	def deleteDirectory(self, path, force = True):
		try:
			# For samba paths
			try:
				if self.existsDirectory(path):
					xbmcvfs.rmdir(path)
					if not self.existsDirectory(path):
						return True
			except:
				pass

			try:
				if self.existsDirectory(path):
					import shutil
					shutil.rmtree(path)
					if not self.existsDirectory(path):
						return True
			except:
				pass

			# All with force
			try:
				if self.existsDirectory(path):
					if force:
						import stat
						os.chmod(path, stat.S_IWRITE) # Remove read only.
					os.rmdir(path)
					if not self.existsDirectory(path):
						return True
			except:
				pass

			# Try individual delete
			try:
				if self.existsDirectory(path):
					directories, files = self.listDirectory(path)
					for i in files:
						self.delete(os.path.join(path, i), force = force)
					for i in directories:
						self.deleteDirectory(os.path.join(path, i), force = force)
					try: xbmcvfs.rmdir(path)
					except: pass
					try:
						import shutil
						shutil.rmtree(path)
					except: pass
					try: os.rmdir(path)
					except: pass
			except:
				pass

			return not self.existsDirectory(path)
		except:
			Logger.error()
			return False

	@classmethod
	def size(self, path):
		return xbmcvfs.File(path).size()

	@classmethod
	def create(self, path):
		return self.writeNow(path, '')

	@classmethod
	def readNow(self, path, utf = True):
		try:
			file = xbmcvfs.File(path)
			result = file.read()
			file.close()
			if utf: return result.decode('utf-8')
			else: return result
		except: return None

	@classmethod
	def writeNow(self, path, value, utf = True):
		file = xbmcvfs.File(path, 'w')
		if utf: value = value.encode('utf-8')
		result = file.write(str(value))
		file.close()
		return result

	# replaceNow(path, 'from', 'to')
	# replaceNow(path, [['from1', 'to1'], ['from2', 'to2']])
	@classmethod
	def replaceNow(self, path, valueFrom, valueTo = None):
		data = self.readNow(path)
		if not isinstance(valueFrom, list):
			valueFrom = [[valueFrom, valueTo]]
		for replacement in valueFrom:
			data = data.replace(replacement[0], replacement[1])
		self.writeNow(path, data)

	# Returns: directories, files
	@classmethod
	def listDirectory(self, path, absolute = False):
		directories, files = xbmcvfs.listdir(path)
		if absolute:
			for i in range(len(files)):
				files[i] = File.joinPath(path, files[i])
			for i in range(len(directories)):
				directories[i] = File.joinPath(path, directories[i])
		return directories, files

	@classmethod
	def copy(self, pathFrom, pathTo, bytes = None, overwrite = False, sleep = True):
		if overwrite and xbmcvfs.exists(pathTo):
			try: self.delete(path = pathTo, force = True)
			except: pass
			# This is important, especailly for Windows.
			# When deleteing a file and immediatly replacing it, the old file might still exist and the file is never replaced.
			if sleep: Time.sleep(0.1 if sleep == True else sleep)
		if bytes == None:
			return xbmcvfs.copy(pathFrom, pathTo)
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
	def copyDirectory(self, pathFrom, pathTo, overwrite = True):
		if not pathFrom.endswith('/') and not pathFrom.endswith('\\'):
			pathFrom += '/'
		if not pathTo.endswith('/') and not pathTo.endswith('\\'):
			pathTo += '/'

		# NB: Always check if directory exists before copying it on Windows.
		# If the source directory does not exist, Windows will simply copy the entire C: drive.
		if self.existsDirectory(pathFrom):
			try:
				if overwrite: File.deleteDirectory(pathTo)
				import shutil
				shutil.copytree(pathFrom, pathTo)
				return True
			except:
				return False
		else:
			return False

	@classmethod
	def renameDirectory(self, pathFrom, pathTo):
		if not pathFrom.endswith('/') and not pathFrom.endswith('\\'):
			pathFrom += '/'
		if not pathTo.endswith('/') and not pathTo.endswith('\\'):
			pathTo += '/'
		os.rename(pathFrom, pathTo)

	# Not for samba paths
	@classmethod
	def move(self, pathFrom, pathTo, replace = True, sleep = True):
		if pathFrom == pathTo:
			return False
		if replace:
			try: self.delete(path = pathTo, force = True)
			except: pass
			# This is important, especailly for Windows.
			# When deleteing a file and immediatly replacing it, the old file might still exist and the file is never replaced.
			# Especailly important for import Reaper's settings on inital use.
			if sleep: Time.sleep(0.1 if sleep == True else sleep)
		try:
			import shutil
			shutil.move(pathFrom, pathTo)
			return True
		except:
			return False

class System(object):

	Observe = 'gaiaobserve'
	Launch = 'gaialaunch'

	StartupScript = 'special://masterprofile/autoexec.py'

	PluginPrefix = 'plugin://'

	GaiaAddon = 'plugin.video.gaia'
	GaiaArtwork = 'script.gaia.artwork'
	GaiaBinaries = 'script.gaia.binaries'
	GaiaResources = 'script.gaia.resources'
	GaiaIcons = 'script.gaia.icons'
	GaiaSkins = 'script.gaia.skins'

	KodiVersionFull = None
	KodiVersion = None

	@classmethod
	def handle(self):
		return int(sys.argv[1])

	@classmethod
	def sleep(self, milliseconds):
		import time
		time.sleep(int(milliseconds / 1000.0))

	@classmethod
	def osLinux(self):
		return sys.platform == 'linux' or sys.platform == 'linux2'

	# If the developers option is enabled.
	@classmethod
	def developers(self):
		return Settings.getString('general.access.code') == Converter.base64From('b3BlbnNlc2FtZQ==')

	@classmethod
	def developersCode(self):
		return Converter.base64From('b3BlbnNlc2FtZQ==')

	@classmethod
	def obfuscate(self, data, iterations = 3, inverse = True):
		if inverse:
			for i in range(iterations):
				data = Converter.base64From(data)[::-1]
		else:
			for i in range(iterations):
				data = Converter.base64To(data[::-1])
		return data

	# Simulated restart of the addon.
	@classmethod
	def restart(self, sleep = True):
		System.execute('Container.Update(path,replace)')
		System.execute('ActivateWindow(Home)')
		System.execute('RunAddon(%s)' % System.GaiaAddon)
		if sleep: Time.sleep(2)

	@classmethod
	def exit(self):
		System.execute('Container.Update(path,replace)')
		System.execute('ActivateWindow(Home)')

	@classmethod
	def aborted(self):
		return xbmc.abortRequested

	@classmethod
	def visible(self, item):
		return xbmc.getCondVisibility(item)

	@classmethod
	def versionKodi(self, full = False):
		if full:
			if System.KodiVersionFull == None:
				System.KodiVersionFull = self.infoLabel('System.BuildVersion')
			return System.KodiVersionFull
		else:
			if System.KodiVersion == None:
				try: System.KodiVersion = float(re.search('^\d+\.?\d+', self.infoLabel('System.BuildVersion')).group(0))
				except: pass
			return System.KodiVersion

	@classmethod
	def versionKodiNew(self):
		try: return self.versionKodi() >= 18
		except: return False

	@classmethod
	def home(self):
		System.execute('ActivateWindow(Home)')

	@classmethod
	def windowPropertyGet(self, property, id = 10000):
		return xbmcgui.Window(id).getProperty(property)

	@classmethod
	def windowPropertySet(self, property, value, id = 10000):
		return xbmcgui.Window(id).setProperty(property, str(value))

	@classmethod
	def addon(self, id = GaiaAddon):
		return xbmcaddon.Addon(id)

	@classmethod
	def path(self, id = GaiaAddon):
		try: addon = xbmcaddon.Addon(id)
		except: addon = None
		if addon == None: return ''
		else: return File.translatePath(addon.getAddonInfo('path').decode('utf-8'))

	@classmethod
	def pathArtwork(self):
		return self.path(System.GaiaArtwork)

	@classmethod
	def pathBinaries(self):
		return self.path(System.GaiaBinaries)

	@classmethod
	def pathIcons(self):
		return self.path(System.GaiaIcons)

	@classmethod
	def pathResources(self):
		return self.path(System.GaiaResources)

	@classmethod
	def pathSkins(self):
		return self.path(System.GaiaSkins)

	# OS user home directory
	@classmethod
	def pathHome(self):
		try: return os.path.expanduser('~')
		except: return None

	@classmethod
	def pathProviders(self, provider = None):
		path = File.joinPath(self.profile(), 'Providers')
		if provider: path = File.joinPath(path, provider)
		return path

	@classmethod
	def info(self, value):
		return xbmcaddon.Addon(System.GaiaAddon).getAddonInfo(value)

	@classmethod
	def plugin(self, id = GaiaAddon):
		return System.PluginPrefix + str(id)

	@classmethod
	def command(self, action = None, parameters = None, id = GaiaAddon, duplicates = False, basic = False):
		import urllib

		if parameters == None: parameters = {}
		if not action == None: parameters['action'] = action

		# urllib.urlencode can take some time, especially for larger parameter sets.
		# Allow to manually encode the string, which is a lot faster, but requires all parameter values to be already urlencoded.
		if basic: parameters = '&'.join([str(key) + '=' + str(value) for key, value in parameters.iteritems()])
		else: parameters = urllib.urlencode(parameters, doseq = duplicates)

		command = '%s?%s' % (self.plugin(id = id), parameters)
		return command

	@classmethod
	def commandPlugin(self, action = None, parameters = None, id = GaiaAddon, duplicates = False, call = True, command = None, basic = False):
		if command == None: command = self.command(action = action, parameters = parameters, id = id, duplicates = duplicates, basic = basic)
		if call: command = 'RunPlugin(%s)' % command
		return command

	@classmethod
	def commandContainer(self, action = None, parameters = None, id = GaiaAddon, duplicates = False, call = True, command = None, basic = False):
		if command == None: command = self.command(action = action, parameters = parameters, id = id, duplicates = duplicates, basic = basic)
		if call: command = 'Container.Update(%s)' % command
		return command

	@classmethod
	def id(self, id = GaiaAddon):
		if id is None: return xbmcaddon.Addon().getAddonInfo('id')
		else: return xbmcaddon.Addon(id).getAddonInfo('id')

	@classmethod
	def name(self, id = GaiaAddon):
		return xbmcaddon.Addon(id).getAddonInfo('name')

	@classmethod
	def author(self, id = GaiaAddon):
		return xbmcaddon.Addon(id).getAddonInfo('author')

	@classmethod
	def version(self, id = GaiaAddon):
		return xbmcaddon.Addon(id).getAddonInfo('version')

	@classmethod
	def profile(self, id = GaiaAddon):
		return File.translatePath(xbmcaddon.Addon(id).getAddonInfo('profile').decode('utf-8'))

	@classmethod
	def description(self, id = GaiaAddon):
		return xbmcaddon.Addon(id).getAddonInfo('description')

	@classmethod
	def disclaimer(self, id = GaiaAddon):
		return xbmcaddon.Addon(id).getAddonInfo('disclaimer')

	@classmethod
	def infoLabel(self, value):
		return xbmc.getInfoLabel(value)

	# Checks if an addon is installed
	@classmethod
	def installed(self, id = GaiaAddon):
		try:
			addon = xbmcaddon.Addon(id)
			id = addon.getAddonInfo('id')
			return not id == None and not id == ''
		except:
			return False

	@classmethod
	def execute(self, command):
		return xbmc.executebuiltin(command)

	@classmethod
	def executeScript(self, script, parameters = None):
		command = 'RunScript(' + script
		if parameters:
			items = []
			if isinstance(parameters, dict):
				for key, value in parameters.iteritems():
					items.append(str(key) + '=' + str(value))
			for item in items:
				command += ',' + str(item)
		command += ')'
		return self.execute(command)

	@classmethod
	def stopScript(self, script):
		return self.execute('StopScript(%s)' % script)

	@classmethod
	def executePlugin(self, action = None, parameters = None, command = None):
		return self.execute(self.commandPlugin(action = action, parameters = parameters, command = command, call = True))

	@classmethod
	def executeContainer(self, action = None, parameters = None, command = None):
		return self.execute(self.commandContainer(action = action, parameters = parameters, command = command, call = True))

	# Either query OR all the other parameters.
	@classmethod
	def executeJson(self, query = None, method = None, parameters = None, version = '2.0', id = 1, addon = False, decode = True):
		if query == None:
			if parameters == None: parameters = {}
			if addon == True: parameters['addonid'] = self.id()
			elif addon: parameters['addonid'] = addon
			query = {}
			query['jsonrpc'] = version
			query['id'] = id
			query['method'] = method
			query['params'] = parameters
			query = Converter.jsonTo(query)
		result = xbmc.executeJSONRPC(query)
		if decode: result = Converter.jsonFrom(unicode(result, 'utf-8', errors = 'ignore'))
		return result

	# sleep for n seconds. Sometimes causes the new window not to show (only in the background). Sleeping seems to solve the problem.
	@classmethod
	def window(self, action = None, parameters = {}, command = None, sleep = None, refresh = False):
		if command == None:
			if action: parameters['action'] = action
			if not parameters == None and not parameters == '' and not parameters == {}:
				if not isinstance(parameters, basestring):
					import urllib
					parameters = urllib.urlencode(parameters)
				if not parameters.startswith('?'):
					parameters = '?' + parameters
			else:
				parameters = ''
			command = '%s%s/%s' % (System.PluginPrefix, System.GaiaAddon, parameters)
		result = System.execute('ActivateWindow(10025,%s,return)' % command) # When launched externally (eg: from shortcut widgets).
		System.execute('Container.Update(%s)' % command)
		if refresh: System.execute('Container.Refresh()')
		if sleep: Time.sleep(sleep)
		return result

	@classmethod
	def temporary(self, directory = None, file = None, gaia = True, make = True, clear = False):
		path = File.translatePath('special://temp/')
		if gaia: path = os.path.join(path, System.name().lower())
		if directory: path = os.path.join(path, directory)
		if clear: File.deleteDirectory(path, force = True)
		if make: File.makeDirectory(path)
		if file: path = os.path.join(path, file)
		return path

	@classmethod
	def temporaryRandom(self, directory = None, extension = 'dat', gaia = True, make = True, clear = False):
		if extension and not extension == '' and not extension.startswith('.'):
			extension = '.' + extension
		file = Hash.random() + extension
		path = self.temporary(directory = directory, file = file, gaia = gaia, make = make, clear = clear)
		while File.exists(path):
			file = Hash.random() + extension
			path = self.temporary(directory = directory, file = file, gaia = gaia, make = make, clear = clear)
		return path

	@classmethod
	def temporaryClear(self):
		return File.deleteDirectory(self.temporary(make = False))

	@classmethod
	def openLink(self, link, popup = True, popupForce = False, front = True):
		from resources.lib.extensions import interface # Circular import.
		interface.Loader.show() # Needs some time to load. Show busy.
		try:
			success = False
			if sys.platform == 'darwin': # OS X
				try:
					import subprocess
					subprocess.Popen(['open', link])
					success = True
				except: pass
			if not success:
				import webbrowser
				webbrowser.open(link, autoraise = front, new = 2) # new = 2 opens new tab.
		except:
			popupForce = True
		if popupForce:
			from resources.lib.extensions import clipboard
			clipboard.Clipboard.copyLink(link, popup)
		interface.Loader.hide()

	@classmethod
	def _observe(self):
		xbmc.Monitor().waitForAbort()
		os._exit(1)

	@classmethod
	def observe(self):
		# Observes when Kodi closes and exits.
		# Reduces the chances the Kodi freezes on exit (might still take a few seconds).
		value = xbmcgui.Window(10000).getProperty(System.Observe)
		first = not value or value == ''
		if first:
			xbmcgui.Window(10000).setProperty(System.Observe, str(Time.timestamp()))
			thread = threading.Thread(target = self._observe)
			thread.start()

	@classmethod
	def launchAddon(self, wait = True):
		System.execute('RunAddon(%s)' % self.id())
		if wait:
			for i in range(0, 150):
				if self.infoLabel('Container.PluginName') == self.GaiaAddon:
					try: items = int(self.infoLabel('Container.NumItems'))
					except: items = 0
					# Check NumItems, because the addon might have been launched, but the container/directory is still loading.
					# The container must be done loading, otherwise if a container update is executed right afterwards, the main menu items and the container update items might be mixed and displayed as the same list.
					if items > 0: break
				Time.sleep(0.2)

	@classmethod
	def launchInitialize(self):
		xbmcgui.Window(10000).setProperty(System.Launch, str(Time.timestamp()))

	@classmethod
	def launchUninitialize(self):
		xbmcgui.Window(10000).setProperty(System.Launch, '')

	@classmethod
	def launch(self):
		thread = threading.Thread(target = self._launch)
		thread.start()

	@classmethod
	def _launch(self):
		value = xbmcgui.Window(10000).getProperty(System.Launch)
		first = not value or value == '' # First launch
		try: idle = (Time.timestamp() - int(value)) > 10800 # If the last launch was more than 3 hours ago.
		except: idle = True
		if first or idle:
			from resources.lib import debrid
			from resources.lib.extensions import interface
			from resources.lib.extensions import settings
			from resources.lib.extensions import provider
			from resources.lib.extensions import window
			from resources.lib.extensions import library
			from resources.lib.extensions import settings
			from resources.lib.extensions import vpn
			from resources.lib.modules import control

			# Adapt settings
			settings.Adaption.adapt()

			# Version
			try:
				versionOld = Settings.getString('internal.version').replace('.', '')
				try:
					versionOld = versionOld.split('~')
					try:
						subversion = versionOld[1].replace('alpha', '').replace('beta', '')
						if not subversion: subversion = '1'
					except: subversion = '0'
					versionOld = versionOld[0] + '.' + str(subversion)
				except: pass
				versionOld = float(versionOld)
			except:
				versionOld = 0
			if not versionOld: versionOld = 0
			try:
				versionNew = self.version().replace('.', '')
				try:
					versionNew = versionNew.split('~')
					try:
						subversion = versionNew[1].replace('alpha', '').replace('beta', '')
						if not subversion: subversion = '1'
					except: subversion = '0'
					versionNew = versionNew[0] + '.' + str(subversion)
				except: pass
				versionNew = float(versionNew)
			except:
				versionNew = 0
			if not versionNew: versionNew = 0
			versionChange = not versionOld == versionNew
			try: versionChangeMajor = not str(versionOld)[0] == str(versionNew)[0]
			except: versionChangeMajor = False
			Settings.set('internal.version', self.version())

			# Splash
			interface.Splash.popup(major = versionChangeMajor, wait = versionChangeMajor or not interface.Legal.initialized())

			# gaiaremove
			# Can be removed in later versions.
			if versionOld < 500 and versionNew >= 500:
				# Because of metadata failures due to the new language system.
				from resources.lib.extensions import history
				history.History().clear(confirm = False)

				# New cache system.
				from resources.lib.extensions import cache
				cache.Cache().clear(confirm = False)

			# gaiaremove
			if versionOld < 503 and versionNew >= 503:
				# The database structure has changed, causing the cache to fail since it cannot insert anything.
				# Drop the entire table instead of deleting rows from the table, like in version 5.0.0 above.
				from resources.lib.extensions import cache
				cache.Cache()._drop(cache.Cache.Name)

			# gaiaremove
			if versionOld < 504 and versionNew >= 504:
				# Seems that some systems didn't correctly drop the database in version 5.0.3.
				# Just delete the entire file.
				from resources.lib.extensions import cache
				cache.Cache()._deleteFile()

			# gaiaremove
			if versionOld < 555 and versionNew >= 555:
				# Clear old metadata due to rating and vote changes.
				from resources.lib.modules import metacache
				metacache.clear()

			# gaiaremove
			if versionOld < 559 and versionNew >= 560:
				# New TVDB API.
				from resources.lib.extensions import cache
				cache.Cache().clear(confirm = False)

			# Backup - Import
			Backup.automaticImport()

			# Help
			Settings.helpClear()

			# Sound
			Audio.startup()

			# Legal Disclaimer
			if not interface.Legal.launchInitial(exit = False):
				self.launchUninitialize()
				System.exit()
				return False

			# Lightpack
			Lightpack().launch(execution = Lightpack.ExecutionGaia)

			# Clear Temporary
			System.temporaryClear()

			# Initial Launch
			self.launchInitial()

			# Providers
			provider.Provider.launch()

			# Local Library Update
			library.Library.service(gaia = True)

			# Initial Launch
			wizard = settings.Wizard().launchInitial()

			# Announcement
			Announcements.show(sleep = True)

			# Promotions
			Promotions.update()

			# Windows
			if versionChange: window.Window.clean()

			# VPN
			vpn.Vpn().launch(vpn.Vpn.ExecutionGaia)

			# Elementum
			Elementum.connect()

			# Quasar
			Quasar.connect()

			# Scrapers
			LamScrapers.check()
			GloScrapers.check()
			UniScrapers.check()
			NanScrapers.check()

			# Intialize Premiumize
			debrid.premiumize.Core().initialize()

			# Clear debrid files
			debrid.premiumize.Core().deleteLaunch()
			debrid.offcloud.Core().deleteLaunch()
			debrid.realdebrid.Core().deleteLaunch()

			# Copy the select theme background as fanart to the root folder.
			# Ensures that the selected theme also shows outside the addon.
			# Requires first a Gaia restart (to replace the old fanart) and then a Kodi restart (to load the new fanart, since the old one was still in memory).
			fanartTo = os.path.join(System.path(), 'fanart.jpg')
			Thumbnail.delete(fanartTo) # Delete from cache
			File.delete(fanartTo) # Delete old fanart
			fanartFrom = control.addonFanart()
			if not fanartFrom == None:
				fanartTo = os.path.join(System.path(), 'fanart.jpg')
				File.copy(fanartFrom, fanartTo, overwrite = True)

			# Backup - Export
			Backup.automaticImport() # Check again, in case the initialization corrupted the settings.
			Backup.automaticExport()

			# Statistics
			# Last, in case video pops up.
			Statistics.share(wait = False)

		self.launchInitialize()

	@classmethod
	def launchInitial(self):
		if not Settings.getBoolean('internal.launch.initialized'):
			# Check Hardware
			# Leave for now, since it is adjusted by the configurations wizard. If this is enabled again, make sure to not show it on every launch, only the first.
			'''if Hardware.slow():
				from resources.lib.extensions import interface
				if interface.Dialog.option(title = 33467, message = 33700, labelConfirm = 33011, labelDeny = 33701):
					Settings.launch()'''
			Settings.set('internal.launch.initialized', False)

	@classmethod
	def launchAutomatic(self):
		if Settings.getBoolean('general.launch.automatic'):
			self.execute('RunAddon(plugin.video.gaia)')

	@classmethod
	def _automaticIdentifier(self, identifier):
		identifier = identifier.upper()
		return ('#[%s]' % identifier, '#[/%s]' % identifier)

	# Checks if a command is in the Kodi startup script.
	@classmethod
	def automaticContains(self, identifier):
		if xbmcvfs.exists(System.StartupScript):
			identifiers = self._automaticIdentifier(identifier)
			file = xbmcvfs.File(System.StartupScript, 'r')
			data = file.read()
			file.close()
			if identifiers[0] in data and identifiers[1] in data:
				return True
		return False

	# Inserts a command into the Kodi startup script.
	@classmethod
	def automaticInsert(self, identifier, command):
		identifiers = self._automaticIdentifier(identifier)
		data = ''
		contains = False

		if xbmcvfs.exists(System.StartupScript):
			file = xbmcvfs.File(System.StartupScript, 'r')
			data = file.read()
			file.close()
			if identifiers[0] in data and identifiers[1] in data:
				contains = True

		if contains:
			return False
		else:
			id = self.id()
			module = identifier.lower() + 'xbmc'
			command = command.replace(System.PluginPrefix, '').replace(id, '')
			while command.startswith('/') or command.startswith('?'):
				command = command[1:]
			command = System.PluginPrefix + id + '/?' + command
			content = '%s\n%s\nimport xbmc as %s\nif %s.getCondVisibility("System.HasAddon(%s)") == 1: %s.executebuiltin("RunPlugin(%s)")\n%s' % (data, identifiers[0], module, module, id, module, command, identifiers[1])
			file = xbmcvfs.File(System.StartupScript, 'w')
			file.write(content)
			file.close()
			return True

	# Removes a command from the Kodi startup script.
	@classmethod
	def automaticRemove(self, identifier):
		identifiers = self._automaticIdentifier(identifier)
		data = ''
		contains = False
		indexStart = 0
		indexEnd = 0
		if xbmcvfs.exists(System.StartupScript):
			file = xbmcvfs.File(System.StartupScript, 'r')
			data = file.read()
			file.close()
			if data and not data == '':
				data += '\n'
				indexStart = data.find(identifiers[0])
				if indexStart >= 0:
					indexEnd = data.find(identifiers[1]) + len(identifiers[1])
					contains = True

		if contains:
			data = data[:indexStart] + data[indexEnd:]
			file = xbmcvfs.File(System.StartupScript, 'w')
			file.write(data)
			file.close()
			return True
		else:
			return False

	#	[
	#		['title' : 'Category 1', 'items' : [{'title' : 'Name 1', 'value' : 'Value 1', 'link' : True}, {'title' : 'Name 2', 'value' : 'Value 2'}]]
	#		['title' : 'Category 2', 'items' : [{'title' : 'Name 3', 'value' : 'Value 3', 'link' : False}, {'title' : 'Name 4', 'value' : 'Value 4'}]]
	#	]
	@classmethod
	def information(self):
		from resources.lib.extensions import convert

		items = []

		# System
		system = self.informationSystem()
		subitems = []
		subitems.append({'title' : 'Name', 'value' : system['name']})
		subitems.append({'title' : 'Version', 'value' : system['version']})
		if not system['codename'] == None: subitems.append({'title' : 'Codename', 'value' : system['codename']})
		subitems.append({'title' : 'Family', 'value' : system['family']})
		subitems.append({'title' : 'Architecture', 'value' : system['architecture']})
		subitems.append({'title' : 'Processors', 'value' : str(Hardware.processors())})
		subitems.append({'title' : 'Memory', 'value' : convert.ConverterSize(value =  Hardware.memory()).stringOptimal()})
		items.append({'title' : 'System', 'items' : subitems})

		# Python
		system = self.informationPython()
		subitems = []
		subitems.append({'title' : 'Version', 'value' : system['version']})
		subitems.append({'title' : 'Implementation', 'value' : system['implementation']})
		subitems.append({'title' : 'Architecture', 'value' : system['architecture']})
		items.append({'title' : 'Python', 'items' : subitems})

		# Kodi
		system = self.informationKodi()
		subitems = []
		subitems.append({'title' : 'Name', 'value' : system['name']})
		subitems.append({'title' : 'Version', 'value' : system['version']})
		items.append({'title' : 'Kodi', 'items' : subitems})

		# Addon
		system = self.informationAddon()
		subitems = []
		subitems.append({'title' : 'Name', 'value' : system['name']})
		subitems.append({'title' : 'Author', 'value' : system['author']})
		subitems.append({'title' : 'Version', 'value' : system['version']})
		items.append({'title' : 'Addon', 'items' : subitems})

		from resources.lib.extensions import interface
		return interface.Dialog.information(title = 33467, items = items)

	@classmethod
	def informationSystem(self):
		import platform
		system = platform.system().capitalize()
		version = platform.release().capitalize()

		distribution = platform.dist()

		try:
			name = distribution[0].replace('"', '') # "elementary"
			if name == 'elementary os': name = 'elementary'
		except:
			name = ''

		distributionHas = not distribution == None and not distribution[0] == None and not distribution[0] == ''
		distributionName = name.capitalize() if distributionHas else None
		distributionVersion = distribution[1].capitalize() if distributionHas and not distribution[1] == None and not distribution[1] == '' else None
		distributionCodename = distribution[2].capitalize() if distributionHas and not distribution[2] == None and not distribution[2] == '' else None

		# Manually check for Android
		if system == 'Linux' and distributionName == None:
			import subprocess
			id = None
			if 'ANDROID_ARGUMENT' in os.environ:
				id = True
			if id == None or id == '':
				try: id = subprocess.Popen('getprop ril.serialnumber'.split(), stdout = subprocess.PIPE).communicate()[0]
				except: pass
			if id == None or id == '':
				try: id = subprocess.Popen('getprop ro.serialno'.split(), stdout = subprocess.PIPE).communicate()[0]
				except: pass
			if id == None or id == '':
				try: id = subprocess.Popen('getprop sys.serialnumber'.split(), stdout = subprocess.PIPE).communicate()[0]
				except: pass
			if id == None or id == '':
				try: id = subprocess.Popen('getprop gsm.sn1'.split(), stdout = subprocess.PIPE).communicate()[0]
				except: pass
			if not id == None and not id == '':
				distributionName = 'Android'
				distributionHas = True

		# Structure used by Statistics.
		return {
			'family' : system,
			'name' : distributionName if distributionHas else system,
			'codename' : distributionCodename if distributionHas else None,
			'version' : distributionVersion if distributionHas else version,
			'architecture' : '64 bit' if '64' in platform.processor() else '32 bit',
		}

	@classmethod
	def informationPython(self):
		import platform
		# Structure used by Statistics.
		return {
			'implementation' : platform.python_implementation(),
			'version' : platform.python_version(),
			'architecture' : '64 bit' if '64' in platform.architecture() else '32 bit',
		}

	@classmethod
	def informationKodi(self):
		spmc = 'spmc' in xbmc.translatePath('special://xbmc').lower() or 'spmc' in xbmc.translatePath('special://logpath').lower()
		version = xbmc.getInfoLabel('System.BuildVersion')
		index = version.find(' ')
		if index >= 0: version = version[:index].strip()
		# Structure used by Statistics.
		return {
			'name' : 'SPMC' if spmc else 'Kodi',
			'version' : version,
		}

	@classmethod
	def informationAddon(self):
		return {
			'name' : self.name(),
			'author' : self.author(),
			'version' : self.version(),
		}

	@classmethod
	def manager(self):
		self.execute('ActivateWindow(systeminfo)')

	@classmethod
	def clean(self, confirm = True):
		from resources.lib.extensions import interface
		if confirm:
			choice = interface.Dialog.option(title = 33468, message = 33469)
		else:
			choice = True
		if choice:
			path = File.translate(File.PrefixSpecial + 'masterprofile/addon_data/' + System.id())
			File.deleteDirectory(path = path, force = True)
			self.temporaryClear()
			if File.existsDirectory(path):
				interface.Dialog.confirm(title = 33468, message = 33916)
			else:
				interface.Dialog.notification(title = 33468, message = 35538, icon = interface.Dialog.IconSuccess)

class Screen(object):

	Ratio4x3  =	'4x3'
	Ratio16x9 =	'16x9'
	Ratio20x9 =	'20x9'
	Ratios = (
		(Ratio4x3,  1.33333333),
		(Ratio16x9, 1.77777777),
		(Ratio20x9, 2.22222222),
	)

	@classmethod
	def dimension(self):
		return [self.width(), self.height()]

	@classmethod
	def width(self):
		try: return xbmcgui.getScreenWidth()
		except: return int(System.infoLabel('System.ScreenWidth')) # Older Kodi versions.

	@classmethod
	def height(self):
		try: return xbmcgui.getScreenHeight()
		except: return int(System.infoLabel('System.ScreenHeight')) # Older Kodi versions.

	@classmethod
	def ratio(self, closest = False):
		ratio = self.width() / float(self.height())
		if closest: ratio = Screen.Ratios[min(range(len(Screen.Ratios)), key = lambda i : abs(Screen.Ratios[i][1] - ratio))]
		return ratio

# NB: Make this a global var and not a class var of Settings.
# NB: Otherwise Kodi complaints about xbmcaddon.Addon being left in memory.
SettingsAddon = xbmcaddon.Addon(System.GaiaAddon)

class Settings(object):

	Database = 'settings'
	Lock = threading.Lock()

	HelpProperty = 'GaiaHelp'
	HelpId = 'help'

	SettingsId = 10140

	ParameterDefault = 'default'
	ParameterValue = 'value'
	ParameterVisible = 'visible'

	CategoryCount = 11

	CategoryGeneral = 0
	CategoryInterface = 1
	CategoryScraping = 2
	CategoryProviders = 3
	CategoryAccounts = 4
	CategoryStreaming = 5
	CategoryManual = 6
	CategoryAutomation = 7
	CategoryDownloads = 8
	CategorySubtitles = 9
	CategoryLibrary = 10
	CategoryLightpack = 11

	CacheInitialized = False
	CacheEnabled = False
	CacheMainData = None
	CacheMainValues = None
	CacheUserData = None
	CacheUserValues = None

	# Also check downloader.py.
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

		'library.locations.combined'			: 'special://userdata/addon_data/plugin.video.gaia/Library/',
		'library.locations.movies'				: 'special://userdata/addon_data/plugin.video.gaia/Library/Movies/',
		'library.locations.shows'				: 'special://userdata/addon_data/plugin.video.gaia/Library/Shows/',
		'library.locations.documentaries'		: 'special://userdata/addon_data/plugin.video.gaia/Library/Documentaries/',
		'library.locations.shorts'				: 'special://userdata/addon_data/plugin.video.gaia/Library/Shorts/',
	}

	@classmethod
	def _database(self):
		from resources.lib.extensions import database
		return database.Database.instance(Settings.Database, default = File.joinPath(System.path(), 'resources'))

	@classmethod
	def help(self, category = None):
		from resources.lib.extensions import window
		help = Converter.boolean(window.Window.propertyGlobal(Settings.HelpProperty))
		help = not help
		window.Window.propertyGlobalSet(Settings.HelpProperty, help)

		# Manually change the settings in the XML file.
		# If Settings.set() is used to iterativley set many values, the process can be very slow.
		#Settings.set(Settings.HelpId, help)
		data = File.readNow(self.pathProfile())
		if System.versionKodiNew(): data = re.sub('(id="%s\..*?")(.*)(<\/setting>)' % Settings.HelpId, '\\1>%s</setting>' % Converter.boolean(help, string = True), data, flags = re.IGNORECASE)
		else: data = re.sub('(id="%s\..*?" )(.*)(\/>)' % Settings.HelpId, '\\1value="%s" />' % Converter.boolean(help, string = True), data, flags = re.IGNORECASE)
		File.writeNow(self.pathProfile(), data)

		self.launch(category = category)

	@classmethod
	def helpClear(self):
		from resources.lib.extensions import window
		window.Window.propertyGlobalClear(Settings.HelpProperty)
		Settings.set(Settings.HelpId, False)

	@classmethod
	def path(self, id):
		path = self.get(id)
		if path == Settings.PathDefault or path.strip() == '' or not path:
			path = Settings.Paths[id]
		return path

	@classmethod
	def pathAddon(self):
		return File.joinPath(System.path(), 'resources', 'settings.xml')

	@classmethod
	def pathProfile(self):
		return File.joinPath(System.profile(), 'settings.xml')

	@classmethod
	def clear(self):
		File.delete(File.joinPath(System.profile(), 'settings.xml'))
		File.delete(File.joinPath(System.profile(), 'settings.db'))

	@classmethod
	def cache(self):
		# Ensures that the data always stays in memory.
		# Otherwise the "static variables" are deleted if there is no more reference to the Settings class.
		if not Settings.CacheInitialized:
			global SettingsAddon
			Settings.CacheInitialized = True
			Settings.CacheEnabled = Converter.boolean(SettingsAddon.getSetting('general.settings.cache'))
			Settings.CacheMainValues = {}
			Settings.CacheUserValues = {}

	@classmethod
	def cacheClear(self):
		# NB: Reset addon in order to clear Kodi's internal settings cache.
		# NB: Important for Reaper settings import in wizard.
		global SettingsAddon
		SettingsAddon = xbmcaddon.Addon(System.GaiaAddon)

		Settings.CacheInitialized = False
		Settings.CacheEnabled = False
		Settings.CacheMainData = None
		Settings.CacheMainValues = None
		Settings.CacheUserData = None
		Settings.CacheUserValues = None

	@classmethod
	def cacheEnabled(self):
		self.cache()
		return Settings.CacheEnabled

	@classmethod
	def cacheGet(self, id, raw, database = False):
		self.cache()
		if raw:
			if Settings.CacheMainData == None:
				Settings.CacheMainData = File.readNow(self.pathAddon())
			data = Settings.CacheMainData
			values = Settings.CacheMainValues
			parameter = Settings.ParameterDefault
		else:
			if Settings.CacheUserData == None:
				Settings.CacheUserData = File.readNow(self.pathProfile())
			data = Settings.CacheUserData
			values = Settings.CacheUserValues
			parameter = Settings.ParameterValue

		if id in values: # Already looked-up previously.
			return values[id]
		elif database:
			result = self._getDatabase(id = id)
			values[id] = result
			return result
		else:
			result = self.raw(id = id, parameter = parameter, data = data)
			if result == None: # Not in the userdata settings yet. Fallback to normal Kodi lookup.
				global SettingsAddon
				result = SettingsAddon.getSetting(id)
			values[id] = result
			return result

	@classmethod
	def cacheSet(self, id, value):
		self.cache()
		Settings.CacheUserValues[id] = value

	@classmethod
	def launch(self, category = None, section = None):
		from resources.lib.extensions import interface
		interface.Loader.hide()
		System.execute('Addon.OpenSettings(%s)' % System.id())
		if System.versionKodiNew():
			# gaiaremove
			# There seems to be an issue with the order of controls in Kodi 18, which doesn't allow one to reliably set the section index.
			# This has to be updated in later stable versions.
			if not category == None:
				System.execute('SetFocus(%i)' % (int(category) - 100))
		else:
			if not category == None:
				System.execute('SetFocus(%i)' % (int(category) + 100))
			if not section == None:
				System.execute('SetFocus(%i)' % (int(section) + 200))

	@classmethod
	def visible(self):
		from resources.lib.extensions import interface
		return interface.Dialog.dialogVisible(Settings.SettingsId)

	@classmethod
	def data(self):
		data = None
		path = File.joinPath(System.path(), 'resources', 'settings.xml')
		with open(path, 'r') as file:
			data = file.read()
		return data

	@classmethod
	def set(self, id, value, cached = False):
		if isinstance(value, (dict, list, tuple)):
			from resources.lib.extensions import database
			database = self._database()
			database._insert('INSERT OR IGNORE INTO %s (id) VALUES(?);' % Settings.Database, parameters = (id,))
			database._update('UPDATE %s SET data = ? WHERE id = ?;' % Settings.Database, parameters = (Converter.jsonTo(value), id))
			if cached or self.cacheEnabled(): self.cacheSet(id = id, value = value)
		else:
			if value is True or value is False: # Use is an not ==, becasue checks type as well. Otherwise int/float might also be true.
				value = Converter.boolean(value, string = True)
			else:
				value = str(value)
			global SettingsAddon
			Settings.Lock.acquire()
			SettingsAddon.setSetting(id = id, value = value)
			Settings.Lock.release()
			if cached or self.cacheEnabled(): self.cacheSet(id = id, value = value)

	@classmethod
	def setMultiple(self, id, values, label = None, attribute = 'items'):
		if label == None: label = len(values)
		self.set(id, label)
		self.set(id + '.' + attribute, values)

	# wait : number of seconds to sleep after command, since it takes a while to send.
	@classmethod
	def external(self, values, wait = 0.1):
		System.executePlugin(action = 'settingsExternal', parameters = values)
		Time.sleep(wait)

	# values is a dictionary.
	@classmethod
	def externalSave(self, values):
		if 'action' in values: del values['action']
		for id, value in values.iteritems():
			self.set(id = id, value = value, external = False)

	# Retrieve the values directly from the original settings instead of the saved user XML.
	# This is for internal values/settings that have a default value. If these values change, they are not propagate to the user XML, since the value was already set from a previous version.
	@classmethod
	def raw(self, id, parameter = ParameterDefault, data = None):
		try:
			if data == None: data = self.data()
			indexStart = data.find('id="%s"' % id)
			if indexStart < 0: return None
			indexStart += 4
			indexStart = data.find('"', indexStart)
			if indexStart < 0: return None
			indexEnd = data.find('/>', indexStart)
			if indexEnd < 0: indexEnd = data.find('/setting>', indexStart) # Kodi 18. Do not include the "<", since we search for it below.
			if indexEnd < 0: return None
			data = data[indexStart : indexEnd]
			indexStart = data.find(parameter + '="')
			if indexStart >= 0:
				indexStart = data.find('"', indexStart) + 1
				indexEnd = data.find('"', indexStart)
			elif parameter == Settings.ParameterValue and System.versionKodiNew():
				indexStart = data.find('>') + 1
				indexEnd = data.find('<', indexStart)
			else:
				return None
			return data[indexStart : indexEnd]
		except:
			return None

	@classmethod
	def _getDatabase(self, id):
		try:
			from resources.lib.extensions import database
			return Converter.jsonFrom(self._database()._selectValue('SELECT data FROM %s WHERE id = "%s";' % (Settings.Database, id)))
		except: return None

	# Kodi reads the settings file on every request, which is slow.
	# If the cached option is used, the settings XML is read manually once, and all requests are done from there, which is faster.
	@classmethod
	def get(self, id, raw = False, cached = True, database = False):
		if cached and self.cacheEnabled():
			return self.cacheGet(id = id, raw = raw, database = database)
		elif raw:
			return self.raw(id)
		elif database:
			return self._getDatabase(id)
		else:
			global SettingsAddon
			return SettingsAddon.getSetting(id)

	@classmethod
	def getString(self, id, raw = False, cached = True):
		return self.get(id = id, raw = raw, cached = cached)

	@classmethod
	def getBoolean(self, id, raw = False, cached = True):
		return Converter.boolean(self.get(id = id, raw = raw, cached = cached))

	@classmethod
	def getBool(self, id, raw = False, cached = True):
		return self.getBoolean(id = id, raw = raw, cached = cached)

	@classmethod
	def getNumber(self, id, raw = False, cached = True):
		return self.getDecimal(id = id, raw = raw, cached = cached)

	@classmethod
	def getDecimal(self, id, raw = False, cached = True):
		value = self.get(id = id, raw = raw, cached = cached)
		try: return float(value)
		except: return 0

	@classmethod
	def getFloat(self, id, raw = False, cached = True):
		return self.getDecimal(id = id, raw = raw, cached = cached)

	@classmethod
	def getInteger(self, id, raw = False, cached = True):
		value = self.get(id = id, raw = raw, cached = cached)
		try: return int(value)
		except: return 0

	@classmethod
	def getInt(self, id, raw = False, cached = True):
		return self.getInteger(id = id, raw = raw, cached = cached)

	@classmethod
	def getList(self, id, raw = False, cached = True):
		result = self.get(id = id, raw = raw, cached = cached, database = True)
		return [] if result == None or result == '' else result

	@classmethod
	def getObject(self, id, raw = False, cached = True):
		result = self.get(id = id, raw = raw, cached = cached, database = True)
		return None if result == None or result == '' else result

	@classmethod
	def has(self, id, raw = False, cached = True):
		result = self.get(id = id, raw = raw, cached = cached, database = True)
		return not result is None and not result is ''

	@classmethod
	def customGetReleases(self, type, raw = False):
		result = self.getList(id = '%s.additional.releases.items' % type, raw = raw)
		if result == '': return None
		else: return result

	@classmethod
	def customSetReleases(self, type):
		from resources.lib.extensions import metadata
		from resources.lib.extensions import interface
		releases = sorted([key[:key.find('|')] for key, value in metadata.Metadata.DictionaryReleases.iteritems()])
		current = self.customGetReleases(type)
		selection = []
		if current == None:
			selection = [i for i in range(len(releases))]
		else:
			selection = [releases.index(current[i]) for i in range(len(current))]
		items = interface.Dialog.options(title = 35164, items = releases, multiple = True, selection = selection)
		if not items == None:
			for i in range(len(items)):
				items[i] = releases[items[i]]
			if len(items) == 0: label = interface.Translation.string(33112)
			elif len(items) == len(releases): label = interface.Translation.string(33029)
			else: label = '%d %s' % (len(items), interface.Translation.string(35164))
			self.setMultiple(id = '%s.additional.releases' % type, values = items, label = label)
		self.launch(Settings.CategoryAutomation if type == 'automatic' else Settings.CategoryManual)

	@classmethod
	def customGetUploaders(self, type, raw = False):
		result = self.getList(id = '%s.additional.uploaders.items' % type, raw = raw)
		if result == '': return None
		else: return result

	@classmethod
	def customSetUploaders(self, type):
		from resources.lib.extensions import metadata
		from resources.lib.extensions import interface
		uploaders = sorted([key for key, value in metadata.Metadata.DictionaryUploaders.iteritems()])
		current = self.customGetUploaders(type)
		selection = []
		if current == None:
			selection = [i for i in range(len(uploaders))]
		else:
			selection = [uploaders.index(current[i]) for i in range(len(current))]
		items = interface.Dialog.options(title = 35165, items = uploaders, multiple = True, selection = selection)
		if not items == None:
			for i in range(len(items)):
				items[i] = uploaders[items[i]]
			if len(items) == 0: label = interface.Translation.string(33112)
			elif len(items) == len(uploaders): label = interface.Translation.string(33029)
			else: label = '%d %s' % (len(items), interface.Translation.string(35165))
			self.setMultiple(id = '%s.additional.uploaders' % type, values = items, label = label)
		self.launch(Settings.CategoryAutomation if type == 'automatic' else Settings.CategoryManual)

###################################################################
# MEDIA
###################################################################

class Media(object):

	TypeNone = None
	TypeMovie = 'movie'
	TypeDocumentary = 'documentary'
	TypeShort = 'short'
	TypeShow = 'show'
	TypeSeason = 'season'
	TypeEpisode = 'episode'

	NameSeasonSpecial = xbmcaddon.Addon(System.GaiaAddon).getLocalizedString(35637).encode('utf-8')
	NameSeasonLong = xbmcaddon.Addon(System.GaiaAddon).getLocalizedString(32055).encode('utf-8')
	NameSeasonShort = NameSeasonLong[0].upper()
	NameEpisodeLong = xbmcaddon.Addon(System.GaiaAddon).getLocalizedString(33028).encode('utf-8')
	NameEpisodeShort = NameEpisodeLong[0].upper()

	OrderTitle = 0
	OrderTitleYear = 1
	OrderYearTitle = 2
	OrderSeason = 3
	OrderEpisode = 4
	OrderSeasonEpisode = 5
	OrderEpisodeTitle = 6
	OrderSeasonEpisodeTitle = 7

	Default = 0

	DefaultMovie = 4
	DefaultDocumentary = 4
	DefaultShort = 4
	DefaultShow = 0
	DefaultSeason = 0
	DefaultEpisode = 6

	DefaultAeonNoxMovie = 0
	DefaultAeonNoxDocumentary = 0
	DefaultAeonNoxShort = 0
	DefaultAeonNoxShow = 0
	DefaultAeonNoxSeason = 0
	DefaultAeonNoxEpisode = 0

	FormatsTitle = [
		(OrderTitle,		'%s'),
		(OrderTitleYear,	'%s %d'),
		(OrderTitleYear,	'%s. %d'),
		(OrderTitleYear,	'%s - %d'),
		(OrderTitleYear,	'%s (%d)'),
		(OrderTitleYear,	'%s [%d]'),
		(OrderYearTitle,	'%d %s'),
		(OrderYearTitle,	'%d. %s'),
		(OrderYearTitle,	'%d - %s'),
		(OrderYearTitle,	'(%d) %s'),
		(OrderYearTitle,	'[%d] %s'),
	]

	FormatsSeason = [
		(OrderSeason,	NameSeasonLong + ' %01d'),
		(OrderSeason,	NameSeasonLong + ' %02d'),
		(OrderSeason,	NameSeasonShort + ' %01d'),
		(OrderSeason,	NameSeasonShort + ' %02d'),
		(OrderSeason,	'%01d ' + NameSeasonLong),
		(OrderSeason,	'%02d ' + NameSeasonLong),
		(OrderSeason,	'%01d. ' + NameSeasonLong),
		(OrderSeason,	'%02d. ' + NameSeasonLong),
		(OrderSeason,	'%01d'),
		(OrderSeason,	'%02d'),
	]

	FormatsEpisode = [
		(OrderTitle,				'%s'),
		(OrderEpisodeTitle,			'%01d %s'),
		(OrderEpisodeTitle,			'%02d %s'),
		(OrderEpisodeTitle,			'%01d. %s'),
		(OrderEpisodeTitle,			'%02d. %s'),
		(OrderSeasonEpisodeTitle,	'%01dx%01d %s'),
		(OrderSeasonEpisodeTitle,	'%01dx%02d %s'),
		(OrderSeasonEpisodeTitle,	'%02dx%02d %s'),
		(OrderEpisodeTitle,			NameEpisodeShort + '%01d %s'),
		(OrderEpisodeTitle,			NameEpisodeShort + '%02d %s'),
		(OrderEpisodeTitle,			NameEpisodeShort + '%01d. %s'),
		(OrderEpisodeTitle,			NameEpisodeShort + '%02d. %s'),
		(OrderSeasonEpisodeTitle,	NameSeasonShort + '%01d' + NameEpisodeShort + '%01d %s'),
		(OrderSeasonEpisodeTitle,	NameSeasonShort + '%01d' + NameEpisodeShort + '%02d %s'),
		(OrderSeasonEpisodeTitle,	NameSeasonShort + '%02d' + NameEpisodeShort + '%02d %s'),
		(OrderEpisode,				'%01d'),
		(OrderEpisode,				'%02d'),
		(OrderSeasonEpisode,		'%01dx%01d'),
		(OrderSeasonEpisode,		'%01dx%02d'),
		(OrderSeasonEpisode,		'%02dx%02d'),
		(OrderEpisode,				NameEpisodeShort + '%01d'),
		(OrderEpisode,				NameEpisodeShort + '%02d'),
		(OrderSeasonEpisode,		NameSeasonShort + '%01d' + NameEpisodeShort + '%01d'),
		(OrderSeasonEpisode,		NameSeasonShort + '%01d' + NameEpisodeShort + '%02d'),
		(OrderSeasonEpisode,		NameSeasonShort + '%02d' + NameEpisodeShort + '%02d'),
	]

	FormatsSkin = None
	FormatsDefault = None

	@classmethod
	def _format(self, format, title = None, year = None, season = None, episode = None, special = False):
		order = format[0]
		format = format[1]
		if order == Media.OrderTitle:
			return format % (title)
		elif order == Media.OrderTitleYear:
			return format % (title, year)
		elif order == Media.OrderYearTitle:
			return format % (year, title)
		elif order == Media.OrderSeason:
			if season == 0 and special: return Media.NameSeasonSpecial
			else: return format % (season)
		elif order == Media.OrderEpisode:
			return format % (episode)
		elif order == Media.OrderSeasonEpisode:
			return format % (season, episode)
		elif order == Media.OrderEpisodeTitle:
			return format % (episode, title)
		elif order == Media.OrderSeasonEpisodeTitle:
			return format % (season, episode, title)
		else:
			return title

	@classmethod
	def _extract(self, metadata, encode = False):
		title = metadata['tvshowtitle'] if 'tvshowtitle' in metadata else metadata['title']
		if encode: title = Converter.unicode(string = title, umlaut = True)
		year = int(metadata['year']) if 'year' in metadata else None
		season = int(metadata['season']) if 'season' in metadata else None
		episode = int(metadata['episode']) if 'episode' in metadata else None
		pack = bool(metadata['pack']) if 'pack' in metadata else False
		return (title, year, season, episode, pack)

	@classmethod
	def _data(self, title, year, season, episode, encode = False):
		if not title == None and encode: title = Converter.unicode(string = title, umlaut = True)
		if not year == None: year = int(year)
		if not season == None: season = int(season)
		if not episode == None: episode = int(episode)
		return (title, year, season, episode)

	@classmethod
	def _initialize(self, skin = True):
		data = Media.FormatsSkin if skin else Media.FormatsDefault
		if data == None:
			from resources.lib.extensions import interface
			aeonNox = interface.Skin.isGaiaAeonNox() if skin else False
			data = {}

			setting = Settings.getInteger('interface.title.movies')
			if setting == Media.Default: setting = Media.DefaultAeonNoxMovie if aeonNox else Media.DefaultMovie
			else: setting -= 1
			data[Media.TypeMovie] = Media.FormatsTitle[setting]

			setting = Settings.getInteger('interface.title.documentaries')
			if setting == Media.Default: setting = Media.DefaultAeonNoxDocumentary if aeonNox else Media.DefaultDocumentary
			else: setting -= 1
			data[Media.TypeDocumentary] = Media.FormatsTitle[setting]

			setting = Settings.getInteger('interface.title.shorts')
			if setting == Media.Default: setting = Media.DefaultAeonNoxShort if aeonNox else Media.DefaultShort
			else: setting -= 1
			data[Media.TypeShort] = Media.FormatsTitle[setting]

			setting = Settings.getInteger('interface.title.shows')
			if setting == Media.Default: setting = Media.DefaultAeonNoxShow if aeonNox else Media.DefaultShow
			else: setting -= 1
			data[Media.TypeShow] = Media.FormatsTitle[setting]

			setting = Settings.getInteger('interface.title.seasons')
			if setting == Media.Default: setting = Media.DefaultAeonNoxSeason if aeonNox else Media.DefaultSeason
			else: setting -= 1
			data[Media.TypeSeason] = Media.FormatsSeason[setting]

			setting = Settings.getInteger('interface.title.episodes')
			if setting == Media.Default: setting = Media.DefaultAeonNoxEpisode if aeonNox else Media.DefaultEpisode
			else: setting -= 1
			data[Media.TypeEpisode] = Media.FormatsEpisode[setting]

			if skin: Media.FormatsSkin = data
			else: Media.FormatsDefault = data
		return data

	@classmethod
	def title(self, type = TypeNone, metadata = None, title = None, year = None, season = None, episode = None, encode = False, pack = False, special = False, skin = True):
		if not metadata == None: title, year, season, episode, packs = self._extract(metadata = metadata, encode = encode)
		title, year, season, episode = self._data(title = title, year = year, season = season, episode = episode, encode = encode)

		if type == Media.TypeNone:
			pack = (pack and packs)
			if not season == None and not episode == None and not pack:
				type = Media.TypeEpisode
			elif not season == None:
				type = Media.TypeSeason
			else:
				type = Media.TypeMovie

		formats = self._initialize(skin = skin)
		format = formats[type]
		return self._format(format = format, title = title, year = year, season = season, episode = episode, special = special)

	# Raw title to search on the web/scrapers.
	@classmethod
	def titleUniversal(self, metadata = None, title = None, year = None, season = None, episode = None, encode = False):
		if not metadata == None:
			title, year, season, episode, packs = self._extract(metadata = metadata, encode = encode)
		title, year, season, episode = self._data(title = title, year = year, season = season, episode = episode, encode = encode)

		if not season == None and not episode == None:
			return '%s S%02dE%02d' % (title, season, episode)
		elif not year == None:
			return  '%s (%s)' % (title, year)
		else:
			return title

	@classmethod
	def typeMovie(self, type):
		return type == Media.TypeMovie or type == Media.TypeDocumentary or type == Media.TypeShort

	@classmethod
	def typeTelevision(self, type):
		return type == Media.TypeShow or type == Media.TypeSeason or type == Media.TypeEpisode

	@classmethod
	def metadataClean(self, metadata, exclude = None):
		# Filter out non-existing/custom keys.
		# Otherise there are tons of errors in Kodi 18 log.
		if metadata == None: return metadata
		allowed = ['genre',	'country', 'year', 'episode', 'season', 'sortepisode', 'sortseason', 'episodeguide', 'showlink', 'top250', 'setid', 'tracknumber', 'rating', 'userrating', 'watched', 'playcount', 'overlay', 'cast', 'castandrole', 'director', 'mpaa', 'plot', 'plotoutline', 'title', 'originaltitle', 'sorttitle', 'duration', 'studio', 'tagline', 'writer', 'tvshowtitle', 'premiered', 'status', 'set', 'setoverview', 'tag', 'imdbnumber', 'code', 'aired', 'credits', 'lastplayed', 'album', 'artist', 'votes', 'path', 'trailer', 'dateadded', 'mediatype', 'dbid']
		if exclude:
			if not isinstance(exclude, (list, tuple)): exclude = ['userrating', 'watched', 'playcount', 'overlay', 'duration']
			allowed = [i for i in allowed if not i in exclude]
		return {k: v for k, v in metadata.iteritems() if k in allowed}

###################################################################
# LIGHTPACK
###################################################################

class Lightpack(object):

	ExecutionKodi = 'kodi'
	ExecutionGaia = 'gaia'

	StatusUnknown = None
	StatusOn = 'on'
	StatusOff = 'off'

	# Number of LEDs in Lightpack
	MapSize = 10

	PathWindows = ['C:\\Program Files (x86)\\Prismatik\\Prismatik.exe', 'C:\\Program Files\\Prismatik\\Prismatik.exe']
	PathLinux = ['/usr/bin/prismatik', '/usr/local/bin/prismatik']

	def __init__(self):
		self.mError = False

		self.mEnabled = Settings.getBoolean('lightpack.enabled')

		self.mPrismatikMode = Settings.getInteger('lightpack.prismatik.mode')
		self.mPrismatikLocation = Settings.getString('lightpack.prismatik.location')

		self.mLaunchAutomatic = Settings.getInteger('lightpack.launch.automatic')
		self.mLaunchAnimation = Settings.getBoolean('lightpack.launch.animation')

		self.mProfileFixed = Settings.getBoolean('lightpack.profile.fixed')
		self.mProfileName = Settings.getString('lightpack.profile.name')

		self.mCount = Settings.getInteger('lightpack.count')
		self.mMap = self._map()

		self.mHost = Settings.getString('lightpack.connection.host')
		self.mPort = Settings.getInteger('lightpack.connection.port')
		self.mAuthorization = Settings.getBoolean('lightpack.connection.authorization')
		self.mApiKey = Settings.getString('lightpack.connection.api')

		self.mLightpack = None
		self._initialize()

	def __del__(self):
		try: self._unlock()
		except: pass
		try: self._disconnect()
		except: pass

	def _map(self):
		result = []
		set = 10
		for i in range(self.mCount):
			start = Lightpack.MapSize * i
			for j in range(1, Lightpack.MapSize + 1):
				result.append(start + j)
		return result

	def _initialize(self):
		if not self.mEnabled:
			return

		from resources.lib.externals.lightpack import lightpack
		api = self.mApiKey if self.mAuthorization else ''
		self.mLightpack = lightpack.lightpack(self.mHost, self.mPort, api, self.mMap)

	def _error(self):
		return self.mError

	def _errorSuccess(self):
		return not self.mError

	def _errorSet(self):
		self.mError = True

	def _errorClear(self):
		self.mError = False

	def _connect(self):
		from resources.lib.externals.lightpack import lightpack
		return self.mLightpack.connect() >= 0

	def _disconnect(self):
		from resources.lib.externals.lightpack import lightpack
		self.mLightpack.disconnect()

	def _lock(self):
		from resources.lib.externals.lightpack import lightpack
		self.mLightpack.lock()

	def _unlock(self):
		from resources.lib.externals.lightpack import lightpack
		self.mLightpack.unlock()

	# Color is RGB array or hex. If index is None, uses all LEDs.
	def _colorSet(self, color, index = None, lock = False):
		from resources.lib.externals.lightpack import lightpack
		if lock: self.mLightpack.lock()

		if isinstance(color, basestring):
			color = color.replace('#', '')
			if len(color) == 6:
				color = 'FF' + color
			color = [int(color[i : i + 2], 16) for i in range(2, 8, 2)]

		if index == None:
			self.mLightpack.setColorToAll(color[0], color[1], color[2])
		else:
			self.mLightpack.setColor(index, color[0], color[1], color[2])

		if lock: self.mLightpack.unlock()

	def _profileSet(self, profile):
		from resources.lib.externals.lightpack import lightpack
		try:
			self._errorClear()
			self._lock()
			self.mLightpack.setProfile(profile)
			self._unlock()
		except:
			self._errorSet()
		return self._errorSuccess()

	def _message(self):
		from resources.lib.extensions import interface
		interface.Dialog.confirm(title = 33406, message = 33410)

	def _launchEnabled(self, execution):
		if self.mEnabled:
			if execution == Lightpack.ExecutionKodi and (self.mLaunchAutomatic == 1 or self.mLaunchAutomatic == 3):
				return True
			if execution == Lightpack.ExecutionGaia and (self.mLaunchAutomatic == 2 or self.mLaunchAutomatic == 3):
				return True
		return False

	def _launch(self):
		try:
			if not self._connect():
				raise Exception()
		except:
			try:
				if self.mLaunchAutomatic > 0:
					automatic = self.mPrismatikMode == 0 or self.mPrismatikPath == None or self.mPrismatikPath == ''

					if 'win' in sys.platform or 'nt' in sys.platform:
						command = 'start "Prismatik" /B /MIN "%s"'
						if automatic:
							executed = False
							for path in Lightpack.PathWindows:
								if os.path.exists(path):
									os.system(command % path)
									executed = True
									break
							if not executed:
								os.system('prismatik') # Global path
						else:
							os.system(command % self.mPrismatikPath)
					elif 'darwin' in sys.platform or 'max' in sys.platform:
						os.system('open "' + self.mPrismatikPath + '"')
					else:
						command = '"%s" &'
						if automatic:
							executed = False
							for path in Lightpack.PathLinux:
								if os.path.exists(path):
									os.system(command % path)
									executed = True
									break
							if not executed:
								os.system('prismatik') # Global path
						else:
							os.system(command % self.mPrismatikPath)

					Time.sleep(3)
					self._connect()
					self.switchOn()
			except:
				self._errorSet()

		try:
			if self.status() == Lightpack.StatusUnknown:
				self.mLightpack = None
			else:
				try:
					if self.mProfileFixed and self.mProfileName and not self.mProfileName == '':
						self._profileSet(self.mProfileName)
				except:
					self._errorSet()
		except:
			self.mLightpack = None

		self.animate(force = False)

	def launchAutomatic(self):
		self.launch(Lightpack.ExecutionKodi)

	def launch(self, execution):
		if self._launchEnabled(execution = execution):
			thread = threading.Thread(target = self._launch)
			thread.start()

	@classmethod
	def settings(self):
		Settings.launch(category = Settings.CategoryLightpack)

	def enabled(self):
		return self.mEnabled

	def status(self):
		if not self.mEnabled:
			return Lightpack.StatusUnknown

		try:
			from resources.lib.externals.lightpack import lightpack
			self._errorClear()
			self._lock()
			status = self.mLightpack.getStatus()
			self._unlock()
			return status.strip()
		except:
			self._errorSet()
		return Lightpack.StatusUnknown

	def statusUnknown(self):
		return self.status() == Lightpack.StatusUnknown

	def statusOn(self):
		return self.status() == Lightpack.StatusOn

	def statusOff(self):
		return self.status() == Lightpack.StatusOff

	def switchOn(self, message = False):
		if not self.mEnabled:
			return False

		try:
			from resources.lib.externals.lightpack import lightpack
			self._errorClear()
			self._lock()
			self.mLightpack.turnOn()
			self._unlock()
		except:
			self._errorSet()
		success = self._errorSuccess()
		if not success and message: self._message()
		return success

	def switchOff(self, message = False):
		if not self.mEnabled:
			return False

		try:
			from resources.lib.externals.lightpack import lightpack
			self._errorClear()
			self._lock()
			self.mLightpack.turnOff()
			self._unlock()
		except:
			self._errorSet()
		success = self._errorSuccess()
		if not success and message: self._message()
		return success

	def _animateSpin(self, color):
		for i in range(len(self.mMap)):
			self._colorSet(color = color, index = i)
			Time.sleep(0.1)

	def animate(self, force = True, message = False, delay = False):
		if not self.mEnabled:
			return False

		if force or self.mLaunchAnimation:
			try:
				self.switchOn()
				self._errorClear()
				if delay: # The Lightpack sometimes gets stuck on the red light on startup animation. Maybe this delay will solve that?
					Time.sleep(1)
				self._lock()

				for i in range(2):
					self._animateSpin('FFFF0000')
					self._animateSpin('FFFF00FF')
					self._animateSpin('FF0000FF')
					self._animateSpin('FF00FFFF')
					self._animateSpin('FF00FF00')
					self._animateSpin('FFFFFF00')

				self._unlock()
			except:
				self._errorSet()
		else:
			return False
		success = self._errorSuccess()
		if not success and message: self._message()
		return success

###################################################################
# PLATFORM
###################################################################

PlatformInstance = None

class Platform:

	FamilyWindows = 'windows'
	FamilyUnix = 'unix'

	SystemWindows = 'windows'
	SystemMacintosh = 'macintosh'
	SystemLinux = 'linux'
	SystemAndroid = 'android'

	Architecture64bit = '64bit'
	Architecture32bit = '32bit'
	ArchitectureArm = 'arm'

	def __init__(self):
		self.mFamilyType = None
		self.mFamilyName = None
		self.mSystemType = None
		self.mSystemName = None
		self.mDistributionType = None
		self.mDistributionName = None
		self.mVersionShort = None
		self.mVersionFull = None
		self.mArchitecture = None
		self.mAgent = None
		self._detect()

	@classmethod
	def instance(self):
		global PlatformInstance
		if PlatformInstance == None:
			PlatformInstance = Platform()
		return PlatformInstance

	@classmethod
	def familyType(self):
		return self.instance().mFamilyType

	@classmethod
	def familyName(self):
		return self.instance().mFamilyName

	@classmethod
	def systemType(self):
		return self.instance().mSystemType

	@classmethod
	def systemName(self):
		return self.instance().mSystemName

	@classmethod
	def distributionType(self):
		return self.instance().mDistributionType

	@classmethod
	def distributionName(self):
		return self.instance().mDistributionName

	@classmethod
	def versionShort(self):
		return self.instance().mVersionShort

	@classmethod
	def versionFull(self):
		return self.instance().mVersionFull

	@classmethod
	def architecture(self):
		return self.instance().mArchitecture

	@classmethod
	def agent(self):
		return self.instance().mAgent

	@classmethod
	def _detectWindows(self):
		import platform
		try: return Platform.SystemWindows in platform.system().lower()
		except: return False

	@classmethod
	def _detectMacintosh(self):
		import platform
		try:
			version = platform.mac_ver()
			return not version[0] == None and not version[0] == ''
		except: return False

	@classmethod
	def _detectLinux(self):
		import platform
		try: return platform.system().lower() == 'linux' and not self._detectAndroid()
		except: return False

	@classmethod
	def _detectAndroid(self):
		import platform
		try:
			system = platform.system().lower()
			distribution = platform.linux_distribution()
			if Platform.SystemAndroid in system or Platform.SystemAndroid in system or (len(distribution) > 0 and isinstance(distribution[0], basestring) and Platform.SystemAndroid in distribution[0].lower()):
				return True
			if system == Platform.SystemLinux:
				import subprocess
				id = ''
				if 'ANDROID_ARGUMENT' in os.environ:
					id = True
				if id == None or id == '':
					try: id = subprocess.Popen('getprop ril.serialnumber'.split(), stdout = subprocess.PIPE).communicate()[0].trim()
					except: pass
				if id == None or id == '':
					try: id = subprocess.Popen('getprop ro.serialno'.split(), stdout = subprocess.PIPE).communicate()[0].trim()
					except: pass
				if id == None or id == '':
					try: id = subprocess.Popen('getprop sys.serialnumber'.split(), stdout = subprocess.PIPE).communicate()[0].trim()
					except: pass
				if id == None or id == '':
					try: id = subprocess.Popen('getprop gsm.sn1'.split(), stdout = subprocess.PIPE).communicate()[0].trim()
					except: pass
				if not id == None and not id == '':
					try: return not 'not found' in id
					except: return True
		except: pass
		return False

	def _detect(self):
		import platform
		try:
			if self._detectWindows():
				self.mFamilyType = Platform.FamilyWindows
				self.mFamilyName = self.mFamilyType.capitalize()

				self.mSystemType = Platform.SystemWindows
				self.mSystemName = self.mSystemType.capitalize()

				version = platform.win32_ver()
				self.mVersionShort = version[0]
				self.mVersionFull = version[1]
			elif self._detectAndroid():
				self.mFamilyType = Platform.FamilyUnix
				self.mFamilyName = self.mFamilyType.capitalize()

				self.mSystemType = Platform.SystemAndroid
				self.mSystemName =  self.mSystemType.capitalize()

				distribution = platform.linux_distribution()
				self.mVersionShort = distribution[1]
				self.mVersionFull = distribution[2]
			elif self._detectMacintosh():
				self.mFamilyType = Platform.FamilyUnix
				self.mFamilyName = self.mFamilyType.capitalize()

				self.mSystemType = Platform.SystemMacintosh
				self.mSystemName =  self.mSystemType.capitalize()

				mac = platform.mac_ver()
				self.mVersionShort = mac[0]
				self.mVersionFull = self.mVersionShort
			elif self._detectLinux():
				self.mFamilyType = Platform.FamilyUnix
				self.mFamilyName = self.mFamilyType.capitalize()

				self.mSystemType = Platform.SystemLinux
				self.mSystemName =  self.mSystemType.capitalize()

				distribution = platform.linux_distribution()
				self.mDistributionType = distribution[0].lower().replace('"', '').replace(' ', '')
				self.mDistributionName = distribution[0].replace('"', '')

				self.mVersionShort = distribution[1]
				self.mVersionFull = distribution[2]

			machine = platform.machine().lower()
			if '64' in machine: self.mArchitecture = Platform.Architecture64bit
			elif '86' in machine or '32' in machine or 'i386' in machine or 'i686' in machine: self.mArchitecture = Platform.Architecture32bit
			elif 'arm' in machine or 'risc' in machine or 'acorn' in machine: self.mArchitecture = Platform.ArchitectureArm

			try:
				system = ''
				if self.mSystemType == Platform.SystemWindows:
					system += 'Windows NT'
					if self.mVersionFull: system += ' ' + self.mVersionFull
					if self.mArchitecture == Platform.Architecture64bit: system += '; Win64; x64'
					elif self.mArchitecture == Platform.ArchitectureArm: system += '; ARM'
				elif self.mSystemType == Platform.SystemMacintosh:
					system += 'Macintosh; Intel Mac OS X ' + self.mVersionShort.replace('.', '_')
				elif self.mSystemType == Platform.SystemLinux:
					system += 'X11;'
					if self.mDistributionName: system += ' ' + self.mDistributionName + ';'
					system += ' Linux;'
					if self.mArchitecture == Platform.Architecture32bit: system += ' x86'
					elif self.mArchitecture == Platform.Architecture64bit: system += ' x86_64'
					elif self.mArchitecture == Platform.ArchitectureArm: system += ' arm'
				elif self.mSystemType == Platform.SystemAndroid:
					system += 'Linux; Android ' + self.mVersionShort
				if not system == '': system = '(' + system + ') '
				system = System.name() + '/' + System.version() + ' ' + system + 'Kodi/' + str(System.versionKodi())

				# Do in 2 steps, previous statement can fail
				self.mAgent = system
			except:
				Logger.error()

		except:
			Logger.error()

###################################################################
# HARDWARE
###################################################################

class Hardware(object):

	PerformanceSlow = 'slow'
	PerformanceMedium = 'medium'
	PerformanceFast = 'fast'

	ConfigurationSlow = {'processors' : 2, 'memory' : 2147483648}
	ConfigurationMedium = {'processors' : 4, 'memory' : 4294967296}

	@classmethod
	def identifier(self):
		import subprocess
		id = None

		# Windows
		if os.name == 'nt':
			if id == None or ' ' in id:
				try:
					import _winreg
					registry = _winreg.HKEY_LOCAL_MACHINE
					address = 'SOFTWARE\\Microsoft\\Cryptography'
					keyargs = _winreg.KEY_READ | _winreg.KEY_WOW64_64KEY
					key = _winreg.OpenKey(registry, address, 0, keyargs)
					value = _winreg.QueryValueEx(key, 'MachineGuid')
					_winreg.CloseKey(key)
					id = value[0]
				except: pass

			if id == None or ' ' in id:
				try:
					id = subprocess.Popen('wmic csproduct get uuid'.split(), stdout = subprocess.PIPE).communicate()[0]
				except: pass

			if id == None or ' ' in id:
				try:
					id = subprocess.Popen('dmidecode.exe -s system-uuid'.split(), stdout = subprocess.PIPE).communicate()[0]
				except: pass

		# Android
		if id == None or ' ' in id:
			try:
				id = subprocess.Popen('getprop ril.serialnumber'.split(), stdout = subprocess.PIPE).communicate()[0]
			except: pass
		if id == None or ' ' in id:
			try:
				id = subprocess.Popen('getprop ro.serialno'.split(), stdout = subprocess.PIPE).communicate()[0]
			except: pass
		if id == None or ' ' in id:
			try:
				id = subprocess.Popen('getprop sys.serialnumber'.split(), stdout = subprocess.PIPE).communicate()[0]
			except: pass
		if id == None or ' ' in id:
			try:
				id = subprocess.Popen('getprop gsm.sn1'.split(), stdout = subprocess.PIPE).communicate()[0]
			except: pass

		# Linux
		if id == None or ' ' in id:
			try:
				id = subprocess.Popen('hal-get-property --udi /org/freedesktop/Hal/devices/computer --key system.hardware.uuid'.split(), stdout = subprocess.PIPE).communicate()[0]
			except: pass

		# Linux
		if id == None or ' ' in id:
			try:
				id = subprocess.Popen('/sys/class/dmi/id/board_serial', stdout = subprocess.PIPE).communicate()[0]
			except: pass

		# Linux
		if id == None or ' ' in id:
			try:
				id = subprocess.Popen('/sys/class/dmi/id/product_uuid', stdout = subprocess.PIPE).communicate()[0]
			except: pass

		# Linux
		if id == None or ' ' in id:
			try:
				id = subprocess.Popen('cat /var/lib/dbus/machine-id', stdout = subprocess.PIPE).communicate()[0]
			except: pass

		# If still not found, get the MAC address
		if id == None or ' ' in id:
			try:
				import psutil
				nics = psutil.net_if_addrs()
				nics.pop('lo')
				for i in nics:
					for j in nics[i]:
						if j.family == 17:
							id = j.address
							break
			except: pass

		# If still not found, get the MAC address
		if id == None or ' ' in id:
			try:
				import netifaces
				interface = [i for i in netifaces.interfaces() if not i.startswith('lo')][0]
				id = netifaces.ifaddresses(interface)[netifaces.AF_LINK]
			except: pass

		# If still not found, get the MAC address
		if id == None or ' ' in id:
			try:
				import uuid
				# Might return a random ID on failure
				# In such a case, save it to the settings and return it, ensuring that the same ID is used.
				id = Settings.getString('general.statistics.identifier')
				if id == None or id == '':
					id = uuid.getnode()
					Settings.set('general.statistics.identifier', id)
			except: pass

		if id == None: id = ''
		else: id = str(id)

		try: id += str(System.informationSystem()['name'])
		except: pass

		try: id += str(self.processors())
		except: pass

		try: id += str(self.memory())
		except: pass

		return Hash.sha256(id)

	@classmethod
	def performance(self):
		processors = self.processors()
		memory = self.memory()

		if processors == None and memory == None:
			return Hardware.PerformanceMedium

		if not processors == None and not Hardware.ConfigurationSlow['processors'] == None and processors <= Hardware.ConfigurationSlow['processors']:
			return Hardware.PerformanceSlow
		if not memory == None and not Hardware.ConfigurationSlow['memory'] == None and memory <= Hardware.ConfigurationSlow['memory']:
			return Hardware.PerformanceSlow

		if not processors == None and not Hardware.ConfigurationMedium['processors'] == None and processors <= Hardware.ConfigurationMedium['processors']:
			return Hardware.PerformanceMedium
		if not memory == None and not Hardware.ConfigurationMedium['memory'] == None and memory <= Hardware.ConfigurationMedium['memory']:
			return Hardware.PerformanceMedium

		return Hardware.PerformanceFast

	@classmethod
	def slow(self):
		processors = self.processors()
		if not processors == None and not Hardware.ConfigurationSlow['processors'] == None and processors <= Hardware.ConfigurationSlow['processors']:
			return True
		memory = self.memory()
		if not memory == None and not Hardware.ConfigurationSlow['memory'] == None and memory <= Hardware.ConfigurationSlow['memory']:
			return True
		return False

	@classmethod
	def processors(self):
		# http://stackoverflow.com/questions/1006289/how-to-find-out-the-number-of-cpus-using-python

		import subprocess

		# Python 2.6+
		try:
			import multiprocessing
			return multiprocessing.cpu_count()
		except: pass

		# PSUtil
		try:
			import psutil
			return psutil.cpu_count() # psutil.NUM_CPUS on old versions
		except: pass

		# POSIX
		try:
			result = int(os.sysconf('SC_NPROCESSORS_ONLN'))
			if result > 0: return result
		except: pass

		# Windows
		try:
			result = int(os.environ['NUMBER_OF_PROCESSORS'])
			if result > 0: return result
		except: pass

		# jython
		try:
			from java.lang import Runtime
			runtime = Runtime.getRuntime()
			result = runtime.availableProcessors()
			if result > 0: return result
		except: pass

		# cpuset
		# cpuset may restrict the number of *available* processors
		try:
			result = re.search(r'(?m)^Cpus_allowed:\s*(.*)$', open('/proc/self/status').read())
			if result:
				result = bin(int(result.group(1).replace(',', ''), 16)).count('1')
				if result > 0: return result
		except: pass

		# BSD
		try:
			sysctl = subprocess.Popen(['sysctl', '-n', 'hw.ncpu'], stdout=subprocess.PIPE)
			scStdout = sysctl.communicate()[0]
			result = int(scStdout)
			if result > 0: return result
		except: pass

		# Linux
		try:
			result = open('/proc/cpuinfo').read().count('processor\t:')
			if result > 0: return result
		except: pass

		# Solaris
		try:
			pseudoDevices = os.listdir('/devices/pseudo/')
			result = 0
			for pd in pseudoDevices:
				if re.match(r'^cpuid@[0-9]+$', pd):
					result += 1
			if result > 0: return result
		except: pass

		# Other UNIXes (heuristic)
		try:
			try:
				dmesg = open('/var/run/dmesg.boot').read()
			except IOError:
				dmesgProcess = subprocess.Popen(['dmesg'], stdout=subprocess.PIPE)
				dmesg = dmesgProcess.communicate()[0]
			result = 0
			while '\ncpu' + str(result) + ':' in dmesg:
				result += 1
			if result > 0: return result
		except: pass

		return None

	@classmethod
	def memory(self):
		try:
			from psutil import virtual_memory
			memory = virtual_memory().total
			if memory > 0: return memory
		except: pass

		try:
			memory = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
			if memory > 0: return memory
		except: pass

		try:
			memory = dict((i.split()[0].rstrip(':'),int(i.split()[1])) for i in open('/proc/meminfo').readlines())
			memory = memory['MemTotal'] * 1024
			if memory > 0: return memory
		except: pass

		try:
			from ctypes import Structure, c_int32, c_uint64, sizeof, byref, windll
			class MemoryStatusEx(Structure):
				_fields_ = [
					('length', c_int32),
					('memoryLoad', c_int32),
					('totalPhys', c_uint64),
					('availPhys', c_uint64),
					('totalPageFile', c_uint64),
					('availPageFile', c_uint64),
					('totalVirtual', c_uint64),
					('availVirtual', c_uint64),
					('availExtendedVirtual', c_uint64)]
				def __init__(self):
					self.length = sizeof(self)
			memory = MemoryStatusEx()
			windll.kernel32.GlobalMemoryStatusEx(byref(memory))
			memory = memory.totalPhys
			if memory > 0: return memory
		except: pass

		return None

###################################################################
# EXTENSIONS
###################################################################

class Extensions(object):

	# Types
	TypeRequired = 'required'
	TypeRecommended = 'recommended'
	TypeOptional = 'optional'

	# IDs
	IdGaiaAddon = 'plugin.video.gaia'
	IdGaiaRepository = 'repository.gaia'
	IdGaiaArtwork = 'script.gaia.artwork'
	IdGaiaBinaries = 'script.gaia.binaries'
	IdGaiaResources = 'script.gaia.resources'
	IdGaiaIcons = 'script.gaia.icons'
	IdGaiaSkins = 'script.gaia.skins'
	IdGaiaAeonNox = 'skin.gaia.aeon.nox' if System.versionKodi() < 18 else 'skin.gaia.aeon.nox.18'
	IdResolveUrl = 'script.module.resolveurl'
	IdUrlResolver = 'script.module.urlresolver'
	IdOpeScrapers = 'script.module.openscrapers'
	IdLamScrapers = 'script.module.lambdascrapers'
	IdCivScrapers = 'script.module.civitasscrapers'
	IdGloScrapers = 'script.module.globalscrapers'
	IdUniScrapers = 'script.module.universalscrapers'
	IdNanScrapers = 'script.module.nanscrapers'
	IdMetaHandler = 'script.module.metahandler'
	IdTrakt = 'script.trakt'
	IdElementum = 'plugin.video.elementum'
	IdElementumRepository = 'repository.elementum'
	IdQuasar = 'plugin.video.quasar'
	IdQuasarRepository = 'repository.quasar'
	IdExtendedInfo = 'script.extendedinfo'
	IdYouTube = 'plugin.video.youtube'

	@classmethod
	def settings(self, id):
		try:
			System.execute('Addon.OpenSettings(%s)' % id)
			return True
		except:
			return False

	@classmethod
	def launch(self, id):
		try:
			System.execute('RunAddon(%s)' % id)
			return True
		except:
			return False

	@classmethod
	def installed(self, id):
		try:
			idReal = xbmcaddon.Addon(id).getAddonInfo('id')
			return id == idReal
		except:
			return False

	@classmethod
	def enable(self, id, refresh = False):
		try: System.execute('InstallAddon(%s)' % id)
		except: pass
		try: System.executeJson(addon = id, method = 'Addons.SetAddonEnabled', parameters = {'enabled' : True})
		except: pass
		if refresh:
			try: System.execute('Container.Refresh')
			except: pass

	@classmethod
	def disable(self, id, refresh = False):
		try: System.executeJson(addon = id, method = 'Addons.SetAddonEnabled', parameters = {'enabled' : False})
		except: pass
		if refresh:
			try: System.execute('Container.Refresh')
			except: pass

	@classmethod
	def list(self):
		from resources.lib.extensions import orionoid
		from resources.lib.extensions import interface

		result = [
			{
				'id' : Extensions.IdGaiaRepository,
				'name' : 'Gaia Repository',
				'type' : Extensions.TypeRequired,
				'description' : 33917,
				'icon' : 'extensionsgaia.png',
			},
			{
				'id' : Extensions.IdGaiaResources,
				'name' : 'Gaia Resources',
				'type' : Extensions.TypeRequired,
				'description' : 33726,
				'icon' : 'extensionsgaia.png',
			},
			{
				'id' : Extensions.IdGaiaArtwork,
				'name' : 'Gaia Artwork',
				'type' : Extensions.TypeRecommended,
				'description' : 33727,
				'icon' : 'extensionsgaia.png',
			},
			{
				'id' : Extensions.IdGaiaBinaries,
				'name' : 'Gaia Binaries',
				'type' : Extensions.TypeOptional,
				'description' : 33728,
				'icon' : 'extensionsgaia.png',
			},
			{
				'id' : Extensions.IdGaiaIcons,
				'name' : 'Gaia Icons',
				'type' : Extensions.TypeOptional,
				'description' : 33729,
				'icon' : 'extensionsgaia.png',
			},
			{
				'id' : Extensions.IdGaiaSkins,
				'name' : 'Gaia Skins',
				'type' : Extensions.TypeOptional,
				'description' : 33730,
				'icon' : 'extensionsgaia.png',
			},
			{
				'id' : Extensions.IdGaiaAeonNox,
				'name' : 'Gaia Aeon Nox',
				'type' : Extensions.TypeOptional,
				'description' : 33731,
				'icon' : 'extensionsgaia.png',
			},
			{
				'id' : Extensions.IdResolveUrl,
				'name' : 'ResolveUrl',
				'type' : Extensions.TypeRequired,
				'description' : 33732,
				'icon' : 'extensionsresolveurl.png',
			},
			{
				'id' : Extensions.IdUrlResolver,
				'name' : 'UrlResolver',
				'type' : Extensions.TypeRequired,
				'description' : 33732,
				'icon' : 'extensionsurlresolver.png',
			},
			{
				'id' : orionoid.Orionoid.Id,
				'name' : orionoid.Orionoid.Name + ' Scrapers',
				'type' : Extensions.TypeRequired,
				'description' : 35401,
				'icon' : 'extensionsorion.png',
			},
			{
				'id' : Extensions.IdOpeScrapers,
				'name' : 'Open Scrapers',
				'type' : Extensions.TypeRecommended,
				'description' : 33963,
				'icon' : 'extensionsopescrapers.png',
			},
			{
				'id' : Extensions.IdLamScrapers,
				'name' : 'Lambda Scrapers',
				'type' : Extensions.TypeRecommended,
				'description' : 33963,
				'icon' : 'extensionslamscrapers.png',
			},
			{
				'id' : Extensions.IdCivScrapers,
				'name' : 'Civitas Scrapers',
				'type' : Extensions.TypeRecommended,
				'description' : 33963,
				'icon' : 'extensionscivscrapers.png',
			},
			{
				'id' : Extensions.IdGloScrapers,
				'name' : 'Global Scrapers',
				'type' : Extensions.TypeRecommended,
				'description' : 33963,
				'icon' : 'extensionsgloscrapers.png',
			},
			{
				'id' : Extensions.IdUniScrapers,
				'name' : 'Universal Scrapers',
				'type' : Extensions.TypeOptional,
				'description' : 33963,
				'icon' : 'extensionsuniscrapers.png',
			},
			{
				'id' : Extensions.IdNanScrapers,
				'name' : 'NaN Scrapers',
				'type' : Extensions.TypeOptional,
				'description' : 33963,
				'icon' : 'extensionsnanscrapers.png',
			},
			{
				'id' : Extensions.IdMetaHandler,
				'name' : 'MetaHandler',
				'type' : Extensions.TypeOptional,
				'description' : 33733,
				'icon' : 'extensionsmetahandler.png',
			},
			{
				'id' : Extensions.IdTrakt,
				'name' : 'Trakt',
				'type' : Extensions.TypeRecommended,
				'description' : 33734,
				'icon' : 'extensionstrakt.png',
			},
			{
				'id' : Extensions.IdElementum,
				'dependencies' : [Extensions.IdElementumRepository],
				'name' : 'Elementum',
				'type' : Extensions.TypeOptional,
				'description' : 33735,
				'icon' : 'extensionselementum.png',
			},
			{
				'id' : Extensions.IdQuasar,
				'dependencies' : [Extensions.IdQuasarRepository],
				'name' : 'Quasar',
				'type' : Extensions.TypeOptional,
				'description' : 33735,
				'icon' : 'extensionsquasar.png',
			},
			{
				'id' : Extensions.IdExtendedInfo,
				'name' : 'ExtendedInfo',
				'type' : Extensions.TypeRequired,
				'description' : 35570,
				'icon' : 'extensionsextendedinfo.png',
			},
			{
				'id' : Extensions.IdYouTube,
				'name' : 'YouTube',
				'type' : Extensions.TypeRequired,
				'description' : 35297,
				'icon' : 'extensionsyoutube.png',
			},
		]

		for i in range(len(result)):
			result[i]['installed'] = self.installed(result[i]['id'])
			if 'dependencies' in result[i]:
				for dependency in result[i]['dependencies']:
					if not self.installed(dependency):
						result[i]['installed'] = False
						break
			result[i]['description'] = interface.Translation.string(result[i]['description'])

		return result

	@classmethod
	def dialog(self, id):
		extensions = self.list()
		for extension in extensions:
			if extension['id'] == id:
				from resources.lib.extensions import interface

				type = ''
				if extension['type'] == Extensions.TypeRequired:
					type = 33723
				elif extension['type'] == Extensions.TypeRecommended:
					type = 33724
				elif extension['type'] == Extensions.TypeOptional:
					type = 33725
				if not type == '':
					type = ' (%s)' % interface.Translation.string(type)

				message = ''
				message += interface.Format.fontBold(extension['name'] + type)
				message += interface.Format.newline() + extension['description']

				action = 33737 if extension['installed'] else 33736

				choice = interface.Dialog.option(title = 33391, message = message, labelConfirm = action, labelDeny = 33486)
				if choice:
					if extension['installed']:
						if extension['type'] == Extensions.TypeRequired:
							interface.Dialog.confirm(title = 33391, message = 33738)
						else:
							self.disable(extension['id'], refresh = True)
					else:
						if 'dependencies' in extension:
							for dependency in extension['dependencies']:
								self.enable(dependency, refresh = True)
						self.enable(extension['id'], refresh = True)

					OpeScrapers.check()
					LamScrapers.check()
					CivScrapers.check()
					GloScrapers.check()
					UniScrapers.check()
					NanScrapers.check()

				return True
		return False

###################################################################
# ELEMENTUM
###################################################################

class Elementum(object):

	Id = Extensions.IdElementum
	Name = 'Elementum'

	@classmethod
	def settings(self):
		Extensions.settings(id = Elementum.Id)

	@classmethod
	def launch(self):
		Extensions.launch(id = Elementum.Id)

	@classmethod
	def install(self, confirm = False):
		Extensions.enable(id = Extensions.IdElementum, refresh = False)
		self.connect(confirm = confirm)
		return True

	@classmethod
	def interface(self):
		System.openLink(self.linkWeb())

	@classmethod
	def link(self, type, parameters = None):
		host = Settings.getString('streaming.torrent.elementum.host')
		port = Settings.getString('streaming.torrent.elementum.port')
		if parameters == None or parameters == [] or parameters == {}: parameters = ''
		else: parameters = '?' + ('&'.join(['%s=%s' % (key, value) for key, value in parameters.iteritems()]))
		return 'http://%s:%s/%s%s' % (host, port, type, parameters)

	@classmethod
	def linkWeb(self, parameters = None):
		return self.link(type = 'web', parameters = parameters)

	@classmethod
	def linkPlay(self, parameters = None):
		return self.link(type = 'playuri', parameters = parameters)

	@classmethod
	def linkAdd(self, parameters = None):
		return self.link(type = 'torrents/add', parameters = parameters)

	@classmethod
	def connected(self):
		return Settings.getBoolean('streaming.torrent.elementum.connected')

	@classmethod
	def connect(self, confirm = False):
		try:
			if not System.installed(Elementum.Id):
				if confirm:
					from resources.lib.extensions import interface
					message = interface.Translation.string(35318) + ' ' + interface.Translation.string(35317)
					if interface.Dialog.option(title = Elementum.Name, message = message):
						self.install(confirm = False)
					else:
						raise Exception()
				else:
					raise Exception()
			Settings.set('streaming.torrent.elementum.connected', True)
			Settings.set('streaming.torrent.elementum.connection', 'Connected')
		except:
			self.disconnect()

	@classmethod
	def disconnect(self):
		Settings.set('streaming.torrent.elementum.connected', False)
		Settings.set('streaming.torrent.elementum.connection', 'Disconnected')

###################################################################
# QUASAR
###################################################################

class Quasar(object):

	Id = Extensions.IdQuasar
	Name = 'Quasar'

	@classmethod
	def settings(self):
		Extensions.settings(id = Quasar.Id)

	@classmethod
	def launch(self):
		Extensions.launch(id = Quasar.Id)

	@classmethod
	def install(self, confirm = False):
		Extensions.enable(id = Extensions.IdQuasar, refresh = False)
		self.connect(confirm = confirm)
		return True

	@classmethod
	def interface(self):
		System.openLink(self.linkWeb())

	@classmethod
	def link(self, type, parameters = None):
		host = Settings.getString('streaming.torrent.quasar.host')
		port = Settings.getString('streaming.torrent.quasar.port')
		if parameters == None or parameters == [] or parameters == {}: parameters = ''
		else: parameters = '?' + ('&'.join(['%s=%s' % (key, value) for key, value in parameters.iteritems()]))
		return 'http://%s:%s/%s%s' % (host, port, type, parameters)

	@classmethod
	def linkWeb(self, parameters = None):
		return self.link(type = 'web', parameters = parameters)

	@classmethod
	def linkPlay(self, parameters = None):
		return self.link(type = 'playuri', parameters = parameters)

	@classmethod
	def linkAdd(self, parameters = None):
		return self.link(type = 'torrents/add', parameters = parameters)

	@classmethod
	def connected(self):
		return Settings.getBoolean('streaming.torrent.quasar.connected')

	@classmethod
	def connect(self, confirm = False):
		try:
			if not System.installed(Quasar.Id):
				if confirm:
					from resources.lib.extensions import interface
					message = interface.Translation.string(33476) + ' ' + interface.Translation.string(33475)
					if interface.Dialog.option(title = Quasar.Name, message = message):
						self.install(confirm = False)
					else:
						raise Exception()
				else:
					raise Exception()
			Settings.set('streaming.torrent.quasar.connected', True)
			Settings.set('streaming.torrent.quasar.connection', 'Connected')
		except:
			self.disconnect()

	@classmethod
	def disconnect(self):
		Settings.set('streaming.torrent.quasar.connected', False)
		Settings.set('streaming.torrent.quasar.connection', 'Disconnected')

###################################################################
# TRAKT
###################################################################

class Trakt(object):

	Id = Extensions.IdTrakt
	Website = 'https://trakt.tv'

	@classmethod
	def settings(self):
		Extensions.settings(id = Trakt.Id)

	@classmethod
	def launch(self):
		Extensions.launch(id = Trakt.Id)

	@classmethod
	def installed(self):
		return Extensions.installed(id = Trakt.Id)

	@classmethod
	def enable(self, refresh = False):
		return Extensions.enable(id = Trakt.Id, refresh = refresh)

	@classmethod
	def disable(self, refresh = False):
		return Extensions.disable(id = Trakt.Id, refresh = refresh)

	@classmethod
	def website(self, open = False):
		if open: System.openLink(Trakt.Website)
		return Trakt.Website

	@classmethod
	def accountEnabled(self):
		return Settings.getBoolean('accounts.informants.trakt.enabled')

###################################################################
# RESOLVEURL
###################################################################

class ResolveUrl(object):

	Id = Extensions.IdResolveUrl

	@classmethod
	def settings(self):
		Extensions.settings(id = ResolveUrl.Id)

	@classmethod
	def installed(self):
		return Extensions.installed(id = ResolveUrl.Id)

	@classmethod
	def enable(self, refresh = False):
		return Extensions.enable(id = ResolveUrl.Id, refresh = refresh)

	@classmethod
	def disable(self, refresh = False):
		return Extensions.disable(id = ResolveUrl.Id, refresh = refresh)


###################################################################
# URLRESOLVER
###################################################################

class UrlResolver(object):

	Id = Extensions.IdUrlResolver

	@classmethod
	def settings(self):
		Extensions.settings(id = UrlResolver.Id)

	@classmethod
	def installed(self):
		return Extensions.installed(id = UrlResolver.Id)

	@classmethod
	def enable(self, refresh = False):
		return Extensions.enable(id = UrlResolver.Id, refresh = refresh)

	@classmethod
	def disable(self, refresh = False):
		return Extensions.disable(id = UrlResolver.Id, refresh = refresh)

###################################################################
# OPESCRAPERS
###################################################################

class OpeScrapers(object):

	Id = Extensions.IdOpeScrapers

	@classmethod
	def settings(self):
		Extensions.settings(id = OpeScrapers.Id)

	@classmethod
	def providers(self, settings = True):
		from resources.lib.providers.external.universal.open import opescrapersx
		opescrapersx.source.instancesSettings()
		if settings: Settings.launch(Settings.CategoryProviders)

	@classmethod
	def check(self):
		Settings.set('providers.external.universal.open.opescrapersx.installed', self.installed())

	@classmethod
	def installed(self):
		return Extensions.installed(id = OpeScrapers.Id)

	@classmethod
	def enable(self, refresh = False):
		result = Extensions.enable(id = OpeScrapers.Id, refresh = refresh)
		self.check()
		return result

	@classmethod
	def disable(self, refresh = False):
		result = Extensions.disable(id = OpeScrapers.Id, refresh = refresh)
		self.check()
		return result

###################################################################
# LAMSCRAPERS
###################################################################

class LamScrapers(object):

	Id = Extensions.IdLamScrapers

	@classmethod
	def settings(self):
		Extensions.settings(id = LamScrapers.Id)

	@classmethod
	def providers(self, settings = True):
		from resources.lib.providers.external.universal.open import lamscrapersx
		lamscrapersx.source.instancesSettings()
		if settings: Settings.launch(Settings.CategoryProviders)

	@classmethod
	def check(self):
		Settings.set('providers.external.universal.open.lamscrapersx.installed', self.installed())

	@classmethod
	def installed(self):
		return Extensions.installed(id = LamScrapers.Id)

	@classmethod
	def enable(self, refresh = False):
		result = Extensions.enable(id = LamScrapers.Id, refresh = refresh)
		self.check()
		return result

	@classmethod
	def disable(self, refresh = False):
		result = Extensions.disable(id = LamScrapers.Id, refresh = refresh)
		self.check()
		return result

###################################################################
# CIVSCRAPERS
###################################################################

class CivScrapers(object):

	Id = Extensions.IdCivScrapers

	@classmethod
	def settings(self):
		Extensions.settings(id = CivScrapers.Id)

	@classmethod
	def providers(self, settings = True):
		from resources.lib.providers.external.universal.open import civscrapersx
		civscrapersx.source.instancesSettings()
		if settings: Settings.launch(Settings.CategoryProviders)

	@classmethod
	def check(self):
		Settings.set('providers.external.universal.open.civscrapersx.installed', self.installed())

	@classmethod
	def installed(self):
		return Extensions.installed(id = CivScrapers.Id)

	@classmethod
	def enable(self, refresh = False):
		result = Extensions.enable(id = CivScrapers.Id, refresh = refresh)
		self.check()
		return result

	@classmethod
	def disable(self, refresh = False):
		result = Extensions.disable(id = CivScrapers.Id, refresh = refresh)
		self.check()
		return result

###################################################################
# GLOSCRAPERS
###################################################################

class GloScrapers(object):

	Id = Extensions.IdGloScrapers

	@classmethod
	def settings(self):
		Extensions.settings(id = GloScrapers.Id)

	@classmethod
	def providers(self, settings = True):
		from resources.lib.providers.external.universal.open import gloscrapersx
		gloscrapersx.source.instancesSettings()
		if settings: Settings.launch(Settings.CategoryProviders)

	@classmethod
	def check(self):
		Settings.set('providers.external.universal.open.gloscrapersx.installed', self.installed())

	@classmethod
	def installed(self):
		return Extensions.installed(id = GloScrapers.Id)

	@classmethod
	def enable(self, refresh = False):
		result = Extensions.enable(id = GloScrapers.Id, refresh = refresh)
		self.check()
		return result

	@classmethod
	def disable(self, refresh = False):
		result = Extensions.disable(id = GloScrapers.Id, refresh = refresh)
		self.check()
		return result

###################################################################
# UNISCRAPERS
###################################################################

class UniScrapers(object):

	Id = Extensions.IdUniScrapers

	@classmethod
	def settings(self):
		Extensions.settings(id = UniScrapers.Id)

	@classmethod
	def providers(self, settings = True):
		from resources.lib.providers.external.universal.open import uniscrapersx
		uniscrapersx.source.instancesSettings()
		if settings: Settings.launch(Settings.CategoryProviders)

	@classmethod
	def check(self):
		Settings.set('providers.external.universal.open.uniscrapersx.installed', self.installed())

	@classmethod
	def installed(self):
		return Extensions.installed(id = UniScrapers.Id)

	@classmethod
	def enable(self, refresh = False):
		result = Extensions.enable(id = UniScrapers.Id, refresh = refresh)
		self.check()
		return result

	@classmethod
	def disable(self, refresh = False):
		result = Extensions.disable(id = UniScrapers.Id, refresh = refresh)
		self.check()
		return result

###################################################################
# NANSCRAPERS
###################################################################

class NanScrapers(object):

	Id = Extensions.IdNanScrapers

	@classmethod
	def settings(self):
		Extensions.settings(id = NanScrapers.Id)

	@classmethod
	def providers(self, settings = True):
		from resources.lib.providers.external.universal.open import nanscrapersx
		nanscrapersx.source.instancesSettings()
		if settings: Settings.launch(Settings.CategoryProviders)

	@classmethod
	def check(self):
		Settings.set('providers.external.universal.open.nanscrapersx.installed', self.installed())

	@classmethod
	def installed(self):
		return Extensions.installed(id = NanScrapers.Id)

	@classmethod
	def enable(self, refresh = False):
		result = Extensions.enable(id = NanScrapers.Id, refresh = refresh)
		self.check()
		return result

	@classmethod
	def disable(self, refresh = False):
		result = Extensions.disable(id = NanScrapers.Id, refresh = refresh)
		self.check()
		return result

###################################################################
# YOUTUBE
###################################################################

class YouTube(object):

	Id = Extensions.IdYouTube
	Website = 'https://youtube.com'

	@classmethod
	def settings(self):
		Extensions.settings(id = YouTube.Id)

	@classmethod
	def launch(self):
		Extensions.launch(id = YouTube.Id)

	@classmethod
	def installed(self):
		return Extensions.installed(id = YouTube.Id)

	@classmethod
	def enable(self, refresh = False):
		return Extensions.enable(id = YouTube.Id, refresh = refresh)

	@classmethod
	def disable(self, refresh = False):
		return Extensions.disable(id = YouTube.Id, refresh = refresh)

	@classmethod
	def website(self, open = False):
		if open: System.openLink(YouTube.Website)
		return YouTube.Website

###################################################################
# METAHANDLER
###################################################################

class MetaHandler(object):

	Id = Extensions.IdMetaHandler

	@classmethod
	def settings(self):
		Extensions.settings(id = MetaHandler.Id)

	@classmethod
	def installed(self):
		return Extensions.installed(id = MetaHandler.Id)

	@classmethod
	def enable(self, refresh = False):
		return Extensions.enable(id = MetaHandler.Id, refresh = refresh)

	@classmethod
	def disable(self, refresh = False):
		return Extensions.disable(id = MetaHandler.Id, refresh = refresh)

###################################################################
# YOUTUBE
###################################################################

class ExtendedInfo(object):

	Id = Extensions.IdExtendedInfo

	@classmethod
	def settings(self):
		Extensions.settings(id = ExtendedInfo.Id)

	@classmethod
	def launch(self):
		Extensions.launch(id = ExtendedInfo.Id)

	@classmethod
	def installed(self):
		return Extensions.installed(id = ExtendedInfo.Id)

	@classmethod
	def enable(self, refresh = False):
		return Extensions.enable(id = ExtendedInfo.Id, refresh = refresh)

	@classmethod
	def disable(self, refresh = False):
		return Extensions.disable(id = ExtendedInfo.Id, refresh = refresh)

###################################################################
# INFORMATION
###################################################################

class Information(object):

	Wait = 300 # 30 seconds with an interval of 0.1.
	Interval = 0.1

	@classmethod
	def _execute(self, parameters = None):
		System.executeScript('script.extendedinfo', parameters = parameters)

	@classmethod
	def show(self, imdb = None, tvdb = None, title = None, season = None, episode = None, wait = True):
		from resources.lib.extensions import interface
		from resources.lib.extensions import window

		if wait: interface.Loader.show()

		if not episode == None: parameters = {'info' : 'extendedepisodeinfo', 'tvshow' : title, 'season' : season, 'episode' : episode}
		elif not season == None: parameters = {'info' : 'seasoninfo', 'tvshow' : title, 'season' : season}
		elif not tvdb == None: parameters = {'info' : 'extendedtvinfo', 'tvdb_id' : tvdb, 'imdb_id' : imdb if imdb else ''}
		elif not imdb == None: command = parameters = {'info' : 'extendedinfo', 'imdb_id' : imdb}
		else: command = command = parameters = {'info' : 'openinfodialog'} # Uses the current selected item in the Kodi control list. If however the selection changes (eg through mouse movement) before the dialog opens, that info (the wrong one) will show.
		self._execute(parameters = parameters)

		if wait:
			for i in range(Information.Wait):
				if Converter.boolean(window.Window.propertyGlobal('infodialogs.active')) and window.Window.visibleCustom(): break
				Time.sleep(Information.Interval)
			interface.Loader.hide()

	@classmethod
	def trailer(self, imdb, wait = True): # Only works for movies.
		from resources.lib.extensions import interface
		if wait: interface.Loader.show()
		self._execute(parameters = {'info' : 'playtrailer', 'imdb_id' : imdb})
		if wait:
			player = xbmc.Player()
			for i in range(Information.Wait):
				if player.isPlaying(): break
				Time.sleep(Information.Interval)
			interface.Loader.hide()

###################################################################
# BACKUP
###################################################################

class Backup(object):

	Extension = 'zip'
	Directory = 'Backups'

	TypeEverything = 'everything'
	TypeSettings = 'settings'
	TypeDatabases = 'databases'

	ResultFailure = 'failure'
	ResultPartial = 'partial'
	ResultSuccess = 'success'

	@classmethod
	def _path(self, clear = False):
		return System.temporary(directory = 'backup', gaia = True, make = True, clear = clear)

	@classmethod
	def _name(self):
		from resources.lib.extensions import interface
		from resources.lib.extensions import convert
		date = convert.ConverterTime(Time.timestamp(), convert.ConverterTime.FormatTimestamp).string(convert.ConverterTime.FormatDateTime)
		date = date.replace(':', '.') # Windows does not support colons in file names.
		return System.name() + ' ' + interface.Translation.string(33773) + ' '+ date + '%s.' + Backup.Extension

	@classmethod
	def _import(self, path):
		try:
			directory = self._path(clear = True)
			directoryData = System.profile()

			import zipfile
			file = zipfile.ZipFile(path, 'r')
			file.extractall(directory)
			file.close()

			directories, files = File.listDirectory(directory)
			counter = 0
			for file in files:
				fileFrom = File.joinPath(directory, file)
				fileTo = File.joinPath(directoryData, file)
				if File.move(fileFrom, fileTo, replace = True):
					counter += 1

			File.deleteDirectory(path = directory, force = True)

			Settings.cacheClear() # Clear the data from the old file.

			if counter == 0: return Backup.ResultFailure
			elif counter == len(files): return Backup.ResultSuccess
			else: return Backup.ResultPartial
		except:
			return Backup.ResultFailure

	@classmethod
	def _export(self, type, path, automatic = False):
		try:
			File.makeDirectory(path)
			name = self._name()
			path = File.joinPath(path, name)
			if automatic:
				path = path % ''
			else:
				counter = 0
				suffix = ''
				while File.exists(path % suffix):
					counter += 1
					suffix = ' [%d]' % counter
				path = path % suffix

			import zipfile
			file = zipfile.ZipFile(path, 'w')

			content = []
			directory = self._path(clear = True)
			directoryData = System.profile()
			directories, files = File.listDirectory(directoryData)

			from resources.lib.extensions import database
			settingsDatabase = (Settings.Database + database.Database.Extension).lower()

			if type == Backup.TypeEverything or type == Backup.TypeSettings:
				settings = ['settings.xml', settingsDatabase]
				for i in range(len(files)):
					if files[i].lower() in settings:
						content.append(files[i])

			if type == Backup.TypeEverything or type == Backup.TypeDatabases:
				extension = '.db'
				for i in range(len(files)):
					if files[i].lower().endswith(extension) and not files[i].lower() == settingsDatabase:
						content.append(files[i])

			tos = [File.joinPath(directory, i) for i in content]
			froms = [File.joinPath(directoryData, i) for i in content]

			for i in range(len(content)):
				try:
					File.copy(froms[i], tos[i], overwrite = True)
					file.write(tos[i], content[i])
				except: pass

			file.close()
			File.deleteDirectory(path = directory, force = True)
			return Backup.ResultSuccess
		except:
			Logger.error()
			return Backup.ResultFailure

	@classmethod
	def automaticPath(self):
		return File.joinPath(System.profile(), Backup.Directory)

	@classmethod
	def automaticClear(self):
		return File.deleteDirectory(self.automaticPath())

	@classmethod
	def automaticClean(self):
		limit = Settings.getInteger('general.settings.backup.limit', cached = False)
		path = self.automaticPath()
		directories, files = File.listDirectory(path)
		count = len(files)
		if count >= limit:
			files.sort(reverse = False)
			i = 0
			while count >= limit:
				File.delete(File.joinPath(path, files[i]), force = True)
				i += 1
				count -= 1

	@classmethod
	def automaticImport(self, force = False):
		try:
			# The problem here is that if the settings are corrupt, the user's preferences, set previously, cannot be determined.
			# Hence, always load the last backup if settings are corrupt. Then check if automatic/selection was enabled.
			# If automatic, don't do anything further.
			# If selection, ask the user which backup to load.

			from resources.lib.extensions import interface
			if force or (Settings.getString('general.settings.backup.time', cached = False) == '' and File.existsDirectory(self.automaticPath())):
				directories, files = File.listDirectory(self.automaticPath())
				Settings.set('general.settings.backup.time', Time.timestamp(), cached = True)

				if len(files) > 0:
					files.sort(reverse = True)
					self._import(path = File.joinPath(self.automaticPath(), files[0]))
					Settings.set('general.settings.backup.time', Time.timestamp(), cached = True)

					if not Settings.getBoolean('general.settings.backup.enabled', cached = False):
						return False

					restore = Settings.getInteger('general.settings.backup.restore', cached = False)
					choice = -1
					if not force and restore == 0:
						choice = 0
					elif force or (restore == 1 and interface.Dialog.option(title = 33773, message = 35210)):
						items = [interface.Format.fontBold(re.search('\\d*-\\d*-\\d*\\s*\\d*\\.\\d*\\.\\d*', file).group(0).replace('.', ':')) for file in files]
						choice = interface.Dialog.options(title = 33773, items = items)

					if choice >= 0:
						result = self._import(path = File.joinPath(self.automaticPath(), files[choice]))
						Settings.set('general.settings.backup.time', Time.timestamp(), cached = True)
						interface.Dialog.notification(title = 33773, message = 35211, icon = interface.Dialog.IconSuccess)
						return result == Backup.ResultSuccess

					return False

			# Not returned from the inner if.
			if force: interface.Dialog.notification(title = 33773, message = 35247, icon = interface.Dialog.IconError)
			return False
		except:
			Logger.error()
		return False

	@classmethod
	def automaticExport(self, force = False):
		try:
			if Settings.getBoolean('general.settings.backup.enabled', cached = False) or force:
				self.automaticClean()
				Settings.set('general.settings.backup.time', Time.timestamp(), cached = True)
				return self._export(type = Backup.TypeSettings, path = self.automaticPath(), automatic = True) == Backup.ResultSuccess
		except:
			Logger.error()
		return False

	@classmethod
	def automatic(self):
		from resources.lib.extensions import interface

		interface.Dialog.confirm(title = 33773, message = 35209)

		items = [
			interface.Format.bold(interface.Translation.string(33774) + ':') + ' ' + interface.Translation.string(35214),
			interface.Format.bold(interface.Translation.string(35212) + ':') + ' ' + interface.Translation.string(35215),
			interface.Format.bold(interface.Translation.string(33011) + ':') + ' ' + interface.Translation.string(35216),
		]

		choice = interface.Dialog.options(title = 33773, items = items)
		if choice == 0:
			if interface.Dialog.option(title = 33773, message = 35217):
				self.automaticImport(force = True)
		elif choice == 1:
			if self.automaticExport(force = True):
				interface.Dialog.notification(title = 33773, message = 35218, icon = interface.Dialog.IconSuccess)
			else:
				interface.Dialog.notification(title = 33773, message = 35219, icon = interface.Dialog.IconError)
		elif choice == 2:
			Settings.launch(Settings.CategoryGeneral)

	@classmethod
	def manualImport(self):
		from resources.lib.extensions import interface

		choice = interface.Dialog.option(title = 33773, message = 33782)
		if not choice: return

		path = interface.Dialog.browse(title = 33773, type = interface.Dialog.BrowseFile, mask = Backup.Extension)
		result = self._import(path = path)

		if result == Backup.ResultSuccess:
			interface.Dialog.notification(title = 33773, message = 33785, icon = interface.Dialog.IconSuccess)
		elif result == Backup.ResultPartial:
			interface.Dialog.confirm(title = 33773, message = interface.Translation.string(33783) % System.id())
		else:
			interface.Dialog.confirm(title = 33773, message = 33778)

	@classmethod
	def manualExport(self):
		from resources.lib.extensions import interface

		choice = interface.Dialog.option(title = 33773, message = 35213)
		if not choice: return

		types = [
			Backup.TypeEverything,
			Backup.TypeSettings,
			Backup.TypeDatabases,
		]
		items = [
			interface.Format.bold(interface.Translation.string(33776) + ':') + ' ' + interface.Translation.string(33779),
			interface.Format.bold(interface.Translation.string(33011) + ':') + ' ' + interface.Translation.string(33780),
			interface.Format.bold(interface.Translation.string(33775) + ':') + ' ' + interface.Translation.string(33781),
		]

		choice = interface.Dialog.options(title = 33773, items = items)
		if choice >= 0:
			path = interface.Dialog.browse(title = 33773, type = interface.Dialog.BrowseDirectoryWrite)
			result = self._export(type = types[choice], path = path)

			if result == Backup.ResultSuccess:
				interface.Dialog.notification(title = 33773, message = 33784, icon = interface.Dialog.IconSuccess)
			else:
				interface.Dialog.confirm(title = 33773, message = 33777)

	@classmethod
	def directImport(self, path):
		from resources.lib.extensions import interface
		self._import(path)
		interface.Dialog.notification(title = 33773, message = 35326, icon = interface.Dialog.IconSuccess)

	'''
	msgctxt "#33229"
	msgid "This option will replace the internal settings structure of Gaia with a structure from a remote source. You can therefore use other third-party developers' settings instead of the one provided by Gaia."

	msgctxt "#33230"
	msgid "Only continue if you know what you are doing and if you have informed yourself on Reddit or similar site about this feature."

	msgctxt "#35538"
	msgid "Settings Replacement Successful - Restart Kodi"

	msgctxt "#35539"
	msgid "Settings Replacement Failure"

	@classmethod
	def replace(self):
		from resources.lib.extensions import interface
		from resources.lib.extensions import network
		if interface.Dialog.option(title = 33011, message = 33229, labelConfirm = 33821, labelDeny = 33743):
			if interface.Dialog.option(title = 33011, message = 33230, labelConfirm = 33821, labelDeny = 33743):
				link = interface.Dialog.input(title = 35540)
				interface.Loader.show()
				success = network.Networker(link).download(path = Settings.pathAddon())
				interface.Loader.hide()
				if success: interface.Dialog.notification(title = 33011, message = 35538, icon = interface.Dialog.IconSuccess)
				else: interface.Dialog.notification(title = 33011, message = 35539, icon = interface.Dialog.IconError)
				return success
		return False'''

	@classmethod
	def reaper(self, confirm = True):
		from resources.lib.extensions import interface
		interface.Dialog.confirm(title = 35321, message = 35323)
		if not confirm or interface.Dialog.option(title = 35321, message = 35324):
			choice = interface.Dialog.options(title = 35321, items = [interface.Format.fontBold(35615), interface.Format.fontBold(35616)])
			if choice < 0: return False
			settings = 'reaper.' + ('slow' if choice == 0 else 'fast') + '.' + ('18' if System.versionKodiNew() else '17') + '.zip'
			Backup.directImport(File.joinPath(System.path(id = System.GaiaResources), 'resources', 'settings', settings))
			return True
		else:
			return False

###################################################################
# DONATIONS
###################################################################

class Donations(object):

	# Type
	TypeNone = None
	TypePaypal = 'paypal'
	TypeBitcoin = 'bitcoin'
	TypeBitcoinCash = 'bitcoincash'
	TypeDash = 'dash'
	TypeEthereum = 'ethereum'
	TypeLitecoin = 'litecoin'
	TypeRipple = 'ripple'
	TypeZcash = 'zcash'
	TypeMonero = 'monero'

	# Popup
	PopupThreshold = 50

	@classmethod
	def donor(self):
		return System.developers() or Settings.getString('general.access.code') == Converter.base64From('ZG9ub3I=')

	@classmethod
	def coinbase(self, openLink = True):
		link = Settings.getString('link.coinbase')
		if openLink: System.openLink(link)
		return link

	@classmethod
	def exodus(self, openLink = True):
		link = Settings.getString('link.exodus')
		if openLink: System.openLink(link)
		return link

	@classmethod
	def other(self, openLink = True):
		link = Settings.getString('link.donation')
		if openLink: System.openLink(link)
		from resources.lib.extensions import interface
		return interface.Splash.popupDonations()
		return link

	@classmethod
	def show(self, type = None):
		if type == None:
			System.window(action = 'donationsNavigator')
		else:
			from resources.lib.extensions import interface
			from resources.lib.extensions import api
			data = api.Api.donations(type)
			return interface.Splash.popupDonations(donation = data)

	@classmethod
	def popup(self, wait = False):
		thread = threading.Thread(target = self._popup)
		thread.start()
		if wait: thread.join()

	@classmethod
	def _popup(self):
		from resources.lib.extensions import interface
		if not self.donor():
			counter = Settings.getInteger('internal.donation')
			counter += 1
			if counter >= Donations.PopupThreshold:
				Settings.set('internal.donation', 0)
				if interface.Dialog.option(title = 33505, message = 35014, labelConfirm = 33505, labelDeny = 35015):
					self.show()
					interface.Loader.hide()
					return True
			else:
				Settings.set('internal.donation', counter)
		interface.Loader.hide()
		return False

	@classmethod
	def types(self):
		return [
			{
				'identifier' : Donations.TypePaypal,
				'name' : 'PayPal',
				'color' : '029BDE',
				'icon' : 'donationspaypal.png',
			},
			{
				'identifier' : Donations.TypeBitcoin,
				'name' : 'Bitcoin',
				'color' : 'F7931A',
				'icon' : 'donationsbitcoin.png',
			},
			{
				'identifier' : Donations.TypeBitcoinCash,
				'name' : 'Bitcoin Cash',
				'color' : '2DB300',
				'icon' : 'donationsbitcoincash.png',
			},
			{
				'identifier' : Donations.TypeEthereum,
				'name' : 'Ethereum',
				'color' : '62688F',
				'icon' : 'donationsethereum.png',
			},
			{
				'identifier' : Donations.TypeLitecoin,
				'name' : 'Litecoin',
				'color' : 'A7A7A7',
				'icon' : 'donationslitecoin.png',
			},
			{
				'identifier' : Donations.TypeRipple,
				'name' : 'Ripple',
				'color' : '00A3DB',
				'icon' : 'donationsripple.png',
			},
			{
				'identifier' : Donations.TypeMonero,
				'name' : 'Monero',
				'color' : 'FF6600',
				'icon' : 'donationsmonero.png',
			},
			{
				'identifier' : Donations.TypeZcash,
				'name' : 'Zcash',
				'color' : 'F5BA0D',
				'icon' : 'donationszcash.png',
			},
			{
				'identifier' : Donations.TypeDash,
				'name' : 'Dash',
				'color' : '2588DC',
				'icon' : 'donationsdash.png',
			},
		]

###################################################################
# PLAYLIST
###################################################################

class Playlist(object):

	Id = xbmc.PLAYLIST_VIDEO

	@classmethod
	def playlist(self):
		return xbmc.PlayList(Playlist.Id)

	@classmethod
	def show(self):
		from resources.lib.extensions import window
		window.Window.show(window.Window.IdWindowPlaylist)

	@classmethod
	def clear(self, notification = True):
		self.playlist().clear()
		if notification:
			from resources.lib.extensions import interface
			interface.Dialog.notification(title = 35515, message = 35521, icon = interface.Dialog.IconSuccess)

	@classmethod
	def items(self):
		try: return [i['label'] for i in System.executeJson(method = 'Playlist.GetItems', parameters = {'playlistid' : Playlist.Id})['result']['items']]
		except: return []

	@classmethod
	def empty(self):
		return len(self.items()) == 0

	@classmethod
	def contains(self, label):
		return label in self.items()

	@classmethod
	def position(self, label):
		try: return self.items().index(label)
		except: return -1

	@classmethod
	def add(self, link = None, label = None, metadata = None, art = None, context = None, notification = True):
		if link == None:
			System.execute('Action(Queue)')
		else:
			if isinstance(metadata, basestring): metadata = Converter.jsonFrom(metadata)
			if isinstance(art, basestring): art = Converter.jsonFrom(art)
			if isinstance(context, basestring): context = Converter.jsonFrom(context)

			item = xbmcgui.ListItem(label = label)
			item.setArt(art)
			item.setInfo(type = 'Video', infoLabels = Media.metadataClean(metadata))

			# Use the global context menu instead.
			'''if not context == None:
				from resources.lib.extensions import interface
				menu = interface.Context()
				menu.jsonFrom(context)
				item.addContextMenuItems([menu.menu()])'''

			self.playlist().add(url = link, listitem = item)
			if notification:
				from resources.lib.extensions import interface
				interface.Dialog.notification(title = 35515, message = 35519, icon = interface.Dialog.IconSuccess)

	@classmethod
	def remove(self, label, notification = True):
		#self.playlist().remove(link) # This doesn't seem to work all the time.
		position = self.position(label = label)
		if position >= 0:
			System.executeJson(method = 'Playlist.Remove', parameters = {'playlistid' : Playlist.Id, 'position' : position})
			if notification:
				from resources.lib.extensions import interface
				interface.Dialog.notification(title = 35515, message = 35520, icon = interface.Dialog.IconSuccess)

###################################################################
# STATISTICS
###################################################################

class Statistics(object):

	@classmethod
	def enabled(self):
		# Do not share if developer is enabled and sharing is switched off.
		return not System.developers() and self.sharing()

	@classmethod
	def sharing(self):
		return Settings.getBoolean('general.statistics.sharing')

	@classmethod
	def share(self, wait = False):
		thread = threading.Thread(target = self._share)
		thread.start()
		if wait: thread.join()

	@classmethod
	def _share(self):
		try:
			if not self.enabled(): return

			from resources.lib import debrid
			from resources.lib.extensions import api
			from resources.lib.extensions import network
			from resources.lib.extensions import orionoid

			orion = orionoid.Orionoid()
			data = {
				'version' : System.version(),
				'orion' : orion.accountValid(),

				'system' : System.informationSystem(),
				'python' : System.informationPython(),
				'kodi' : System.informationKodi(),

				'hardware' :
				{
					'processors' : Hardware.processors(),
					'memory' : Hardware.memory(),
				},

				'premium' :
				{
					'premiumize' : debrid.premiumize.Core().accountValid(),
					'offcloud' : debrid.offcloud.Core().accountValid(),
					'realdebrid' : debrid.realdebrid.Core().accountValid(),
					'easynews' : debrid.easynews.Core().accountValid(),
					'alldebrid' : debrid.alldebrid.Core().accountValid(),
					'rapidpremium' : debrid.rapidpremium.Core().accountValid(),
				},
			}

			if self.sharing():
				information = network.Networker.information(obfuscate = True)
				information = information['global']

				# Strip important data to make it anonymous.
				information['connection']['address'] = None
				information['connection']['name'] = None
				information['location']['coordinates']['latitude'] = None
				information['location']['coordinates']['longitude'] = None

				data.update(information)

			api.Api.deviceUpdate(data = data)
		except:
			Logger.error()

###################################################################
# BINGE
###################################################################

class Binge(object):

	ModeNone = 0
	ModeFirst = 1
	ModeContinue = 2
	ModeBackground = 3

	DialogNone = 0
	DialogFull = 1
	DialogOverlay = 2
	DialogUpNext = 3

	ActionContinue = 0
	ActionCancel = 1

	ActionInterrupt = 0
	ActionFinish = 1

	@classmethod
	def enabled(self):
		return Settings.getBoolean('playback.binge.enabled')

	@classmethod
	def dialog(self):
		return Settings.getInteger('playback.binge.dialog')

	@classmethod
	def dialogNone(self):
		return self.dialog() == Binge.DialogNone

	@classmethod
	def dialogFull(self):
		return self.dialog() == Binge.DialogFull

	@classmethod
	def dialogOverlay(self):
		return self.dialog() == Binge.DialogOverlay

	@classmethod
	def dialogUpNext(self):
		return self.dialog() == Binge.DialogUpNext

	@classmethod
	def delay(self):
		return Settings.getInteger('playback.binge.delay')

	@classmethod
	def suppress(self):
		return Settings.getBoolean('playback.binge.suppress')

	@classmethod
	def actionNone(self):
		return Settings.getInteger('playback.binge.action.none')

	@classmethod
	def actionContinue(self):
		return Settings.getInteger('playback.binge.action.continue')

	@classmethod
	def actionCancel(self):
		return Settings.getInteger('playback.binge.action.cancel')

###################################################################
# ANNOUNCEMENT
###################################################################

class Announcements(object):

	@classmethod
	def show(self, force = False, wait = False, sleep = False):
		thread = threading.Thread(target = self._show, args = (force, sleep))
		thread.start()
		if wait: thread.join()

	@classmethod
	def _show(self, force = False, sleep = False):
		from resources.lib.extensions import api
		from resources.lib.extensions import interface
		if sleep: Time.sleep(2) # Wait a bit so that everything has been loaded.
		try: last = int(Settings.getString('internal.announcements'))
		except: last = None
		if force:
			interface.Loader.show()
			result = api.Api.announcements(version = System.version())
		else:
			result = api.Api.announcements(last = last, version = System.version())
		try:
			time = result['time']
			mode = result['mode']
			text = result['format']
			if not force: Settings.set('internal.announcements', str(time))
			if mode == 'dialog': interface.Dialog.confirm(title = 33962, message = text)
			elif mode == 'splash': interface.Splash.popupMessage(message = text)
			elif mode == 'page': interface.Dialog.page(title = 33962, message = text)
		except: pass
		if force: interface.Loader.hide()

###################################################################
# PROMOTIONS
###################################################################

class Promotions(object):

	Cache = None
	OrionAnonymous = 'orionanonymous'

	@classmethod
	def update(self, wait = False, refresh = True):
		thread = threading.Thread(target = self._update, args = (refresh,))
		thread.start()

	@classmethod
	def _update(self, refresh = True):
		try:
			from resources.lib.extensions import api
			self._cache()
			enabled = self.enabled()
			result = []
			promotions = api.Api.promotions()
			for i in promotions:
				i['viewed'] = False
				for j in Promotions.Cache:
					if i['id'] == j['id']:
						i['viewed'] = j['viewed']
						break
				result.append(i)
			self._cacheUpdate(result)
			if refresh and self.enabled() and not enabled:
				from resources.lib.extensions import interface
				interface.Directory.refresh(clear = True)
		except: pass

	@classmethod
	def _cache(self):
		if Promotions.Cache == None: Promotions.Cache = Settings.getList('internal.promotions')
		return Promotions.Cache

	@classmethod
	def _cacheUpdate(self, data = None):
		if not data == None: Promotions.Cache = data
		Settings.set('internal.promotions', Promotions.Cache)

	@classmethod
	def _fixed(self):
		try:
			from resources.lib.extensions import interface
			from resources.lib.extensions import orionoid
			orion = orionoid.Orionoid()
			if orion.accountAnonymousEnabled(): orionoid.Orionoid().accountAnonymous()
			return [{
				'id' : Promotions.OrionAnonymous,
				'viewed' : not orion.accountAnonymousEnabled(),
				'provider' : 'Orion',
				'start' : Time.timestamp(),
				'expiration' : None,
				'title' : interface.Translation.string(35428),
			}]
		except:
			Logger.error()

	@classmethod
	def enabled(self):
		try:
			from resources.lib.extensions import orionoid
			if not Settings.getBoolean('interface.menu.promotions'): return False
			elif orionoid.Orionoid().accountAnonymousEnabled(): return True
			current = Time.timestamp()
			for i in self._cache():
				if not i['viewed'] and (i['expiration'] == None or i['expiration'] > current):
					return True
		except:
			Logger.error()
		return False

	@classmethod
	def navigator(self, force = False):
		from resources.lib.extensions import interface

		if force:
			interface.Loader.show()
			self.update(wait = True, refresh = False)
			interface.Loader.hide()
		elif not Settings.getBoolean('internal.promotions.initialized'):
			Settings.set('internal.promotions.initialized', True)
			interface.Dialog.confirm(title = 35442, message = 35445)

		items = []
		promotions = [i['provider'] for i in self._fixed()]
		lower = []
		for i in self._cache():
			if not i['provider'] in promotions:
				promotions.append(i['provider'])
				lower.append(i['provider'].lower())

		if len(promotions) == 0:
			interface.Dialog.notification(title = 35443, message = 35444, icon = interface.Dialog.IconNativeInformation)
		else:
			# Use a specific order.
			for i in ['orion', 'premiumize', 'offcloud', 'realdebrid']:
				try:
					i = lower.index(i)
					items.append(promotions[i])
					del promotions[i]
					del lower[i]
				except: pass
			items.extend(promotions)

			directory = interface.Directory()
			for i in items:
				directory.add(label = i, action = 'promotionsSelect', parameters = {'provider' : i}, icon = '%s.png' % (i.lower() if interface.Icon.exists(i.lower()) else 'promotion'), iconDefault = 'DefaultAddonProgram.png')
			directory.finish()

	@classmethod
	def select(self, provider):
		import copy
		from resources.lib.extensions import interface
		from resources.lib.extensions import convert

		current = Time.timestamp()
		promotions = []
		items = copy.deepcopy(self._cache()) # Deep copy becuase we append Orion.

		if provider.lower() == 'orion':
			items.extend(self._fixed())

		for i in items:
			if i['provider'].lower() == provider.lower():
				if i['expiration']:
					time = i['expiration'] - current
					if time < 0: continue
					time = convert.ConverterDuration(value = time, unit = convert.ConverterDuration.UnitSecond).string(format = convert.ConverterDuration.FormatWordMinimal).title()
					time += ' ' + interface.Translation.string(35449)
				else:
					time = interface.Translation.string(35446)
				status = interface.Translation.string(35448 if i['viewed'] else 35447)
				status = '[%s]' % status
				status = interface.Format.font(status, bold = True, color = interface.Format.colorPoor() if i['viewed'] else interface.Format.colorExcellent())
				promotions.append({
					'id' : i['id'],
					'title' : '%s %s: %s' % (status, i['title'], time),
					'time' : i['start'],
				})
		promotions = sorted(promotions, key = lambda i : i['time'], reverse = True)

		choice = interface.Dialog.options(title = provider + ' ' + interface.Translation.string(provider), items = [i['title'] for i in promotions])
		if choice >= 0:
			choice = promotions[choice]['id']
			if choice == Promotions.OrionAnonymous:
				try: orionoid.Orionoid().accountAnonymous()
				except: Logger.error()
			else:
				for i in range(len(Promotions.Cache)):
					if Promotions.Cache[i]['id'] == choice:
						Promotions.Cache[i]['viewed'] = True
						self._cacheUpdate()
						message = interface.Format.fontBold(Promotions.Cache[i]['title']) + interface.Format.newline()
						if Promotions.Cache[i]['expiration']: message += interface.Format.newline() + interface.Format.fontBold('Expiration: ') + convert.ConverterTime(Promotions.Cache[i]['expiration']).string(format = convert.ConverterTime.FormatDateTime)
						if Promotions.Cache[i]['link']: message += interface.Format.newline() + interface.Format.fontBold('Link: ') + interface.Format.fontItalic(Promotions.Cache[i]['link'])
						if Promotions.Cache[i]['expiration'] or Promotions.Cache[i]['link']: message += interface.Format.newline()
						message += interface.Format.newline() + Promotions.Cache[i]['description'] + interface.Format.newline()
						interface.Dialog.page(title = Promotions.Cache[i]['provider'] +' ' + interface.Translation.string(35442), message = message)
						break

###################################################################
# RATER
###################################################################

class Rater(object):

	ModeRating = 'rating'
	ModeVotes = 'votes'

	@classmethod
	def _extract(self, mode, item, own, order):
		if own: order.insert(0, 'own')
		for i in order:
			i = mode + i
			if i in item and item[i] and not item[i] == '0':
				if mode == Rater.ModeRating:
					try: return float(item[i])
					except: continue
				else:
					try: return int(item[i])
					except: continue
		return item[mode] if mode in item else None

	@classmethod
	def _average(self, item, own):
		ratingGlobal = []
		votesGlobal = []
		for i in ['imdb', 'tmdb', 'tvdb', 'trakt', 'tvmaze']:
			key = Rater.ModeRating + i
			if key in item and item[key] and not item[key] == '0':
				try:
					ratingGlobal.append(float(item[key]))
					found = False
					key = Rater.ModeVotes + i
					if key in item and item[key] and not item[key] == '0':
						try:
							votesGlobal.append(int(re.sub(',', '', item[key])))
							found = True
						except: pass
					if not found: votesGlobal.append(1)
				except: pass

		if len(ratingGlobal) == 0:
			try:
				ratingGlobal.append(float(item[Rater.ModeRating]))
				try: votesGlobal.append(int(re.sub(',', '', item[Rater.ModeVotes])))
				except: votesGlobal.append(1)
			except: pass

		rating = 0
		total = sum(votesGlobal)
		if own and 'ratingown' in item and item['ratingown'] and not item['ratingown'] == '0':
			rating = item['ratingown']
		elif total > 0:
			for i in range(len(ratingGlobal)):
				rating += (ratingGlobal[i] / total) * votesGlobal[i]

		return rating, total

	@classmethod
	def extract(self, item, mode = None):
		rating = None
		votes = None

		if 'tvshowtitle' in item or 'season' in item or 'episode' in item:
			type = Settings.getInteger('interface.ratings.shows.type')
			own = Settings.getBoolean('interface.ratings.shows.own')

			if type == 0:
				rating, votes = self._average(item = item, own = own)
				if mode == Rater.ModeRating: return rating
				if mode == Rater.ModeVotes: return votes
			else:
				if mode is None or mode == Rater.ModeRating:
					if type == 1: rating = self._extract(mode = Rater.ModeRating, item = item, own = own, order = ['imdb', 'tvdb', 'trakt', 'tvmaze'])
					elif type == 2: rating = self._extract(mode = Rater.ModeRating, item = item, own = own, order = ['trakt', 'imdb', 'tvdb', 'tvmaze'])
					elif type == 3: rating = self._extract(mode = Rater.ModeRating, item = item, own = own, order = ['tvdb', 'imdb', 'trakt', 'tvmaze'])
					elif type == 4: rating = self._extract(mode = Rater.ModeRating, item = item, own = own, order = ['tvmaze', 'imdb', 'tvdb', 'trakt'])
					if mode == Rater.ModeRating: return rating

				if mode is None or mode == Rater.ModeVotes:
					if type == 1: votes = self._extract(mode = Rater.ModeVotes, item = item, own = own, order = ['imdb', 'tvdb', 'trakt', 'tvmaze'])
					elif type == 2: votes = self._extract(mode = Rater.ModeVotes, item = item, own = own, order = ['trakt', 'imdb', 'tvdb', 'tvmaze'])
					elif type == 3: votes = self._extract(mode = Rater.ModeVotes, item = item, own = own, order = ['tvdb', 'imdb', 'trakt', 'tvmaze'])
					elif type == 4: votes = self._extract(mode = Rater.ModeVotes, item = item, own = own, order = ['tvmaze', 'imdb', 'tvdb', 'trakt'])
					if mode == Rater.ModeVotes: return votes
		else:
			type = Settings.getInteger('interface.ratings.movies.type')
			own = Settings.getBoolean('interface.ratings.movies.own')

			if type == 0:
				rating, votes = self._average(item = item, own = own)
				if mode == Rater.ModeRating: return rating
				if mode == Rater.ModeVotes: return votes
			else:
				if mode is None or mode == Rater.ModeRating:
					if type == 1: rating = self._extract(mode = Rater.ModeRating, item = item, own = own, order = ['imdb', 'tmdb', 'trakt'])
					elif type == 2: rating = self._extract(mode = Rater.ModeRating, item = item, own = own, order = ['trakt', 'imdb', 'tmdb'])
					elif type == 3: rating = self._extract(mode = Rater.ModeRating, item = item, own = own, order = ['tmdb', 'imdb', 'trakt'])
					if mode == Rater.ModeRating: return rating

				if mode is None or mode == Rater.ModeVotes:
					if type == 1: votes = self._extract(mode = Rater.ModeVotes, item = item, own = own, order = ['imdb', 'tmdb', 'trakt'])
					elif type == 2: votes = self._extract(mode = Rater.ModeVotes, item = item, own = own, order = ['trakt', 'imdb', 'tmdb'])
					elif type == 3: votes = self._extract(mode = Rater.ModeVotes, item = item, own = own, order = ['tmdb', 'imdb', 'trakt'])
					if mode == Rater.ModeVotes: return votes

		ratingown = 0
		if 'ratingown' in item and item['ratingown'] and not item['ratingown'] == '0': ratingown = item['ratingown']
		return {Rater.ModeRating : str(rating), Rater.ModeVotes : str(votes), 'userrating' : str(ratingown)}

	@classmethod
	def rating(self, item):
		return self.extract(mode = Rater.ModeRating, item = item)

	@classmethod
	def votes(self, item):
		return self.extract(mode = Rater.ModeVotes, item = item)
