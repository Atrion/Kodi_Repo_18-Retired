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
# ORIONPLATFORM
##############################################################################
# Class for detecting the operating system.
##############################################################################

import platform
import subprocess
from orion.modules.oriontools import *

OrionPlatformInstance = None

class OrionPlatform:

	##############################################################################
	# CONSTANTS
	##############################################################################

	FamilyWindows = 'windows'
	FamilyUnix = 'unix'

	SystemWindows = 'windows'
	SystemMacintosh = 'macintosh'
	SystemLinux = 'linux'
	SystemAndroid = 'android'

	Architecture64bit = '64bit'
	Architecture32bit = '32bit'
	ArchitectureArm = 'arm'

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

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

	##############################################################################
	# INSTANCE
	##############################################################################

	@classmethod
	def instance(self):
		global OrionPlatformInstance
		if OrionPlatformInstance == None:
			OrionPlatformInstance = OrionPlatform()
		return OrionPlatformInstance

		platform.familyName()

	##############################################################################
	# LABEL
	##############################################################################

	@classmethod
	def label(self):
		instance = self.instance()
		system = OrionTools.unicode(instance.mDistributionName) + ' ' + OrionTools.unicode(instance.mVersionShort) + ' (' + OrionTools.unicode(instance.mVersionFull) + ')'
		return ' | '.join([OrionTools.unicode(instance.mFamilyName), OrionTools.unicode(instance.mSystemName), OrionTools.unicode(instance.mArchitecture), system])

	##############################################################################
	# FAMILY
	##############################################################################

	@classmethod
	def familyType(self):
		return self.instance().mFamilyType

	@classmethod
	def familyName(self):
		return self.instance().mFamilyName

	##############################################################################
	# SYSTEM
	##############################################################################

	@classmethod
	def systemType(self):
		return self.instance().mSystemType

	@classmethod
	def systemName(self):
		return self.instance().mSystemName

	##############################################################################
	# DISTRIBUTION
	##############################################################################

	@classmethod
	def distributionType(self):
		return self.instance().mDistributionType

	@classmethod
	def distributionName(self):
		return self.instance().mDistributionName

	##############################################################################
	# VERSION
	##############################################################################

	@classmethod
	def versionShort(self):
		return self.instance().mVersionShort

	@classmethod
	def versionFull(self):
		return self.instance().mVersionFull

	##############################################################################
	# ARCHITECTURE
	##############################################################################

	@classmethod
	def architecture(self):
		return self.instance().mArchitecture

	##############################################################################
	# AGENT
	##############################################################################

	@classmethod
	def agent(self):
		return self.instance().mAgent

	##############################################################################
	# DETECT
	##############################################################################

	@classmethod
	def _detectWindows(self):
		try: return OrionPlatform.SystemWindows in platform.system().lower()
		except: return False

	@classmethod
	def _detectMacintosh(self):
		try:
			version = platform.mac_ver()
			return not version[0] == None and not version[0] == ''
		except: return False

	@classmethod
	def _detectLinux(self):
		try: return platform.system().lower() == 'linux' and not self._detectAndroid()
		except: return False

	@classmethod
	def _detectAndroid(self):
		try:
			system = platform.system().lower()
			distribution = platform.linux_distribution()
			if OrionPlatform.SystemAndroid in system or OrionPlatform.SystemAndroid in system or (len(distribution) > 0 and OrionTools.isString(distribution[0]) and OrionPlatform.SystemAndroid in distribution[0].lower()):
				return True
			if system == OrionPlatform.SystemLinux:
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
		try:
			if self._detectWindows():
				self.mFamilyType = OrionPlatform.FamilyWindows
				self.mFamilyName = self.mFamilyType.capitalize()

				self.mSystemType = OrionPlatform.SystemWindows
				self.mSystemName = self.mSystemType.capitalize()

				version = platform.win32_ver()
				self.mVersionShort = version[0]
				self.mVersionFull = version[1]
			elif self._detectAndroid():
				self.mFamilyType = OrionPlatform.FamilyUnix
				self.mFamilyName = self.mFamilyType.capitalize()

				self.mSystemType = OrionPlatform.SystemAndroid
				self.mSystemName =  self.mSystemType.capitalize()

				distribution = platform.linux_distribution()
				self.mVersionShort = distribution[1]
				self.mVersionFull = distribution[2]
			elif self._detectMacintosh():
				self.mFamilyType = OrionPlatform.FamilyUnix
				self.mFamilyName = self.mFamilyType.capitalize()

				self.mSystemType = OrionPlatform.SystemMacintosh
				self.mSystemName =  self.mSystemType.capitalize()

				mac = platform.mac_ver()
				self.mVersionShort = mac[0]
				self.mVersionFull = self.mVersionShort
			elif self._detectLinux():
				self.mFamilyType = OrionPlatform.FamilyUnix
				self.mFamilyName = self.mFamilyType.capitalize()

				self.mSystemType = OrionPlatform.SystemLinux
				self.mSystemName =  self.mSystemType.capitalize()

				distribution = platform.linux_distribution()
				self.mDistributionType = distribution[0].lower().replace('"', '').replace(' ', '')
				self.mDistributionName = distribution[0].replace('"', '')

				self.mVersionShort = distribution[1]
				self.mVersionFull = distribution[2]

			machine = platform.machine().lower()
			if '64' in machine: self.mArchitecture = OrionPlatform.Architecture64bit
			elif '86' in machine or '32' in machine or 'i386' in machine or 'i686' in machine: self.mArchitecture = OrionPlatform.Architecture32bit
			elif 'arm' in machine or 'risc' in machine or 'acorn' in machine: self.mArchitecture = OrionPlatform.ArchitectureArm

			try:
				system = ''
				if self.mSystemType == OrionPlatform.SystemWindows:
					system += 'Windows NT'
					if self.mVersionFull: system += ' ' + self.mVersionFull
					if self.mArchitecture == OrionPlatform.Architecture64bit: system += '; Win64; x64'
					elif self.mArchitecture == OrionPlatform.ArchitectureArm: system += '; ARM'
				elif self.mSystemType == OrionPlatform.SystemMacintosh:
					system += 'Macintosh; Intel Mac OS X ' + self.mVersionShort.replace('.', '_')
				elif self.mSystemType == OrionPlatform.SystemLinux:
					system += 'X11;'
					if self.mDistributionName: system += ' ' + self.mDistributionName + ';'
					system += ' Linux;'
					if self.mArchitecture == OrionPlatform.Architecture32bit: system += ' x86'
					elif self.mArchitecture == OrionPlatform.Architecture64bit: system += ' x86_64'
					elif self.mArchitecture == OrionPlatform.ArchitectureArm: system += ' arm'
				elif self.mSystemType == OrionPlatform.SystemAndroid:
					system += 'Linux; Android ' + self.mVersionShort
				if not system == '': system = '(' + system + ') '
				system = OrionTools.addonName() + '/' + OrionTools.addonVersion() + ' ' + system + 'Kodi/' + str(OrionTools.kodiVersion())

				# Do in 2 steps, previous statement can fail
				self.mAgent = system
			except:
				OrionTools.error()

		except:
			OrionTools.error()
