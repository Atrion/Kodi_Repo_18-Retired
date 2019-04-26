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

import re, requests
from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import source_utils


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']
        self.domains = ['cmovieshd.bz']
        self.base_link = 'http://w1.cmovieshd.bz'
        self.search_link = '/film/%s/watching.html?ep=0'

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            title = cleantitle.geturl(title).replace('--', '-')
            url = self.base_link + self.search_link % title
            return url
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        try:
            sources = []
            r = requests.get(url).content
            qual = re.compile('class="quality">(.+?)<').findall(r)
            for i in qual:
                if '1080' in i:
                    quality = '1080p'
                elif '720' in i:
                    quality = '720p'
                else:
                    quality = 'SD'
            u = client.parseDOM(r, "div", attrs={"class": "pa-main anime_muti_link"})
            for t in u:
                u = re.findall('<li class=".+?" data-video="(.+?)"', t)
                for url in u:
                    if 'vidcloud' in url:
                        url = 'https:' + url
                        r = requests.get(url).content
                        t = re.findall('li data-status=".+?" data-video="(.+?)"', r)
                        for url in t:
                            if 'vidcloud' in url:
                                continue
                            valid, host = source_utils.is_host_valid(url, hostDict)
                            sources.append({'source': host, 'quality': quality, 'language': 'en', 'url': url, 'direct': False, 'debridonly': False})
                    if 'vidcloud' in url:
                        continue
                    valid, host = source_utils.is_host_valid(url, hostDict)
                    sources.append({'source': host, 'quality': quality, 'language': 'en', 'url': url, 'direct': False, 'debridonly': False})
                return sources
        except:
            return

    def resolve(self, url):
        return url
