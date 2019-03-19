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

import xbmcgui
import re
import math
import copy
import threading

from resources.lib.extensions import tools
from resources.lib.extensions import interface

class WindowBase(object):

	# Actions
	ActionSelectItem = 7
	ActionPreviousMenu = 10
	ActionNavigationBack = 92
	ActionMoveLeft = 1
	ActionMoveRight = 2
	ActionMoveUp = 3
	ActionMoveDown = 4
	ActionContextMenu = 117
	ActionPreviousMenu = 10
	ActionNavigationBack = 92
	ActionShowInfo = 11
	ActionItemNext = 14
	ActionItemPrevious = 15
	ActionsCancel = [ActionPreviousMenu, ActionNavigationBack, ActionMoveRight]

	def __init__(self, **arguments):
		self.mActions = []
		self.mControls = []
		self.mClicks = []
		self.mVisible = False

	def __del__(self):
		self.mVisible = False

	def show(self):
		self.mVisible = True
		xbmcgui.WindowDialog.show(self)

	def doModal(self):
		self.mVisible = True
		xbmcgui.WindowDialog.doModal(self)

	def close(self):
		self.mVisible = False
		xbmcgui.WindowDialog.close(self)

	def visible(self):
		return self.mVisible

	def _onAction(self, action, callback):
		self.mActions.append((action, callback))

	def _onControl(self, x, y, callback):
		self.mControls.append((x, y, callback))

	def _onClick(self, control, callback):
		try: control = control.getId()
		except: pass
		self.mClicks.append((control, callback))

	def onAction(self, action):
		id = action.getId()
		if id in WindowBase.ActionsCancel: self.mVisible = False
		xbmcgui.WindowDialog.onAction(self, action)
		for i in self.mActions:
			if i[0] == id:
				try: i[1](action = id)
				except: i[1]()

	def onControl(self, control):
		distances = []
		actions = []
		x = control.getX()
		y = control.getY()

		for i in self.mControls:
			distances.append(abs(x - i[0]) + abs(y - i[1]))
			actions.append(i[2])

		smallestIndex = -1
		smallestDistance = 999999
		for i in range(len(distances)):
			if distances[i] < smallestDistance:
				smallestDistance = distances[i]
				smallestIndex = i

		if smallestIndex >= 0:
			actions[smallestIndex]()

	def onClick(self, controlId):
		for i in self.mClicks:
			if i[0] == controlId:
				i[1]()

class WindowCore(WindowBase, xbmcgui.WindowDialog):

	def __init__(self):
		super(WindowCore, self).__init__()

	def __del__(self):
		try: super(WindowCore, self).__del__()
		except: pass

class WindowXml(WindowBase, xbmcgui.WindowXMLDialog):

	def __init__(self, file, path, skin, resolution):
		# Using super() here with multiple inheritance does not work.
		WindowBase.__init__(self)
		xbmcgui.WindowXMLDialog.__init__(self, xmlFilename = file, scriptPath = path, defaultSkin = skin, defaultRes = resolution)

	def __del__(self):
		try: super(WindowXml, self).__del__()
		except: pass

class Window(object):

	Instance = None

	InitializeIterations = 100
	InitializeSleep = 0.1

	IdMinimum = 10000
	IdMaximum = 13000
	IdWindowHome = 10000
	IdWindowVideo = 10025
	IdWindowPlayer = 12901
	IdWindowPlayerFull = 12005
	IdWindowPlaylist = 10028
	IdWindowInformation = 12003
	IdListControl = 52000

	# All Kodi windows have this fixed dimension.
	SizeWidth = 1280
	SizeHeight = 720

	# Size
	SizeLarge = 'large'
	SizeMedium = 'medium'
	SizeSmall = 'small'

	# Replacements
	Replacements = {
		tools.Screen.Ratio4x3 : {
			'[GAIAPANELLEFT]' : '40',
			'[GAIAPOSTERTOP]' : '130',
			'[GAIAPOSTERWIDTH]' : '360',
			'[GAIAPOSTERHEIGHT]' : '400',
		},
		tools.Screen.Ratio16x9 : {
			'[GAIAPANELLEFT]' : '40',
			'[GAIAPOSTERTOP]' : '0',
			'[GAIAPOSTERWIDTH]' : '360',
			'[GAIAPOSTERHEIGHT]' : '530',
		},
		tools.Screen.Ratio20x9 : {
			'[GAIAPANELLEFT]' : '70',
			'[GAIAPOSTERTOP]' : '0',
			'[GAIAPOSTERWIDTH]' : '300',
			'[GAIAPOSTERHEIGHT]' : '530',
		},
	}

	# Type
	TypePlain = 'plain'
	TypeBasic = 'basic'
	TypeIcons = 'icons'
	TypeDefault = TypeIcons
	Types = [TypePlain, TypeBasic, TypeIcons]

	# Background
	BackgroundColorOpaque = 'FFFFFFFF'
	BackgroundColor1 = 'DD222222'
	BackgroundColor2 = 'AA111111'
	BackgroundNone = 0
	BackgroundCombined = 1
	BackgroundSkin = 2
	BackgroundFanart = 3

	# Separator
	Separator = '•'
	SeparatorPadded = '  ' + Separator + '  '
	SeparatorLineWidth = 850
	SeparatorLineHeight = 3
	SeparatorLinePadding = 25

	# Font
	# Some skins (including the default one) does not have all font sizes. Stick with even numbers and limit to 16.
	FontSmall = 'font10'
	FontMedium = 'font12'
	FontLarge = 'font14'
	FontHuge = 'font16'

	# Alignment
	AlignmentLeft = 0x00000000
	AlignmentRight = 0x00000001
	AlignmentTruncated = 0x00000008
	AlignmentJustified = 0x00000010
	AlignmentCenterX = 0x00000002
	AlignmentCenterY = 0x00000004
	AlignmentCenter = AlignmentCenterX | AlignmentCenterY
	AlignmentLeftCenter = AlignmentLeft | AlignmentCenterY
	AlignmentRightCenter = AlignmentRight | AlignmentCenterY
	AlignmentTruncatedCenter = AlignmentTruncated | AlignmentCenterY
	AlignmentJustifiedCenter = AlignmentJustified | AlignmentCenterY

	# Color
	ColorDefault = interface.Format.ColorWhite
	ColorHighlight = interface.Format.ColorPrimary
	ColorDiffuse = interface.Format.ColorDisabled
	ColorSeparator = interface.Format.ColorSecondary

	def __init__(self, backgroundType, backgroundPath, xml = None, xmlScale = False, xmlType = TypeDefault):
		self.mId = 0
		self.mLock = threading.Lock()

		if xml:
			if xmlScale:
				ratio = tools.Screen.ratio(closest = True)[0]
				xmlRatio = xml.replace('.xml', '') + xmlType + ratio + '.xml'
				if not '.' in xml: xml += '.xml'
				pathTemplate = self._pathTemplate()
				pathWindow = self._pathWindow(True)
				pathXml = tools.File.joinPath(pathTemplate, xml)
				pathRatio = tools.File.joinPath(pathWindow, xmlRatio)
				xml = xmlRatio

				if not tools.File.exists(pathRatio):
					tools.File.makeDirectory(pathWindow)
					data = tools.File.readNow(pathXml)

					for key, value in Window.Replacements[ratio].iteritems():
						data = data.replace(key, value)

					types = Window.Types
					types.remove(xmlType)
					types = ['<!-- \[GAIATYPE%s/\] -->.*?<!-- \[/GAIATYPE%s\] -->' % (type.upper(), type.upper()) for type in types]
					for type in types:
						data = re.sub(type, '', data, flags = re.DOTALL)

					tools.File.writeNow(pathRatio, data)
			if not '.' in xml: xml += '.xml'
			self.mWindow = WindowXml(xml, self._pathWindow(False), 'default', '720p')
		else:
			self.mWindow = WindowCore()

		self.mAfter = False
		self.mControls = []
		self.mContexts = []

		self.mBackgroundType = backgroundType
		self.mBackgroundPath = backgroundPath

		self.mScaleWidth = (Window.SizeWidth / float(Window.SizeHeight)) / (tools.Screen.width() / float(tools.Screen.height()))
		self.mScaleHeight = 1

		self.mWidth = Window.SizeWidth
		self.mHeight = Window.SizeHeight

	def __del__(self):
		self._remove()

	@classmethod
	def _instance(self, instance = None):
		# One instance per class.
		if not instance == None: globals()[self.__name__].Instance = instance
		return globals()[self.__name__].Instance

	@classmethod
	def _instanceHas(self):
		return not globals()[self.__name__].Instance == None

	@classmethod
	def _instanceDelete(self):
		try:
			del globals()[self.__name__].Instance
			globals()[self.__name__].Instance = None
		except: pass

	def _lock(self):
		self.mLock.acquire()

	def _unlock(self):
		self.mLock.release()

	def _initializeStart(self):
		pass

	def _initializeEnd(self):
		self._addBackground(type = self.mBackgroundType, path = self.mBackgroundPath)

	def _initializeAfter(self):
		self.mAfter = True

	def _onAction(self, action, callback):
		self.mWindow._onAction(action, callback)

	def _onControl(self, x, y, callback):
		self.mWindow._onControl(x, y, callback)

	def _onClick(self, control, callback):
		self.mWindow._onClick(control, callback)

	@classmethod
	def _after(self):
		try: return self._instance().mAfter
		except: pass

	@classmethod
	def _idPropertyName(self):
		return tools.System.name() + self.__name__

	@classmethod
	def _idProperty(self):
		id = self.propertyGlobal(self._idPropertyName())
		if id == None or id == '': return None
		else: return int(id)

	@classmethod
	def _idPropertySet(self, id):
		return self.propertyGlobalSet(self._idPropertyName(), id)

	@classmethod
	def _idPropertyClear(self):
		return self.propertyGlobalClear(self._idPropertyName())

	@classmethod
	def _initialize1(self, **arguments):
		try:
			window = self._instance(self(**arguments))
		except:
			try:
				try: del arguments['retry']
				except: pass
				window = self._instance(self(**arguments))
			except:
				tools.Logger.error()
				tools.Logger.log('GAIA ERROR WINDOW: ' + str(arguments)) # gaiaremove - for temporary debugging. Can be removed later.
				return None
		window._initializeStart()
		window._initializeEnd()
		window.mWindow.doModal()
		window.close()

	@classmethod
	def _initialize2(self):
		try:
			count = 0
			instance = self._instance()
			while instance == None and count < Window.InitializeIterations:
				tools.Time.sleep(Window.InitializeSleep)
				count += 1
				instance = self._instance()
			if not instance == None:
				while not instance.visible() and count < Window.InitializeIterations:
					tools.Time.sleep(Window.InitializeSleep)
					count += 1
				id = self.current()
				instance.mId = id
				self._idPropertySet(instance.mId)
				instance._initializeAfter()
		except: pass

	@classmethod
	def _show(self, **arguments):
		try:
			close = arguments['close']
			del arguments['close']
		except:
			close = False
		if self.visible() and not close:
			return False
		elif close:
			self.close()
			tools.Time.sleep(0.1)

		wait = arguments['wait']
		del arguments['wait']
		initialize = arguments['initialize']
		del arguments['initialize']
		thread1 = threading.Thread(target = self._initialize1, kwargs = arguments)
		thread1.start()
		thread2 = threading.Thread(target = self._initialize2)
		thread2.start()
		if wait:
			thread1.join()
		elif initialize: # Wait until launched.
			count = 0
			while not self.visible() and count < Window.InitializeIterations:
				tools.Time.sleep(Window.InitializeSleep)
				count += 1
			while not self._after() and count < Window.InitializeIterations:
				tools.Time.sleep(Window.InitializeSleep)
				count += 1
		return True

	@classmethod
	def clean(self):
		tools.File.deleteDirectory(self._pathWindow())

	@classmethod
	def close(self, id = None, loader = True):
		try:
			# Instance might be lost if accessed in a subsequent execution (eg: applying filters).
			if id == None and not self._instanceHas(): id = self._idProperty()

			if id == None:
				instance = self._instance()
				instance._remove()
				instance.mWindow.close()
				if loader: interface.Loader.hide() # Sometimes is visible if canceling playback window.
				try:
					del instance.mWindow
					instance.mWindow = None
				except: pass
				self._instanceDelete()
			else:
				interface.Dialog.close(id)

			self._idPropertyClear()
			return True
		except:
			self._idPropertyClear()
			return False

	@classmethod
	def show(self, id):
		return tools.System.execute('ActivateWindow(%s)' % str(id))

	@classmethod
	def id(self):
		try: return self._instance().mId
		except: return None

	@classmethod
	def current(self, id = None):
		return self.currentDialog(id = id)

	@classmethod
	def currentWindow(self, id = None):
		result = xbmcgui.getCurrentWindowId()
		if id == None: return result
		else: return result == id

	@classmethod
	def currentDialog(self, id = None):
		result = xbmcgui.getCurrentWindowDialogId()
		if id == None: return result
		else: return result == id

	@classmethod
	def visible(self, id = None):
		try:
			if id == None: return self._instance().mWindow.visible()
			else: return self.visibleWindow(id) or self.visibleDialog(id)
		except: return False

	@classmethod
	def visibleWindow(self, id):
		return self.currentWindow() == id

	@classmethod
	def visibleDialog(self, id):
		return self.currentDialog() == id

	@classmethod
	def visibleCustom(self, id = None):
		return self.currentWindow() >= Window.IdMaximum or self.currentDialog() >= Window.IdMaximum

	@classmethod
	def separator(self, items = None, bold = True, color = None):
		separator = Window.SeparatorPadded
		if bold:
			separator = interface.Format.font(separator, bold = True, translate = False)
		if color:
			if color == True: color = Window.ColorDiffuse
			separator = interface.Format.font(separator, color = color, translate = False)
		if items: return separator.join([i for i in items if not i == None and not i == ''])
		else: return separator

	@classmethod
	def focus(self, control = IdListControl, sleep = True):
		try:
			if isinstance(control, (int, long)): result = self._instance().mWindow.setFocusId(control)
			else: result = self._instance().mWindow.setFocus(control)
			if sleep: tools.Time.sleep(0.01) # Otherwise the control is not yet focused when later code requires the focus somehow (eg: opening the context menu).
			return result
		except: pass

	@classmethod
	def itemClear(self, control = IdListControl):
		try: return self._instance().control(control).reset()
		except: pass

	@classmethod
	def itemAdd(self, item, context = None, control = IdListControl):
		try:
			instance = self._instance()
			if isinstance(item, list):
				instance.mContexts.extend(context)
				return instance.control(control).addItems(item)
			else:
				instance.mContexts.append(context)
				return instance.control(control).addItem(item)
		except: pass

	@classmethod
	def itemSelect(self, index, control = IdListControl):
		try: return self._instance().control(control).selectItem(index)
		except: pass

	@classmethod
	def itemSelected(self, control = IdListControl, index = True):
		if id:
			try: return self._instance().control(control).getSelectedPosition()
			except: pass
		else:
			try: return self._instance().control(control).getSelectedItem()
			except: pass

	@classmethod
	def property(self, property, id = None):
		try:
			if id == None: return self._instance().mWindow.getProperty(property)
			else: return xbmcgui.Window(id).getProperty(property)
		except: pass

	@classmethod
	def propertyClear(self, property, id = None):
		try:
			if id == None: return self._instance().mWindow.clearProperty(property)
			else: return xbmcgui.Window(id).clearProperty(property)
		except: pass

	@classmethod
	def propertySet(self, property, value, id = None):
		try:
			if value is None: value = ''
			elif isinstance(value, bool): value = int(value)
			value = str(value)
			if id == None: return self._instance().mWindow.setProperty(property, value)
			else: return xbmcgui.Window(id).setProperty(property, value)
		except: pass

	@classmethod
	def propertyGlobal(self, property):
		return self.property(property = property, id = Window.IdWindowHome)

	@classmethod
	def propertyGlobalClear(self, property):
		return self.propertyClear(property = property, id = Window.IdWindowHome)

	@classmethod
	def propertyGlobalSet(self, property, value):
		return self.propertySet(property = property, value = value, id = Window.IdWindowHome)

	def control(self, id):
		try: return self.mWindow.getControl(id)
		except: return None

	def _window(self):
		return self.mWindow

	@classmethod
	def _theme(self):
		theme = tools.Settings.getString('interface.theme.skin').lower()
		theme = theme.replace(' ', '').lower()
		index = theme.find('(')
		if index >= 0: theme = theme[:index]
		return theme

	@classmethod
	def _pathTemplate(self):
		return tools.File.joinPath(tools.System.pathResources(), 'resources', 'skins', 'default', '720p')

	@classmethod
	def _pathWindow(self, kodi = False):
		path = tools.File.joinPath(tools.System.profile(), 'Windows')
		if kodi: path = tools.File.joinPath(path, 'resources', 'skins', 'default', '720p')
		return path

	@classmethod
	def _pathInterface(self):
		return tools.File.joinPath(tools.System.pathResources(), 'resources', 'media', 'interface')

	@classmethod
	def _pathSkin(self):
		theme = self._theme()
		addon = tools.System.pathResources() if theme == 'default' or 'gaia1' in theme else tools.System.pathSkins()
		return tools.File.joinPath(addon, 'resources', 'media', 'skins', theme)

	@classmethod
	def _pathImage(self, image, interface = True):
		if not '.' in image: image += '.png'
		path = tools.File.joinPath(self._pathSkin(), 'interface' if interface else '', image)
		if not tools.File.exists(path): path = tools.File.joinPath(self._pathInterface(), image)
		return path

	def _pathIcon(self, icon):
		if not '.' in icon: icon += '.png'
		return interface.Icon.path(icon, type = interface.Icon.ThemeIcon)

	def _pathLogo(self, size = SizeLarge):
		return tools.File.joinPath(tools.System.pathResources(), 'resources', 'media', 'logo', size)

	@classmethod
	def _background(self, type = None, path = None):
		result = []
		if type == Window.BackgroundFanart or type == Window.BackgroundCombined:
			result.append({'path' : path if path else self._pathImage('background.jpg', interface = False), 'color' : Window.BackgroundColorOpaque})
		elif type == Window.BackgroundSkin :
			result.append({'path' : self._pathImage('background.jpg', interface = False), 'color' : Window.BackgroundColorOpaque})
		if type == Window.BackgroundCombined:
			result.append({'path' : self._pathImage('background.jpg', interface = False), 'color' : Window.BackgroundColor1})
		else:
			result.append({'path' : self._pathImage('pixel.png'), 'color' : Window.BackgroundColor2})
		return result

	def _scaleWidth(self, value):
		return int(self.mScaleWidth * value)

	def _scaleHeight(self, value):
		return int(self.mScaleHeight * value)

	def _centerX(self, width):
		return int((self.mWidth - width) / 2.0)

	def _centerY(self, height):
		return int((self.mHeight - height) / 2.0)

	def _offsetX(self):
		return self.mDimensionX + self.mDimensionWidth

	def _offsetY(self):
		return self.mDimensionY + self.mDimensionHeight

	def _dimensionSeparator(self):
		return [Window.SeparatorLineWidth, Window.SeparatorLineHeight + Window.SeparatorLinePadding]

	def _dimensionButton(self, text = None, icon = None):
		return [(len(self._buttonText(text = text, icon = icon)) * 14) if text else self._scaleWidth(250), self._scaleHeight(50)]

	def _buttonText(self, text, icon = None):
		text = interface.Translation.string(text)
		if not icon == None: text = '       ' + text
		return text

	def _remove(self, controls = None, force = False):
		try:
			if controls == None:
				result = []
				remove = []
				for control in self.mControls[::-1]: # Iterate reverse, because there is a delay.
					if force or not control[1]: control[0].setVisible(False)
				for control in self.mControls[::-1]: # Iterate reverse, because there is a delay.
					if not force and control[1]: result.append(control)
					else: remove.append(control[0])
				self.mWindow.removeControls(remove)
				for control in remove:
					del control
				self.mControls = result
			else:
				if isinstance(controls, list): self.mWindow.removeControls(controls)
				else: self.mWindow.removeControl(controls)
				for control in controls:
					del control
		except: pass

	def _add(self, control, fixed = False):
		self._lock()
		self.mControls.append([control, fixed])
		self.mWindow.addControl(control)
		self._unlock()
		return control

	def _addImage(self, path, x, y, width, height, color = None, fixed = False):
		image = xbmcgui.ControlImage(x, y, width, height, path)
		if color: image.setColorDiffuse(color)
		return self._add(control = image, fixed = fixed)

	def _addBackground(self, type = BackgroundCombined, path = None, fixed = False):
		images = self._background(type = type, path = path)
		for image in images:
			self._addImage(path = image['path'], color = image['color'], x = 0, y = 0, width = self.mWidth, height = self.mHeight, fixed = fixed)

	def _addButton(self, text, x, y, width = None, height = None, callback = None, icon = None, bold = True, uppercase = True):
		dimension = self._dimensionButton(text = text, icon = icon)
		if width == None: width = dimension[0]
		if height == None: height = dimension[1]

		text = self._buttonText(text = text, icon = icon)
		pathNormal = self._pathImage('buttonnormal')
		pathFocus = self._pathImage('buttonfocus')
		control = self._add(xbmcgui.ControlButton(x, y, width, height, interface.Format.font(text, bold = bold, uppercase = uppercase), focusTexture = pathFocus, noFocusTexture = pathNormal, alignment = Window.AlignmentCenter, textColor = Window.ColorDefault, font = Window.FontHuge))

		if not icon == None:
			iconSize = int(height * 0.8)
			iconX = int(x + (width * 0.1))
			iconY = int(y + ((height - iconSize) / 2.0))
			controlIcon = self._addImage(path = self._pathIcon(icon), x = iconX, y = iconY, width = iconSize, height = iconSize)
		else:
			controlIcon = None

		if callback:
			self.mWindow._onControl(x, y, callback)

		return [control, controlIcon]

	def _addSeparator(self, x = None, y = None, control = False):
		dimension = self._dimensionSeparator()
		height = self._scaleHeight(Window.SeparatorLineHeight)
		if x == None: x = self._centerX(dimension[0])
		if y == None: y = self._offsetY() + int((dimension[1] - height) / 2.0)
		image = self._addImage(self._pathImage('separator'), x = x, y = y, width = dimension[0], height = height)
		if control: return (image, dimension)
		else: return dimension

	def _addLabel(self, text, x, y, width, height, color = ColorDefault, size = FontMedium, alignment = AlignmentLeft, bold = False, italic = False, light = False, uppercase = False, lowercase = False, capitalcase = False):
		# NB: Fix suggested by NG.
		# Sometimes when the special window is closed, the text of the lables remain afterwards. The text is then shown in various places of the current Kodi native window.
		# NG suggested to add labels to window BEFORE setting the text.
		control = self._add(xbmcgui.ControlLabel(x, y, width, height, '', font = size, textColor = color, alignment = alignment))
		self._setLabel(control = control, text = text, color = color, size = size, bold = bold, italic = italic, light = light, uppercase = uppercase, lowercase = lowercase, capitalcase = capitalcase)
		return control

	def _setLabel(self, control, text, color = ColorDefault, size = FontMedium, bold = False, italic = False, light = False, uppercase = False, lowercase = False, capitalcase = False, translate = False):
		control.setLabel(interface.Format.font(text, bold = bold, italic = italic, light = light, uppercase = uppercase, lowercase = lowercase, capitalcase = capitalcase, translate = translate), font = size, textColor = color)

class WindowIntro(Window):

	Parts = 7

	TimeAnimation = 1000
	TimeDelay = 400
	TimeOpen = (2 * TimeAnimation) + ((Parts + 1) * TimeDelay)

	LogoWidth = 700
	LogoHeight = 302

	def __init__(self, backgroundType, backgroundPath):
		super(WindowIntro, self).__init__(backgroundType = backgroundType, backgroundPath = backgroundPath)

	def __del__(self):
		super(WindowIntro, self).__del__()

	@classmethod
	def show(self, wait = False, initialize = True, close = False):
		return super(WindowIntro, self)._show(backgroundType = self.BackgroundCombined, backgroundPath = None, wait = wait, initialize = initialize, close = close)

	def _initializeEnd(self):
		super(WindowIntro, self)._initializeEnd()
		self._addLogo()

	def _initializeAfter(self):
		super(WindowIntro, self)._initializeAfter()
		tools.Time.sleep(WindowIntro.TimeOpen / 1000.0)
		self.close()

	def _logoPath(self, part):
		return tools.File.joinPath(tools.System.pathResources(), 'resources', 'media', 'logo', 'splash', 'gaia%d.png' % part)

	def _dimensionLogo(self):
		return [self._scaleWidth(WindowIntro.LogoWidth), self._scaleHeight(WindowIntro.LogoHeight)]

	def _addLogo(self):
		dimension = self._dimensionLogo()
		x = self._centerX(dimension[0])
		y = self._centerY(dimension[1])
		width = dimension[0]
		height = dimension[1]
		delay = WindowIntro.TimeDelay

		for i in range(1, WindowIntro.Parts + 1):
			logo = self._addImage(path = self._logoPath(i), x = x, y = y, width = width, height = height)
			logo.setAnimations([('WindowOpen', 'effect=fade start=0 end=100 time=%d delay=%d' % (WindowIntro.TimeAnimation, delay))])
			if i < WindowIntro.Parts - 1: delay += WindowIntro.TimeDelay

		return dimension

class WindowProgress(Window):

	# Logo
	LogoNone = None
	LogoIcon = 'icon'
	LogoName = 'name'

	LogoIconWidth = 128
	LogoIconHeight = 128
	LogoNameWidth = 197
	LogoNameHeight = 100
	LogoOffsetY = 0.24

	ProgressPercentage = 'GaiaProgressPercentage'
	ProgressFinished = 'GaiaProgressFinished'
	ProgressCount = 10
	ProgressSize = 24
	ProgressPaddingX = 8
	ProgressPaddingY = 20
	ProgressInterval = 0.1
	ProgressColorEmpty = interface.Format.ColorSecondary
	ProgressColorFull = interface.Format.ColorPrimary

	def __init__(self, backgroundType, backgroundPath, logo = None, status = None, xml = None, xmlScale = False, xmlType = Window.TypeDefault):
		super(WindowProgress, self).__init__(backgroundType = backgroundType, backgroundPath = backgroundPath, xml = xml, xmlScale = xmlScale, xmlType = xmlType)

		self.mLogo = logo

		self.mProgress = 0
		self.mProgressFinished = False
		self.mProgressIcons = []
		self.mProgressColors = interface.Format.colorGradient(WindowProgress.ProgressColorEmpty, WindowProgress.ProgressColorFull, int(100 / WindowProgress.ProgressCount))
		self.propertySet(WindowProgress.ProgressPercentage, self.mProgress)
		self.propertySet(WindowProgress.ProgressFinished, False)

		self.mStatus = status
		self.mStatusControl = None

	def __del__(self):
		super(WindowProgress, self).__del__()

	def _initializeStart(self):
		super(WindowProgress, self)._initializeStart()

		self.mDimensionWidth = 0
		self.mDimensionHeight = 0

		if self.mLogo: self._dimensionUpdate(self._dimensionLogo(self.mLogo))
		self._dimensionUpdate(self._dimensionProgress())
		if not self.mStatus == False and not self.mStatus == None:
			self._dimensionUpdate(self._dimensionSpace())
			self._dimensionUpdate(self._dimensionLine())
			self._dimensionUpdate(self._dimensionSpace())

	def _initializeEnd(self):
		super(WindowProgress, self)._initializeEnd()

		if self.mLogo: self.mDimensionHeight += self._offsetLogo(self._dimensionLogo(self.mLogo)[1])

		self.mDimensionX = self._centerX(self.mDimensionWidth)
		self.mDimensionY = self._centerY(self.mDimensionHeight)

		self.mDimensionWidth = 0
		self.mDimensionHeight = 0

		if self.mLogo: self._dimensionUpdate(self._addLogo(self.mLogo))
		self._dimensionUpdate(self._addProgress())
		if not self.mStatus == False and not self.mStatus == None:
			self._dimensionUpdate(self._dimensionSpace())
			self._dimensionUpdate(self._addStatus())
			self._dimensionUpdate(self._dimensionSpace())

	@classmethod
	def show(self, backgroundType = None, backgroundPath = None, logo = LogoIcon, status = None, wait = False, initialize = True, close = False, retry = False):
		return super(WindowProgress, self)._show(backgroundType = backgroundType, backgroundPath = backgroundPath, logo = logo, status = status, wait = wait, initialize = initialize, close = close, retry = retry)

	@classmethod
	def update(self, progress = None, finished = None, status = None):
		instance = self._instance()
		if not instance or not instance.visible(): return None
		instance._lock()

		if finished is True:
			progress = 100

		if not progress is None:
			if progress < 1: progress *= 100
			reduced = progress < instance.mProgress
			instance.mProgress = progress
			instance.propertySet(WindowProgress.ProgressPercentage, int(instance.mProgress))
			progress = instance._progress()
			for i in range(progress):
				instance.mProgressIcons[i].setColorDiffuse(instance.ProgressColorFull)
			try: instance.mProgressIcons[progress].setColorDiffuse(instance.mProgressColors[instance._progressSub()])
			except: pass
			if reduced:
				for i in range(progress, WindowProgress.ProgressCount):
					instance.mProgressIcons[i].setColorDiffuse(instance.ProgressColorEmpty)

		if not finished is None:
			instance.mProgressFinished = finished
			instance.propertySet(WindowProgress.ProgressFinished, finished)

		if not status == None:
			instance.mStatus = status
			instance._setLabel(control = instance.mStatusControl, text = interface.Format.fontColor(instance.mStatus, self.ColorHighlight), size = self.FontHuge, bold = True, uppercase = True)

		instance._unlock()
		return instance

	def _logoName(self, force = False, size = Window.SizeLarge):
		theme = self._theme()
		return tools.File.joinPath(self._pathLogo(size), 'namecolor.png' if force or theme == 'default' or 'gaia' in theme  else 'nameglass.png')

	def _logoIcon(self, force = False, size = Window.SizeLarge):
		theme = self._theme()
		return tools.File.joinPath(self._pathLogo(size), 'iconcolor.png' if force or theme == 'default' or 'gaia' in theme else 'iconglass.png')

	def _progress(self):
		return int(math.floor(self.mProgress / float(WindowProgress.ProgressCount)))

	def _progressSub(self):
		return int(self.mProgress % float(WindowProgress.ProgressCount))

	@classmethod
	def _separator(self, values):
		return self.separator(values, color = self.ColorSeparator, bold = False)

	@classmethod
	def _highlight(self, value):
		return interface.Format.fontColor(str(value), self.ColorHighlight)

	def _offsetLogo(self, y):
		return int(y * WindowProgress.LogoOffsetY)

	def _dimensionUpdate(self, size):
		self.mDimensionWidth = max(self.mDimensionWidth, size[0])
		self.mDimensionHeight += size[1]

	def _dimensionLine(self):
		return [self._scaleWidth(1200), self._scaleHeight(30)]

	def _dimensionSpace(self):
		return [1, self._scaleHeight(10)]

	def _dimensionLogo(self, logo):
		if logo == WindowProgress.LogoIcon: return [self._scaleWidth(WindowProgress.LogoIconWidth), self._scaleHeight(WindowProgress.LogoIconHeight)]
		elif logo == WindowProgress.LogoName: return [self._scaleWidth(WindowProgress.LogoNameWidth), self._scaleHeight(WindowProgress.LogoNameHeight)]
		else: return [0, 0]

	def _dimensionProgress(self):
		width = (WindowProgress.ProgressCount * self._scaleWidth(WindowProgress.ProgressSize)) + ((WindowProgress.ProgressCount - 1) * self._scaleWidth(WindowProgress.ProgressPaddingX))
		height = self._scaleHeight(WindowProgress.ProgressSize + WindowProgress.ProgressPaddingY)
		return [width, height]

	def _addLogo(self, logo):
		dimension = self._dimensionLogo(logo)
		if logo == WindowProgress.LogoIcon: path = self._logoIcon(force = True)
		elif logo == WindowProgress.LogoName: path = self._logoName(force = True)
		self._addImage(path = path, x = self._centerX(dimension[0]), y = self._offsetY(), width = dimension[0], height = dimension[1])
		if logo == WindowProgress.LogoName: dimension[1] += self._offsetLogo(dimension[1]) # Add padding below.
		return dimension

	def _addProgress(self):
		pathInner = self._pathImage('progressinner')
		pathOuter = self._pathImage('progressouter')
		padding = self._scaleWidth(WindowProgress.ProgressPaddingX)
		dimension = self._dimensionProgress()
		width = self._scaleWidth(WindowProgress.ProgressSize)
		height = self._scaleHeight(WindowProgress.ProgressSize)
		x = self._centerX(dimension[0])
		y = self._offsetY()

		# Use threads, otherwise the progress bar create takes too long and you can see one icon at a time appearing on the screen.
		threads = []
		self.mProgressIcons = [None] * WindowProgress.ProgressCount
		for i in range(WindowProgress.ProgressCount):
			thread = threading.Thread(target = self._addProgressIcon, args = (i, pathInner, pathOuter, x, y, width, height))
			thread.start() # Start here already that the threads' lock acquisition overlaps as least as possible.
			threads.append(thread)
			x += width + padding
		[thread.join() for thread in threads]

		return dimension

	def _addProgressIcon(self, index, pathInner, pathOuter, x, y, width, height):
		icon = self._addImage(path = pathInner, x = x, y = y, width = width, height = height, color = WindowProgress.ProgressColorEmpty)
		self._addImage(path = pathOuter, x = x, y = y, width = width, height = height)
		self._lock()
		self.mProgressIcons[index] = icon
		self._unlock()

	def _addLine(self, text = '', color = Window.ColorDefault, size = Window.FontHuge, alignment = Window.AlignmentCenter, bold = True, uppercase = True):
		dimension = self._dimensionLine()
		control = self._addLabel(text = text, x = self._centerX(dimension[0]), y = self._offsetY(), width = dimension[0], height = dimension[1], color = color, size = size, alignment = alignment, bold = bold, uppercase = uppercase)
		return control, dimension

	def _addStatus(self, text = None):
		if text == None: text = self.mStatus
		self.mStatusControl, dimension = self._addLine(text = text, color = self.ColorHighlight)
		return dimension

class WindowScrape(WindowProgress):

	def __init__(self, backgroundType, backgroundPath, logo, status):
		super(WindowScrape, self).__init__(backgroundType = backgroundType, backgroundPath = backgroundPath, logo = logo, status = status)

		self.mTime = None
		self.mStreamsTotal = 0
		self.mStreamsHdUltra = 0
		self.mStreamsHd1080 = 0
		self.mStreamsHd720 = 0
		self.mStreamsSd = 0
		self.mStreamsLd = 0
		self.mStreamsTorrent = 0
		self.mStreamsUsenet = 0
		self.mStreamsHoster = 0
		self.mStreamsCached = 0
		self.mStreamsDebrid = 0
		self.mStreamsDirect = 0
		self.mStreamsPremium = 0
		self.mStreamsLocal = 0
		self.mStreamsFinished = 0
		self.mStreamsBusy = 0
		self.mProvidersFinished = 0
		self.mProvidersBusy = 0
		self.mProvidersLabels = None

		self.mControlDetails = None
		self.mControlStreams1 = None
		self.mControlStreams2 = None
		self.mControlStreams3 = None
		self.mControlStreams4 = None
		self.mControlProcessed = None
		self.mControlProviders = None
		self.mControlCancel = None

		self._onAction(WindowBase.ActionMoveLeft, self._actionFocus)
		self._onAction(WindowBase.ActionMoveRight, self._actionFocus)
		self._onAction(WindowBase.ActionMoveUp, self._actionFocus)
		self._onAction(WindowBase.ActionMoveDown, self._actionFocus)
		self._onAction(WindowBase.ActionItemNext, self._actionFocus)
		self._onAction(WindowBase.ActionItemPrevious, self._actionFocus)
		self._onAction(WindowBase.ActionSelectItem, self._actionFocus)

	def __del__(self):
		super(WindowScrape, self).__del__()

	def _initializeStart(self):
		super(WindowScrape, self)._initializeStart()
		self._dimensionUpdate(self._dimensionSeparator())
		self._dimensionUpdate(self._dimensionLine())
		self._dimensionUpdate(self._dimensionSeparator())
		self._dimensionUpdate(self._dimensionLine())
		self._dimensionUpdate(self._dimensionLine())
		self._dimensionUpdate(self._dimensionLine())
		self._dimensionUpdate(self._dimensionLine())
		self._dimensionUpdate(self._dimensionSeparator())
		self._dimensionUpdate(self._dimensionLine())
		if tools.Settings.getBoolean('interface.navigation.scrape.providers'): self._dimensionUpdate(self._dimensionLine())
		self._dimensionUpdate(self._dimensionSeparator())
		self._dimensionUpdate(self._dimensionCancel())

	def _initializeEnd(self):
		super(WindowScrape, self)._initializeEnd()
		self._dimensionUpdate(self._addSeparator())
		self._dimensionUpdate(self._addDetails())
		self._dimensionUpdate(self._addSeparator())
		self._dimensionUpdate(self._addStreams1())
		self._dimensionUpdate(self._addStreams2())
		self._dimensionUpdate(self._addStreams3())
		self._dimensionUpdate(self._addStreams4())
		self._dimensionUpdate(self._addSeparator())
		self._dimensionUpdate(self._addProcessed())
		if tools.Settings.getBoolean('interface.navigation.scrape.providers'): self._dimensionUpdate(self._addProviders())
		self._dimensionUpdate(self._addSeparator())
		self._dimensionUpdate(self._addCancel())

	@classmethod
	def show(self, background = None, status = True, wait = False, initialize = True, close = False):
		return super(WindowScrape, self).show(backgroundType = tools.Settings.getInteger('interface.navigation.scrape.background'), backgroundPath = background, logo = self.LogoIcon, status = status, wait = wait, initialize = initialize, close = close)

	@classmethod
	def update(self, progress = None, finished = None, status = None, time = None, streamsTotal = None, streamsHdUltra = None, streamsHd1080 = None, streamsHd720 = None, streamsSd = None, streamsLd = None, streamsTorrent = None, streamsUsenet = None, streamsHoster = None, streamsCached = None, streamsDebrid = None, streamsDirect = None, streamsPremium = None, streamsLocal = None, streamsFinished = None, streamsBusy = None, providersFinished = None, providersBusy = None, providersLabels = None):
		instance = super(WindowScrape, self).update(progress = progress, finished = finished, status = status)
		if instance == None: return instance
		instance._lock()

		if not time == None: instance.mTime = time
		if not streamsTotal == None: instance.mStreamsTotal = streamsTotal
		if not streamsHdUltra == None: instance.mStreamsHdUltra = streamsHdUltra
		if not streamsHd1080 == None: instance.mStreamsHd1080 = streamsHd1080
		if not streamsHd720 == None: instance.mStreamsHd720 = streamsHd720
		if not streamsSd == None: instance.mStreamsSd = streamsSd
		if not streamsLd == None: instance.mStreamsLd = streamsLd
		if not streamsTorrent == None: instance.mStreamsTorrent = streamsTorrent
		if not streamsUsenet == None: instance.mStreamsUsenet = streamsUsenet
		if not streamsHoster == None: instance.mStreamsHoster = streamsHoster
		if not streamsCached == None: instance.mStreamsCached = streamsCached
		if not streamsDebrid == None: instance.mStreamsDebrid = streamsDebrid
		if not streamsDirect == None: instance.mStreamsDirect = streamsDirect
		if not streamsPremium == None: instance.mStreamsPremium = streamsPremium
		if not streamsLocal == None: instance.mStreamsLocal = streamsLocal
		if not streamsFinished == None: instance.mStreamsFinished = streamsFinished
		if not streamsBusy == None: instance.mStreamsBusy = streamsBusy
		if not providersFinished == None: instance.mProvidersFinished = providersFinished
		if not providersBusy == None: instance.mProvidersBusy = providersBusy
		try: instance.mProvidersLabels = providersLabels[:3]
		except: instance.mProvidersLabels = providersLabels

		if not progress == None or not time == None:
			labels = []
			labels.append('%s: %s %%' % (interface.Translation.string(32037), instance._highlight(instance.mProgress)))
			labels.append('%s: %s %s' % (interface.Translation.string(35029), instance._highlight(instance.mTime), interface.Translation.string(32405)))
			instance._setLabel(control = instance.mControlDetails, text = self._separator(labels), size = self.FontHuge, bold = True, uppercase = True)

		if not streamsTotal == None:
			label = 'STREAMS FOUND: ' + instance._highlight(instance.mStreamsTotal)
			instance._setLabel(control = instance.mControlStreams1, text = label, size = self.FontHuge, bold = True, uppercase = True)

		if not streamsTorrent == None or not streamsUsenet == None or not streamsHoster == None:
			labels = []
			labels.append('TORRENT: ' + instance._highlight(instance.mStreamsTorrent))
			labels.append('USENET: ' + instance._highlight(instance.mStreamsUsenet))
			labels.append('HOSTER: ' + instance._highlight(instance.mStreamsHoster))
			instance._setLabel(control = instance.mControlStreams2, text = self._separator(labels), size = self.FontHuge, bold = True, uppercase = True)

		if not streamsHdUltra == None or not streamsHd1080 == None or not streamsHd720 == None or not streamsSd == None or not streamsLd == None:
			labels = []
			labels.append('HDULTRA: ' + instance._highlight(instance.mStreamsHdUltra))
			labels.append('HD1080: ' + instance._highlight(instance.mStreamsHd1080))
			labels.append('HD720: ' + instance._highlight(instance.mStreamsHd720))
			labels.append('SD: ' + instance._highlight(instance.mStreamsSd))
			labels.append('LD: ' + instance._highlight(instance.mStreamsLd))
			instance._setLabel(control = instance.mControlStreams3, text = self._separator(labels), size = self.FontHuge, bold = True, uppercase = True)

		if not streamsCached == None or not streamsDebrid == None or not streamsDirect == None or not streamsPremium == None or not streamsLocal == None:
			labels = []
			labels.append('CACHED: ' + instance._highlight(instance.mStreamsCached))
			labels.append('DEBRID: ' + instance._highlight(instance.mStreamsDebrid))
			labels.append('DIRECT: ' + instance._highlight(instance.mStreamsDirect))
			labels.append('PREMIUM: ' + instance._highlight(instance.mStreamsPremium))
			labels.append('LOCAL: ' + instance._highlight(instance.mStreamsLocal))
			instance._setLabel(control = instance.mControlStreams4, text = self._separator(labels), size = self.FontHuge, bold = True, uppercase = True)

		if instance.mStreamsFinished > 0 or instance.mStreamsBusy > 0:
			labels = []
			labels.append('FINISHED STREAMS: ' + instance._highlight(instance.mStreamsFinished))
			labels.append('BUSY STREAMS: ' + instance._highlight(instance.mStreamsBusy))
			instance._setLabel(control = instance.mControlProcessed, text = self._separator(labels), size = self.FontHuge, bold = True, uppercase = True)
		elif not providersFinished == None or not providersBusy == None:
			labels = []
			labels.append('BUSY PROVIDERS: ' + instance._highlight(instance.mProvidersBusy))
			labels.append('FINISHED PROVIDERS: ' + instance._highlight(instance.mProvidersFinished))
			instance._setLabel(control = instance.mControlProcessed, text = self._separator(labels), size = self.FontHuge, bold = True, uppercase = True)

		if not instance.mControlProviders == None:
			try:
				if instance.mProvidersLabels is None: label = 'PROVIDERS STARTED'
				elif len(instance.mProvidersLabels) == 0: label = 'PROVIDERS FINISHED'
				else: label = self._separator([i.encode('utf-8') for i in instance.mProvidersLabels]) # Must be encoded, otherwise throws UnicodeDecodeError on some machines.
				instance._setLabel(control = instance.mControlProviders, text = label, size = self.FontHuge, bold = True, uppercase = True)
			except:
				tools.Logger.error()

		instance._unlock()
		return instance

	@classmethod
	def enabled(self):
		return tools.Settings.getInteger('interface.navigation.scrape') == 0

	def _actionFocus(self):
		try: self.focus(self.mControlCancel[0])
		except: pass

	def _dimensionCancel(self):
		return self._dimensionButton(text = 33743, icon = True)

	def _addDetails(self):
		self.mControlDetails, dimension = self._addLine()
		return dimension

	def _addStreams1(self):
		self.mControlStreams1, dimension = self._addLine()
		return dimension

	def _addStreams2(self):
		self.mControlStreams2, dimension = self._addLine()
		return dimension

	def _addStreams3(self):
		self.mControlStreams3, dimension = self._addLine()
		return dimension

	def _addStreams4(self):
		self.mControlStreams4, dimension = self._addLine()
		return dimension

	def _addProcessed(self):
		self.mControlProcessed, dimension = self._addLine()
		return dimension

	def _addProviders(self):
		self.mControlProviders, dimension = self._addLine()
		return dimension

	def _addCancel(self):
		dimension = self._dimensionCancel()
		x = self._centerX(dimension[0])
		y = self._offsetY() + self._scaleHeight(20)
		self.mControlCancel = self._addButton(text = 33743, x = x, y = y, callback = self.close, icon = 'error')
		return dimension

class WindowPlayback(WindowProgress):

	def __init__(self, backgroundType, backgroundPath, logo, status, retry):
		super(WindowPlayback, self).__init__(backgroundType = backgroundType, backgroundPath = backgroundPath, logo = logo, status = status)
		self.mRetry = retry
		self.mRetryCount = None
		self.mControlSeparator1 = None
		self.mControlSeparator2 = None
		self.mControlSubstatus = None
		self.mControlRetries = None
		self.mControlCancel = None

		self._onAction(WindowBase.ActionMoveLeft, self._actionFocus)
		self._onAction(WindowBase.ActionMoveRight, self._actionFocus)
		self._onAction(WindowBase.ActionMoveUp, self._actionFocus)
		self._onAction(WindowBase.ActionMoveDown, self._actionFocus)
		self._onAction(WindowBase.ActionItemNext, self._actionFocus)
		self._onAction(WindowBase.ActionItemPrevious, self._actionFocus)
		self._onAction(WindowBase.ActionSelectItem, self._actionFocus)

	def __del__(self):
		super(WindowPlayback, self).__del__()

	def _initializeStart(self, retry = False):
		super(WindowPlayback, self)._initializeStart()
		if self.mRetry:
			self._dimensionUpdate(self._dimensionSeparator())
			self._dimensionUpdate(self._dimensionLine())
			self._dimensionUpdate(self._dimensionLine())
			self._dimensionUpdate(self._dimensionSeparator())
		self._dimensionUpdate(self._dimensionCancel())

	def _initializeEnd(self, retry = False):
		super(WindowPlayback, self)._initializeEnd()
		if self.mRetry:
			self._dimensionUpdate(self._addSeparator1())
			self._dimensionUpdate(self._addSubstatus())
			self._dimensionUpdate(self._addRetries())
			self._dimensionUpdate(self._addSeparator2())
		self._dimensionUpdate(self._addCancel())

	@classmethod
	def show(self, background = None, status = True, wait = False, initialize = True, close = False, retry = False):
		return super(WindowPlayback, self).show(backgroundType = tools.Settings.getInteger('interface.navigation.playback.background'), backgroundPath = background, logo = self.LogoIcon, status = status, wait = wait, initialize = initialize, close = close, retry = retry)

	@classmethod
	def update(self, progress = None, finished = None, status = None, substatus1 = None, substatus2 = None, total = None, remaining = None):
		instance = super(WindowPlayback, self).update(progress = progress, finished = finished, status = status)
		if instance == None: return instance
		instance._lock()

		try:
			remaining += 1 # Otherwise it shows "0 of 2" after the first retry. Just looks better as "1 of 2".
			retry = not((total - remaining) == 0)
		except: retry = False

		if retry and not remaining == instance.mRetryCount:
			background = instance.mBackgroundPath
			instance._unlock()
			interface.Loader.show()
			instance.close(loader = False)
			self.show(background = background, status = True, retry = True)
			instance = super(WindowPlayback, self).update(progress = progress, finished = finished, status = status)
			interface.Loader.hide()
			if instance == None: return instance
			instance._lock()
			instance.mRetryCount = remaining

		if retry:
			if not substatus1 == None or not substatus2 == None:
				labels = []
				labels.append(substatus1)
				labels.append(substatus2)
				instance._setLabel(control = instance.mControlSubstatus, text = self._separator(labels), size = self.FontHuge, bold = True, uppercase = True)

			if not total == None or not remaining == None:
				labels = []
				labels.append('%s: %s' % (interface.Translation.string(35475), instance._highlight(remaining)))
				labels.append('%s: %s' % (interface.Translation.string(35476), instance._highlight(total)))
				instance._setLabel(control = instance.mControlRetries, text = self._separator(labels), size = self.FontHuge, bold = True, uppercase = True)

		instance._unlock()
		return instance

	@classmethod
	def enabled(self):
		return tools.Settings.getInteger('interface.navigation.playback') == 0

	def _actionFocus(self):
		try: self.focus(self.mControlCancel[0])
		except: pass

	def _dimensionCancel(self):
		return self._dimensionButton(text = 33743, icon = True)

	def _addSeparator1(self):
		self.mControlSeparator1, dimension = self._addSeparator(control = True)
		return dimension

	def _addSeparator2(self):
		self.mControlSeparator2, dimension = self._addSeparator(control = True)
		return dimension

	def _addSubstatus(self):
		self.mControlSubstatus, dimension = self._addLine()
		return dimension

	def _addRetries(self):
		self.mControlRetries, dimension = self._addLine()
		return dimension

	def _addCancel(self):
		dimension = self._dimensionCancel()
		x = self._centerX(dimension[0])
		y = self._offsetY() + self._scaleHeight(20)
		self.mControlCancel = self._addButton(text = 33743, x = x, y = y, callback = self.close, icon = 'error')
		return dimension

class WindowStreams(WindowProgress):

	def __init__(self, backgroundType, backgroundPath, logo, status, xmlType):
		super(WindowStreams, self).__init__(backgroundType = backgroundType, backgroundPath = backgroundPath, logo = logo, status = status, xml = 'streams', xmlScale = True, xmlType = xmlType)
		self._onAction(WindowBase.ActionContextMenu, self._actionContext)
		self._onAction(WindowBase.ActionShowInfo, self._actionInformation)
		self._onClick(self.IdListControl, self._actionSelect)

	def __del__(self):
		super(WindowStreams, self).__del__()

	@classmethod
	def show(self, background = None, status = True, wait = False, initialize = True, close = False):
		backgroundType = tools.Settings.getInteger('interface.navigation.streams.background')
		decorations = tools.Settings.getInteger('interface.navigation.streams.decorations')
		if decorations == 0: decorations = self.TypePlain
		elif decorations == 1: decorations = self.TypeBasic
		elif decorations == 2: decorations = self.TypeIcons
		else: decorations = self.TypePlain
		return super(WindowStreams, self)._show(xmlType = decorations, backgroundType = backgroundType, backgroundPath = background, logo = self.LogoIcon, status = status, wait = wait, initialize = initialize, close = close)

	@classmethod
	def update(self, progress = None, finished = None, status = None):
		instance = super(WindowStreams, self).update(progress = progress, finished = finished, status = status)
		try:
			if finished: instance._remove()
		except: pass

	@classmethod
	def enabled(self):
		return tools.Settings.getInteger('interface.navigation.streams') == 0

	def _initializeEnd(self):
		# Create the main background.
		self._addBackground(type = self.mBackgroundType, path = self.mBackgroundPath, fixed = True)

	def _initializeAfter(self):
		# The XML interface is only created during doModal().
		# In order to create the loader on top of the XML, it must be added AFTER the window has been shown.
		super(WindowStreams, self)._initializeEnd()
		super(WindowStreams, self)._initializeAfter()

	def _actionSelect(self):
		path = self.control(self.IdListControl).getSelectedItem().getProperty('GaiaAction')
		tools.System.executePlugin(command = path)

	def _actionInformation(self):
		# This only works if the user has opened the information dialog on the normal movie/episode menu before.
		# This adds the metadata to memory and when the window is opened from here, it will correctly display the metadata.
		# But if the information was not displayed before, this window stays empty.
		# Use the ExtendedInfo dialog instead.
		#Window.show(self.IdWindowInformation)
		tools.Information.show()

	def _actionContext(self):
		index = self.control(self.IdListControl).getSelectedPosition()
		if index >= 0:
			self.focus(50000)
			self.mContexts[index].show()
