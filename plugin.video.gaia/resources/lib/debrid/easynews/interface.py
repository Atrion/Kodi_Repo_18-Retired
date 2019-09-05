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

from resources.lib.debrid import base
from resources.lib.debrid.easynews import core
from resources.lib.extensions import convert
from resources.lib.extensions import tools
from resources.lib.extensions import interface

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
				type = account['type']
				status = account['status'].capitalize()

				date = account['expiration']['date']
				days = str(account['expiration']['remaining'])

				loyaltyDate = account['loyalty']['time']['date']
				loyaltyPoints = '%.3f' % account['loyalty']['points']

				total = convert.ConverterSize(account['usage']['total']['size']['bytes']).stringOptimal()
				remaining = convert.ConverterSize(account['usage']['remaining']['size']['bytes']).stringOptimal() + (' (%.1f%%)' % account['usage']['remaining']['percentage'])
				consumed = convert.ConverterSize(account['usage']['consumed']['size']['bytes']).stringOptimal() + (' (%.1f%%)' % account['usage']['consumed']['percentage'])
				consumedWeb = convert.ConverterSize(account['usage']['consumed']['web']['size']['bytes']).stringOptimal() + (' (%.1f%%)' % account['usage']['consumed']['web']['percentage'])
				consumedNntp = convert.ConverterSize(account['usage']['consumed']['nntp']['size']['bytes']).stringOptimal() + (' (%.1f%%)' % account['usage']['consumed']['nntp']['percentage'])
				consumedNntpUnlimited = convert.ConverterSize(account['usage']['consumed']['nntpunlimited']['size']['bytes']).stringOptimal() + (' (%.1f%%)' % account['usage']['consumed']['nntpunlimited']['percentage'])

				items = []

				items = []

				# Information
				items.append({
					'title' : 33344,
					'items' : [
						{ 'title' : 33340, 'value' : valid },
						{ 'title' : 32303, 'value' : user },
						{ 'title' : 33343, 'value' : type },
						{ 'title' : 33389, 'value' : status },
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

				# Loyalty
				items.append({
					'title' : 33750,
					'items' : [
						{ 'title' : 33346, 'value' : loyaltyDate },
						{ 'title' : 33349, 'value' : loyaltyPoints }
					]
				})

				# Usage
				items.append({
					'title' : 33228,
					'items' : [
						{ 'title' : 33497, 'value' : total },
						{ 'title' : 33367, 'value' : remaining },
						{ 'title' : 33754, 'value' : consumed },
						{ 'title' : 33751, 'value' : consumedWeb },
						{ 'title' : 33752, 'value' : consumedNntp },
						{ 'title' : 33753, 'value' : consumedNntpUnlimited },
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
