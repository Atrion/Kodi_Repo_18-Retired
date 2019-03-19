import xbmc, xbmcgui
from resources.lib import Utils
from resources.lib import ImageTools
from resources.lib import TheMovieDB
from resources.lib.WindowManager import wm
from resources.lib.VideoPlayer import PLAYER
from resources.lib.OnClickHandler import OnClickHandler
from resources.lib.DialogBaseInfo import DialogBaseInfo

ch = OnClickHandler()

def get_episode_window(window_type):

	class DialogEpisodeInfo(DialogBaseInfo, window_type):

		def __init__(self, *args, **kwargs):
			if Utils.NETFLIX_VIEW == 'true':
				super(DialogEpisodeInfo, self).__init__(*args, **kwargs)
				self.type = 'Episode'
				self.tvshow_id = kwargs.get('tvshow_id')
				data = TheMovieDB.extended_episode_info(tvshow_id=self.tvshow_id, season=kwargs.get('season'), episode=kwargs.get('episode'))
				if not data:
					return None
				self.info, self.data = data
				self.listitems = [
					(1000, self.data['actors'] + self.data['guest_stars']),
					(750, self.data['crew']),
					(1350, self.data['images'])
					]
			else:
				super(DialogEpisodeInfo, self).__init__(*args, **kwargs)
				self.type = 'Episode'
				self.tvshow_id = kwargs.get('tvshow_id')
				data = TheMovieDB.extended_episode_info(tvshow_id=self.tvshow_id, season=kwargs.get('season'), episode=kwargs.get('episode'))
				if not data:
					return None
				self.info, self.data = data
				self.info['ImageFilter'], self.info['ImageColor'] = ImageTools.filter_image(input_img=self.info.get('thumb', ''), radius=25)
				self.listitems = [
					(1150, self.data['videos']),
					(1000, self.data['actors'] + self.data['guest_stars']),
					(750, self.data['crew']),
					(1350, self.data['images'])
					]

		def onInit(self):
			super(DialogEpisodeInfo, self).onInit()
			Utils.pass_dict_to_skin(self.info, 'movie.', False, False, self.window_id)
			self.get_youtube_vids('%s tv' % self.info['title'])
			self.fill_lists()

		def onClick(self, control_id):
			super(DialogEpisodeInfo, self).onClick(control_id)
			ch.serve(control_id, self)

		@ch.click(750)
		@ch.click(1000)
		def open_actor_info(self):
			wm.open_actor_info(prev_window=self, actor_id=self.listitem.getProperty('id'))

		@ch.click(132)
		def open_text(self):
			wm.open_textviewer(header='Overview', text=self.info['Plot'], color='FFFFFFFF')

		@ch.click(350)
		@ch.click(1150)
		def play_youtube_video(self):
			PLAYER.playtube(self.listitem.getProperty('youtube_id'), listitem=self.listitem, window=self)

		@ch.click(8)
		def play_episode(self):
			if self.dbid:
				dbid = self.dbid
				url = ''
			else:
				dbid = 0
				url = 'plugin://plugin.video.x-wing/tv/play/%s/%s/%s' % (Utils.fetch(TheMovieDB.get_tvshow_ids(self.tvshow_id), 'tvdb_id'), self.info['season'], self.info['episode'])
			PLAYER.play_from_button(url, listitem=None, window=self, type='episodeid', dbid=dbid)

		@ch.click(445)
		def show_manage_dialog(self):
			manage_list = []
			manage_list.append(["[B][COLOR lightseagreen]D[/COLOR]eath[COLOR  lightseagreen]S[/COLOR]tar EIM[/B] Settings", 'Addon.OpenSettings("script.extendedinfo")'])
			manage_list.append(["[B][COLOR lightseagreen]M[/COLOR]x-win[COLOR lightseagreen]G[/COLOR] D[COLOR lightseagreen]S[/COLOR][/B] Settings", 'Addon.OpenSettings("plugin.video.x-wing")'])
			manage_list.append(["YouTube Settings", 'Addon.OpenSettings("plugin.video.youtube")'])
			selection = xbmcgui.Dialog().select(heading='Settings', list=[i[0] for i in manage_list])
			if selection > -1:
				for item in manage_list[selection][1].split('||'):
					xbmc.executebuiltin(item)

	return DialogEpisodeInfo