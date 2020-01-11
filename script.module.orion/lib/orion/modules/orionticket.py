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
# ORIONAPP
##############################################################################
# Class for managing Orion support tickets.
##############################################################################

import re
import copy
import threading
from orion.modules.orionapi import *
from orion.modules.orionuser import *
from orion.modules.orioninterface import *

class OrionTicket:

	##############################################################################
	# CONSTANTS
	##############################################################################

	StatusOpen = 'open'
	StatusClosed = 'closed'

	CategoryGeneral = 'general'
	CategoryAccount = 'account'
	CategoryBugs = 'bugs'
	CategoryDevelopment = 'development'
	CategoryLinks = 'links'
	CategoryPrivacy = 'privacy'
	CategoryLegal = 'legal'
	Categories = [
		{'type' : CategoryGeneral, 'name' : 'General & Questions'},
		{'type' : CategoryAccount, 'name' : 'Account & Payments'},
		{'type' : CategoryBugs, 'name' : 'Bugs & Suggestions'},
		{'type' : CategoryDevelopment, 'name' : 'API & Development'},
		{'type' : CategoryLinks, 'name' : 'Invalid & Dead Links'},
		{'type' : CategoryPrivacy, 'name' : 'Unsubscribe & GDPR'},
		{'type' : CategoryLegal, 'name' : 'Legal & DMCA'},
	]

	SubjectLength = 50
	SubjectDefault = 'Kodi %s Inquiry'

	Replacement = '\[\/?[^bi]\]'
	Replacements = (
		(('[URL]', '[url]'), '[I][COLOR ' + OrionInterface.ColorSecondary + ']'),
		(('[/URL]', '[/url]'), '[/COLOR][/I]'),

		# Kodi only understands upper tags.
		('[cr]', '[CR]'),
		('[b]', '[B]'),
		('[/b]', '[/B]'),
		('[i]', '[I]'),
		('[/i]', '[/I]'),
		('[light]', '[LIGHT]'),
		('[/light]', '[/LIGHT]'),
		('[color]', '[COLOR]'),
		('[/color]', '[/COLOR]'),

		# Kodi has no underlined.
		(('[U]', '[u]'), ''),
		(('[/U]', '[/u]'), ''),
	)

	AttachmentSize = 10485760 # 10 MB
	AttachmentCount = 3

	SupportEnabled = 'enabled'
	SupportDisabled = 'disabled'
	SupportDelayed = 'delayed'

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, id = None, status = None, data = {}):
		self.mData = data
		if id: self.idSet(id)
		if status: self.statusSet(status)

	##############################################################################
	# DATA
	##############################################################################

	def data(self):
		return self.mData

	##############################################################################
	# GENERAL
	##############################################################################

	def valid(self, default = None):
		return not self.status() == None

	##############################################################################
	# ID
	##############################################################################

	def id(self, default = None):
		try: return self.mData['id']
		except: return default

	def idSet(self, id):
		try: self.mData['id'] = id
		except: pass

	##############################################################################
	# TOKEN
	##############################################################################

	def token(self, default = None):
		try: return self.mData['token']
		except: return default

	##############################################################################
	# USER
	##############################################################################

	def user(self, default = None):
		try: return self.mData['user']
		except: return default

	##############################################################################
	# EMAIL
	##############################################################################

	def email(self, default = None):
		try: return self.mData['email']
		except: return default

	##############################################################################
	# CATEGORY
	##############################################################################

	def category(self, default = None, name = False):
		try:
			category = self.mData['category']
			if name:
				for i in OrionTicket.Categories:
					if category == i['type']:
						category = i['name']
						break
			return category
		except: return default

	##############################################################################
	# SUBJECT
	##############################################################################

	def subject(self, default = None, ellipse = False):
		try:
			subject = self.mData['subject']
			if ellipse and len(subject) > OrionTicket.SubjectLength:
				subject = subject[:OrionTicket.SubjectLength].strip() + ' ...'
			return subject
		except: return default

	##############################################################################
	# LAST
	##############################################################################

	def last(self, default = None):
		try: return self.mData['last']
		except: return default

	##############################################################################
	# STATUS
	##############################################################################

	def status(self, default = None):
		try: return self.mData['status']
		except: return default

	def statusSet(self, status):
		try: self.mData['status'] = status
		except: pass

	def statusOpen(self):
		return self.status() == OrionTicket.StatusOpen

	def statusClosed(self):
		return self.status() == OrionTicket.StatusClosed

	def statusColor(self):
		return OrionInterface.ColorBad if self.statusClosed() else OrionInterface.ColorPoor if self.last() else OrionInterface.ColorGood

	def statusLabel(self, uppercase = False, brackets = False, bold = False):
		label = OrionTools.unicodeString(self.status())
		label = label.upper() if uppercase else label.capitalize()
		if brackets: label = '[' + label + ']'
		return OrionInterface.font(label, color = self.statusColor(), bold = bold)

	##############################################################################
	# TIME
	##############################################################################

	def timeAdded(self, default = None):
		try: return self.mData['time']['added']
		except: return default

	def timeUpdated(self, default = None):
		try: return self.mData['time']['updated']
		except: return default

	def timeClosed(self, default = None):
		try: return self.mData['time']['closed']
		except: return default

	##############################################################################
	# MESSAGES
	##############################################################################

	def messages(self, reverse = False, default = None):
		try: return self.mData['messages'][::-1] if reverse else self.mData['messages']
		except: return default

	##############################################################################
	# FILES
	##############################################################################

	@classmethod
	def filesClean(self, files):
		files = copy.deepcopy(files)
		for i in range(len(files)):
			if 'path' in files[i]: del files[i]['path']
		return files

	##############################################################################
	# RETRIEVE
	##############################################################################

	def retrieve(self):
		try:
			api = OrionApi()
			result = api.ticketRetrieve(id = self.id())
			if not result: return False
			data = api.data()
			if data:
				self.mData = data
				return True
			else:
				return False
		except:
			OrionTools.error()
		return False

	@classmethod
	def retrieveAll(self):
		tickets = []
		try:
			api = OrionApi()
			if api.ticketRetrieve():
				ticketsApi = api.data()
				for data in ticketsApi:
					ticket = OrionTicket(data = data)
					tickets.append(ticket)
		except:
			OrionTools.error()
		return tickets

	##############################################################################
	# ADD
	##############################################################################

	def add(self, category, message, files = None, subject = None):
		try:
			if subject == None: subject = OrionTicket.SubjectDefault % category.capitalize()
			api = OrionApi()
			result = api.ticketAdd(category = category, subject = subject, message = message, files = self.filesClean(files))
			if not result: return False
			data = api.data()
			if data:
				self.mData = data
				return True
			else:
				return False
		except:
			OrionTools.error()
		return False

	##############################################################################
	# UPDATE
	##############################################################################

	def update(self, message, files = None):
		try:
			api = OrionApi()
			result = api.ticketUpdate(id = self.id(), message = message, files = self.filesClean(files))
			if not result: return False
			data = api.data()
			if data:
				self.mData = data
				return True
			else:
				return False
		except:
			OrionTools.error()
		return False

	##############################################################################
	# CLOSE
	##############################################################################

	def close(self):
		try:
			api = OrionApi()
			result = api.ticketClose(id = self.id())
			if not result: return False
			data = api.data()
			if data:
				self.mData = data
				return True
			else:
				return False
		except:
			OrionTools.error()
		return False

	##############################################################################
	# LABEL
	##############################################################################

	def label(self):
		label = []
		label.append(self.statusLabel(uppercase = True, brackets = True, bold = True))
		label.append(OrionInterface.fontBold(OrionTools.unicodeString(self.token())))
		label.append(OrionTools.unicodeString(self.subject(ellipse = True)))
		return OrionInterface.fontSeparator().join(label)

	##############################################################################
	# PATH
	##############################################################################

	@classmethod
	def _temporaryPath(self, create = True):
		path = OrionTools.pathJoin(OrionTools.pathTemporary(), 'attachments')
		if create: OrionTools.directoryCreate(path)
		return path

	@classmethod
	def _temporaryName(self):
		return OrionTools.addonName() + ' Attachment %s.%s' % (OrionTools.timeFormat(format = '%Y-%m-%d %H.%M.%S', local = True), OrionTools.ArchiveExtension)

	##############################################################################
	# DIALOG
	##############################################################################

	def dialog(self):
		if self.id() == None:
			self.dialogUpdate(new = True, refresh = True)
		else:
			items = [32292, 32293]
			if self.statusOpen(): items.append(32294)
			choice = OrionInterface.dialogOptions(title = 32286, items = items)
			if choice == 0: self.dialogView(retrieve = True)
			elif choice == 1: self.dialogUpdate(refresh = True)
			elif choice == 2: self.dialogClose(refresh = True)

	def dialogView(self, retrieve = False):
		if retrieve:
			OrionInterface.loaderShow()
			success = self.retrieve()
			OrionInterface.loaderHide()
			if not success: return False

		sections = []

		id = OrionUser.instance().id()
		you = OrionInterface.font(OrionTools.translate(32288), color = OrionInterface.ColorPrimary)
		orion = OrionInterface.font(OrionTools.addonName(), color = OrionInterface.ColorPrimary)

		message = ''
		message += OrionInterface.font(OrionTools.unicodeString(self.subject()), bold = True, color = OrionInterface.ColorSecondary) + OrionInterface.fontNewline() + OrionInterface.fontNewline()
		message += OrionInterface.font(OrionTools.translate(32295) + ': ', bold = True, color = OrionInterface.ColorPrimary) + OrionTools.unicodeString(self.token()) + OrionInterface.fontNewline()
		message += OrionInterface.font(OrionTools.translate(32296) + ': ', bold = True, color = OrionInterface.ColorPrimary) + OrionTools.unicodeString(self.category(name = True)) + OrionInterface.fontNewline()
		message += OrionInterface.font(OrionTools.translate(32297) + ': ', bold = True, color = OrionInterface.ColorPrimary) + self.statusLabel()
		sections.append(message)

		items = self.messages(reverse = True)
		for item in items:
			text = item['text']
			for i in OrionTicket.Replacements:
				if OrionTools.isArray(i[0]):
					for j in i[0]:
						text = text.replace(j, i[1])
				else:
					text = text.replace(i[0], i[1])
			text = re.sub(OrionTicket.Replacement, '', text, flags = re.IGNORECASE)

			meta = [
				you if id == item['user'] else orion,
				OrionTools.timeFormat(date = item['time'], format = OrionTools.FormatDateTime, local = True),
			]
			try:
				attachments = len(item['attachments'])
				if attachments > 0: meta.append(OrionInterface.font(OrionTools.unicodeString(attachments) + ' ' + OrionTools.translate(32298 if attachments == 1 else 32299), color = OrionInterface.ColorSecondary))
			except: pass

			message = ''
			message += OrionInterface.fontBold(OrionInterface.fontSeparator().join(meta)) + OrionInterface.fontNewline() + OrionInterface.fontNewline()
			message += OrionInterface.fontLight(text)
			sections.append(message)

		OrionInterface.dialogPage(title = 32286, message = OrionInterface.fontLine().join(sections))
		return True

	def dialogUpdate(self, new = False, refresh = False):
		if new or self.statusOpen() or OrionInterface.dialogOption(title = 32286, message = 33051):
			category = None
			message = None
			files = []
			defaults = [OrionTools.directoryNameClean(OrionTools.pathHome()), OrionTools.directoryNameClean(OrionTools.pathKodi())]
			path = self._temporaryPath()

			if new:
				types = []
				items = []
				for item in OrionTicket.Categories:
					types.append(item['type'])
					items.append(item['name'])
				choice = OrionInterface.dialogOptions(title = 32286, items = items)
				if choice < 0: return False
				category = types[choice]

			while True:
				message = OrionInterface.dialogInput(title = 32300)
				if message:
					message = message.replace('\\n', '\n')
					break
				choice = OrionInterface.dialogOption(title = 32286, message = 33052, labelConfirm = 32250, labelDeny = 32251)
				if not choice: return False
			while True:
				items = [32306, 32301, 32302, 32303, 32304, 32305] if len(files) < OrionTicket.AttachmentCount else [32306]
				count = len(items)
				for file in files:
					items.append(OrionInterface.fontSeparator().join([OrionInterface.fontBold('[' + file['type'] + ']'), OrionTools.fileSizeFormat(file['size']), file['name']]))
				choice = OrionInterface.dialogOptions(title = 32286, items = items)

				if choice < 0:
					for file in files:
						OrionTools.fileDelete(path = file['path'])
					return False
				elif choice == 0:
					OrionInterface.loaderShow()
					for i in range(len(files)):
						files[i]['data'] = OrionTools.base64To(OrionTools.fileRead(path = files[i]['path'], binary = True))
					result = self.add(category = category, message = message, files = files) if new else self.update(message = message, files = files)
					if result:
						for file in files:
							OrionTools.fileDelete(path = file['path'])
						if refresh: OrionInterface.containerRefresh()
						OrionInterface.dialogNotification(title = 32286, message = 33060, icon = OrionInterface.IconSuccess)
						OrionInterface.loaderHide()
						return True
					OrionInterface.loaderHide()
				elif choice < count:
					file = None
					if choice == 1:
						if OrionInterface.dialogOption(title = 32286, message = 33055, labelConfirm = 32250, labelDeny = 32251):
							if not OrionTools.kodiDebugging() or OrionInterface.dialogOption(title = 32286, message = 33056, labelConfirm = 32250, labelDeny = 32251):
								OrionInterface.loaderShow()
								file = OrionTools.bugs(path)
								OrionInterface.loaderHide()
								if not file: OrionInterface.dialogNotification(title = 32286, message = 33058, icon = OrionInterface.IconError)
					else:
						if choice == 2: source = OrionInterface.dialogBrowse(title = 32286, type = OrionInterface.BrowseFile, default = OrionTools.pathKodi())
						elif choice == 3: source = OrionInterface.dialogBrowse(title = 32286, type = OrionInterface.BrowseDirectoryRead, default = OrionTools.pathKodi())
						elif choice == 4: source = OrionInterface.dialogBrowse(title = 32286, type = OrionInterface.BrowseFile)
						elif choice == 5: source = OrionInterface.dialogBrowse(title = 32286, type = OrionInterface.BrowseDirectoryRead)

						# If you get to the most parent directory and hit backspace, the Kodi file dialog returns the user home directory or the default path if set.
						# Check this, otherwise Orion will zip the entire home dir.
						if source and not OrionTools.directoryNameClean(source) in defaults:
							OrionInterface.loaderShow()
							file = OrionTools.pathJoin(path, self._temporaryName())
							if not OrionTools.archiveCreate(file, source, parent = (choice == 3 or choice == 5)):
								OrionInterface.dialogNotification(title = 32286, message = 33059, icon = OrionInterface.IconError)
								OrionTools.fileDelete(file)
								file = None
							OrionInterface.loaderHide()

					if file:
						file = {
							'type' : OrionTools.fileExtension(file).upper(),
							'size' : OrionTools.fileSize(file),
							'name' : OrionTools.fileName(file),
							'path' : file,
						}
						if file['size'] <= OrionTicket.AttachmentSize: files.append(file)
						else: OrionInterface.dialogConfirm(title = 32286, message = OrionTools.translate(33057) % (OrionTools.fileSizeFormat(file['size']), OrionTools.fileSizeFormat(OrionTicket.AttachmentSize)))
				else:
					choice -= count
					OrionTools.fileDelete(path = files[choice]['path'])
					files.pop(choice)
					OrionInterface.dialogNotification(title = 32286, message = 32307, icon = OrionInterface.IconInformation)

	def dialogClose(self, refresh = False):
		if OrionInterface.dialogOption(title = 32286, message = 33050):
			OrionInterface.loaderShow()
			if self.close():
				if refresh: OrionInterface.containerRefresh()
				OrionInterface.dialogNotification(title = 32286, message = 33053, icon = OrionInterface.IconSuccess)
				return True
			OrionInterface.loaderHide()
		return False

	@classmethod
	def dialogNew(self):
		if OrionSettings.getGeneralNotificationsTickets():
			tickets = self.retrieveAll()
			for ticket in tickets:
				if ticket.statusOpen() and not ticket.last():
					OrionInterface.dialogNotification(title = 32285, message = 33061, icon = OrionInterface.IconInformation)
					return

	@classmethod
	def dialogSupport(self, wait = False):
		def _dialogStatus():
			api = OrionApi()
			result = api.ticketStatus()
			if result:
				data = api.data()
				message = None
				if data['status'] == OrionTicket.SupportDisabled: message = OrionTools.translate(33064) % OrionTools.timeFormat(date = data['time']['start'], format = OrionTools.FormatDateReadable, local = True) if data['time']['start'] else 33063
				elif data['status'] == OrionTicket.SupportDelayed: message = OrionTools.translate(33066) % OrionTools.timeFormat(date = data['time']['start'], format = OrionTools.FormatDateReadable, local = True) if data['time']['start'] else 33065
				if message:
					if data['message']: message += ' ' + data['message']
					OrionInterface.dialogConfirm(title = 32284, message = message)
		thread = threading.Thread(target = _dialogStatus)
		thread.start()
		if wait: thread.join()
