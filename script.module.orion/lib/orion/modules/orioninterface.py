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
# ORIONINTERFACE
##############################################################################
# Class for graphic interface.
##############################################################################

import xbmc
import xbmcgui
from orion.modules.oriontools import *

class OrionInterface:

	##############################################################################
	# CONSTANTS
	##############################################################################

	IconPlain = 'logo'
	IconInformation = 'information'
	IconWarning = 'warning'
	IconError = 'error'
	IconSuccess = 'success'

	IconNativeLogo = 'nativelogo'
	IconNativeInformation = 'nativeinformation'
	IconNativeWarning = 'nativewarning'
	IconNativeError = 'nativeerror'

	ThemeDefault = None
	ThemeLight = 'light'
	ThemeDark = 'dark'
	ThemeApps = 'apps'
	ThemeNotifications = 'notifications'

	ColorPrimary = 'FF47CAE9'
	ColorSecondary = 'FF637385'
	ColorTertiary = 'FF010B14'
	ColorGood = 'FF1E8449'
	ColorMedium = 'FF668D2E'
	ColorPoor = 'FFBA4A00'
	ColorBad = 'FF922B21'
	ColorEnabled = ColorGood
	ColorDisabled = ColorBad

	FontNewline = '[CR]'
	FontSeparator = ' • '
	FontDivider = ' - '
	FontLine = '••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••'

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

	##############################################################################
	# FONT
	##############################################################################

	@classmethod
	def font(self, label, color = None, bold = None, italic = None, light = None, uppercase = None, lowercase = None, capitalcase = None, newline = None, separator = None):
		label = OrionTools.translate(label)
		if label:
			if color:
				label = self.fontColor(label, color)
			if bold:
				label = self.fontBold(label)
			if italic:
				label = self.fontItalic(label)
			if light:
				label = self.fontLight(label)
			if uppercase:
				label = self.fontUppercase(label)
			elif lowercase:
				label = self.fontLowercase(label)
			elif capitalcase:
				label = self.fontCapitalcase(label)
			if newline:
				label += self.fontNewline()
			if separator:
				label += self.fontSeparator()
			return label
		else:
			return ''

	@classmethod
	def fontColor(self, label, color):
		if color == None: return label
		if len(color) == 6: color = 'FF' + color
		label = OrionTools.translate(label)
		return '[COLOR ' + color + ']' + label + '[/COLOR]'

	@classmethod
	def fontBold(self, label):
		label = OrionTools.translate(label)
		return '[B]' + label + '[/B]'

	@classmethod
	def fontItalic(self, label):
		label = OrionTools.translate(label)
		return '[I]' + label + '[/I]'

	@classmethod
	def fontLight(self, label):
		label = OrionTools.translate(label)
		return '[LIGHT]' + label + '[/LIGHT]'

	@classmethod
	def fontUppercase(self, label):
		label = OrionTools.translate(label)
		return '[UPPERCASE]' + label + '[/UPPERCASE]'

	@classmethod
	def fontLowercase(self, label):
		label = OrionTools.translate(label)
		return '[LOWERCASE]' + label + '[/LOWERCASE]'

	@classmethod
	def fontCapitalcase(self, label):
		label = OrionTools.translate(label)
		return '[CAPITALIZE]' + label + '[/CAPITALIZE]'

	@classmethod
	def fontNewline(self):
		return OrionInterface.FontNewline

	@classmethod
	def fontSeparator(self):
		return OrionInterface.FontSeparator

	@classmethod
	def fontDivider(self):
		return OrionInterface.FontDivider

	@classmethod
	def fontLine(self, color = True, bold = True, newline = True):
		if color is True: color = OrionInterface.ColorSecondary
		label = self.fontColor(OrionInterface.FontLine, color)
		if bold: label = self.fontBold(label)
		if newline: label = self.fontNewline() + self.fontNewline() + label + self.fontNewline() + self.fontNewline()
		return label

	##############################################################################
	# CONTAINER
	##############################################################################

	@classmethod
	def containerRefresh(self, orion = True):
		if not orion or OrionTools.kodiPlugin() == OrionTools.addonId():
			OrionTools.execute('Container.Refresh()')

	@classmethod
	def containerUpdate(self, orion = True, reset = False):
		if not orion or OrionTools.kodiPlugin() == OrionTools.addonId():
			OrionTools.execute('Container.Update' + ('(path,replace)' if reset else '()'))

	##############################################################################
	# ICON
	##############################################################################

	@classmethod
	def iconPath(self, icon, theme = ThemeDefault):
		if theme == OrionInterface.ThemeDefault:
			from orion.modules.orionsettings import OrionSettings
			theme = OrionInterface.ThemeLight if OrionSettings.getBoolean('general.interface.theme') == 0 else OrionInterface.ThemeDark
		if not icon.endswith('.png'): icon += '.png'
		return OrionTools.pathJoin(OrionTools.addonPath(), 'resources', 'media', 'icons', theme, icon)

	##############################################################################
	# LOADER
	##############################################################################

	@classmethod
	def loaderShow(self):
		xbmc.executebuiltin('ActivateWindow(%s)' % ('busydialognocancel' if OrionTools.kodiVersionNew() else 'busydialog'))

	@classmethod
	def loaderHide(self):
		xbmc.executebuiltin('Dialog.Close(%s)' % ('busydialognocancel' if OrionTools.kodiVersionNew() else 'busydialog'))

	@classmethod
	def loaderVisible(self):
		return xbmc.getCondVisibility('Window.IsActive(%s)' % ('busydialognocancel' if OrionTools.kodiVersionNew() else 'busydialog')) == 1

	##############################################################################
	# DIALOG
	##############################################################################

	@classmethod
	def _dialogTitle(self, extension = None, bold = True, titleless = False):
		title = '' if titleless else OrionTools.unicodeEncode(OrionTools.addonName())
		if not extension == None:
			if not titleless: title += self.fontDivider()
			title += OrionTools.translate(extension)
		if bold: title = self.fontBold(title)
		return title

	@classmethod
	def _dialogId(self):
		return xbmcgui.getCurrentWindowDialogId()

	@classmethod
	def _dialogVisible(self, id):
		return self._dialogId() == id

	@classmethod
	def dialogConfirm(self, message, title = None):
		return xbmcgui.Dialog().ok(self._dialogTitle(title), OrionTools.translate(message))

	@classmethod
	def dialogOption(self, message, labelConfirm = None, labelDeny = None, title = None):
		if not labelConfirm == None:
			labelConfirm = OrionTools.translate(labelConfirm)
		if not labelDeny == None:
			labelDeny = OrionTools.translate(labelDeny)
		return xbmcgui.Dialog().yesno(self._dialogTitle(title), OrionTools.translate(message), yeslabel = labelConfirm, nolabel = labelDeny)

	@classmethod
	def dialogOptions(self, items, multiple = False, preselect = [], title = None):
		items = [OrionTools.translate(item) for item in items]
		if multiple:
			try: return xbmcgui.Dialog().multiselect(self._dialogTitle(title), items, preselect = preselect)
			except: return xbmcgui.Dialog().multiselect(self._dialogTitle(title), items)
		else:
			return xbmcgui.Dialog().select(self._dialogTitle(title), items)

	@classmethod
	def dialogNotification(self, message, icon = None, time = 5000, sound = False, title = None, titleless = False):
		if icon:
			icon = icon.lower()
			if icon == OrionInterface.IconNativeInformation: icon = xbmcgui.NOTIFICATION_INFO
			elif icon == OrionInterface.IconNativeWarning: icon = xbmcgui.NOTIFICATION_WARNING
			elif icon == OrionInterface.IconNativeError: icon = xbmcgui.NOTIFICATION_ERROR
			else:
				if icon == OrionInterface.IconPlain or icon == OrionInterface.IconNativeLogo: icon = 'plain'
				elif icon == OrionInterface.IconWarning: icon = 'warning'
				elif icon == OrionInterface.IconError: icon = 'error'
				elif icon == OrionInterface.IconSuccess: icon = 'success'
				else: icon = 'information'
				icon = self.iconPath(icon, theme = OrionInterface.ThemeNotifications)
		xbmcgui.Dialog().notification(self._dialogTitle(title, titleless = titleless), OrionTools.translate(message), icon, time, sound = sound)

	@classmethod
	def dialogInformation(self, items, title = None):
		if items == None or len(items) == 0:
			return False

		def decorate(item):
			if 'value' in item:
				value = item['value']
				if value == None: value = ''
			else:
				value = None
			label = OrionTools.translate(item['title']) if 'title' in item else ''
			if value == None:
				label = self.font(label, bold = True, uppercase = True)
			else:
				if not label == '':
					if not value == None:
						label += ': '
					label = self.font(label, bold = True)
				if not value == None:
					label += self.font(value, italic = ('link' in item and item['link']))
			return label

		result = []
		for item in items:
			if 'items' in item:
				if not len(result) == 0:
					result.append('')
				result.append(decorate(item))
				for i in item['items']:
					result.append(decorate(i))
			else:
				result.append(decorate(item))

		return self.dialogOptions(result, title = title)

	@classmethod
	def dialogInput(self, type = InputAlphabetic, verify = False, confirm = False, hidden = False, default = None, title = None):
		default = '' if default == None else default
		if verify and not OrionTools.isArray(verify):
			option = xbmcgui.PASSWORD_VERIFY
			if OrionTools.isString(verify): default = verify
		elif confirm: option = 0
		elif hidden: option = xbmcgui.ALPHANUM_HIDE_INPUT
		else: option = None
		if option == None: result = xbmcgui.Dialog().input(self._dialogTitle(title), default, type = type)
		else: result = xbmcgui.Dialog().input(self._dialogTitle(title), default, type = type, option = option)
		if type == OrionInterface.InputNumeric:
			try: result = float(result)
			except: result = None
		if verify:
			if OrionTools.isArray(verify):
				if not result is None and result >= verify[0] and result <= verify[1]:
					return result
				else:
					self.dialogNotification(title = 32255, message = OrionTools.translate(33037) % verify, icon = OrionInterface.IconInformation)
					return self.dialogInput(type = type, verify = verify, confirm = confirm, hidden = hidden, default = default, title = title)
			else:
				return not result == ''
		else:
			return result

	@classmethod
	def dialogPage(self, message, title = None):
		xbmcgui.Dialog().textviewer(self._dialogTitle(title), OrionTools.translate(message))

	@classmethod
	def dialogBrowse(self, type = BrowseDefault, default = None, multiple = False, mask = [], title = None):
		if default == None: default = OrionTools.pathJoin(OrionTools.pathHome(), '') # Needs to end with a slash
		if mask == None: mask = []
		elif OrionTools.isString(mask): mask = [mask]
		for i in range(len(mask)):
			mask[i] = mask[i].lower()
			if not mask[i].startswith('.'):
				mask[i] = '.' + mask[i]
		mask = '|'.join(mask)
		return xbmcgui.Dialog().browse(type, self._dialogTitle(title), 'files', mask, True, False, default, multiple)
