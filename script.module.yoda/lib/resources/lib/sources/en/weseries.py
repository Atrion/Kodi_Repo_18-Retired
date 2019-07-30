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

import re, urllib, urlparse, json

from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import dom_parser2
from resources.lib.modules import source_utils

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']
        self.domains = ['watchepisodeseries.com']
        self.base_link = 'https://watchepisodeseries.unblocked.gdnp'
        self.base_link2 = 'http://www.watchepisodeseries.com'

        self.search_link = 'home/search?q=%s'

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            simple_title = cleantitle.getsearch(tvshowtitle)
            tvshowtitle = urllib.quote_plus(simple_title)
            search_url = urlparse.urljoin(self.base_link, self.search_link % tvshowtitle)

            r = client.request(search_url)
            if r:
                r = json.loads(r)['series']
                r = [(urlparse.urljoin(self.base_link, i['seo_name'])) for i in r if
                     simple_title == cleantitle.get_simple(i['original_name'])]
                if r:
                    return r[0]
                else:
                    return
            else:
                search_url2 = urlparse.urljoin(self.base_link2, self.search_link % tvshowtitle)
                r = client.request(search_url2)
                r = json.loads(r)['series']
                r = [(urlparse.urljoin(self.base_link2, i['seo_name'])) for i in r if
                     simple_title == cleantitle.get_simple(i['original_name'])]
                if r:
                    return r[0]
                else:
                    return
        except BaseException:
            return
            
    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if url is None: return
            r = client.request(url)
            r = dom_parser2.parse_dom(r, 'div', {'class': 'el-item'})
            r = [(dom_parser2.parse_dom(i, 'div', {'class': 'season'}),
                  dom_parser2.parse_dom(i, 'div', {'class': 'episode'}),
                  dom_parser2.parse_dom(i, 'a', req='href')) for i in r if i]
            r = [(i[2][0].attrs['href']) for i in r if i[0][0].content == 'Season %01d' % int(season) and i[1][0].content == 'Episode %01d' % int(episode)]
            if r: return r[0]
            else: return
        except BaseException:
            return

    def sources(self, url, hostDict, hostprDict):
        try:
            sources = []
            if url is None: return sources
            r = client.request(url)
            r = dom_parser2.parse_dom(r, 'div', {'class': 'll-item'})
            r = [(dom_parser2.parse_dom(i, 'a', req='href'),
                  dom_parser2.parse_dom(i, 'div', {'class': 'notes'})) for i in r if i]
            r = [(i[0][0].attrs['href'], i[0][0].content, i[1][0].content if i[1] else 'None') for i in r]
            for i in r:
                try:
                    url = i[0]
                    url = client.replaceHTMLCodes(url)
                    url = url.encode('utf-8')
                    valid, host = source_utils.is_host_valid(i[1], hostDict)
                    if not valid: continue
                    host = client.replaceHTMLCodes(host)
                    host = host.encode('utf-8')
                    
                    info = []
                    quality, info = source_utils.get_release_quality(i[2], i[2])

                    info = ' | '.join(info)
                    sources.append({'source': host, 'quality': quality, 'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': False})
                except BaseException:
                    pass

            return sources
        except BaseException:
            return sources

    def resolve(self, url):
        try:
            r = client.request(url)
            r = dom_parser2.parse_dom(r, 'a', req=['href','data-episodeid','data-linkid'])[0]
            url = r.attrs['href']
            url = client.replaceHTMLCodes(url)
            url = url.encode('utf-8')
            return url
        except BaseException:
            return
