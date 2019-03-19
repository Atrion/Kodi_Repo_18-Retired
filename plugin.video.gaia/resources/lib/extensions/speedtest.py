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
import time
import urllib
import threading
import random
from resources.lib.externals.speedtest import speedtest
from resources.lib.extensions import interface
from resources.lib.extensions import tools
from resources.lib.extensions import convert
from resources.lib.extensions import network
from resources.lib.extensions import debrid
from resources.lib.extensions import api
from resources.lib.modules import client
from resources.lib.modules import workers

class SpeedTester(object):

	Unknown = 'unknown'
	UnknownCapitalize = Unknown.capitalize()

	UpdateNone = None
	UpdateAsk = 'ask'
	UpdateBoth = 'both'
	UpdateManual = 'manual'
	UpdateAutomatic = 'automatic'
	UpdateDefault = UpdateNone

	PhaseLatency = 'latency'
	PhaseDownload = 'download'
	PhaseUpload = 'upload'

	PerformanceSlow = 'slow'
	PerformanceMedium = 'medium'
	PerformanceFast = 'fast'

	PerformanceLatencySlow = 4000 # ms
	PerformanceLatencyMedium = 2000 # ms

	PerformanceSpeedSlow = 4194304 # 4 mbps
	PerformanceSpeedMedium = 20971520 # 20 mbps

	def __init__(self, name, phases):
		self.mId = name.lower()
		self.mName = name
		self.mMode = None

		self.mPhases = phases
		self.mPhase = None

		self.mLatency = None
		self.mDownload = None
		self.mUpload = None

		self.mCurrent = 0
		self.mError = False

		self.mInformation = None
		self.mInformationNetwork = None

	def latency(self):
		return self.mLatency

	def download(self):
		return self.mDownload

	def upload(self):
		return self.mUpload

	def latencySet(self, value):
		self.mLatency = value

	def downloadSet(self, value):
		self.mDownload = value

	def uploadSet(self, value):
		self.mUpload = value

	def formatLatency(self, unknown = UnknownCapitalize):
		if self.mLatency: return self._formatLatency(self.mLatency)
		else: return unknown

	def formatDownload(self, unknown = UnknownCapitalize):
		if self.mDownload: return self._formatSpeed(self.mDownload)
		else: return unknown

	def formatUpload(self, unknown = UnknownCapitalize):
		if self.mUpload: return self._formatSpeed(self.mUpload)
		else: return unknown

	def performance(self, test = True):
		if test:
			self.testLatency()
			self.testDownload()

		if self.mLatency == None or self.mLatency <= 0 or self.mDownload == None or self.mDownload <= 0:
			performance = SpeedTester.PerformanceMedium
		elif self.mDownload <= SpeedTester.PerformanceSpeedSlow:
			performance = SpeedTester.PerformanceSlow
		elif self.mDownload <= SpeedTester.PerformanceSpeedMedium:
			if self.mLatency >= SpeedTester.PerformanceLatencySlow:
				performance = SpeedTester.PerformanceSlow
			else:
				performance = SpeedTester.PerformanceMedium
		else:
			if self.mLatency >= SpeedTester.PerformanceLatencySlow:
				performance = SpeedTester.PerformanceSlow
			elif self.mLatency >= SpeedTester.PerformanceLatencySlow:
				performance = SpeedTester.PerformanceMedium
			else:
				performance = SpeedTester.PerformanceFast

		return performance

	def _validate(self):
		return True

	@classmethod
	def _formatLatency(self, latency):
		if not latency: # Use not to check for both None and 0.
			return SpeedTester.UnknownCapitalize
		else:
			return '%.0f ms' % latency

	@classmethod
	def _formatSpeed(self, speed):
		if not speed: # Use not to check for both None and 0.
			return SpeedTester.UnknownCapitalize
		else:
			return convert.ConverterSpeed(value = speed, unit = convert.ConverterSpeed.Bit).stringOptimal(unit = convert.ConverterSpeed.Bit, notation = convert.ConverterSpeed.SpeedLetter)

	@classmethod
	def _formatSpeedLatency(self, speed = None, latency = None, ignore = False):
		if not speed and not latency: # Use not to check for both None and 0.
			return interface.Translation.string(33387)
		else:
			if ignore:
				if not speed: return self._formatLatency(latency)
				elif not latency: return self._formatLatency(speed)
			return '%s (%s)' % (self._formatSpeed(speed), self._formatLatency(latency))

	def _formatDifference(self, local, community, formatter, colorPositive, colorNegative, colorNeutral):
		differenceLabel = ''
		if not community:
			return SpeedTester.UnknownCapitalize
		if local:
			difference = local - community
			differenceAbsolute = abs(difference)
			differenceAbsolute = formatter(differenceAbsolute)
			if difference > 0: differenceLabel = interface.Format.color('+ %s' % differenceAbsolute, colorPositive)
			elif difference < 0: differenceLabel = interface.Format.color('- %s' % differenceAbsolute, colorNegative)
			else: differenceLabel = interface.Format.color(differenceAbsolute, colorNeutral)
			differenceLabel = ' (%s)' % differenceLabel
		return '%s%s' % (formatter(community), differenceLabel)

	def _formatDifferenceLatency(self, local, community):
		return self._formatDifference(local = local, community = community, formatter = self._formatLatency, colorPositive = interface.Format.ColorBad, colorNegative = interface.Format.ColorExcellent, colorNeutral = interface.Format.ColorMedium)

	def _formatDifferenceSpeed(self, local, community):
		return self._formatDifference(local = local, community = community, formatter = self._formatSpeed, colorPositive = interface.Format.ColorExcellent, colorNegative = interface.Format.ColorBad, colorNeutral = interface.Format.ColorMedium)

	def _informationInternal(self, service = api.Api.ServiceNone, selection = api.Api.SelectionAverage):
		self.mInformation = self._information(service = service, selection = selection, networkInformation = True)
		if self.mInformation:
			self.mInformationNetwork = self.mInformation[1]
			self.mInformation = self.mInformation[0]
		return self.mInformation

	@classmethod
	def _information(self, service = api.Api.ServiceNone, selection = api.Api.SelectionAverage, networkInformation = False):
		try:
			information = network.Networker.information()
			continent = information['global']['location']['continent']['name']
			country = information['global']['location']['country']['name']
			region = information['global']['location']['region']['name']
			city = information['global']['location']['city']['name']

			result = api.Api.speedtestRetrieve(service = service, selection = selection, continent = continent, country = country, region = region, city = city)
			if result:
				result = result[selection]
				if networkInformation: return (result, information)
				else: return result
		except:
			tools.Logger.error()
		return None

	'''
		items = [
			{
				'name' : string, // Made bold
				'description' : string, // Made non-bold
				'result' : anything,
			}
		]
	'''
	@classmethod
	def _testDialog(self, options):
		if options == None or len(options) == 0:
			return None

		items = []
		for option in options:
			name = option['name'] if 'name' in option else None
			description = option['description'] if 'description' in option else None
			item = ''
			if name: item += interface.Format.bold(interface.Translation.string(name))
			if name and description: item += interface.Format.bold(': ')
			if description: item += interface.Translation.string(description)
			items.append(item)

		choice = interface.Dialog.options(title = 33030, items = items)
		if choice < 0: return None
		else: return choice

	def _testSelection(self):
		return True

	def _testLatency(self):
		return None

	def _testDownload(self):
		return None

	def _testUpload(self):
		return None

	def testLatency(self, format = False):
		try:
			self.mPhase = SpeedTester.PhaseLatency
			latency = self._testLatency()
			if latency == 0 or latency == 10000: self.mLatency = None # Global speed test failures lasts a maximum of 10 secs.
			else: self.mLatency = latency
			if format: latency = self._formatLatency(latency)
			return latency
		except:
			tools.Logger.error()
			self.mError = True
		return None

	def testDownload(self, format = False):
		try:
			self.mPhase = SpeedTester.PhaseDownload
			download = self._testDownload()
			if download == 0: self.mDownload = None
			else: self.mDownload = download
			if format: download = self._formatSpeed(download)
			return download
		except:
			tools.Logger.error()
			self.mError = True
		return None

	def testUpload(self, format = False):
		try:
			self.mPhase = SpeedTester.PhaseUpload
			upload = self._testUpload()
			if upload == 0: self.mUpload = None
			else: self.mUpload = upload
			if format: upload = self._formatSpeed(upload)
			return upload
		except:
			tools.Logger.error()
			self.mError = True
		return None

	def test(self, format = True):
		self.mPhase = None
		self.mError = False
		self.mCurrent = 0
		result = {}

		if SpeedTester.PhaseLatency in self.mPhases:
			self.mCurrent += 1
			result[SpeedTester.PhaseLatency] = self.testLatency(format)
		if SpeedTester.PhaseDownload in self.mPhases:
			self.mCurrent += 1
			result[SpeedTester.PhaseDownload] = self.testDownload(format)
		if SpeedTester.PhaseUpload in self.mPhases:
			self.mCurrent += 1
			result[SpeedTester.PhaseUpload] = self.testUpload(format)

		return result

	@classmethod
	def select(self, update = UpdateNone):
		self.participation()
		options = [
			{
				'name' : interface.Translation.string(33509) + ' ' + interface.Translation.string(33030),
				'result' : SpeedTesterGlobal(),
			},
			{
				'name' : interface.Translation.string(33566) + ' ' + interface.Translation.string(33030),
				'result' : SpeedTesterPremiumize(),
			},
			{
				'name' : interface.Translation.string(35200) + ' ' + interface.Translation.string(33030),
				'result' : SpeedTesterOffCloud(),
			},
			{
				'name' : interface.Translation.string(33567) + ' ' + interface.Translation.string(33030),
				'result' : SpeedTesterRealDebrid(),
			},
			{
				'name' : interface.Translation.string(33794) + ' ' + interface.Translation.string(33030),
				'result' : SpeedTesterEasyNews(),
			},
		]
		choice = self._testDialog(options)
		if choice == None: return False
		options[choice]['result'].show(update = update)

	def show(self, update = UpdateDefault):
		self.participation()

		self.mMode = self._testSelection()
		if self.mMode == False: return
		try: self.mMode = self.mMode.lower()
		except: self.mMode = None

		if not self._validate(): return

		self.mPhase = None
		self.mError = False

		title = 'Speed Test'
		message = 'Testing the internet connection %s:'
		info = message % 'capabilities'
		progressDialog = interface.Dialog.progress(title = title, message = info)

		dots = ''
		stringLatency = '%s     %s: ' % (interface.Format.fontNewline(), interface.Translation.string(33858))
		stringSpeedDownload = '%s     %s: ' % (interface.Format.fontNewline(), interface.Translation.string(33074))
		stringSpeedUpload = '%s     %s: ' % (interface.Format.fontNewline(), interface.Translation.string(33859))

		threadInformation = workers.Thread(self._informationInternal, self.mId)
		threadInformation.start()

		thread = workers.Thread(self.test)
		thread.start()

		while True:
			try:
				if self.mError: break
				try:
					# NB: Do not check for abort here. This will cause the speedtest to close automatically in the configuration wizard.
					if progressDialog.iscanceled(): return None
				except: pass

				if self.mPhase == SpeedTester.PhaseLatency:
					info = message % 'latency'
				elif self.mPhase == SpeedTester.PhaseDownload:
					info = message % 'download speed'
				elif self.mPhase == SpeedTester.PhaseUpload:
					info = message % 'upload speed'
				else:
					info = message % 'capabilities'

				dots += '.'
				if len(dots) > 3: dots = ''

				if self.mPhase == SpeedTester.PhaseLatency:
					if SpeedTester.PhaseLatency in self.mPhases:
						info += stringLatency + dots
				elif self.mPhase == SpeedTester.PhaseDownload:
					if SpeedTester.PhaseLatency in self.mPhases:
						info += stringLatency + self._formatLatency(self.mLatency)
					if SpeedTester.PhaseDownload in self.mPhases:
						info += stringSpeedDownload + dots
				elif self.mPhase == SpeedTester.PhaseUpload:
					if SpeedTester.PhaseLatency in self.mPhases:
						info += stringLatency + self._formatLatency(self.mLatency)
					if SpeedTester.PhaseDownload in self.mPhases:
						info += stringSpeedDownload + self._formatSpeed(self.mDownload)
					if SpeedTester.PhaseUpload in self.mPhases:
						info += stringSpeedUpload + dots

				lines = 4 - info.count(interface.Format.fontNewline())
				for i in range(max(0, lines)):
					info += interface.Format.fontNewline()

				try: progressDialog.update(int((max(0, self.mCurrent - 1) / len(self.mPhases)) * 100), info)
				except: pass

				if not thread.is_alive(): break
				if self.mError: break
				time.sleep(0.5)
			except:
				tools.Logger.error()

		threadInformation.join()

		try: progressDialog.close()
		except: pass

		if self.mError:
			interface.Dialog.confirm(title = title, message = 'The internet connection can currently not be tested. Please try again later.')
		else:
			self._share()

			items = []

			itemsCategory = []
			if SpeedTester.PhaseLatency in self.mPhases:
				itemsCategory.append({ 'title' : 33858, 'value' : self._formatLatency(self.mLatency) })
			if SpeedTester.PhaseDownload in self.mPhases:
				itemsCategory.append({ 'title' : 33074, 'value' : self._formatSpeed(self.mDownload) })
			if SpeedTester.PhaseUpload in self.mPhases:
				itemsCategory.append({ 'title' : 33859, 'value' : self._formatSpeed(self.mUpload) })
			items.append({'title' : 33860, 'items' : itemsCategory})

			if self.mInformation:
				areas = ['international', 'continent', 'country', 'region', 'city']
				titles = [33861, 33862, 33863, 33864, 33865]
				networkInformation = self.mInformationNetwork['global']['location']

				for i in range(len(titles)):
					itemsCategory = []

					if areas[i] in networkInformation:
						location = networkInformation[areas[i]]['name']
						if not location: location = SpeedTester.UnknownCapitalize
						itemsCategory.append({ 'title' : 33874, 'value' : location })

					area = self.mInformation[areas[i]]

					if SpeedTester.PhaseLatency in self.mPhases:
						itemsCategory.append({ 'title' : 33858, 'value' : self._formatDifferenceLatency(local = self.mLatency, community = area[self.mId]['latency']) })
					if SpeedTester.PhaseDownload in self.mPhases:
						itemsCategory.append({ 'title' : 33074, 'value' : self._formatDifferenceSpeed(local = self.mDownload, community = area[self.mId]['download']) })
					if SpeedTester.PhaseUpload in self.mPhases:
						itemsCategory.append({ 'title' : 33859, 'value' : self._formatDifferenceSpeed(local = self.mUpload, community = area[self.mId]['upload']) })
					items.append({'title' : titles[i], 'items' : itemsCategory})

			# Dialog
			interface.Loader.hide()
			interface.Dialog.information(title = 33030, items = items)

			if not update == None:
				option = 0
				speedString = self._formatSpeed(self.mDownload).lower()
				try: speed = float(speedString.replace('kbps', '').replace('mbps', '').replace('gbps', '').replace('tbps', '').replace('bps', ''))
				except: speed = None # Unknown speed
				if 'kbps' in speedString:
					option = 1
				elif 'mbps' in speedString:
					if speed >= 900: option = 56
					elif speed >= 800: option = 55
					elif speed >= 700: option = 54
					elif speed >= 600: option = 53
					elif speed >= 500: option = 52
					elif speed >= 450: option = 51
					elif speed >= 400: option = 50
					elif speed >= 350: option = 49
					elif speed >= 300: option = 48
					elif speed >= 250: option = 47
					elif speed >= 200: option = 46
					elif speed >= 190: option = 45
					elif speed >= 180: option = 44
					elif speed >= 170: option = 43
					elif speed >= 160: option = 42
					elif speed >= 150: option = 41
					elif speed >= 140: option = 40
					elif speed >= 130: option = 39
					elif speed >= 120: option = 38
					elif speed >= 110: option = 37
					elif speed >= 100: option = 36
					elif speed >= 95: option = 35
					elif speed >= 90: option = 34
					elif speed >= 85: option = 33
					elif speed >= 80: option = 32
					elif speed >= 75: option = 31
					elif speed >= 70: option = 30
					elif speed >= 65: option = 29
					elif speed >= 60: option = 28
					elif speed >= 55: option = 27
					elif speed >= 50: option = 26
					elif speed >= 45: option = 25
					elif speed >= 40: option = 24
					elif speed >= 35: option = 23
					elif speed >= 30: option = 22
					elif speed >= 25: option = 21
					elif speed >= 20: option = 20
					elif speed >= 19: option = 19
					elif speed >= 18: option = 18
					elif speed >= 17: option = 17
					elif speed >= 16: option = 16
					elif speed >= 15: option = 15
					elif speed >= 14: option = 14
					elif speed >= 13: option = 13
					elif speed >= 12: option = 12
					elif speed >= 11: option = 11
					elif speed >= 10: option = 10
					elif speed >= 9: option = 9
					elif speed >= 8: option = 8
					elif speed >= 7: option = 7
					elif speed >= 6: option = 6
					elif speed >= 5: option = 5
					elif speed >= 4: option = 4
					elif speed >= 3: option = 3
					elif speed >= 2: option = 2
					elif speed >= 1: option = 1
				elif 'gbps' in speedString:
					if speed >= 15: option = 0
					elif speed >= 10: option = 66
					elif speed >= 9: option = 65
					elif speed >= 8: option = 64
					elif speed >= 7: option = 63
					elif speed >= 6: option = 62
					elif speed >= 5: option = 61
					elif speed >= 4: option = 60
					elif speed >= 3: option = 59
					elif speed >= 2: option = 58
					elif speed >= 1: option = 57
				elif 'tbps' in speedString:
					option = 0
				elif 'bps' in speedString:
					option = 1

				updateManual = False
				updateAutomatic = False

				if update == SpeedTester.UpdateManual:
					updateManual = True
				elif update == SpeedTester.UpdateAutomatic:
					updateAutomatic = True
				elif update == SpeedTester.UpdateBoth:
					updateManual = True
					updateAutomatic = True
				else:
					info = 'Do you want to automatically optimize your bandwidth restrictions and hide the streams that are too large to stream over your connection without buffering?'
					answer = interface.Dialog.option(title = title, message = info, labelConfirm = 'Optimize Settings', labelDeny = 'Keep Settings')
					if answer:
						items = [
							interface.Format.bold('Manual: ') + 'Optimize the manual playback restriction',
							interface.Format.bold('Automatic: ') + 'Optimize the automatic playback restriction',
							interface.Format.bold('Both: ') + 'Optimize the manual and automatic playback restrictions',
							interface.Format.bold('Cancel: ') + 'Do not optimize the playback restriction',
						]
						choice = interface.Dialog.options(title = title, items = items)
						updateManual = choice == 0 or choice == 2
						updateAutomatic = choice == 1 or choice == 2

				if updateManual:
					tools.Settings.set(id = 'manual.bandwidth.maximum', value = option)
				if updateAutomatic:
					tools.Settings.set(id = 'automatic.bandwidth.maximum', value = option)
				if updateManual or updateAutomatic:
					interface.Dialog.notification(title = 'Bandwidth Optimized', message = 'Bandwidth Restriction Settings Optimized', icon = interface.Dialog.IconSuccess)

	@classmethod
	def comparison(self, force = False):
		try:
			interface.Loader.show()
			result = self._information(networkInformation = True)
			networkInformation = result[1]['global']['location']
			result = result[0]
			items = []

			international = result['international']
			items.append({
				'title' : interface.Translation.string(33853),
				'items' : [
					{ 'title' : 33509, 'value' : self._formatSpeedLatency(speed = international['global']['download'], latency = international['global']['latency']) },
					{ 'title' : 33566, 'value' : self._formatSpeedLatency(speed = international['premiumize']['download'], latency = international['premiumize']['latency']) },
					{ 'title' : 35200, 'value' : self._formatSpeedLatency(speed = international['offcloud']['download'], latency = international['offcloud']['latency']) },
					{ 'title' : 33567, 'value' : self._formatSpeedLatency(speed = international['realdebrid']['download'], latency = international['realdebrid']['latency']) },
					{ 'title' : 33794, 'value' : self._formatSpeedLatency(speed = international['easynews']['download'], latency = international['easynews']['latency']) },
				]
			})

			continent = result['continent']
			items.append({
				'title' : interface.Translation.string(33713),
				'items' : [
					{ 'title' : 33874, 'value' : networkInformation['continent']['name'] },
					{ 'title' : 33509, 'value' : self._formatSpeedLatency(speed = continent['global']['download'], latency = continent['global']['latency']) },
					{ 'title' : 33566, 'value' : self._formatSpeedLatency(speed = continent['premiumize']['download'], latency = continent['premiumize']['latency']) },
					{ 'title' : 35200, 'value' : self._formatSpeedLatency(speed = continent['offcloud']['download'], latency = continent['offcloud']['latency']) },
					{ 'title' : 33567, 'value' : self._formatSpeedLatency(speed = continent['realdebrid']['download'], latency = continent['realdebrid']['latency']) },
					{ 'title' : 33794, 'value' : self._formatSpeedLatency(speed = continent['easynews']['download'], latency = continent['easynews']['latency']) },
				]
			})

			country = result['country']
			items.append({
				'title' : interface.Translation.string(33714),
				'items' : [
					{ 'title' : 33874, 'value' : networkInformation['country']['name'] },
					{ 'title' : 33509, 'value' : self._formatSpeedLatency(speed = country['global']['download'], latency = country['global']['latency']) },
					{ 'title' : 33566, 'value' : self._formatSpeedLatency(speed = country['premiumize']['download'], latency = country['premiumize']['latency']) },
					{ 'title' : 35200, 'value' : self._formatSpeedLatency(speed = country['offcloud']['download'], latency = country['offcloud']['latency']) },
					{ 'title' : 33567, 'value' : self._formatSpeedLatency(speed = country['realdebrid']['download'], latency = country['realdebrid']['latency']) },
					{ 'title' : 33794, 'value' : self._formatSpeedLatency(speed = country['easynews']['download'], latency = country['easynews']['latency']) },
				]
			})

			region = result['region']
			items.append({
				'title' : interface.Translation.string(33715),
				'items' : [
					{ 'title' : 33874, 'value' : networkInformation['region']['name'] },
					{ 'title' : 33509, 'value' : self._formatSpeedLatency(speed = region['global']['download'], latency = region['global']['latency']) },
					{ 'title' : 33566, 'value' : self._formatSpeedLatency(speed = region['premiumize']['download'], latency = region['premiumize']['latency']) },
					{ 'title' : 35200, 'value' : self._formatSpeedLatency(speed = region['offcloud']['download'], latency = region['offcloud']['latency']) },
					{ 'title' : 33567, 'value' : self._formatSpeedLatency(speed = region['realdebrid']['download'], latency = region['realdebrid']['latency']) },
					{ 'title' : 33794, 'value' : self._formatSpeedLatency(speed = region['easynews']['download'], latency = region['easynews']['latency']) },
				]
			})

			city = result['city']
			items.append({
				'title' : interface.Translation.string(33716),
				'items' : [
					{ 'title' : 33874, 'value' : networkInformation['city']['name'] },
					{ 'title' : 33509, 'value' : self._formatSpeedLatency(speed = city['global']['download'], latency = city['global']['latency']) },
					{ 'title' : 33566, 'value' : self._formatSpeedLatency(speed = city['premiumize']['download'], latency = city['premiumize']['latency']) },
					{ 'title' : 35200, 'value' : self._formatSpeedLatency(speed = city['offcloud']['download'], latency = city['offcloud']['latency']) },
					{ 'title' : 33567, 'value' : self._formatSpeedLatency(speed = city['realdebrid']['download'], latency = city['realdebrid']['latency']) },
					{ 'title' : 33794, 'value' : self._formatSpeedLatency(speed = city['easynews']['download'], latency = city['easynews']['latency']) },
				]
			})

			# Dialog
			interface.Loader.hide()
			interface.Dialog.information(title = 33030, items = items)
		except:
			tools.Logger.error()
			interface.Loader.hide()
			interface.Dialog.notification(title = 33030, message = 33852, icon = interface.Dialog.IconError)

	@classmethod
	def participation(self, force = False):
		if force or not tools.Settings.getBoolean('general.statistics.confirmation'):
			choice = interface.Dialog.option(title = 33845, message = 33847, labelConfirm = 33743, labelDeny = 33821)
			if force and choice: return
			choice = interface.Dialog.option(title = 33845, message = 33880, labelConfirm = 33743, labelDeny = 33821)
			if force and choice: return
			choice = interface.Dialog.option(title = 33845, message = 33848, labelConfirm = 33743, labelDeny = 33821)
			if force and choice: return
			choice = interface.Dialog.option(title = 33845, message = 33849, labelConfirm = 33743, labelDeny = 33821)
			if force and choice: return
			choice = interface.Dialog.option(title = 33845, message = 33850, labelConfirm = 33342, labelDeny = 33341)
			tools.Settings.set('general.statistics.sharing', not choice)
			tools.Settings.set('general.statistics.confirmation', True)

	def _share(self):
		thread = threading.Thread(target = self._shareBackground)
		thread.start()

	def _shareBackground(self):
		try:
			if tools.Settings.getBoolean('general.statistics.sharing'):
				information = network.Networker.information(obfuscate = True)
				data = information['global']

				data['type'] = {
					'service' : self.mId,
					'mode' : self.mMode,
				}
				data['measurement'] = {
					'latency' : {
						'value' : self.mLatency,
						'description' : self._formatLatency(self.mLatency),
					},
					'download' : {
						'value' : self.mDownload,
						'description' : None if self.mDownload == None else self._formatSpeed(self.mDownload),
					},
					'upload' : {
						'value' : self.mUpload,
						'description' : None if self.mUpload == None else self._formatSpeed(self.mUpload),
					},
				}

				api.Api.speedtestAdd(data = data)
		except:
			tools.Logger.error()
			interface.Dialog.notification(title = 33030, message = 33843, icon = interface.Dialog.IconError)

class SpeedTesterGlobal(SpeedTester):

	Name = 'Global'

	def __init__(self):
		SpeedTester.__init__(self, name = SpeedTesterGlobal.Name, phases = [self.PhaseLatency, self.PhaseDownload, self.PhaseUpload])
		self.mTester = None
		self.mServer = None
		self.mCity = None

	def _testSelection(self):
		options = [
			{
				'name' : 33800,
				'result' : 'automatic',
			},
			{
				'name' : 'Argentina',
				'result' : 'buenos aires',
			},
			{
				'name' : 'Austria',
				'result' : 'vienna',
			},
			{
				'name' : 'Australia',
				'result' : 'sydney',
			},
			{
				'name' : 'Belgium',
				'result' : 'brussels',
			},
			{
				'name' : 'Brazil',
				'result' : 'rio de janeiro',
			},
			{
				'name' : 'Canada',
				'result' : 'toronto',
			},
			{
				'name' : 'China',
				'result' : 'beijing',
			},
			{
				'name' : 'Colombia',
				'result' : 'bogota',
			},
			{
				'name' : 'Czech Republic',
				'result' : 'prague',
			},
			{
				'name' : 'Denmark',
				'result' : 'copenhagen',
			},
			{
				'name' : 'Egypt',
				'result' : 'cairo',
			},
			{
				'name' : 'Finland',
				'result' : 'helsinki',
			},
			{
				'name' : 'France',
				'result' : 'paris',
			},
			{
				'name' : 'Germany',
				'result' : 'berlin',
			},
			{
				'name' : 'Greece',
				'result' : 'athens',
			},
			{
				'name' : 'Greenland',
				'result' : 'nuuk',
			},
			{
				'name' : 'Hong Kong',
				'result' : 'hong kong',
			},
			{
				'name' : 'Hungary',
				'result' : 'budapest',
			},
			{
				'name' : 'Iceland',
				'result' : 'reykjavik',
			},
			{
				'name' : 'India',
				'result' : 'new delhi',
			},
			{
				'name' : 'Indonesia',
				'result' : 'jakarta',
			},
			{
				'name' : 'Israel',
				'result' : 'jerusalem',
			},
			{
				'name' : 'Italy',
				'result' : 'rome',
			},
			{
				'name' : 'Japan',
				'result' : 'tokyo',
			},
			{
				'name' : 'Mexico',
				'result' : 'mexico city',
			},
			{
				'name' : 'Netherlands',
				'result' : 'amsterdam',
			},
			{
				'name' : 'New Zealand',
				'result' : 'auckland',
			},
			{
				'name' : 'Nigeria',
				'result' : 'abuja',
			},
			{
				'name' : 'Norway',
				'result' : 'oslo',
			},
			{
				'name' : 'Pakistan',
				'result' : 'islamabad',
			},
			{
				'name' : 'Philippines',
				'result' : 'manila',
			},
			{
				'name' : 'Poland',
				'result' : 'warsaw',
			},
			{
				'name' : 'Portugal',
				'result' : 'lisbon',
			},
			{
				'name' : 'Russia',
				'result' : 'moscow',
			},
			{
				'name' : 'Singapore',
				'result' : 'singapore',
			},
			{
				'name' : 'South Africa',
				'result' : 'johannesburg',
			},
			{
				'name' : 'South Korea',
				'result' : 'seoul',
			},
			{
				'name' : 'Spain',
				'result' : 'barcelona',
			},
			{
				'name' : 'Sweden',
				'result' : 'stockholm',
			},
			{
				'name' : 'Switzerland',
				'result' : 'zurich',
			},
			{
				'name' : 'Taiwan',
				'result' : 'taipei',
			},
			{
				'name' : 'Turkey',
				'result' : 'istanbul',
			},
			{
				'name' : 'Ukraine',
				'result' : 'kiev',
			},
			{
				'name' : 'United Kingdom',
				'result' : 'london',
			},
			{
				'name' : 'United States Central',
				'result' : 'denver',
			},
			{
				'name' : 'United States East',
				'result' : 'new york',
			},
			{
				'name' : 'United States West',
				'result' : 'san francisco',
			},
		]
		choice = self._testDialog(options)
		if choice == None: return False
		self.mCity = None if options[choice]['result'] == 'automatic' else options[choice]['result']
		return options[choice]['result'].replace(' ', '').lower()

	def _filter(self, items):
		result = []
		if isinstance(items, list):
			for item in items:
				result.extend(self._filter(item))
		elif isinstance(items, dict):
			if 'url' in items and 'name' in items:
				result.append(items)
			else:
				for item in items.itervalues():
					result.extend(self._filter(item))
		return result

	def _serverName(self, city):
		city = city.lower()
		index = city.find(',')
		if index >= 0: city = city[:index]
		return city.strip()

	def _server(self):
		try:
			if not self.mTester:
				for i in range(5):
					# Sometimes error 503 is returned. Try a few times.
					try: self.mTester = speedtest.Speedtest()
					except: time.sleep(1)
				if not self.mTester:
					self.mError = True
					return None

			if self.mServer:
				return self.mServer
			else:
				result = []
				servers = self.mTester.get_servers()
				servers = self._filter(servers)
				names = [self._serverName(server['name']) for server in servers]

				if self.mCity:
					selections = [self._serverName(self.mCity)]
				else:
					selections = ['new york', 'london', 'berlin', 'moscow', 'johannesburg', 'tokyo', 'sydney', 'rio de janeiro']

				serverSelections = []
				self.mMode = None
				for selection in selections:
					for i in range(len(names)):
						if selection == names[i]:
							if self.mMode == None: self.mMode = selection.replace(' ', '').lower()
							serverSelections.append(servers[i])

				if len(serverSelections) == 0:
					result = self._filter(self.mTester.get_closest_servers())
				if len(serverSelections) > 0:
					try:
						# Select a random server. In case one fails, it will pick a different one during the next test.
						result.append(random.choice(serverSelections))
						self.mServer = self.mTester.get_best_server(result)
						return self.mServer
					except:
						pass
				return None
		except:
			tools.Logger.error()
			self.mError = True

	def _testLatency(self):
		try:
			server = self._server()
			if server and 'latency' in server:
				return server['latency']
			else:
				self.mError = True
		except:
			tools.Logger.error()
			self.mError = True
		return None

	def _testDownload(self):
		try:
			server = self._server()
			if server:
				return self.mTester.download()
			else:
				self.mError = True
		except:
			tools.Logger.error()
			self.mError = True
		return None

	def _testUpload(self):
		try:
			server = self._server()
			if server:
				return self.mTester.upload()
			else:
				self.mError = True
		except:
			tools.Logger.error()
			self.mError = True
		return None

class SpeedTesterDebrid(SpeedTester):

	# Not all hosters have the same download speed on debrid services (or at least on Premiumize). Or maybe this is just random?
	# The links are sorted from fastest to slowest.
	Links = [
		'https://openload.co/f/ps1KfFMcPoc/gaia.dat',
		'http://uptobox.com/n2k4i2p1ifkk',
		'https://1fichier.com/?n0yfptgzyx',
		'http://www.unibytes.com/DJDt3WGsErsLqw-Us4P3UgBB',

		# OLd Bubbles files, just in case the previous ones don't work.
		'http://datei.to/?0uLJGjFaQm',
		'http://www.mediafire.com/file/fxrjw6acjbtgsqr/gaia.dat',
		'https://openload.co/f/n5ui1nNbaIg/gaia.dat',
		'http://www.unibytes.com/lUYVrJ-z2kQLqw-Us4P3UgBB',
	]

	LatencyTotal = 20 # How many time to do the latency test. Must be a lot, otherwise the average is not good.
	LatencyCount = 5 # The number of last tests to calculate the mean latency from.

	def __init__(self, name, link = None):
		SpeedTester.__init__(self, name = name, phases = [self.PhaseLatency, self.PhaseDownload])
		self.mLink = link
		self.mLinks = None

	def _testLatency(self):
		timer = tools.Time()
		latencies = []

		for i in range(SpeedTesterDebrid.LatencyTotal):
			networker = network.Networker(self.mLink)
			timer.restart()
			networker.headers()
			latencies.append(timer.elapsed(milliseconds = True))

		latencies.sort()
		last = latencies[:SpeedTesterDebrid.LatencyCount]
		self.mLatency = int(sum(last) / float(len(last)))

		return self.mLatency

	def _testLink(self, link):
		return None

	def _testDownload(self):
		try:
			links = SpeedTesterDebrid.Links if self.mLinks == None else self.mLinks
			link = None
			for i in links:
				result = self._testLink(i)
				try:
					if network.Networker.linkIs(result): # Direct/main link.
						link = result
					elif result['success']:
						link = result['link']
						break
					elif result['error'] == debrid.RealDebrid.ErrorBlocked: # Blocked RealDebrid IP address.
						return None
				except: pass
			if not network.Networker.linkIs(link): # Errors returned by debrid, eg: ErrorRealDebrid
				return None

			size = 0
			networker = network.Networker(link)
			timer = tools.Time()
			response = networker.request()

			timer.start()
			if response == None:
				return None
			while True:
				chunk = response.read()
				if chunk:
					size += len(chunk)
				else:
					break
			return int((size * 8) / float(timer.elapsed()))
		except:
			tools.Logger.error()
			return None

class SpeedTesterPremiumize(SpeedTesterDebrid):

	Name = 'Premiumize'

	Link = 'http://energycdn.com'
	LinkServer = 'http://mirror.nforce.com/pub/speedtests/10mb.bin'

	def __init__(self):
		SpeedTesterDebrid.__init__(self, name = SpeedTesterPremiumize.Name, link = SpeedTesterPremiumize.Link)

	def _testSelection(self):
		options = [
			{
				'identifier' : 'main',
				'name' : 33668,
			},
			{
				'identifier' : 'streaming',
				'name' : 33667,
			},
		]
		choice = self._testDialog(options)
		if choice == None: return False
		if choice == 0: self.mLinks = [SpeedTesterPremiumize.LinkServer]
		return options[choice]['identifier']

	def _testLink(self, link):
		if link == SpeedTesterPremiumize.LinkServer:
			return link
		else:
			return debrid.Premiumize().add(link)

	def _validate(self):
		if not self.mLinks == None and not len(self.mLinks) == 0 and self.mLinks[0] == SpeedTesterPremiumize.LinkServer or debrid.Premiumize().accountValid():
			return True
		else:
			name = interface.Translation.string(33566)
			message = interface.Translation.string(33640) % name
			interface.Dialog.confirm(title = name, message = message)
			return False

class SpeedTesterOffCloud(SpeedTesterDebrid):

	Name = 'OffCloud'

	# https://offcloud.com/api/speedtest
	Link = 'https://fr-4.offcloud.com'
	LinkServer = 'https://fr-4.offcloud.com/test10MB.zip'

	def __init__(self):
		SpeedTesterDebrid.__init__(self, name = SpeedTesterOffCloud.Name, link = SpeedTesterOffCloud.Link)

	def _testSelection(self):
		options = [
			{
				'identifier' : 'main',
				'name' : 33668,
			},
			{
				'identifier' : 'streaming',
				'name' : 33667,
			},
		]
		choice = self._testDialog(options)
		if choice == None: return False
		if choice == 0: self.mLinks = [SpeedTesterOffCloud.LinkServer]
		return options[choice]['identifier']

	def _testLink(self, link):
		if link == self.LinkServer:
			return link
		else:
			return debrid.OffCloud().add(link)

	def _validate(self):
		if not self.mLinks == None and not len(self.mLinks) == 0 and self.mLinks[0] == SpeedTesterOffCloud.LinkServer or debrid.OffCloud().accountValid():
			return True
		else:
			name = interface.Translation.string(35200)
			message = interface.Translation.string(33640) % name
			interface.Dialog.confirm(title = name, message = message)
			return False

class SpeedTesterRealDebrid(SpeedTesterDebrid):

	Name = 'RealDebrid'

	Link = 'http://real-debrid.com'

	def __init__(self):
		SpeedTesterDebrid.__init__(self, name = SpeedTesterRealDebrid.Name, link = SpeedTesterRealDebrid.Link)

	def _testLink(self, link):
		return debrid.RealDebrid().add(link)

	def _validate(self):
		if debrid.RealDebrid().accountValid():
			return True
		else:
			name = interface.Translation.string(33567)
			message = interface.Translation.string(33640) % name
			interface.Dialog.confirm(title = name, message = message)
			return False

class SpeedTesterEasyNews(SpeedTester):

	Name = 'EasyNews'

	Download = '/test/10M?_='

	LinkUsWest = 'https://iad-dl-01.easynews.com'
	LinkUsEast = 'https://lax-dl-01.easynews.com'
	LinkEurope = 'https://fra-dl-01.easynews.com'

	LatencyTotal = 20 # How many time to do the latency test. Must be a lot, otherwise the average is not good.
	LatencyCount = 5 # The number of last tests to calculate the mean latency from.

	def __init__(self):
		SpeedTester.__init__(self, name = SpeedTesterEasyNews.Name, phases = [self.PhaseLatency, self.PhaseDownload])
		self.mLinkLatency = None
		self.mLinkDownload = None

	def _testLatency(self):
		timer = tools.Time()
		latencies = []

		for i in range(SpeedTesterEasyNews.LatencyTotal):
			networker = network.Networker(self.mLinkLatency)
			timer.restart()
			networker.headers()
			latencies.append(timer.elapsed(milliseconds = True))

		latencies.sort()
		last = latencies[:SpeedTesterEasyNews.LatencyCount]
		self.mLatency = int(sum(last) / float(len(last)))

		return self.mLatency

	def _testDownload(self):
		size = 0
		networker = network.Networker(self.mLinkDownload)
		timer = tools.Time()
		response = networker.request()
		timer.start()
		if response == None:
			return None
		while True:
			chunk = response.read()
			if chunk:
				size += len(chunk)
			else:
				break
		return int((size * 8) / float(timer.elapsed()))

	def _testSelection(self):
		options = [
			{
				'identifier' : 'europe',
				'name' : 33799,
				'result' : SpeedTesterEasyNews.LinkEurope,
			},
			{
				'identifier' : 'unitedstateseast',
				'name' : 33797,
				'result' : SpeedTesterEasyNews.LinkUsEast,
			},
			{
				'identifier' : 'unitedstateswest',
				'name' : 33798,
				'result' : SpeedTesterEasyNews.LinkUsWest,
			},
		]
		choice = self._testDialog(options)
		if choice == None: return False

		timestamp = str(tools.Time.timestamp() * 1000) # Uses millisecond timestamp
		self.mLinkLatency = options[choice]['result']
		self.mLinkDownload = options[choice]['result'] + SpeedTesterEasyNews.Download + timestamp

		return options[choice]['identifier']
