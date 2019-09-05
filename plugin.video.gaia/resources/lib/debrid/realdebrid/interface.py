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

import threading

from resources.lib.debrid import base
from resources.lib.debrid.realdebrid import core
from resources.lib.extensions import convert
from resources.lib.extensions import tools
from resources.lib.extensions import interface
from resources.lib.extensions import network
from resources.lib.extensions import clipboard

class Interface(base.Interface):

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		base.Interface.__init__(self)
		self.mDebrid = core.Core()

	##############################################################################
	# ACCOUNT
	##############################################################################

	def account(self):
		interface.Loader.show()
		valid = False
		title = core.Core.Name + ' ' + interface.Translation.string(33339)
		if self.mDebrid.accountEnabled():
			account = self.mDebrid.account(cached = False)
			if account:
				valid = interface.Translation.string(33341) if self.mDebrid.accountValid() else interface.Translation.string(33342)
				user = account['user']
				id = str(account['id'])
				email = account['email']
				type = account['type'].capitalize()
				points = str(account['points'])

				date = account['expiration']['date']
				days = str(account['expiration']['remaining'])

				items = []

				# Information
				items.append({
					'title' : 33344,
					'items' : [
						{ 'title' : 33340, 'value' : valid },
						{ 'title' : 32305, 'value' : id },
						{ 'title' : 32303, 'value' : user },
						{ 'title' : 32304, 'value' : email },
						{ 'title' : 33343, 'value' : type },
						{ 'title' : 33349, 'value' : points }
					]
				})

				# Expiration
				items.append({
					'title' : 33345,
					'items' : [
						{ 'title' : 33346, 'value' : date },
						{ 'title' : 33347, 'value' : days }
					]
				})

				# Dialog
				interface.Loader.hide()
				interface.Dialog.information(title = title, items = items)
			else:
				interface.Loader.hide()
				interface.Dialog.confirm(title = title, message = interface.Translation.string(33352) % core.Core.Name)
		else:
			interface.Loader.hide()
			interface.Dialog.confirm(title = title, message = interface.Translation.string(33351) % core.Core.Name)

		return valid

	def accountAuthentication(self, openSettings = True):
		interface.Loader.show()
		try:
			if self.mDebrid.accountValid():
				if interface.Dialog.option(title = core.Core.Name, message = 33492):
					self.mDebrid.accountAuthenticationReset(save = False)
				else:
					return None

			self.mDebrid.accountAuthenticationStart()

			# Link and token on top for skins that don't scroll text in a progress dialog.
			message = ''
			message += interface.Format.fontBold(interface.Translation.string(33381) + ': ' + self.mDebrid.accountAuthenticationLink())
			message += interface.Format.newline()
			message += interface.Format.fontBold(interface.Translation.string(33495) + ': ' + self.mDebrid.accountAuthenticationCode())
			message += interface.Format.newline() + interface.Translation.string(33494) + ' ' + interface.Translation.string(33978)

			clipboard.Clipboard.copy(self.mDebrid.accountAuthenticationCode())
			progressDialog = interface.Dialog.progress(title = core.Core.Name, message = message, background = False)

			interval = self.mDebrid.accountAuthenticationInterval()
			timeout = 3600
			synchronized = False

			for i in range(timeout):
				try:
					try: canceled = progressDialog.iscanceled()
					except: canceled = False
					if canceled: break
					progressDialog.update(int((i / float(timeout)) * 100))

					if not float(i) % interval == 0:
						raise Exception()
					tools.Time.sleep(1)

					if self.mDebrid.accountAuthenticationWait():
						synchronized = True
						break
				except:
					pass

			try: progressDialog.close()
			except: pass

			if synchronized:
				if self.mDebrid.accountAuthenticationFinish():
					interface.Dialog.notification(title = 33567, message = 35462, icon = interface.Dialog.IconSuccess)
			else:
				self.mDebrid.accountAuthenticationReset(save = True) # Make sure the values are reset if the waiting dialog is canceled.
		except:
			pass
		if openSettings:
			tools.Settings.launch(category = tools.Settings.CategoryAccounts)
		interface.Loader.hide()

	##############################################################################
	# CLEAR
	##############################################################################

	def clear(self):
		title = core.Core.Name + ' ' + interface.Translation.string(33013)
		message = 'Do you want to clear your RealDebrid downloads and delete all your files from the server?'
		if interface.Dialog.option(title = title, message = message):
			interface.Loader.show()
			self.mDebrid.deleteAll()
			interface.Loader.hide()
			message = 'RealDebrid Downloads Cleared'
			interface.Dialog.notification(title = title, message = message, icon = interface.Dialog.IconSuccess)

	##############################################################################
	# ADD
	##############################################################################

	def addManual(self):
		result = None
		title = 35082
		items = [
			interface.Format.bold(interface.Translation.string(35076) + ': ') + interface.Translation.string(35077),
			interface.Format.bold(interface.Translation.string(33381) + ': ') + interface.Translation.string(35080),
			interface.Format.bold(interface.Translation.string(33380) + ': ') + interface.Translation.string(35081),
		]
		choice = interface.Dialog.select(title = title, items = items)

		if choice >= 0:
			link = None
			if choice == 0 or choice == 1:
				link = interface.Dialog.input(title = title, type = interface.Dialog.InputAlphabetic)
			elif choice == 2:
				link = interface.Dialog.browse(title = title, type = interface.Dialog.BrowseFile, multiple = False, mask = ['torrent'])

			if not link == None or not link == '':
				interface.Dialog.notification(title = 35070, message = 35072, icon = interface.Dialog.IconSuccess)
				interface.Loader.show()
				result = self.add(link)
				if result['success']:
					interface.Dialog.closeAllProgress()
					choice = interface.Dialog.option(title = 35073, message = 35075)
					if choice: interface.Player.playNow(result['link'])

		interface.Loader.hide()
		return result

	def add(self, link, title = None, season = None, episode = None, pack = False, close = True, source = None, cached = None, select = False, cloud = False):
		if cloud: interface.Loader.show()
		result = self.mDebrid.add(link = link, title = title, season = season, episode = episode, pack = pack, source = source)

		if result['success']:
			return result
		elif result['id']:
			result = self._addWait(result = result, season = season, episode = episode, close = close, pack = pack, source = source, cached = cached, select = select, cloud = cloud)
		if cloud: interface.Loader.hide()

		if result['success']:
			return result
		elif result['error'] == core.Core.ErrorInaccessible:
			title = 'Stream Error'
			message = 'Stream Is Inaccessible'
		elif result['error'] == core.Core.ErrorRealDebrid:
			title = 'Stream Error'
			message = 'Failed To Add Stream To RealDebrid'
		elif result['error'] == core.Core.ErrorSelection:
			title = 'Selection Error'
			message = 'No File Selected'
		else:
			tools.Logger.errorCustom('Unexpected RealDebrid Error: ' + str(result))
			title = 'Stream Error'
			message = 'Stream File Unavailable'
		self._addError(title = title, message = message)
		result['notification'] = True
		return result

	def _addSelect(self, result):
		try:
			if not result: return result
			items = [i for i in result['items']['files'] if i['name'] and not i['name'].endswith(core.Core.Exclusions)]
			items = sorted(items, key = lambda x : x['name'])
			choice = interface.Dialog.options(title = 35542, items = [i['name'].strip('/') for i in items])
			if choice < 0:
				result['success'] = False
				result['error'] = core.Core.ErrorSelection
			else:
				result['items']['video'] = items[choice]
				result['selection'] = items[choice]['id']
		except:
			tools.Logger.error()
		return result

	def _addDelete(self, id, notification = False):
		def __addDelete(id, notification):
			result = self.mDebrid.delete(id)
			if notification:
				if result == True:
					interface.Dialog.notification(title = 'Deletion Success', message = 'Download Deleted From List', icon = interface.Dialog.IconSuccess)
				else:
					interface.Dialog.notification(title = 'Deletion Failure', message = 'Download Not Deleted From List', icon = interface.Dialog.IconError)
		thread = threading.Thread(target = __addDelete, args = (id, notification))
		thread.start()

	def _addAction(self, result):
		items = []
		items.append(interface.Format.font(interface.Translation.string(33077) + ': ', bold = True) + interface.Translation.string(33078))
		items.append(interface.Format.font(interface.Translation.string(33079) + ': ', bold = True) + interface.Translation.string(33080))
		items.append(interface.Format.font(interface.Translation.string(33083) + ': ', bold = True) + interface.Translation.string(33084))

		interface.Core.close()
		tools.Time.sleep(0.1) # Ensures progress dialog is closed, otherwise shows flickering.
		choice = interface.Dialog.options(title = 33076, items = items)

		if choice == -1:
			return False
		elif choice == 0:
			return True
		elif choice == 1:
			return False
		elif choice == 2:
			self._addDelete(id = result['id'], notification = True)
			return False

	def _addError(self, title, message, delay = True):
		interface.Loader.hide() # Make sure hided from sources __init__.py
		interface.Dialog.notification(title = title, message = message, icon = interface.Dialog.IconError)
		if delay: tools.Time.sleep(2) # Otherwise the message disappears to quickley when another notification is shown afterwards.

	def _addErrorDetermine(self, item):
		error = False
		status = item['status']

		if status == core.Core.StatusError:
			title = 'Download Error'
			message = 'Download Failure With Unknown Error'
			error = True
		elif status == core.Core.StatusMagnetError:
			title = 'Download Magnet'
			message = 'Magnet Link Download Failure'
			error = True
		elif status == core.Core.StatusVirus:
			title = 'Download Virus'
			message = 'Download Contains Virus'
			error = True
		elif status == core.Core.StatusDead:
			title = 'Download Dead'
			message = 'Torrent Download Dead'
			error = True

		if error:
			self._addError(title = title, message = message)
			try: self.mDebrid.deleteFailure(item['hash'])
			except: pass

		return error

	def _addWaitAction(self, result, seconds = None):
		# Ask to close a background dialog, because there is no cancel button as with the foreground dialog.
		elapsed = self.mTimer.elapsed()
		conditionShort = self.mTimerShort == False and elapsed > 30
		conditionLong = self.mTimerLong == False and elapsed > 120
		if conditionShort or conditionLong:
			if conditionShort: question = 'The download is taking a bit longer.'
			else: question = 'The download is taking a lot longer.'

			if seconds: question += ' The estimated remaining time is ' + convert.ConverterDuration(seconds, convert.ConverterDuration.UnitSecond).string(format = convert.ConverterDuration.FormatWordMedium) + '.'
			else: question += ' The estimated remaining time is currently unknown.'

			if conditionShort: question += ' Do you want to take action or let the download continue in the background?'
			else: question += ' Are you sure you do not want to take action and let the download continue in the background?'

			if conditionShort: self.mTimerShort = True
			if conditionLong: self.mTimerLong = True

			title = core.Core.Name + ' Download'
			answer = interface.Dialog.option(title = title, message = question, labelConfirm = 'Take Action', labelDeny = 'Continue Download')
			if answer:
				self._addAction(result)
				return True
		return False

	def _addWait(self, result, season = None, episode = None, close = True, pack = False, source = None, cached = None, select = False, cloud = False):
		try:
			id = result['id']

			# In case the progress dialog was canceled while transfering torrent data.
			if interface.Core.canceled():
				self._addDelete(id = id, notification = False)
				return self.mDebrid.addResult(error = core.Core.ErrorCancel)

			self.mTimer = tools.Time(start = True)
			self.mTimerShort = False
			self.mTimerLong = False

			if cached: apiInterval = 5 # Only 2.5 seconds for cached content, to reduce waiting time.
			else: apiInterval = 5 * 2 # Times 2, because the loops run in 0.5 seconds.
			apiCounter = 0

			unknown = 'Unknown'
			title = core.Core.Name + ' Download'
			descriptionInitialize = interface.Format.fontBold('Initializing Download') + '%s'
			descriptionWaiting = interface.Format.fontBold('Waiting For Download Start') + '%s'
			descriptionSeeds = interface.Format.fontBold('Waiting For Seed Connection') + '%s'
			descriptionFinalize = interface.Format.fontBold('Finalizing Download') + '%s'
			percentage = 0
			selectionFile = None
			canceled = False

			if not cloud: interface.Loader.hide()
			background = interface.Core.background()

			while True:

				# Do not launch the dialog if the torrent is cached, since RealDebird downloads do not distiguish between cahced and non-cahced downloads.
				# Do not use the the item's cached status, since it might be outdated (eg: items from the stream history list).
				if not cached:
					interface.Core.create(type = interface.Core.TypeDownload, title = title, message = descriptionInitialize)
					interface.Core.update(progress = int(percentage), title = title, message = descriptionInitialize)

				item = self.mDebrid.item(id = id, season = season, episode = episode, pack = pack)
				status = item['status']

				#####################################################################################################################################
				# Select the largest file for download.
				#####################################################################################################################################

				while status == core.Core.StatusMagnetConversion or status == core.Core.StatusFileSelection or status == core.Core.StatusQueued:
					if interface.Core.canceled() or canceled:
						canceled = True
						break

					if background and self._addWaitAction(result = result):
						if not cached and close: interface.Core.close()
						return self.mDebrid.addError()

					if not cached: interface.Core.update(progress = int(percentage), title = title, message = descriptionSeeds)

					apiCounter += 1
					if apiCounter == apiInterval:
						apiCounter = 0
						item = self.mDebrid.item(id = id, season = season, episode = episode, pack = pack)
						status = item['status']
						if self._addErrorDetermine(item):
							if not cached and close: interface.Core.close()
							return self.mDebrid.addError()

					# Select the largest/name, so that the direct download link points to the main video file.
					# Otherwise, if all files are selected, RealDebrid will create a rar file in the final link.
					if select:
						selection = False
						while True:
							result = self.mDebrid.selectManualInitial(id = id, item = item, pack = pack)
							if isinstance(result, dict):
								if selectionFile == None:
									selectionFile = self._addSelect(result)
									if 'error' in selectionFile and selectionFile['error']: return selectionFile
								selection = self.mDebrid.selectManualFinal(id = id, selection = selectionFile['selection'])
								break
							tools.Time.sleep(1)
					else:
						selection = self.mDebrid.selectName(id = id, item = item, season = season, episode = episode, pack = pack)

					if selection == True:
						item = self.mDebrid.item(id = id, season = season, episode = episode, pack = pack)
						status = item['status']
						if status == core.Core.StatusFinished: # In case of "cached" RealDebrid torrents that are available immediatley.
							percentage = 100
							if not cached:
								interface.Core.update(progress = int(percentage), title = title, message = descriptionFinalize)
								if close: interface.Core.close()
							result = self.mDebrid.add(item['link'])
							result['id'] = id # Torrent ID is different to the unrestirction ID. The torrent ID is needed for deletion.
							return result
						else:
							break
					elif selection == core.Core.ErrorUnavailable and not status == core.Core.StatusMagnetConversion:
						if not cached and close: interface.Core.close()
						title = 'Invalid Stream'
						if pack: message = 'No Episode In Season Pack'
						else: message = 'No Playable Stream Found'
						self._addError(title = title, message = message)
						try: self.mDebrid.deleteFailure(item['hash'])
						except: pass
						return self.mDebrid.addError()

					tools.Time.sleep(0.5)

				#####################################################################################################################################
				# Wait for the download to start.
				#####################################################################################################################################

				waiting = item['transfer']['progress']['completed']['value'] == 0 and item['transfer']['speed']['bytes'] == 0
				while status == core.Core.StatusQueued or waiting:
					if not cached and (interface.Core.canceled() or canceled):
						canceled = True
						break

					if background and self._addWaitAction(result = result):
						if not cached and close: interface.Core.close()
						return self.mDebrid.addError()

					if not cached: interface.Core.update(progress = int(percentage), title = title, message = descriptionWaiting)

					apiCounter += 1
					if apiCounter == apiInterval:
						apiCounter = 0
						item = self.mDebrid.item(id = id, season = season, episode = episode, pack = pack)
						status = item['status']
						if self._addErrorDetermine(item):
							if not cached and close: interface.Core.close()
							return self.mDebrid.addError()
						waiting = item['transfer']['progress']['completed']['value'] == 0 and item['transfer']['speed']['bytes'] == 0

					tools.Time.sleep(0.5)

				#####################################################################################################################################
				# Wait for the download to finish.
				#####################################################################################################################################

				seconds = None
				while True:
					if not cached and (interface.Core.canceled() or canceled):
						canceled = True
						break

					if background and self._addWaitAction(result = result, seconds = seconds):
						return self.mDebrid.addError()

					apiCounter += 1
					if apiCounter == apiInterval:
						apiCounter = 0
						item = self.mDebrid.item(id = id, season = season, episode = episode, pack = pack)

						if self._addErrorDetermine(item):
							if not cached and close: interface.Core.close()
							return self.mDebrid.addError()

						status = item['status']
						if status == core.Core.StatusFinished:
							percentage = 100
							if not cached:
								interface.Core.update(progress = int(percentage), title = title, message = descriptionFinalize)
								if close: interface.Core.close()
							result = self.mDebrid.add(item['link'])
							result['id'] = id # Torrent ID is different to the unrestirction ID. The torrent ID is needed for deletion.
							return result

						percentageNew = item['transfer']['progress']['completed']['percentage']
						if percentageNew >= percentage:
							percentage = percentageNew
							speed = item['transfer']['speed']['description']
							speedBytes = item['transfer']['speed']['bytes']
							size = item['size']['description']
							sizeBytes = item['size']['bytes']
							sizeCompleted = item['transfer']['progress']['completed']['size']['description']
							seconds = item['transfer']['progress']['remaining']['time']['seconds']
							if seconds == 0:
								eta = unknown
								if background: eta += ' ETA'
							else:
								eta = item['transfer']['progress']['remaining']['time']['description']

							description = []
							if background:
								if speed: description.append(speed)
								if size and sizeBytes > 0: description.append(size)
								if eta: description.append(eta)
								if len(description) > 0:
									description = interface.Format.fontSeparator().join(description)
								else:
									description = 'Unknown Progress'
							else:
								if speed:
									if speedBytes <= 0:
										speed = unknown
									description.append(interface.Format.font('Download Speed: ', bold = True) + speed)
								if size:
									if sizeBytes > 0:
										size = sizeCompleted + ' of ' + size
									else:
										size = unknown
									description.append(interface.Format.font('Download Size: ', bold = True) + size)
								if eta: description.append(interface.Format.font('Remaining Time: ', bold = True) + eta)
								description = interface.Format.fontNewline().join(description)

							if not cached: interface.Core.update(progress = int(percentage), title = title, message = description)

					tools.Time.sleep(0.5)

				#####################################################################################################################################
				# Continue
				#####################################################################################################################################

				# Action Dialog
				if interface.Core.canceled() or canceled:
					if not self._addAction(result):
						return self.mDebrid.addResult(error = core.Core.ErrorCancel)

				# NB: This is very important.
				# Close the dialog and sleep (0.1 is not enough).
				# This alows the dialog to properley close and reset everything.
				# If not present, the internal iscanceled variable of the progress dialog will stay True after the first cancel.
				interface.Core.close()
				tools.Time.sleep(0.5)

		except:
			tools.Logger.error()
			if close: interface.Core.close()
			return self.mDebrid.addError()

	##############################################################################
	# DOWNLOAD
	##############################################################################

	def downloadInformation(self):
		interface.Loader.show()
		title = core.Core.Name + ' ' + interface.Translation.string(32009)
		if self.mDebrid.accountEnabled():
			account = self.mDebrid.account()
			if account:
				information = self.mDebrid.downloadInformation()
				items = []

				# Torrent Count
				count = information['count']
				items.append({
					'title' : 33496,
					'items' : [
						{ 'title' : 33497, 'value' : str(count['total']) },
						{ 'title' : 33291, 'value' : str(count['busy']) },
						{ 'title' : 33294, 'value' : str(count['finished']) },
						{ 'title' : 33295, 'value' : str(count['failed']) },
					]
				})

				# Torrent Size
				# NB: Currently ignore the size, since RealDebrid always returns 0 bytes for downloads.
				'''size = information['size']
				items.append({
					'title' : 33498,
					'items' : [
						{ 'title' : 33497, 'value' : size['description'] },
					]
				})'''

				# Torrent Host
				if 'host' in information:
					host = information['host']
					items.append({
						'title' : 33499,
						'items' : [
							{ 'title' : 33500, 'value' : host['domain'] },
							{ 'title' : 33501, 'value' : host['size']['description'] },
						]
					})

				# Dialog
				interface.Loader.hide()
				interface.Dialog.information(title = title, items = items)
			else:
				interface.Loader.hide()
				interface.Dialog.confirm(title = title, message = interface.Translation.string(33352) % core.Core.Name)
		else:
			interface.Loader.hide()
			interface.Dialog.confirm(title = title, message = interface.Translation.string(33351) % core.Core.Name)

	##############################################################################
	# DIRECTORY
	##############################################################################

	def directoryListAction(self, item):
		itemNew = tools.Converter.jsonFrom(item)
		if itemNew: item = itemNew

		actions = []
		items = []

		if item['status'] == core.Core.StatusFinished:
			actions.append('download')
			items.append(interface.Format.bold(interface.Translation.string(35154) + ': ') + interface.Translation.string(35155))
			actions.append('stream')
			items.append(interface.Format.bold(interface.Translation.string(35083) + ': ') + interface.Translation.string(35086))
			actions.append('copy')
			items.append(interface.Format.bold(interface.Translation.string(33031) + ': ') + interface.Translation.string(35087))
			actions.append('open')
			items.append(interface.Format.bold(interface.Translation.string(35085) + ': ') + interface.Translation.string(35088))

		actions.append('remove')
		items.append(interface.Format.bold(interface.Translation.string(35100) + ': ') + interface.Translation.string(35101))
		actions.append('refresh')
		items.append(interface.Format.bold(interface.Translation.string(35103) + ': ') + interface.Translation.string(35104))
		actions.append('cancel')
		items.append(interface.Format.bold(interface.Translation.string(35105) + ': ') + interface.Translation.string(35106))

		choice = interface.Dialog.select(title = 32009, items = items)
		if choice >= 0:
			choice = actions[choice]
			if choice == 'refresh':
				interface.Directory.refresh()
			elif not choice == 'cancel':
				hide = True
				interface.Loader.show()
				try:
					id = item['id']
					if choice == 'remove':
						self.mDebrid.deleteSingle(id, wait = True)
						interface.Directory.refresh()
						hide = False # Already hidden by container refresh.
					elif choice == 'download':
						from resources.lib.extensions import downloader
						try: itemLink = self.mDebrid.add(item['link'])['link']
						except: itemLink = None
						if network.Networker.linkIs(itemLink): downloader.Downloader(downloader.Downloader.TypeManual).download(media = downloader.Downloader.MediaOther, link = itemLink)
						else: raise Exception('Invalid Link: ' + str(itemLink))
					else:
						item = self.mDebrid.item(id)
						try: itemLink = self.mDebrid.add(item['link'])['link']
						except: itemLink = None
						if network.Networker.linkIs(itemLink):
							if choice == 'stream':
								interface.Player.playNow(itemLink)
							elif choice == 'copy':
								clipboard.Clipboard.copyLink(itemLink, True)
							elif choice == 'open':
								tools.System.openLink(itemLink)
						else: # RealDebrid API errors
							raise Exception('Invalid Link: ' + str(itemLink))
				except:
					tools.Logger.error()
					interface.Dialog.notification(title = 33567, message = 35108, icon = interface.Dialog.IconError)
				if hide: interface.Loader.hide()

	def directoryList(self):
		directory = interface.Directory(content = interface.Directory.ContentAddons)
		items = self.mDebrid.items()
		itemsNew = [[], [], [], [], []]

		for item in items:
			info = []
			icon = None
			index = 0

			try: status = item['status']
			except: status = None

			if not status == None and not status == core.Core.StatusUnknown:
				color = None
				if status == core.Core.StatusError:
					color = interface.Format.colorBad()
					icon = 'downloadsfailed.png'
					statusLabel = 'Failure'
					index = 0
				elif status == core.Core.StatusMagnetError:
					color = interface.Format.colorBad()
					icon = 'downloadsfailed.png'
					statusLabel = 'Magnet'
					index = 0
				elif status == core.Core.StatusMagnetConversion:
					color = interface.Format.colorMedium()
					icon = 'downloadsbusy.png'
					statusLabel = 'Conversion'
					index = 1
				elif status == core.Core.StatusFileSelection:
					color = interface.Format.colorMedium()
					icon = 'downloadsbusy.png'
					statusLabel = 'Selection'
					index = 1
				elif status == core.Core.StatusQueued:
					color = interface.Format.colorMedium()
					icon = 'downloadsbusy.png'
					statusLabel = 'Queued'
					index = 1
				elif status == core.Core.StatusBusy:
					color = interface.Format.colorExcellent()
					icon = 'downloadsbusy.png'
					statusLabel = 'Busy'
					index = 2
				elif status == core.Core.StatusFinished:
					color = interface.Format.colorSpecial()
					icon = 'downloadscompleted.png'
					statusLabel = 'Finished'
					index = 3
				elif status == core.Core.StatusVirus:
					color = interface.Format.colorBad()
					icon = 'downloadsfailed.png'
					statusLabel = 'Virus'
					index = 0
				elif status == core.Core.StatusCompressing:
					color = interface.Format.colorMain()
					icon = 'downloadsbusy.png'
					statusLabel = 'Compressing'
					index = 4
				elif status == core.Core.StatusUploading:
					color = interface.Format.colorMain()
					icon = 'downloadsbusy.png'
					statusLabel = 'Uploading'
					index = 4
				elif status == core.Core.StatusDead:
					color = interface.Format.colorBad()
					icon = 'downloadsfailed.png'
					statusLabel = 'Dead'
					index = 0
				info.append(interface.Format.fontColor(statusLabel, color))

			if status == core.Core.StatusBusy:
				try:
					colors = interface.Format.colorGradient(interface.Format.colorMedium(), interface.Format.colorExcellent(), 101) # One more, since it goes from 0 - 100
					percentage = int(item['transfer']['progress']['completed']['percentage'])
					info.append(interface.Format.fontColor('%d%%' % percentage, colors[percentage]))
				except:
					tools.Logger.error()
					pass

				try:
					if item['transfer']['speed']['bits'] > 0:
						info.append(item['transfer']['speed']['description'])
				except: pass
				try:
					if item['transfer']['progress']['remaining']['time']['seconds'] > 0:
						info.append(item['transfer']['progress']['remaining']['time']['description'])
				except: pass

			try:
				if item['size']['bytes'] > 0:
					info.append(item['size']['description'])
			except: pass

			label = interface.Format.bold(item['name'])
			label += interface.Format.newline()
			label += ' | '.join(info)

			itemJson = tools.Converter.jsonTo(item)

			context = []
			context.append({'label' : 32072, 'command' : 'Container.Refresh'})
			context.append({'label' : 33371, 'command' : tools.System.commandPlugin(action = 'realdebridListAction', parameters = {'item' : itemJson})})

			itemsNew[index].append({'item' : itemJson, 'label' : label, 'context' : context, 'icon' : icon})

		for item in itemsNew:
			for i in item:
				directory.add(label = i['label'], action = 'realdebridListAction', parameters = {'item' : i['item']}, context = i['context'], folder = True, icon = i['icon'], iconDefault = 'DefaultAddonProgram.png')

		directory.finish()
