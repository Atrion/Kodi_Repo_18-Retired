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

from resources.lib.indexers import episodes as episodesx
from resources.lib.indexers import tvshows as tvshowsx

from resources.lib.extensions import tools
from resources.lib.extensions import cache
from resources.lib.extensions import interface
from resources.lib.extensions import shortcuts

class seasons:

	def __init__(self, type = tools.Media.TypeShow, kids = tools.Selection.TypeUndefined):
		self.type = type

		self.kids = kids
		self.certificates = None
		self.restriction = 0

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

		self.list = []

		self.lang = control.apiLanguage()['tvdb']
		self.datetime = (datetime.datetime.utcnow() - datetime.timedelta(hours = 5))
		self.today_date = (self.datetime).strftime('%Y-%m-%d')
		self.tvdb_key = tools.System.obfuscate(tools.Settings.getString('internal.tvdb.api', raw = True))

		self.trakt_user = tools.Settings.getString('accounts.informants.trakt.user').strip()
		self.traktwatchlist_link = 'http://api-v2launch.trakt.tv/users/me/watchlist/seasons'
		self.traktlist_link = 'http://api-v2launch.trakt.tv/users/%s/lists/%s/items'
		self.traktlists_link = 'http://api-v2launch.trakt.tv/users/me/lists'

		self.tvdb_info_link = 'http://thetvdb.com/api/%s/series/%s/all/%s.zip' % (self.tvdb_key, '%s', '%s')
		self.tvdb_by_imdb = 'http://thetvdb.com/api/GetSeriesByRemoteID.php?imdbid=%s'
		self.tvdb_by_query = 'http://thetvdb.com/api/GetSeries.php?seriesname=%s'
		self.imdb_by_query = 'http://www.omdbapi.com/?t=%s&y=%s'
		self.tvdb_image = 'http://thetvdb.com/banners/'
		self.tvdb_poster = 'http://thetvdb.com/banners/_cache/'

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
	def mark(self, title, imdb, tvdb, season, watched = True):
		if watched: self.markWatch(title = title, imdb = imdb, tvdb = tvdb, season = season)
		else: self.markUnwatch(title = title, imdb = imdb, tvdb = tvdb, season = season)

	@classmethod
	def markWatch(self, title, imdb, tvdb, season):
		interface.Loader.show()
		playcount.seasons(title, imdb, tvdb, season, '7')
		interface.Loader.hide()
		interface.Dialog.notification(title = 35513, message = 35510, icon = interface.Dialog.IconSuccess)

	@classmethod
	def markUnwatch(self, title, imdb, tvdb, season):
		interface.Loader.show()
		playcount.seasons(title, imdb, tvdb, season, '6')
		interface.Loader.hide()
		interface.Dialog.notification(title = 35513, message = 35511, icon = interface.Dialog.IconSuccess)

	def get(self, tvshowtitle, year, imdb, tvdb, idx = True):
		if control.window.getProperty('PseudoTVRunning') == 'True':
			return episodes().get(tvshowtitle, year, imdb, tvdb)

		if idx == True:
			self.list = cache.Cache().cacheMedium(self.tvdb_list, tvshowtitle, year, imdb, tvdb, self.lang)
			if self.kidsOnly():
				self.list = [i for i in self.list if 'mpaa' in i and tools.Kids.allowed(i['mpaa'])]
			self.seasonDirectory(self.list)
			return self.list
		else:
			self.list = self.tvdb_list(tvshowtitle, year, imdb, tvdb, 'en')
			if self.kidsOnly():
				self.list = [i for i in self.list if 'mpaa' in i and tools.Kids.allowed(i['mpaa'])]
			return self.list


	def seasonList(self, url):
		# Dirty implementation, but avoids rewritting everything from episodes.py.

		episodes = episodesx.episodes(type = self.type, kids = self.kids)
		self.list = cache.Cache().cacheMini(episodes.trakt_list, url, self.trakt_user)
		self.list = self.list[::-1]

		tvshows = tvshowsx.tvshows(type = self.type, kids = self.kids)
		tvshows.list = self.list
		tvshows.worker()
		self.list = tvshows.list

		# Remove duplicate season entries.
		try:
			result = []
			for i in self.list:
				found = False
				for j in result:
					if i['imdb'] == j['imdb'] and i['season'] == j['season']:
						found = True
						break
				if not found:
					result.append(i)
			self.list = result
		except: pass

		self.seasonDirectory(self.list)


	def userlists(self):
		episodes = episodesx.episodes(type = self.type, kids = self.kids)
		userlists = []
		try:
			if trakt.getTraktCredentialsInfo() == False: raise Exception()
			self.list = []
			userlists += cache.Cache().cacheMini(episodes.trakt_user_list, self.traktlists_link, self.trakt_user)
		except:
			pass

		try:
			if trakt.getTraktCredentialsInfo() == False: raise Exception()
			self.list = []
			userlists += cache.Cache().cacheMini(episodes.trakt_user_list, self.traktlikedlists_link, self.trakt_user)
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

		for i in range(0, len(self.list)): self.list[i].update({'image': 'traktlists.png', 'action': self.parameterize('seasonsList')})

		# Watchlist
		if trakt.getTraktCredentialsInfo():
		    self.list.insert(0, {'name' : interface.Translation.string(32033), 'url' : self.traktwatchlist_link, 'image': 'traktwatch.png', 'action': self.parameterize('seasons')})

		episodes.addDirectory(self.list, queue = True)
		return self.list


	def tvdb_list(self, tvshowtitle, year, imdb, tvdb, lang, limit=''):
		list = []

		try:
			if imdb == '0':
				try:
					imdb = trakt.SearchTVShow(urllib.quote_plus(tvshowtitle), year, full=False)[0]
					imdb = imdb.get('show', '0')
					imdb = imdb.get('ids', {}).get('imdb', '0')
					imdb = 'tt' + re.sub('[^0-9]', '', str(imdb))

					if not imdb: imdb = '0'
				except:
					imdb = '0'

			if tvdb == '0' and not imdb == '0':
				url = self.tvdb_by_imdb % imdb

				result = client.request(url, timeout='10')

				try: tvdb = client.parseDOM(result, 'seriesid')[0]
				except: tvdb = '0'

				try: name = client.parseDOM(result, 'SeriesName')[0]
				except: name = '0'
				dupe = re.compile('[***]Duplicate (\d*)[***]').findall(name)
				if len(dupe) > 0: tvdb = str(dupe[0])

				if tvdb == '': tvdb = '0'


			if tvdb == '0':
				url = self.tvdb_by_query % (urllib.quote_plus(tvshowtitle))

				years = [str(year), str(int(year)+1), str(int(year)-1)]

				tvdb = client.request(url, timeout='10')
				tvdb = re.sub(r'[^\x00-\x7F]+', '', tvdb)
				tvdb = client.replaceHTMLCodes(tvdb)
				tvdb = client.parseDOM(tvdb, 'Series')
				tvdb = [(x, client.parseDOM(x, 'SeriesName'), client.parseDOM(x, 'FirstAired')) for x in tvdb]
				tvdb = [(x, x[1][0], x[2][0]) for x in tvdb if len(x[1]) > 0 and len(x[2]) > 0]
				tvdb = [x for x in tvdb if cleantitle.get(tvshowtitle) == cleantitle.get(x[1])]
				tvdb = [x[0][0] for x in tvdb if any(y in x[2] for y in years)][0]
				tvdb = client.parseDOM(tvdb, 'seriesid')[0]

				if tvdb == '': tvdb = '0'
		except:
			return

		try:
			if tvdb == '0': return

			url = self.tvdb_info_link % (tvdb, 'en')
			data = urllib2.urlopen(url, timeout=30).read()

			zip = zipfile.ZipFile(StringIO.StringIO(data))
			result = zip.read('%s.xml' % 'en')
			artwork = zip.read('banners.xml')
			zip.close()

			dupe = client.parseDOM(result, 'SeriesName')[0]
			dupe = re.compile('[***]Duplicate (\d*)[***]').findall(dupe)

			if len(dupe) > 0:
				tvdb = str(dupe[0]).encode('utf-8')

				url = self.tvdb_info_link % (tvdb, 'en')
				data = urllib2.urlopen(url, timeout=30).read()

				zip = zipfile.ZipFile(StringIO.StringIO(data))
				result = zip.read('%s.xml' % 'en')
				artwork = zip.read('banners.xml')
				zip.close()

			if not lang == 'en':
				url = self.tvdb_info_link % (tvdb, lang)
				data = urllib2.urlopen(url, timeout=30).read()

				zip = zipfile.ZipFile(StringIO.StringIO(data))
				result2 = zip.read('%s.xml' % lang)
				zip.close()
			else:
				result2 = result

			artwork = artwork.split('<Banner>')
			artwork = [i for i in artwork if '<Language>en</Language>' in i and '<BannerType>season</BannerType>' in i]
			artwork = [i for i in artwork if not 'seasonswide' in re.findall('<BannerPath>(.+?)</BannerPath>', i)[0]]

			result = result.split('<Episode>')
			result2 = result2.split('<Episode>')

			item = result[0]
			item2 = result2[0]
			episodes = [i for i in result if '<EpisodeNumber>' in i]
			if not tools.Settings.getBoolean('interface.tvshows.special.seasons'):
				episodes = [i for i in episodes if not '<SeasonNumber>0</SeasonNumber>' in i]
			if not tools.Settings.getBoolean('interface.tvshows.special.episodes'):
				episodes = [i for i in episodes if not '<EpisodeNumber>0</EpisodeNumber>' in i]
			seasons = [i for i in episodes if '<EpisodeNumber>1</EpisodeNumber>' in i]

			counts = self.seasonCountParse(seasons = seasons, episodes = episodes)

			locals = [i for i in result2 if '<EpisodeNumber>' in i]

			result = ''
			result2 = ''

			if limit == '':
				episodes = []
			elif limit == '-1':
				seasons = []
			else:
				episodes = [i for i in episodes if '<SeasonNumber>%01d</SeasonNumber>' % int(limit) in i]
				seasons = []

			try: poster = client.parseDOM(item, 'poster')[0]
			except: poster = ''
			if not poster == '': poster = self.tvdb_image + poster
			else: poster = '0'
			poster = client.replaceHTMLCodes(poster)
			poster = poster.encode('utf-8')

			try: banner = client.parseDOM(item, 'banner')[0]
			except: banner = ''
			if not banner == '': banner = self.tvdb_image + banner
			else: banner = '0'
			banner = client.replaceHTMLCodes(banner)
			banner = banner.encode('utf-8')

			try: fanart = client.parseDOM(item, 'fanart')[0]
			except: fanart = ''
			if not fanart == '': fanart = self.tvdb_image + fanart
			else: fanart = '0'
			fanart = client.replaceHTMLCodes(fanart)
			fanart = fanart.encode('utf-8')

			if not poster == '0': pass
			elif not fanart == '0': poster = fanart
			elif not banner == '0': poster = banner

			if not banner == '0': pass
			elif not fanart == '0': banner = fanart
			elif not poster == '0': banner = poster

			try: status = client.parseDOM(item, 'Status')[0]
			except: status = ''
			if status == '': status = 'Ended'
			status = client.replaceHTMLCodes(status)
			status = status.encode('utf-8')

			try: studio = client.parseDOM(item, 'Network')[0]
			except: studio = ''
			if studio == '': studio = '0'
			studio = client.replaceHTMLCodes(studio)
			studio = studio.encode('utf-8')

			try: genre = client.parseDOM(item, 'Genre')[0]
			except: genre = ''
			genre = [x for x in genre.split('|') if not x == '']
			genre = ' / '.join(genre)
			if genre == '': genre = '0'
			genre = client.replaceHTMLCodes(genre)
			genre = genre.encode('utf-8')

			try: duration = client.parseDOM(item, 'Runtime')[0]
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

			try: votes = client.parseDOM(item, 'RatingCount')[0]
			except: votes = '0'
			if votes == '': votes = '0'
			votes = client.replaceHTMLCodes(votes)
			votes = votes.encode('utf-8')

			try: mpaa = client.parseDOM(item, 'ContentRating')[0]
			except: mpaa = ''
			if mpaa == '': mpaa = '0'
			mpaa = client.replaceHTMLCodes(mpaa)
			mpaa = mpaa.encode('utf-8')

			try: cast = client.parseDOM(item, 'Actors')[0]
			except: cast = ''
			cast = [x for x in cast.split('|') if not x == '']
			try: cast = [(x.encode('utf-8'), '') for x in cast]
			except: cast = []

			try: label = client.parseDOM(item2, 'SeriesName')[0]
			except: label = '0'
			label = client.replaceHTMLCodes(label)
			label = label.encode('utf-8')

			try: plot = client.parseDOM(item2, 'Overview')[0]
			except: plot = ''
			if plot == '': plot = '0'
			plot = client.replaceHTMLCodes(plot)
			plot = plot.encode('utf-8')
		except:
			pass

		for item in seasons:
			try:
				premiered = client.parseDOM(item, 'FirstAired')[0]
				if premiered == '' or '-00' in premiered: premiered = '0'
				premiered = client.replaceHTMLCodes(premiered)
				premiered = premiered.encode('utf-8')

				# Gaia
				# Show future items.
				if status == 'Ended': pass
				elif premiered == '0': raise Exception()
				#elif int(re.sub('[^0-9]', '', str(premiered))) > int(re.sub('[^0-9]', '', str(self.today_date))): raise Exception()
				elif not tools.Settings.getBoolean('interface.tvshows.future.seasons'):
					if int(re.sub('[^0-9]', '', str(premiered))) > int(re.sub('[^0-9]', '', str(self.today_date))): raise Exception()

				season = client.parseDOM(item, 'SeasonNumber')[0]
				season = '%01d' % int(season)
				season = season.encode('utf-8')

				thumb = [i for i in artwork if client.parseDOM(i, 'Season')[0] == season]
				try: thumb = client.parseDOM(thumb[0], 'BannerPath')[0]
				except: thumb = ''
				if not thumb == '': thumb = self.tvdb_image + thumb
				else: thumb = '0'
				thumb = client.replaceHTMLCodes(thumb)
				thumb = thumb.encode('utf-8')

				if thumb == '0': thumb = poster

				try: seasoncount = counts[season]
				except: seasoncount = None

				item = {'season': season, 'seasoncount': seasoncount, 'tvshowtitle': tvshowtitle, 'label': label, 'year': year, 'premiered': premiered, 'status': status, 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'ratingtvdb': rating, 'votestvdb': votes, 'mpaa': mpaa, 'cast': cast, 'plot': plot, 'imdb': imdb, 'tvdb': tvdb, 'poster': poster, 'banner': banner, 'fanart': fanart, 'thumb': thumb}
				item.update(tools.Rater.extract(item))
				list.append(item)
			except:
				pass


		for item in episodes:
			try:
				premiered = client.parseDOM(item, 'FirstAired')[0]
				if premiered == '' or '-00' in premiered: premiered = '0'
				premiered = client.replaceHTMLCodes(premiered)
				premiered = premiered.encode('utf-8')

				# Gaia
				# Show future items.
				if status == 'Ended': pass
				elif premiered == '0': raise Exception()
				#elif int(re.sub('[^0-9]', '', str(premiered))) > int(re.sub('[^0-9]', '', str(self.today_date))): raise Exception()
				elif not tools.Settings.getBoolean('interface.tvshows.future.episodes'):
					if int(re.sub('[^0-9]', '', str(premiered))) > int(re.sub('[^0-9]', '', str(self.today_date))): raise Exception()

				season = client.parseDOM(item, 'SeasonNumber')[0]
				season = '%01d' % int(season)
				season = season.encode('utf-8')

				episode = client.parseDOM(item, 'EpisodeNumber')[0]
				episode = re.sub('[^0-9]', '', '%01d' % int(episode))
				episode = episode.encode('utf-8')

				title = client.parseDOM(item, 'EpisodeName')[0]
				if title == '': title = '0'
				title = client.replaceHTMLCodes(title)
				try: title = title.encode('utf-8')
				except: pass

				try: thumb = client.parseDOM(item, 'filename')[0]
				except: thumb = ''
				if not thumb == '': thumb = self.tvdb_image + thumb
				else: thumb = '0'
				thumb = client.replaceHTMLCodes(thumb)
				thumb = thumb.encode('utf-8')

				if not thumb == '0': pass
				elif not fanart == '0': thumb = fanart.replace(self.tvdb_image, self.tvdb_poster)
				elif not poster == '0': thumb = poster

				try: rating = client.parseDOM(item, 'Rating')[0]
				except: rating = ''
				if rating == '': rating = '0'
				rating = client.replaceHTMLCodes(rating)
				rating = rating.encode('utf-8')

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

				try:
					local = client.parseDOM(item, 'id')[0]
					local = [x for x in locals if '<id>%s</id>' % str(local) in x][0]
				except:
					local = item

				label = client.parseDOM(local, 'EpisodeName')[0]
				if label == '': label = '0'
				label = client.replaceHTMLCodes(label)
				label = label.encode('utf-8')

				try: episodeplot = client.parseDOM(local, 'Overview')[0]
				except: episodeplot = ''
				if episodeplot == '': episodeplot = '0'
				if episodeplot == '0': episodeplot = plot
				episodeplot = client.replaceHTMLCodes(episodeplot)
				try: episodeplot = episodeplot.encode('utf-8')
				except: pass

				try: seasoncount = counts[season]
				except: seasoncount = None

				item = {'title': title, 'label': label, 'seasoncount' : seasoncount, 'season': season, 'episode': episode, 'tvshowtitle': tvshowtitle, 'year': year, 'premiered': premiered, 'status': status, 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'ratingtvdb': rating, 'votestvdb': votes, 'mpaa': mpaa, 'director': director, 'writer': writer, 'cast': cast, 'plot': episodeplot, 'imdb': imdb, 'tvdb': tvdb, 'poster': poster, 'banner': banner, 'fanart': fanart, 'thumb': thumb}
				item.update(tools.Rater.extract(item))
				list.append(item)
			except:
				pass

		return list

	@classmethod
	def seasonCountParse(self, season = None, items = None, seasons = None, episodes = None):
		# Determine the number of episodes per season to estimate season pack episode sizes.
		index = season
		counts = {} # Do not use a list, since not all seasons are labeled by number. Eg: MythBusters
		if episodes == None:
			episodes = [i for i in items if '<EpisodeNumber>' in i]
			if not tools.Settings.getBoolean('interface.tvshows.special.seasons'):
				episodes = [i for i in episodes if not '<SeasonNumber>0</SeasonNumber>' in i]
			if not tools.Settings.getBoolean('interface.tvshows.special.episodes'):
				episodes = [i for i in episodes if not '<EpisodeNumber>0</EpisodeNumber>' in i]
			seasons = [i for i in episodes if '<EpisodeNumber>1</EpisodeNumber>' in i]
		for s in seasons:
		    season = client.parseDOM(s, 'SeasonNumber')[0]
		    season = '%01d' % int(season)
		    season = season.encode('utf-8')
		    counts[season] = 0
		for e in episodes:
		    try:
		        season = client.parseDOM(e, 'SeasonNumber')[0]
		        season = '%01d' % int(season)
		        season = season.encode('utf-8')
		        counts[season] += 1
		    except: pass
		try:
			if index == None: return counts
			else: return counts[index]
		except: return None

	def seasonCount(self, tvshowtitle, year, imdb, tvdb, season):
		try: return cache.Cache().cacheLong(self._seasonCount, tvshowtitle, year, imdb, tvdb)[season]
		except: return None

	def _seasonCount(self, tvshowtitle, year, imdb, tvdb):
		try:
			if imdb == '0':
				try:
					imdb = trakt.SearchTVShow(urllib.quote_plus(tvshowtitle), year, full=False)[0]
					imdb = imdb.get('show', '0')
					imdb = imdb.get('ids', {}).get('imdb', '0')
					imdb = 'tt' + re.sub('[^0-9]', '', str(imdb))
					if not imdb: imdb = '0'
				except:
					imdb = '0'

			if tvdb == '0' and not imdb == '0':
				url = self.tvdb_by_imdb % imdb
				result = client.request(url, timeout='10')
				try: tvdb = client.parseDOM(result, 'seriesid')[0]
				except: tvdb = '0'
				try: name = client.parseDOM(result, 'SeriesName')[0]
				except: name = '0'
				dupe = re.compile('[***]Duplicate (\d*)[***]').findall(name)
				if len(dupe) > 0: tvdb = str(dupe[0])
				if tvdb == '': tvdb = '0'

			if tvdb == '0':
				url = self.tvdb_by_query % (urllib.quote_plus(tvshowtitle))
				years = [str(year), str(int(year)+1), str(int(year)-1)]
				tvdb = client.request(url, timeout='10')
				tvdb = re.sub(r'[^\x00-\x7F]+', '', tvdb)
				tvdb = client.replaceHTMLCodes(tvdb)
				tvdb = client.parseDOM(tvdb, 'Series')
				tvdb = [(x, client.parseDOM(x, 'SeriesName'), client.parseDOM(x, 'FirstAired')) for x in tvdb]
				tvdb = [(x, x[1][0], x[2][0]) for x in tvdb if len(x[1]) > 0 and len(x[2]) > 0]
				tvdb = [x for x in tvdb if cleantitle.get(tvshowtitle) == cleantitle.get(x[1])]
				tvdb = [x[0][0] for x in tvdb if any(y in x[2] for y in years)][0]
				tvdb = client.parseDOM(tvdb, 'seriesid')[0]
				if tvdb == '': tvdb = '0'
		except:
			return None

		try:
			if tvdb == '0': return None

			url = self.tvdb_info_link % (tvdb, 'en')
			data = urllib2.urlopen(url, timeout=30).read()
			zip = zipfile.ZipFile(StringIO.StringIO(data))
			result = zip.read('%s.xml' % 'en')
			zip.close()

			dupe = client.parseDOM(result, 'SeriesName')[0]
			dupe = re.compile('[***]Duplicate (\d*)[***]').findall(dupe)

			if len(dupe) > 0:
				tvdb = str(dupe[0]).encode('utf-8')
				url = self.tvdb_info_link % (tvdb, 'en')
				data = urllib2.urlopen(url, timeout=30).read()
				zip = zipfile.ZipFile(StringIO.StringIO(data))
				result = zip.read('%s.xml' % 'en')
				zip.close()

			result = result.split('<Episode>')
			return self.seasonCountParse(items = result)
		except:
			return None

	def recaps(self, tvshowtitle, year, imdb, tvdb):
		count = 0
		current = tools.Time.timestamp()
		seasons = self.get(tvshowtitle = tvshowtitle, year = year, imdb = imdb, tvdb = tvdb, idx = False)
		for season in seasons:
			time = tools.Time.timestamp(season['premiered'], format = tools.Time.FormatDate)
			if time < current: count += 1
		return count

	def context(self, tvshowtitle, title, year, imdb, tvdb, season):
		from resources.lib.indexers import tvshows
		metadata = tvshows.tvshows(type = self.type, kids = self.kids).metadata(tvshowtitle = tvshowtitle, title = title, year = year, imdb = imdb, tvdb = tvdb, season = season)

		addon = tools.System.plugin()
		addonPoster, addonBanner = control.addonPoster(), control.addonBanner()
		addonFanart, settingFanart = control.addonFanart(), tools.Settings.getBoolean('interface.theme.fanart')

		try: indicators = playcount.getSeasonIndicators(items[0]['imdb'])
		except: indicators = None
		ratingsOwn = tools.Settings.getInteger('interface.ratings.type') == 1

		imdb, tvdb, year, season = metadata['imdb'], metadata['tvdb'], metadata['year'], metadata['season']
		title = metadata['tvshowtitle']
		label = None
		try: label = tools.Media().title(tools.Media.TypeSeason, season = season, special = True)
		except: pass
		if label == None: label = season

		systitle = urllib.quote_plus(title)

		meta = dict((k,v) for k, v in metadata.iteritems() if not v == '0')
		meta.update({'mediatype': 'season', 'season' : season})
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
		try:
			if not 'tvshowyear' in meta: meta.update({'tvshowyear': year})
		except: pass

		try:
			# Year is the shows year, not the seasons year. Extract the correct year frpm the premier date.
			yearNew = metadata['premiered']
			yearNew = re.findall('(\d{4})', yearNew)[0]
			yearNew = yearNew.encode('utf-8')
			meta.update({'year': yearNew})
		except:
			pass

		meta.update(tools.Rater.extract(meta)) # Update again, in case the old metadata was retrieved from cache, but the settings changed.

		watched = int(playcount.getSeasonOverlay(indicators, imdb, tvdb, season)) == 7
		if watched: meta.update({'playcount': 1, 'overlay': 7})
		else: meta.update({'playcount': 0, 'overlay': 6})
		meta.update({'watched': int(watched)}) # Kodi's documentation says this value is deprecate. However, without this value, Kodi adds the watched checkmark over the remaining episode count.

		# First check thumbs, since they typically contains the seasons poster. The normal poster contains the show poster.
		poster = '0'
		if poster == '0' and 'thumb3' in metadata: poster = metadata['thumb3']
		if poster == '0' and 'thumb2' in metadata: poster = metadata['thumb2']
		if poster == '0' and 'thumb' in metadata: poster = metadata['thumb']
		if poster == '0' and 'poster3' in metadata: poster = metadata['poster3']
		if poster == '0' and 'poster2' in metadata: poster = metadata['poster2']
		if poster == '0' and 'poster' in metadata: poster = metadata['poster']

		posterShow = '0'
		if posterShow == '0' and 'poster3' in metadata: posterShow = metadata['poster3']
		if posterShow == '0' and 'poster2' in metadata: posterShow = metadata['poster2']
		if posterShow == '0' and 'poster' in metadata: posterShow = metadata['poster']

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
		if not poster == '0' and not poster == None: art.update({'poster' : poster, 'tvshow.poster' : posterShow, 'season.poster' : poster})
		if not icon == '0' and not icon == None: art.update({'icon' : icon})
		if not thumb == '0' and not thumb == None: art.update({'thumb' : thumb})
		if not banner == '0' and not banner == None: art.update({'banner' : banner})
		if not clearlogo == '0' and not clearlogo == None: art.update({'clearlogo' : clearlogo})
		if not clearart == '0' and not clearart == None: art.update({'clearart' : clearart})
		if not fanart == '0' and not fanart == None: art.update({'fanart' : fanart})
		if not landscape == '0' and not landscape == None: art.update({'landscape' : landscape})

		meta.update({'trailer': '%s?action=streamsVideo&video=trailer&title=%s&year=%s&season=%s&imdb=%s&art=%s' % (addon, systitle, year, str(season), imdb, urllib.quote_plus(json.dumps(art)))})
		link = self.parameterize('%s?action=episodesRetrieve&tvshowtitle=%s&year=%s&imdb=%s&tvdb=%s&season=%s&metadata=%s' % (addon, systitle, year, imdb, tvdb, season, urllib.quote_plus(json.dumps(meta))))

		return interface.Context(mode = interface.Context.ModeItem, type = tools.Media.TypeSeason, kids = self.kids, create = True, watched = watched, season = season, metadata = meta, art = art, label = label, link = link, title = title, year = year, imdb = imdb, tvdb = tvdb)

	def extras(self, metadata, art):
		from resources.lib.extensions import video

		sysaddon = sys.argv[0]
		syshandle = int(sys.argv[1])
		isPlayable = 'true' if not 'plugin' in control.infoLabel('Container.PluginName') else 'false'
		context = interface.Context.enabled()
		label = interface.Translation.string(32055)

		metadata['mediatype'] = 'video'
		metadata['episode'] = 0
		metadata['rating'] = 0
		metadata['userrating'] = 0
		metadata['votes'] = 0
		metadata['premiered'] = 0

		title = metadata['tvshowtitle']
		year = metadata['year']
		imdb = metadata['imdb']
		tvdb = metadata['tvdb']
		season = int(metadata['season'])

		sysart = urllib.quote_plus(json.dumps(art))
		systitle = urllib.quote_plus(title)

		videos = [video.Review, video.Extra, video.Deleted, video.Making, video.Director, video.Interview, video.Explanation]
		for i in videos:
			try:
				if i.enabled():
					metadata['duration'] = i.Duration
					metadata['title'] = metadata['originaltitle'] = metadata['tagline'] = label + ' ' + interface.Translation.string(i.Label)
					metadata['plot'] = interface.Translation.string(i.Description) % (str(season), title)

					item = control.item(label = metadata['title'])
					item.setArt(art)
					item.setProperty('IsPlayable', isPlayable)
					item.setInfo(type = 'Video', infoLabels = tools.Media.metadataClean(metadata))

					url = self.parameterize('%s?action=streamsVideo&video=%s&title=%s&year=%s&season=%s&imdb=%s&metadata=%s&art=%s' % (sysaddon, i.Id, systitle, year, str(season), imdb, urllib.quote_plus(json.dumps(metadata)), sysart))
					if context: item.addContextMenuItems([interface.Context(mode = interface.Context.ModeVideo, video = i.Id, type = tools.Media.TypeEpisode, kids = self.kids, season = season, metadata = metadata, art = art, title = title, year = year, imdb = imdb, tvdb = tvdb).menu()])
					control.addItem(handle = syshandle, url = url, listitem = item, isFolder = False)
			except:
				tools.Logger.error()

		control.content(syshandle, 'episodes')
		control.directory(syshandle, cacheToDisc = True)
		views.setView('episodes', {'skin.estuary' : 55, 'skin.confluence' : 504})

	def seasonDirectory(self, items):
		if isinstance(items, dict) and 'value' in items:
			items = items['value']
		if isinstance(items, basestring):
			try: items = tools.Converter.jsonFrom(items)
			except: pass

		if items == None or len(items) == 0:
			interface.Loader.hide()
			interface.Dialog.notification(title = 32054, message = 33049, icon = interface.Dialog.IconInformation)
			sys.exit()

		sysaddon = sys.argv[0]
		syshandle = int(sys.argv[1])
		media = tools.Media()

		addonPoster, addonBanner = control.addonPoster(), control.addonBanner()
		addonFanart, settingFanart = control.addonFanart(), tools.Settings.getBoolean('interface.theme.fanart')

		try: indicators = playcount.getSeasonIndicators(items[0]['imdb'])
		except: indicators = None

		ratingsOwn = tools.Settings.getInteger('interface.ratings.type') == 1
		unwatchedEnabled = tools.Settings.getBoolean('interface.tvshows.unwatched.enabled')
		unwatchedLimit = tools.Settings.getBoolean('interface.tvshows.unwatched.limit')
		context = interface.Context.enabled()

		try: multi = [i['tvshowtitle'] for i in items]
		except: multi = []
		multi = len([x for y,x in enumerate(multi) if x not in multi[:y]])
		multi = True if multi > 1 else False

		for i in items:
			try:
				imdb, tvdb, year, season = i['imdb'], i['tvdb'], i['year'], i['season']
				title = i['tvshowtitle']
				label = None
				try: label = media.title(tools.Media.TypeSeason, season = season, special = True)
				except: pass
				if label == None: label = season
				if multi == True and not label in title and not title in label: label = '%s - %s' % (title, label)

				systitle = urllib.quote_plus(title)

				meta = dict((k,v) for k, v in i.iteritems() if not v == '0')
				meta.update({'mediatype': 'season', 'season' : season})
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
				try:
					if not 'tvshowyear' in meta: meta.update({'tvshowyear': year})
				except: pass

				try:
					# Year is the shows year, not the seasons year. Extract the correct year frpm the premier date.
					yearNew = i['premiered']
					yearNew = re.findall('(\d{4})', yearNew)[0]
					yearNew = yearNew.encode('utf-8')
					meta.update({'year': yearNew})
				except:
					pass

				meta.update(tools.Rater.extract(meta)) # Update again, in case the old metadata was retrieved from cache, but the settings changed.

				item = control.item(label = label)

				try:
					overlay = int(playcount.getSeasonOverlay(indicators, imdb, tvdb, season))
					watched = overlay == 7
					if watched: meta.update({'playcount': 1, 'overlay': 7})
					else: meta.update({'playcount': 0, 'overlay': 6})
					meta.update({'watched': int(watched)}) # Kodi's documentation says this value is deprecate. However, without this value, Kodi adds the watched checkmark over the remaining episode count.
					if unwatchedEnabled:
						count = playcount.getSeasonCount(imdb, season, unwatchedLimit)
						if count:
							item.setProperty('TotalEpisodes', str(count['total']))
							item.setProperty('WatchedEpisodes', str(count['watched']))
							item.setProperty('UnWatchedEpisodes', str(count['unwatched']))
				except: pass

				# First check thumbs, since they typically contains the seasons poster. The normal poster contains the show poster.
				poster = '0'
				if poster == '0' and 'thumb3' in i: poster = i['thumb3']
				if poster == '0' and 'thumb2' in i: poster = i['thumb2']
				if poster == '0' and 'thumb' in i: poster = i['thumb']
				if poster == '0' and 'poster3' in i: poster = i['poster3']
				if poster == '0' and 'poster2' in i: poster = i['poster2']
				if poster == '0' and 'poster' in i: poster = i['poster']

				posterShow = '0'
				if posterShow == '0' and 'poster3' in i: posterShow = i['poster3']
				if posterShow == '0' and 'poster2' in i: posterShow = i['poster2']
				if posterShow == '0' and 'poster' in i: posterShow = i['poster']

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
				if not poster == '0' and not poster == None: art.update({'poster' : poster, 'tvshow.poster' : posterShow, 'season.poster' : poster})
				if not icon == '0' and not icon == None: art.update({'icon' : icon})
				if not thumb == '0' and not thumb == None: art.update({'thumb' : thumb})
				if not banner == '0' and not banner == None: art.update({'banner' : banner})
				if not clearlogo == '0' and not clearlogo == None: art.update({'clearlogo' : clearlogo})
				if not clearart == '0' and not clearart == None: art.update({'clearart' : clearart})
				if not fanart == '0' and not fanart == None: art.update({'fanart' : fanart})
				if not landscape == '0' and not landscape == None: art.update({'landscape' : landscape})

				meta.update({'trailer': self.parameterize('%s?action=streamsVideo&video=trailer&title=%s&year=%s&imdb=%s&art=%s' % (sysaddon, systitle, year, imdb, urllib.quote_plus(json.dumps(art))))})
				url = self.parameterize('%s?action=episodesRetrieve&tvshowtitle=%s&year=%s&imdb=%s&tvdb=%s&season=%s&metadata=%s' % (sysaddon, systitle, year, imdb, tvdb, season, urllib.quote_plus(json.dumps(meta))))

				if not fanart == '0' and not fanart == None: item.setProperty('Fanart_Image', fanart)
				item.setArt(art)
				item.setInfo(type = 'Video', infoLabels = tools.Media.metadataClean(meta))
				if context: item.addContextMenuItems([interface.Context(mode = interface.Context.ModeItem, type = tools.Media.TypeSeason, kids = self.kids, create = True, watched = watched, season = season, metadata = meta, art = art, label = label, link = url, title = title, year = year, imdb = imdb, tvdb = tvdb).menu()])
				control.addItem(handle = syshandle, url = url, listitem = item, isFolder = True)
			except:
				pass

		try: control.property(syshandle, 'showplot', items[0]['plot'])
		except: pass

		control.content(syshandle, 'seasons')
		control.directory(syshandle, cacheToDisc = True)
		views.setView('seasons', {'skin.estuary': 55, 'skin.confluence': 500})
