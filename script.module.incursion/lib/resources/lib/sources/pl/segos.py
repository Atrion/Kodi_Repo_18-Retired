# -*- coding: utf-8 -*-

'''
    Incursion Add-on
    Copyright (C) 2018 CherryTeam

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

    
from resources.lib.modules import source_utils, client, cleantitle, control
import urllib, urlparse
import requests

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['pl']
        self.domains = ['segos.es']
        
        self.base_link = 'https://segos.es'
        self.search_link = '/?search=%s'
        self.user_name = control.setting('segos.username')
        self.user_pass = control.setting('segos.password')        
    def movie(self, imdb, title, localtitle, aliases, year):
        return self.search(title,localtitle, year)

    
    def search(self, title, localtitle, year):
        try:
            simply_name = cleantitle.get(localtitle)
            simply_name2 = cleantitle.get(title)
            query = self.search_link % urllib.quote_plus(cleantitle.query(localtitle))
            url = urlparse.urljoin(self.base_link, query)
            headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0', 'Referer': 'https://segos.es/?page=login' }
            data ={"login" : self.user_name, 'password': self.user_pass,'loguj': ''}
            url = 'https://segos.es/?page=login'
            s = requests.Session()
            s.post('https://segos.es/?page=login',data=data,headers=headers)
            url=urlparse.urljoin(self.base_link,query)
            k = s.get(url)
            result = k.text
 
            results = client.parseDOM(result, 'div', attrs={'class':'col-lg-12 col-md-12 col-xs-12'})
            for result in results:
                segosurl = client.parseDOM(result, 'a', ret='href')[0]
                result = client.parseDOM(result, 'a')
                segostitles = cleantitle.get(result[1]).split('/')
                for segostitle in segostitles:
                    if simply_name == segostitle or simply_name2 == segostitle:
                        return urlparse.urljoin(self.base_link,segosurl)
                    continue
        except Exception, e:
            print str(e)
            return


    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        return localtvshowtitle


    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        query = url + ' s' + season.zfill(2) + 'e' + episode.zfill(2)
        return self.search(query, None)        
    
    def sources(self, url, hostDict, hostprDict):
        
        sources = []
        try:
            if url == None: return sources
            headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0', 'Referer': 'https://segos.es/?page=login' }
            data ={"login" : self.user_name, 'password': self.user_pass,'loguj': ''}
            s = requests.Session()
            s.post('https://segos.es/?page=login',data=data,headers=headers)
            k = s.get(url)
            result = k.text
            result = client.parseDOM(result, 'table', attrs={'class':'table table-hover table-bordered'})                        
            results = client.parseDOM(result, 'tr')
            for result in results:
                try:
                    quality = client.parseDOM(result, 'td')[1]
                    quality = quality.replace(' [EXTENDED]','')
                    lang = 'en'
                    info = client.parseDOM(result, 'td')[0]
                    info = client.parseDOM(info, 'img', ret='src')
                    if 'napisy' in info[0]: 
                        info[0] = 'Napisy'
                        lang = 'pl'
                    if 'lektor' in info[0]: 
                        info[0] = 'Lektor'
                        lang = 'pl'
                    if 'dubbing' in info[0]: 
                        info[0] = 'Dubbing'
                        lang = 'pl'
                    link = client.parseDOM(result, 'td')[5]
                    link = client.parseDOM(link, 'a', ret='href')
                    link = urlparse.urljoin(self.base_link,str(link[0]))
                    k = s.get(link)
                    video_link_content = k.text
                    video_link_content = client.parseDOM(video_link_content, 'div', attrs={'class':'embed-responsive embed-responsive-16by9'})
                    video_link = client.parseDOM(video_link_content, 'iframe', ret='src')
                    valid, host = source_utils.is_host_valid(video_link[0], hostDict)
                    if 'ebd.cda.pl' in host and quality == '1080p':
                        sources.append({'source': host, 'quality': quality, 'language': lang, 'url': video_link[0], 'info': info[0], 'direct': False, 'debridonly': False})
                        sources.append({'source': host, 'quality': '720p', 'language': lang, 'url': video_link[0].replace('1080p','720p'), 'info': info[0], 'direct': False, 'debridonly': False})
                        sources.append({'source': host, 'quality': 'SD', 'language': lang, 'url': video_link[0].replace('1080p','480p'), 'info': info[0], 'direct': False, 'debridonly': False})
                        sources.append({'source': host, 'quality': 'SD', 'language': lang, 'url': video_link[0].replace('1080p','360p'), 'info': info[0], 'direct': False, 'debridonly': False})
                        continue
                    if 'ebd.cda.pl' in host and quality == '720p':
                        sources.append({'source': host, 'quality': quality, 'language': lang, 'url': video_link[0], 'info': info[0], 'direct': False, 'debridonly': False})
                        sources.append({'source': host, 'quality': 'SD', 'language': lang, 'url': video_link[0].replace('720p','480p'), 'info': info[0], 'direct': False, 'debridonly': False})
                        sources.append({'source': host, 'quality': 'SD', 'language': lang, 'url': video_link[0].replace('720p','360p'), 'info': info[0], 'direct': False, 'debridonly': False})
                        continue    
                    sources.append({'source': host, 'quality': quality, 'language': lang, 'url': video_link[0], 'info': info[0], 'direct': False, 'debridonly': False})
                except:
                    pass
            return sources
        except:
            return sources
    
    def resolve(self, url):
        return url      
