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

import urllib
from resources.lib.extensions import database
from resources.lib.extensions import tools
from resources.lib.extensions import interface

class Shortcuts(database.Database):

	Name = 'shortcuts' # The name of the file. Update version number of the database structure changes.

	ParameterId = 'shortcutId'
	ParameterLocation = 'shortcutLocation'

	LocationDialog = 'dialog'
	LocationMain = 'main'
	LocationTools = 'tools'
	LocationMovies = 'movies'
	LocationMoviesFavourites = 'moviesfavourites'
	LocationShows = 'shows'
	LocationShowsFavourites = 'showsfavourites'
	LocationDocumentaries = 'documentaries'
	LocationDocumentariesFavourites = 'documentariesfavourites'
	LocationShorts = 'shorts'
	LocationShortsFavourites = 'shortsfavourites'

	def __init__(self):
		database.Database.__init__(self, Shortcuts.Name)

	@classmethod
	def direct(self, link):
		return 'action=scrape' in link or 'action=play' in link

	@classmethod
	def parameterize(self, link, location, id):
		return '%s&%s=%s&%s=%s' % (link, Shortcuts.ParameterId, str(id), Shortcuts.ParameterLocation, location)

	@classmethod
	def process(self, parameters):
		id = parameters.get(Shortcuts.ParameterId)
		if not id == None:
			location = parameters.get(Shortcuts.ParameterLocation)
			self().update(id = id, location = location)

	def _initialize(self):
		self._createAll('''
			CREATE TABLE IF NOT EXISTS %s
			(
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				link TEXT,
				name TEXT,
				time INTEGER,
				count INTEGER,
				UNIQUE(link)
			);
			''',
			[Shortcuts.LocationDialog, Shortcuts.LocationMain, Shortcuts.LocationTools, Shortcuts.LocationMovies, Shortcuts.LocationMoviesFavourites, Shortcuts.LocationShows, Shortcuts.LocationShowsFavourites, Shortcuts.LocationDocumentaries, Shortcuts.LocationDocumentariesFavourites, Shortcuts.LocationShorts, Shortcuts.LocationShortsFavourites]
		)

	def _prepare(self, data):
		return urllib.quote_plus(data)

	def _unprepare(self, data):
		return urllib.unquote(data)

	def insert(self, location, link, name):
		link = self._prepare(link)
		self._insert('''
			INSERT INTO %s
			(link, name, time, count)
			VALUES
			("%s", "%s", %d, 0);
			'''
			% (location, link, name, tools.Time.timestamp())
		)

	def update(self, location, id):
		self._update('UPDATE %s SET count = count + 1 WHERE id = %s;' % (location, str(id)))

	def delete(self, location, id):
		self._delete('DELETE FROM %s WHERE id = %s;' % (location, str(id)))

	def retrieveSingle(self, location, id):
		value = self._selectSingle('SELECT id, link, name, time, count FROM %s WHERE id = %s;' % (location, str(id)))
		value = (value[0], self._unprepare(value[1]), value[2], value[3])
		return value

	def retrieve(self, location):
		values = self._select('SELECT id, link, name, time, count FROM %s ORDER BY count DESC;' % location)
		for i in range(len(values)):
			values[i] = (values[i][0], self._unprepare(values[i][1]), values[i][2], values[i][3])
		return values

	def open(self, location, id):
		self.update(location = location, id = id)
		link = self.retrieveSingle(location = location, id = id)[1] # Do not unprepare here, otherwise shortcuts directly to movies/espideos don't work.
		if self.direct(link): # Run plugin directly if it searches videos (that is a movie/episode), otherwise an empty window shows in the background.
			tools.System.execute('RunPlugin(%s)' % link)
		else: # All other windows must be forcefully refreshed.
			tools.System.window(command = link, sleep = 1, refresh = True)

	def show(self, location = None, id = None, link = None, name = None, create = False, delete = False):
		items = [interface.Format.bold(35135)]
		if create: items.append(interface.Format.bold(35120))
		if delete: items.append(interface.Format.bold(35134))

		interface.Loader.hide()
		choice = interface.Dialog.options(title = 35119, items = items)
		if choice >= 0:
			if choice == 0: self.showOpen()
			elif choice == 1:
				if create: self.showCreate(link = link, name = name)
				else: self.showDelete(id = id, location = location)

	def showCreate(self, link, name = None, refresh = False):
		items = [
			interface.Format.bold(35525),
			interface.Format.bold(35121),
			interface.Format.bold(35137),
			interface.Format.bold(35122),
			interface.Format.bold(35123),
			interface.Format.bold(35124),
			interface.Format.bold(35125),
			interface.Format.bold(35126),
			interface.Format.bold(35127),
			interface.Format.bold(35128),
			interface.Format.bold(35129),
		]
		choice = interface.Dialog.options(title = 35130, items = items)
		if choice >= 0:
			if choice == 0: location = Shortcuts.LocationDialog
			elif choice == 1: location = Shortcuts.LocationMain
			elif choice == 2: location = Shortcuts.LocationTools
			elif choice == 3: location = Shortcuts.LocationMovies
			elif choice == 4: location = Shortcuts.LocationMoviesFavourites
			elif choice == 5: location = Shortcuts.LocationShows
			elif choice == 6: location = Shortcuts.LocationShowsFavourites
			elif choice == 7: location = Shortcuts.LocationDocumentaries
			elif choice == 8: location = Shortcuts.LocationDocumentariesFavourites
			elif choice == 9: location = Shortcuts.LocationShorts
			elif choice == 10: location = Shortcuts.LocationShortsFavourites

			if not name or name == '': name = interface.Translation.string(35131)
			name = interface.Dialog.input(title = 35132, type = interface.Dialog.InputAlphabetic, default = name)
			if not name or name == '': name = interface.Translation.string(35131)

			self.insert(location = location, link = link, name = name)
			if refresh: interface.Directory.refresh()
			interface.Dialog.notification(title = 35119, message = interface.Translation.string(35133) % items[choice], icon = interface.Dialog.IconSuccess)

	def showDelete(self, location, id, refresh = True):
		self.delete(location = location, id = id)
		if refresh: interface.Directory.refresh()
		interface.Dialog.notification(title = 35119, message = interface.Translation.string(35136), icon = interface.Dialog.IconSuccess)

	def showOpen(self):
		location = [
			(35525, Shortcuts.LocationDialog),
			(35121, Shortcuts.LocationMain),
			(35137, Shortcuts.LocationTools),
			(35122, Shortcuts.LocationMovies),
			(35123, Shortcuts.LocationMoviesFavourites),
			(35125, Shortcuts.LocationShows),
			(35124, Shortcuts.LocationShowsFavourites),
			(35126, Shortcuts.LocationDocumentaries),
			(35127, Shortcuts.LocationDocumentariesFavourites),
			(35128, Shortcuts.LocationShorts),
			(35129, Shortcuts.LocationShortsFavourites),
		]
		items = []
		ids = []
		locations = []
		for l in location:
			entries = self.retrieve(location = l[1])
			label = interface.Format.bold(interface.Translation.string(l[0]) + ': ')
			for entry in entries:
				items.append(label + entry[2])
				ids.append(entry[0])
				locations.append(l[1])
		choice = interface.Dialog.options(title = 35130, items = items)
		if choice >= 0:
			self.open(location = locations[choice], id = ids[choice])
