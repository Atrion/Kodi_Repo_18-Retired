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
import xbmcplugin
import re
import os
import json
import copy
import urllib
import time
import math
import datetime
import threading
from resources.lib.extensions import tools
from resources.lib.extensions import network
from resources.lib.extensions import convert
from resources.lib.modules import workers

class Translation(object):

	@classmethod
	def string(self, id, utf8 = True, system = False):
		if isinstance(id, (int, long)):
			# Needs ID when called from RunScript(vpn.py)
			if system: result = xbmc.getLocalizedString(id)
			else: result = xbmcaddon.Addon(tools.System.GaiaAddon).getLocalizedString(id)
		else:
			try: result = str(id)
			except: result = id
		if utf8:
			try:
				if not '•' in result: result = tools.Converter.unicode(string = result, umlaut = True).encode('utf-8')
			except:
				result = tools.Converter.unicode(string = result, umlaut = True).encode('utf-8')
		return result


class Skin(object):

	TypeAeonNox = 'aeon.nox'
	TypeGaiaAeonNox = 'skin.gaia.aeon.nox'

	@classmethod
	def _directory(self):
		return xbmc.getSkinDir()

	@classmethod
	def id(self):
		return self._directory()

	# Any Aeon Nox version
	@classmethod
	def isAeonNox(self):
		return Skin.TypeAeonNox in self.id()

	@classmethod
	def isGaiaAeonNox(self):
		return Skin.TypeGaiaAeonNox in self.id()

	@classmethod
	def select(self):
		id = tools.Extensions.IdGaiaSkins
		items = ['Default', 'Gaia 1 (Color)']
		getMore = Format.fontBold(Translation.string(33740))
		if tools.Extensions.installed(id):
			items.extend(['Gaia 2 (Color)', 'Gaia 3 (Color)', 'Bubbles 1 (Blue)', 'Bubbles 2 (Color)', 'Minimalism (Grey)', 'Universe (Color)', 'Glass (Transparent)', 'Cinema 1 (Blue)', 'Cinema 2 (Blue)', 'Cinema 3 (Orange)', 'Cinema 4 (Red)', 'Home 1 (Color)', 'Home 2 (Blue)', 'Home 3 (Red)', 'Home 4 (White)', 'Home 5 (Black)', 'Home 6 (Blue)'])
		else:
			items.extend([getMore])
		choice = Dialog.options(title = 33337, items = items)
		if choice >= 0:
			if items[choice] == getMore:
				choice = Dialog.option(title = 33337, message = 33742, labelConfirm = 33736, labelDeny = 33743)
				if choice:
					tools.Extensions.enable(id = id)
			else:
				tools.Settings.set('interface.theme.skin', items[choice])


class Icon(object):

	TypeIcon = 'icon'
	TypeThumb = 'thumb'
	TypePoster = 'poster'
	TypeBanner = 'banner'
	TypeDefault = TypeIcon

	QualitySmall = 'small'
	QualityLarge = 'large'
	QualityDefault = QualityLarge

	SpecialNone = None
	SpecialQuality = 'quality'
	SpecialDonations = 'donations'
	SpecialNotifications = 'notifications'

	ThemeInitialized = False
	ThemePath = None
	ThemeIcon = None
	ThemeThumb = None
	ThemePoster = None
	ThemeBanner = None

	@classmethod
	def _initialize(self, special = SpecialNone):
		if special == False or not special == Icon.ThemeInitialized:
			Icon.ThemeInitialized = special
			if special: theme = special
			else: theme = tools.Settings.getString('interface.theme.icon').lower()

			if not theme in ['default', '-', '']:

				theme = theme.replace(' ', '').lower()
				if 'glass' in theme:
					theme = theme.replace('(', '').replace(')', '')
				else:
					index = theme.find('(')
					if index >= 0: theme = theme[:index]

				addon = tools.System.pathResources() if theme in ['white', Icon.SpecialQuality, Icon.SpecialDonations, Icon.SpecialNotifications] else tools.System.pathIcons()
				Icon.ThemePath = tools.File.joinPath(addon, 'resources', 'media', 'icons', theme)

				quality = tools.Settings.getInteger('interface.theme.icon.quality')
				if quality == 0:
					if Skin.isAeonNox():
						Icon.ThemeIcon = Icon.QualitySmall
						Icon.ThemeThumb = Icon.QualitySmall
						Icon.ThemePoster = Icon.QualityLarge
						Icon.ThemeBanner = Icon.QualityLarge
					else:
						Icon.ThemeIcon = Icon.QualityLarge
						Icon.ThemeThumb = Icon.QualityLarge
						Icon.ThemePoster = Icon.QualityLarge
						Icon.ThemeBanner = Icon.QualityLarge
				elif quality == 1:
					Icon.ThemeIcon = Icon.QualitySmall
					Icon.ThemeThumb = Icon.QualitySmall
					Icon.ThemePoster = Icon.QualitySmall
					Icon.ThemeBanner = Icon.QualitySmall
				elif quality == 2:
					Icon.ThemeIcon = Icon.QualityLarge
					Icon.ThemeThumb = Icon.QualityLarge
					Icon.ThemePoster = Icon.QualityLarge
					Icon.ThemeBanner = Icon.QualityLarge
				else:
					Icon.ThemeIcon = Icon.QualityLarge
					Icon.ThemeThumb = Icon.QualityLarge
					Icon.ThemePoster = Icon.QualityLarge
					Icon.ThemeBanner = Icon.QualityLarge

	@classmethod
	def exists(self, icon, type = TypeDefault, default = None, special = SpecialNone, quality = None):
		return tools.File.exists(self.path(icon = icon, type = type, default = default, special = special, quality = quality))

	@classmethod
	def path(self, icon, type = TypeDefault, default = None, special = SpecialNone, quality = None):
		if icon == None: return None
		self._initialize(special = special)
		if Icon.ThemePath == None:
			return default
		else:
			if quality == None:
				if type == Icon.TypeIcon: type = Icon.ThemeIcon
				elif type == Icon.TypeThumb: type = Icon.ThemeThumb
				elif type == Icon.TypePoster: type = Icon.ThemePoster
				elif type == Icon.TypeBanner: type = Icon.ThemeBanner
				else: type = Icon.ThemeIcon
			else:
				type = quality
			if not icon.endswith('.png'): icon += '.png'
			return tools.File.joinPath(Icon.ThemePath, type, icon)

	@classmethod
	def pathAll(self, icon, default = None, special = SpecialNone):
		return (
			self.pathIcon(icon = icon, default = default, special = special),
			self.pathThumb(icon = icon, default = default, special = special),
			self.pathPoster(icon = icon, default = default, special = special),
			self.pathBanner(icon = icon, default = default, special = special)
		)

	@classmethod
	def pathIcon(self, icon, default = None, special = SpecialNone):
		return self.path(icon = icon, type = Icon.TypeIcon, default = default, special = special)

	@classmethod
	def pathThumb(self, icon, default = None, special = SpecialNone):
		return self.path(icon = icon, type = Icon.TypeThumb, default = default, special = special)

	@classmethod
	def pathPoster(self, icon, default = None, special = SpecialNone):
		return self.path(icon = icon, type = Icon.TypePoster, default = default, special = special)

	@classmethod
	def pathBanner(self, icon, default = None, special = SpecialNone):
		return self.path(icon = icon, type = Icon.TypeBanner, default = default, special = special)

	@classmethod
	def select(self):
		id = tools.Extensions.IdGaiaIcons
		items = ['Default', 'White']
		getMore = Format.fontBold(Translation.string(33739))
		if tools.Extensions.installed(id):
			items.extend(['Black', 'Glass (Light)', 'Glass (Dark)', 'Shadow (Grey)', 'Fossil (Grey)', 'Navy (Blue)', 'Cerulean (Blue)', 'Sky (Blue)', 'Pine (Green)', 'Lime (Green)', 'Ruby (Red)', 'Candy (Red)', 'Tiger (Orange)', 'Pineapple (Yellow)', 'Violet (Purple)', 'Magenta (Pink)', 'Amber (Brown)'])
		else:
			items.extend([getMore])
		choice = Dialog.options(title = 33338, items = items)
		if choice >= 0:
			if items[choice] == getMore:
				choice = Dialog.option(title = 33338, message = 33741, labelConfirm = 33736, labelDeny = 33743)
				if choice:
					tools.Extensions.enable(id = id)
			else:
				tools.Settings.set('interface.theme.icon', items[choice])


def formatColorInitialize(customize, type, default):
	if customize:
		color = tools.Settings.getString('interface.color.' + type)
		try: return re.search('\\[.*\\](.*)\\[.*\\]', color, re.IGNORECASE).group(1)
		except: return ''
	else:
		return default


class Format(object):

	ColorCustomize = tools.Settings.getBoolean('interface.color.enabled')

	ColorNone = None
	ColorPrimary = formatColorInitialize(ColorCustomize, 'primary', 'FFA0C12C')
	ColorSecondary = formatColorInitialize(ColorCustomize, 'secondary', 'FF3C7DBF')
	ColorOrion = formatColorInitialize(ColorCustomize, 'orion', 'FF637385')
	ColorMain = formatColorInitialize(ColorCustomize, 'main', 'FF2396FF')
	ColorAlternative = formatColorInitialize(ColorCustomize, 'alternative', 'FF004F98')
	ColorSpecial = formatColorInitialize(ColorCustomize, 'special', 'FF6C3483')
	ColorUltra = formatColorInitialize(ColorCustomize, 'ultra', 'FF00A177')
	ColorExcellent = formatColorInitialize(ColorCustomize, 'excellent', 'FF1E8449')
	ColorGood = formatColorInitialize(ColorCustomize, 'good', 'FF668D2E')
	ColorMedium = formatColorInitialize(ColorCustomize, 'medium', 'FFB7950B')
	ColorPoor = formatColorInitialize(ColorCustomize, 'poor', 'FFBA4A00')
	ColorBad = formatColorInitialize(ColorCustomize, 'bad', 'FF922B21')
	ColorGaia1 = 'FFA0C12C'
	ColorGaia2 = 'FF3C7DBF'
	ColorWhite = 'FFFFFFFF'
	ColorBlack = 'FF000000'
	ColorDisabled = 'FF888888'

	Gradients = {}

	FontNewline = '[CR]'
	FontSeparator = ' • '
	FontPassword = '••••••••••'
	FontDivider = ' - '
	FontSplitInterval = 50

	@classmethod
	def settingsColorUpdate(self, type):
		setting = 'interface.color.' + type
		color = Dialog.input(title = 35235, type = Dialog.InputAlphabetic, default = self.settingsColor(tools.Settings.getString(setting)))
		if self.colorIsHex(color):
			while len(color) < 8: color = 'F' + color
			if len(color) > 8: color = color[:8]
			tools.Settings.set(setting, self.fontColor(color, color))
		else:
			Dialog.notification(title = 35235, message = 35236, icon = Dialog.IconNativeError)

		# If this option is disabled and the user enables it and immediately afterwards selects a color, the settings dialog is closed without being saved first.
		# Force enable it here.
		tools.Settings.set('interface.color.enabled', True)

	@classmethod
	def settingsColor(self, color):
		try: return re.search('\\[.*\\](.*)\\[.*\\]', color, re.IGNORECASE).group(1)
		except: return ''

	@classmethod
	def colorIsHex(self, color):
		return re.match('[0-9a-fA-F]*', color)

	@classmethod
	def colorToRgb(self, hex):
		return [int(hex[i:i+2], 16) for i in range(2,8,2)]

	@classmethod
	def colorToHex(self, rgb):
		rgb = [int(i) for i in rgb]
		return 'FF' + ''.join(['0{0:x}'.format(i) if i < 16 else '{0:x}'.format(i) for i in rgb])

	@classmethod
	def colorGradient(self, startHex, endHex, count = 10):
		key = '%s_%s_%s' % (str(startHex), str(endHex), str(count))
		if not key in Format.Gradients:
			# http://bsou.io/posts/color-gradients-with-python
			start = self.colorToRgb(startHex)
			end = self.colorToRgb(endHex)
			colors = [start]
			for i in range(1, count):
				vector = [int(start[j] + (float(i) / (count-1)) * (end[j] - start[j])) for j in range(3)]
				colors.append(vector)
			Format.Gradients[key] = [self.colorToHex(i) for i in colors]
		return Format.Gradients[key]

	@classmethod
	def colorGradientIncrease(self, count = 10):
		return self.colorGradient(Format.ColorBad, Format.ColorExcellent, count)

	@classmethod
	def colorGradientDecrease(self, count = 10):
		return self.colorGradient(Format.ColorExcellent, Format.ColorBad, count)

	@classmethod
	def colorChange(self, color, change = 10):
		if color:
			color = self.colorToRgb(color)
			color = [i + change for i in color]
			color = [min(255, max(0, i)) for i in color]
			return self.colorToHex(color)
		else:
			return None

	@classmethod
	def colorLighter(self, color, change = 10):
		return self.colorChange(color, change)

	@classmethod
	def colorDarker(self, color, change = 10):
		return self.colorChange(color, -change)

	@classmethod
	def __translate(self, label, utf8 = True):
		return Translation.string(label, utf8 = utf8)

	@classmethod
	def font(self, label, color = None, bold = None, italic = None, light = None, uppercase = None, lowercase = None, capitalcase = None, newline = None, separator = None, translate = True):
		if label == None: return label
		if translate: label = self.__translate(label)
		if label:
			if color:
				label = self.fontColor(label, color, translate = False)
			if bold:
				label = self.fontBold(label, translate = False)
			if italic:
				label = self.fontItalic(label, translate = False)
			if light:
				label = self.fontLight(label, translate = False)
			if uppercase:
				label = self.fontUppercase(label, translate = False)
			elif lowercase:
				label = self.fontLowercase(label, translate = False)
			elif capitalcase:
				label = self.fontCapitalcase(label, translate = False)
			if newline:
				label += self.fontNewline(translate = False)
			if separator:
				label += self.fontSeparator(translate = False)
			return label
		else:
			return ''

	@classmethod
	def fontColor(self, label, color, translate = True):
		if color == None: return label
		if len(color) == 6: color = 'FF' + color
		if translate: label = self.__translate(label)
		return '[COLOR ' + color + ']' + label + '[/COLOR]'

	@classmethod
	def fontBold(self, label, translate = True):
		if translate: label = self.__translate(label)
		return '[B]' + label + '[/B]'

	@classmethod
	def fontItalic(self, label, translate = True):
		if translate: label = self.__translate(label)
		return '[I]' + label + '[/I]'

	@classmethod
	def fontLight(self, label, translate = True):
		if translate: label = self.__translate(label)
		return '[LIGHT]' + label + '[/LIGHT]'

	@classmethod
	def fontUppercase(self, label, translate = True):
		if translate: label = self.__translate(label)
		return '[UPPERCASE]' + label + '[/UPPERCASE]'

	@classmethod
	def fontLowercase(self, label, translate = True):
		if translate: label = self.__translate(label)
		return '[LOWERCASE]' + label + '[/LOWERCASE]'

	@classmethod
	def fontCapitalcase(self, label, translate = True):
		if translate: label = self.__translate(label)
		return '[CAPITALIZE]' + label + '[/CAPITALIZE]'

	@classmethod
	def fontNewline(self):
		return Format.FontNewline

	@classmethod
	def fontSeparator(self, color = ColorDisabled):
		return self.fontColor(Format.FontSeparator, color = color, translate = False)

	@classmethod
	def fontDivider(self):
		return Format.FontDivider

	@classmethod
	def fontSplit(self, label, interval = None, type = None):
		if not interval: interval = Format.FontSplitInterval
		if not type: type = Format.FontNewline
		return re.sub('(.{' + str(interval) + '})', '\\1' + type, label, 0, re.DOTALL)

	# Synonyms

	@classmethod
	def color(self, label, color):
		return self.fontColor(label, color)

	@classmethod
	def bold(self, label):
		return self.fontBold(label)

	@classmethod
	def italic(self, label):
		return self.fontItalic(label)

	@classmethod
	def light(self, label):
		return self.fontLight(label)

	@classmethod
	def uppercase(self, label):
		return self.fontUppercase(label)

	@classmethod
	def lowercase(self, label):
		return self.fontLowercase(label)

	@classmethod
	def capitalcase(self, label):
		return self.fontCapitalcase(label)

	@classmethod
	def newline(self):
		return self.fontNewline()

	@classmethod
	def separator(self):
		return self.fontSeparator()

	@classmethod
	def divider(self):
		return self.fontDivider()

	@classmethod
	def split(self, label, interval = None, type = None):
		return self.fontSplit(label = label, interval = interval, type = type)


class Changelog(object):

	@classmethod
	def show(self):
		path = tools.File.joinPath(tools.System.path(), 'changelog.txt')
		file = open(path)
		text = file.read()
		file.close()
		Dialog.page(title = 33503, message = text)


CoreIntance = None

class Core(object):

	TypeScrape = 'interface.navigation.scrape'
	TypePlayback = 'interface.navigation.playback'
	TypeDownload = 'downloads.manual.progress'

	def __init__(self):
		self.mType = None
		self.mDialog = None
		self.mTitle = None
		self.mTitleBold = None
		self.mMessage = None
		self.mProgress = None
		self.mBackground = False
		self.mClosed = True

		self.mThread = None
		self.mRunning = False
		self.mDots = False
		self.mSuffix = ''

	def __del__(self):
		# If CoreIntance runs out of scope, close the dialog.
		self.close()

	def _dots(self):
		dots = ' '
		self.mRunning = True
		while self.mDots and self.visible():
			dots += '.'
			if len(dots) > 4: dots = ' '
			self.mSuffix = Format.fontBold(dots)
			self._update()
			tools.Time.sleep(0.5)
		self.mRunning = False

	def _set(self, type = None, dialog = None, title = None, message = None, progress = None, background = None, dots = None):
		if not type == None: self.mType = type
		if not dots == None: self.mDots = dots
		if not dialog == None: self.mDialog = dialog

		if not title == None: self.mTitle = title
		if self.mTitle == None: self.mTitle = 35302
		self.mTitleBold = Format.fontBold(self.mTitle)

		if not message == None: self.mMessage = message
		if self.mMessage == None: self.mMessage = 35302

		if not progress == None: self.mProgress = progress
		if self.mProgress == None: self.mProgress = 0

		if not background == None: self.mBackground = background
		else: self.mBackground = self.backgroundSetting()

	@classmethod
	def instance(self):
		global CoreIntance
		if CoreIntance == None:
			CoreIntance = Core()
		return CoreIntance

	@classmethod
	def instanceHas(self):
		global CoreIntance
		return CoreIntance == None

	@classmethod
	def dialog(self):
		return self.instance().mDialog

	@classmethod
	def background(self):
		return self.instance().mBackground

	@classmethod
	def backgroundSetting(self):
		type = self.instance().mType
		if type == Core.TypeDownload: index = 3
		else: index = 2
		return tools.Settings.getInteger(type) == index

	@classmethod
	def canceled(self):
		try: return self.dialog().iscanceled()
		except: return False

	@classmethod
	def visible(self):
		return not self.instance().mClosed and not self.canceled()

	@classmethod
	def create(self, type = None, title = None, message = None, progress = None, background = None, close = None, dots = True):
		try:
			core = self.instance()

			if close == None:
				# Background dialog has a lot more problems. Always close.
				# Foreground dialog is more robust as does not need it.
				# This ensures the the foreground dialog stays open, instead of popping up and closing all the time.

				# NB: Currently seems fine with background dialogs as well. In case the interleaving flickering between messages starts again, enable this.
				close = False
				#if background == None: close = core.mBackground
				#else: close = background

			if close or not core.mDialog:
				self.close()

			core._set(type = type, title = title, message = message, progress = progress, background = background, dots = dots)

			if core.mClosed or not core.mDialog:
				# If launched for the first time, close all other progress dialogs.
				if not core.mDialog:
					Dialog.closeAllProgress()
					tools.Time.sleep(0.1)
				try: del core.mDialog
				except: pass
				core.mDialog = Dialog.progress(background = core.mBackground, title = core.mTitle, message = core.mMessage)

			core.mClosed = False
			core._update()

			if core.mDots and (not core.mThread or not core.mRunning):
				core.mThread = threading.Thread(target = core._dots)
				core.mThread.start()

			return core.mDialog
		except:
			tools.Logger.error()

	def _update(self):
		if self.mBackground:
			try: self.mDialog.update(self.mProgress, self.mTitleBold, self.mMessage % self.mSuffix)
			except: self.mDialog.update(self.mProgress, self.mTitleBold, self.mMessage)
		else:
			try: self.mDialog.update(self.mProgress, self.mMessage % self.mSuffix)
			except: self.mDialog.update(self.mProgress, self.mMessage)

	@classmethod
	def update(self, title = None, message = None, progress = None, background = None, dots = None):
		try:
			core = self.instance()
			if core.mDialog == None or not self.visible():
				if dots == None: return self.create(title = title, message = message, progress = progress, background = background)
				else: return self.create(title = title, message = message, progress = progress, background = background, dots = dots)
			else:
				core._set(title = title, message = message, progress = progress, dots = dots)
				core._update()
				return core.mDialog
		except: pass

	@classmethod
	def close(self, delay = 0):
		try:
			# NB: Checking DialogCoreClosed is very important.
			# Do not rely on the try-catch statement.
			# Kodi crashes instead of throwing an exception.
			core = self.instance()
			if not core.mClosed:
				core.mClosed = True
				if core.mDialog:
					# Must be set to 100, otherwise it shows up in a later dialog.
					#if core.mBackground: core.mDialog.update(100, ' ', ' ')
					#else: core.mDialog.update(100, ' ')
					core.mProgress = 100
					core._update()

					core.mDialog.close()
					try:
						del core.mDialog
						core.mDialog = None
					except: pass
				if delay > 0: tools.Time.sleep(delay)
		except: pass


class Dialog(object):

	IconPlain = 'logo'
	IconInformation = 'information'
	IconWarning = 'warning'
	IconError = 'error'
	IconSuccess = 'success'

	IconNativeLogo = 'nativelogo'
	IconNativeInformation = 'nativeinformation'
	IconNativeWarning = 'nativewarning'
	IconNativeError = 'nativeerror'

	InputAlphabetic = xbmcgui.INPUT_ALPHANUM # Standard keyboard
	InputNumeric = xbmcgui.INPUT_NUMERIC # Format: #
	InputDate = xbmcgui.INPUT_DATE # Format: DD/MM/YYYY
	InputTime = xbmcgui.INPUT_TIME # Format: HH:MM
	InputIp = xbmcgui.INPUT_IPADDRESS # Format: #.#.#.#
	InputPassword = xbmcgui.INPUT_PASSWORD # Returns MD55 hash of input and the input is masked.

	# Numbers/values must correspond with Kodi
	BrowseFile = 1
	BrowseImage = 2
	BrowseDirectoryRead = 0
	BrowseDirectoryWrite = 3
	BrowseDefault = BrowseFile

	PrefixColor = Format.ColorPrimary
	PrefixBack = '« '
	PrefixNext = '» '

	IdDialogText = 10147
	IdDialogProgress = 10101
	IdDialogOk = 12002
	IdDialogNotification = 10107

	@classmethod
	def prefix(self, text, prefix, color = PrefixColor, bold = True):
		return Format.font(prefix, color = color, bold = bold, translate = False) + Translation.string(text)

	@classmethod
	def prefixBack(self, text, color = PrefixColor, bold = None):
		return self.prefix(text = text, prefix = Dialog.PrefixBack, color = color, bold = bold)

	@classmethod
	def prefixNext(self, text, color = PrefixColor, bold = None):
		return self.prefix(text = text, prefix = Dialog.PrefixNext, color = color, bold = bold)

	@classmethod
	def prefixContains(self, text):
		try: return Dialog.PrefixBack in text or Dialog.PrefixNext in text
		except: return False

	@classmethod
	def close(self, id, sleep = None):
		xbmc.executebuiltin('Dialog.Close(%s,true)' % str(id))
		if sleep: time.sleep(sleep / 1000.0)

	@classmethod
	def closeOk(self, sleep = None):
		self.close(id = self.IdDialogOk, sleep = sleep)

	@classmethod
	def closeNotification(self, sleep = None):
		self.close(id = self.IdDialogNotification, sleep = sleep)

	# Close all open dialog.
	# Sometimes if you open a dialog right after this, it also clauses. Might need some sleep to prevent this. sleep in ms.
	@classmethod
	def closeAll(self, sleep = None):
		xbmc.executebuiltin('Dialog.Close(all,true)')
		if sleep: time.sleep(sleep / 1000.0)

	@classmethod
	def closeAllProgress(self, sleep = None):
		xbmc.executebuiltin('Dialog.Close(progressdialog,true)')
		xbmc.executebuiltin('Dialog.Close(extendedprogressdialog,true)')
		if sleep: time.sleep(sleep / 1000.0)

	@classmethod
	def closeAllNative(self, sleep = None):
		xbmc.executebuiltin('Dialog.Close(virtualkeyboard,true)')
		xbmc.executebuiltin('Dialog.Close(yesnodialog,true)')
		xbmc.executebuiltin('Dialog.Close(progressdialog,true)')
		xbmc.executebuiltin('Dialog.Close(extendedprogressdialog,true)')
		xbmc.executebuiltin('Dialog.Close(sliderdialog,true)')
		xbmc.executebuiltin('Dialog.Close(okdialog,true)')
		xbmc.executebuiltin('Dialog.Close(selectdialog,true)')
		if sleep: time.sleep(sleep / 1000.0)

	@classmethod
	def aborted(self):
		return xbmc.abortRequested

	# Current window ID
	@classmethod
	def windowId(self):
		return xbmcgui.getCurrentWindowId()

	# Check if certain window is currently showing.
	@classmethod
	def windowVisible(self, id):
		return self.windowId() == id

	# Current dialog ID
	@classmethod
	def dialogId(self):
		return xbmcgui.getCurrentWindowDialogId()

	# Check if certain dialog is currently showing.
	@classmethod
	def dialogVisible(self, id):
		return self.dialogId() == id

	@classmethod
	def dialogProgressVisible(self):
		return self.dialogVisible(Dialog.IdDialogProgress)

	@classmethod
	def confirm(self, message, title = None):
		return xbmcgui.Dialog().ok(self.title(title), self.__translate(message))

	@classmethod
	def select(self, items, multiple = False, selection = None, title = None):
		return self.options(items = items, multiple = multiple, selection = selection, title = title)

	@classmethod
	def option(self, message, labelConfirm = None, labelDeny = None, title = None):
		if not labelConfirm == None:
			labelConfirm = self.__translate(labelConfirm)
		if not labelDeny == None:
			labelDeny = self.__translate(labelDeny)
		return xbmcgui.Dialog().yesno(self.title(title), self.__translate(message), yeslabel = labelConfirm, nolabel = labelDeny)

	@classmethod
	def options(self, items, multiple = False, selection = None, title = None):
		if multiple:
			try: return xbmcgui.Dialog().multiselect(self.title(title), items, preselect = selection)
			except: return xbmcgui.Dialog().multiselect(self.title(title), items)
		else:
			try: return xbmcgui.Dialog().select(self.title(title), items, preselect = selection)
			except: return xbmcgui.Dialog().select(self.title(title), items)

	# icon: icon or path to image file.
	# titleless: Without Gaia at the front of the title.
	@classmethod
	def notification(self, message, icon = None, time = 3000, sound = False, title = None, titleless = False):
		if icon and not (icon.startswith('http') or icon.startswith('ftp') or tools.File.exists(icon)):
			icon = icon.lower()
			if icon == Dialog.IconNativeInformation: icon = xbmcgui.NOTIFICATION_INFO
			elif icon == Dialog.IconNativeWarning: icon = xbmcgui.NOTIFICATION_WARNING
			elif icon == Dialog.IconNativeError: icon = xbmcgui.NOTIFICATION_ERROR
			else:
				if icon == Dialog.IconPlain or icon == Dialog.IconNativeLogo: icon = 'plain'
				elif icon == Dialog.IconWarning: icon = 'warning'
				elif icon == Dialog.IconError: icon = 'error'
				elif icon == Dialog.IconSuccess: icon = 'success'
				else: icon = 'information'
				icon = Icon.pathIcon(icon = icon, special = Icon.SpecialNotifications)
		xbmcgui.Dialog().notification(self.title(title, titleless = titleless), self.__translate(message), icon, time, sound = sound)

	# items = [(label1,callback1),(label2,callback2),...]
	# or labels = [label1,label2,...]
	@classmethod
	def context(self, items = None, labels = None):
		if items:
			labels = [i[0] for i in items]
			choice = xbmcgui.Dialog().contextmenu(labels)
			if choice >= 0: return items[choice][1]()
			else: return False
		else:
			return xbmcgui.Dialog().contextmenu(labels)

	@classmethod
	def progress(self, message = None, background = False, title = None):
		if background:
			dialog = xbmcgui.DialogProgressBG()
		else:
			dialog = xbmcgui.DialogProgress()
		if not message:
			message = ''
		else:
			message = self.__translate(message)
		title = self.title(title)
		dialog.create(title, message)
		if background:
			dialog.update(0, title, message)
		else:
			dialog.update(0, message)
		return dialog

	# verify: Existing MD5 password string to compare against.
	# confirm: Confirm password. Must be entered twice
	# hidden: Hides alphabetic input.
	# default: Default set input.
	@classmethod
	def input(self, type = InputAlphabetic, verify = False, confirm = False, hidden = False, default = None, title = None):
		default = '' if default == None else default
		if verify:
			option = xbmcgui.PASSWORD_VERIFY
			if isinstance(verify, basestring):
				default = verify
		elif confirm:
			option = 0
		elif hidden:
			option = xbmcgui.ALPHANUM_HIDE_INPUT
		else:
			option = None
		# NB: Although the default parameter is given in the docs, it seems that the parameter is not actually called "default". Hence, pass it in as an unmaed parameter.
		if option == None: result = xbmcgui.Dialog().input(self.title(title), str(default), type = type)
		else: result = xbmcgui.Dialog().input(self.title(title), str(default), type = type, option = option)

		if verify:
			return not result == ''
		else:
			return result

	@classmethod
	def inputPassword(self, verify = False, confirm = False, title = None):
		return self.input(title = title, type = Dialog.InputPassword, verify = verify, confirm = confirm)

	@classmethod
	def browse(self, type = BrowseDefault, default = None, multiple = False, mask = [], title = None):
		if default == None: default = tools.File.joinPath(tools.System.pathHome(), '') # Needs to end with a slash
		if mask == None: mask = []
		elif isinstance(mask, basestring): mask = [mask]
		for i in range(len(mask)):
			mask[i] = mask[i].lower()
			if not mask[i].startswith('.'):
				mask[i] = '.' + mask[i]
		mask = '|'.join(mask)
		return xbmcgui.Dialog().browse(type, self.title(title), 'files', mask, True, False, default, multiple)

	@classmethod
	def page(self, message, title = None):
		xbmc.executebuiltin('ActivateWindow(%d)' % Dialog.IdDialogText)
		time.sleep(0.5)
		window = xbmcgui.Window(Dialog.IdDialogText)
		retry = 50
		while retry > 0:
			try:
				time.sleep(0.01)
				retry -= 1
				window.getControl(1).setLabel(self.title(title))
				window.getControl(5).setText('[CR]' + message)
				break
			except: pass
		return window

	@classmethod
	def pageVisible(self):
		return self.dialogVisible(Dialog.IdDialogText)

	# Creates an information dialog.
	# Either a list of item categories, or a list of items.
	# Without actions:
	#	[
	#		{'title' : 'Category 1', 'items' : [{'title' : 'Name 1', 'value' : 'Value 1', 'link' : True}, {'title' : 'Name 2', 'value' : 'Value 2'}]},
	#		{'title' : 'Category 2', 'items' : [{'title' : 'Name 3', 'value' : 'Value 3', 'link' : False}, {'title' : 'Name 4', 'value' : 'Value 4'}]},
	#	]
	# With actions:
	#	[
	#		{'title' : 'Category 1', 'items' : [{'title' : 'Name 1', 'value' : 'Value 1', 'link' : True, 'action' : function, 'close' : True, 'return' : 'return value'}, {'title' : 'Name 2', 'value' : 'Value 2', 'action' : function, 'close' : True}]},
	#		{'title' : 'Category 2', 'items' : [{'title' : 'Name 3', 'value' : 'Value 3', 'link' : False, 'action' : function, 'close' : True, 'return' : 'return value'}, {'title' : 'Name 4', 'value' : 'Value 4', 'action' : function, 'close' : True}]},
	#	]
	@classmethod
	def information(self, items, title = None, refresh = None):
		if items == None or len(items) == 0:
			return False

		def decorate(item):
			value = item['value'] if 'value' in item else None
			label = item['title'] if 'title' in item else ''
			prefix = Dialog.prefixContains(label)
			if not prefix: label = self.__translate(label)
			if value == None:
				heading = value or 'items' in item
				label = Format.font(label, bold = True, uppercase = heading, color = Format.ColorPrimary if heading else None, translate = False if prefix else True)
			else:
				if not label == '':
					if not value == None:
						label += ': '
					label = Format.font(label, bold = True, color = Format.ColorSecondary)
				if not value == None:
					label += Format.font(self.__translate(item['value']), italic = ('link' in item and item['link']))
			return label

		def create(items):
			result = []
			actions = []
			closes = []
			returns = []
			for item in items:
				if not item == None:
					if 'items' in item:
						if not len(result) == 0:
							result.append('')
							actions.append(None)
							closes.append(None)
							returns.append(None)
						result.append(decorate(item))
						actions.append(item['action'] if 'action' in item else None)
						closes.append(item['close'] if 'close' in item else False)
						returns.append(item['return'] if 'return' in item else None)
						for i in item['items']:
							if not i == None:
								result.append(decorate(i))
								actions.append(i['action'] if 'action' in i else None)
								closes.append(i['close'] if 'close' in i else False)
								returns.append(i['return'] if 'return' in i else None)
					else:
						result.append(decorate(item))
						actions.append(item['action'] if 'action' in item else None)
						closes.append(item['close'] if 'close' in item else False)
						returns.append(item['return'] if 'return' in item else None)
			return result, actions, closes, returns

		items, actions, closes, returns = create(items)
		if any(i for i in actions):
			while True:
				choice = self.select(items = items, title = title)
				if choice < 0: break
				if actions[choice]: actions[choice]()
				if closes[choice]: break
				elif refresh: items, actions, closes, returns = create(refresh())
		elif any(i for i in returns):
			choice = self.select(items, title = title)
			if choice < 0: return None
			return returns[choice]
		else:
			return self.select(items, title = title)

	@classmethod
	def __translate(self, string):
		return Translation.string(string)

	@classmethod
	def title(self, extension = None, bold = True, titleless = False):
		title = '' if titleless else tools.System.name().encode('utf-8')
		if not extension == None:
			if not titleless:
				title += Format.divider()
			title += self.__translate(extension)
		if bold:
			title = Format.fontBold(title)
		return title


class Splash(xbmcgui.WindowDialog):

	# Types
	TypeFull = 'full'
	TypeMini = 'mini'
	TypeName = 'name'
	TypeIcon = 'icon'
	TypeAbout = 'about'
	TypeMessage = 'message'
	TypeDonations = 'donations'

	# Actions
	ActionSelectItem = 7
	ActionPreviousMenu = 10
	ActionNavigationBack = 92
	ActionMoveRight = 2
	ActionMoveLeft = 1
	ActionsCancel = [ActionPreviousMenu, ActionNavigationBack, ActionMoveRight]
	ActionsMaximum = 100 # Mouse other unwanted actions.

	# Duration
	Duration = 2000

	# All Kodi windows have this fixed dimension.
	SizeWidth = 1280
	SizeHeight = 720

	# Size
	SizeLarge = 'large'
	SizeMedium = 'medium'
	SizeSmall = 'small'

	# Format
	FormatWhite = '0xFFFFFFFF'
	FormatCenter = 0x00000002 | 0x00000004

	def __init__(self, type, message = None, donation = None):
		Loader.show()

		from resources.lib.extensions import debrid
		self.mType = type
		self.mSplash = None

		self.mScaleWidthExtra = 1
		self.mScaleHeightExtra = 1
		self.mScaleWidth = tools.Screen.height() / float(Splash.SizeHeight)
		self.mScaleHeight = tools.Screen.width() / float(Splash.SizeWidth)
		if self.mScaleWidth > self.mScaleHeight:
			self.mScaleWidth = self.mScaleWidth / self.mScaleHeight
			self.mScaleHeight = 1
			self.mScaleWidthExtra = self.mScaleHeightExtra = self.mScaleHeight / self.mScaleWidth
		elif self.mScaleWidth < self.mScaleHeight:
			self.mScaleHeight = self.mScaleHeight / self.mScaleWidth
			self.mScaleWidth = 1
			self.mScaleWidthExtra = self.mScaleHeightExtra = self.mScaleWidth / self.mScaleHeight

		self.mWidth = Splash.SizeWidth
		self.mHeight = Splash.SizeHeight

		self.mButtonPremiumize = None
		self.mButtonOffCloud = None
		self.mButtonRealDebrid = None
		self.mButtonEasyNews = None
		self.mButtonFreeHosters = None
		self.mButtonCoinBase = None
		self.mButtonExodus = None
		self.mButtonClose = None

		try:
			if type == Splash.TypeMini:
				widthTotal, heightTotal = self.__window(False, True)
			elif type == Splash.TypeName:
				width = self.__scaleWidth(379)
				height = self.__scaleHeight(192)
				x = self.__centerX(width)
				y = self.__centerY(height)
				self.addControl(xbmcgui.ControlImage(x, y, width, height, self.__name(True)))
			elif type == Splash.TypeIcon:
				width = self.__scaleWidth(381)
				height = self.__scaleHeight(384)
				x = self.__centerX(width)
				y = self.__centerY(height)
				self.addControl(xbmcgui.ControlImage(x, y, width, height, self.__icon(True, Splash.SizeLarge)))
			elif type == Splash.TypeFull:
				widthTotal, heightTotal = self.__window(True, True)

				width = widthTotal - self.__scaleWidth(165)
				height = self.__scaleHeight(113)
				x = self.__centerX(widthTotal) + self.__scaleWidth(83)
				y = self.__centerY(heightTotal) + self.__scaleHeight(225)
				label = 'Gaia is optimized for the premium services ' + Format.fontBold('Premiumize') + ', ' + Format.fontBold('OffCloud') + ', ' + Format.fontBold('RealDebrid') + ', and ' + Format.fontBold('EasyNews') + ' to facilitate additional, faster, and higher quality streams. Purchase an account by clicking the buttons below and support the addon development at the same time.'
				self.__textbox(x, y, width, height, label)

				# PREMIUMIZE
				self.mButtonPremiumize = self.__button(
					buttonLabel = '        Premiumize',
					buttonX = self.__centerX(widthTotal) + self.__scaleWidth(83),
					buttonY = self.__centerY(heightTotal) + self.__scaleHeight(345),
					buttonWidth = self.__scaleWidth(173),
					buttonHeight = self.__scaleHeight(53),

					iconPath = Icon.path('premiumize.png', type = Icon.ThemeIcon),
					iconX = self.__centerX(widthTotal) + self.__scaleWidth(86),
					iconY = self.__centerY(heightTotal) + self.__scaleHeight(345),
					iconWidth = self.__scaleWidth(53),
					iconHeight = self.__scaleHeight(53),

					infoLabel = 'Torrents • Usenet • Hosters',
					infoX = self.__centerX(widthTotal) + self.__scaleWidth(83),
					infoY = self.__centerY(heightTotal) + self.__scaleHeight(405),
					infoWidth = self.__scaleWidth(173),
					infoHeight = self.__scaleHeight(15)
				)

				# OFFCLOUD
				self.mButtonOffCloud = self.__button(
					buttonLabel = '       OffCloud',
					buttonX = self.__centerX(widthTotal) + self.__scaleWidth(270),
					buttonY = self.__centerY(heightTotal) + self.__scaleHeight(345),
					buttonWidth = self.__scaleWidth(173),
					buttonHeight = self.__scaleHeight(53),

					iconPath = Icon.path('realdebrid.png', type = Icon.ThemeIcon),
					iconX = self.__centerX(widthTotal) + self.__scaleWidth(274),
					iconY = self.__centerY(heightTotal) + self.__scaleHeight(345),
					iconWidth = self.__scaleWidth(53),
					iconHeight = self.__scaleHeight(53),

					infoLabel = 'Torrents • Usenet • Hosters',
					infoX = self.__centerX(widthTotal) + self.__scaleWidth(270),
					infoY = self.__centerY(heightTotal) + self.__scaleHeight(405),
					infoWidth = self.__scaleWidth(173),
					infoHeight = self.__scaleHeight(15)
				)

				# REALDEBRID
				self.mButtonRealDebrid = self.__button(
					buttonLabel = '       RealDebrid',
					buttonX = self.__centerX(widthTotal) + self.__scaleWidth(458),
					buttonY = self.__centerY(heightTotal) + self.__scaleHeight(345),
					buttonWidth = self.__scaleWidth(173),
					buttonHeight = self.__scaleHeight(53),

					iconPath = Icon.path('realdebrid.png', type = Icon.ThemeIcon),
					iconX = self.__centerX(widthTotal) + self.__scaleWidth(461),
					iconY = self.__centerY(heightTotal) + self.__scaleHeight(345),
					iconWidth = self.__scaleWidth(53),
					iconHeight = self.__scaleHeight(53),

					infoLabel = 'Torrents • Hosters',
					infoX = self.__centerX(widthTotal) + self.__scaleWidth(458),
					infoY = self.__centerY(heightTotal) + self.__scaleHeight(405),
					infoWidth = self.__scaleWidth(173),
					infoHeight = self.__scaleHeight(15)
				)

				# EASYNEWS
				self.mButtonEasyNews = self.__button(
					buttonLabel = '       EasyNews',
					buttonX = self.__centerX(widthTotal) + self.__scaleWidth(645),
					buttonY = self.__centerY(heightTotal) + self.__scaleHeight(345),
					buttonWidth = self.__scaleWidth(173),
					buttonHeight = self.__scaleHeight(53),

					iconPath = Icon.path('easynews.png', type = Icon.ThemeIcon),
					iconX = self.__centerX(widthTotal) + self.__scaleWidth(649),
					iconY = self.__centerY(heightTotal) + self.__scaleHeight(345),
					iconWidth = self.__scaleWidth(53),
					iconHeight = self.__scaleHeight(53),

					infoLabel = 'Usenet',
					infoX = self.__centerX(widthTotal) + self.__scaleWidth(645),
					infoY = self.__centerY(heightTotal) + self.__scaleHeight(405),
					infoWidth = self.__scaleWidth(173),
					infoHeight = self.__scaleHeight(15)
				)

				# FREE HOSTERS
				self.mButtonFreeHosters = self.__button(
					buttonLabel = '       Free Hosters',
					buttonX = self.__centerX(widthTotal) + self.__scaleWidth(356),
					buttonY = self.__centerY(heightTotal) + self.__scaleHeight(435),
					buttonWidth = self.__scaleWidth(188),
					buttonHeight = self.__scaleHeight(53),

					iconPath = Icon.path('networks.png', type = Icon.ThemeIcon),
					iconX = self.__centerX(widthTotal) + self.__scaleHeight(360),
					iconY = self.__centerY(heightTotal) + self.__scaleHeight(435),
					iconWidth = self.__scaleHeight(53),
					iconHeight = self.__scaleHeight(53),

					infoLabel = 'Free Access • Fewer Streams • Lower Quality',
					infoX = self.__centerX(widthTotal) + self.__scaleWidth(83),
					infoY = self.__centerY(heightTotal) + self.__scaleHeight(495),
					infoWidth = self.__scaleWidth(735),
					infoHeight = self.__scaleHeight(15)
				)

			elif type == Splash.TypeAbout:
				widthTotal, heightTotal = self.__window(True, True)

				width = widthTotal
				height = heightTotal
				x = self.__centerX(widthTotal)
				y = self.__centerY(heightTotal) - self.__scaleHeight(30)
				label = Format.fontBold(Translation.string(33359) + ' ' + tools.System.version())
				label += Format.newline() + Format.fontBold(tools.Settings.getString('link.website', raw = True))
				self.addControl(xbmcgui.ControlLabel(x, y, width, height, label, textColor = Splash.FormatWhite, alignment = Splash.FormatCenter))

				width = widthTotal - self.__scaleWidth(165)
				height = self.__scaleHeight(150)
				x = self.__centerX(widthTotal) + self.__scaleWidth(83)
				y = self.__centerY(heightTotal) + self.__scaleHeight(285)
				label = tools.System.disclaimer()
				self.__textbox(x, y, width, height, label)

				self.mButtonClose = self.__button(
					buttonLabel = '       Close',
					buttonX = self.__centerX(widthTotal) + self.__scaleWidth(375),
					buttonY = self.__centerY(heightTotal) + self.__scaleHeight(450),
					buttonWidth = self.__scaleWidth(150),
					buttonHeight = self.__scaleHeight(53),

					iconPath = Icon.path('error.png', type = Icon.ThemeIcon),
					iconX = self.__centerX(widthTotal) + self.__scaleWidth(379),
					iconY = self.__centerY(heightTotal) + self.__scaleHeight(450),
					iconWidth = self.__scaleWidth(53),
					iconHeight = self.__scaleHeight(53),
				)

			elif type == Splash.TypeMessage:
				widthTotal, heightTotal = self.__window(True, True)

				width = widthTotal - self.__scaleWidth(165)
				height = self.__scaleHeight(210)
				x = self.__centerX(widthTotal) + self.__scaleWidth(83)
				y = self.__centerY(heightTotal) + self.__scaleHeight(225)
				self.__textbox(x, y, width, height, message, font = 'font14')

				self.mButtonClose = self.__button(
					buttonLabel = '       Close',
					buttonX = self.__centerX(widthTotal) + self.__scaleWidth(375),
					buttonY = self.__centerY(heightTotal) + self.__scaleHeight(450),
					buttonWidth = self.__scaleWidth(150),
					buttonHeight = self.__scaleHeight(53),

					iconPath = Icon.path('error.png', type = Icon.ThemeIcon),
					iconX = self.__centerX(widthTotal) + self.__scaleWidth(379),
					iconY = self.__centerY(heightTotal) + self.__scaleHeight(450),
					iconWidth = self.__scaleWidth(53),
					iconHeight = self.__scaleHeight(53),
				)

			elif type == Splash.TypeDonations:
				try:
					try:
						donationIdentifier = donation['identifier']
						donationAddress = donation['address']
						if network.Networker.linkIs(donationAddress): donationAddressQr = urllib.quote_plus(donationAddress)
						else: donationAddressQr = donationAddress
						donationQrcode = 'https://api.qrserver.com/v1/create-qr-code/?size=300x300&bgcolor=FFFFFF&color=000000&data=%s' % donationAddressQr
						if len(donationAddress) > 75: donationAddress = tools.Settings.getString('link.donation', raw = True)
						if network.Networker.linkIs(donationAddress):
							donationAddressLabel = Translation.string(33915) + ': ' + donationAddress
						else:
							donationAddressLabel = Translation.string(33507) + ': ' + donationAddress
					except:
						donationIdentifier = 'other'
						donationAddress = tools.Settings.getString('link.donation', raw = True)
						donationQrcode = ''
						donationAddressLabel = Translation.string(33915) + ': ' + donationAddress

					from resources.lib.extensions import clipboard
					clipboard.Clipboard.copy(donationAddress)

					widthTotal, heightTotal = self.__window(True, True)

					width = self.__scaleWidth(188)
					height = self.__scaleHeight(188)
					x = self.__centerX(widthTotal) + self.__scaleWidth(105)
					y = self.__centerY(heightTotal) + self.__scaleHeight(225)
					self.addControl(xbmcgui.ControlImage(x, y, width, height, Icon.path('donations' + donationIdentifier, special = Icon.SpecialDonations, quality = Icon.QualityLarge)))

					width = self.__scaleWidth(143)
					height = self.__scaleHeight(143)
					x = self.__centerX(widthTotal) + self.__scaleWidth(128)
					y = self.__centerY(heightTotal) + self.__scaleHeight(248)
					self.addControl(xbmcgui.ControlImage(x, y, width, height, donationQrcode))

					width = self.__scaleWidth(488)
					height = self.__scaleHeight(150)
					x = self.__centerX(widthTotal) + self.__scaleWidth(293)
					y = self.__centerY(heightTotal) + self.__scaleHeight(240)
					label = Translation.string(33506)
					self.__textbox(x, y, width, height, label)

					width = widthTotal
					height = self.__scaleHeight(38)
					x = self.__centerX(widthTotal)
					y = self.__centerY(heightTotal) + self.__scaleHeight(401)
					wallet = xbmcgui.ControlFadeLabel(x, y, width, height, 'font14', Splash.FormatWhite, Splash.FormatCenter) # Do not use named parameters, since it causes crashes.
					self.addControl(wallet)
					wallet.addLabel(Format.font(donationAddressLabel, bold = True))

					# COINBASE
					self.mButtonCoinBase = self.__button(
						buttonLabel = '       CoinBase',
						buttonX = self.__centerX(widthTotal) + self.__scaleWidth(128),
						buttonY = self.__centerY(heightTotal) + self.__scaleHeight(450),
						buttonWidth = self.__scaleWidth(188),
						buttonHeight = self.__scaleHeight(53),

						iconPath = Icon.path('coinbase.png', type = Icon.ThemeIcon),
						iconX = self.__centerX(widthTotal) + self.__scaleWidth(131),
						iconY = self.__centerY(heightTotal) + self.__scaleHeight(450),
						iconWidth = self.__scaleWidth(53),
						iconHeight = self.__scaleHeight(53),
					)

					# EXODUS
					self.mButtonExodus = self.__button(
						buttonLabel = '       Exodus',
						buttonX = self.__centerX(widthTotal) + self.__scaleWidth(356),
						buttonY = self.__centerY(heightTotal) + self.__scaleHeight(450),
						buttonWidth = self.__scaleWidth(188),
						buttonHeight = self.__scaleHeight(53),

						iconPath = Icon.path('exodus.png', type = Icon.ThemeIcon),
						iconX = self.__centerX(widthTotal) + self.__scaleWidth(360),
						iconY = self.__centerY(heightTotal) + self.__scaleHeight(450),
						iconWidth = self.__scaleWidth(53),
						iconHeight = self.__scaleHeight(53),
					)

					# CLOSE
					self.mButtonClose = self.__button(
						buttonLabel = '       Close',
						buttonX = self.__centerX(widthTotal) + self.__scaleWidth(585),
						buttonY = self.__centerY(heightTotal) + self.__scaleHeight(450),
						buttonWidth = self.__scaleWidth(188),
						buttonHeight = self.__scaleHeight(53),

						iconPath = Icon.path('error.png', type = Icon.ThemeIcon),
						iconX = self.__centerX(widthTotal) + self.__scaleWidth(589),
						iconY = self.__centerY(heightTotal) + self.__scaleHeight(450),
						iconWidth = self.__scaleWidth(53),
						iconHeight = self.__scaleHeight(53),
					)

				except:
					tools.Logger.error()
					tools.System.openLink(tools.Settings.getString('link.donation', raw = True))
		except:
			pass
		Loader.hide()

	def __theme(self):
		theme = tools.Settings.getString('interface.theme.skin').lower()
		theme = theme.replace(' ', '').lower()
		index = theme.find('(')
		if index >= 0: theme = theme[:index]
		return theme

	def __logo(self, size = SizeMedium):
		return tools.File.joinPath(tools.System.pathResources(), 'resources', 'media', 'logo', size)

	def __name(self, force = False, size = SizeMedium):
		theme = self.__theme()
		return tools.File.joinPath(self.__logo(size), 'namecolor.png' if force or theme == 'default' or 'gaia' in theme  else 'nameglass.png')

	def __icon(self, force = False, size = SizeMedium):
		theme = self.__theme()
		return tools.File.joinPath(self.__logo(size), 'iconcolor.png' if force or theme == 'default' or 'gaia' in theme else 'iconglass.png')

	def __interface(self):
		return tools.File.joinPath(tools.System.pathResources(), 'resources', 'media', 'interface')

	def __skin(self):
		theme = self.__theme()
		addon = tools.System.pathResources() if theme == 'default' or 'gaia' in theme else tools.System.pathSkins()
		return tools.File.joinPath(addon, 'resources', 'media', 'skins', theme)

	def __scaleWidth(self, value):
		return int(self.mScaleWidth * self.mScaleWidthExtra * value)

	def __scaleHeight(self, value):
		return int(self.mScaleHeight * self.mScaleHeightExtra * value)

	def __window(self, full = True, logo = True):
		if full:
			name = 'splashfull.png'
			width = self.__scaleWidth(900)
			height = self.__scaleHeight(563)
			logoWidth = self.__scaleWidth(263)
			logoHeight = self.__scaleHeight(133)
			logoX = self.__scaleWidth(319)
			logoY = self.__scaleHeight(75)
		else:
			name = 'splashmini.png'
			width = self.__scaleWidth(525)
			height = self.__scaleHeight(315)
			logoWidth = self.__scaleWidth(370)
			logoHeight = self.__scaleHeight(188)
			logoX = self.__scaleWidth(77)
			logoY = self.__scaleHeight(64)

		x = self.__centerX(width)
		y = self.__centerY(height)

		path = tools.File.joinPath(self.__skin(), 'interface', name)
		if tools.File.exists(path):
			self.addControl(xbmcgui.ControlImage(x, y, width, height, path))

		path = tools.File.joinPath(self.__interface(), name)
		self.addControl(xbmcgui.ControlImage(x, y, width, height, path))

		if logo:
			logoX = self.__centerX(width) + logoX
			logoY = self.__centerY(height) + logoY
			path = self.__name()
			self.addControl(xbmcgui.ControlImage(logoX, logoY, logoWidth, logoHeight, path))

		return (width, height)

	def __button(self, buttonLabel, buttonX, buttonY, buttonWidth, buttonHeight, iconPath = None, iconX = None, iconY = None, iconWidth = None, iconHeight = None, infoLabel = None, infoX = None, infoY = None, infoWidth = None, infoHeight = None):
		pathNormal = tools.File.joinPath(self.__skin(), 'interface', 'buttonnormal.png')
		if not tools.File.exists(pathNormal):
			pathNormal = tools.File.joinPath(self.__interface(), 'buttonnormal.png')

		pathFocus = tools.File.joinPath(self.__skin(), 'interface', 'buttonfocus.png')
		if not tools.File.exists(pathFocus):
			pathFocus = tools.File.joinPath(self.__interface(), 'buttonfocus.png')

		buttonLabel = Format.fontBold(buttonLabel)
		self.addControl(xbmcgui.ControlButton(buttonX, buttonY, buttonWidth, buttonHeight, buttonLabel, focusTexture = pathFocus, noFocusTexture = pathNormal, alignment = Splash.FormatCenter, textColor = Splash.FormatWhite, font = 'font14'))

		if not iconPath == None:
			self.addControl(xbmcgui.ControlImage(iconX, iconY, iconWidth, iconHeight, iconPath))

		if not infoLabel == None:
			# Do not use named parameters, since it causes a crash.
			info = xbmcgui.ControlFadeLabel(infoX, infoY, infoWidth, infoHeight, 'font10', Splash.FormatWhite, Splash.FormatCenter)
			self.addControl(info)
			info.addLabel(infoLabel)

		return (buttonX, buttonY)

	def __textbox(self, x, y, width, height, label, delay = 3000, time = 4000, repeat = True, font = 'font12'):
		box = xbmcgui.ControlTextBox(x, y, width, height, textColor = Splash.FormatWhite, font = font)
		self.addControl(box)
		box.autoScroll(delay, time, repeat)
		box.setText(label)

	def __centerX(self, width):
		return int((self.mWidth - width) / 2)

	def __centerY(self, height):
		return int((self.mHeight - height) / 2)

	def __referalPremiumize(self):
		from resources.lib.extensions import debrid
		debrid.Premiumize.website(open = True)
		self.close()

	def __referalRealDebrid(self):
		from resources.lib.extensions import debrid
		debrid.RealDebrid.website(open = True)
		self.close()

	def __referalEasyNews(self):
		from resources.lib.extensions import debrid
		debrid.EasyNews.website(open = True)
		self.close()

	def __referalCoinBase(self):
		tools.Donations.coinbase(openLink = True)
		self.close()

	def __referalExodus(self):
		tools.Donations.exodus(openLink = True)
		self.close()

	def __continue(self):
		if self.mType == Splash.TypeFull:
			tools.System.openLink(tools.Settings.getString('link.website', raw = True), popup = False, front = False)
		self.close()

	def onControl(self, control):
		distances = []
		actions = []
		if self.mButtonPremiumize:
			distances.append(abs(control.getX() - self.mButtonPremiumize[0]) + abs(control.getY() - self.mButtonPremiumize[1]))
			actions.append(self.__referalPremiumize)
		if self.mButtonOffCloud:
			distances.append(abs(control.getX() - self.mButtonOffCloud[0]) + abs(control.getY() - self.mButtonOffCloud[1]))
			actions.append(self.__referalRealDebrid)
		if self.mButtonRealDebrid:
			distances.append(abs(control.getX() - self.mButtonRealDebrid[0]) + abs(control.getY() - self.mButtonRealDebrid[1]))
			actions.append(self.__referalRealDebrid)
		if self.mButtonEasyNews:
			distances.append(abs(control.getX() - self.mButtonEasyNews[0]) + abs(control.getY() - self.mButtonEasyNews[1]))
			actions.append(self.__referalEasyNews)
		if self.mButtonFreeHosters:
			distances.append(abs(control.getX() - self.mButtonFreeHosters[0]) + abs(control.getY() - self.mButtonFreeHosters[1]))
			actions.append(self.__continue)
		if self.mButtonCoinBase:
			distances.append(abs(control.getX() - self.mButtonCoinBase[0]) + abs(control.getY() - self.mButtonCoinBase[1]))
			actions.append(self.__referalCoinBase)
		if self.mButtonExodus:
			distances.append(abs(control.getX() - self.mButtonExodus[0]) + abs(control.getY() - self.mButtonExodus[1]))
			actions.append(self.__referalExodus)
		if self.mButtonClose:
			distances.append(abs(control.getX() - self.mButtonClose[0]) + abs(control.getY() - self.mButtonClose[1]))
			actions.append(self.__continue)

		smallestIndex = -1
		smallestDistance = 999999
		for i in range(len(distances)):
			if distances[i] < smallestDistance:
				smallestDistance = distances[i]
				smallestIndex = i

		if smallestIndex < 0:
			self.__continue()
		else:
			actions[smallestIndex]()

	def onAction(self, action):
		action = action.getId()
		if action < Splash.ActionsMaximum:
			if self.mButtonClose == None:
				if action in Splash.ActionsCancel or self.mType == Splash.TypeFull:
					self.__continue()
				else:
					tools.System.openLink(tools.Settings.getString('link.website', raw = True))
			else:
				self.__continue()

	@classmethod
	def popup(self, major = False, time = Duration, wait = True):
		try:
			type = tools.Settings.getInteger('general.launch.splash.type')
			if type == 4 or major:
				from resources.lib.extensions import window
				window.WindowIntro.show(wait = wait)
				return True
			else:
				if type == 1: self.popupIcon(time = time)
				elif type == 2: self.popupName(time = time)
				elif type == 3: self.popupMini(time = time)
				else: return False
				return True
		except:
			pass
		return False

	@classmethod
	def popupFull(self, wait = False):
		try:
			# So that the interface can load in the background while the splash loads.
			thread = workers.Thread(self.__popupFull)
			thread.start()
			if wait: thread.join()
		except:
			pass

	@classmethod
	def popupMini(self, time = Duration, wait = False):
		try:
			# So that the interface can load in the background while the splash loads.
			thread = workers.Thread(self.__popupMini, time)
			thread.start()
			if wait: thread.join()
		except:
			pass

	@classmethod
	def popupName(self, time = Duration, wait = False):
		try:
			# So that the interface can load in the background while the splash loads.
			thread = workers.Thread(self.__popupName, time)
			thread.start()
			if wait: thread.join()
		except:
			pass

	@classmethod
	def popupIcon(self, time = Duration, wait = False):
		try:
			# So that the interface can load in the background while the splash loads.
			thread = workers.Thread(self.__popupIcon, time)
			thread.start()
			if wait: thread.join()
		except:
			pass

	@classmethod
	def popupAbout(self, wait = False):
		try:
			# So that the interface can load in the background while the splash loads.
			thread = workers.Thread(self.__popupAbout)
			thread.start()
			if wait: thread.join()
		except:
			pass

	@classmethod
	def popupMessage(self, message, wait = False):
		try:
			# So that the interface can load in the background while the splash loads.
			thread = workers.Thread(self.__popupMessage, message)
			thread.start()
			if wait: thread.join()
		except:
			pass

	@classmethod
	def popupDonations(self, donation = None, wait = False):
		try:
			# So that the interface can load in the background while the splash loads.
			thread = workers.Thread(self.__popupDonations, donation)
			thread.start()
			if wait: thread.join()
		except:
			pass

	@classmethod
	def __popupFull(self):
		try:
			self.mSplash = Splash(Splash.TypeFull)
			self.mSplash.doModal()
		except:
			pass

	@classmethod
	def __popupMini(self, time = Duration):
		try:
			self.mSplash = Splash(Splash.TypeMini)
			self.mSplash.show()
			tools.System.sleep(time)
			self.mSplash.close()
		except:
			pass

	@classmethod
	def __popupName(self, time = Duration):
		try:
			self.mSplash = Splash(Splash.TypeName)
			self.mSplash.show()
			tools.System.sleep(time)
			self.mSplash.close()
		except:
			pass

	@classmethod
	def __popupIcon(self, time = Duration):
		try:
			self.mSplash = Splash(Splash.TypeIcon)
			self.mSplash.show()
			tools.System.sleep(time)
			self.mSplash.close()
		except:
			pass

	@classmethod
	def __popupAbout(self):
		try:
			self.mSplash = Splash(Splash.TypeAbout)
			self.mSplash.doModal()
		except:
			pass

	@classmethod
	def __popupMessage(self, message):
		try:
			self.mSplash = Splash(Splash.TypeMessage, message = message)
			self.mSplash.doModal()
		except:
			pass

	@classmethod
	def __popupDonations(self, donation = None):
		try:
			self.mSplash = Splash(Splash.TypeDonations, donation = donation)
			self.mSplash.doModal()
		except:
			pass


# Spinner loading bar
class Loader(object):

	Type = None

	@classmethod
	def type(self):
		if Loader.Type == None: Loader.Type = 'busydialognocancel' if tools.System.versionKodiNew() else 'busydialog'
		return Loader.Type

	@classmethod
	def show(self):
		xbmc.executebuiltin('ActivateWindow(%s)' % self.type())

	@classmethod
	def hide(self):
		if tools.System.versionKodiNew(): xbmc.executebuiltin('Dialog.Close(busydialognocancel)')
		xbmc.executebuiltin('Dialog.Close(busydialog)')

	@classmethod
	def visible(self):
		if tools.System.versionKodiNew() and xbmc.getCondVisibility('Window.IsActive(busydialognocancel)') == 1: return True
		return xbmc.getCondVisibility('Window.IsActive(busydialog)') == 1


# Kodi Directory Interface
class Directory(object):

	ContentAddons = 'addons'
	ContentFiles = 'files'
	ContentSongs = 'songs'
	ContentArtists = 'artists'
	ContentAlbums = 'albums'
	ContentMovies = 'movies'
	ContentShows = 'tvshows'
	ContentEpisodes = 'episodes'
	ContentMusicVideos = 'musicvideos'

	def __init__(self, content = ContentAddons, cache = True):
		self.mContent = content
		self.mHandle = tools.System.handle()
		self.mCache = cache

	# context = [{'label', 'action', 'parameters'}]
	# Optional 'command' parameter to specify a custom command instead of construction one from action and parameters.
	def add(self, label, action = None, parameters = None, context = [], folder = False, icon = None, iconDefault = None, iconSpecial = None, fanart = None):
		link = tools.System.commandPlugin(action = action, parameters = parameters, call = False)
		item = xbmcgui.ListItem(label = Translation.string(label))

		if len(context) > 0:
			contextMenu = []
			for c in context:
				contextLabel = Translation.string(c['label'])
				if 'command' in c:
					command = c['command']
				else:
					contextAction = c['action'] if 'action' in c else None
					contextParameters = c['parameters'] if 'parameters' in c else None
					command = tools.System.commandPlugin(action = contextAction, parameters = contextParameters)
				contextMenu.append((contextLabel, command))
			item.addContextMenuItems(contextMenu)

		iconIcon, iconThumb, iconPoster, iconBanner = Icon.pathAll(icon = icon, default = iconDefault, special = iconSpecial)
		item.setArt({'icon': iconIcon, 'thumb': iconThumb, 'poster': iconPoster, 'banner': iconBanner})

		if fanart == None:
			from resources.lib.modules import control
			fanart = control.addonFanart()
		item.setProperty('Fanart_Image', fanart)

		xbmcplugin.addDirectoryItem(handle = self.mHandle, url = link, listitem = item, isFolder = folder)

	def finish(self):
		xbmcplugin.setContent(self.mHandle, self.mContent)
		xbmcplugin.endOfDirectory(self.mHandle, cacheToDisc = self.mCache)

	# Clear: Clear the path history.
	@classmethod
	def refresh(self, clear = False):
		tools.System.execute('Container.Refresh')
		if clear: tools.System.execute('Container.Update(path,replace)')


class Legal(object):

	ChoiceLeft = True
	ChoiceRight = False

	@classmethod
	def _option(self, message, left, right):
		return Dialog.option(title = 35109, message = message, labelConfirm = left, labelDeny = right)

	@classmethod
	def _message(self, message):
		return Dialog.confirm(title = 35109, message = message)

	@classmethod
	def initialized(self):
		return tools.Settings.getBoolean('internal.disclaimer.initialized')

	@classmethod
	def launchInitial(self, exit = True):
		if not self.initialized():
			if self.show(exit = exit,short = True):
				tools.Settings.set('internal.disclaimer.initialized', True)
				return True
			else:
				return False
		return True

	@classmethod
	def show(self, exit = True, short = False):
		if short:
			message = Translation.string(35111) + Format.newline() + Translation.string(35112) + Format.newline() + Translation.string(35113)
			choice = self._option(message = message, left = 35116, right = 35115)
		else:
			while True:
				choice = self._option(message = 35111, left = 33743, right = 33821)
				if choice == Legal.ChoiceLeft: self._message(message = 35114)
				else: break
			while True:
				choice = self._option(message = 35112, left = 33743, right = 33821)
				if choice == Legal.ChoiceLeft: self._message(message = 35114)
				else: break
			choice = self._option(message = 35113, left = 35116, right = 35115)
		if choice == Legal.ChoiceLeft:
			tools.Settings.set('internal.disclaimer.initialized', False)
			tools.System.launchUninitialize()
			tools.System.exit()
			return False
		else:
			return True


class Player(xbmc.Player):

	def __init__ (self):
		xbmc.Player.__init__(self)

	def __del__(self):
		try: xbmc.Player.__del__(self)
		except: pass

	@classmethod
	def playNow(self, link):
		Player().play(link)


class Context(object):

	ModeNone = None
	ModeGeneric = 'generic'
	ModeItem = 'item'
	ModeStream = 'stream'

	PrefixColor = Dialog.PrefixColor
	PrefixNext = Format.font(Dialog.PrefixNext, color = PrefixColor, bold = True, translate = False)
	PrefixBack = Format.font(Dialog.PrefixBack, color = PrefixColor, bold = True, translate = False)

	Labels = {}
	LabelMenu = None
	LabelBack = None
	LabelClose = None

	EnabledTrakt = None
	EnabledOrion = None
	EnabledYoutube = None
	EnabledLibrary = None
	EnabledPresets = None
	EnabledAutoplay = None
	EnabledDownloadCloud = None
	EnabledDownloadManual = None
	EnabledDownloadCache = None
	EnabledManagerManual = None
	EnabledManagerCache = None

	def __init__(self, mode = ModeNone, items = None, source = None, metadata = None, art = None, link = None, trailer = None, label = None, title = None, year = None, season = None, episode = None, imdb = None, tmdb = None, tvdb = None, id = None, orion = None, location = None, create = None, delete = None, library = None, queue = None, watched = None, refresh = None, type = None, kids = None, loader = False):
		if loader: Loader.show()
		if not mode == self.ModeNone: self._load(mode = mode, items = items, source = source, metadata = metadata, art = art, link = link, trailer = trailer, label = label, title = title, year = year, season = season, episode = episode, imdb = imdb, tmdb = tmdb, tvdb = tvdb, id = id, orion = orion, location = location, create = create, delete = delete, library = library, queue = queue, watched = watched, refresh = refresh, type = type, kids = kids, loader = loader)

	def _load(self, mode = ModeNone, items = None, source = None, metadata = None, art = None, link = None, trailer = None, label = None, title = None, year = None, season = None, episode = None, imdb = None, tmdb = None, tvdb = None, id = None, orion = None, location = None, create = None, delete = None, library = None, queue = None, watched = None, refresh = None, type = None, kids = None, loader = False):
		self.mMode = mode
		self.mType = type
		self.mKids = kids

		if isinstance(items, basestring): items = tools.Converter.jsonFrom(items)
		self.mItems = items if items else []
		self.mData = None

		if isinstance(source, dict): source = tools.Converter.quoteTo(tools.Converter.jsonTo(source))
		self.mSource = source

		if isinstance(metadata, dict): metadata = tools.Converter.quoteTo(tools.Converter.jsonTo(metadata))
		self.mMetadata = metadata

		if isinstance(art, dict): art = tools.Converter.quoteTo(tools.Converter.jsonTo(art))
		self.mArt = art

		if isinstance(orion, dict): orion = tools.Converter.quoteTo(tools.Converter.jsonTo(orion))
		self.mOrion = orion

		self.mLink = tools.Converter.quoteTo(link) # Important to quote (for scrape options, shortcuts, etc).
		self.mTrailer = trailer
		self.mLabel = label
		self.mTitle = title
		self.mYear = year
		self.mSeason = season
		self.mEpisode = episode
		self.mImdb = imdb
		self.mTmdb = tmdb
		self.mTvdb = tvdb

		self.mId = id
		self.mLocation = location
		self.mCreate = create
		self.mDelete = delete
		self.mLibrary = library
		self.mQueue = queue
		self.mWatched = watched
		self.mRefresh = refresh

		self._initialize()
		if len(self.mItems) == 0:
			if self.mMode == Context.ModeGeneric: self.addGeneric()
			elif self.mMode == Context.ModeItem: self.addItem()
			elif self.mMode == Context.ModeStream: self.addStream()

	def _initialize(self):
		if Context.LabelMenu == None:
			from resources.lib.extensions import downloader
			from resources.lib.extensions import orionoid
			from resources.lib.extensions import debrid
			Context.LabelMenu = self._label(tools.System.name(), next = True, color = True)
			Context.LabelBack = self._labelBack()
			Context.LabelClose = self._labelClose()
			Context.EnabledTrakt = tools.Trakt.accountEnabled()
			Context.EnabledOrion = orionoid.Orionoid().accountEnabled()
			Context.EnabledYoutube = tools.YouTube.installed()
			Context.EnabledLibrary = tools.Settings.getBoolean('library.enabled')
			Context.EnabledPresets = tools.Settings.getBoolean('providers.customization.presets.enabled')
			Context.EnabledAutoplay = tools.Settings.getBoolean('automatic.enabled')
			Context.EnabledDownloadCloud = debrid.Debrid.enabled()
			Context.EnabledDownloadManual = tools.Settings.getBoolean('downloads.manual.enabled')
			Context.EnabledDownloadCache = tools.Settings.getBoolean('downloads.cache.enabled')
			Context.EnabledManagerManual = not(self.mKids == tools.Selection.TypeInclude) and Context.EnabledDownloadManual
			Context.EnabledManagerCache = not(self.mKids == tools.Selection.TypeInclude) and Context.EnabledDownloadCache

	@classmethod
	def _translate(self, label, replace = None):
		if isinstance(label, basestring):
			result = label
		else:
			if not label in Context.Labels: Context.Labels[label] = Translation.string(label)
			result = Context.Labels[label]
		if not replace == None: result = result % self._translate(replace)
		return result

	@classmethod
	def _label(self, label, next, color):
		if color == True: color = Context.PrefixColor
		elif color == False: color = None
		return (Context.PrefixNext if next else Context.PrefixBack) + Format.font(label, bold = True, color = color)

	@classmethod
	def _labelNext(self, label):
		return self._label(label = label, next = True, color = False)

	@classmethod
	def _labelBack(self):
		return self._label(label = 35374, next = False, color = True)

	@classmethod
	def _labelClose(self):
		return self._label(label = 33486, next = False, color = True)

	def _labelItem(self):
		if self.mLabel: return self.mLabel
		else: return tools.Media.title(type = self.mType, title = self.mTitle, year = self.mYear, season = self.mSeason, episode = self.mEpisode)

	@classmethod
	def _close(self):
		from resources.lib.extensions import window
		window.WindowStreams.close()

	def _command(self, parameters = {}):
		if not self.mType == None: parameters['type'] = self.mType
		if not self.mKids == None: parameters['kids'] = self.mKids
		return dict((key, value) for key, value in parameters.iteritems() if not value is None)

	def _commandPlugin(self, action, parameters = {}, basic = True):
		return tools.System.commandPlugin(action = action, parameters = self._command(parameters), basic = basic)

	def _commandContainer(self, action, parameters = {}, basic = True):
		return tools.System.commandContainer(action = action, parameters = self._command(parameters), basic = basic)

	def jsonTo(self, force = False):
		# NB: Do not create full commands for each action in the context menu.
		# NB: If mutiple actions contain the source/metadata attribute, the context menu JSON can become very large and can take very long to generate.
		# NB: Instead, create a barebone context menu and append all parameters ONCE. The plugin commands are then dymaically created ONLY if they are called.
		if force or self.mData == None:
			self.mData = {
				'mode' : self.mMode,

				'items' : self.mItems,
				'source' : self.mSource,
				'metadata' : self.mMetadata,
				'art' : self.mArt,
				'orion' : self.mOrion,

				'link' : tools.Converter.quoteFrom(self.mLink), # Unquote, since it is quoted in constructor.
				'trailer' : self.mTrailer,
				'label' : self.mLabel,
				'title' : self.mTitle,
				'year' : self.mYear,
				'season' : self.mSeason,
				'episode' : self.mEpisode,
				'imdb' : self.mImdb,
				'tmdb' : self.mTmdb,
				'tvdb' : self.mTvdb,

				'id' : self.mId,
				'location' : self.mLocation,
				'create' : self.mCreate,
				'delete' : self.mDelete,
				'library' : self.mLibrary,
				'queue' : self.mQueue,
				'watched' : self.mWatched,
				'refresh' : self.mRefresh,
			}
			self.mData = tools.Converter.quoteTo(tools.Converter.jsonTo(self._command(self.mData)))
		return self.mData

	def jsonFrom(self, data):
		if isinstance(data, basestring): data = tools.Converter.jsonFrom(data)
		self._load(**data)

	def menu(self):
		return (Context.LabelMenu, self._commandPlugin(action = 'contextShow', parameters = {'context' : self.jsonTo()}))

	def commandInformationStream(self):
		return self._commandPlugin(action = 'streamsInformation', parameters = {'source' : self.mSource, 'metadata' : self.mMetadata})

	def commandInformationMovie(self):
		return self._commandPlugin(action = 'informationDialog', parameters = {'imdb' : self.mImdb})

	def commandInformationShow(self):
		return self._commandPlugin(action = 'informationDialog', parameters = {'imdb' : self.mImdb, 'tvdb' : self.mTvdb, 'title' : self.mTitle})

	def commandInformationSeason(self):
		return self._commandPlugin(action = 'informationDialog', parameters = {'imdb' : self.mImdb, 'tvdb' : self.mTvdb, 'title' : self.mTitle, 'season' : self.mSeason})

	def commandInformationEpisode(self):
		return self._commandPlugin(action = 'informationDialog', parameters = {'imdb' : self.mImdb, 'tvdb' : self.mTvdb, 'title' : self.mTitle, 'season' : self.mSeason, 'episode' : self.mEpisode})

	def commandFilters(self):
		return self._commandPlugin(action = 'streamsFilter')

	def commandMarkEpisodeWatch(self):
		return self._commandPlugin(action = 'episodesWatch', parameters = {'imdb' : self.mImdb, 'tvdb' : self.mTvdb, 'title' : self.mTitle, 'season' : self.mSeason, 'episode' : self.mEpisode})

	def commandMarkEpisodeUnwatch(self):
		return self._commandPlugin(action = 'episodesUnwatch', parameters = {'imdb' : self.mImdb, 'tvdb' : self.mTvdb, 'title' : self.mTitle, 'season' : self.mSeason, 'episode' : self.mEpisode})

	def commandMarkSeasonWatch(self):
		return self._commandPlugin(action = 'seasonsWatch', parameters = {'imdb' : self.mImdb, 'tvdb' : self.mTvdb, 'title' : self.mTitle, 'season' : self.mSeason, 'episode' : self.mEpisode})

	def commandMarSeasonUnwatch(self):
		return self._commandPlugin(action = 'seasonsUnwatch', parameters = {'imdb' : self.mImdb, 'tvdb' : self.mTvdb, 'title' : self.mTitle, 'season' : self.mSeason, 'episode' : self.mEpisode})

	def commandMarkShowWatch(self):
		return self._commandPlugin(action = 'showsWatch', parameters = {'imdb' : self.mImdb, 'tvdb' : self.mTvdb, 'title' : self.mTitle, 'season' : self.mSeason, 'episode' : self.mEpisode})

	def commandMarkShowUnwatch(self):
		return self._commandPlugin(action = 'showsUnwatch', parameters = {'imdb' : self.mImdb, 'tvdb' : self.mTvdb, 'title' : self.mTitle, 'season' : self.mSeason, 'episode' : self.mEpisode})

	def commandMarkMovieWatch(self):
		return self._commandPlugin(action = 'moviesWatch', parameters = {'imdb' : self.mImdb})

	def commandMarkMovieUnwatch(self):
		return self._commandPlugin(action = 'moviesUnwatch', parameters = {'imdb' : self.mImdb})

	def commandScrapeManual(self):
		return self._commandPlugin(action = 'scrapeManual', parameters = {'link' : self.mLink})

	def commandScrapeAutomatic(self):
		return self._commandPlugin(action = 'scrapeAutomatic', parameters = {'link' : self.mLink})

	def commandScrapePreset(self):
		return self._commandPlugin(action = 'scrapePreset', parameters = {'link' : self.mLink})

	def commandPlaylistShow(self):
		return self._commandPlugin(action = 'playlistShow')

	def commandPlaylistClear(self):
		return self._commandPlugin(action = 'playlistClear')

	def commandPlaylistAdd(self):
		return self._commandPlugin(action = 'playlistAdd', parameters = {'link' : self.mLink, 'label' : self._labelItem(), 'metadata' : self.mMetadata, 'art' : self.mArt, 'context' : self.jsonTo()})

	def commandPlaylistRemove(self):
		return self._commandPlugin(action = 'playlistRemove', parameters = {'label' : label})

	def commandTrailer(self):
		return self._commandContainer(action = 'streamsTrailer', parameters = {'title' : self.mTrailer, 'imdb' : self.mImdb})

	def commandRefresh(self):
		return self._commandContainer(action = 'navigatorRefresh')

	def commandBrowse(self):
		return self._commandContainer(action = 'seasonsRetrieve', parameters = {'tvshowtitle' : self.mTitle, 'year' : self.mYear, 'imdb' : self.mImdb, 'tvdb' : self.mTvdb})

	def commandDownloadsCloud(self):
		return self._commandContainer(action = 'downloadCloud', parameters = {'source' : self.mSource})

	def commandDownloadsManual(self):
		from resources.lib.extensions import downloader
		return self._commandContainer(action = 'downloadsManager', parameters = {'downloadType' : downloader.Downloader.TypeManual})

	def commandDownloadsCache(self):
		from resources.lib.extensions import downloader
		return self._commandContainer(action = 'downloadsManager', parameters = {'downloadType' : downloader.Downloader.TypeCache})

	def commandManualDefault(self):
		from resources.lib.extensions import handler
		from resources.lib.extensions import downloader
		try: poster = tools.Converter.jsonFrom(tools.Converter.quoteFrom(self.mArt))['poster']
		except: poster = None
		return self._commandPlugin(action = 'download', parameters = {'downloadType' : downloader.Downloader.TypeManual, 'handleMode' : handler.Handler.ModeDefault, 'image' : poster, 'source' : self.mSource, 'metadata' : self.mMetadata})

	def commandManualSelection(self):
		from resources.lib.extensions import handler
		from resources.lib.extensions import downloader
		try: poster = tools.Converter.jsonFrom(tools.Converter.quoteFrom(self.mArt))['poster']
		except: poster = None
		return self._commandPlugin(action = 'download', parameters = {'downloadType' : downloader.Downloader.TypeManual, 'handleMode' : handler.Handler.ModeSelection, 'image' : poster, 'source' : self.mSource, 'metadata' : self.mMetadata})

	def commandManualFile(self):
		from resources.lib.extensions import handler
		from resources.lib.extensions import downloader
		try: poster = tools.Converter.jsonFrom(tools.Converter.quoteFrom(self.mArt))['poster']
		except: poster = None
		return self._commandPlugin(action = 'download', parameters = {'downloadType' : downloader.Downloader.TypeManual, 'handleMode' : handler.Handler.ModeFile, 'image' : poster, 'source' : self.mSource, 'metadata' : self.mMetadata})

	def commandManualManager(self):
		from resources.lib.extensions import downloader
		return self._commandContainer(action = 'downloadsManager', parameters = {'downloadType' : downloader.Downloader.TypeManual})

	def commandCacheDefault(self):
		from resources.lib.extensions import handler
		from resources.lib.extensions import downloader
		return self._commandPlugin(action = 'playCache', parameters = {'handleMode' : handler.Handler.ModeDefault, 'source' : self.mSource, 'metadata' : self.mMetadata})

	def commandCacheSelection(self):
		from resources.lib.extensions import handler
		return self._commandPlugin(action = 'playCache', parameters = {'handleMode' : handler.Handler.ModeSelection, 'source' : self.mSource, 'metadata' : self.mMetadata})

	def commandCacheFile(self):
		from resources.lib.extensions import handler
		return self._commandPlugin(action = 'playCache', parameters = {'handleMode' : handler.Handler.ModeFile, 'source' : self.mSource, 'metadata' : self.mMetadata})

	def commandCacheManager(self):
		from resources.lib.extensions import downloader
		return self._commandContainer(action = 'downloadsManager', parameters = {'downloadType' : downloader.Downloader.TypeCache})

	def commandPlayDefault(self):
		from resources.lib.extensions import handler
		return self._commandPlugin(action = 'play', parameters = {'handleMode' : handler.Handler.ModeDefault, 'source' : self.mSource, 'metadata' : self.mMetadata})

	def commandPlaySelection(self):
		from resources.lib.extensions import handler
		return self._commandPlugin(action = 'play', parameters = {'handleMode' : handler.Handler.ModeSelection, 'source' : self.mSource, 'metadata' : self.mMetadata})

	def commandPlayFile(self):
		from resources.lib.extensions import handler
		return self._commandPlugin(action = 'play', parameters = {'handleMode' : handler.Handler.ModeFile, 'source' : self.mSource, 'metadata' : self.mMetadata})

	def commandLinkCopy(self):
		return self._commandPlugin(action = 'linkCopy', parameters = {'source' : self.mSource})

	def commandLinkOpen(self):
		return self._commandPlugin(action = 'linkOpen', parameters = {'source' : self.mSource})

	def commandLinkAdd(self):
		return self._commandPlugin(action = 'linkAdd')

	def commandShortcutCreate(self):
		return self._commandPlugin(action = 'shortcutsShow', parameters = {'link' : self.mLink, 'name' : self.mTitle, 'create' : True})

	def commandShortcutDelete(self):
		return self._commandPlugin(action = 'shortcutsShow', parameters = {'id' : self.mId, 'location' : self.mLocation, 'delete' : True})

	def commandTrakt(self):
		return self._commandPlugin(action = 'traktManager', parameters = {'refresh' : not self.mMode == Context.ModeStream, 'season' : self.mSeason, 'episode' : self.mEpisode, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb})

	def commandOrionVoteUp(self):
		orion = tools.Converter.jsonFrom(tools.Converter.quoteFrom(self.mOrion))
		return self._commandPlugin(action = 'orionVoteUp', parameters = {'idItem' : orion['item'], 'idStream' : orion['stream']})

	def commandOrionVoteDown(self):
		orion = tools.Converter.jsonFrom(tools.Converter.quoteFrom(self.mOrion))
		return self._commandPlugin(action = 'orionVoteDown', parameters = {'idItem' : orion['item'], 'idStream' : orion['stream']})

	def commandOrionRemove(self):
		orion = tools.Converter.jsonFrom(tools.Converter.quoteFrom(self.mOrion))
		return self._commandPlugin(action = 'orionRemove', parameters = {'idItem' : orion['item'], 'idStream' : orion['stream']})

	def commandLibraryAddDirect(self):
		return self._commandPlugin(action = 'libraryAdd', parameters = {'link' : self.mLibrary})

	def commandLibraryAddStream(self):
		return self._commandPlugin(action = 'libraryAdd', parameters = {'link' : self.mLink, 'title' : self.mTitle, 'year' : self.mYear, 'season' : self.mSeason, 'episode' : self.mEpisode, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'metadata' : self.mMetadata})

	def commandLibraryAddMovie(self):
		return self._commandPlugin(action = 'libraryAdd', parameters = {'title' : self.mTitle, 'year' : self.mYear, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'metadata' : self.mMetadata})

	def commandLibraryAddEpisode(self):
		return self._commandPlugin(action = 'libraryAdd', parameters = {'title' : self.mTitle, 'year' : self.mYear, 'season' : self.mSeason, 'episode' : self.mEpisode, 'imdb' : self.mImdb, 'tvdb' : self.mTvdb, 'metadata' : self.mMetadata})

	def commandLibraryAddSeason(self):
		return self._commandPlugin(action = 'libraryAdd', parameters = {'title' : self.mTitle, 'year' : self.mYear, 'season' : self.mSeason, 'imdb' : self.mImdb, 'tvdb' : self.mTvdb, 'metadata' : self.mMetadata})

	def commandLibraryAddShow(self):
		return self._commandPlugin(action = 'libraryAdd', parameters = {'title' : self.mTitle, 'year' : self.mYear, 'imdb' : self.mImdb, 'tvdb' : self.mTvdb, 'metadata' : self.mMetadata})

	def commandLibraryUpdate(self):
		return self._commandPlugin(action = 'libraryUpdate', parameters = {'force' : True})

	def add(self, label, action = None, command = None, condition = None, loader = None, items = None):
		item = {'label' : self._translate(label)}
		if action: item['action'] = action
		if command: item['command'] = command
		if condition: item['condition'] = condition
		if loader: item['loader'] = loader
		if items: item['items'] = [i for i in items if i]
		self.mItems.append(item)

	def addGeneric(self):
		self.addLibrary()
		self.addPlaylist()
		self.addShortcut()

	def addItem(self):
		self.addInformation()
		self.addTrailer()
		self.addRefresh()
		self.addBrowse()
		self.addScrape()
		self.addMark()
		self.addTrakt()
		self.addLibrary()
		self.addPlaylist()
		self.addShortcut()
		self.addDownloads()

	def addStream(self):
		self.addInformation()
		self.addFilters()
		self.addCache()
		self.addPlay()
		self.addLink()
		self.addMark()
		self.addTrakt()
		self.addOrion()
		self.addLibrary()
		self.addPlaylist()
		self.addShortcut()
		self.addManual()

	def addInformation(self):
		items = []
		if not self.mEpisode == None: items.insert(0, {'label' : 35509, 'command' : 'commandInformationEpisode', 'loader' : True})
		if not self.mSeason == None: items.insert(0, {'label' : 35508, 'command' : 'commandInformationSeason', 'loader' : True})
		if not self.mTvdb == None: items.insert(0, {'label' : 35507, 'command' : 'commandInformationShow', 'loader' : True})
		if not self.mImdb == None and self.mTvdb == None and self.mSeason == None and self.mEpisode == None: items.insert(0, {'label' : 35506, 'command' : 'commandInformationMovie', 'loader' : True})
		if self.mMode == Context.ModeStream: items.insert(0, {'label' : 33415, 'command' : 'commandInformationStream', 'loader' : True})
		self.add(label = 33344, items = items)

	def addFilters(self):
		self.add(label = 35477, command = 'commandFilters', loader = True)

	def addMark(self):
		items = []
		if tools.Media.typeTelevision(self.mType):
			if not self.mSeason == None and not self.mEpisode == None:
				actionWatch = 'commandMarkEpisodeWatch'
				actionUnwatch = 'commandMarkEpisodeUnwatch'
			elif not self.mSeason == None:
				actionWatch = 'commandMarkSeasonWatch'
				actionUnwatch = 'commandMarSeasonUnwatch'
			else:
				actionWatch = 'commandMarkShowWatch'
				actionUnwatch = 'commandMarkShowUnwatch'
			if self.mEpisode == None or not self.mWatched: items.append({'label' : 33651, 'command' : actionWatch})
			if self.mEpisode == None or self.mWatched: items.append({'label' : 33652, 'command' : actionUnwatch})
		else:
			if self.mWatched: items.append({'label' : 33652, 'command' : 'commandMarkMovieUnwatch'})
			else: items.append({'label' : 33651, 'command' : 'commandMarkMovieWatch'})
		self.add(label = 35512, items = items)

	def addScrape(self):
		if self.mTvdb == None or not self.mEpisode == None:
			self.add(label = 35514, items = [
				{'label' : 35522, 'command' : 'commandScrapeManual', 'loader' : True},
				{'label' : 35523, 'command' : 'commandScrapeAutomatic', 'condition' : 'Context.EnabledAutoplay', 'loader' : True},
				{'label' : 35524, 'command' : 'commandScrapePreset', 'condition' : 'Context.EnabledPresets', 'loader' : True},
			])

	def addPlaylist(self):
		# NB: Do not add the custom context menu to items in the playlist.
		# NB: This requires additional JSON and URL encodings and the entire context menu must be added as a parameter to the main context menu, increasing the size of the plugin command.
		# NB: More importantly, it drastically increases the time in takes to generate context menus, epsecially for lists with a lot of streams.
		# NB: Bad luck, playlist items have to work without a context menu.
		label = self._labelItem() if self.mQueue else None
		self.add(label = 35515, items = [
			{'label' : 35517, 'command' : 'commandPlaylistShow', 'close' : True},
			{'label' : 35516, 'command' : 'commandPlaylistClear', 'condition' : 'not tools.Playlist.empty()'},
			{'label' : 32065, 'command' : 'commandPlaylistAdd', 'condition' : 'not tools.Playlist.contains("%s")' % label} if self.mQueue else None,
			{'label' : 35518, 'command' : 'commandPlaylistRemove', 'condition' : 'tools.Playlist.contains("%s")' % label} if self.mQueue else None,
		])

	def addTrailer(self):
		if Context.EnabledYoutube or not tools.Media.typeTelevision(self.mType):
			self.add(label = 35536, command = 'commandTrailer', loader = True)

	def addRefresh(self):
		if self.mRefresh:
			self.add(label = 32072, command = 'commandRefresh', loader = True)

	def addBrowse(self):
		if not self.mEpisode == None:
			self.add(label = 32071, command = 'commandBrowse')

	def addDownloads(self):
		self.add(label = 32009, items = [
			{'label' : 33585, 'command' : 'commandDownloadsManual', 'close' : True, 'condition' : 'Context.EnabledDownloadManual and Context.EnabledManagerManual'},
			{'label' : 35499, 'command' : 'commandDownloadsCache', 'close' : True, 'condition' : 'Context.EnabledDownloadCache and Context.EnabledManagerCache'},
		])

	def addManual(self):
		self.add(label = 33051, items = [
			{'label' : 35472, 'command' : 'commandManualDefault', 'condition' : 'Context.EnabledDownloadManual'},
			{'label' : 33562, 'command' : 'commandManualSelection', 'condition' : 'Context.EnabledDownloadManual'},
			{'label' : 35154, 'command' : 'commandManualFile', 'condition' : 'Context.EnabledDownloadManual'},
			{'label' : 33229, 'command' : 'commandDownloadsCloud', 'condition' : 'Context.EnabledDownloadCloud'},
			{'label' : 33585, 'command' : 'commandManualManager', 'close' : True, 'condition' : 'Context.EnabledDownloadManual and Context.EnabledManagerManual', 'loader' : True},
		])

	def addCache(self):
		self.add(label = 33016, items = [
			{'label' : 35471, 'command' : 'commandCacheDefault', 'condition' : 'Context.EnabledDownloadCache'},
			{'label' : 33563, 'command' : 'commandCacheSelection', 'condition' : 'Context.EnabledDownloadCache'},
			{'label' : 35544, 'command' : 'commandCacheFile', 'condition' : 'Context.EnabledDownloadCache'},
			{'label' : 35499, 'command' : 'commandCacheManager', 'close' : True, 'condition' : 'Context.EnabledDownloadCache and Context.EnabledManagerCache', 'loader' : True},
		])

	def addPlay(self):
		self.add(label = 35470, items = [
			{'label' : 35378, 'command' : 'commandPlayDefault'},
			{'label' : 33561, 'command' : 'commandPlaySelection'},
			{'label' : 35543, 'command' : 'commandPlayFile'},
		])

	def addLink(self):
		self.add(label = 33381, items = [
			{'label' : 33031, 'command' : 'commandLinkCopy'},
			{'label' : 35085, 'command' : 'commandLinkOpen'},
			{'label' : 35434, 'command' : 'commandLinkAdd', 'close' : True},
		])

	def addShortcut(self):
		if self.mCreate: self.add(label = 35119, command = 'commandShortcutCreate', loader = True)
		elif self.mDelete: self.add(label = 35119, command = 'commandShortcutDelete', loader = True)

	def addTrakt(self):
		self.add(label = 32315, command = 'commandTrakt', condition = 'Context.EnabledTrakt', loader = True)

	def addOrion(self):
		if Context.EnabledOrion and self.mOrion:
			self.add(label = 35400, items = [
				{'label' : 35527, 'command' : 'commandOrionVoteUp'},
				{'label' : 35528, 'command' : 'commandOrionVoteDown'},
				{'label' : 35529, 'command' : 'commandOrionRemove'},
			])

	def addLibrary(self):
		items = []
		if not self.mLibrary == None:
			items.append({'label' : self._translate(35495, 32515), 'command' : 'commandLibraryAddDirect', 'condition' : 'Context.EnabledLibrary'})
		elif self.mMode == Context.ModeStream and not self.mLink == None:
			items.append({'label' : self._translate(35495, 33071), 'command' : 'commandLibraryAddStream', 'condition' : 'Context.EnabledLibrary'})
		if tools.Media.typeMovie(self.mType) and (not self.mImdb == None or not self.mTmdb == None):
			items.append({'label' : self._translate(35495, 35497 if self.mType == tools.Media.TypeDocumentary else 35110  if self.mType == tools.Media.TypeShort else 35496), 'command' : 'commandLibraryAddMovie', 'condition' : 'Context.EnabledLibrary'})
		if tools.Media.typeTelevision(self.mType) and (not self.mImdb == None or not self.mTvdb == None):
			if not self.mSeason == None and not self.mEpisode == None:
				items.append({'label' : self._translate(35495, 33028), 'command' : 'commandLibraryAddEpisode', 'condition' : 'Context.EnabledLibrary'})
			if not self.mSeason == None:
				items.append({'label' : self._translate(35495, 32055), 'command' : 'commandLibraryAddSeason', 'condition' : 'Context.EnabledLibrary'})
			items.append({'label' : self._translate(35495, 35498), 'command' : 'commandLibraryAddShow', 'condition' : 'Context.EnabledLibrary'})
		items.append({'label' : self._translate(35493), 'command' : 'commandLibraryUpdate', 'condition' : 'Context.EnabledLibrary'})
		self.add(label = 35170, items = items)

	def show(self, wait = False):
		# Start in a background thread, so that the underlying window/dialog can be closed and reopened.
		# The context menu is therefore not depended on the parent window.
		thread = threading.Thread(target = self._show)
		thread.start()
		if wait: thread.join()

	def _condition(self, item):
		if 'condition' in item:
			exec('result = ' + item['condition'])
			return result
		else:
			return True

	def _filter(self, items):
		items = [i for i in items if self._condition(i)]
		items = [i for i in items if not 'items' in i or len(self._filter(i['items'])) > 0]
		return items

	def _show(self):
		Loader.hide()
		items = [i for i in self.mItems if i]
		choices = []
		while True:
			index = len(choices)
			sub = index > 0

			item = items
			item = self._filter(item)
			for i in choices: item = item[i]['items']
			item = self._filter(item)

			labels = [self._labelNext(i['label']) for i in item]
			if sub: labels.insert(0, Context.LabelBack)
			else: labels.insert(0, Context.LabelClose)
			choice = Dialog.context(labels = labels)

			if choice < 0 or (not sub and choice == 0):
				break
			elif sub and choice == 0:
				choices = choices[:-1]
				continue
			else:
				choice -= 1
				menu = item[choice]
				if 'items' in menu:
					choices.append(choice)
					continue
				else:
					if 'command' in menu and menu['command']:
						if 'loader' in menu and menu['loader']: Loader.show()
						tools.System.execute(getattr(self, menu['command'])())
					if 'close' in menu and menu['close']: self._close()
					break


class Filters(object):

	FilterRemovalDuplicates = 'GaiaFilterRemovalDuplicates'
	FilterRemovalUnsupported = 'GaiaFilterRemovalUnsupported'

	FilterSortQuality = 'GaiaFilterSortQuality'
	FilterSortPrimary = 'GaiaFilterSortPrimary'
	FilterSortSize = 'GaiaFilterSortSize'
	FilterSortAge = 'GaiaFilterSortAge'
	FilterSortSeeds = 'GaiaFilterSortSeeds'
	FilterSortPopularity = 'GaiaFilterSortPopularity'

	FilterProviderService = 'GaiaFilterProviderService'
	FilterProviderSelection = 'GaiaFilterProviderSelection'
	FilterProviderAge = 'GaiaFilterProviderAge'
	FilterProviderSeeds = 'GaiaFilterProviderSeeds'
	FilterProviderPopularity = 'GaiaFilterProviderPopularity'
	FilterProviderCacheTorrent = 'GaiaFilterProviderCacheTorrent'
	FilterProviderCacheUsenet = 'GaiaFilterProviderCacheUsenet'
	FilterProviderCacheHoster = 'GaiaFilterProviderCacheHoster'

	FilterFileNameInclude = 'GaiaFilterFileNameInclude'
	FilterFileNameExclude = 'GaiaFilterFileNameExclude'
	FilterFileSizeMinimum = 'GaiaFilterFileSizeMinimum'
	FilterFileSizeMaximum = 'GaiaFilterFileSizeMaximum'

	FilterVideoQualityMinimum = 'GaiaFilterVideoQualityMinimum'
	FilterVideoQualityMaximum = 'GaiaFilterVideoQualityMaximum'
	FilterVideoCodec = 'GaiaFilterVideoCodec'
	FilterVideo3D = 'GaiaFilterVideo3D'

	FilterAudioChannels = 'GaiaFilterAudioChannels'
	FilterAudioCodec = 'GaiaFilterAudioCodec'
	FilterAudioLanguage = 'GaiaFilterAudioLanguage'
	FilterAudioDubbed = 'GaiaFilterAudioDubbed'

	FilterSubtitlesSoft = 'GaiaFilterSubtitlesSoft'
	FilterSubtitlesHard = 'GaiaFilterSubtitlesHard'

	Filters = [
		FilterRemovalDuplicates, FilterRemovalUnsupported,
		FilterSortQuality, FilterSortPrimary, FilterSortSize, FilterSortAge, FilterSortSeeds, FilterSortPopularity,
		FilterProviderService, FilterProviderSelection, FilterProviderAge, FilterProviderSeeds, FilterProviderPopularity, FilterProviderCacheTorrent, FilterProviderCacheUsenet, FilterProviderCacheHoster,
		FilterFileNameInclude, FilterFileNameExclude, FilterFileSizeMinimum, FilterFileSizeMaximum,
		FilterVideoQualityMinimum, FilterVideoQualityMaximum, FilterVideoCodec, FilterVideo3D,
		FilterAudioChannels, FilterAudioCodec, FilterAudioLanguage, FilterAudioDubbed,
		FilterSubtitlesSoft, FilterSubtitlesHard,
	]

	@classmethod
	def show(self):
		Loader.hide()
		Dialog.information(title = 35477, items = self._items(), refresh = self._items)

	@classmethod
	def _items(self):
		return [
			{'title' : Dialog.prefixBack(33486), 'close' : True},
			{'title' : Dialog.prefixNext(35478), 'action' : self._reload, 'close' : True},
			{'title' : Dialog.prefixNext(35479), 'action' : self._reset, 'close' : True},
			{'title' : Dialog.prefixNext(33013), 'action' : self._clear, 'close' : True},

			{'title' : 35480, 'items' : [
				{'title' : 35450, 'value' : self.removalDuplicates(label = True), 'action' : self._removalDuplicates},
				{'title' : 35451, 'value' : self.removalUnsupported(label = True), 'action' : self._removalUnsupported},
			]},

			{'title' : 33678, 'items' : [
				{'title' : 33764, 'value' : self.sortQuality(label = True), 'action' : self._sortQuality},
				{'title' : 35402, 'value' : self.sortPrimary(label = True), 'action' : self._sortPrimary},
				{'title' : 35457, 'value' : self.sortSize(label = True), 'action' : self._sortSize},
				{'title' : 35225, 'value' : self.sortAge(label = True), 'action' : self._sortAge},
				{'title' : 35224, 'value' : self.sortSeeds(label = True), 'action' : self._sortSeeds},
				{'title' : 35404, 'value' : self.sortPopularity(label = True), 'action' : self._sortPopularity},
			]},

			{'title' : 33194, 'items' : [
				{'title' : 33205, 'value' : self.providerService(label = True), 'action' : self._providerService},
				{'title' : 33197, 'value' : self.providerSelection(label = True), 'action' : self._providerSelection},
				{'title' : 33136, 'value' : self.providerAge(label = True), 'action' : self._providerAge},
				{'title' : 33135, 'value' : self.providerSeeds(label = True), 'action' : self._providerSeeds},
				{'title' : 35491, 'value' : self.providerPopularity(label = True), 'action' : self._providerPopularity},
				{'title' : 33464, 'value' : self.providerCacheTorrent(label = True), 'action' : self._providerCacheTorrent},
				{'title' : 33465, 'value' : self.providerCacheUsenet(label = True), 'action' : self._providerCacheUsenet},
				{'title' : 35054, 'value' : self.providerCacheHoster(label = True), 'action' : self._providerCacheHoster},
			]},

			{'title' : 35481, 'items' : [
				{'title' : 35482, 'value' : self.fileNameInclude(label = True), 'action' : self._fileNameInclude},
				{'title' : 35483, 'value' : self.fileNameExclude(label = True), 'action' : self._fileNameExclude},
				{'title' : 35304, 'value' : self.fileSizeMinimum(label = True), 'action' : self._fileSizeMinimum},
				{'title' : 35305, 'value' : self.fileSizeMaximum(label = True), 'action' : self._fileSizeMaximum},
			]},

			{'title' : 33120, 'items' : [
				{'title' : 33125, 'value' : self.videoQualityMinimum(label = True), 'action' : self._videoQualityMinimum},
				{'title' : 33126, 'value' : self.videoQualityMaximum(label = True), 'action' : self._videoQualityMaximum},
				{'title' : 33127, 'value' : self.videoCodec(label = True), 'action' : self._videoCodec},
				{'title' : 33128, 'value' : self.video3D(label = True), 'action' : self._video3D},
			]},

			{'title' : 33121, 'items' : [
				{'title' : 33129, 'value' : self.audioChannels(label = True), 'action' : self._audioChannels},
				{'title' : 33130, 'value' : self.audioCodec(label = True), 'action' : self._audioCodec},
				{'title' : 35038, 'value' : self.audioLanguage(label = True), 'action' : self._audioLanguage},
				{'title' : 35161, 'value' : self.audioDubbed(label = True), 'action' : self._audioDubbed},
			]},

			{'title' : 33122, 'items' : [
				{'title' : 33131, 'value' : self.subtitlesSoft(label = True), 'action' : self._subtitlesSoft},
				{'title' : 33132, 'value' : self.subtitlesHard(label = True), 'action' : self._subtitlesHard},
			]},
		]

	@classmethod
	def filter(self, id, value = None, empty = False):
		from resources.lib.extensions import window
		if value == None:
			result = window.Window.propertyGlobal(id)
			if not empty and result == '': result = None
			return result
		else:
			return window.Window.propertyGlobalSet(id, value)

	@classmethod
	def clear(self):
		from resources.lib.extensions import window
		for i in self.Filters:
			window.Window.propertyGlobalClear(i)

	@classmethod
	def _clear(self):
		self._reload(filter = False)

	@classmethod
	def _reload(self, filter = True):
		from resources.lib.extensions import core
		core.Core().showStreams(filter = filter)

	@classmethod
	def _reset(self):
		self.clear()
		self._reload()

	@classmethod
	def _itemList(self, items, index = None):
		result = [Translation.string(i) for i in items]
		if not index == None: result = result[index]
		return result

	@classmethod
	def _itemListBoolean(self, index = None):
		return self._itemList(items = [33342, 33341], index = index)

	@classmethod
	def _itemListInclude(self, index = None):
		return self._itemList(items = [33114, 33115, 33116], index = index)

	@classmethod
	def _itemSelection(self, filter, items, value = None, label = None):
		result = self.filter(filter, value)
		if not result == None: result = int(result)
		if label: result = None if result == None else items(result)
		return result

	@classmethod
	def _itemDialog(self, title, items, function):
		choice = Dialog.options(title = title, items = items(), selection = function())
		if choice >= 0: function(value = choice)

	@classmethod
	def _textDialog(self, title, function):
		choice = Dialog.input(title = title, type = Dialog.InputAlphabetic, default = function())
		function(value = choice)

	@classmethod
	def _numberDialog(self, title, function):
		choice = Dialog.input(title = title, type = Dialog.InputNumeric, default = function())
		function(value = choice)

	# REMOVAL

	@classmethod
	def removalDuplicates(self, value = None, label = None):
		return self._itemSelection(filter = Filters.FilterRemovalDuplicates, items = self._itemListBoolean, value = value, label = label)

	@classmethod
	def _removalDuplicates(self):
		self._itemDialog(title = 35450, items = self._itemListBoolean, function = self.removalDuplicates)

	@classmethod
	def removalUnsupported(self, value = None, label = None):
		return self._itemSelection(filter = Filters.FilterRemovalUnsupported, items = self._itemListBoolean, value = value, label = label)

	@classmethod
	def _removalUnsupported(self):
		self._itemDialog(title = 35451, items = self._itemListBoolean, function = self.removalUnsupported)

	# Sort

	@classmethod
	def sortQuality(self, value = None, label = None):
		return self._itemSelection(filter = Filters.FilterSortQuality, items = self._sortQualityList, value = value, label = label)

	@classmethod
	def _sortQuality(self):
		self._itemDialog(title = 33764, items = self._sortQualityList, function = self.sortQuality)

	@classmethod
	def _sortQualityList(self, index = None):
		return self._itemList(items = [33765, 33766], index = index)

	@classmethod
	def sortPrimary(self, value = None, label = None):
		return self._itemSelection(filter = Filters.FilterSortPrimary, items = self._sortPrimaryList, value = value, label = label)

	@classmethod
	def _sortPrimary(self):
		self._itemDialog(title = 35402, items = self._sortPrimaryList, function = self.sortPrimary)

	@classmethod
	def _sortPrimaryList(self, index = None):
		return self._itemList(items = [33680, 33681], index = index)

	@classmethod
	def _sortSecondaryList(self, index = None):
	    return self._itemList(items = [32302, 35226, 35227, 35228, 35229, 35230, 35231], index = index)

	@classmethod
	def sortSize(self, value = None, label = None):
	    return self._itemSelection(filter = Filters.FilterSortSize, items = self._sortSecondaryList, value = value, label = label)

	@classmethod
	def _sortSize(self):
	    self._itemDialog(title = 35457, items = self._sortSecondaryList, function = self.sortSize)

	@classmethod
	def sortAge(self, value = None, label = None):
	    return self._itemSelection(filter = Filters.FilterSortAge, items = self._sortSecondaryList, value = value, label = label)

	@classmethod
	def _sortAge(self):
	    self._itemDialog(title = 35225, items = self._sortSecondaryList, function = self.sortAge)

	@classmethod
	def sortSeeds(self, value = None, label = None):
	    return self._itemSelection(filter = Filters.FilterSortSeeds, items = self._sortSecondaryList, value = value, label = label)

	@classmethod
	def _sortSeeds(self):
	    self._itemDialog(title = 35224, items = self._sortSecondaryList, function = self.sortSeeds)

	@classmethod
	def sortPopularity(self, value = None, label = None):
	    return self._itemSelection(filter = Filters.FilterSortPopularity, items = self._sortSecondaryList, value = value, label = label)

	@classmethod
	def _sortPopularity(self):
	    self._itemDialog(title = 35404, items = self._sortSecondaryList, function = self.sortPopularity)

	# PROVIDER

	@classmethod
	def providerService(self, value = None, label = None):
		return self._itemSelection(filter = Filters.FilterProviderService, items = self._providerServiceList, value = value, label = label)

	@classmethod
	def _providerService(self):
		self._itemDialog(title = 33205, items = self._providerServiceList, function = self.providerService)

	@classmethod
	def _providerServiceList(self, index = None):
		return self._itemList(items = [33029, 33206, 33207, 33208, 33209, 33210, 33211], index = index)

	@classmethod
	def providerSelection(self, value = None, label = None):
		return self._itemSelection(filter = Filters.FilterProviderSelection, items = self._providerSelectionList, value = value, label = label)

	@classmethod
	def _providerSelection(self):
		self._itemDialog(title = 33197, items = self._providerSelectionList, function = self.providerSelection)

	@classmethod
	def _providerSelectionList(self, index = None):
		return self._itemList(items = [33029, 33201, 33202, 33203, 33198, 33199, 33200], index = index)

	@classmethod
	def providerAge(self, value = None, label = None):
		result = self.filter(id = Filters.FilterProviderAge, value = value)
		if not result == None: result = int(result)
		if label:
			if result == 0: result = Translation.string(33112)
			else: result = str(result) + ' ' + Translation.string(33347)
		return result

	@classmethod
	def _providerAge(self):
		self._numberDialog(title = 33136, function = self.providerAge)

	@classmethod
	def providerSeeds(self, value = None, label = None):
		result = self.filter(id = Filters.FilterProviderSeeds, value = value)
		if not result == None: result = int(result)
		if label:
			if result == 0: result = Translation.string(33112)
			else: result = str(result) + ' ' + Translation.string(33204)
		return result

	@classmethod
	def _providerSeeds(self):
		self._numberDialog(title = 33135, function = self.providerSeeds)

	@classmethod
	def providerPopularity(self, value = None, label = None):
		result = self.filter(id = Filters.FilterProviderPopularity, value = value)
		if not result == None: result = int(result)
		if label:
			if result == 0: result = Translation.string(33112)
			else: result = str(result) + '%'
		return result

	@classmethod
	def _providerPopularity(self):
		self._numberDialog(title = 35491, function = self.providerPopularity)

	@classmethod
	def providerCacheTorrent(self, value = None, label = None):
		return self._itemSelection(filter = Filters.FilterProviderCacheTorrent, items = self._itemListInclude, value = value, label = label)

	@classmethod
	def _providerCacheTorrent(self):
		self._itemDialog(title = 33464, items = self._itemListInclude, function = self.providerCacheTorrent)

	@classmethod
	def providerCacheUsenet(self, value = None, label = None):
		return self._itemSelection(filter = Filters.FilterProviderCacheUsenet, items = self._itemListInclude, value = value, label = label)

	@classmethod
	def _providerCacheUsenet(self):
		self._itemDialog(title = 33465, items = self._itemListInclude, function = self.providerCacheUsenet)

	@classmethod
	def providerCacheHoster(self, value = None, label = None):
		return self._itemSelection(filter = Filters.FilterProviderCacheHoster, items = self._itemListInclude, value = value, label = label)

	@classmethod
	def _providerCacheHoster(self):
		self._itemDialog(title = 35054, items = self._itemListInclude, function = self.providerCacheHoster)

	# FILE

	@classmethod
	def fileNameInclude(self, value = None, label = None):
		result = self.filter(id = Filters.FilterFileNameInclude, value = value, empty = True)
		if label and result.strip() == '': result = Translation.string(33112)
		return result

	@classmethod
	def _fileNameInclude(self):
		self._textDialog(title = 35482, function = self.fileNameInclude)

	@classmethod
	def fileNameExclude(self, value = None, label = None):
		result = self.filter(id = Filters.FilterFileNameExclude, value = value, empty = True)
		if label and result.strip() == '': result = Translation.string(33112)
		return result

	@classmethod
	def _fileNameExclude(self):
		self._textDialog(title = 35483, function = self.fileNameExclude)

	@classmethod
	def _fileSize(self, filter, value = None, label = None):
		result = self.filter(id = filter, value = value)
		if not result == None: result = int(result)
		if label:
			if result == 0: result = Translation.string(33112)
			else: result = convert.ConverterSize(result, convert.ConverterSize.ByteMega).stringOptimal()
		return result

	@classmethod
	def fileSizeMinimum(self, value = None, label = None):
		return self._fileSize(filter = Filters.FilterFileSizeMinimum, value = value, label = label)

	@classmethod
	def _fileSizeMinimum(self):
		self._numberDialog(title = 35304, function = self.fileSizeMinimum)

	@classmethod
	def fileSizeMaximum(self, value = None, label = None):
		return self._fileSize(filter = Filters.FilterFileSizeMaximum, value = value, label = label)

	@classmethod
	def _fileSizeMaximum(self):
		self._numberDialog(title = 35305, function = self.fileSizeMaximum)

	# VIDEO

	@classmethod
	def _videoQualityList(self, index = None):
		return self._itemList(items = [33112, 33763, 33762, 33761, 33760, 33759, 33758, 33137, 33138, 33139, 33140, 33141, 33142, 33143], index = index)

	@classmethod
	def videoQualityMinimum(self, value = None, label = None):
		return self._itemSelection(filter = Filters.FilterVideoQualityMinimum, items = self._videoQualityList, value = value, label = label)

	@classmethod
	def _videoQualityMinimum(self):
		self._itemDialog(title = 33125, items = self._videoQualityList, function = self.videoQualityMinimum)

	@classmethod
	def videoQualityMaximum(self, value = None, label = None):
		return self._itemSelection(filter = Filters.FilterVideoQualityMaximum, items = self._videoQualityList, value = value, label = label)

	@classmethod
	def _videoQualityMaximum(self):
		self._itemDialog(title = 33126, items = self._videoQualityList, function = self.videoQualityMaximum)

	@classmethod
	def videoCodec(self, value = None, label = None):
		return self._itemSelection(filter = Filters.FilterVideoCodec, items = self._videoCodecList, value = value, label = label)

	@classmethod
	def _videoCodec(self):
		self._itemDialog(title = 33127, items = self._videoCodecList, function = self.videoCodec)

	@classmethod
	def _videoCodecList(self, index = None):
		return self._itemList(items = [33113, 33146, 33144, 33145, 35416, 35417], index = index)

	@classmethod
	def video3D(self, value = None, label = None):
		return self._itemSelection(filter = Filters.FilterVideo3D, items = self._itemListInclude, value = value, label = label)

	@classmethod
	def _video3D(self):
		self._itemDialog(title = 33128, items = self._itemListInclude, function = self.video3D)

	# AUDIO

	@classmethod
	def audioChannels(self, value = None, label = None):
		return self._itemSelection(filter = Filters.FilterAudioChannels, items = self._audioChannelsList, value = value, label = label)

	@classmethod
	def _audioChannels(self):
		self._itemDialog(title = 33129, items = self._audioChannelsList, function = self.audioChannels)

	@classmethod
	def _audioChannelsList(self, index = None):
		return self._itemList(items = [33113, 33150, 33149, 33148, 33147], index = index)

	@classmethod
	def audioCodec(self, value = None, label = None):
		return self._itemSelection(filter = Filters.FilterAudioCodec, items = self._audioCodecList, value = value, label = label)

	@classmethod
	def _audioCodec(self):
		self._itemDialog(title = 33130, items = self._audioCodecList, function = self.audioCodec)

	@classmethod
	def _audioCodecList(self, index = None):
		return self._itemList(items = [33113, 33155, 33154, 33151, 33152, 33153, 35418, 35419, 35420], index = index)

	@classmethod
	def audioLanguage(self, value = None, label = None):
		if value == '': value = 0
		elif isinstance(value, basestring): value = tools.Language.language(value, index = True)
		return self._itemSelection(filter = Filters.FilterAudioLanguage, items = self._audioLanguageList, value = value, label = label)

	@classmethod
	def _audioLanguage(self):
		self._itemDialog(title = 35038, items = self._audioLanguageList, function = self.audioLanguage)

	@classmethod
	def _audioLanguageList(self, index = None):
		items = [33113]
		items.extend(tools.Language.names(universal = False))
		return self._itemList(items = items, index = index)

	@classmethod
	def audioDubbed(self, value = None, label = None):
		return self._itemSelection(filter = Filters.FilterAudioDubbed, items = self._itemListInclude, value = value, label = label)

	@classmethod
	def _audioDubbed(self):
		self._itemDialog(title = 35161, items = self._itemListInclude, function = self.audioDubbed)

	# SUBTITLES

	@classmethod
	def subtitlesSoft(self, value = None, label = None):
		return self._itemSelection(filter = Filters.FilterSubtitlesSoft, items = self._itemListInclude, value = value, label = label)

	@classmethod
	def _subtitlesSoft(self):
		self._itemDialog(title = 33131, items = self._itemListInclude, function = self.subtitlesSoft)

	@classmethod
	def subtitlesHard(self, value = None, label = None):
		return self._itemSelection(filter = Filters.FilterSubtitlesHard, items = self._itemListInclude, value = value, label = label)

	@classmethod
	def _subtitlesHard(self):
		self._itemDialog(title = 33132, items = self._itemListInclude, function = self.subtitlesHard)
