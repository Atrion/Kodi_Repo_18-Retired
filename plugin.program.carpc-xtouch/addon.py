import xbmc
import xbmcgui
import xbmcaddon
import time

# Get global paths
addon = xbmcaddon.Addon(id='plugin.program.carpc-xtouch')
addonpath = addon.getAddonInfo('path').decode("utf-8")
updating = 0

#control
HOME_BUTTON  = 1201
BACK_BUTTON  = 1202
BUTTON_FOCUS = 1203
SETTINGS_BUTTON  = 1204
LOADDAY_BUTTON  = 1205
LOADNIGHT_BUTTON  = 1206
SAVEDAY_BUTTON  = 1207
SAVENIGHT_BUTTON  = 1208
ACTION_BACK  = 92


COMMANDLIST = ['BGPicturesAllowFocus','BottomBGColor','BottomBGTransparency','ClockColor','ConfigButton',
'Container.SortMethod','CustomBackgroundPath','CustomColorFocus','CustomColorHomebuttons','CustomColorNofocus',
'CustomLogoPath','CustomMusicPath','CustomMusicPath1','CustomMusicPath2','CustomMusicPath3','CustomMusicPath4',
'CustomMusicPath5','CustomMusicPath6','CustomRadioBgFullPath','CustomSubmenuBGColor','CustomVideoPath2',
'CustomVideoPath3','CustomVideoPath4','CustomVideoPath5','CustomVideoPath6','CustomVisBgFullPath',
'CustomVisBgPath','DayNightModus','DeleteRadioStation','DeleteRadioStation','Enable_Clock_Animation',
'Enable_Clock_Animation','Enable_Clock_Second_Hand','Enable_Clock_Second_Hand','EnableBGColor','EnableBGColor',
'EnableBGPictures','EnableBGPictures','EnableBottomBG','EnableBottomBG','EnablePlayerButtonsBG',
'EnablePlayerButtonsBG','EnableSubmenuBG','EnableTempOutput','EnableTempOutput','EnableTitleImage',
'EnableTitleText','EnableTitleText','FirstSettings','HBOutlineColor','HBSolidColor','HBTransparency',
'Hide1024x600Fix','HideAlternateRadio','HideAppSwitcher','HideHomeButtonConnect3g','HideHomeButtonConnect3g',
'HideHomeButtonConnectWiFi','HideHomeButtonDayNight','HideHomeButtonFavourites','HideHomeButtonFavourites',
'HideHomeButtonFileManager','HideHomeButtonFileManager','HideHomeButtonMusic','HideHomeButtonMusic',
'HideHomeButtonMusicAlbums','HideHomeButtonMusicArtists','HideHomeButtonMusicGenre','HideHomeButtonMusicPlayerTitle',
'HideHomeButtonMusicPlayerTitle','HideHomeButtonNavigation','HideHomeButtonNavigation','HideHomeButtonOBD',
'HideHomeButtonPictures','HideHomeButtonPrograms','HideHomeButtonPrograms','HideHomeButtonRadio','HideHomeButtonRadio',
'HideHomeButtonRadioStationName','HideHomeButtonRadioStationName','HideHomeButtonShutdownDialog',
'HideHomeButtonShutdownDialog','HideHomeButtonTime','HideHomeButtonTime','HideHomeButtonVideo','HideHomeButtonVideo',
'HideHomeButtonWeather','HideHomeButtonWeather','HideHomeRadioText','HideRandomRepeat','HideRandomRepeat',
'HideVisualisationHome','HideVisualisationHome','HideVolumeBar','HideWeatherTitleWidget','HideWeatherTitleWidget',
'Home1BG','Home1BGFocus','Home2BG','Home2BGFocus','Home3BG','Home3BGFocus','Home4BG','Home4BGFocus','Home5BG',
'Home5BGFocus','Home6BG','Home6BGFocus','HomeButton1Value','HomeButton2Value','HomeButton3Value','HomeButton4Value',
'HomeButton5Value','HomeButton6Value','HomeScreenTitle','HomeScreenTitleImage','ListRadioStation','ListRadioStation',
'MagicButtonIcon1','MagicButtonIcon2','MagicButtonIcon3','MagicButtonIcon4','MagicButtonIcon5','MagicButtonIcon6',
'MediaSubMenuVisible','MediaSubMenuVisible2','PlayerButtonsBGColor','PlayerButtonsBGTransparency',
'PlayerControlsShowAudioInfo','PlayerControlsShowAudioInfo','PlayerControlsShowVideoInfo','PlayerControlsShowVideoInfo',
'PlayerControlsSubMenuVisible','PlayerControlsSubMenuVisible','RadioAddonBackground','RadioAddonBackgroundImage',
'RadioAddonRadioText','RadioBGColor','RadioBGTransparency','RadioDisplayColor','RadioDisplayTransparency','RadioMuteOn',
'SaveDayNight','SaveRadioStation','SaveRadioStation','SettingsIcon2','Show_Clock_white','Show_Clock_white',
'ShowMousePointer','ShowOutlines','ShowOutlines','ShowStationbuttonsOutlines','SkinHelper.EnableAnimatedPosters',
'SkinHelper.EnablePVRThumbs','SkinSettings','StartEndDay','Startup_Playlist_Path','StationbuttonsOutlineColor',
'SubmenuBGTransparency','SubmenuIconsBig','SubmenuIconsMid','SubmenuIconsSmall','SubtitleScript_Path','TempSensor',
'Use_Startup_Playlist','UseCustomBackground','UseCustomBackground','UseCustomLogo','UseCustomLogo','UseRadioBG',
'UseVisBg','UseVisBg','UseVisBgCover','UseVisBgCover','UseVisBgFull','UseVisBgFull','TempSensor','TempSensorCount',
'TempBackgroundPath','TempLabelColor','TempClockColorHours','TempClockColorMinutes','ShowRecentlyAdded','ShowNextTrack',
'ShowNextTrackDuration','HideMusicInfoBG',]

def readDaySetting(command):
    xbmc.executebuiltin('Skin.SetString(' + command + ',' + addon.getSetting("day_" + command) + ')')

def readNightSetting(command):
    xbmc.executebuiltin('Skin.SetString(' + command + ',' + addon.getSetting("night_" + command) + ')')

def saveDaySetting(command):
    addon.setSetting('day_' + command,str(xbmc.getInfoLabel('Skin.String(' + command + ')')))

def saveNightSetting(command):
    addon.setSetting('night_' + command,str(xbmc.getInfoLabel('Skin.String(' + command + ')')))

def loadDay():
	global COMMANDLIST
	xbmcgui.Window(10000).setProperty('xtouch.updating','true')
	time.sleep(0.5)
	for item in COMMANDLIST:
	    readDaySetting(item)
	time.sleep(1)
	xbmcgui.Window(10000).setProperty('xtouch.updating','false')
	addon.setSetting('state','day')
	xbmcgui.Window(10000).setProperty('xtouch.daynight','day')

def loadNight():
	global COMMANDLIST
	xbmcgui.Window(10000).setProperty('xtouch.updating','true')
	time.sleep(0.5)
	for item in COMMANDLIST:
	    readNightSetting(item)
	time.sleep(1)
	xbmcgui.Window(10000).setProperty('xtouch.updating','false')
	addon.setSetting('state','night')
	xbmcgui.Window(10000).setProperty('xtouch.daynight','night')

def saveDay():
	global COMMANDLIST
	xbmcgui.Window(10000).setProperty('xtouch.saving','true')
	time.sleep(0.5)
	for item in COMMANDLIST:
	    saveDaySetting(item)
	time.sleep(1)
	xbmcgui.Window(10000).setProperty('xtouch.saving','false')

def saveNight():
	global COMMANDLIST
	xbmcgui.Window(10000).setProperty('xtouch.saving','true')
	time.sleep(0.5)
	for item in COMMANDLIST:
	    saveNightSetting(item)
	time.sleep(0.5)
	xbmcgui.Window(10000).setProperty('xtouch.saving','false')

count = len(sys.argv) - 1
if count > 0:
    given_arg = sys.argv[1]
    if given_arg != "-1":
	if given_arg == "loadday":
	    loadDay()
    	    quit()

	if given_arg == "saveday":
	    saveDay()
    	    quit()

	if given_arg == "loadnight":
	    loadNight()
    	    quit()

	if given_arg == "savenight":
	    saveNight()
    	    quit()

class xtouch(xbmcgui.WindowXMLDialog):

    def onInit(self):
        xtouch.button_home=self.getControl(HOME_BUTTON)
        xtouch.button_back=self.getControl(BACK_BUTTON)
        xtouch.buttonfocus=self.getControl(BUTTON_FOCUS)
        xtouch.button_settings=self.getControl(SETTINGS_BUTTON)
	xbmcgui.Window(10000).setProperty('xtouch.updating','false')
	xbmcgui.Window(10000).setProperty('xtouch.saving','false')

	if str(xbmc.getSkinDir()) != "skin.carpc-xtouch":
	    xbmcgui.Window(10000).setProperty('xtouch.warning','true')
	else:
	    xbmcgui.Window(10000).setProperty('xtouch.warning','false')

    def onClick(self, controlID):

        if controlID == HOME_BUTTON:
            self.close()

        if controlID == BACK_BUTTON:
            self.close()

        if controlID == SETTINGS_BUTTON:
	    self.setFocus(self.buttonfocus)
	    addon.openSettings()
	    self.setFocus(self.buttonfocus)

        if controlID == LOADDAY_BUTTON:
	    loadDay()

        if controlID == LOADNIGHT_BUTTON:
	    loadNight()

        if controlID == SAVEDAY_BUTTON:
	    saveDay()

        if controlID == SAVENIGHT_BUTTON:
	    saveNight()

    def onFocus(self, controlID):
        pass
    
    def onControl(self, controlID):
        pass

xtouchdialog = xtouch("xtouch.xml", addonpath, 'default', '720')

xtouchdialog.doModal()
del xtouchdialog
