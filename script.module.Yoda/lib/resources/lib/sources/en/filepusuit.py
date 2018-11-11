# -*- coding: UTF-8 -*-
#######################################################################
 # ----------------------------------------------------------------------------
 # "THE BEER-WARE LICENSE" (Revision 42):
 # @tantrumdev wrote this file.  As long as you retain this notice you
 # can do whatever you want with this stuff. If we meet some day, and you think
 # this stuff is worth it, you can buy me a beer in return. - Muad'Dib
 # ----------------------------------------------------------------------------
#######################################################################

# Addon Name: Yoda
# Addon id: plugin.video.Yoda
# Addon Provider: Supremacy

import re
import urllib
import urlparse
from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import proxy
from resources.lib.modules import log_utils
from resources.lib.modules import source_utils 
from resources.lib.modules import cfscrape

class source:
    def __init__(self):
        self.priority = 1                           
        self.language = ['en']                      
        self.domains = ['filepursuit.com']           
        self.base_link = 'https://filepursuit.com'  
        self.search_link = '/search5/%s/' 
 
    def movie(self, imdb, title, localtitle, aliases, year):
       
        
       
        try:
           
            title = cleantitle.geturl(title)
            
            url = '%s+%s' % (title,year)
           
           
            return url
        except:
            return
           
    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        
        try:
           
           
            url = cleantitle.geturl(tvshowtitle)
            return url
        except:
            return
 
    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if not url: return
           
           
            tvshowtitle = url
           
           
           
            season = '%02d' % int(season)
            episode = '%02d' % int(episode)
           
            
           
            url = '%s+s%se%s' % (tvshowtitle,str(season),str(episode))
           
           
            return url
        except:
            return
 
 
    def sources(self, url, hostDict, hostprDict):
       
      
       
        try:
            sources = []
            scraper = cfscrape.create_scraper()
           
            query = url
 
           
 
            url = self.base_link + self.search_link % query
 
 
            r = scraper.get(url).content
 
 
            try:
               
 
                match = re.compile('data-clipboard-text="(.+?)"').findall(r)
               
               
                for url in match:
               
               
                    if '2160' in url: quality = '4K'
                    elif '4k' in url: quality = '4K'
                    elif '1080' in url: quality = '1080p'
                    elif '720' in url: quality = 'HD'
                    elif '480' in url: quality = 'SD' 
                    else: quality = 'SD'
                   
                   
                    sources.append({
                        'source': 'Direct', 
                        'quality': quality, 
                        'language': 'en',   
                        'url': url,         
                        'direct': False,   
                        'debridonly': False 
                    })
            except:
                return
        except Exception:
            return
           
    
           
        return sources
 
    def resolve(self, url):
        return url