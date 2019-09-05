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
from resources.lib.debrid.premiumize import core
from resources.lib.extensions import tools
from resources.lib.extensions import interface
from resources.lib.extensions import network
from resources.lib.extensions import convert
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

				date = account['expiration']['date']
				days = str(account['expiration']['remaining'])

				percentage = str(account['usage']['consumed']['percentage']) + '%'

				pointsUsed = account['usage']['consumed']['points']
				pointsTotal = account['usage']['consumed']['points'] + account['usage']['remaining']['points']
				points = str(pointsUsed) + ' ' + interface.Translation.string(33073) + ' ' + str(pointsTotal)

				storageUsed = account['usage']['consumed']['size']['description']
				storageTotal = convert.ConverterSize(account['usage']['consumed']['size']['bytes'] + account['usage']['remaining']['size']['bytes']).stringOptimal()
				storage = storageUsed + ' ' + interface.Translation.string(33073) + ' ' + storageTotal

				items = []

				# Information
				items.append({
					'title' : 33344,
					'items' : [
						{ 'title' : 33340, 'value' : valid },
						{ 'title' : 32303, 'value' : user },
					]
				})

				# Expiration
				items.append({
					'title' : 33345,
					'items' : [
						{ 'title' : 33346, 'value' : date },
						{ 'title' : 33347, 'value' : days },
					]
				})

				# Usage
				items.append({
					'title' : 33228,
					'items' : [
						{ 'title' : 33348, 'value' : percentage },
						{ 'title' : 33349, 'value' : points },
						{ 'title' : 33350, 'value' : storage },
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
					interface.Dialog.notification(title = 33566, message = 35462, icon = interface.Dialog.IconSuccess)
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
		message = 'Do you want to clear your Premiumize downloads and delete all your files from the server?'
		if interface.Dialog.option(title = title, message = message):
			interface.Loader.show()
			self.mDebrid.deleteAll()
			interface.Loader.hide()
			message = 'Premiumize Downloads Cleared'
			interface.Dialog.notification(title = title, message = message, icon = interface.Dialog.IconSuccess)

	##############################################################################
	# ADD
	##############################################################################

	def addManual(self):
		result = None
		title = 35082
		items = [
			interface.Format.bold(interface.Translation.string(35076) + ': ') + interface.Translation.string(35077),
			interface.Format.bold(interface.Translation.string(33381) + ': ') + interface.Translation.string(35078),
			interface.Format.bold(interface.Translation.string(33380) + ': ') + interface.Translation.string(35079),
		]
		choice = interface.Dialog.select(title = title, items = items)

		if choice >= 0:
			link = None
			if choice == 0 or choice == 1:
				link = interface.Dialog.input(title = title, type = interface.Dialog.InputAlphabetic)
			elif choice == 2:
				link = interface.Dialog.browse(title = title, type = interface.Dialog.BrowseFile, multiple = False, mask = ['torrent', 'nzb'])

			if not link == None and not link == '':
				interface.Dialog.notification(title = 35070, message = 35071, icon = interface.Dialog.IconSuccess)
				interface.Loader.show()
				result = self.add(link)
				if result['success']:
					interface.Dialog.closeAllProgress()
					choice = interface.Dialog.option(title = 35073, message = 35074)
					if choice: interface.Player.playNow(result['link'])

		interface.Loader.hide()
		return result

	# season/episode: Filter out the correct file from a season pack.
	def add(self, link, title = None, season = None, episode = None, pack = False, close = True, source = None, cached = False, select = False, cloud = False):
		if cloud: interface.Loader.show()
		result = self.mDebrid.add(link = link, title = title, season = season, episode = episode, pack = pack, source = source, cached = cached, cloud = cloud)
		if select: result = self._addSelect(result)
		if cloud: interface.Loader.hide()
		if result['success']:
			return result
		elif result['id']:
			return self._addLink(result, season = season, episode = episode, close = close, pack = pack, select = select)
		elif result['error'] == core.Core.ErrorInaccessible:
			title = 'Stream Error'
			message = 'Stream Is Inaccessible'
		elif result['error'] == core.Core.ErrorPremiumize:
			title = 'Stream Error'
			message = 'Failed To Add Stream To Premiumize'
		elif result['error'] == core.Core.ErrorAuthentication:
			title = 'Stream Error'
			message = 'Premiumize Authentication Failed'
		elif result['error'] == core.Core.ErrorPremium:
			title = 'Stream Error'
			message = 'Premiumize Premium Membership Required'
		elif result['error'] == core.Core.ErrorTemporary:
			title = 'Stream Error'
			message = 'Temporary Premiumize Error'
		elif result['error'] == core.Core.ErrorSelection:
			title = 'Selection Error'
			message = 'No File Selected'
		elif result['error'] == core.Core.ErrorUnsupported:
			title = 'Unsupported Error'
			message = 'Requested Feature Unsupported'
		else:
			tools.Logger.errorCustom('Unexpected Premiumize Error: ' + str(result))
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
			choice = interface.Dialog.options(title = 35542, items = [i['name'] for i in items])
			if choice < 0:
				result['success'] = False
				result['error'] = core.Core.ErrorSelection
			else:
				result['items']['video'] = items[choice]
				result['link'] = items[choice]['link']
		except:
			tools.Logger.error()
		return result

	def _addDelete(self, id, notification = False):
		def __addDelete(id, notification):
			result = self.mDebrid.deleteTransfer(id = id)
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

	def _addErrorDetermine(self, item, api = False, pack = False):
		error = False
		status = item['status'] if 'status' in item else None
		if status == core.Core.StatusError:
			title = 'Download Error'
			message = None
			if item['error']:
				message = item['error']
			if message == None:
				message = 'Download Failure With Unknown Error'
			self._addError(title = title, message = message)
			error = True
		elif status == core.Core.StatusTimeout:
			title = 'Download Timeout'
			message = 'Download Timeout Failure'
			self._addError(title = title, message = message)
			error = True
		elif api:
			if not 'video' in item or item['video'] == None:
				title = 'Invalid Stream'
				if pack: message = 'No Episode In Season Pack'
				else: message = 'No Playable Stream Found'
				self._addError(title = title, message = message)
				error = False # Do not return True, since it won't have a video stream while still downloading.

		if error:
			try:
				self.mDebrid.deleteFailure(id = item['id'], pack = pack)
			except: pass

		return error

	def _addLink(self, result, season = None, episode = None, close = True, pack = False, select = False):
		self.tActionCanceled = False
		unknown = 'Unknown'
		id = result['id']

		# In case the progress dialog was canceled while transfering torrent data.
		if interface.Core.canceled():
			self._addDelete(id = id, notification = False)
			return self.mDebrid.addResult(error = core.Core.ErrorCancel)

		self.tLink =  ''
		item = self.mDebrid.item(idTransfer = id, content = True, season = season, episode = episode)
		if select: item = self._addSelect(item)
		if item:
			try:
				self.tLink = item['video']['link']
				if self.tLink: return self.mDebrid.addResult(id = id, link = self.tLink)
			except: pass
			try: percentage = item['transfer']['progress']['completed']['percentage']
			except: percentage = 0
			status = item['status']
			if self._addErrorDetermine(item, pack = pack):
				pass
			elif status == core.Core.StatusQueued or core.Core.StatusBusy or status == core.Core.StatusFinalize:
				title = 'Premiumize Download'
				descriptionWaiting = interface.Format.fontBold('Waiting For Download Start') + '%s'
				descriptionFinalize = interface.Format.fontBold('Finalizing Download') + '%s'

				interface.Loader.hide() # Make sure hided from sources __init__.py

				self.timer = tools.Time(start = True)
				self.timerShort = False
				self.timerLong = False

				def updateProgress(id, percentage, close):
					while True:
						background = interface.Core.background()
						interface.Core.create(type = interface.Core.TypeDownload, title = title, message = descriptionWaiting)
						interface.Core.update(progress = int(percentage), title = title, message = descriptionWaiting)
						try:
							status = core.Core.StatusQueued
							seconds = None
							counter = 0
							canceled = False
							item = self.mDebrid.item(idTransfer = id, content = True, season = season, episode = episode)
							if select: item = self._addSelect(item)
							while True:
								if counter == 10: # Only make an API request every 5 seconds.
									item = self.mDebrid.item(idTransfer = id, content = True, season = season, episode = episode)
									if select: item = self._addSelect(item)
									counter = 0
								counter += 1

								status = item['status'] if 'status' in item else None
								try:
									self.tLink = item['video']['link']
									if self.tLink: return
								except: pass
								if not status == core.Core.StatusQueued and not status == core.Core.StatusBusy and not status == core.Core.StatusFinalize:
									close = True
									self._addErrorDetermine(item, api = True, pack = pack)
									break

								waiting = item['transfer']['speed']['bytes'] == 0 and item['size']['bytes'] == 0 and item['transfer']['progress']['completed']['value'] == 0 and item['transfer']['progress']['completed']['time']['seconds'] == 0

								if status == core.Core.StatusFinalize:
									interface.Core.update(progress = 0, title = title, message = descriptionFinalize)
								elif waiting:
									interface.Core.update(progress = 0, title = title, message = descriptionWaiting)
								else:
									percentageNew = item['transfer']['progress']['completed']['percentage']
									# If Premiumize looses the connection in the middle of the download, the progress goes back to 0, causing the dialog to close. Avoid this by keeping track of the last progress.
									if percentageNew >= percentage:
										percentage = percentageNew
										description = ''
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
												peers = item['transfer']['torrent']['peers']
												if peers == 0: peers = ''
												else: peers = ' from ' + str(peers) + ' nodes'
												description.append(interface.Format.font('Download Speed: ', bold = True) + speed + peers)
											if size:
												if sizeBytes > 0:
													size = sizeCompleted + ' of ' + size
												else:
													size = unknown
												description.append(interface.Format.font('Download Size: ', bold = True) + size)
											if eta: description.append(interface.Format.font('Remaining Time: ', bold = True) + eta)
											description = interface.Format.fontNewline().join(description)

										interface.Core.update(progress = int(percentage), title = title, message = description)

								if interface.Core.canceled():
									canceled = True # Because the status is reset with interface.Core.close().
									break

								# Ask to close a background dialog, because there is no cancel button as with the foreground dialog.
								elapsed = self.timer.elapsed()
								conditionShort = self.timerShort == False and elapsed > 30
								conditionLong = self.timerLong == False and elapsed > 120
								if (conditionShort or conditionLong) and background:
									if conditionShort: question = 'The download is taking a bit longer.'
									else: question = 'The download is taking a lot longer.'

									if seconds: question += ' The estimated remaining time is ' + convert.ConverterDuration(seconds, convert.ConverterDuration.UnitSecond).string(format = convert.ConverterDuration.FormatWordMedium) + '.'
									else: question += ' The estimated remaining time is currently unknown.'

									if conditionShort: question += ' Do you want to take action or let the download continue in the background?'
									else: question += ' Are you sure you do not want to take action and let the download continue in the background?'

									if conditionShort: self.timerShort = True
									if conditionLong: self.timerLong = True

									answer = interface.Dialog.option(title = title, message = question, labelConfirm = 'Take Action', labelDeny = 'Continue Download')
									if answer:
										if self._addAction(result):
											break
										else:
											self.tActionCanceled = True
											return None

								# Sleep
								tools.Time.sleep(0.5)

							if close: interface.Core.close()
						except:
							tools.Logger.error()

						# Action Dialog
						if interface.Core.canceled() or canceled:
							if not self._addAction(result):
								self.tActionCanceled = True
								return None

						# NB: This is very important.
						# Close the dialog and sleep (0.1 is not enough).
						# This alows the dialog to properley close and reset everything.
						# If not present, the internal iscanceled variable of the progress dialog will stay True after the first cancel.
						interface.Core.close()
						tools.Time.sleep(0.5)

				# END of updateProgress

				try:
					thread = threading.Thread(target = updateProgress, args = (id, percentage, close))
					thread.start()
					thread.join()
				except:
					tools.Logger.error()
		else:
			title = 'Download Error'
			message = 'Download Failure'
			self._addError(title = title, message = message)

		if self.tActionCanceled:
			return self.mDebrid.addResult(error = core.Core.ErrorCancel)
		else:
			return self.mDebrid.addResult(id = id, link = self.tLink)

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

				# Count
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

				# Size
				size = information['size']
				items.append({
					'title' : 33498,
					'items' : [
						{ 'title' : 33497, 'value' : size['description'] },
					]
				})

				# Usage
				percentage = str(information['usage']['consumed']['percentage']) + '%'

				pointsUsed = information['usage']['consumed']['points']
				pointsTotal = information['usage']['consumed']['points'] + information['usage']['remaining']['points']
				points = str(pointsUsed) + ' ' + interface.Translation.string(33073) + ' ' + str(pointsTotal)

				storageUsed = information['usage']['consumed']['size']['description']
				storageTotal = convert.ConverterSize(information['usage']['consumed']['size']['bytes'] + information['usage']['remaining']['size']['bytes']).stringOptimal()
				storage = storageUsed + ' ' + interface.Translation.string(33073) + ' ' + storageTotal

				items.append({
					'title' : 33228,
					'items' : [
						{ 'title' : 33348, 'value' : percentage },
						{ 'title' : 33349, 'value' : points },
						{ 'title' : 33350, 'value' : storage },
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

	def directoryItemAction(self, item):
		itemNew = tools.Converter.jsonFrom(item)
		if itemNew: item = itemNew
		link = item['link']

		items = [
			interface.Format.bold(interface.Translation.string(35083) + ': ') + interface.Translation.string(35086),
			interface.Format.bold(interface.Translation.string(33031) + ': ') + interface.Translation.string(35087),
			interface.Format.bold(interface.Translation.string(35085) + ': ') + interface.Translation.string(35088),
		]
		choice = interface.Dialog.select(title = 32009, items = items)
		if choice >= 0:
			if choice == 0: interface.Player.playNow(link)
			elif choice == 1: clipboard.Clipboard.copyLink(link, True)
			elif choice == 2: tools.System.openLink(link)

	def directoryItem(self, item):
		itemNew = tools.Converter.jsonFrom(item)
		if itemNew: item = itemNew

		directory = interface.Directory(content = interface.Directory.ContentAddons)
		items = item['files']
		itemsNew = []

		for item in items:
			info = []
			icon = 'downloads.png'

			try: info.append(item['extension'].upper())
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
			context.append({'label' : 33371, 'command' : tools.System.commandPlugin(action = 'premiumizeItemAction', parameters = {'item' : itemJson})})

			itemsNew.append({'item' : itemJson, 'label' : label, 'context' : context, 'icon' : icon})

		# Sort so that episodes show in ascending order.
		itemsNew.sort(key = lambda i: i['label'])

		for item in itemsNew:
			directory.add(label = item['label'], action = 'premiumizeItemAction', parameters = {'item' : item['item']}, context = item['context'], folder = False, icon = item['icon'], iconDefault = 'DefaultAddonProgram.png')

		directory.finish()

	def directoryListAction(self, item, context = False):
		itemNew = tools.Converter.jsonFrom(item)
		if itemNew: item = itemNew
		try: context = bool(context)
		except:	context = False

		actions = []
		items = []

		if item['status'] == core.Core.StatusFinished:
			actions.append('browsecontent')
			items.append(interface.Format.bold(interface.Translation.string(35089) + ': ') + interface.Translation.string(35094))
			actions.append('downloadlargest')
			items.append(interface.Format.bold(interface.Translation.string(35150) + ': ') + interface.Translation.string(35151))
			actions.append('streamlargest')
			items.append(interface.Format.bold(interface.Translation.string(35090) + ': ') + interface.Translation.string(35095))
			actions.append('copylargest')
			items.append(interface.Format.bold(interface.Translation.string(35091) + ': ') + interface.Translation.string(35096))
			actions.append('openlargest')
			items.append(interface.Format.bold(interface.Translation.string(35092) + ': ') + interface.Translation.string(35097))
			actions.append('downloadzip')
			items.append(interface.Format.bold(interface.Translation.string(35152) + ': ') + interface.Translation.string(35153))
			actions.append('copyzip')
			items.append(interface.Format.bold(interface.Translation.string(35084) + ': ') + interface.Translation.string(35098))
			actions.append('openzip')
			items.append(interface.Format.bold(interface.Translation.string(35093) + ': ') + interface.Translation.string(35099))

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
					idFolder = item['folder']
					idFile = item['file']
					if choice == 'remove':
						self.mDebrid.deleteSingle(id, wait = True)
						interface.Directory.refresh()
						hide = False # Already hidden by container refresh.
					else:
						from resources.lib.extensions import downloader
						item = self.mDebrid.item(idFolder = idFolder, idFile = idFile)
						itemLink = item['video']['link']
						if choice == 'browsecontent':
							# Kodi cannot set the directory structure more than once in a single run.
							# If the action is launched directly by clicking on the item, Kodi seems to clear the structure so that you can create a new one.
							# This is not the case when the action menu is launched from the "Actions" option in the context menu.
							# Open the window externally. However, this will load longer and the back action is to the main menu.
							if context:
								itemJson = tools.Converter.jsonTo(item)
								tools.System.window(action = 'premiumizeItem', parameters = {'item' : itemJson})
							else:
								self.directoryItem(item)
						elif choice == 'streamlargest':
							if network.Networker.linkIs(itemLink): interface.Player.playNow(itemLink)
							else: raise Exception('Invalid Largest Link: ' + str(itemLink))
						elif choice == 'downloadlargest':
							if network.Networker.linkIs(itemLink): downloader.Downloader(downloader.Downloader.TypeManual).download(media = downloader.Downloader.MediaOther, link = itemLink)
							else: raise Exception('Invalid Largest Link: ' + str(itemLink))
						elif choice == 'copylargest':
							if network.Networker.linkIs(itemLink): clipboard.Clipboard.copyLink(itemLink, True)
							else: raise Exception('Invalid Largest Link: ' + str(itemLink))
						elif choice == 'openlargest':
							if network.Networker.linkIs(itemLink): tools.System.openLink(itemLink)
							else: raise Exception('Invalid Largest Link: ' + str(itemLink))
						else:
							itemZip = self.mDebrid.zip(idFolder)
							if choice == 'downloadzip':
								if network.Networker.linkIs(itemZip): downloader.Downloader(downloader.Downloader.TypeManual).download(media = downloader.Downloader.MediaOther, link = itemZip)
								else: raise Exception('Invalid ZIP Link: ' + str(itemZip))
							elif choice == 'copyzip':
								if network.Networker.linkIs(itemZip): clipboard.Clipboard.copyLink(itemZip, True)
								else: raise Exception('Invalid ZIP Link: ' + str(itemZip))
							elif choice == 'openzip':
								if network.Networker.linkIs(itemZip): tools.System.openLink(itemZip)
								else: raise Exception('Invalid ZIP Link: ' + str(itemZip))
				except:
					tools.Logger.error()
					interface.Dialog.notification(title = 33566, message = 35107, icon = interface.Dialog.IconError)
				if hide: interface.Loader.hide()

	def directoryList(self):
		directory = interface.Directory(content = interface.Directory.ContentAddons)
		items = self.mDebrid._itemsTransfer()
		itemsNew = [[], [], [], [], [], []]

		for item in items:
			info = []
			icon = None

			try: status = item['status']
			except: status = None

			if not status == None and not status == core.Core.StatusUnknown:
				color = None
				if status == core.Core.StatusError:
					color = interface.Format.colorBad()
					icon = 'downloadsfailed.png'
				elif status == core.Core.StatusTimeout:
					color = interface.Format.colorPoor()
					icon = 'downloadsfailed.png'
				elif status == core.Core.StatusQueued:
					color = interface.Format.colorMedium()
					icon = 'downloadsbusy.png'
				elif status == core.Core.StatusBusy:
					color = interface.Format.colorExcellent()
					icon = 'downloadsbusy.png'
				elif status == core.Core.StatusFinalize:
					color = interface.Format.colorMain()
					icon = 'downloadsbusy.png'
				elif status == core.Core.StatusFinished:
					color = interface.Format.colorSpecial()
					icon = 'downloadscompleted.png'
				info.append(interface.Format.fontColor(status.capitalize(), color))

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
			context.append({'label' : 33371, 'command' : tools.System.commandPlugin(action = 'premiumizeListAction', parameters = {'item' : itemJson, 'context' : 1})})

			if status == core.Core.StatusError: index = 0
			elif status == core.Core.StatusTimeout: index = 1
			elif status == core.Core.StatusQueued: index = 2
			elif status == core.Core.StatusBusy: index = 3
			elif status == core.Core.StatusFinalize: index = 4
			elif status == core.Core.StatusFinished: index = 5
			else: index = 0

			itemsNew[index].append({'item' : itemJson, 'label' : label, 'context' : context, 'icon' : icon})

		for item in itemsNew:
			for i in item:
				directory.add(label = i['label'], action = 'premiumizeListAction', parameters = {'item' : i['item']}, context = i['context'], folder = True, icon = i['icon'], iconDefault = 'DefaultAddonProgram.png')

		directory.finish()
