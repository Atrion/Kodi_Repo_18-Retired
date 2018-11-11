# -*- coding: utf-8 -*-

'''
    Incursion Add-on

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

import re,json,urllib,urlparse

from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import directstream
from resources.lib.modules import dom_parser2


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']
        self.domains = ['genvideos.org', 'genvideos.com']
        self.base_link = 'http://genvideos.com'
        self.search_link = '/watch_%s_%s.html'


    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = {'imdb': imdb, 'title': title, 'year': year}
            url = urllib.urlencode(url)
            return url
        except:
            return


    def sources(self, url, hostDict, hostprDict):
        try:
            sources = []

            if url == None: return sources

            data = urlparse.parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
            year = data['year']
            h = {'User-Agent': client.randomagent()}
            title = cleantitle.geturl(data['title']).replace('-', '_')
            url = urlparse.urljoin(self.base_link, self.search_link %(title, year))
            r = client.request(url, headers=h)
            vidlink = re.findall('d\/(.+)"',r)
            r = dom_parser2.parse_dom(r, 'div', {'class': 'title'})
            if '1080p' in r[0].content:
                quality = '1080p'
            elif '720p' in r[0].content:
                quality = '720p'
            else:
                quality = 'SD'
            u = 'https://vidlink.org/streamdrive/info/%s' % vidlink[0]
            r = client.request(u, headers=h)
            r = json.loads(r)
            for i in r:
                try: sources.append({'source': 'gvideo', 'quality': quality, 'language': 'en', 'url': i['url'], 'direct': True, 'debridonly': False})
                except: pass
            return sources
        except:
            return sources


    def resolve(self, url):
        return directstream.googlepass(url)


