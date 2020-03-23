"""
    Plugin for UrlResolver
    Copyright (C) 2020

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

from __generic_resolver__ import GenericResolver
from lib import helpers


class StreamWireResolver(GenericResolver):
    name = "streamwire"
    domains = ['streamwire.net']
    pattern = r'(?://|\.)(streamwire\.net)/(?:embed-)?([0-9a-zA-Z]+)'

    def get_media_url(self, host, media_id):
        return helpers.get_media_url(self.get_url(host, media_id),
                                     patterns=[r'''src:\s*"(?P<url>[^"]+)'''],
                                     generic_patterns=False)

    def get_url(self, host, media_id):
        return self._default_get_url(host, media_id, template='https://{host}/embed-{media_id}.html')
