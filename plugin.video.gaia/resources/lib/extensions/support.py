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

from resources.lib.extensions import api
from resources.lib.extensions import tools
from resources.lib.extensions import interface

class Support(object):

	def __init__(self):
		pass

	@classmethod
	def _error(self):
		interface.Dialog.notification(title = 35311, message = tools.System.name() + ' ' + interface.Translation.string(35312), icon = interface.Dialog.IconError)

	@classmethod
	def guide(self):
		tools.System.openLink(tools.Settings.getString('link.guide', raw = True))

	@classmethod
	def bugs(self):
		tools.System.openLink(tools.Settings.getString('link.support', raw = True))

	@classmethod
	def navigator(self):
		directory = interface.Directory()
		directory.add(label = 35314, action = 'supportCategories', folder = True, icon = 'help')
		directory.add(label = 35313, action = 'supportBugs', folder = False, icon = 'bug')
		directory.add(label = 35315, action = 'supportGuide', folder = False, icon = 'bulb')
		directory.add(label = 35321, action = 'backupReaper', folder = True, icon = 'settings')
		directory.finish()

	@classmethod
	def categories(self):
		interface.Loader.show()
		try:
			categories = api.Api.supportCategories()
			directory = interface.Directory()
			for category in categories:
				label = interface.Format.bold(category['name'] + ': ') + category['description'].replace('.', '')
				directory.add(label = label, action = 'supportQuestions', parameters = {'id' : category['id']}, folder = True, icon = 'help')
			directory.finish()
		except:
			self._error()
		interface.Loader.hide()

	@classmethod
	def questions(self, id):
		interface.Loader.show()
		try:
			questions = api.Api.supportList(id)
			directory = interface.Directory()
			for question in questions:
				directory.add(label = question['title'], action = 'supportQuestion', parameters = {'id' : question['id']}, folder = False, icon = 'help')
			directory.finish()
		except:
			self._error()
		interface.Loader.hide()

	@classmethod
	def question(self, id):
		interface.Loader.show()
		try:
			question = api.Api.supportQuestion(id)
			interface.Dialog.page(title = question['title'], message = question['message']['format'])
		except:
			self._error()
		interface.Loader.hide()
