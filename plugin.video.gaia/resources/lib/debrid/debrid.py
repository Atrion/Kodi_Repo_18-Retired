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

from resources.lib.extensions import tools

class Debrid(object):

	Instances = {}

	@classmethod
	def _path(self):
		return tools.File.directory(__file__)

	@classmethod
	def _import(self):
		import importlib
		directories, files = tools.File.listDirectory(self._path(), absolute = False)
		for directory in directories:
			module = importlib.import_module('resources.lib.debrid.' + directory)

	@classmethod
	def _instances(self, type = 'core'):
		if not type in Debrid.Instances:
			import importlib
			instances = []
			directories, files = tools.File.listDirectory(self._path(), absolute = False)
			for directory in directories:
				module = importlib.import_module('resources.lib.debrid.' + directory + '.' + type.lower())
				try: module = getattr(module, type.capitalize())()
				except: continue # If does not have the class (eg: EasyNews Handle).
				instances.append(module)
			Debrid.Instances[type] = instances
		return Debrid.Instances[type]

	@classmethod
	def enabled(self):
		for instance in self._instances():
			if instance.accountEnabled() and instance.accountValid(): return True
		return False

	@classmethod
	def services(self):
		result = {}
		for instance in self._instances():
			result[instance.id()] = instance.servicesList(onlyEnabled = True)
		return result

	@classmethod
	def cached(self, items):
		for value in items.itervalues():
			if value: return True
		return False

	@classmethod
	def deletePlayback(self, link, source):
		try: id = source['stream']['id']
		except: id = link
		try: handle = source['stream']['handle']
		except: handle = None
		try: category = source['stream']['category']
		except: category = None
		try: pack = source['pack']
		except: pack = None

		for instance in self._instances():
			if instance.id() == handle:
				if instance.deletePossible(source['source']):
					instance.deletePlayback(id = id, pack = pack, category = category)
				break

	@classmethod
	def handles(self, data = False, priority = False):
		instances = self._instances(type = 'handle')
		if priority:
			highest = 0
			for instance in instances:
				if instance.priority() > highest:
					highest = instance.priority()
			temp = [None] * (max(highest, len(instances)) + 1)
			for instance in instances:
				temp[instance.priority() - 1] = instance
			instances = [i for i in temp if i]
		if data:
			for i in range(len(instances)):
				instances[i] = instances[i].data()
		return instances
