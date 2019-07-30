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

from resources.lib.modules import source_utils
from resources.lib.modules import cfscrape


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']
        self.domains = ['hackimdb.com']
        self.base_link = 'https://hackimdb.com'
        self.search_link = '/title/&%s'
        self.scraper = cfscrape.create_scraper()

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = self.base_link + self.search_link % imdb
            return url
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        try:
            sources = []
            hostDict = hostprDict + hostDict
            headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
            r = self.scraper.get(url, headers=headers).content
            try:
                try:
                    match = re.compile('<iframe .+?src="(.+?)"').findall(r)
                    for url in match:
                        if 'youtube' in url:
                            continue
                        valid, host = source_utils.is_host_valid(url, hostDict)
                        if valid:
                            sources.append(
                                {'source': host, 'quality': '720p', 'language': 'en', 'url': url, 'direct': False,
                                 'debridonly': False})
                except:
                    return
                try:
                    match = re.compile('<iframe src="(.+?)"').findall(r)
                    for url in match:
                        if 'youtube' in url:
                            continue
                        valid, host = source_utils.is_host_valid(url, hostDict)
                        if valid:
                            sources.append(
                                {'source': host, 'quality': '720p', 'language': 'en', 'url': url, 'direct': False,
                                 'debridonly': False})
                except:
                    return
            except:
                return
        except Exception:
            return
        return sources

    def resolve(self, url):
        return url
