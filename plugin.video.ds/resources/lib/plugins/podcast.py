"""
    podcast.py --- Youraddonname Plugin to play podcasts
    Copyright (C) 2017, CandyLand

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
"""
import base64
import pickle
import time
import xbmc
from BeautifulSoup import BeautifulSoup

import feedparser
import koding
import xbmcaddon
import xbmcgui
from koding import route
from resources.lib.util.context import get_context_items
from resources.lib.util.url import replace_url
from resources.lib.util.xml import JenItem, JenList, display_list
from unidecode import unidecode

from ..plugin import Plugin

CACHE_TIME = 3600 * 12  # change to wanted cache time in seconds

addon_fanart = xbmcaddon.Addon().getAddonInfo('fanart')
addon_icon = xbmcaddon.Addon().getAddonInfo('icon')
addon_name = xbmcaddon.Addon().getAddonInfo('name')


class Podcast(Plugin):
    name = "podcast"

    def process_item(self, item_xml):
        if "<podcast>" in item_xml:
            item = JenItem(item_xml)
            result_item = {
                'label': item["title"],
                'icon': replace_url(item.get("thumbnail", addon_icon)),
                'fanart': replace_url(item.get("fanart", addon_fanart)),
                'mode': "podcast",
                'url': item.get("podcast", ""),
                'folder': True,
                'imdb': "0",
                'content': "files",
                'season': "0",
                'episode': "0",
                'info': {},
                'year': "0",
                'context': get_context_items(item),
                "summary": item.get("summary", None)
            }
            result_item["properties"] = {'fanart_image': result_item["fanart"]}
            result_item['fanart_small'] = result_item["fanart"]
            return result_item

    def clear_cache(self):
        dialog = xbmcgui.Dialog()
        if dialog.yesno(addon_name, "Clear Podcast Plugin Cache?"):
            koding.Remove_Table("podcast_plugin")


@route(mode='podcast', args=["url"])
def podcast(url):
    xml = fetch_from_db(url)
    if not xml:
        xml = ""
        feed = feedparser.parse(url)
        # feed_title = feed.feed.title
        feed_image = feed.feed.image.href
        for episode in feed.entries:
            episode_title = remove_non_ascii(episode.title)
            xbmc.log("episode_title" + repr(episode_title), xbmc.LOGNOTICE)
            summary = extract_text_from_html(episode.summary)
            links = episode.links
            audiofile = ""
            for enclosure in episode.enclosures:
                if enclosure.type.startswith("audio"):
                    audiofile = enclosure.href
                    break
            else:
                for link in links:
                    if link["type"].startswith("audio"):
                        audiofile = link.href
                        break
                else:
                    continue
            xml += "<item>\n"\
                   "\t<title>%s</title>\n"\
                   "\t<thumbnail>%s</thumbnail>\n"\
                   "\t<fanart>%s</fanart>\n"\
                   "\t<link>%s</link>\n"\
                   "\t<summary>%s</summary>\n"\
                   '</item>\n' % (episode_title, feed_image, feed_image,
                                  audiofile, summary)
        save_to_db(xml, url)
    jenlist = JenList(xml)
    display_list(jenlist.get_list(), "songs")


def extract_text_from_html(html):
    soup = BeautifulSoup(html)

    # get text
    text = soup.text

    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)
    return remove_non_ascii(text)


def remove_non_ascii(text):
    return unidecode(unicode(text))


def save_to_db(item, url):
    if not item or not url:
        return False
    koding.reset_db()
    koding.Remove_From_Table(
        "podcast_plugin",
        {
            "url": url
        })

    koding.Add_To_Table("podcast_plugin",
                        {
                            "url": url,
                            "item": base64.b64encode(pickle.dumps(item)),
                            "created": time.time()
                        })


def fetch_from_db(url):
    koding.reset_db()
    podcast_plugin_spec = {
        "columns": {
            "url": "TEXT",
            "item": "TEXT",
            "created": "TEXT"
        },
        "constraints": {
            "unique": "url"
        }
    }
    koding.Create_Table("podcast_plugin", podcast_plugin_spec)
    match = koding.Get_From_Table(
        "podcast_plugin", {"url": url})
    if match:
        match = match[0]
        if not match["item"]:
            return None
        created_time = match["created"]
        if created_time and float(created_time) + CACHE_TIME >= time.time():
            match_item = match["item"]
            try:
                    result = pickle.loads(base64.b64decode(match_item))
            except:
                    return None
            return result
        else:
            return []
    else:
        return []
