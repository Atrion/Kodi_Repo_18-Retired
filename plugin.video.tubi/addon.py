# -*- coding: utf-8 -*-
#Библиотеки, които използват python и Kodi в тази приставка
import re
import sys
import os
import urllib
import urllib2
import json
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon


#Място за дефиниране на константи, които ще се използват няколкократно из отделните модули
__addon_id__= 'plugin.video.tubi'
__Addon = xbmcaddon.Addon(__addon_id__)
md = xbmc.translatePath(__Addon.getAddonInfo('path') + "/resources/media/")
srtsubs_path = xbmc.translatePath('special://temp/tubi.English.srt')

MUA = 'Mozilla/5.0 (Linux; Android 5.0.2; bg-bg; SAMSUNG GT-I9195 Build/JDQ39) AppleWebKit/535.19 (KHTML, like Gecko) Version/1.0 Chrome/18.0.1025.308 Mobile Safari/535.19' #За симулиране на заявка от мобилно устройство
UA = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:69.0) Gecko/20100101 Firefox/69.0' #За симулиране на заявка от  компютърен браузър


#Категории на съдържанието
def CATEGORIES():
        req = urllib2.Request('http://tubitv.com/oz/containers/')
        req.add_header('User-Agent', UA)
        req.add_header('Referer', 'https://tubitv.com/')
        opener = urllib2.build_opener()
        f = opener.open(req)
        jsonrsp = json.loads(f.read())
        #print jsonrsp['hash']['featured']['title']
        #print jsonrsp['hash']['featured']['id']
        
        
        addDir('Search','http://tubitv.com/oz/search/','Search in TUBI Database',2,md+'DefaultAddonsSearch.png')
        try:
            for categories in range(0, len(jsonrsp['list'])):
                try:
                    desc = jsonrsp['hash'][jsonrsp['list'][categories]]['description'].decode('utf8', 'ignore').encode('utf8', 'ignore')
                except:
                    desc = ' '
                try:
                    Cover = jsonrsp['hash'][jsonrsp['list'][categories]]['thumbnail']
                except:
                    Cover = md+'DefaultFolder.png'
                addDir(jsonrsp['hash'][jsonrsp['list'][categories]]['title'],jsonrsp['list'][categories],desc,1,Cover)
        except:
            pass
        #addDir('','',1,'DefaultFolder.png')


#Разлистване заглавията от отделните категории
def INDEXCONTENT(url):
        try:
            req = urllib2.Request('http://tubitv.com/oz/containers/'+url+'/content?cursor=1&limit=200')
            req.add_header('User-Agent', UA)
            req.add_header('Referer', 'https://tubitv.com/')
            opener = urllib2.build_opener()
            f = opener.open(req)
            jsonrsp = json.loads(f.read())
            #print jsonrsp
        
            #Начало на обхождането
            for movie in jsonrsp['contents'].keys(): #Обхождане по името/ключа на елемента, без индекс
                try:
                    if jsonrsp['contents'][movie]['type'] == 'v': #Ако е игрален филм
                        #addLink(name,url,vd,plot,year,mpaa,cast,director,mode,iconimage)
                        try:
                            addLink(jsonrsp['contents'][movie]['title'],jsonrsp['contents'][movie]['id'],str(jsonrsp['contents'][movie]['duration']),jsonrsp['contents'][movie]['description'].decode('utf8', 'ignore').encode('utf8', 'ignore'),jsonrsp['contents'][movie]['year'],jsonrsp['contents'][movie]['ratings'][0]['value'],jsonrsp['contents'][movie]['actors'],jsonrsp['contents'][movie]['directors'],3,jsonrsp['contents'][movie]['posterarts'][0])
                        except:
                            addLink(jsonrsp['contents'][movie]['title'],jsonrsp['contents'][movie]['id'],str(jsonrsp['contents'][movie]['duration']),'',jsonrsp['contents'][movie]['year'],jsonrsp['contents'][movie]['ratings'][0]['value'],jsonrsp['contents'][movie]['actors'],jsonrsp['contents'][movie]['directors'],3,jsonrsp['contents'][movie]['posterarts'][0])
                    elif jsonrsp['contents'][movie]['type'] == 's': #Ако е сериал
                        try:
                            addDir(jsonrsp['contents'][movie]['title'],jsonrsp['contents'][movie]['id'],jsonrsp['contents'][movie]['description'].decode('utf8', 'ignore').encode('utf8', 'ignore'),4,jsonrsp['contents'][movie]['posterarts'][0])
                        except:
                            addDir(jsonrsp['contents'][movie]['title'],jsonrsp['contents'][movie]['id'],'',4,jsonrsp['contents'][movie]['posterarts'][0])
                except:
                    pass
                xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
        except:
            xbmcgui.Dialog().ok('Tubi TV','This is geo-blocked content!', 'You must have USA IP address in order to access this content or services.')
        #Край на обхождането
        
        
        
#Разлистване заглавията от търсенето
def SEARCHCONTENT(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', UA)
        req.add_header('Referer', 'http://tubitv.com/')
        opener = urllib2.build_opener()
        f = opener.open(req)
        jsonrsp = json.loads(f.read())
        
        #Начало на обхождането
        for movie in range(0, len(jsonrsp)):
            try:
                if jsonrsp[movie]['type'] == 'v': #Ако е игрален филм
                    xbmcplugin.setContent(int(sys.argv[1]), 'movie')
                    addLink(jsonrsp[movie]['title'],jsonrsp[movie]['id'],str(jsonrsp[movie]['duration']),jsonrsp[movie]['description'].decode('utf8', 'ignore').encode('utf8', 'ignore'),jsonrsp[movie]['year'],jsonrsp[movie]['ratings'][0]['value'],jsonrsp[movie]['actors'],jsonrsp[movie]['directors'],3,jsonrsp[movie]['posterarts'][0])
                elif jsonrsp[movie]['type'] == 's': #Ако е сериал
                    addDir(jsonrsp[movie]['title'],jsonrsp[movie]['id'],jsonrsp[movie]['description'].decode('utf8', 'ignore').encode('utf8', 'ignore'),4,jsonrsp[movie]['posterarts'][0])
            except:
                pass
            xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
        #Край на обхождането





#Разлистване епизодите на сериал
def EPISODES(url):
        req = urllib2.Request('http://tubitv.com/oz/videos/0'+url+'/content')
        req.add_header('User-Agent', UA)
        req.add_header('Referer', 'http://tubitv.com/')
        opener = urllib2.build_opener()
        f = opener.open(req)
        jsonrsp = json.loads(f.read())
        #print jsonrsp['k'][0]
        
        #Начало на обхождането
        for season in range(0, len(jsonrsp['children'])):
            for episode in range(0, len(jsonrsp['children'][season]['children'])):
                xbmcplugin.setContent(int(sys.argv[1]), 'episode')
                try:
                    addLink(jsonrsp['children'][season]['children'][episode]['title'],jsonrsp['children'][season]['children'][episode]['id'],str(jsonrsp['children'][season]['children'][episode]['duration']),jsonrsp['children'][season]['children'][episode]['description'].decode('utf8', 'ignore').encode('utf8', 'ignore'),jsonrsp['children'][season]['children'][episode]['year'],jsonrsp['children'][season]['children'][episode]['ratings'][0]['value'],jsonrsp['children'][season]['children'][episode]['actors'],jsonrsp['children'][season]['children'][episode]['directors'],3,jsonrsp['children'][season]['children'][episode]['thumbnails'][0])
                except:
                    addLink(jsonrsp['children'][season]['children'][episode]['title'],jsonrsp['children'][season]['children'][episode]['id'],str(jsonrsp['children'][season]['children'][episode]['duration']),'',jsonrsp['children'][season]['children'][episode]['year'],jsonrsp['children'][season]['children'][episode]['ratings'][0]['value'],[''],jsonrsp['children'][season]['children'][episode]['directors'],3,jsonrsp['children'][season]['children'][episode]['thumbnails'][0])
        #Край на обхождането





#Търсачка
def SEARCH(url):
        keyb = xbmc.Keyboard('', 'Search in TUBI Database')
        keyb.doModal()
        searchText = ''
        if (keyb.isConfirmed()):
            searchText = urllib.quote_plus(keyb.getText())
            searchText=searchText.replace(' ','+')
            searchurl = url + searchText
            searchurl = searchurl.encode('utf-8')
            SEARCHCONTENT(searchurl)
        else:
            addDir('Go to main menu...','','',md+'DefaultFolderBack.png')







#Зареждане на видео
def PLAY(name,url):
        req = urllib2.Request('http://tubitv.com/oz/videos/'+url+'/content')
        req.add_header('User-Agent', UA)
        req.add_header('Referer', 'http://tubitv.com/')
        opener = urllib2.build_opener()
        f = opener.open(req)
        jsonrsp = json.loads(f.read())
        #print jsonrsp['url']
        
        #Изтегляне на субтитри
        suburl=''
        try:
            suburl=jsonrsp['subtitles'][0]['url']
            req = urllib2.Request(suburl)
            req.add_header('User-Agent', UA)
            response = urllib2.urlopen(req)
            data=response.read()
            response.close()
            with open(srtsubs_path, "w") as subfile:
                subfile.write(data)
                sub = 'true'
                xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%('TUBI','Loaded English subtitles', 4000, md+'DefaultAddonSubtitles.png'))
        except:
            sub = 'false'
        
        
        li = xbmcgui.ListItem(iconImage=jsonrsp['thumbnails'][0], thumbnailImage=jsonrsp['thumbnails'][0], path=jsonrsp['url']+'|User-Agent=stagefright&Referer=http://tubitv.com')
        li.setInfo( type="Video", infoLabels={ "Title": name, "Plot": jsonrsp['description'] } ) #.decode('utf8', 'ignore').encode('utf8', 'ignore')
        if sub=='true': #Задаване на външни субтитри, ако има такива
            li.setSubtitles([srtsubs_path])
        try:
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)
        except:
            xbmc.executebuiltin("Notification('TUBI','Video Not Found!')")






#Модул за добавяне на отделно заглавие и неговите атрибути към съдържанието на показваната в Kodi директория - НЯМА НУЖДА ДА ПРОМЕНЯТЕ НИЩО ТУК
def addLink(name,url,vd,plot,year,mpaa,cast,director,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
        liz.setArt({ 'thumb': iconimage,'poster': iconimage, 'banner' : iconimage, 'fanart': iconimage })
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setInfo( type="Video", infoLabels={ "Duration": vd, "Plot": plot } )
        liz.setInfo( type="Video", infoLabels={ "Year": year, "Mpaa": mpaa } )
        liz.setInfo( type="Video", infoLabels={ "Cast": cast, "Director": director } )
        liz.addStreamInfo('video', { 'aspect': 1.78, 'codec': 'h264' })
        liz.addStreamInfo('audio', { 'codec': 'aac', 'channels': 2 })
        liz.setProperty("IsPlayable" , "true")
        
        contextmenu = []
        contextmenu.append(('Information', 'XBMC.Action(Info)'))
        liz.addContextMenuItems(contextmenu)
        
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
        return ok

#Модул за добавяне на отделна директория и нейните атрибути към съдържанието на показваната в Kodi директория - НЯМА НУЖДА ДА ПРОМЕНЯТЕ НИЩО ТУК
def addDir(name,url,desc,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
        liz.setArt({ 'thumb': iconimage,'poster': iconimage, 'banner' : iconimage, 'fanart': iconimage })
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": desc } )
        
        if len(desc)>0:
            contextmenu = []
            contextmenu.append(('Information', 'XBMC.Action(Info)'))
            liz.addContextMenuItems(contextmenu)
        
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok


#НЯМА НУЖДА ДА ПРОМЕНЯТЕ НИЩО ТУК
def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                                
        return param



params=get_params()
url=None
name=None
iconimage=None
mode=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        name=urllib.unquote_plus(params["iconimage"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass


#Списък на отделните подпрограми/модули в тази приставка - трябва напълно да отговаря на кода отгоре
if mode==None or url==None or len(url)<1:
        CATEGORIES()
    
elif mode==1:
        INDEXCONTENT(url)

elif mode==2:
        SEARCH(url)

elif mode==3:
        PLAY(name,url)

elif mode==4:
        EPISODES(url)

elif mode==5:
        SEARCHCONTENT(url)


xbmcplugin.endOfDirectory(int(sys.argv[1]))
