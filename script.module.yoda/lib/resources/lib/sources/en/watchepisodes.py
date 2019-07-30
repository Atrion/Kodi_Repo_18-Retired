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
from resources.lib.modules import client, source_utils


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']
        self.domains = ['watchepisodes.com', 'watchepisodes.unblocked.pl']
        self.base_link = 'http://www.watchepisodes4.com/'
        self.search_link = 'search/ajax_search?q=%s'

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'year': year}
            url = urllib.urlencode(url)
            return url
        except BaseException:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if url is None:
                return

            url = urlparse.parse_qs(url)
            url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
            url['title'], url['premiered'], url['season'], url['episode'] = title, premiered, season, episode
            url = urllib.urlencode(url)
            return url
        except BaseException:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:
            if url is None:
                return sources

            data = urlparse.parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
            title = data['tvshowtitle']
            hdlr = 's%02de%02d' % (int(data['season']), int(data['episode']))

            query = urllib.quote_plus(cleantitle.getsearch(title))
            surl = urlparse.urljoin(self.base_link, self.search_link % query)
            r = client.request(surl, XHR=True)
            r = json.loads(r)
            r = r['series']
            for i in r:
                tit = i['value']
                if not cleantitle.get(title) == cleantitle.get(tit): raise Exception()
                slink = i['seo']
                slink = urlparse.urljoin(self.base_link, slink)

                r = client.request(slink)
                if not data['imdb'] in r: raise Exception()
                data = client.parseDOM(r, 'div', {'class': 'el-item\s*'})
                epis = [client.parseDOM(i, 'a', ret='href')[0] for i in data if i]
                epis = [i for i in epis if hdlr in i.lower()][0]
                r = client.request(epis)
                links = client.parseDOM(r, 'a', ret='data-actuallink')
                for url in links:
                    try:
                        valid, host = source_utils.is_host_valid(url, hostDict)
                        if not valid: raise Exception()
                        sources.append({'source': host, 'quality': 'SD', 'language': 'en', 'url': url, 'direct': False, 'debridonly': False})
                    except BaseException:
                        return sources

            return sources
        except BaseException:
            return sources

    def resolve(self, url):
        return url
