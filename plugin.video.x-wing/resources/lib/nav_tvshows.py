import os, time, _strptime
import xbmc, xbmcvfs, xbmcplugin
from resources.lib import text
from resources.lib import Trakt
from resources.lib import tools
from resources.lib import executor
from resources.lib import nav_base
from resources.lib import meta_info
from resources.lib import lib_tvshows
from resources.lib import play_tvshows
from resources.lib.TheTVDB import TVDB
from resources.lib.xswift2 import plugin


SORT = [
	xbmcplugin.SORT_METHOD_UNSORTED,
	xbmcplugin.SORT_METHOD_LABEL,
	xbmcplugin.SORT_METHOD_VIDEO_YEAR,
	xbmcplugin.SORT_METHOD_GENRE,
	xbmcplugin.SORT_METHOD_VIDEO_RATING,
	xbmcplugin.SORT_METHOD_PLAYCOUNT]
SORTRAKT = [
	xbmcplugin.SORT_METHOD_UNSORTED,
	xbmcplugin.SORT_METHOD_LABEL,
	xbmcplugin.SORT_METHOD_VIDEO_YEAR,
	xbmcplugin.SORT_METHOD_GENRE,
	xbmcplugin.SORT_METHOD_VIDEO_RATING,
	xbmcplugin.SORT_METHOD_PLAYCOUNT,
	xbmcplugin.SORT_METHOD_DURATION,
	xbmcplugin.SORT_METHOD_MPAA_RATING]

def list_trakt_tvshows(results, pages, page):
	genres_dict = dict([(x['slug'], x['name']) for x in Trakt.get_genres('shows')])
	shows = [meta_info.get_tvshow_metadata_trakt(item['show'], genres_dict) for item in results]
	items = [make_tvshow_item(show) for show in shows if show.get('tvdb_id')]
	page = int(page)
	pages = int(pages)
	if pages > 1:
		args = nav_base.caller_args()
		args['page'] = page + 1
		args['confirm'] = 'yes'
		items.append(
			{
				'label': '%s/%s  [I]Next page[/I]  >>' % (page + 1, pages + 1),
				'path': plugin.url_for(nav_base.caller_name(), **args),
				'thumbnail': plugin.get_media_icon('item_next'),
				'fanart': plugin.get_addon_fanart()
			})
	return plugin.finish(items=items, sort_methods=SORT)

@plugin.route('/tv/trakt_watched/<page>')
def trakt_tv_watched(page, raw=False):
	results, pages = Trakt.get_watched_shows_paginated(page)
	if raw:
		return results
	else:
		return list_trakt_tvshows(results, pages, page)

@plugin.route('/tv/trakt_netflix_collected/<page>')
def trakt_netflix_tv_collected(page, raw=False):
	results, pages = Trakt.get_netflix_collected_shows(page)
	if raw:
		return results
	else:
		return list_trakt_tvshows(results, pages, page)

@plugin.route('/tv/trakt_collected/<page>')
def trakt_tv_collected(page, raw=False):
	results, pages = Trakt.get_collected_shows_paginated(page)
	if raw:
		return results
	else:
		return list_trakt_tvshows(results, pages, page)

@plugin.route('/tv/trakt_popular/<page>')
def tv_trakt_popular(page, raw=False):
	results, pages = Trakt.get_popular_shows_paginated(page)
	if raw:
		return results
	else:
		genres_dict = dict([(x['slug'], x['name']) for x in Trakt.get_genres('shows')])
		shows = [meta_info.get_tvshow_metadata_trakt(item, genres_dict) for item in results]
		items = [make_tvshow_item(show) for show in shows if show.get('tvdb_id')]
		page = int(page)
		pages = int(pages)
		if pages > 1:
			items.append(
				{
					'label': '%s/%s  [I]Next page[/I]  >>' % (page + 1, pages + 1),
					'path': plugin.url_for('tv_trakt_popular', page=page + 1),
					'thumbnail': plugin.get_media_icon('item_next'),
					'fanart': plugin.get_addon_fanart()
				})
		return plugin.finish(items=items, sort_methods=SORT)

@plugin.route('/tv/trakt_trending/<page>')
def trakt_tv_trending(page, raw=False):
	results, pages = Trakt.get_trending_shows_paginated(page)
	if raw:
		return results
	else:
		list_trakt_tvshows(results, pages, page)

@plugin.route('/tv/tvdb_search_term/<term>/<page>')
def tvdb_tv_search_term(term, page):
	search_results = TVDB.search(term, language='en')
	items = []
	load_full_tvshow = lambda tvshow : TVDB.get_show(tvshow['id'], full=True)
	for tvdb_show in executor.execute(load_full_tvshow, search_results, workers=10):
		info = build_tvshow_info(tvdb_show)
		items.append(make_tvshow_item(info))
	return items

def list_trakt_search_items(results, pages, page):
	shows = [meta_info.get_tvshow_metadata_trakt(item['show'], None) for item in results]
	items = [make_tvshow_item(show) for show in shows if show.get('tvdb_id')]
	page = int(page)
	pages = int(pages)
	if pages > 1:
		args = nav_base.caller_args()
		nextpage = page + 1
		args['page'] = page + 1
		items.append(
			{
				'label': '%s/%s  [I]Next page[/I]  >>' % (nextpage, pages),
				'path': plugin.url_for(nav_base.caller_name(), **args),
				'thumbnail': plugin.get_media_icon('item_next'),
				'fanart': plugin.get_addon_fanart()
			})
	return items

@plugin.route('/tv/trakt_search_term/<term>/<page>')
def trakt_tv_search_term(term, page):
	results, pages = Trakt.search_for_tvshow_paginated(term, page)
	return list_trakt_search_items(results, pages, page)

@plugin.cached_route('/tv_genres', TTL=60)
def tmdb_tv_genres():
	genres = nav_base.get_tv_genres()
	items = sorted([
		{
			'label': name,
			'path': plugin.url_for('tmdb_tv_genre', id=id, page=1),
			'thumbnail': nav_base.get_genre_icon(id),
			'fanart': plugin.get_addon_fanart()
		} for id, name in genres.items()], key=lambda k: k['label'])
	return items

@plugin.cached_route('/tv/genre/<id>/<page>', TTL=60)
def tmdb_tv_genre(id, page, raw=False):
	from resources.lib.TheMovieDB import Discover
	result = Discover().tv(with_genres=id, page=page, language='en')
	if raw:
		return result
	else:
		return list_tvshows(result)

@plugin.cached_route('/tv/tmdb_now_playing/<page>', TTL=60)
def tmdb_tv_on_the_air(page, raw=False):
	from resources.lib.TheMovieDB import TV
	result = TV().on_the_air(page=page, language='en')
	if raw:
		return result
	else:
		return list_tvshows(result)

@plugin.cached_route('/tv/tmdb_most_popular/<page>', TTL=60)
def tmdb_tv_most_popular(page, raw=False):
	from resources.lib.TheMovieDB import TV
	result = TV().popular(page=page, language='en')
	if raw:
		return result
	else:
		return list_tvshows(result)

def get_tvdb_id_from_name(name, lang):
	tools.show_busy()
	search_results = TVDB.search(name, language=lang)
	if not search_results:
		tools.hide_busy()
		plugin.ok('TV show not found', 'no show information found for %s in tvdb' % text.to_utf8(name))
	items = []
	for show in search_results:
		if 'firstaired' in show:
			show['year'] = int(show['firstaired'].split('-')[0].strip())
		else:
			show['year'] = 'unknown'
		items.append(show)
	if len(items) > 1:
		selection = plugin.select('Choose TV Show', ['%s (%s)' % (text.to_utf8(s['seriesname']), s['year']) for s in items])
	else:
		selection = 0
	tools.hide_busy()
	if selection != -1:
		return items[selection]['id']

def get_tvdb_id_from_imdb_id(imdb_id):
	tvdb_id = TVDB.search_by_imdb(imdb_id)
	if not tvdb_id:
		plugin.ok('TV show not found', 'no show information found for %s in tvdb' % imdb_id)
	return tvdb_id

@plugin.route('/tv/play/<id>/<season>/<episode>')
def tv_play(id, season, episode):
	play_tvshows.play_episode(id, season, episode)

@plugin.route('/tv/play_by_name/<name>/<season>/<episode>/<lang>', options={'lang': 'en'})
def tv_play_by_name(name, season, episode, lang):
	tvdb_id = get_tvdb_id_from_name(name, lang)
	if tvdb_id:
		tv_play(tvdb_id, season, episode)

@plugin.route('/tv/tvdb/<id>/')
def tv_tvshow(id):
	plugin.set_content('seasons')
	return plugin.finish(items=list_seasons_tvdb(id), sort_methods=SORT)


@plugin.route('/tv/tvdb/<id>/<season_num>/')
def tv_season(id, season_num):
	plugin.set_content('episodes')
	return plugin.finish(items=list_episodes_tvdb(id, season_num), sort_methods=SORT)

@plugin.route('/tv/add_to_library_parsed/<id>/<player>')
def tv_add_to_library_parsed(id, player):
	if id.startswith('tt'):
		try:
			id = TVDB.search_by_imdb(id)
		except:
			plugin.ok('TV show not found', 'no show information found for %s in TheTVDB' % id)
	library_folder = lib_tvshows.setup_library(plugin.get_setting('tv_library_folder', unicode))
	show = TVDB[int(id)]
	imdb = show['imdb_id']
	library_folder = lib_tvshows.setup_library(plugin.get_setting('tv_library_folder', unicode))
	if lib_tvshows.add_tvshow_to_library(library_folder, show, player):
		plugin.setProperty('plugin.video.x-wing.clean_library', 'true')
	tools.scan_library(path=plugin.get_setting('tv_library_folder', unicode))

@plugin.route('/tv/add_to_library/<id>')
def tv_add_to_library(id):
	library_folder = lib_tvshows.setup_library(plugin.get_setting('tv_library_folder', unicode))
	show = TVDB[int(id)]
	imdb = show['imdb_id']
	library_folder = lib_tvshows.setup_library(plugin.get_setting('tv_library_folder', unicode))
	if lib_tvshows.add_tvshow_to_library(library_folder, show):
		plugin.setProperty('plugin.video.x-wing.clean_library', 'true')
	tools.scan_library(path=plugin.get_setting('tv_library_folder', unicode))

def tv_add_all_to_library(items, noscan=False):
	library_folder = lib_tvshows.setup_library(plugin.get_setting('tv_library_folder', unicode))
	ids = ''
	if 'results' in items:
		preids = []
		for tvdb_show, tmdb_show in executor.execute(tmdb_to_tvdb, items['results'], workers=10):
			if tvdb_show is not None:
				preids.append(tvdb_show['id'])
		ids = '\n'.join(preids)
	else:
		ids = '\n'.join([str(i['show']['ids']['tvdb']) if i['show']['ids']['tvdb'] != None and i['show']['ids']['tvdb'] != '' else i['show']['ids']['imdb'] for i in items])
	shows_batch_add_file = plugin.get_setting('tv_batch_add_file_path', unicode)
	if xbmcvfs.exists(shows_batch_add_file):
		batch_add_file = xbmcvfs.File(shows_batch_add_file)
		pre_ids = batch_add_file.read()
		xids = pre_ids.split('\n')
		for id in xids:
			if id != '' and id != None and id not in ids:
				ids = ids + str(id) + '\n'
		batch_add_file.close()
		xbmcvfs.delete(shows_batch_add_file)
	batch_add_file = xbmcvfs.File(shows_batch_add_file, 'w')
	batch_add_file.write(str(ids))
	batch_add_file.close()
	xbmc.executebuiltin('RunPlugin(plugin://plugin.video.x-wing/tv/batch_add_to_library)')

@plugin.route('/tv/batch_add_to_library')
def tv_batch_add_to_library():
	tv_batch_file = plugin.get_setting('tv_batch_add_file_path', unicode)
	if xbmcvfs.exists(tv_batch_file):
		try:
			f = open(xbmc.translatePath(tv_batch_file), 'r')
			r = f.read()
			f.close()
			ids = r.split('\n')
		except:
			plugin.notify('TV shows', 'not found', plugin.get_addon_icon(), 3000)
		library_folder = lib_tvshows.setup_library(plugin.get_setting('tv_library_folder', unicode))
		ids_index = 0
		for id in ids:
			if id == None or id == 'None':
				pass
			elif ',' in id:
				csvs = id.split(',')
				for csv in csvs:
					if csv == None or csv == 'None':
						pass
					elif str(csv).startswith('tt') and csv != '':
						tvdb_id = get_tvdb_id_from_imdb_id(csv)
					else:
						tvdb_id = csv
					show = TVDB[int(tvdb_id)]
					lib_tvshows.batch_add_tvshows_to_library(library_folder, show)
			else:
				if id == None or id == 'None' or id == '':
					pass
				elif str(id).startswith('tt'):
					tvdb_id = get_tvdb_id_from_imdb_id(id)
				else:
					tvdb_id = id
				try:
					show = TVDB[int(tvdb_id)]
					lib_tvshows.batch_add_tvshows_to_library(library_folder, show)
				except:
					plugin.notify('Failed to add', '%s' % id, plugin.get_addon_icon(), 3000)
			ids_index += 1
		os.remove(xbmc.translatePath(tv_batch_file))
		lib_tvshows.update_library()
		return True

def list_tvshows(response):
	items = []
	results = response['results']
	for tvdb_show, tmdb_show in executor.execute(tmdb_to_tvdb, results, workers=10):
		if tvdb_show is not None:
			info = build_tvshow_info(tvdb_show, tmdb_show)
			items.append(make_tvshow_item(info))
	if xbmc.Monitor().abortRequested():
		return
	if 'page' in response:
		page = response['page']
		args = nav_base.caller_args()
		if page < response['total_pages']:
			args['page'] = str(page + 1)
			items.append(
				{
					'label': '%s/%s  [I]Next page[/I]  >>' % (page + 1, response['total_pages']),
					'path': plugin.url_for(nav_base.caller_name(), **args),
					'thumbnail': plugin.get_media_icon('item_next'),
					'fanart': plugin.get_addon_fanart()
				})
	return items

def list_trakt_episodes(result):
	genres_dict = dict([(x['slug'], x['name']) for x in Trakt.get_genres('shows')])
	items = []
	for item in result:
		if 'episode' in item:
			episode = item['episode']
		else:
			episode = item
		if 'show' in item:
			show = item['show']
		try:
			id = episode['show']['ids']['tvdb']
		except:
			id = episode['ids'].get('tvdb')
		if not id:
			continue
		try:
			season_num = episode['season']
		except:
			season_num = episode.get('season')
		try:
			episode_num = episode['number']
		except:
			episode_num = episode.get('number')
		if show:
			tvshow_title = show.get('title').encode('utf-8')
		else:
			try:
				tvshow_title = (episode['show']['title']).encode('utf-8')
			except:
				tvshow_title = str(episode.get('title')).encode('utf-8')
		if episode['title'] != None:
			try:
				episode_title = episode['title'].encode('utf-8')
			except:
				episode_title = episode.get('title').encode('utf-8')
		else:
			episode_title = 'TBA'
		info = meta_info.get_tvshow_metadata_trakt(item['show'], genres_dict)
		episode_info = meta_info.get_episode_metadata_trakt(info, episode)
		episode_info['title'] = '%s (%02dx%02d): %s' % (tvshow_title, season_num, episode_num, episode_title)
		if xbmc.getCondVisibility('system.hasaddon(script.extendedinfo)'):
			context_menu = [
				('[COLOR limegreen]EIM[/COLOR]4[COLOR limegreen]Q[/COLOR]ed', 'RunScript(script.extendedinfo,info=extendedepisodeinfo,tvshow=%s,season=%s,episode=%s)' % (tvshow_title, season_num, episode_num))]
		else:
			context_menu = []
		items.append(
			{
				'label': episode_info['title'],
				'path': plugin.url_for('tv_play', id=id, season=season_num, episode=episode_num),
				'context_menu': context_menu,
				'info': episode_info,
				'is_playable': True,
				'info_type': 'video',
				'stream_info': {'video': {}},
				'thumbnail': episode_info['poster'],
				'poster': episode_info['poster'],
				'fanart': episode_info['fanart']
			})
	return plugin.finish(items=items, sort_methods=SORTRAKT, cache_to_disc=False)

def build_tvshow_info(tvdb_show, tmdb_show=None):
	tvdb_info = meta_info.get_tvshow_metadata_tvdb(tvdb_show)
	tmdb_info = meta_info.get_tvshow_metadata_tmdb(tmdb_show)
	info = {}
	info.update(tvdb_info)
	info.update(dict((k,v) for k,v in tmdb_info.iteritems() if v))
	return info

def make_tvshow_item(info):
	from resources.lib.TheMovieDB import TV, Find
	try:
		tvdb_id = info['tvdb']
	except:
		tvdb_id = ''
	if tvdb_id == '': 
		try:
			tvdb_id = info['tvdb_id']
		except:
			tvdb_id = ''
	try:
		tmdb_id = info['tmdb']
	except:
		tmdb_id = ''
	if tmdb_id == '': 
		try:
			tmdb_id = info['id']
		except:
			tmdb_id = ''
	try:
		imdb_id = info['imdb_id']
	except:
		imdb_id = ''
	if imdb_id == '': 
		try:
			imdb_id = info['imdb']
		except:
			imdb_id = ''
	if not info['poster']:
		info['poster'] = None
	if not info['fanart']:
		info['fanart'] = None
	if info['poster'] == None or info['poster'] == '':
		if tmdb_id != None and tmdb_id != '':
			show = TV(tmdb_id).info()
			if show['poster_path'] != None and show['poster_path'] != '':
				info['poster'] = u'https://image.tmdb.org/t/p/w500' + show['poster_path']
			if info['fanart'] == None or info['fanart'] == '':
				if show['backdrop_path'] != None and show['backdrop_path'] != '':
					info['fanart'] = u'https://image.tmdb.org/t/p/original' + show['backdrop_path']
	if info['poster'] == None or info['poster'] == '':
		if tvdb_id != None and tvdb_id != '':
			show = TVDB.get_show(int(tvdb_id), full=False)
			if show != None:
				if show['seriesname'] != None and show['seriesname'] != '':
					if show.get('poster', '') != None and show.get('poster', '') != '':
						info['poster'] = show.get('poster', '')
					if info['fanart'] == None or info['fanart'] == '':
						if show.get('fanart', '') != None and show.get('fanart', '') != '':
							info['fanart'] = show.get('fanart', '')
	if info['poster'] == None or info['poster'] == '':
		if imdb_id != None and imdb_id != '':
			preshow = Find(imdb_id).info(external_source='imdb_id')
			proshow = preshow['tv_results']
			if proshow != []:
				show = proshow[0]
			else:
				show = []
			if show != []:
				if show['poster_path'] != None and show['poster_path'] != '':
					info['poster'] = u'https://image.tmdb.org/t/p/w500' + show['poster_path']
				if info['fanart'] == None or info['fanart'] == '':
					if show['backdrop_path'] != None and show['backdrop_path'] != '':
						info['fanart'] = u'https://image.tmdb.org/t/p/original' + show['backdrop_path']
	if info['fanart'] == None or info['fanart'] == '':
		info['fanart'] = plugin.get_addon_fanart()
	if xbmc.getCondVisibility('system.hasaddon(script.extendedinfo)'):
		context_menu = [
			('[COLOR limegreen]EIM[/COLOR]4[COLOR limegreen]Q[/COLOR]ed', 'RunScript(script.extendedinfo,info=extendedtvinfo,tvdb_id=%s)' % tvdb_id),
			('TV trailer', 'RunScript(script.extendedinfo,info=playtvtrailer,tvdb_id=%s)' % tvdb_id),
			('Add to library', 'RunPlugin(%s)' % plugin.url_for('tv_add_to_library', id=tvdb_id))]
	else:
		context_menu = [
			('Add to library', 'RunPlugin(%s)' % plugin.url_for('tv_add_to_library', id=tvdb_id))]
	return {
		'label': text.to_utf8(info['title']),
		'path': plugin.url_for('tv_tvshow', id=tvdb_id),
		'context_menu': context_menu,
		'thumbnail': info['poster'],
		'poster': info['poster'],
		'fanart': info['fanart'],
		'info_type': 'video',
		'stream_info': {'video': {}},
		'info': info
		}

@plugin.cached(TTL=60)
def list_seasons_tvdb(id):
	id = int(id)
	show = TVDB[id]
	show_info = meta_info.get_tvshow_metadata_tvdb(show, banners=False)
	items = []
	for (season_num, season) in show.items():
		if season_num == 0 and not False:
			continue
		elif not season.has_aired(flexible=False):
			continue
		season_info = meta_info.get_season_metadata_tvdb(show_info, season)
		if xbmc.getCondVisibility('system.hasaddon(script.extendedinfo)'):
			context_menu = [
				('[COLOR limegreen]EIM[/COLOR]4[COLOR limegreen]Q[/COLOR]ed', 'RunScript(script.extendedinfo,info=seasoninfo,tvshow=%s,season=%s)' % (show_info['name'], season_num))]
		else:
			context_menu = []
		items.append(
			{
				'label': 'Season %s' % season_num,
				'path': plugin.url_for('tv_season', id=id, season_num=season_num),
				'context_menu': context_menu,
				'info': season_info,
				'thumbnail': season_info['poster'],
				'poster': season_info['poster'],
				'fanart': season_info['fanart']
			})
	return items

@plugin.cached(TTL=60)
def list_episodes_tvdb(id, season_num):
	id = int(id)
	season_num = int(season_num)
	show = TVDB[id]
	show_info = meta_info.get_tvshow_metadata_tvdb(show, banners=False)
	season = show[season_num]
	season_info = meta_info.get_season_metadata_tvdb(show_info, season, banners=True)
	items = []
	for (episode_num, episode) in season.items():
		if not season_num == 0 and not episode.has_aired(flexible=False):
			break
		episode_info = meta_info.get_episode_metadata_tvdb(season_info, episode)
		if xbmc.getCondVisibility('system.hasaddon(script.extendedinfo)'):
			context_menu = [
				('[COLOR limegreen]EIM[/COLOR]4[COLOR limegreen]Q[/COLOR]ed', 'RunScript(script.extendedinfo,info=extendedepisodeinfo,tvshow=%s,season=%s,episode=%s)' % (show_info['name'], season_num, episode_num))]
		else:
			context_menu = []
		items.append(
			{
				'label': episode_info['title'],
				'path': plugin.url_for('tv_play', id=id, season=season_num, episode=episode_num),
				'context_menu': context_menu,
				'info': episode_info,
				'is_playable': True,
				'info_type': 'video',
				'stream_info': {'video': {}},
				'thumbnail': episode_info['poster'],
				'poster': season_info['poster'],
				'fanart': episode_info['fanart']
			})
	return items

def tmdb_to_tvdb(tmdb_show):
	from resources.lib.TheMovieDB import TV
	tvdb_show = None
	name = tmdb_show['original_name']
	try:
		year = int(text.parse_year(tmdb_show['first_air_date']))
	except:
		year = ''
	results = [x['id'] for x in TVDB.search(name, year)]
	if len(results) != 1:
		id = TV(tmdb_show['id']).external_ids().get('tvdb_id', None)
		if id:
			results = [id]
	if results:
		tvdb_show = TVDB[results[0]]
	return tvdb_show, tmdb_show

@plugin.route('/my_trakt/tv_lists/tv_episodes_upcoming')
def trakt_tv_upcoming_episodes(raw=False):
	result = Trakt.get_calendar()
	if raw: 
		return result
	else:
		return list_trakt_episodes(result)

@plugin.route('/my_trakt/tv_lists/tv_episodes_next')
def trakt_tv_next_episodes(raw=False):
	items = []
	result = Trakt.get_next_episodes()
	for episode in result:
		trakt_id = episode['show']['ids']['trakt']
		episode_info = Trakt.get_episode(trakt_id, episode['season'], episode['number'])
		first_aired_string = episode_info['first_aired']
		episode['first_aired'] = first_aired_string
		if int(first_aired_string[:4]) < 1970:
			items.append(episode)
		elif first_aired_string:
			first_aired = time.mktime(time.strptime(first_aired_string[:19], '%Y-%m-%dT%H:%M:%S'))
			if first_aired < time.time():
				items.append(episode)
	if raw:
		return items
	else:
		return list_trakt_episodes(items)

@plugin.route('/my_trakt/tv_lists/tv/watchlist')
def trakt_tv_watchlist(raw=False):
	result = Trakt.get_watchlist('shows')
	if raw:
		return result
	else:
		return list_trakt_tvshows(result, '1', '1')

@plugin.route('/my_trakt/tv_lists/trakt_my_tv_lists')
def lists_trakt_my_tv_lists():
	lists = Trakt.get_lists()
	items = []
	for list in lists:
		name = list['name']
		user = list['user']['username']
		slug = list['ids']['slug']
		items.append(
			{
				'label': name,
				'path': plugin.url_for('lists_trakt_show_tv_list', user=user, slug=slug),
				'thumbnail': plugin.get_media_icon('traktmylists'),
				'fanart': plugin.get_addon_fanart()
			})
	return plugin.finish(items=items, sort_methods=SORT)

@plugin.route('/my_trakt/tv_lists/trakt_liked_tv_list/<page>')
def lists_trakt_liked_tv_lists(page):
	lists, pages = Trakt.get_liked_lists(page)
	items = []
	for list in lists:
		info = list['list']
		name = info['name']
		user = info['user']['username']
		slug = info['ids']['slug']
		items.append(
			{
				'label': name,
				'path': plugin.url_for('lists_trakt_show_tv_list', user = user, slug = slug),
				'thumbnail': plugin.get_media_icon('traktlikedlists'),
				'fanart': plugin.get_addon_fanart()
			})
	nextpage = int(page) + 1
	if pages > page:
		items.append(
			{
				'label': '%s/%s  [I]Next page[/I]  >>' % (nextpage, pages),
				'path': plugin.url_for('lists_trakt_liked_tv_lists', page=int(page) + 1),
				'thumbnail': plugin.get_media_icon('item_next'),
				'fanart': plugin.get_addon_fanart()
			})
	return plugin.finish(items=items, sort_methods=SORT)

@plugin.route('/my_trakt/tv_lists/tv/collection')
def lists_trakt_tv_collection(raw=False):
	results = sorted(Trakt.get_collection('shows'), key=lambda k: k['last_collected_at'], reverse=True)
	if raw:
		return results
	shows = [meta_info.get_tvshow_metadata_trakt(item['show']) for item in results]
	items = [make_tvshow_item(show) for show in shows if show.get('tvdb_id')]
	return items

@plugin.route('/my_trakt/tv_lists/tv/collection/tv_to_library')
def lists_trakt_tv_collection_to_library():
	tv_add_all_to_library(Trakt.get_collection('shows'))

@plugin.route('/my_trakt/tv_lists/tv/show_list/<user>/<slug>')
def lists_trakt_show_tv_list(user, slug, raw=False):
	list_items = Trakt.get_list(user, slug)
	if raw:
		return list_items
	return _lists_trakt_show_tv_list(list_items)

@plugin.route('/my_trakt/tv_lists/tv/_show_tv_list/<list_items>')
def _lists_trakt_show_tv_list(list_items):
	genres_dict = dict([(x['slug'], x['name']) for x in Trakt.get_genres('shows')])
	items = []
	for list_item in list_items:
		item = None
		item_type = list_item['type']
		if item_type == 'show':
			tvdb_id = list_item['show']['ids']['tvdb']
			if tvdb_id != '' and tvdb_id != None:
				show = list_item['show']
				info = meta_info.get_tvshow_metadata_trakt(show, genres_dict)
				item = make_tvshow_item(info)
			else:
				item = None
		elif item_type == 'season':
			tvdb_id = list_item['show']['ids']['tvdb']
			season = list_item['season']
			show = list_item['show']
			show_info = meta_info.get_tvshow_metadata_trakt(show, genres_dict)
			season_info = meta_info.get_season_metadata_trakt(show_info,season, genres_dict)
			label = '%s - Season %s' % (show['title'], season['number'])
			item = (
				{
					'label': label,
					'path': plugin.url_for('tv_season', id=tvdb_id, season_num=list_item['season']['number']),
					'info': season_info,
					'thumbnail': season_info['poster'],
					'poster': season_info['poster'],
					'fanart': season_info['fanart']
				})
		elif item_type == 'episode':
			tvdb_id = list_item['show']['ids']['tvdb']
			episode = list_item['episode']
			show = list_item['show']
			season_number = episode['season']
			episode_number = episode['number']
			show_info = meta_info.get_tvshow_metadata_trakt(show, genres_dict)
			episode_info = meta_info.get_episode_metadata_trakt(show_info, episode)
			label = '%s - S%sE%s - %s' % (show_info['title'], season_number, episode_number, episode_info['title'])
			item = (
				{
					'label': label,
					'path': plugin.url_for('tv_play', id=tvdb_id, season=season_number, episode=episode_number),
					'info': episode_info,
					'is_playable': True,
					'info_type': 'video',
					'stream_info': {'video': {}},
					'thumbnail': episode_info['poster'],
					'poster': episode_info['poster'],
					'fanart': episode_info['fanart']
				})
		if item is not None:
			items.append(item)
	return items