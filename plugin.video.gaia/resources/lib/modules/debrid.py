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


import urllib,json,time
from resources.lib.modules import cache
from resources.lib.modules import control
from resources.lib.modules import client

from resources.lib.extensions import tools
from resources.lib.extensions import debrid as debridx


def servicesPremiumize():
	try:
		premiumize = debridx.Premiumize()
		if premiumize.accountEnabled() and premiumize.accountValid():
			return premiumize.servicesList(onlyEnabled = True)
	except:
		pass
	return []

def servicesOffCloud():
	try:
		offcloud = debridx.OffCloud()
		if offcloud.accountEnabled() and offcloud.accountValid():
			return offcloud.servicesList(onlyEnabled = True)
	except:
		pass
	return []

def servicesRealDebrid():
	try:
		realdebrid = debridx.RealDebrid()
		if realdebrid.accountEnabled() and realdebrid.accountValid():
			return realdebrid.servicesList(onlyEnabled = True)
	except:
		pass
	return []

def servicesAllDebrid():
	try:
		alldebrid = debridx.AllDebrid()
		if alldebrid.accountEnabled() and alldebrid.accountValid():
			return alldebrid.servicesList(onlyEnabled = True)
	except:
		pass
	return []

def servicesRapidPremium():
	try:
		rapidpremium = debridx.RapidPremium()
		if rapidpremium.accountEnabled() and rapidpremium.accountValid():
			return rapidpremium.servicesList(onlyEnabled = True)
	except:
		pass
	return []

def services():
	return {
		'premiumize': servicesPremiumize(),
		'offcloud': servicesOffCloud(),
		'realdebrid': servicesRealDebrid(),
		'alldebrid': servicesAllDebrid(),
		'rapidpremium': servicesRapidPremium()
	}

def credentials():
	premiumize = debridx.Premiumize()
	offcloud = debridx.OffCloud()
	realdebrid = debridx.RealDebrid()
	alldebrid = debridx.AllDebrid()
	rapidpremium = debridx.RapidPremium()
	return {
		'premiumize': {
			'enabled' : premiumize.accountEnabled(),
			'user': premiumize.accountUsername(),
			'pass': premiumize.accountPassword(),
		},
		'offcloud': {
			'enabled' : offcloud.accountEnabled(),
			'api': offcloud.accountApi(),
		},
		'realdebrid': {
			'enabled' : realdebrid.accountEnabled(),
			'id': realdebrid.accountId(),
			'secret': realdebrid.accountSecret(),
			'token': realdebrid.accountToken(),
			'refresh': realdebrid.accountRefresh(),
		},
		'alldebrid': {
			'enabled' : alldebrid.accountEnabled(),
			'user': alldebrid.accountUsername(),
			'pass': alldebrid.accountPassword(),
		},
		'rapidpremium': {
			'enabled' : rapidpremium.accountEnabled(),
			'user': rapidpremium.accountUsername(),
			'api': rapidpremium.accountApi(),
		}
	}

def status(name = None):
	try:
		services = credentials()
		if name and not name == '':
			if name in services:
				services = {name : services[name]}
			else:
				services = {}
		c = [i for i in services.values() if (not '' in i.values() and i['enabled'])]
		if len(c) == 0: return False
		else: return True
	except:
		return False

def resolver(url, debrid, title = None, season = None, episode = None, close = True, source = None, pack = False, cached = False, hash = None, select = False, cloud = False):
	try: debrid = debrid.lower()
	except: pass

	url = url.replace('filefactory.com/stream/', 'filefactory.com/file/')

	if select: pack = True # Even non-season-pack archives should be selectable.

	# Always try Premiumize first.
	try:
		if not debrid == 'premiumize' and not debrid == True: raise Exception()
		if not debridx.Premiumize().accountValid(): raise Exception()
		return debridx.PremiumizeInterface().add(link = url, title = title, season = season, episode = episode, pack = pack, close = close, source = source, cached = cached, select = select, cloud = cloud)
	except:
		pass

	try:
		if not debrid == 'offcloud' and not debrid == True: raise Exception()
		if not debridx.OffCloud().accountValid(): raise Exception()
		return debridx.OffCloudInterface().add(link = url, title = title, season = season, episode = episode, pack = pack, close = close, source = source, cached = cached, select = select)
	except:
		pass

	try:
		if not debrid == 'realdebrid' and not debrid == True: raise Exception()
		if not debridx.RealDebrid().accountValid(): raise Exception()
		return debridx.RealDebridInterface().add(link = url, title = title, season = season, episode = episode, pack = pack, close = close, source = source, cached = cached, select = select)
	except:
		pass

	try:
		if not debrid == 'alldebrid' and not debrid == True: raise Exception()
		if not debridx.AllDebrid().accountValid(): raise Exception()
		return debridx.AllDebrid().add(link = url)
	except:
		pass

	try:
		if not debrid == 'rapidpremium' and not debrid == True: raise Exception()
		if not debridx.RapidPremium().accountValid(): raise Exception()
		return debridx.RapidPremium().add(link = url)
	except:
		pass

	return None
