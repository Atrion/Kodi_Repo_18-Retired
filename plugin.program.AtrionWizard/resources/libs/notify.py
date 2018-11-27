import xbmc, xbmcaddon, xbmcgui, xbmcplugin, os, sys, xbmcvfs, glob
import shutil
import urllib2,urllib
import re
import uservar
import time
import datetime
from resources.libs import traktit, wizard as wiz
from datetime import date

ADDON_ID       = uservar.ADDON_ID
ADDON          = wiz.addonId(ADDON_ID)
ADDONTITLE     = uservar.ADDONTITLE
DIALOG         = xbmcgui.Dialog()
DP             = xbmcgui.DialogProgress()
HOME           = xbmc.translatePath('special://home/')
ADDONS         = os.path.join(HOME,     'addons')
USERDATA       = os.path.join(HOME,     'userdata')
PLUGIN         = os.path.join(ADDONS,   ADDON_ID)
PACKAGES       = os.path.join(ADDONS,   'packages')
ADDONDATA      = os.path.join(USERDATA, 'addon_data', ADDON_ID)
FANART         = os.path.join(PLUGIN,   'fanart.jpg')
ICON           = os.path.join(PLUGIN,   'icon.png')
ART            = os.path.join(PLUGIN,   'resources', 'art')
NOTIFY         = wiz.getS('notify')
NOTEID         = wiz.getS('noteid')
NOTEDISMISS    = wiz.getS('notedismiss')
TODAY          = datetime.date.today()
TOMORROW       = TODAY + datetime.timedelta(days=1)
THREEDAYS      = TODAY + datetime.timedelta(days=3)
NOTIFICATION   = uservar.NOTIFICATION
ENABLE         = uservar.ENABLE
FONTSETTINGS   = uservar.FONTSETTINGS if not uservar.FONTSETTINGS == "" else "Font14"
BACKGROUND     = uservar.BACKGROUND if not uservar.BACKGROUND == "" else FANART
	
############################
###NOTIFICATIONS############
####THANKS GUYS @ TVADDONS##
######MODIFIED BY AFTERMATH#
ACTION_PREVIOUS_MENU 		    =  10	## ESC action
ACTION_NAV_BACK 				=  92	## Backspace action
ACTION_MOVE_UP 					=   3	## Up arrow key
ACTION_MOVE_DOWN 				=   4	## Down arrow key
ACTION_MOUSE_WHEEL_UP 	        = 104	## Mouse wheel up
ACTION_MOUSE_WHEEL_DOWN         = 105	## Mouse wheel down
ACTION_SELECT_ITEM			    =   7	## ?
ACTION_BACKSPACE				= 110	## ?

def Notification(msg='', title='', img=BACKGROUND, resize=False, L=0 ,T=0 ,W=1280 ,H=720 , TxtColor='0xFFFFFFFF', Font='font14', BorderWidth=10):
	class MyWindow(xbmcgui.WindowDialog):
		scr={};
		WINDOW=10147
		CONTROL_LABEL=1
		CONTROL_TEXTBOX=5
		def __init__(self,msg='',bgArt='',L=0,T=0,W=1280,H=720,TxtColor='0xFFFFFFFF',Font='font14',BorderWidth=10):
			self.background=bgArt; self.scr['L']=L; self.scr['T']=T; self.scr['W']=W; self.scr['H']=H; 
			image_path = os.path.join(ART, 'ContentPanel.png')
			self.border = xbmcgui.ControlImage(self.scr['L'],self.scr['T'],self.scr['W'],self.scr['H'], image_path)
			self.addControl(self.border); 
			self.BG=xbmcgui.ControlImage(self.scr['L']+BorderWidth,self.scr['T']+BorderWidth,self.scr['W']-(BorderWidth*2),self.scr['H']-(BorderWidth*2),self.background,aspectRatio=0, colorDiffuse='0x2FFFFFFF')
			self.addControl(self.BG); 
			#title
			temp = title.replace('[', '<').replace(']', '>')
			temp = re.sub('<[^<]+?>', '', temp)
			title_width = len(str(temp))*11
			self.title=xbmcgui.ControlTextBox(L+(W-title_width)/2,T+BorderWidth,title_width,30,font=Font,textColor='0xFF1E90FF'); 
			self.addControl(self.title); 
			self.title.setText(title);
			#body
			self.TxtMessage=xbmcgui.ControlTextBox(self.scr['L']+BorderWidth,self.scr['T']+30+BorderWidth,self.scr['W']-(BorderWidth*2),self.scr['H']-(BorderWidth*2)-75,font=Font,textColor=TxtColor); 
			self.addControl(self.TxtMessage); 
			self.TxtMessage.setText(msg);
			#buttons
			focus=os.path.join(ART, 'button-focus_lightblue.png'); nofocus=os.path.join(ART, 'button-focus_grey.png');
			w1=160; h1=35; w2=160; h2=35; spacing1=20;
			l2=L+W-spacing1-w2; t2=T+H-h2-spacing1; 
			l1=L+W-spacing1-w2-spacing1-w1; t1=T+H-h1-spacing1; 
			self.buttonDismiss=xbmcgui.ControlButton(l1,t1,w1,h1,"Dismiss",textColor="0xFF000000",focusedColor="0xFF000000",alignment=2,focusTexture=focus,noFocusTexture=nofocus); 
			self.buttonRemindMe=xbmcgui.ControlButton(l2,t2,w2,h2,"Remind Later",textColor="0xFF000000",focusedColor="0xFF000000",alignment=2,focusTexture=focus,noFocusTexture=nofocus);
			self.addControl(self.buttonDismiss); self.addControl(self.buttonRemindMe);
			self.buttonRemindMe.controlLeft(self.buttonDismiss); self.buttonRemindMe.controlRight(self.buttonDismiss); 
			self.buttonDismiss.controlLeft(self.buttonRemindMe); self.buttonDismiss.controlRight(self.buttonRemindMe); 
			self.setFocus(self.buttonRemindMe);
		def doRemindMeLater(self):
			try:    wiz.setS("notedismiss","false")
			except: pass
			self.CloseWindow()
			
		def doDismiss(self):
			try:    wiz.setS("notedismiss","true")
			except: pass
			self.CloseWindow()
			
		def onAction(self,action):
			try: F=self.getFocus()
			except: F=False
			if   action == ACTION_PREVIOUS_MENU: self.doRemindMeLater()
			elif action == ACTION_NAV_BACK: self.doRemindMeLater()
			elif action == ACTION_SELECT_ITEM: self.doDismiss()
			else:
				try:
					if not F==self.buttonRemindMe:
						self.setFocus(self.buttonDismiss); 
				except: pass
		def onControl(self,control):
			if   control==self.buttonRemindMe: self.doRemindMeLater()
			elif control== self.buttonDismiss: self.doDismiss()
			else:
				try:    self.setFocus(self.buttonRemindMe); 
				except: pass
		def CloseWindow(self): self.close()
	if resize==False: maxW=1280; maxH=720; W=int(maxW/1.5); H=int(maxH/1.5); L=maxW/6; T=maxH/6; 
	TempWindow=MyWindow(msg=msg,bgArt=img,L=L,T=T,W=W,H=H,TxtColor=TxtColor,Font=Font,BorderWidth=BorderWidth); 
	TempWindow.doModal()
	del TempWindow