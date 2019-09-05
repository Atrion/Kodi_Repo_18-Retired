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

import os,sys,re,json,zipfile,StringIO,urllib,urllib2,urlparse,datetime,copy

from resources.lib.modules import trakt
from resources.lib.modules import cleantitle
from resources.lib.modules import cleangenre
from resources.lib.modules import control
from resources.lib.modules import client
from resources.lib.modules import playcount
from resources.lib.modules import workers
from resources.lib.modules import views
from resources.lib.modules import metacache

from resources.lib.extensions import tools
from resources.lib.extensions import cache
from resources.lib.extensions import interface
from resources.lib.extensions import shortcuts

class episodes:

	def __init__(self, type = tools.Media.TypeShow, kids = tools.Selection.TypeUndefined, notifications = True):
		self.type = type

		self.kids = kids
		self.certificates = None
		self.restriction = 0
		self.notifications = notifications

		if self.kidsOnly():
			self.certificates = []
			self.restriction = tools.Settings.getInteger('general.kids.restriction')
			if self.restriction >= 0:
				#self.certificates.append('TV-G') Althougn IMDb has this rating, when filtered, it returns series with other mature ratings as well.
				self.certificates.append('TV-Y')
			if self.restriction >= 1:
				self.certificates.append('TV-Y7')
			if self.restriction >= 2:
				self.certificates.append('TV-PG')
			if self.restriction >= 3:
				self.certificates.append('TV-13')
				self.certificates.append('TV-14')
			self.certificates = '&certificates=' + self.certificatesFormat(self.certificates)
		else:
			self.certificates = ''

		self.threads = []
		self.list = []

		self.trakt_link = 'http://api-v2launch.trakt.tv'
		self.tvmaze_link = 'http://api.tvmaze.com'
		self.tvdb_key = tools.System.obfuscate(tools.Settings.getString('internal.tvdb.api', raw = True))
		self.datetime = (datetime.datetime.utcnow() - datetime.timedelta(hours = 5))
		self.today_date = (self.datetime).strftime('%Y-%m-%d')
		self.trakt_user = tools.Settings.getString('accounts.informants.trakt.user').strip()
		self.lang = control.apiLanguage()['tvdb']

		self.fanart_tv_user = tools.Settings.getString('accounts.artwork.fanart.api') if tools.Settings.getBoolean('accounts.artwork.fanart.enabled') else ''
		self.user = self.fanart_tv_user + str('')

		self.tvdb_info_link = 'http://thetvdb.com/api/%s/series/%s/all/%s.zip' % (self.tvdb_key, '%s', '%s')
		self.tvdb_image = 'http://thetvdb.com/banners/'
		self.tvdb_poster = 'http://thetvdb.com/banners/_cache/'

		self.added_link = 'http://api.tvmaze.com/schedule'
		self.mycalendar_link = 'http://api-v2launch.trakt.tv/calendars/my/shows/date[29]/60/'
		self.trakthistory_link = 'http://api-v2launch.trakt.tv/users/me/history/shows?limit=300'
		self.progress_link = 'http://api-v2launch.trakt.tv/users/me/watched/shows'
		self.hiddenprogress_link = 'http://api-v2launch.trakt.tv/users/hidden/progress_watched?limit=1000&type=show'
		self.calendar_link = 'http://api.tvmaze.com/schedule?date=%s'

		self.traktwatchlist_link = 'http://api-v2launch.trakt.tv/users/me/watchlist/episodes'
		self.traktlists_link = 'http://api-v2launch.trakt.tv/users/me/lists'
		self.traktlikedlists_link = 'http://api-v2launch.trakt.tv/users/likes/lists?limit=1000000'
		self.traktlist_link = 'http://api-v2launch.trakt.tv/users/%s/lists/%s/items'
		self.traktunfinished_link = 'https://api.trakt.tv/sync/playback/episodes'

	def parameterize(self, action):
		if not self.type == None: action += '&type=%s' % self.type
		if not self.kids == None: action += '&kids=%d' % self.kids
		return action

	def certificatesFormat(self, certificates):
		base = 'US%3A'
		if not isinstance(certificates, (tuple, list)): certificates = [certificates]
		return ','.join([base + i.upper() for i in certificates])

	def kidsOnly(self):
		return self.kids == tools.Selection.TypeInclude

	@classmethod
	def mark(self, title, imdb, tvdb, season, episode, watched = True):
		if watched: self.markWatch(title = title, imdb = imdb, tvdb = tvdb, season = season, episode = episode)
		else: self.markUnwatch(title = title, imdb = imdb, tvdb = tvdb, season = season, episode = episode)

	@classmethod
	def markWatch(self, title, imdb, tvdb, season, episode):
		interface.Loader.show()
		playcount.episodes(imdb, tvdb, season, episode, '7')
		interface.Loader.hide()
		interface.Dialog.notification(title = 35513, message = 35510, icon = interface.Dialog.IconSuccess)

	@classmethod
	def markUnwatch(self, title, imdb, tvdb, season, episode):
		interface.Loader.show()
		playcount.episodes(imdb, tvdb, season, episode, '6')
		interface.Loader.hide()
		interface.Dialog.notification(title = 35513, message = 35511, icon = interface.Dialog.IconSuccess)

	def sort(self, type = 'shows'):
		try:
			attribute = tools.Settings.getInteger('interface.sort.%s.type' % type)
			reverse = tools.Settings.getInteger('interface.sort.%s.order' % type) == 1
			if attribute > 0:
				if attribute == 1:
					if tools.Settings.getBoolean('interface.sort.articles'):
						try: self.list = sorted(self.list, key = lambda k: re.sub('(^the |^a |^an )', '', k['tvshowtitle'].lower()), reverse = reverse)
						except: self.list = sorted(self.list, key = lambda k: re.sub('(^the |^a |^an )', '', k['title'].lower()), reverse = reverse)
					else:
						try: self.list = sorted(self.list, key = lambda k: k['tvshowtitle'].lower(), reverse = reverse)
						except: self.list = sorted(self.list, key = lambda k: k['title'].lower(), reverse = reverse)
				elif attribute == 2:
					self.list = sorted(self.list, key = lambda k: float(k['rating']), reverse = reverse)
				elif attribute == 3:
					self.list = sorted(self.list, key = lambda k: int(k['votes'].replace(',', '')), reverse = reverse)
				elif attribute == 4:
					for i in range(len(self.list)):
						if not 'premiered' in self.list[i]: self.list[i]['premiered'] = ''
					self.list = sorted(self.list, key = lambda k: k['premiered'], reverse = reverse)
				elif attribute == 5:
					for i in range(len(self.list)):
						if not 'added' in self.list[i]: self.list[i]['added'] = ''
					self.list = sorted(self.list, key = lambda k: k['added'], reverse = reverse)
				elif attribute == 6:
					for i in range(len(self.list)):
						if not 'watched' in self.list[i]: self.list[i]['watched'] = ''
					self.list = sorted(self.list, key = lambda k: k['watched'], reverse = reverse)
			elif reverse:
				self.list.reverse()
		except:
			tools.Logger.error()

	def get(self, tvshowtitle, year, imdb, tvdb, season = None, episode = None, single = False, idx = True):
		from resources.lib.indexers import seasons
		try:
			if season is None and episode is None:
				self.list = cache.Cache().cacheShort(seasons.seasons().tvdb_list, tvshowtitle, year, imdb, tvdb, self.lang, '-1')
			elif episode is None:
				self.list = cache.Cache().cacheShort(seasons.seasons().tvdb_list, tvshowtitle, year, imdb, tvdb, self.lang, season)
			else:
				self.list = cache.Cache().cacheShort(seasons.seasons().tvdb_list, tvshowtitle, year, imdb, tvdb, self.lang, '-1')
				num = [x for x, y in enumerate(self.list) if y['season'] == str(season) and y['episode'] == str(episode)][-1]
				if single: self.list = [y for x, y in enumerate(self.list) if x == num]
				else: self.list = [y for x, y in enumerate(self.list) if x >= num]

			if self.kidsOnly():
				self.list = [i for i in self.list if 'mpaa' in i and tools.Kids.allowed(i['mpaa'])]

			if idx == True: self.episodeDirectory(self.list)

			return self.list
		except:
			try: invalid = self.list == None or len(self.list) == 0
			except: invalid = True
			if invalid:
				interface.Loader.hide()
				if self.notifications: interface.Dialog.notification(title = 32326, message = 33049, icon = interface.Dialog.IconInformation)

	def next(self, tvshowtitle, year, imdb, tvdb, season, episode):
		try:
			result = self.get(tvshowtitle = tvshowtitle, year = year, imdb = imdb, tvdb = tvdb, season = int(season), episode = int(episode) + 1, idx = False)
			if not result: result = self.get(tvshowtitle = tvshowtitle, year = year, imdb = imdb, tvdb = tvdb, season = int(season) + 1, episode = 1, idx = False)
			result = result[0]
			if int(re.sub('[^0-9]', '', str(result['premiered']))) < int(re.sub('[^0-9]', '', str(self.today_date))): return result
		except: pass
		return None

	def unfinished(self):
		try:
			self.list = cache.Cache().cacheMini(self.trakt_list, self.traktunfinished_link, self.trakt_user, True)
			if self.kidsOnly(): self.list = [i for i in self.list if 'mpaa' in i and tools.Kids.allowed(i['mpaa'])]
			self.episodeDirectory(self.list, unfinished = True)
			return self.list
		except:
			tools.Logger.error()
			try: invalid = self.list == None or len(self.list) == 0
			except: invalid = True
			if invalid:
				interface.Loader.hide()
				interface.Dialog.notification(title = 32326, message = 33049, icon = interface.Dialog.IconInformation)

	def seasonCount(self, items, index):
		if not 'seasoncount' in items[index] or not items[index]['seasoncount']:
			thread = workers.Thread(self._seasonCount, items, index)
			self.threads.append(thread)
			thread.start()

	def seasonCountWait(self):
		[i.join() for i in self.threads]
		self.threads = []

	def _seasonCount(self, items, index):
		try:
			from resources.lib.indexers import seasons
			items[index]['seasoncount'] = seasons.seasons().seasonCount(items[index]['tvshowtitle'], items[index]['year'], items[index]['imdb'], items[index]['tvdb'], items[index]['season'])
		except:
			tools.Logger.error()

	def calendar(self, url, idx = True, direct = None):
		try:
			if direct is None: direct = tools.Settings.getBoolean('interface.tvshows.direct')

			multi = False
			try: url = getattr(self, url + '_link')
			except: pass

			if self.trakt_link in url and url == self.progress_link:
				multi = True
				self.list = cache.Cache().cacheMini(self.trakt_progress_list, url, self.trakt_user, self.lang, direct)
				self.sort(type = 'progress')

			elif self.trakt_link in url and url == self.mycalendar_link:
				self.list = cache.Cache().cacheMini(self.trakt_episodes_list, url, self.trakt_user, self.lang, direct)
				self.sort(type = 'calendar')

			elif self.trakt_link in url and '/users/' in url:
				self.list = cache.Cache().cacheMini(self.trakt_list, url, self.trakt_user, True, direct)
				self.list = self.list[::-1]

			elif self.trakt_link in url:
				self.list = cache.Cache().cacheShort(self.trakt_list, url, self.trakt_user, True, direct)

			elif self.tvmaze_link in url and url == self.added_link:
				urls = [i['url'] for i in self.calendars(idx = False)][:5]
				self.list = []
				for url in urls:
					self.list += cache.Cache().cacheLong(self.tvmaze_list, url, True, True, direct)

			elif self.tvmaze_link in url:
				self.list = cache.Cache().cacheShort(self.tvmaze_list, url, False, True, direct)

			if self.kidsOnly():
				self.list = [i for i in self.list if 'mpaa' in i and tools.Kids.allowed(i['mpaa'])]

			if idx: self.episodeDirectory(self.list, multi = multi)
			return self.list
		except:
			pass

	def arrivals(self, idx = True):
		direct = tools.Settings.getBoolean('interface.tvshows.direct')
		if trakt.getTraktIndicatorsInfo() == True: setting = tools.Settings.getInteger('interface.arrivals.shows')
		else: setting = 0

		if setting == 0: return self.calendar(self.added_link, idx = idx, direct = direct)
		elif setting == 1: return self.home(idx = idx, direct = direct)
		elif setting == 2:
			from resources.lib.indexers import tvshows
			return tvshows.tvshows(type = self.type, kids = self.kids).get('airing')
		elif setting == 3: return self.calendar(self.progress_link, idx = idx, direct = direct)
		elif setting == 4: return self.calendar(self.mycalendar_link, idx = idx, direct = direct)
		else: return self.home(idx = idx, direct = direct)

	def home(self, idx = True, direct = False):
		date = self.datetime - datetime.timedelta(days = 1)
		url = self.calendar_link % date.strftime('%Y-%m-%d')
		self.list = cache.Cache().cacheShort(self.tvmaze_list, url, False, True, direct)
		if idx: self.episodeDirectory(self.list)
		return self.list

	def calendars(self, idx = True):
		m = control.lang(32060).encode('utf-8').split('|')
		try: months = [(m[0], 'January'), (m[1], 'February'), (m[2], 'March'), (m[3], 'April'), (m[4], 'May'), (m[5], 'June'), (m[6], 'July'), (m[7], 'August'), (m[8], 'September'), (m[9], 'October'), (m[10], 'November'), (m[11], 'December')]
		except: months = []

		d = control.lang(32061).encode('utf-8').split('|')
		try: days = [(d[0], 'Monday'), (d[1], 'Tuesday'), (d[2], 'Wednesday'), (d[3], 'Thursday'), (d[4], 'Friday'), (d[5], 'Saturday'), (d[6], 'Sunday')]
		except: days = []

		for i in range(0, 30):
			try:
				name = (self.datetime - datetime.timedelta(days = i))
				name = (control.lang(32062) % (name.strftime('%A'), name.strftime('%d %B'))).encode('utf-8')
				for m in months: name = name.replace(m[1], m[0])
				for d in days: name = name.replace(d[1], d[0])
				try: name = name.encode('utf-8')
				except: pass

				url = self.calendar_link % (self.datetime - datetime.timedelta(days = i)).strftime('%Y-%m-%d')

				self.list.append({'name': name, 'url': url, 'image': 'calendar.png', 'action': 'showsCalendar'})
			except:
				pass

		if idx == True: self.addDirectory(self.list)
		return self.list

	def userlists(self):
		userlists = []

		try:
			if trakt.getTraktCredentialsInfo() == False: raise Exception()
			self.list = []
			userlists += cache.Cache().cacheMini(self.trakt_user_list, self.traktlists_link, self.trakt_user)
		except:
			pass

		try:
			if trakt.getTraktCredentialsInfo() == False: raise Exception()
			self.list = []
			userlists += cache.Cache().cacheMini(self.trakt_user_list, self.traktlikedlists_link, self.trakt_user)
		except:
			pass

		self.list = []

		# Filter the user's own lists that were
		for i in range(len(userlists)):
			contains = False
			adapted = userlists[i]['url'].replace('/me/', '/%s/' % self.trakt_user)
			for j in range(len(self.list)):
				if adapted == self.list[j]['url'].replace('/me/', '/%s/' % self.trakt_user):
					contains = True
					break
			if not contains:
				self.list.append(userlists[i])

		for i in range(0, len(self.list)): self.list[i].update({'image': 'traktlists.png', 'action': self.parameterize('showsCalendar')})

		# Watchlist
		if trakt.getTraktCredentialsInfo():
			self.list.insert(0, {'name' : interface.Translation.string(32033), 'url' : self.traktwatchlist_link, 'image': 'traktwatch.png', 'action': self.parameterize('tvshows')})

		self.addDirectory(self.list)
		return self.list


	def trakt_list(self, url, user, count = False, direct = False):
		try:
			for i in re.findall('date\[(\d+)\]', url):
				url = url.replace('date[%s]' % i, (self.datetime - datetime.timedelta(days = int(i))).strftime('%Y-%m-%d'))

			q = dict(urlparse.parse_qsl(urlparse.urlsplit(url).query))
			q.update({'extended': 'full'})
			q = (urllib.urlencode(q)).replace('%2C', ',')
			u = url.replace('?' + urlparse.urlparse(url).query, '') + '?' + q

			itemlist = []
			items = trakt.getTraktAsJson(u)
		except:
			return

		for item in items:
			try:
				if not 'show' in item or not 'episode' in item:
					raise Exception()

				try: title = item['episode']['title'].encode('utf-8')
				except: title = item['episode']['title']
				if title == None or title == '': raise Exception()
				title = client.replaceHTMLCodes(title)
				try: title = title.encode('utf-8')
				except: pass

				season = item['episode']['season']
				season = re.sub('[^0-9]', '', '%01d' % int(season))
				if season == '0': raise Exception()
				season = season.encode('utf-8')

				episode = item['episode']['number']
				episode = re.sub('[^0-9]', '', '%01d' % int(episode))
				if episode == '0': raise Exception()
				episode = episode.encode('utf-8')

				try: tvshowtitle = item['show']['title'].encode('utf-8')
				except: tvshowtitle = item['show']['title']
				if tvshowtitle == None or tvshowtitle == '': raise Exception()
				tvshowtitle = client.replaceHTMLCodes(tvshowtitle)
				try: tvshowtitle = tvshowtitle.encode('utf-8')
				except: pass

				year = item['show']['year']
				year = re.sub('[^0-9]', '', str(year))
				year = year.encode('utf-8')

				try: progress = max(0, min(1, item['progress'] / 100.0))
				except: progress = None

				try:
					imdb = item['show']['ids']['imdb']
					if imdb == None or imdb == '': imdb = '0'
					else: imdb = 'tt' + re.sub('[^0-9]', '', str(imdb))
					imdb = imdb.encode('utf-8')
				except:
					imdb = '0'

				try:
					tvdb = item['show']['ids']['tvdb']
					#if tvdb == None or tvdb == '': raise Exception()
					tvdb = re.sub('[^0-9]', '', str(tvdb))
					tvdb = tvdb.encode('utf-8')
				except:
					tvdb = '0'

				premiered = item['episode']['first_aired']
				try: premiered = re.compile('(\d{4}-\d{2}-\d{2})').findall(premiered)[0]
				except: premiered = '0'
				premiered = premiered.encode('utf-8')

				try: added = item['show']['updated_at']
				except: added = None

				try: watched = item['show']['last_watched_at']
				except: watched = None

				studio = item['show']['network']
				if studio == None: studio = '0'
				studio = studio.encode('utf-8')

				genre = item['show']['genres']
				genre = [i.title() for i in genre]
				if genre == []: genre = '0'
				genre = ' / '.join(genre)
				genre = genre.encode('utf-8')

				# Gaia
				if 'duration' in item and not item['duration'] == None and not item['duration'] == '':
					duration = item['duration']
				else:
					try: duration = str(item['show']['runtime'])
					except: duration = '0'
					if duration == None: duration = '0'
					duration = duration.encode('utf-8')
				try: duration = str(int(duration) * 60)
				except: pass

				try: rating = str(item['episode']['rating'])
				except: rating = '0'
				if rating == None or rating == '0.0': rating = '0'
				rating = rating.encode('utf-8')

				try: votes = str(item['show']['votes'])
				except: votes = '0'
				try: votes = str(format(int(votes),',d'))
				except: pass
				if votes == None: votes = '0'
				votes = votes.encode('utf-8')

				# Gaia
				if 'mpaa' in item and not item['mpaa'] == None and not item['mpaa'] == '':
					mpaa = item['mpaa']
				else:
					mpaa = item['show']['certification']
					if mpaa == None: mpaa = '0'
					mpaa = mpaa.encode('utf-8')

				try: plot = item['episode']['overview'].encode('utf-8')
				except: plot = '0'
				if plot == None or plot == '': plot = item['show']['overview']
				if plot == None or plot == '': plot = '0'
				plot = client.replaceHTMLCodes(plot)
				plot = plot.encode('utf-8')

				values = {'title': title, 'season': season, 'episode': episode, 'tvshowtitle': tvshowtitle, 'year': year, 'premiered': premiered, 'added' : added, 'watched' : watched, 'status': 'Continuing', 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa, 'plot': plot, 'imdb': imdb, 'tvdb': tvdb, 'poster': '0', 'thumb': '0', 'progress' : progress}

				if not direct: values['action'] = 'episodes'

				if 'airday' in item and not item['airday'] == None and not item['airday'] == '':
					values['airday'] = item['airday']
				if 'airtime' in item and not item['airtime'] == None and not item['airtime'] == '':
					values['airtime'] = item['airtime']
				if 'airzone' in item and not item['airzone'] == None and not item['airzone'] == '':
					values['airzone'] = item['airzone']
				try:
					air = item['show']['airs']
					if not 'airday' in item or item['airday'] == None or item['airday'] == '':
						values['airday'] = air['day'].strip()
					if not 'airtime' in item or item['airtime'] == None or item['airtime'] == '':
						values['airtime'] = air['time'].strip()
					if not 'airzone' in item or item['airzone'] == None or item['airzone'] == '':
						values['airzone'] = air['timezone'].strip()
				except:
					pass

				itemlist.append(values)
				if count: self.seasonCount(itemlist, len(itemlist) - 1)

			except:
				pass

		if count: self.seasonCountWait()
		itemlist = itemlist[::-1]

		return itemlist


	def trakt_progress_list(self, url, user, lang, direct = None):
		from resources.lib.indexers import seasons
		if direct is None: direct = tools.Settings.getBoolean('interface.tvshows.direct')
		self.listNew = []

		try:
			url += '?extended=full'
			result = trakt.getTrakt(url)
			result = json.loads(result)
			items = []
		except:
			return

		for item in result:
			try:
				num_1 = 0
				for i in range(0, len(item['seasons'])): num_1 += len(item['seasons'][i]['episodes'])
				num_2 = int(item['show']['aired_episodes'])
				if num_1 >= num_2: raise Exception()

				season = str(item['seasons'][-1]['number'])
				season = season.encode('utf-8')

				episode = str(item['seasons'][-1]['episodes'][-1]['number'])
				episode = episode.encode('utf-8')

				tvshowtitle = item['show']['title']
				if tvshowtitle == None or tvshowtitle == '': raise Exception()
				tvshowtitle = client.replaceHTMLCodes(tvshowtitle)
				try: tvshowtitle = tvshowtitle.encode('utf-8')
				except: pass

				year = item['show']['year']
				year = re.sub('[^0-9]', '', str(year))
				if int(year) > int(self.datetime.strftime('%Y')): raise Exception()

				imdb = item['show']['ids']['imdb']
				if imdb == None or imdb == '': imdb = '0'
				imdb = imdb.encode('utf-8')

				tvdb = item['show']['ids']['tvdb']
				if tvdb == None or tvdb == '': raise Exception()
				tvdb = re.sub('[^0-9]', '', str(tvdb))
				tvdb = tvdb.encode('utf-8')

				try: added = item['show']['updated_at']
				except: added = None

				try: watched = item['show']['last_watched_at']
				except:
					try: watched = item['last_watched_at']
					except: watched = None

				values = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'year': year, 'snum': season, 'enum': episode, 'added' : added, 'watched' : watched}

				# Gaia
				try:
					air = item['show']['airs']
					values['airday'] = air['day'].strip()
					values['airtime'] = air['time'].strip()
					values['airzone'] = air['timezone'].strip()
					values['duration'] = air['runtime']
					values['mpaa'] = air['certification'].strip()
				except:
					pass

				items.append(values)
			except:
				pass

		try:
			result = trakt.getTrakt(self.hiddenprogress_link)
			result = json.loads(result)
			result = [str(i['show']['ids']['tvdb']) for i in result]

			items = [i for i in items if not i['tvdb'] in result]
		except:
			pass

		def items_list(i):
			try:
				url = self.tvdb_info_link % (i['tvdb'], lang)
				data = urllib2.urlopen(url, timeout=10).read()

				zip = zipfile.ZipFile(StringIO.StringIO(data))
				result = zip.read('%s.xml' % lang)
				artwork = zip.read('banners.xml')
				zip.close()

				result = result.split('<Episode>')
				item = [x for x in result if '<EpisodeNumber>' in x]
				item2 = result[0]

				num = [x for x,y in enumerate(item) if re.compile('<SeasonNumber>(.+?)</SeasonNumber>').findall(y)[0] == str(i['snum']) and re.compile('<EpisodeNumber>(.+?)</EpisodeNumber>').findall(y)[0] == str(i['enum'])][-1]
				item = [y for x,y in enumerate(item) if x > num][0]

				premiered = client.parseDOM(item, 'FirstAired')[0]
				if premiered == '' or '-00' in premiered: premiered = '0'
				premiered = client.replaceHTMLCodes(premiered)
				premiered = premiered.encode('utf-8')

				try: added = i['added']
				except: added = None

				try: watched = i['watched']
				except: watched = None

				try: status = client.parseDOM(item2, 'Status')[0]
				except: status = ''
				if status == '': status = 'Ended'
				status = client.replaceHTMLCodes(status)
				status = status.encode('utf-8')

				if status == 'Ended': pass
				elif premiered == '0': raise Exception()
				#elif int(re.sub('[^0-9]', '', str(premiered))) > int(re.sub('[^0-9]', '', str(self.today_date))): raise Exception()
				elif not tools.Settings.getBoolean('interface.tvshows.future.episodes'):
					if int(re.sub('[^0-9]', '', str(premiered))) > int(re.sub('[^0-9]', '', str(self.today_date))): raise Exception()

				title = client.parseDOM(item, 'EpisodeName')[0]
				if title == '': title = '0'
				title = client.replaceHTMLCodes(title)
				try: title = title.encode('utf-8')
				except: pass

				season = client.parseDOM(item, 'SeasonNumber')[0]
				season = '%01d' % int(season)
				season = season.encode('utf-8')

				episode = client.parseDOM(item, 'EpisodeNumber')[0]
				episode = re.sub('[^0-9]', '', '%01d' % int(episode))
				episode = episode.encode('utf-8')

				seasoncount = seasons.seasons.seasonCountParse(season = season, items = result)

				tvshowtitle = i['tvshowtitle']
				imdb, tvdb = i['imdb'], i['tvdb']

				year = i['year']
				try: year = year.encode('utf-8')
				except: pass

				tvshowyear = i['year']
				try: tvshowyear = i['tvshowyear']
				except: pass
				try: tvshowyear = tvshowyear.encode('utf-8')
				except: pass

				try: poster = client.parseDOM(item2, 'poster')[0]
				except: poster = ''
				if not poster == '': poster = self.tvdb_image + poster
				else: poster = '0'
				poster = client.replaceHTMLCodes(poster)
				poster = poster.encode('utf-8')

				try: banner = client.parseDOM(item2, 'banner')[0]
				except: banner = ''
				if not banner == '': banner = self.tvdb_image + banner
				else: banner = '0'
				banner = client.replaceHTMLCodes(banner)
				banner = banner.encode('utf-8')

				try: fanart = client.parseDOM(item2, 'fanart')[0]
				except: fanart = ''
				if not fanart == '': fanart = self.tvdb_image + fanart
				else: fanart = '0'
				fanart = client.replaceHTMLCodes(fanart)
				fanart = fanart.encode('utf-8')

				try: thumb = client.parseDOM(item, 'filename')[0]
				except: thumb = ''
				if not thumb == '': thumb = self.tvdb_image + thumb
				else: thumb = '0'
				thumb = client.replaceHTMLCodes(thumb)
				thumb = thumb.encode('utf-8')

				if not poster == '0': pass
				elif not fanart == '0': poster = fanart
				elif not banner == '0': poster = banner

				if not banner == '0': pass
				elif not fanart == '0': banner = fanart
				elif not poster == '0': banner = poster

				if not thumb == '0': pass
				elif not fanart == '0': thumb = fanart.replace(self.tvdb_image, self.tvdb_poster)
				elif not poster == '0': thumb = poster

				try: studio = client.parseDOM(item2, 'Network')[0]
				except: studio = ''
				if studio == '': studio = '0'
				studio = client.replaceHTMLCodes(studio)
				studio = studio.encode('utf-8')

				try: genre = client.parseDOM(item2, 'Genre')[0]
				except: genre = ''
				genre = [x for x in genre.split('|') if not x == '']
				genre = ' / '.join(genre)
				if genre == '': genre = '0'
				genre = client.replaceHTMLCodes(genre)
				genre = genre.encode('utf-8')

				# Gaia
				if 'duration' in i and not i['duration'] == None and not i['duration'] == '':
					duration = i['duration']
				else:
					try: duration = client.parseDOM(item2, 'Runtime')[0]
					except: duration = ''
					if duration == '': duration = '0'
					duration = client.replaceHTMLCodes(duration)
					duration = duration.encode('utf-8')
				try: duration = str(int(duration) * 60)
				except: pass

				try: rating = client.parseDOM(item, 'Rating')[0]
				except: rating = ''
				if rating == '': rating = '0'
				rating = client.replaceHTMLCodes(rating)
				rating = rating.encode('utf-8')

				try: votes = client.parseDOM(item2, 'RatingCount')[0]
				except: votes = '0'
				if votes == '': votes = '0'
				votes = client.replaceHTMLCodes(votes)
				votes = votes.encode('utf-8')

				# Gaia
				if 'mpaa' in i and not i['mpaa'] == None and not i['mpaa'] == '':
					mpaa = i['mpaa']
				else:
					try: mpaa = client.parseDOM(item2, 'ContentRating')[0]
					except: mpaa = ''
					if mpaa == '': mpaa = '0'
					mpaa = client.replaceHTMLCodes(mpaa)
					mpaa = mpaa.encode('utf-8')

				try: director = client.parseDOM(item, 'Director')[0]
				except: director = ''
				director = [x for x in director.split('|') if not x == '']
				director = ' / '.join(director)
				if director == '': director = '0'
				director = client.replaceHTMLCodes(director)
				director = director.encode('utf-8')

				try: writer = client.parseDOM(item, 'Writer')[0]
				except: writer = ''
				writer = [x for x in writer.split('|') if not x == '']
				writer = ' / '.join(writer)
				if writer == '': writer = '0'
				writer = client.replaceHTMLCodes(writer)
				writer = writer.encode('utf-8')

				try: cast = client.parseDOM(item2, 'Actors')[0]
				except: cast = ''
				cast = [x for x in cast.split('|') if not x == '']
				try: cast = [(x.encode('utf-8'), '') for x in cast]
				except: cast = []

				try: plot = client.parseDOM(item, 'Overview')[0]
				except: plot = ''
				if plot == '':
					try: plot = client.parseDOM(item2, 'Overview')[0]
					except: plot = ''
				if plot == '': plot = '0'
				plot = client.replaceHTMLCodes(plot)
				plot = plot.encode('utf-8')

				values = {'title': title, 'seasoncount' : seasoncount, 'season': season, 'episode': episode, 'year': year, 'tvshowtitle': tvshowtitle, 'tvshowyear': tvshowyear, 'premiered': premiered, 'added' : added, 'watched' : watched, 'status': status, 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa, 'director': director, 'writer': writer, 'cast': cast, 'plot': plot, 'imdb': imdb, 'tvdb': tvdb, 'poster': poster, 'banner': banner, 'fanart': fanart, 'thumb': thumb, 'snum': i['snum'], 'enum': i['enum']}

				if not direct: values['action'] = 'episodes'

				if 'airday' in i and not i['airday'] == None and not i['airday'] == '':
					values['airday'] = i['airday']
				if 'airtime' in i and not i['airtime'] == None and not i['airtime'] == '':
					values['airtime'] = i['airtime']
				if 'airzone' in i and not i['airzone'] == None and not i['airzone'] == '':
					values['airzone'] = i['airzone']

				self.listNew.append(values)
			except:
				pass


		items = items[:100]

		threads = []
		for i in items: threads.append(workers.Thread(items_list, i))
		[i.start() for i in threads]
		[i.join() for i in threads]

		return self.listNew


	def trakt_episodes_list(self, url, user, lang, direct = False):
		from resources.lib.indexers import seasons

		self.listNew = []
		items = self.trakt_list(url, user)
		def items_list(i):
			try:
				url = self.tvdb_info_link % (i['tvdb'], lang)
				data = urllib2.urlopen(url, timeout=10).read()

				zip = zipfile.ZipFile(StringIO.StringIO(data))
				result = zip.read('%s.xml' % lang)
				artwork = zip.read('banners.xml')
				zip.close()

				result = result.split('<Episode>')
				item = [(re.findall('<SeasonNumber>%01d</SeasonNumber>' % int(i['season']), x), re.findall('<EpisodeNumber>%01d</EpisodeNumber>' % int(i['episode']), x), x) for x in result]
				item = [x[2] for x in item if len(x[0]) > 0 and len(x[1]) > 0][0]
				item2 = result[0]

				premiered = client.parseDOM(item, 'FirstAired')[0]
				if premiered == '' or '-00' in premiered: premiered = '0'
				premiered = client.replaceHTMLCodes(premiered)
				premiered = premiered.encode('utf-8')

				try: status = client.parseDOM(item2, 'Status')[0]
				except: status = ''
				if status == '': status = 'Ended'
				status = client.replaceHTMLCodes(status)
				status = status.encode('utf-8')

				title = client.parseDOM(item, 'EpisodeName')[0]
				if title == '': title = '0'
				title = client.replaceHTMLCodes(title)
				try: title = title.encode('utf-8')
				except: pass

				season = client.parseDOM(item, 'SeasonNumber')[0]
				season = '%01d' % int(season)
				season = season.encode('utf-8')

				episode = client.parseDOM(item, 'EpisodeNumber')[0]
				episode = re.sub('[^0-9]', '', '%01d' % int(episode))
				episode = episode.encode('utf-8')

				seasoncount = seasons.seasons.seasonCountParse(season = season, items = result)

				tvshowtitle = i['tvshowtitle']
				imdb, tvdb = i['imdb'], i['tvdb']

				year = i['year']
				try: year = year.encode('utf-8')
				except: pass

				tvshowyear = i['year']
				try: tvshowyear = i['tvshowyear']
				except: pass
				try: tvshowyear = tvshowyear.encode('utf-8')
				except: pass

				try: poster = client.parseDOM(item2, 'poster')[0]
				except: poster = ''
				if not poster == '': poster = self.tvdb_image + poster
				else: poster = '0'
				poster = client.replaceHTMLCodes(poster)
				poster = poster.encode('utf-8')

				try: banner = client.parseDOM(item2, 'banner')[0]
				except: banner = ''
				if not banner == '': banner = self.tvdb_image + banner
				else: banner = '0'
				banner = client.replaceHTMLCodes(banner)
				banner = banner.encode('utf-8')

				try: fanart = client.parseDOM(item2, 'fanart')[0]
				except: fanart = ''
				if not fanart == '': fanart = self.tvdb_image + fanart
				else: fanart = '0'
				fanart = client.replaceHTMLCodes(fanart)
				fanart = fanart.encode('utf-8')

				try: thumb = client.parseDOM(item, 'filename')[0]
				except: thumb = ''
				if not thumb == '': thumb = self.tvdb_image + thumb
				else: thumb = '0'
				thumb = client.replaceHTMLCodes(thumb)
				thumb = thumb.encode('utf-8')

				if not poster == '0': pass
				elif not fanart == '0': poster = fanart
				elif not banner == '0': poster = banner

				if not banner == '0': pass
				elif not fanart == '0': banner = fanart
				elif not poster == '0': banner = poster

				if not thumb == '0': pass
				elif not fanart == '0': thumb = fanart.replace(self.tvdb_image, self.tvdb_poster)
				elif not poster == '0': thumb = poster

				try: studio = client.parseDOM(item2, 'Network')[0]
				except: studio = ''
				if studio == '': studio = '0'
				studio = client.replaceHTMLCodes(studio)
				studio = studio.encode('utf-8')

				try: genre = client.parseDOM(item2, 'Genre')[0]
				except: genre = ''
				genre = [x for x in genre.split('|') if not x == '']
				genre = ' / '.join(genre)
				if genre == '': genre = '0'
				genre = client.replaceHTMLCodes(genre)
				genre = genre.encode('utf-8')

				if 'duration' in i and not i['duration'] == None and not i['duration'] == '':
					duration = i['duration']
				else:
					try: duration = client.parseDOM(item2, 'Runtime')[0]
					except: duration = ''
					if duration == '': duration = '0'
					duration = client.replaceHTMLCodes(duration)
					duration = duration.encode('utf-8')
				try: duration = str(int(duration) * 60)
				except: pass

				try: rating = client.parseDOM(item, 'Rating')[0]
				except: rating = ''
				if rating == '': rating = '0'
				rating = client.replaceHTMLCodes(rating)
				rating = rating.encode('utf-8')

				try: votes = client.parseDOM(item2, 'RatingCount')[0]
				except: votes = '0'
				if votes == '': votes = '0'
				votes = client.replaceHTMLCodes(votes)
				votes = votes.encode('utf-8')

				if 'mpaa' in i and not i['mpaa'] == None and not i['mpaa'] == '':
					mpaa = i['mpaa']
				else:
					try: mpaa = client.parseDOM(item2, 'ContentRating')[0]
					except: mpaa = ''
					if mpaa == '': mpaa = '0'
					mpaa = client.replaceHTMLCodes(mpaa)
					mpaa = mpaa.encode('utf-8')

				try: director = client.parseDOM(item, 'Director')[0]
				except: director = ''
				director = [x for x in director.split('|') if not x == '']
				director = ' / '.join(director)
				if director == '': director = '0'
				director = client.replaceHTMLCodes(director)
				director = director.encode('utf-8')

				try: writer = client.parseDOM(item, 'Writer')[0]
				except: writer = ''
				writer = [x for x in writer.split('|') if not x == '']
				writer = ' / '.join(writer)
				if writer == '': writer = '0'
				writer = client.replaceHTMLCodes(writer)
				writer = writer.encode('utf-8')

				try: cast = client.parseDOM(item2, 'Actors')[0]
				except: cast = ''
				cast = [x for x in cast.split('|') if not x == '']
				try: cast = [(x.encode('utf-8'), '') for x in cast]
				except: cast = []

				try: plot = client.parseDOM(item, 'Overview')[0]
				except: plot = ''
				if plot == '':
					try: plot = client.parseDOM(item2, 'Overview')[0]
					except: plot = ''
				if plot == '': plot = '0'
				plot = client.replaceHTMLCodes(plot)
				plot = plot.encode('utf-8')

				values = {'title': title, 'seasoncount' : seasoncount, 'season': season, 'episode': episode, 'year': year, 'tvshowtitle': tvshowtitle, 'tvshowyear': tvshowyear, 'premiered': premiered, 'status': status, 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa, 'director': director, 'writer': writer, 'cast': cast, 'plot': plot, 'imdb': imdb, 'tvdb': tvdb, 'poster': poster, 'banner': banner, 'fanart': fanart, 'thumb': thumb}

				if not direct: values['action'] = 'episodes'

				if 'airday' in i and not i['airday'] == None and not i['airday'] == '':
					values['airday'] = i['airday']
				if 'airtime' in i and not i['airtime'] == None and not i['airtime'] == '':
					values['airtime'] = i['airtime']
				if 'airzone' in i and not i['airzone'] == None and not i['airzone'] == '':
					values['airzone'] = i['airzone']
				try:
					air = i['show']['airs']
					if not 'airday' in i or i['airday'] == None or i['airday'] == '':
						values['airday'] = air['day'].strip()
					if not 'airtime' in i or i['airtime'] == None or i['airtime'] == '':
						values['airtime'] = air['time'].strip()
					if not 'airzone' in i or i['airzone'] == None or i['airzone'] == '':
						values['airzone'] = air['timezone'].strip()
				except:
					pass

				self.listNew.append(values)
			except:
				pass

		items = items[:100]

		threads = []
		for i in items: threads.append(workers.Thread(items_list, i))
		[i.start() for i in threads]
		[i.join() for i in threads]

		return self.listNew


	def trakt_user_list(self, url, user):
		list = []

		try:
			result = trakt.getTrakt(url)
			items = json.loads(result)
		except:
			pass

		for item in items:
			try:
				try: name = item['list']['name']
				except: name = item['name']
				name = client.replaceHTMLCodes(name)
				name = name.encode('utf-8')

				try: url = (trakt.slug(item['list']['user']['username']), item['list']['ids']['slug'])
				except: url = ('me', item['ids']['slug'])
				url = self.traktlist_link % url
				url = url.encode('utf-8')

				list.append({'name': name, 'url': url})
			except:
				pass

		list = sorted(list, key=lambda k: re.sub('(^the |^a |^an )', '', k['name'].lower()))
		return list


	def tvmaze_list(self, url, limit, count = True, direct = False):
		try:
			result = client.request(url)
			itemlist = []
			items = json.loads(result)
		except:
			return

		for item in items:
			try:
				if not 'english' in item['show']['language'].lower(): raise Exception()

				if limit == True and not 'scripted' in item['show']['type'].lower(): raise Exception()

				title = item['name']
				if title == None or title == '': raise Exception()
				title = client.replaceHTMLCodes(title)
				try: title = title.encode('utf-8')
				except: pass

				season = item['season']
				season = re.sub('[^0-9]', '', '%01d' % int(season))
				if season == '0': raise Exception()
				season = season.encode('utf-8')

				episode = item['number']
				episode = re.sub('[^0-9]', '', '%01d' % int(episode))
				if episode == '0': raise Exception()
				episode = episode.encode('utf-8')

				year = item['show']['premiered']
				year = re.findall('(\d{4})', year)[0]
				year = year.encode('utf-8')

				tvshowtitle = item['show']['name']
				if tvshowtitle == None or tvshowtitle == '': raise Exception()
				tvshowtitle = client.replaceHTMLCodes(tvshowtitle)
				try: tvshowtitle = tvshowtitle.encode('utf-8')
				except: pass

				try: tvshowyear = item['show']['year']
				except: tvshowyear = year

				imdb = item['show']['externals']['imdb']
				if imdb == None or imdb == '': imdb = '0'
				else: imdb = 'tt' + re.sub('[^0-9]', '', str(imdb))
				imdb = imdb.encode('utf-8')

				tvdb = item['show']['externals']['thetvdb']
				if tvdb == None or tvdb == '': raise Exception()
				tvdb = re.sub('[^0-9]', '', str(tvdb))
				tvdb = tvdb.encode('utf-8')

				poster = '0'
				try: poster = item['show']['image']['original']
				except: poster = '0'
				if poster == None or poster == '': poster = '0'
				poster = poster.encode('utf-8')

				try: thumb1 = item['show']['image']['original']
				except: thumb1 = '0'
				try: thumb2 = item['image']['original']
				except: thumb2 = '0'
				if thumb2 == None or thumb2 == '0': thumb = thumb1
				else: thumb = thumb2
				if thumb == None or thumb == '': thumb = '0'
				thumb = thumb.encode('utf-8')

				premiered = item['airdate']
				try: premiered = re.findall('(\d{4}-\d{2}-\d{2})', premiered)[0]
				except: premiered = '0'
				premiered = premiered.encode('utf-8')

				try: studio = item['show']['network']['name']
				except: studio = '0'
				if studio == None: studio = '0'
				studio = studio.encode('utf-8')

				try: genre = item['show']['genres']
				except: genre = '0'
				genre = [i.title() for i in genre]
				if genre == []: genre = '0'
				genre = ' / '.join(genre)
				genre = genre.encode('utf-8')

				# Gaia
				if 'duration' in item and not item['duration'] == None and not item['duration'] == '':
					duration = item['duration']
				else:
					try: duration = item['show']['runtime']
					except: duration = '0'
					if duration == None: duration = '0'
					duration = str(duration)
					duration = duration.encode('utf-8')
				try: duration = str(int(duration) * 60)
				except: pass

				try: rating = item['show']['rating']['average']
				except: rating = '0'
				if rating == None or rating == '0.0': rating = '0'
				rating = str(rating)
				rating = rating.encode('utf-8')

				try: plot = item['show']['summary']
				except: plot = '0'
				if plot == None: plot = '0'
				plot = re.sub('<.+?>|</.+?>|\n', '', plot)
				plot = client.replaceHTMLCodes(plot)
				plot = plot.encode('utf-8')

				values = {'title': title, 'season': season, 'episode': episode, 'year': year, 'tvshowtitle': tvshowtitle, 'tvshowyear': tvshowyear, 'premiered': premiered, 'status': 'Continuing', 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating, 'plot': plot, 'imdb': imdb, 'tvdb': tvdb, 'poster': poster, 'thumb': thumb}

				if not direct: values['action'] = 'episodes'

				if 'airday' in item and not item['airday'] == None and not item['airday'] == '':
					values['airday'] = item['airday']
				if 'airtime' in item and not item['airtime'] == None and not item['airtime'] == '':
					values['airtime'] = item['airtime']
				if 'airzone' in item and not item['airzone'] == None and not item['airzone'] == '':
					values['airzone'] = item['airzone']
				try:
					air = item['show']['airs']
					if not 'airday' in item or item['airday'] == None or item['airday'] == '':
						values['airday'] = air['day'].strip()
					if not 'airtime' in item or item['airtime'] == None or item['airtime'] == '':
						values['airtime'] = air['time'].strip()
					if not 'airzone' in item or item['airzone'] == None or item['airzone'] == '':
						values['airzone'] = air['timezone'].strip()
				except:
					pass

				itemlist.append(values)
				if count: self.seasonCount(itemlist, len(itemlist) - 1)
			except:
				pass

		if count: self.seasonCountWait()
		itemlist = itemlist[::-1]

		return itemlist


	def context(self, tvshowtitle, title, year, imdb, tvdb, season, episode):
		from resources.lib.indexers import tvshows
		metadata = tvshows.tvshows(type = self.type, kids = self.kids).metadata(tvshowtitle = tvshowtitle, title = title, year = year, imdb = imdb, tvdb = tvdb, season = season, episode = episode)

		addon = tools.System.plugin()
		addonPoster, addonBanner = control.addonPoster(), control.addonBanner()
		addonFanart, settingFanart = control.addonFanart(), tools.Settings.getBoolean('interface.theme.fanart')

		indicators = playcount.getShowIndicators()
		ratingsOwn = tools.Settings.getInteger('interface.ratings.type') == 1

		imdb, tvdb, year, season, episode, premiered = metadata['imdb'], metadata['tvdb'], metadata['year'], metadata['season'], metadata['episode'], metadata['premiered']
		title = metadata['tvshowtitle']
		if not 'label' in metadata: metadata['label'] = metadata['title']
		if metadata['tvshowtitle'] == metadata['label'] or metadata['label'] == None or metadata['label'] == '' or metadata['label'] == '0': metadata['label'] = '%s %d' % (tools.Media.NameEpisodeLong, int(episode))
		label = None
		try: label = tools.Media().title(tools.Media.TypeEpisode, title = metadata['label'], season = season, episode = episode)
		except: pass
		if label == None: label = metadata['label']

		trailer = '%s Season %s' % (title, str(season))

		try: seasoncount = metadata['seasoncount']
		except: seasoncount = None

		# Allow special episodes with season = '0' or episode = '0'
		#meta = dict((k,v) for k, v in i.iteritems() if not v == '0')
		meta = dict((k,v) for k, v in metadata.iteritems())
		meta.update({'mediatype': 'episode', 'episode' : episode})
		meta.update({'code': imdb, 'imdbnumber': imdb, 'imdb_id': imdb, 'tvdb_id': tvdb})

		# Remove default time, since this might mislead users. Rather show no time.
		#if not 'duration' in i: meta.update({'duration': '60'})
		#elif metadata['duration'] == '0': meta.update({'duration': '60'})

		# Some descriptions have a link at the end that. Remove it.
		try:
			plot = meta['plot']
			index = plot.rfind('See full summary')
			if index >= 0: plot = plot[:index]
			plot = plot.strip()
			if re.match('[a-zA-Z\d]$', plot): plot += ' ...'
			meta['plot'] = plot
		except: pass

		try: meta.update({'duration': int(meta['duration'])})
		except: pass
		try: meta.update({'genre': cleangenre.lang(meta['genre'], self.lang)})
		except: pass
		try: meta.update({'title': metadata['label']})
		except: pass
		try: meta.update({'year': date.year}) # Kodi uses the year (the year the show started) as the year for the episode. Change it from the premiered date.
		except: pass
		try:
			if not 'tvshowyear' in meta: meta.update({'tvshowyear': year}) # Kodi uses the year (the year the show started) as the year for the episode. Change it from the premiered date.
		except: pass

		if ratingsOwn and 'ratingown' in meta and not meta['ratingown'] == '0':
			meta['rating'] = meta['ratingown']

		watched = int(playcount.getEpisodeOverlay(indicators, imdb, tvdb, season, episode)) == 7
		if watched: meta.update({'playcount': 1, 'overlay': 7})
		else: meta.update({'playcount': 0, 'overlay': 6})
		meta.update({'watched': int(watched)}) # Kodi's documentation says this value is deprecate. However, without this value, Kodi adds the watched checkmark over the remaining episode count.

		poster = '0'
		if poster == '0' and 'poster3' in metadata: poster = metadata['poster3']
		if poster == '0' and 'poster2' in metadata: poster = metadata['poster2']
		if poster == '0' and 'poster' in metadata: poster = metadata['poster']

		icon = '0'
		if icon == '0' and 'icon3' in metadata: icon = metadata['icon3']
		if icon == '0' and 'icon2' in metadata: icon = metadata['icon2']
		if icon == '0' and 'icon' in metadata: icon = metadata['icon']

		thumb = '0'
		if thumb == '0' and 'thumb3' in metadata: thumb = metadata['thumb3']
		if thumb == '0' and 'thumb2' in metadata: thumb = metadata['thumb2']
		if thumb == '0' and 'thumb' in metadata: thumb = metadata['thumb']

		banner = '0'
		if banner == '0' and 'banner3' in metadata: banner = metadata['banner3']
		if banner == '0' and 'banner2' in metadata: banner = metadata['banner2']
		if banner == '0' and 'banner' in metadata: banner = metadata['banner']

		fanart = '0'
		if settingFanart:
			if fanart == '0' and 'fanart3' in metadata: fanart = metadata['fanart3']
			if fanart == '0' and 'fanart2' in metadata: fanart = metadata['fanart2']
			if fanart == '0' and 'fanart' in metadata: fanart = metadata['fanart']

		clearlogo = '0'
		if clearlogo == '0' and 'clearlogo' in metadata: clearlogo = metadata['clearlogo']

		clearart = '0'
		if clearart == '0' and 'clearart' in metadata: clearart = metadata['clearart']

		landscape = '0'
		if landscape == '0' and 'landscape' in metadata: landscape = metadata['landscape']

		if poster == '0': poster = addonPoster
		if icon == '0': icon = poster
		if thumb == '0': thumb = poster
		if banner == '0': banner = addonBanner
		if fanart == '0': fanart = addonFanart

		art = {}
		if not poster == '0' and not poster == None: art.update({'poster' : poster, 'tvshow.poster' : poster, 'season.poster' : poster})
		if not icon == '0' and not icon == None: art.update({'icon' : icon})
		if not thumb == '0' and not thumb == None: art.update({'thumb' : thumb})
		if not banner == '0' and not banner == None: art.update({'banner' : banner})
		if not clearlogo == '0' and not clearlogo == None: art.update({'clearlogo' : clearlogo})
		if not clearart == '0' and not clearart == None: art.update({'clearart' : clearart})
		if not fanart == '0' and not fanart == None: art.update({'fanart' : fanart})
		if not landscape == '0' and not landscape == None: art.update({'landscape' : landscape})

		meta.update({'trailer': '%s?action=streamsTrailer&title=%s&imdb=%s&art=%s' % (addon, urllib.quote_plus(trailer), imdb, urllib.quote_plus(json.dumps(art)))})
		link = self.parameterize('%s?action=scrape&title=%s&year=%s&imdb=%s&tvdb=%s&season=%s&episode=%s&tvshowtitle=%s&premiered=%s&metadata=%s%s' % (addon, urllib.quote_plus(metadata['title']), year, imdb, tvdb, season, episode, urllib.quote_plus(title), urllib.quote_plus(premiered), urllib.quote_plus(json.dumps(meta)), '' if seasoncount == None else ('&seasoncount=%d' % seasoncount)))

		return interface.Context(mode = interface.Context.ModeItem, type = self.type, kids = self.kids, create = True, watched = watched, season = season, episode = episode, metadata = meta, art = art, label = label, link = link, trailer = trailer, title = title, year = year, imdb = imdb, tvdb = tvdb).menu()[1]

	def episodeDirectory(self, items, multi = None, unfinished = False):

		# Retrieve additional metadata if not super info was retireved (eg: Trakt lists, such as Unfinished and History)
		try:
			if not 'extended' in items[0] or not items[0]['extended']:
				from resources.lib.indexers import tvshows
				show = tvshows.tvshows(type = self.type, kids = self.kids)
				show.list = copy.deepcopy(self.list)
				show.worker()
				for i in range(len(self.list)):
					self.list[i] = dict(show.list[i].items() + self.list[i].items())
		except:
			pass

		if isinstance(items, dict) and 'value' in items:
			items = items['value']
		if isinstance(items, basestring):
			try: items = tools.Converter.jsonFrom(items)
			except: pass

		if items == None or len(items) == 0:
			interface.Loader.hide()
			interface.Dialog.notification(title = 32326, message = 33049, icon = interface.Dialog.IconInformation)
			sys.exit()

		sysaddon = sys.argv[0]
		syshandle = int(sys.argv[1])
		media = tools.Media()

		addonPoster, addonBanner = control.addonPoster(), control.addonBanner()
		addonFanart, settingFanart = control.addonFanart(), tools.Settings.getBoolean('interface.theme.fanart')

		indicators = playcount.getShowIndicators()

		# Different variable to multi.
		# "multiple" handles the title format and the directory type.
		# "multi" is used to avoid the watched mark being shown on top of the unwarched episode count.
		try: multiple = [i['tvshowtitle'] for i in items]
		except: multiple = []
		multiple = len([x for y,x in enumerate(multiple) if x not in multiple[:y]])
		multiple = True if multiple > 1 else False

		try: sysaction = items[0]['action']
		except: sysaction = ''
		isFolder = True if sysaction == 'episodes' else False
		isPlayable = 'true' if not 'plugin' in control.infoLabel('Container.PluginName') else 'false'
		ratingsOwn = tools.Settings.getInteger('interface.ratings.type') == 1
		unwatchedEnabled = tools.Settings.getBoolean('interface.tvshows.unwatched.enabled')
		unwatchedLimit = tools.Settings.getBoolean('interface.tvshows.unwatched.limit')
		futureEpisode = tools.Settings.getBoolean('interface.tvshows.future.episodes')
		context = interface.Context.enabled()

		airEnabled = tools.Settings.getBoolean('interface.tvshows.air.enabled')
		if airEnabled:
			airZone = tools.Settings.getInteger('interface.tvshows.air.zone')
			airLocation = tools.Settings.getInteger('interface.tvshows.air.location')
			airFormat = tools.Settings.getInteger('interface.tvshows.air.format')
			airFormatDay = tools.Settings.getInteger('interface.tvshows.air.day')
			airFormatTime = tools.Settings.getInteger('interface.tvshows.air.time')
			airBold = tools.Settings.getBoolean('interface.tvshows.air.bold')
			airLabel = interface.Format.bold(interface.Translation.string(35032) + ': ')

		for i in items:
			try:
				imdb, tvdb, year, season, episode, premiered = i['imdb'], i['tvdb'], i['year'], i['season'], i['episode'], i['premiered']
				title = i['tvshowtitle']
				if not 'label' in i: i['label'] = i['title']
				if i['tvshowtitle'] == i['label'] or i['label'] == None or i['label'] == '' or i['label'] == '0': i['label'] = '%s %d' % (tools.Media.NameEpisodeLong, int(episode))
				label = None
				try: label = media.title(tools.Media.TypeEpisode, title = i['label'], season = season, episode = episode)
				except: pass
				if label == None: label = i['label']
				if multiple == True and not label in title and not title in label: label = '%s - %s' % (title, label)
				try: labelProgress = label + ' [' + str(int(i['progress'] * 100)) + '%]'
				except: labelProgress = label

				trailer = '%s Season %s' % (title, str(season))

				systitle = urllib.quote_plus(i['title'])
				systvshowtitle = urllib.quote_plus(title)
				syspremiered = urllib.quote_plus(premiered)

				try: seasoncount = i['seasoncount']
				except: seasoncount = None

				# Make new episodes italic.
				if not futureEpisode and syspremiered and int(re.sub('[^0-9]', '', str(syspremiered))) > int(re.sub('[^0-9]', '', str(self.today_date))): continue
				try: # Special episodes without a premiered date.
					date = tools.Time.datetime(premiered, format = '%Y-%m-%d')
					current = datetime.datetime.now()
					if current <= date or current.date() == date.date():
						labelProgress = '[I]' + labelProgress + '[/I]'
						if (date - current) > datetime.timedelta(days = 1):
							labelProgress = '[LIGHT]' + labelProgress + '[/LIGHT]'
				except: pass

				# Allow special episodes with season = '0' or episode = '0'
				#meta = dict((k,v) for k, v in i.iteritems() if not v == '0')
				meta = dict((k,v) for k, v in i.iteritems())
				meta.update({'mediatype': 'episode', 'season' : season, 'episode' : episode})
				meta.update({'code': imdb, 'imdbnumber': imdb, 'imdb_id': imdb, 'tvdb_id': tvdb})

				# Gaia
				# Remove default time, since this might mislead users. Rather show no time.
				#if not 'duration' in i: meta.update({'duration': '60'})
				#elif i['duration'] == '0': meta.update({'duration': '60'})

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

				try: meta.update({'duration': int(meta['duration'])})
				except: pass
				try: meta.update({'genre': cleangenre.lang(meta['genre'], self.lang)})
				except: pass
				try: meta.update({'title': i['label']})
				except: pass
				try: meta.update({'year': date.year}) # Kodi uses the year (the year the show started) as the year for the episode. Change it from the premiered date.
				except: pass
				try:
					if not 'tvshowyear' in meta: meta.update({'tvshowyear': year}) # Kodi uses the year (the year the show started) as the year for the episode. Change it from the premiered date.
				except: pass

				if airEnabled:
					air = []
					airday = None
					airtime = None
					if 'airday' in meta and not meta['airday'] == None and not meta['airday'] == '':
						airday = meta['airday']
					if 'airtime' in meta and not meta['airtime'] == None and not meta['airtime'] == '':
						airtime = meta['airtime']
						if 'airzone' in meta and not meta['airzone'] == None and not meta['airzone'] == '':
							if airZone == 1: zoneTo = meta['airzone']
							elif airZone == 2: zoneTo = tools.Time.ZoneUtc
							else: zoneTo = tools.Time.ZoneLocal

							if airFormatTime == 1: formatOutput = '%I:%M'
							elif airFormatTime == 2: formatOutput = '%I:%M %p'
							else: formatOutput = '%H:%M'

							abbreviate = airFormatDay == 1
							airtime = tools.Time.convert(stringTime = airtime, stringDay = airday, zoneFrom = meta['airzone'], zoneTo = zoneTo, abbreviate = abbreviate, formatOutput = formatOutput)
							if airday:
								airday = airtime[1]
								airtime = airtime[0]
					if airday: air.append(airday)
					if airtime: air.append(airtime)
					if len(air) > 0:
						if airFormat == 0: air = airtime
						elif airFormat == 1: air = airday
						elif airFormat == 2: air = air = ' '.join(air)

						if airLocation == 0 or airLocation == 1:
							air = '[%s]' % air

						if airBold: air = interface.Format.bold(air)

						if airLocation == 0: labelProgress = '%s %s' % (air, labelProgress)
						elif airLocation == 1: labelProgress = '%s %s' % (labelProgress, air)
						elif airLocation == 2: meta['plot'] = '%s%s\r\n%s' % (airLabel, air, meta['plot'])
						elif airLocation == 3: meta['plot'] = '%s\r\n%s%s' % (meta['plot'], airLabel, air)

				if ratingsOwn and 'ratingown' in meta and not meta['ratingown'] == '0':
					meta['rating'] = meta['ratingown']

				item = control.item(label = labelProgress)

				try:
					overlay = int(playcount.getEpisodeOverlay(indicators, imdb, tvdb, season, episode))
					watched = overlay == 7

					# Skip episodes marked as watched for the unfinished list.
					try:
						if unfinished and watched and not i['progress'] is None: continue
					except: pass

					if watched: meta.update({'playcount': 1, 'overlay': 7})
					else: meta.update({'playcount': 0, 'overlay': 6})
					meta.update({'watched': int(watched)}) # Kodi's documentation says this value is deprecate. However, without this value, Kodi adds the watched checkmark over the remaining episode count.
					if multi and unwatchedEnabled:
						count = playcount.getShowCount(indicators, imdb, tvdb, unwatchedLimit)
						if count:
							item.setProperty('TotalEpisodes', str(count['total']))
							item.setProperty('WatchedEpisodes', str(count['watched']))
							item.setProperty('UnWatchedEpisodes', str(count['unwatched']))
				except: pass

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

				landscape = '0'
				if landscape == '0' and 'landscape' in i: landscape = i['landscape']

				if poster == '0': poster = addonPoster
				if icon == '0': icon = poster
				if thumb == '0': thumb = poster
				if banner == '0': banner = addonBanner
				if fanart == '0': fanart = addonFanart

				art = {}
				if not poster == '0' and not poster == None: art.update({'poster' : poster, 'tvshow.poster' : poster, 'season.poster' : poster})
				if not icon == '0' and not icon == None: art.update({'icon' : icon})
				if not thumb == '0' and not thumb == None: art.update({'thumb' : thumb})
				if not banner == '0' and not banner == None: art.update({'banner' : banner})
				if not clearlogo == '0' and not clearlogo == None: art.update({'clearlogo' : clearlogo})
				if not clearart == '0' and not clearart == None: art.update({'clearart' : clearart})
				if not fanart == '0' and not fanart == None: art.update({'fanart' : fanart})
				if not landscape == '0' and not landscape == None: art.update({'landscape' : landscape})

				meta.update({'trailer': '%s?action=streamsTrailer&title=%s&imdb=%s&art=%s' % (sysaddon, urllib.quote_plus(trailer), imdb, urllib.quote_plus(json.dumps(art)))})
				if isFolder: url = self.parameterize('%s?action=episodesRetrieve&tvshowtitle=%s&year=%s&imdb=%s&tvdb=%s&season=%s&episode=%s&metadata=%s' % (sysaddon, systvshowtitle, year, imdb, tvdb, season, episode, urllib.quote_plus(json.dumps(meta))))
				else: url = self.parameterize('%s?action=scrape&title=%s&year=%s&imdb=%s&tvdb=%s&season=%s&episode=%s&tvshowtitle=%s&premiered=%s&metadata=%s%s' % (sysaddon, systitle, year, imdb, tvdb, season, episode, systvshowtitle, syspremiered, urllib.quote_plus(json.dumps(meta)), '' if seasoncount == None else ('&seasoncount=%d' % seasoncount)))

				if not fanart == '0' and not fanart == None: item.setProperty('Fanart_Image', fanart)
				item.setArt(art)
				item.setProperty('IsPlayable', isPlayable)
				item.setInfo(type = 'Video', infoLabels = tools.Media.metadataClean(meta))
				if context: item.addContextMenuItems([interface.Context(mode = interface.Context.ModeItem, type = self.type, kids = self.kids, create = True, watched = watched, season = season, episode = episode, metadata = meta, art = art, label = label, link = url, trailer = trailer, title = title, year = year, imdb = imdb, tvdb = tvdb).menu()])
				control.addItem(handle = syshandle, url = url, listitem = item, isFolder = isFolder)
			except:
				tools.Logger.error()

		# Gaia
		# Show multiple as show, in order to display unwatched count.
		if multiple:
			control.content(syshandle, 'tvshows')
			control.directory(syshandle, cacheToDisc = True)
			views.setView('shows', {'skin.estuary' : 55, 'skin.confluence' : 500})
		else:
			control.content(syshandle, 'episodes')
			control.directory(syshandle, cacheToDisc = True)
			views.setView('episodes', {'skin.estuary' : 55, 'skin.confluence' : 504})

	def addDirectory(self, items, queue = False):
		if items == None or len(items) == 0:
			interface.Loader.hide()
			interface.Dialog.notification(title = 32326, message = 33049, icon = interface.Dialog.IconInformation)
			sys.exit()

		sysaddon = sys.argv[0]
		syshandle = int(sys.argv[1])

		addonFanart = control.addonFanart()
		addonThumb = control.addonThumb()
		context = interface.Context.enabled()

		for i in items:
			try:
				name = i['name']
				link = i['url']
				url = '%s?action=%s' % (sysaddon, i['action'])
				try: url += '&url=%s' % urllib.quote_plus(link)
				except: pass

				item = control.item(label=name)

				if i['image'].startswith('http'): iconIcon = iconThumb = iconPoster = iconBanner = i['image']
				else: iconIcon, iconThumb, iconPoster, iconBanner = interface.Icon.pathAll(icon = i['image'], default = addonThumb)
				item.setArt({'icon': iconIcon, 'thumb': iconThumb, 'poster': iconPoster, 'banner': iconBanner})
				if not addonFanart == None: item.setProperty('Fanart_Image', addonFanart)

				if context: item.addContextMenuItems([interface.Context(mode = interface.Context.ModeGeneric, type = self.type, kids = self.kids, link = url, title = name, create = True, library = link, queue = queue).menu()])
				control.addItem(handle = syshandle, url = url, listitem = item, isFolder = True)
			except:
				pass

		control.content(syshandle, 'addons')
		control.directory(syshandle, cacheToDisc = True)
