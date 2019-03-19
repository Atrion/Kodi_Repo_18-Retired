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

import sys,re,json,urllib,urlparse,datetime

from resources.lib.modules import cache
from resources.lib.modules import cleangenre
from resources.lib.modules import control
from resources.lib.modules import client
from resources.lib.modules import metacache
from resources.lib.modules import workers
from resources.lib.modules import trakt
from resources.lib.modules import playcount

from resources.lib.extensions import tools
from resources.lib.extensions import interface
from resources.lib.extensions import shortcuts

class channels:

	def __init__(self, type = tools.Media.TypeMovie, kids = tools.Selection.TypeUndefined):
		self.type = type

		self.kids = kids
		self.restriction = 0

		self.list = []
		self.items = []
		self.channels = {}
		self.groups = ['sky', 'bbc', 'tcm', '5', 'channel', 'film4', 'itv', 'movies 24', 'quest', 'sony', 'syfy', 'true']

		# https://github.com/Mermade/openSky/wiki/URL-links
		# https://github.com/Mermade/openSky/wiki/Channel-Identifiers
		self.uk_datetime = self.uk_datetime()
		self.systime = (self.uk_datetime).strftime('%Y%m%d%H%M%S%f')
		self.tm_img_link = 'https://image.tmdb.org/t/p/w%s%s'
		self.sky_channels_link = 'http://epgservices.sky.com/tvlistings-proxy/TVListingsProxy/init.json'
		self.sky_programme_link = 'http://epgservices.sky.com/tvlistings-proxy/TVListingsProxy/tvlistings.json?detail=2&channels=%s&time=%s'
		self.generes = ['3', '6']

		self.lang = control.apiLanguage()['trakt']

	def parameterize(self, action):
		if not self.type == None: action += '&type=%s' % self.type
		if not self.kids == None: action += '&kids=%d' % self.kids
		return action

	def certificatesFormat(self, certificates):
		base = 'US%3A'
		if not isinstance(certificates, (tuple, list)): certificates = [certificates]
		return ','.join([base + i.upper() for i in base])

	def kidsOnly(self):
		return self.kids == tools.Selection.TypeInclude

	def getGroups(self):
		if not trakt.getTraktCredentialsInfo():
			interface.Dialog.confirm(title = 32007, message = 35245)
			return None
		if self.sky_channels():
			channels = sorted([i for i in self.channels.iterkeys()])
			self.groupDirectory(channels)
		return self.channels

	def getChannels(self, group = None):
		if not trakt.getTraktCredentialsInfo():
			interface.Dialog.confirm(title = 32007, message = 35245)
			return None
		if len(self.channels.keys()) == 0:
			if not self.sky_channels():
				return None
		if self.sky_list(group = group):
			threads = []
			for i in range(0, len(self.items)): threads.append(workers.Thread(self.items_list, self.items[i]))
			[i.start() for i in threads]
			[i.join() for i in threads]
			self.list = metacache.local(self.list, self.tm_img_link, 'poster2', 'fanart')
			try: self.list = sorted(self.list, key = lambda k : k['channel'])
			except: pass
			self.channelDirectory(self.list)
		return self.list

	def nameClean(self, name, group = None):
		name = name.replace('horhd', 'horror hd')
		name = re.sub('\s*hd$', '', name.lower())
		if group:
			group = group.lower()
			if bool(re.search('^(%s)[^\s].*' % group, name)): name = name.replace(group, group + ' ', 1)
		if bool(re.search('[^\s](\+1)', name)): name = name.replace('+1', ' +1')
		name = name.replace('prem ', 'premiere ')
		name = name.replace('megahits', 'mega hits').replace('feelgood', 'feel good')
		bbc = re.search('(bbc two)', name)
		if bbc: name = bbc.group(1)
		return name.strip()

	def sky_channels(self):
		try:
			result = cache.get(client.request, 744, self.sky_channels_link)
			result = json.loads(result)['channels']
			channels = []
			for i in self.groups:
				self.channels[i] = []
				names = []
				for j in result:
					if j['genre'] in self.generes:
						name = j['title'].lower()
						if name.startswith(i):
							name = self.nameClean(name = name, group = i.replace(' ', ''))
							if not name in names:
								names.append(name)
								names.append(name.replace(' ', ''))
								self.channels[i].append(j['channelid'])
			return len(self.channels.keys()) > 0
		except:
			tools.Logger.error()
			return False

	def sky_list(self, group = None):
		try:
			channels = []
			if group:
				channels = self.channels[group]
			else:
				for i in self.channels.itervalues():
					channels.extend(i)
			url = self.sky_programme_link % (','.join(channels), (self.uk_datetime).strftime('%Y%m%d%H%M'))
			result = cache.get(client.request, 0.25, url)
			result = json.loads(result)['channels']
			for i in result:
				try:
					if bool(re.search('(season|episode|s\s*\d+.*(e|ep)\s*\d+)', i['program']['shortDesc'], re.IGNORECASE)): continue
				except: pass
				name = self.nameClean(name = i['title'], group = group).upper()
				title = client.replaceHTMLCodes(i['program']['title'].strip()).encode('utf-8')
				try: year = int(re.findall('[(](\d{4})[)]', i['program']['shortDesc'])[0].strip().encode('utf-8'))
				except: year = None
				self.items.append((name, title, year))
			return len(self.items) > 0
		except:
			tools.Logger.error()
			return False

	def items_list(self, i):
		try:
			item = cache.get(trakt.SearchAll, 3, urllib.quote_plus(i[1]), i[2], True)[0]

			content = item.get('movie')
			if not content: content = item.get('show')
			item = content

			title = item.get('title')
			title = client.replaceHTMLCodes(title)

			originaltitle = title

			year = item.get('year', 0)
			year = re.sub('[^0-9]', '', str(year))

			imdb = item.get('ids', {}).get('imdb', '0')
			imdb = 'tt' + re.sub('[^0-9]', '', str(imdb))

			tmdb = str(item.get('ids', {}).get('tmdb', 0))

			premiered = item.get('released', '0')
			try: premiered = re.compile('(\d{4}-\d{2}-\d{2})').findall(premiered)[0]
			except: premiered = '0'

			genre = item.get('genres', [])
			genre = [x.title() for x in genre]
			genre = ' / '.join(genre).strip()
			if not genre: genre = '0'

			duration = str(item.get('Runtime', 0))

			rating = item.get('rating', '0')
			if not rating or rating == '0.0': rating = '0'

			votes = item.get('votes', '0')
			try: votes = str(format(int(votes), ',d'))
			except: pass

			mpaa = item.get('certification', '0')
			if not mpaa: mpaa = '0'

			tagline = item.get('tagline', '0')

			plot = item.get('overview', '0')

			people = trakt.getPeople(imdb, 'movies')
			director = writer = ''
			cast = []

			if people:
				if 'crew' in people and 'directing' in people['crew']:
					director = ', '.join([director['person']['name'] for director in people['crew']['directing'] if director['job'].lower() == 'director'])
				if 'crew' in people and 'writing' in people['crew']:
					writer = ', '.join([writer['person']['name'] for writer in people['crew']['writing'] if writer['job'].lower() in ['writer', 'screenplay', 'author']])
				for person in people.get('cast', []):
					cast.append({'name': person['person']['name'], 'role': person['character']})
				cast = [(person['name'], person['role']) for person in cast]

			try:
				if self.lang == 'en' or self.lang not in item.get('available_translations', [self.lang]): raise Exception()

				trans_item = trakt.getMovieTranslation(imdb, self.lang, full = True)

				title = trans_item.get('title') or title
				tagline = trans_item.get('tagline') or tagline
				plot = trans_item.get('overview') or plot
			except:
				pass

			self.list.append({'title': title, 'originaltitle': originaltitle, 'year': year, 'premiered': premiered, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa, 'director': director, 'writer': writer, 'cast': cast, 'plot': plot, 'tagline': tagline, 'imdb': imdb, 'tmdb': tmdb, 'poster': '0', 'channel': i[0]})
		except:
			pass

	def uk_datetime(self):
		dt = datetime.datetime.utcnow() + datetime.timedelta(hours = 0)
		d = datetime.datetime(dt.year, 4, 1)
		dston = d - datetime.timedelta(days=d.weekday() + 1)
		d = datetime.datetime(dt.year, 11, 1)
		dstoff = d - datetime.timedelta(days=d.weekday() + 1)
		if dston <=  dt < dstoff:
			return dt + datetime.timedelta(hours = 1)
		else:
			return dt

	def groupDirectory(self, items):
		if items == None or len(items) == 0:
			interface.Loader.hide()
			interface.Dialog.notification(title = 32007, message = 33049, icon = interface.Dialog.IconInformation)
			sys.exit()

		sysaddon = sys.argv[0]
		syshandle = int(sys.argv[1])
		addonFanart = control.addonFanart()

		for i in items:
			try:
				name = i
				url = self.parameterize('%s?action=channelsRetrieve&group=%s' % (sysaddon, name.lower()))

				item = control.item(label = name.replace(' ', '').upper())

				iconIcon, iconThumb, iconPoster, iconBanner = interface.Icon.pathAll(icon = 'networks.png', default = 'DefaultNetwork.png')
				item.setArt({'icon': iconIcon, 'thumb': iconThumb, 'poster': iconPoster, 'banner': iconBanner})
				if not addonFanart == None: item.setProperty('Fanart_Image', addonFanart)

				item.addContextMenuItems([interface.Context(mode = interface.Context.ModeGeneric, type = self.type, kids = self.kids, link = url, title = name, create = True).menu()])
				control.addItem(handle = syshandle, url = url, listitem = item, isFolder = True)
			except:
				pass

		control.content(syshandle, 'files')
		control.directory(syshandle, cacheToDisc = True)

	def channelDirectory(self, items):
		if items == None or len(items) == 0:
			interface.Loader.hide()
			interface.Dialog.notification(title = 32007, message = 33049, icon = interface.Dialog.IconInformation)
			sys.exit()

		sysaddon = sys.argv[0]
		syshandle = int(sys.argv[1])

		addonPoster, addonBanner = control.addonPoster(), control.addonBanner()
		addonFanart, settingFanart = control.addonFanart(), tools.Settings.getBoolean('interface.fanart')

		indicators = playcount.getMovieIndicators()
		isPlayable = 'true' if not 'plugin' in control.infoLabel('Container.PluginName') else 'false'

		for i in items:
			try:
				title = i['title']
				imdb, tmdb, year = i['imdb'], i['tmdb'], i['year']
				label = '[B]%s[/B][CR]%s (%s)' % (i['channel'].upper(), title, year)
				name = '%s (%s)' % (title, year)
				sysname = urllib.quote_plus(name)
				systitle = urllib.quote_plus(title)

				meta = dict((k,v) for k, v in i.iteritems() if not v == '0')
				meta.update({'mediatype': 'movie'})
				meta.update({'trailer': '%s?action=streamsTrailer&title=%s&imdb=%s' % (sysaddon, sysname, imdb)})
				meta.update({'playcount': 0, 'overlay': 6})
				try: meta.update({'genre': cleangenre.lang(meta['genre'], self.lang)})
				except: pass

				# Gaia
				# Some descriptions have a link at the end that. Remove it.
				try:
					plot = meta['plot']
					index = plot.rfind('See full summary')
					if index >= 0: plot = plot[:index]
					plot = plot.strip()
					if re.match('[a-zA-Z\d]$', plot): plot += ' ...'
					meta['plot'] = plot
				except: pass

				sysmeta = urllib.quote_plus(json.dumps(meta))
				url = self.parameterize('%s?action=scrape&title=%s&year=%s&imdb=%s&metadata=%s&t=%s' % (sysaddon, systitle, year, imdb, sysmeta, self.systime))

				watched = int(playcount.getMovieOverlay(indicators, imdb)) == 7
				if watched: meta.update({'playcount': 1, 'overlay': 7})
				else: meta.update({'playcount': 0, 'overlay': 6})

				item = control.item(label = label)

				poster = '0'
				if poster == '0' and 'poster3' in i: poster = i['poster3']
				if poster == '0' and 'poster2' in i: poster = i['poster2']
				if poster == '0' and 'poster' in i: poster = i['poster']

				icon = '0'
				if icon == '0' and 'icon3' in i: icon = i['icon3']
				if icon == '0' and 'icon2' in i: icon = i['icon2']
				if icon == '0' and 'icon' in i: icon = i['icon']

				thumb = '0'
				if thumb == '0' and 'thumb3' in i: thumb = i['thumb3']
				if thumb == '0' and 'thumb2' in i: thumb = i['thumb2']
				if thumb == '0' and 'thumb' in i: thumb = i['thumb']

				banner = '0'
				if banner == '0' and 'banner3' in i: banner = i['banner3']
				if banner == '0' and 'banner2' in i: banner = i['banner2']
				if banner == '0' and 'banner' in i: banner = i['banner']

				fanart = '0'
				if settingFanart:
					if fanart == '0' and 'fanart3' in i: fanart = i['fanart3']
					if fanart == '0' and 'fanart2' in i: fanart = i['fanart2']
					if fanart == '0' and 'fanart' in i: fanart = i['fanart']

				clearlogo = '0'
				if clearlogo == '0' and 'clearlogo' in i: clearlogo = i['clearlogo']

				clearart = '0'
				if clearart == '0' and 'clearart' in i: clearart = i['clearart']

				if poster == '0': poster = addonPoster
				if icon == '0': icon = poster
				if thumb == '0': thumb = poster
				if banner == '0': banner = addonBanner
				if fanart == '0': fanart = addonFanart

				art = {}
				if not poster == '0' and not poster == None: art.update({'poster' : poster})
				if not icon == '0' and not icon == None: art.update({'icon' : icon})
				if not thumb == '0' and not thumb == None: art.update({'thumb' : thumb})
				if not banner == '0' and not banner == None: art.update({'banner' : banner})
				if not clearlogo == '0' and not clearlogo == None: art.update({'clearlogo' : clearlogo})
				if not clearart == '0' and not clearart == None: art.update({'clearart' : clearart})
				if not fanart == '0' and not fanart == None: item.setProperty('Fanart_Image', fanart)

				item.setArt(art)
				item.setProperty('IsPlayable', isPlayable)
				item.setInfo(type = 'Video', infoLabels = tools.Media.metadataClean(meta))
				item.addContextMenuItems([interface.Context(mode = interface.Context.ModeItem, type = self.type, kids = self.kids, create = True, queue = True, watched = watched, refresh = True, metadata = meta, art = art, label = label, trailer = name, link = url, title = title, year = year, imdb = imdb, tmdb = tmdb).menu()])
				control.addItem(handle = syshandle, url = url, listitem = item, isFolder = False)
			except:
				pass

		control.content(syshandle, 'files')
		control.directory(syshandle, cacheToDisc = True)
